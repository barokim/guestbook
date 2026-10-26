"""실제 Uvicorn TCP 연결에서도 두 방문자의 메시지 전달을 검증합니다."""
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from websockets.sync.client import connect


@pytest.fixture
def live_server(tmp_path):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    origin = f'http://127.0.0.1:{port}'
    env = dict(os.environ, GUESTBOOK_SESSION_SECRET='network-test-only-'+'x'*40,
               GUESTBOOK_LAB_DB=str(tmp_path/'network.sqlite3'), GUESTBOOK_LAB_ORIGIN=origin,
               GUESTBOOK_LAB_HTTPS_ONLY='0')
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'lab_main:from_environment',
        '--factory', '--host', '127.0.0.1', '--port', str(port), '--workers', '1',
        '--ws-max-size', '8192'], cwd=Path(__file__).parent, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        with httpx.Client(base_url=origin, trust_env=False, timeout=1) as c:
            for _ in range(100):
                if process.poll() is not None:
                    pytest.fail('실습 서버 시작 실패')
                try:
                    if c.get('/health').status_code==200: break
                except httpx.TransportError:
                    time.sleep(.05)
            else: pytest.fail('실습 서버 시작 시간 초과')
        yield origin
    finally:
        process.terminate()
        try: process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait(timeout=5)


def test_real_uvicorn_two_visitors(live_server):
    origin=live_server
    with httpx.Client(base_url=origin,headers={'origin':origin},trust_env=False) as a, httpx.Client(base_url=origin,headers={'origin':origin},trust_env=False) as b:
        assert a.post('/nickname',data={'name':'바로'}).status_code==303
        assert b.post('/nickname',data={'name':'손님'}).status_code==303
        rid=a.post('/chat/rooms',data={'title':'실제 연결'}).json()['id']
        assert b.post(f'/chat/rooms/{rid}/join').status_code==200
        url=origin.replace('http:','ws:')+f'/chat/rooms/{rid}/ws'
        def cookie(c): return '; '.join(f'{key}={value}' for key,value in c.cookies.items())
        with connect(url,origin=origin,additional_headers={'Cookie':cookie(a)},proxy=None,open_timeout=3) as aw, connect(url,origin=origin,additional_headers={'Cookie':cookie(b)},proxy=None,open_timeout=3) as bw:
            aw.send(json.dumps({'message':'실시간 안녕'}))
            first=json.loads(aw.recv(timeout=3)); assert first==json.loads(bw.recv(timeout=3))
            bw.send(json.dumps({'message':'실시간 응답'}))
            second=json.loads(aw.recv(timeout=3)); assert second==json.loads(bw.recv(timeout=3))
            assert first['name']=='바로' and second['name']=='손님'
        assert len(a.get(f'/chat/rooms/{rid}/messages').json())==2


def test_real_uvicorn_cross_origin(live_server):
    from websockets.exceptions import InvalidStatus
    origin=live_server
    with httpx.Client(base_url=origin,trust_env=False) as c:
        assert c.post('/nickname',data={'name':'공격'},headers={'origin':'https://evil.test'}).status_code==403
    with pytest.raises(InvalidStatus) as caught:
        with connect(origin.replace('http:','ws:')+'/chat/rooms/1/ws',origin='https://evil.test',proxy=None,open_timeout=3):
            pass
    assert caught.value.response.status_code==403
