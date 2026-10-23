"""실행: python -m pytest -q -p no:cacheprovider test_app.py"""

import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GUESTBOOK_DB", str(tmp_path / "test.sqlite3"))
    with TestClient(main.app) as test_client:
        yield test_client


def test_empty_page_and_assets(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "아직은 빈 페이지예요" in response.text
    assert '<html lang="ko">' in response.text
    assert "<script" not in response.text
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}


def test_create_redirect_and_persist(client):
    response = client.post("/entries", data={"name": "  민수  ", "message": " 반가워요!\n좋은 하루! "}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/?saved=1#entries"
    with TestClient(main.app) as another_client:
        page = another_client.get("/").text
    assert "반가워요!\n좋은 하루!" in page
    with main.closing(main.connect_db()) as connection:
        row = connection.execute("SELECT * FROM entries").fetchone()
        assert row["name"] == "민수"
        assert row["created_at"].endswith("+09:00")
        # 내부 자동 증가 테이블도 만들지 않는, 단일 테이블 구조.
        tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        assert [row[0] for row in tables] == ["entries"]


@pytest.mark.parametrize("data", [
    {"name": "", "message": "내용"},
    {"name": "   ", "message": "내용"},
    {"name": "민수", "message": "\n\t "},
    {"name": "가" * 21, "message": "내용"},
    {"name": "민수", "message": "가" * 1001},
    {"name": "민수"},
])
def test_reject_invalid_fields(client, data):
    response = client.post("/entries", data=data)
    assert response.status_code == 422
    assert "role=\"alert\"" in response.text
    with main.closing(main.connect_db()) as connection:
        assert connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0] == 0


def test_max_lengths_accepted(client):
    response = client.post("/entries", data={"name": "가" * 20, "message": "나" * 1000}, follow_redirects=False)
    assert response.status_code == 303


def test_escape_html_and_parameterized_sql(client):
    message = "<script>alert('x')</script>\n'); DROP TABLE entries; --"
    client.post("/entries", data={"name": '<b>이름</b>', "message": message})
    page = client.get("/").text
    assert "<script>" not in page
    assert "&lt;script&gt;" in page
    assert "&lt;b&gt;이름&lt;/b&gt;" in page
    with main.closing(main.connect_db()) as connection:
        assert connection.execute("SELECT message FROM entries").fetchone()[0] == message


def test_invalid_form_preserves_escaped_input(client):
    response = client.post("/entries", data={"name": "", "message": "</textarea><script>x</script>"})
    assert response.status_code == 422
    assert "&lt;/textarea&gt;" in response.text
    assert "<script>" not in response.text


def test_latest_first_and_pagination(client):
    for index in range(11):
        client.post("/entries", data={"name": "손님", "message": f"게시글-{index:02}"})
    first = client.get("/").text
    second = client.get("/?page=2").text
    assert "게시글-10" in first and "게시글-00" not in first
    assert first.index("게시글-10") < first.index("게시글-09")
    assert "게시글-00" in second and "게시글-10" not in second
    assert client.get("/?page=999999").text == second


@pytest.mark.parametrize("page", ["0", "-1", "abc", "1.5", "9" * 5000, "²"])
def test_invalid_page_is_html(client, page):
    response = client.get("/", params={"page": page})
    assert response.status_code == 422
    assert "페이지 번호" in response.text


@pytest.mark.parametrize("body", ["name=a&name=b&message=c", "name=a&message=b&extra=c", "name=%FF&message=a"])
def test_malformed_form(client, body):
    response = client.post("/entries", content=body, headers={"content-type": "application/x-www-form-urlencoded"})
    assert response.status_code == 422


def test_request_size_and_media_type(client):
    assert client.post("/entries", json={"name": "민수", "message": "안녕"}).status_code == 415
    response = client.post("/entries", content="x" * (main.MAX_BODY_BYTES + 1), headers={"content-type": "application/x-www-form-urlencoded"})
    assert response.status_code == 413


def test_atomic_storage_limit(client, monkeypatch):
    monkeypatch.setattr(main, "MAX_ENTRIES", 2)
    client.get("/health")
    entry = main.EntryInput(name="손님", message="동시 작성")
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(main.save_entry, [entry] * 4))
    assert sum(results) == 2
    assert client.post("/entries", data={"name": "손님", "message": "추가"}).status_code == 409


def test_database_failure_returns_recoverable_page(client, monkeypatch):
    def broken_connection():
        raise sqlite3.OperationalError("private filesystem detail")
    monkeypatch.setattr(main, "connect_db", broken_connection)
    response = client.get("/")
    assert response.status_code == 503
    assert "private filesystem detail" not in response.text
    assert response.headers["retry-after"] == "5"
