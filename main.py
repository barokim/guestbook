"""실행: python -m uvicorn main:app --reload (이 파일이 있는 폴더에서)."""

import logging
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import parse_qs, quote, unquote

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

BASE_DIR = Path(__file__).resolve().parent
PAGE_SIZE = 10
MAX_ENTRIES = 1000
MAX_BODY_BYTES = 16384
KST = timezone(timedelta(hours=9))
PAGE = Template((BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8"))

# [변경] 대화명만 쿠키에 기억합니다. 회원가입이나 본인 인증 기능은 아닙니다.
NICKNAME_COOKIE = "guestbook_name"
logger = logging.getLogger("guestbook")
NICKNAME_DIALOG = Template('''
<div class="nickname-overlay">
  <section class="nickname-dialog" role="dialog" aria-modal="true" aria-labelledby="nickname-title" aria-describedby="nickname-help">
    <span class="nickname-sun" aria-hidden="true">✳</span>
    <p class="eyebrow">WELCOME TO THE SHORE</p>
    <h2 id="nickname-title">대화명을 입력해주세요</h2>
    <p id="nickname-help">방명록에 남길 이름을 알려주세요.</p>
    $error
    <form method="post" action="/nickname" accept-charset="UTF-8">
      <label for="nickname">대화명 <span>1~20자</span></label>
      <input id="nickname" name="name" value="$value" maxlength="20" required autofocus autocomplete="nickname">
      <p class="privacy">대화명은 작성한 글과 함께 공개됩니다.</p>
      <button type="submit">이 이름으로 들어가기 <span aria-hidden="true">→</span></button>
    </form>
    $cancel
  </section>
</div>
''')


class NicknameInput(BaseModel):
    # [변경] 쿠키와 폼 입력 모두 같은 규칙으로 검증합니다.
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=20)

    @field_validator("name")
    @classmethod
    def no_control_characters(cls, value: str) -> str:
        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError("대화명에는 줄바꿈이나 제어문자를 넣을 수 없습니다.")
        return value


def get_nickname(request: Request) -> str:
    """[변경] 한글 쿠키를 복원하고, 없거나 잘못된 쿠키는 첫 방문으로 처리."""
    raw = request.cookies.get(NICKNAME_COOKIE, "")
    if not raw or len(raw) > 300:
        return ""
    try:
        return NicknameInput(name=unquote(raw, encoding="utf-8", errors="strict")).name
    except (UnicodeError, ValidationError):
        return ""


class EntryInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=1, max_length=20)
    message: str = Field(min_length=1, max_length=1000)


def get_database_path() -> Path:
    """[변경] 실행 작업 폴더가 바뀌어도 같은 DB 파일을 사용하도록 경로를 고정."""
    configured = os.environ.get("GUESTBOOK_DB", "").strip()
    path = Path(configured).expanduser() if configured else BASE_DIR / "data" / "guestbook.sqlite3"
    if not path.is_absolute():
        path = BASE_DIR / path
    # 경로를 고정해도 Render Free의 임시 디스크가 영구 디스크로 바뀌지는 않습니다.
    return path.resolve()


def connect_db():
    """연결을 작업마다 열고 closing으로 닫는다. 테이블은 기존 entries 하나만 사용."""
    path = get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    try:
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
    except sqlite3.Error:
        # [변경] 초기화 실패 시에도 DB 연결을 닫고 오류를 상위 처리기로 전달합니다.
        connection.close()
        raise
    return connection


def render_page(page=1, error="", name="", message="", status_code=200, saved=False,
                show_nickname=False, nickname_error="", nickname_value=None):
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

    # [변경] JS 없이 HTML 폼을 팝업처럼 표시합니다. 뒤 화면은 inert로 조작을 막습니다.
    dialog = ""
    if show_nickname:
        dialog = NICKNAME_DIALOG.substitute(
            value=escape(name if nickname_value is None else nickname_value, quote=True),
            error=f'<p class="notice error" role="alert">{escape(nickname_error)}</p>' if nickname_error else "",
            cancel='<a class="nickname-cancel" href="/">취소하고 돌아가기</a>' if name else "",
        )

    return HTMLResponse(PAGE.substitute(
        total=total, entries="".join(cards), navigation="".join(navigation),
        notice=notice, name=escape(name, quote=True), message=escape(message),
        nickname_dialog=dialog, background_inert="inert" if show_nickname else "",
        greeting=escape(f"{name}님, 반가워요" if name else "만나서 반가워요"),
    ), status_code=status_code, headers={
        "Content-Security-Policy": "default-src 'none'; style-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-store",
    })


def save_entry(entry):
    """건수 확인과 저장을 같은 트랜잭션으로 묶어 동시 요청의 상한 초과를 막는다."""
    with closing(connect_db()) as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            count = connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            if count >= MAX_ENTRIES:
                connection.rollback()
                return False
            connection.execute(
                "INSERT INTO entries (name, message, created_at) VALUES (?, ?, ?)",
                (entry.name, entry.message, datetime.now(KST).isoformat(timespec="seconds")),
            )
            # [변경] commit이 성공한 경우에만 저장 완료로 응답합니다.
            # 기존 with connection도 자동 commit했지만 학습·오류 추적을 위해 명시했습니다.
            connection.commit()
        except sqlite3.Error:
            connection.rollback()
            raise
    return True


