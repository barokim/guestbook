"""실제 HTTP/WebSocket ASGI 경로와 임시 SQLite를 이용하는 실습 테스트."""
import base64
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, contextmanager

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from starlette.websockets import WebSocketDisconnect

import lab_main as lab
import main

SECRET = 'unit-test-only-' + 'x' * 40
ORIGIN = 'http://127.0.0.1:8001'

@pytest.fixture
def app(tmp_path):
    return lab.create_lab_app(secret=SECRET, db_path=tmp_path / 'lab.sqlite3', origin=ORIGIN, https_only=False)

@pytest.fixture
def client(app):
    with TestClient(app, base_url=ORIGIN, headers={'origin': ORIGIN}) as c:
        yield c


def name(client, value='바로'):
    response = client.post('/nickname', data={'name': value}, follow_redirects=False)
    assert response.status_code == 303
    return response


def room(client, title='연습방'):
    response = client.post('/chat/rooms', data={'title': title})
    assert response.status_code == 201, response.text
    return response.json()['id']


def ws_path(rid):
    return f'ws://127.0.0.1:8001/chat/rooms/{rid}/ws'


def signed(payload, key=SECRET, issued=None):
    signer = TimestampSigner(key)
    if issued is not None:
        signer.get_timestamp = lambda: issued
    return signer.sign(base64.b64encode(json.dumps(payload).encode())).decode()


def assert_ws_rejected(client, path, code=1008, **kwargs):
    with pytest.raises(WebSocketDisconnect) as caught:
        with client.websocket_connect(path, **kwargs):
            pass
    assert caught.value.code == code


def test_session_cookie_flags_and_korean_roundtrip(client):
    response = name(client)
    header = response.headers['set-cookie'].lower()
    assert 'guestbook_name=""' in header
    cookie = client.cookies.get(lab.COOKIE)
    body = TimestampSigner(SECRET).unsign(cookie)
    assert json.loads(base64.b64decode(body))['name'] == '바로'  # 암호화가 아님
    flags = response.headers.get_list('set-cookie')[-1].lower()
    assert 'httponly' in flags and 'samesite=lax' in flags and 'max-age=3600' in flags
    assert '바로님' in client.get('/').text
    assert 'href="/chat"' in client.get('/').text
    assert client.post('/entries', data={'message': '반가워요'}).status_code == 200
    assert '반가워요' in client.get('/').text


def test_secure_cookie_https(tmp_path):
    app = lab.create_lab_app(secret=SECRET, db_path=tmp_path/'https.db', origin='https://example.test')
    with TestClient(app, base_url='https://example.test', headers={'origin':'https://example.test'}) as c:
        assert 'secure' in name(c).headers.get_list('set-cookie')[-1]
        assert '바로님' in c.get('/').text


@pytest.mark.parametrize('cookie', ['garbage', signed({'name':'위조', 'sid':'a'*32}, key='wrong'), signed({'name':'만료', 'sid':'a'*32}, issued=1)])
def test_invalid_cookie_legacy_fallback_forbidden(client, cookie):
    client.cookies.set(lab.COOKIE, cookie)
    client.cookies.set('guestbook_name','admin')
    assert client.post('/entries', data={'message':'실패'}).status_code == 401
    assert client.get('/chat/rooms').status_code == 401
    assert_ws_rejected(client, ws_path(1))


def test_cookie_tampering(client):
    name(client)
    value = client.cookies.get(lab.COOKIE)
    payload, rest = value.split('.', 1)
    data = json.loads(base64.b64decode(payload)); data['name'] = '관리자'
    client.cookies.clear()
    client.cookies.set(lab.COOKIE, base64.b64encode(json.dumps(data).encode()).decode()+'.'+rest)
    assert client.post('/entries', data={'message':'실패'}).status_code == 401


def test_clear_and_replay_limitation(client):
    name(client)
    captured = client.cookies.get(lab.COOKIE)
    assert client.post('/session/clear', follow_redirects=False).status_code == 303
    assert client.get('/chat/rooms').status_code == 401
    # 서명 쿠키만으로는 서버 측 개별 폐기가 불가능하다는 한계를 명시적으로 검증.
    client.cookies.set(lab.COOKIE, captured)
    assert client.get('/chat/rooms').status_code == 200


