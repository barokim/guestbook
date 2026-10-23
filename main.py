"""실행: python -m uvicorn main:app --reload (이 파일이 있는 폴더에서)."""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, ValidationError

BASE_DIR = Path(__file__).resolve().parent
PAGE_SIZE = 10
MAX_ENTRIES = 1000
MAX_BODY_BYTES = 16384
KST = timezone(timedelta(hours=9))
PAGE = Template((BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8"))


class EntryInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=1, max_length=20)
    message: str = Field(min_length=1, max_length=1000)


def connect_db():
    """연결을 작업마다 열고 closing으로 닫는다. 경로는 환경변수로 변경 가능."""
    path = Path(os.environ.get("GUESTBOOK_DB", str(BASE_DIR / "data" / "guestbook.sqlite3")))
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 20),
            message TEXT NOT NULL CHECK(length(trim(message)) BETWEEN 1 AND 1000),
            created_at TEXT NOT NULL
        )
    """)
    connection.commit()
    return connection


def render_page(page=1, error="", name="", message="", status_code=200, saved=False):
    with closing(connect_db()) as connection:
        total = connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        page = min(max(1, page), pages)
        records = connection.execute(
            "SELECT * FROM entries ORDER BY id DESC LIMIT ? OFFSET ?",
            (PAGE_SIZE, (page - 1) * PAGE_SIZE),
        ).fetchall()

    cards = []
    for entry in records:
        cards.append(
            '<article class="entry">'
            '<header class="entry-heading">'
            f'<span class="avatar" aria-hidden="true">{escape(entry["name"][0])}</span>'
            f'<h3>{escape(entry["name"])}</h3>'
            f'<time datetime="{escape(entry["created_at"])}">'
            f'{escape(datetime.fromisoformat(entry["created_at"]).strftime("%Y.%m.%d · %H:%M"))}'
            '</time></header>'
            f'<p class="message">{escape(entry["message"])}</p></article>'
        )

    if not cards:
        cards.append('<div class="empty"><span aria-hidden="true">✳</span>'
                     '<h3>아직은 빈 페이지예요.</h3><p>첫 번째 인사를 남겨주세요.</p></div>')
    navigation = []
    if page > 1:
        navigation.append(f'<a href="/?page={page - 1}#entries">← 이전</a>')
    navigation.append(f'<span aria-current="page">{page} / {pages}</span>')
    if page < pages:
        navigation.append(f'<a href="/?page={page + 1}#entries">다음 →</a>')

    notice = ""
    if error:
        notice = f'<p class="notice error" role="alert">{escape(error)}</p>'
    elif saved:
        notice = '<p class="notice success" role="status">인사를 남겼어요. 방문해 주셔서 감사합니다!</p>'

    return HTMLResponse(PAGE.substitute(
        total=total, entries="".join(cards), navigation="".join(navigation),
        notice=notice, name=escape(name, quote=True), message=escape(message),
    ), status_code=status_code, headers={
        "Content-Security-Policy": "default-src 'none'; style-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-store",
    })


def save_entry(entry):
    """건수 확인과 저장을 같은 트랜잭션으로 묶어 동시 요청의 상한 초과를 막는다."""
    with closing(connect_db()) as connection:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            count = connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            if count >= MAX_ENTRIES:
                return False
            connection.execute(
                "INSERT INTO entries (name, message, created_at) VALUES (?, ?, ?)",
                (entry.name, entry.message, datetime.now(KST).isoformat(timespec="seconds")),
            )
    return True


app = FastAPI(title="작은 방명록", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home(page: str = "1", saved: str = ""):
    # 거대한 정수 변환이나 잘못된 쿼리도 간단한 HTML 안내로 처리한다.
    if len(page) > 6 or not page.isascii() or not page.isdigit() or int(page) < 1:
        return render_page(error="페이지 번호는 1 이상의 정수로 입력해주세요.", status_code=422)
    return render_page(page=int(page), saved=(saved == "1"))


@app.post("/entries", response_class=HTMLResponse)
async def create_entry(request: Request):
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type != "application/x-www-form-urlencoded":
        return await run_in_threadpool(render_page, error="방명록의 작성 폼을 이용해주세요.", status_code=415)

    # stream으로 읽으며 제한하여 Content-Length가 없거나 잘못된 요청도 제한한다.
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_BODY_BYTES:
            return await run_in_threadpool(render_page, error="입력한 내용이 너무 큽니다.", status_code=413)
        body.extend(chunk)
    try:
        fields = parse_qs(body.decode("utf-8"), keep_blank_values=True, max_num_fields=2, errors="strict")
        if set(fields) != {"name", "message"} or any(len(values) != 1 for values in fields.values()):
            raise ValueError("invalid fields")
    except (UnicodeError, ValueError):
        return await run_in_threadpool(render_page, error="이름과 내용을 올바르게 입력해주세요.", status_code=422)

    name, message = fields["name"][0], fields["message"][0]
    try:
        entry = EntryInput(name=name, message=message)
    except ValidationError:
        return await run_in_threadpool(
            render_page, error="이름은 1~20자, 내용은 1~1,000자로 입력해주세요. 공백만 입력할 수 없습니다.",
            name=name[:20], message=message[:1000], status_code=422,
        )
    if not await run_in_threadpool(save_entry, entry):
        return await run_in_threadpool(
            render_page, error="방명록이 가득 찼습니다. 운영자에게 알려주세요.",
            name=entry.name, message=entry.message, status_code=409,
        )
    # 저장 뒤 GET으로 이동하여 새로고침으로 같은 POST가 재전송되는 것을 줄인다.
    return RedirectResponse("/?saved=1#entries", status_code=303)


@app.exception_handler(sqlite3.Error)
async def database_error(request: Request, error: sqlite3.Error):
    # DB가 고장 난 경우 DB를 다시 조회하는 render_page를 호출하지 않는다.
    return HTMLResponse(
        '<!doctype html><html lang="ko"><meta charset="utf-8"><title>잠시 후 다시 시도해주세요</title>'
        '<h1>방명록을 잠시 이용할 수 없습니다.</h1><p>잠시 후 다시 시도해주세요.</p><a href="/">돌아가기</a></html>',
        status_code=503, headers={"Retry-After": "5", "Cache-Control": "no-store"},
    )


@app.get("/health")
def health():
    with closing(connect_db()) as connection:
        connection.execute("SELECT 1 FROM entries LIMIT 1").fetchall()
    return {"status": "ok"}