app = FastAPI(title="작은 방명록", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home(request: Request, page: str = "1", saved: str = ""):
    name = get_nickname(request)
    if not name:
        return render_page(show_nickname=True)
    # 거대한 정수 변환이나 잘못된 쿼리도 간단한 HTML 안내로 처리한다.
    if len(page) > 6 or not page.isascii() or not page.isdigit() or int(page) < 1:
        return render_page(name=name, error="페이지 번호는 1 이상의 정수로 입력해주세요.", status_code=422)
    return render_page(name=name, page=int(page), saved=(saved == "1"))


async def read_html_form(request: Request, field_names: set[str]) -> dict[str, str]:
    """[변경] 대화명 폼과 글 작성 폼에 크기·인코딩·중복 필드 검사를 공통 적용."""
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type != "application/x-www-form-urlencoded":
        raise HTTPException(status_code=415, detail="화면의 입력 폼을 이용해주세요.")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_BODY_BYTES:
            raise HTTPException(status_code=413, detail="입력한 내용이 너무 큽니다.")
        body.extend(chunk)
    try:
        fields = parse_qs(body.decode("utf-8"), keep_blank_values=True,
                          max_num_fields=len(field_names), errors="strict")
        if set(fields) != field_names or any(len(values) != 1 for values in fields.values()):
            raise ValueError("invalid fields")
    except (UnicodeError, ValueError) as error:
        raise HTTPException(status_code=422, detail="입력 항목을 올바르게 작성해주세요.") from error
    return {key: values[0] for key, values in fields.items()}


@app.get("/nickname", response_class=HTMLResponse)
def nickname_form(request: Request):
    # [변경] 기존 방문자도 '변경' 링크로 대화명을 다시 선택할 수 있습니다.
    return render_page(name=get_nickname(request), show_nickname=True)


@app.post("/nickname", response_class=HTMLResponse)
async def set_nickname(request: Request):
    current_name = get_nickname(request)
    fields = {}
    try:
        fields = await read_html_form(request, {"name"})
        name = NicknameInput(**fields).name
    except (HTTPException, ValidationError) as error:
        message = str(error.detail) if isinstance(error, HTTPException) else "대화명은 앞뒤 공백을 제외하고 1~20자로 입력해주세요. 공백만 입력하거나 줄바꿈을 넣을 수 없습니다."
        return await run_in_threadpool(
            render_page, name=current_name, show_nickname=True, nickname_error=message,
            nickname_value=fields.get("name", "")[:20],
            status_code=error.status_code if isinstance(error, HTTPException) else 422,
        )
    response = RedirectResponse("/", status_code=303)
    # [변경] 한글을 URL 인코딩한 쿠키로 30일 기억합니다. JS에서는 읽을 수 없습니다.
    response.set_cookie(NICKNAME_COOKIE, quote(name, safe=""), max_age=30 * 24 * 60 * 60,
                        httponly=True, secure=request.url.scheme == "https", samesite="lax", path="/")
    return response


@app.post("/entries", response_class=HTMLResponse)
async def create_entry(request: Request):
    # [변경] 이름은 처음 입력한 쿠키에서 가져옵니다. 글 작성 시의 임의 이름은 받지 않습니다.
    name = get_nickname(request)
    if not name:
        return await run_in_threadpool(render_page, show_nickname=True,
                                        nickname_error="먼저 대화명을 입력해주세요.", status_code=401)
    try:
        fields = await read_html_form(request, {"message"})
    except HTTPException as error:
        return await run_in_threadpool(render_page, name=name, error=str(error.detail), status_code=error.status_code)
    message = fields["message"]
    try:
        entry = EntryInput(name=name, message=message)
    except ValidationError:
        return await run_in_threadpool(
            render_page, error="내용은 1~1,000자로 입력해주세요. 공백만 입력할 수 없습니다.",
            name=name, message=message[:1000], status_code=422,
        )
    if not await run_in_threadpool(save_entry, entry):
        return await run_in_threadpool(
            render_page, error="방명록이 가득 찼습니다. 운영자에게 알려주세요.",
            name=entry.name, message=entry.message, status_code=409,
        )
    # 저장 뒤 GET으로 이동하여 새로고침으로 같은 POST가 재전송되는 것을 줄인다.
    return RedirectResponse("/?saved=1#entries", status_code=303)


@app.exception_handler(sqlite3.Error)
@app.exception_handler(OSError)
async def database_error(request: Request, error: Exception):
    # [변경] 저장 실패는 로그와 503으로 알립니다. 사용자에게 저장 성공을 안내하지 않습니다.
    logger.error("방명록 DB/파일 작업 실패", exc_info=error)
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

def health():
    with closing(connect_db()) as connection:
        connection.execute("SELECT 1 FROM entries LIMIT 1").fetchall()
    return {"status": "ok"}