def test_key_rotation_and_new_identity(tmp_path):
    path=tmp_path/'same.sqlite3'
    a=lab.create_lab_app(secret=SECRET, db_path=path, origin=ORIGIN, https_only=False)
    with TestClient(a, base_url=ORIGIN, headers={'origin':ORIGIN}) as c:
        name(c); old=c.cookies.get(lab.COOKIE); rid=room(c)
        name(c, '변경')
        assert c.get(f'/chat/rooms/{rid}/messages').status_code == 403
    b=lab.create_lab_app(secret='new-secret-'+'y'*40, db_path=path, origin=ORIGIN, https_only=False)
    with TestClient(b, base_url=ORIGIN, headers={'origin':ORIGIN}) as c:
        c.cookies.set(lab.COOKIE, old)
        assert c.get('/chat/rooms').status_code == 401


@pytest.mark.parametrize('origin', ['', 'null', 'https://evil.test', ORIGIN+'.evil.test'])
def test_cross_origin_http_and_ws(client, origin):
    name(client); rid=room(client)
    assert client.post('/session/clear', headers={'origin':origin}).status_code == 403
    assert client.post('/nickname', data={'name':'공격'}, headers={'origin':origin}).status_code == 403
    assert_ws_rejected(client, ws_path(rid), headers={'origin':origin})


def test_missing_origin(client):
    client.headers.pop('origin')
    assert client.post('/nickname', data={'name':'공격'}).status_code == 403
    assert_ws_rejected(client, ws_path(1))


@pytest.mark.parametrize('value', ['', ' '*3, '가'*21, '줄\n바꿈', '\x00'])
def test_invalid_nickname(client, value):
    assert client.post('/nickname', data={'name':value}).status_code == 422
    assert client.get('/chat/rooms').status_code == 401


def test_routes_assets_and_guestbook_escaping(client):
    name(client, '<b>바로</b>')
    text='<script>alert(1)</script>\n\'); DROP TABLE entries; --'
    assert client.post('/entries', data={'message':text}).status_code == 200
    assert '&lt;script&gt;' in client.get('/').text
    assert '&lt;b&gt;바로&lt;/b&gt;' in client.get('/').text
    page=client.get('/chat')
    assert page.status_code == 200
    assert "script-src 'self'" in page.headers['content-security-policy']
    js=client.get('/static/chat.js')
    assert js.status_code == 200 and 'li.textContent =' in js.text
    assert 'innerHTML' not in js.text
    assert client.get('/health').json() == {'status':'ok'}


@pytest.mark.parametrize('title', ['', ' '*3, '가'*41, '줄\n바꿈'])
def test_invalid_room_title(client, title):
    name(client)
    assert client.post('/chat/rooms',data={'title':title}).status_code == 422


def test_form_errors_and_room_not_found(client):
    name(client)
    assert client.post('/chat/rooms',json={'title':'a'}).status_code == 415
    assert client.post('/chat/rooms',content='title=a&title=b',headers={'content-type':'application/x-www-form-urlencoded'}).status_code == 422
    assert client.post('/chat/rooms',content='x'*17000,headers={'content-type':'application/x-www-form-urlencoded'}).status_code == 413
    assert client.post('/chat/rooms/999/join').status_code == 404
    assert client.get('/chat/rooms/999/messages').status_code == 404
    rid=room(client)
    for after in ['-1',str(2**64),'abc']:
        assert client.get(f'/chat/rooms/{rid}/messages',params={'after':after}).status_code == 422


@contextmanager
def visitor(app, primary):
    # 실제 서버처럼 여러 방문자를 동일한 ASGI 이벤트 루프에서 실행합니다.
    b = TestClient(app, base_url=ORIGIN, headers={'origin': ORIGIN})
    b.portal = primary.portal
    try:
        yield b
    finally:
        b.close()


def test_two_visitors_room_isolation_history_leave(client, app):
    name(client,'바로'); rid=room(client); other=room(client,'다른방')
    with visitor(app, client) as b:
        name(b,'손님')
        assert b.get(f'/chat/rooms/{rid}/messages').status_code == 403
        assert_ws_rejected(b, ws_path(rid))
        assert b.post(f'/chat/rooms/{rid}/join').status_code == 200
        assert b.post(f'/chat/rooms/{rid}/join').status_code == 200
        with client.websocket_connect(ws_path(rid)) as a_ws, b.websocket_connect(ws_path(rid)) as b_ws:
            a_ws.send_json({'message':'안녕'})
            a_msg=a_ws.receive_json(); b_msg=b_ws.receive_json()
            assert a_msg == b_msg and a_msg['name']=='바로'
            b_ws.send_json({'message':'반가워요'})
            assert a_ws.receive_json()==b_ws.receive_json()
        assert len(b.get(f'/chat/rooms/{rid}/messages').json())==2
        assert len(client.get(f'/chat/rooms/{rid}/messages',params={'after':a_msg['id']}).json())==1
        assert client.get(f'/chat/rooms/{other}/messages').json()==[]
        assert b.post(f'/chat/rooms/{rid}/leave').status_code == 200
        assert b.get(f'/chat/rooms/{rid}/messages').status_code == 403
        assert_ws_rejected(b,ws_path(rid))


