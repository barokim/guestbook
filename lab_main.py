"""격리된 익명 세션/공개 채팅 실습. 실행 방법은 SESSION_LAB.md 참고."""
import asyncio
import os
import sqlite3
import time
from contextlib import asynccontextmanager, closing
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from itsdangerous import TimestampSigner
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.middleware.sessions import SessionMiddleware

import main as guestbook

COOKIE = "guestbook_lab_session"
SESSION_SECONDS = 3600
MAX_ROOMS = 50
MAX_MESSAGES = 1000
MAX_MEMBERS = 100


class MessageInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)
    message: str = Field(min_length=1, max_length=1000)


def init_chat():
    with closing(guestbook.connect_db()) as db, db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS chat_rooms (
            id INTEGER PRIMARY KEY, title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 40));
        CREATE TABLE IF NOT EXISTS chat_members (
            room_id INTEGER NOT NULL REFERENCES chat_rooms(id), sid TEXT NOT NULL,
            PRIMARY KEY(room_id, sid));
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY, room_id INTEGER NOT NULL REFERENCES chat_rooms(id),
            name TEXT NOT NULL, message TEXT NOT NULL CHECK(length(message) BETWEEN 1 AND 1000),
            created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS chat_room_messages ON chat_messages(room_id, id);
        """)


def room_exists(db, room_id):
    if not db.execute("SELECT 1 FROM chat_rooms WHERE id=?", (room_id,)).fetchone():
        raise HTTPException(404, "채팅방이 없습니다.")


def is_member(room_id, sid):
    with closing(guestbook.connect_db()) as db:
        return bool(db.execute("SELECT 1 FROM chat_members WHERE room_id=? AND sid=?", (room_id, sid)).fetchone())


def rooms():
    with closing(guestbook.connect_db()) as db:
        return [dict(row) for row in db.execute("SELECT id,title FROM chat_rooms ORDER BY id DESC LIMIT 50")]


def make_room(title, sid):
    title = title.strip()
    if not 1 <= len(title) <= 40 or any(ord(c) < 32 or ord(c) == 127 for c in title):
        raise HTTPException(422, "방 제목은 제어문자 없이 1~40자로 입력해주세요.")
    with closing(guestbook.connect_db()) as db, db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT count(*) FROM chat_rooms").fetchone()[0] >= MAX_ROOMS:
            raise HTTPException(409, "실습용 방 개수 제한입니다.")
        cursor = db.execute("INSERT INTO chat_rooms(title) VALUES (?)", (title,))
        room_id = cursor.lastrowid
        db.execute("INSERT INTO chat_members VALUES (?,?)", (room_id, sid))
    return room_id


def membership(room_id, sid, join):
    with closing(guestbook.connect_db()) as db, db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        room_exists(db, room_id)
        if join:
            if db.execute("SELECT 1 FROM chat_members WHERE room_id=? AND sid=?", (room_id, sid)).fetchone():
                return
            if db.execute("SELECT count(*) FROM chat_members WHERE room_id=?", (room_id,)).fetchone()[0] >= MAX_MEMBERS:
                raise HTTPException(409, "실습용 참여자 제한입니다.")
            db.execute("INSERT INTO chat_members VALUES (?,?)", (room_id, sid))
        else:
            db.execute("DELETE FROM chat_members WHERE room_id=? AND sid=?", (room_id, sid))


def history(room_id, sid, after=0):
    with closing(guestbook.connect_db()) as db:
        room_exists(db, room_id)
        if not db.execute("SELECT 1 FROM chat_members WHERE room_id=? AND sid=?", (room_id, sid)).fetchone():
            raise HTTPException(403, "먼저 공개 방에 참여해주세요.")
        return [dict(row) for row in db.execute(
            "SELECT id,name,message,created_at FROM chat_messages WHERE room_id=? AND id>? ORDER BY id LIMIT 100",
            (room_id, after))]


def persist(room_id, sid, name, message):
    with closing(guestbook.connect_db()) as db, db:
        db.execute("BEGIN IMMEDIATE")
        if not db.execute("SELECT 1 FROM chat_members WHERE room_id=? AND sid=?", (room_id, sid)).fetchone():
            raise HTTPException(403, "참여가 종료되었습니다.")
        if db.execute("SELECT count(*) FROM chat_messages WHERE room_id=?", (room_id,)).fetchone()[0] >= MAX_MESSAGES:
            raise HTTPException(409, "실습용 메시지 제한입니다.")
        now = datetime.now(guestbook.KST).isoformat(timespec="seconds")
        cur = db.execute("INSERT INTO chat_messages(room_id,name,message,created_at) VALUES (?,?,?,?)", (room_id,name,message,now))
        return dict(id=cur.lastrowid, name=name, message=message, created_at=now)


class LabBoundary:
    """DB ContextVar는 동기 엔드포인트/스레드풀에도 전달됩니다."""
    def __init__(self, app, db_path, origin):
        self.app, self.db_path, self.origin = app, str(db_path), origin

    async def __call__(self, scope, receive, send):
        if scope["type"] not in {"http", "websocket"}:
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        # POST 폼에도 Origin을 요구합니다. 누락/null/외부 Origin은 거절합니다.
        if (scope["type"] == "websocket" or scope.get("method") not in {"GET", "HEAD", "OPTIONS"}) and headers.get(b"origin", b"").decode() != self.origin:
            if scope["type"] == "websocket":
                return await send({"type": "websocket.close", "code": 1008})
            return await JSONResponse({"detail": "동일 출처 요청만 허용합니다."}, status_code=403)(scope, receive, send)
        token = guestbook.DB_PATH_OVERRIDE.set(self.db_path)
        try:
            await self.app(scope, receive, send)
        finally:
            guestbook.DB_PATH_OVERRIDE.reset(token)


def create_lab_app(*, secret, db_path, origin="http://127.0.0.1:8001", https_only=True):
    from urllib.parse import urlsplit
    parts = urlsplit(origin)
    if parts.scheme not in {"http", "https"} or not parts.netloc or parts.path or parts.query or parts.fragment or parts.username:
        raise ValueError("GUESTBOOK_LAB_ORIGIN에는 경로 없는 http(s) 출처를 지정하세요.")
    if len(secret.encode()) < 32:
        raise ValueError("GUESTBOOK_SESSION_SECRET은 최소 32바이트의 무작위 비밀값이 필요합니다.")
    db_path = Path(db_path).expanduser().resolve()
    if db_path in {guestbook.get_database_path(), guestbook.BASE_DIR / "data/guestbook.sqlite3", guestbook.BASE_DIR / "data/preview.sqlite3"}:
        raise ValueError("실습 DB는 기존 방명록 DB와 다른 경로를 사용해야 합니다.")
    peers = {}  # room -> {WebSocket: sid}; 단일 프로세스 실습 전용
    locks = {}

    @asynccontextmanager
    async def lifespan(app):
        token = guestbook.DB_PATH_OVERRIDE.set(str(db_path))
        try:
            await run_in_threadpool(init_chat)
            yield
        finally:
            guestbook.DB_PATH_OVERRIDE.reset(token)

    app = FastAPI(title="익명 세션과 공개 채팅 실습", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.include_router(guestbook.app.router)
    app.mount("/static", guestbook.StaticFiles(directory=guestbook.BASE_DIR / "static"), name="lab-static")
    app.add_exception_handler(sqlite3.Error, guestbook.database_error)
    app.add_exception_handler(OSError, guestbook.database_error)
    app.add_middleware(SessionMiddleware, secret_key=secret, session_cookie=COOKIE,
                       max_age=SESSION_SECONDS, same_site="lax", https_only=https_only)
    app.add_middleware(LabBoundary, db_path=db_path, origin=origin)

    def identity(connection):
        name = guestbook.get_nickname(connection)
        sid = connection.session.get("sid")
        if not name or not isinstance(sid, str) or len(sid) != 32:
            raise HTTPException(401, "먼저 대화명을 선택해주세요. 본인 인증은 아닙니다.")
        return sid, name

    async def close_sid(sid, room_id=None):
        for rid, sockets in list(peers.items()):
            if room_id is not None and rid != room_id:
                continue
            async with locks[rid]:
                for ws, owner in list(sockets.items()):
                    if owner == sid:
                        sockets.pop(ws, None)
                        try:
                            await asyncio.wait_for(ws.close(code=1008), 2)
                        except (RuntimeError, OSError, asyncio.TimeoutError):
                            pass

    app.state.on_nickname_change = close_sid

    @app.post("/session/clear")
    async def clear(request: Request):
        sid = request.session.get("sid")
        if sid:
            await close_sid(sid)
        request.session.clear()
        return RedirectResponse("/", 303)

    @app.get("/chat", response_class=HTMLResponse)
    def chat_page():
        return HTMLResponse((guestbook.BASE_DIR / "templates/chat.html").read_text(), headers={
            "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

    @app.get("/chat/rooms")
    def list_rooms(request: Request):
        identity(request)
        return rooms()

    @app.post("/chat/rooms", status_code=201)
    async def create_room(request: Request):
        sid, _ = identity(request)
        fields = await guestbook.read_html_form(request, {"title"})
        return {"id": await run_in_threadpool(make_room, fields["title"], sid)}

    @app.post("/chat/rooms/{room_id}/join")
    async def join_room(room_id: int, request: Request):
        sid, _ = identity(request)
        await run_in_threadpool(membership, room_id, sid, True)
        return {"joined": True}

    @app.post("/chat/rooms/{room_id}/leave")
    async def leave_room(room_id: int, request: Request):
        sid, _ = identity(request)
        await run_in_threadpool(membership, room_id, sid, False)
        await close_sid(sid, room_id)
        return {"left": True}

    @app.get("/chat/rooms/{room_id}/messages")
    def messages(room_id: int, request: Request, after: int = Query(default=0, ge=0, le=2**63-1)):
        sid, _ = identity(request)
        return history(room_id, sid, after)

    @app.websocket("/chat/rooms/{room_id}/ws")
    async def chat(ws: WebSocket, room_id: int):
        try:
            sid, name = identity(ws)
            if not await run_in_threadpool(is_member, room_id, sid):
                raise HTTPException(403)
        except HTTPException:
            await ws.close(code=1008)
            return
        except (sqlite3.Error, OSError):
            guestbook.logger.exception("채팅 연결 DB 작업 실패")
            await ws.close(code=1011)
            return
        # 열린 연결도 서명 시점으로부터 최대 한 시간 후 종료합니다.
        _, issued = TimestampSigner(secret).unsign(ws.cookies[COOKIE], max_age=SESSION_SECONDS, return_timestamp=True)
        deadline = issued.timestamp() + SESSION_SECONDS
        lock = locks.setdefault(room_id, asyncio.Lock())
        sockets = peers.setdefault(room_id, {})
        await ws.accept()
        sockets[ws] = sid
        last_send = 0.0
        try:
            while True:
                remaining = deadline - time.time()
                if remaining <= 0:
                    await ws.close(code=1008)
                    return
                frame = await asyncio.wait_for(ws.receive(), remaining)
                if frame["type"] == "websocket.disconnect":
                    raise WebSocketDisconnect(frame.get("code", 1000))
                if "text" not in frame:
                    await ws.close(code=1003)
                    return
                raw = frame["text"]
                if len(raw.encode("utf-8")) > 8192:
                    await ws.close(code=1009)
                    return
                try:
                    payload = MessageInput.model_validate_json(raw)
                except ValidationError:
                    await ws.send_json({"type": "error", "detail": "message 문자열 1~1000자만 허용합니다."})
                    continue
                if time.monotonic() - last_send < 0.25:
                    await ws.send_json({"type": "error", "detail": "잠시 후 보내주세요."})
                    continue
                last_send = time.monotonic()
                async with lock:
                    event = await run_in_threadpool(persist, room_id, sid, name, payload.message)
                    for target, owner in list(sockets.items()):
                        if not await run_in_threadpool(is_member, room_id, owner):
                            continue
                        try:
                            await asyncio.wait_for(target.send_json({"type": "message", **event}), 2)
                        except (OSError, RuntimeError, WebSocketDisconnect, asyncio.TimeoutError):
                            sockets.pop(target, None)
        except asyncio.TimeoutError:
            await ws.close(code=1008)
        except WebSocketDisconnect:
            pass
        except HTTPException as error:
            await ws.send_json({"type": "error", "detail": error.detail})
            await ws.close(code=1008)
        except (sqlite3.Error, OSError):
            guestbook.logger.exception("채팅 DB 작업 실패")
            await ws.close(code=1011)
        finally:
            sockets.pop(ws, None)

    return app


def from_environment():
    secret = os.environ.get("GUESTBOOK_SESSION_SECRET", "")
    return create_lab_app(secret=secret,
        db_path=os.environ.get("GUESTBOOK_LAB_DB", str(guestbook.BASE_DIR / "data/session-lab.sqlite3")),
        origin=os.environ.get("GUESTBOOK_LAB_ORIGIN", "http://127.0.0.1:8001"),
        https_only=os.environ.get("GUESTBOOK_LAB_HTTPS_ONLY", "1") != "0")


# uvicorn lab_main:from_environment --factory; 비밀값 없는 import도 테스트에 활용 가능.
