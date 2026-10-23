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
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError

BASE_DIR = Path(__file__).resolve().parent
PAGE_SIZE = 10
MAX_ENTRIES = 1000
MAX_BODY_BYTES = 16384
KST = timezone(timedelta(hours=9))
# RENDER_SINGLE_FILE_V1: HTML/CSS를 파일 안에 포함한 배포본입니다.
PAGE = Template('<!doctype html>\n<html lang="ko">\n<head>\n  <meta charset="utf-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1">\n  <meta name="description" content="잠깐 들러, 작은 인사를 남기는 방명록입니다.">\n  <title>작은 방명록 — 당신의 한마디</title>\n  <link rel="stylesheet" href="/static/style.css">\n</head>\n<body>\n  <header class="topbar"><a class="brand" href="/"><span aria-hidden="true">✳</span> 작은 방명록</a><span class="top-note">만나서 반가워요</span></header>\n  <main>\n    <section class="intro" aria-labelledby="title">\n      <p class="eyebrow">A LITTLE HELLO</p>\n      <h1 id="title">당신의 한마디가<br>머무는 곳.</h1>\n      <p class="description">오늘의 기분도, 짧은 안부도 좋아요.<br>잠깐 들러 작은 흔적을 남겨주세요.</p>\n    </section>\n    $notice\n    <div class="layout">\n      <section class="compose" aria-labelledby="write-title">\n        <div class="section-heading"><h2 id="write-title">인사 남기기</h2><span aria-hidden="true">↗</span></div>\n        <p class="hint">다정한 한마디를 기다리고 있어요.</p>\n        <form method="post" action="/entries" accept-charset="UTF-8">\n          <label for="name">이름 <span>최대 20자</span></label>\n          <input id="name" name="name" maxlength="20" required autocomplete="nickname" placeholder="어떤 이름으로 남길까요?" value="$name">\n          <label for="message">남기고 싶은 말 <span>최대 1,000자</span></label>\n          <textarea id="message" name="message" maxlength="1000" rows="7" required placeholder="편하게 인사를 건네주세요.">$message</textarea>\n          <p class="privacy">작성한 이름과 내용은 모두에게 공개됩니다.<br>연락처 등 개인정보는 남기지 말아주세요.</p>\n          <button type="submit">방명록 남기기 <span aria-hidden="true">→</span></button>\n        </form>\n      </section>\n      <section id="entries" class="entries" aria-labelledby="entries-title">\n        <div class="section-heading"><h2 id="entries-title">남겨진 인사 <span class="count">$total</span></h2><span class="sort">최신순</span></div>\n        $entries\n        <nav class="pagination" aria-label="방명록 페이지">$navigation</nav>\n      </section>\n    </div>\n  </main>\n  <footer><span aria-hidden="true">✳</span> 작은 인사가 모여, 따뜻한 공간이 됩니다.</footer>\n</body>\n</html>\n')
STYLESHEET = ':root { color-scheme: light; --paper: #f7f6f0; --ink: #283d34; --green: #42644f; --muted: #767c72; --line: #dcded4; }\n* { box-sizing: border-box; }\nhtml { scroll-behavior: smooth; }\nbody { margin: 0; background: var(--paper); color: var(--ink); font-family: "Malgun Gothic", "Apple SD Gothic Neo", sans-serif; font-size: 15px; line-height: 1.7; }\na { color: inherit; text-decoration: none; }\na:hover { text-decoration: underline; }\n.topbar { max-width: 1120px; margin: auto; padding: 26px 40px; border-bottom: 1px solid var(--line); display: flex; justify-content: space-between; align-items: center; }\n.brand { font-size: 17px; font-weight: 700; letter-spacing: -.5px; }\n.brand span { margin-right: 9px; color: var(--green); font-size: 26px; vertical-align: middle; }\n.top-note, .hint, .sort, .privacy, label span { color: var(--muted); font-size: 12px; }\nmain { max-width: 1040px; padding: 0 32px; margin: auto; }\n.intro { padding: 66px 0 48px; }\n.eyebrow { font-size: 10px; letter-spacing: 3px; font-weight: 700; color: var(--green); margin: 0 0 18px; }\nh1 { font-size: clamp(36px, 5vw, 50px); line-height: 1.35; letter-spacing: -2.5px; margin: 0 0 20px; font-weight: 600; }\n.description { color: var(--muted); line-height: 1.9; font-size: 14px; }\n.layout { display: grid; grid-template-columns: 340px minmax(0, 1fr); gap: 64px; align-items: start; }\n.compose { background: #eeefe6; padding: 26px; border: 1px solid #e2e5d9; border-radius: 5px; }\n.section-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; }\nh2 { margin: 0; font-size: 18px; letter-spacing: -.6px; font-weight: 600; }\n.hint { margin: 7px 0 25px; }\nlabel { display: flex; justify-content: space-between; margin: 20px 0 8px; font-size: 13px; font-weight: 600; }\nlabel span { font-size: 10px; font-weight: 400; }\ninput, textarea, button { font: inherit; }\ninput, textarea { display: block; width: 100%; border: 1px solid #d9ddcf; border-radius: 3px; background: #fbfbf7; padding: 12px; font-size: 12px; color: var(--ink); }\ninput::placeholder, textarea::placeholder { color: #8a9084; }\ntextarea { resize: vertical; min-height: 150px; }\n:focus-visible { outline: 2px solid var(--green); outline-offset: 3px; }\n.privacy { font-size: 10px; line-height: 1.8; margin: 14px 0 20px; }\nbutton { display: flex; align-items: center; justify-content: space-between; width: 100%; background: var(--green); color: white; border: 0; border-radius: 3px; padding: 13px 16px; font-size: 13px; cursor: pointer; }\nbutton:hover { background: #304e3b; }\n.entries > .section-heading { padding: 5px 0 20px; border-bottom: 1px solid var(--line); }\n.count { color: var(--green); font-size: 13px; margin-left: 7px; }\n.entry { padding: 23px 0; border-bottom: 1px solid var(--line); }\n.entry-heading { display: flex; align-items: center; gap: 10px; }\n.avatar { flex: 0 0 30px; width: 30px; height: 30px; border-radius: 50%; background: #e5e9dc; color: var(--green); text-align: center; line-height: 30px; font-size: 12px; }\nh3 { margin: 0; font-size: 13px; font-weight: 600; overflow-wrap: anywhere; }\ntime { margin-left: auto; flex-shrink: 0; font-size: 10px; color: var(--muted); }\n.message { white-space: pre-wrap; overflow-wrap: anywhere; font-size: 13px; line-height: 1.9; margin: 13px 0 0; }\n.empty { text-align: center; padding: 70px 15px; color: var(--muted); }\n.empty > span { font-size: 32px; color: #9cab8e; }\n.empty h3 { margin-top: 14px; font-size: 15px; }\n.empty p { font-size: 12px; }\n.pagination { display: flex; justify-content: center; gap: 25px; font-size: 12px; padding: 24px 0; }\n.pagination span { color: var(--muted); }\n.notice { padding: 14px 18px; border: 1px solid var(--line); border-radius: 4px; margin: 0 0 24px; font-size: 13px; }\n.success { background: #e8efdf; }\n.error { background: #faeee7; color: #8a4333; }\nfooter { max-width: 1040px; margin: 65px auto 0; padding: 24px 32px; border-top: 1px solid var(--line); color: var(--muted); font-size: 11px; }\nfooter span { margin-right: 8px; color: var(--green); }\n@media (max-width: 760px) { .layout { grid-template-columns: 1fr; gap: 35px; } main { padding: 0 22px; } .topbar { padding: 18px 22px; } .top-note { font-size: 10px; } .intro { padding: 44px 0 30px; } .compose { padding: 22px; } footer { margin-top: 35px; padding: 22px; } time { font-size: 9px; } }\n@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }\n'


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
print("RENDER_SINGLE_FILE_V1: embedded HTML/CSS loaded", flush=True)


@app.get("/static/style.css", include_in_schema=False)
def stylesheet():
    return Response(STYLESHEET, media_type="text/css", headers={"X-Content-Type-Options": "nosniff"})


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