def test_leave_closes_active_socket(client):
    name(client); rid=room(client)
    with client.websocket_connect(ws_path(rid)) as ws:
        assert client.post(f'/chat/rooms/{rid}/leave').status_code == 200
        with pytest.raises(WebSocketDisconnect) as caught: ws.receive_json()
        assert caught.value.code==1008


def test_clear_closes_active_socket(client):
    name(client); rid=room(client)
    with client.websocket_connect(ws_path(rid)) as ws:
        client.post('/session/clear')
        with pytest.raises(WebSocketDisconnect): ws.receive_json()


@pytest.mark.parametrize('raw', ['bad json', '[]', 'null', '{"message":123}', '{"message":""}', '{"message":"   "}', json.dumps({'message':'가'*1001}), '{"message":"a","name":"사칭"}'])
def test_bad_ws_payload_then_valid(client,raw):
    name(client); rid=room(client)
    with client.websocket_connect(ws_path(rid)) as ws:
        ws.send_text(raw)
        assert ws.receive_json()['type']=='error'
        ws.send_json({'message':'정상'})
        assert ws.receive_json()['message']=='정상'
    assert len(client.get(f'/chat/rooms/{rid}/messages').json())==1


def test_large_binary_and_rate_limit(client):
    name(client); rid=room(client)
    with client.websocket_connect(ws_path(rid)) as ws:
        ws.send_text('a'*8193)
        with pytest.raises(WebSocketDisconnect) as caught: ws.receive_json()
        assert caught.value.code==1009
    with client.websocket_connect(ws_path(rid)) as ws:
        ws.send_bytes(b'abc')
        with pytest.raises(WebSocketDisconnect) as caught: ws.receive_json()
        assert caught.value.code==1003
    with client.websocket_connect(ws_path(rid)) as ws:
        ws.send_json({'message':'a'}); assert ws.receive_json()['type']=='message'
        ws.send_json({'message':'b'}); assert ws.receive_json()['type']=='error'


def test_message_limit_and_atomic_room_limit(client, monkeypatch):
    name(client); rid=room(client)
    monkeypatch.setattr(lab,'MAX_MESSAGES',1)
    with client.websocket_connect(ws_path(rid)) as ws:
        ws.send_json({'message':'a'}); ws.receive_json()
    with client.websocket_connect(ws_path(rid)) as ws:
        ws.send_json({'message':'b'}); assert ws.receive_json()['type']=='error'
    monkeypatch.setattr(lab,'MAX_ROOMS',2)
    def create(_):
        return client.post('/chat/rooms',data={'title':'동시 요청'}).status_code
    with ThreadPoolExecutor(max_workers=4) as pool:
        statuses=list(pool.map(create, range(4)))
    assert statuses.count(201)==1 and statuses.count(409)==3


def test_member_limit(client, app, monkeypatch):
    name(client); rid=room(client)
    monkeypatch.setattr(lab,'MAX_MEMBERS',1)
    with visitor(app, client) as b:
        name(b,'다른사람')
        assert b.post(f'/chat/rooms/{rid}/join').status_code==409
    assert client.post(f'/chat/rooms/{rid}/join').status_code==200


def test_database_error_http_ws(client,monkeypatch):
    name(client); rid=room(client)
    with client.websocket_connect(ws_path(rid)) as ws:
        def broken(*args): raise sqlite3.OperationalError('private-detail')
        monkeypatch.setattr(lab,'persist',broken)
        ws.send_json({'message':'실패'})
        with pytest.raises(WebSocketDisconnect) as caught: ws.receive_json()
        assert caught.value.code==1011
    monkeypatch.setattr(lab,'rooms',broken)
    response=client.get('/chat/rooms')
    assert response.status_code==503 and 'private-detail' not in response.text


def test_lab_db_isolated_and_existing_rows_preserved(tmp_path,monkeypatch):
    original=tmp_path/'production.db'; sandbox=tmp_path/'lab.db'
    monkeypatch.setenv('GUESTBOOK_DB',str(original))
    main.save_entry(main.EntryInput(name='기존', message='유지'))
    old=original.read_bytes()
    app=lab.create_lab_app(secret=SECRET,db_path=sandbox,origin=ORIGIN,https_only=False)
    with TestClient(app,base_url=ORIGIN,headers={'origin':ORIGIN}) as c:
        name(c); room(c)
        c.post('/entries',data={'message':'실습'})
    assert original.read_bytes()==old
    with closing(sqlite3.connect(original)) as db:
        assert db.execute('SELECT message FROM entries').fetchall()==[('유지',)]
    # 재시작 후에도 실습 DB의 글·방·메시지를 조회 가능.
    with TestClient(app,base_url=ORIGIN,headers={'origin':ORIGIN}) as c:
        name(c); assert '실습' in c.get('/').text
        assert len(c.get('/chat/rooms').json())==1


def test_fail_closed_configuration(tmp_path,monkeypatch):
    for secret in ['', 'short']:
        with pytest.raises(ValueError): lab.create_lab_app(secret=secret,db_path=tmp_path/'x')
    with pytest.raises(ValueError): lab.create_lab_app(secret=SECRET,db_path=main.get_database_path())
    for origin in ['*','https://example.test/path','https://example.test?x=1']:
        with pytest.raises(ValueError): lab.create_lab_app(secret=SECRET,db_path=tmp_path/'x',origin=origin)
    monkeypatch.delenv('GUESTBOOK_SESSION_SECRET',raising=False)
    with pytest.raises(ValueError): lab.from_environment()


def test_nickname_change_closes_previous_socket(client):
    name(client); rid=room(client)
    with client.websocket_connect(ws_path(rid)) as ws:
        name(client,'새이름')
        with pytest.raises(WebSocketDisconnect): ws.receive_json()
    assert client.get(f'/chat/rooms/{rid}/messages').status_code==403


def test_open_websocket_expires(client):
    import time
    client.cookies.set(lab.COOKIE,signed({'name':'만료예정','sid':'e'*32},issued=int(time.time())-lab.SESSION_SECONDS+2))
    rid=room(client)
    with client.websocket_connect(ws_path(rid)) as ws:
        with pytest.raises(WebSocketDisconnect) as caught: ws.receive_json()
        assert caught.value.code==1008


def test_websocket_database_error_during_handshake(client,monkeypatch):
    name(client); rid=room(client)
    def broken(*args): raise sqlite3.OperationalError('private-detail')
    monkeypatch.setattr(lab,'is_member',broken)
    assert_ws_rejected(client,ws_path(rid),code=1011)


def test_message_persistence_restart_and_sql_payload(tmp_path):
    path=tmp_path/'persist.db'
    app=lab.create_lab_app(secret=SECRET,db_path=path,origin=ORIGIN,https_only=False)
    text="<script>alert('x')</script>'); DROP TABLE chat_messages; --"
    with TestClient(app,base_url=ORIGIN,headers={'origin':ORIGIN}) as c:
        name(c); rid=room(c); captured=c.cookies.get(lab.COOKIE)
        with c.websocket_connect(ws_path(rid)) as ws:
            ws.send_json({'message':text})
            assert ws.receive_json()['message']==text
    restarted=lab.create_lab_app(secret=SECRET,db_path=path,origin=ORIGIN,https_only=False)
    with TestClient(restarted,base_url=ORIGIN,headers={'origin':ORIGIN}) as c:
        c.cookies.set(lab.COOKIE,captured)
        rows=c.get(f'/chat/rooms/{rid}/messages').json()
        assert len(rows)==1 and rows[0]['message']==text


def test_concurrent_senders_keep_database_order(client,app):
    name(client,'A'); rid=room(client)
    with visitor(app,client) as b:
        name(b,'B'); b.post(f'/chat/rooms/{rid}/join')
        with client.websocket_connect(ws_path(rid)) as a_ws, b.websocket_connect(ws_path(rid)) as b_ws:
            with ThreadPoolExecutor(max_workers=2) as pool:
                list(pool.map(lambda pair: pair[0].send_json({'message':pair[1]}),[(a_ws,'A'),(b_ws,'B')]))
            a_events=[a_ws.receive_json(),a_ws.receive_json()]
            b_events=[b_ws.receive_json(),b_ws.receive_json()]
            assert a_events==b_events
            assert a_events[0]['id']<a_events[1]['id']
            assert {event['name'] for event in a_events}=={'A','B'}
