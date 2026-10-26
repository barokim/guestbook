# 서명 세션·공개 채팅 실습

2026-10-26 기준 `barokim/guestbook`의 `1f790ad1987511a47af6bc4f319a25152470da6e`에서 분기한 실습 패치입니다. 학습 일정(10/28~11/3)은 요청에 제시된 범위를 따릅니다.

## 기존 코드 분석

`POST /nickname`에서 1~20자 이름을 검사하고 URL 인코딩하여 `guestbook_name` 쿠키에 30일 저장합니다. 이후 GET 및 글 작성 시 디코딩·재검증한 이름을 사용합니다. `entries`에는 이름·본문·KST 작성 시각이 저장됩니다. HTML 이스케이프, SQL 매개변수 바인딩, 본문 크기 제한도 기존에 있습니다.

- URL 인코딩은 한글 전송을 위한 표현 변환이며 서명이나 암호화가 아닙니다. 올바른 길이의 다른 이름으로 쿠키를 직접 바꾸면 통과합니다.
- HttpOnly는 브라우저 JavaScript의 쿠키 읽기를 제한합니다. 쿠키 소유자가 직접 수정하거나 탈취 쿠키를 재사용하는 것을 막지 않습니다. XSS 자체나 XSS를 통한 같은 출처 요청도 막지 않습니다.
- SameSite=Lax는 일부 교차 사이트 요청에 쿠키를 보내지 않게 하는 보조 방어입니다. 사용자 신원이나 완전한 CSRF 방어를 제공하지 않습니다.
- 기존 Secure 설정은 요청 URL의 https 여부에 의존합니다. 역방향 프록시의 스킴 전달을 신뢰할 수 있게 구성해야 합니다.
- 이름의 중복·사칭을 막는 계정, 비밀번호 검증, 서버 세션 저장소가 없습니다.

## 변경 설계

`main:app`은 기존 닉네임 쿠키 흐름을 유지합니다. 별도 `lab_main:from_environment --factory`에서만 SessionMiddleware와 채팅을 활성화합니다. `render.yaml`, 기본 `requirements.txt`, `render-upload/`는 수정하지 않습니다. main에 병합하거나 기존 서비스를 실습 브랜치로 재배포하지 않습니다.

실습 쿠키 `guestbook_lab_session`에는 `{name, sid}`가 들어갑니다. `sid`는 UUID4 익명 식별자입니다. Starlette/itsdangerous가 타임스탬프와 서명을 검증한 뒤 `request.session`을 제공합니다. 기존 `guestbook_name`은 실습 앱에서 신뢰하거나 자동 이관하지 않으며, 대화명 선택 시 삭제합니다.

| 구분 | 저장 위치와 의미 | 한계 |
| --- | --- | --- |
| 기존 닉네임 쿠키 | 브라우저의 이름 문자열 | 방문자가 직접 바꿀 수 있음 |
| 이번 서명 세션 | 브라우저의 이름·익명 sid와 서명 | 서명키 없는 변조는 거절, 내용은 읽을 수 있음 |
| 서버 저장 세션(미구현) | 쿠키에는 불투명 ID, 서버에 세션 상태·만료·폐기 기록 | 공유 저장소와 수명 관리 필요 |
| 실제 인증(미구현) | 계정·자격 증명 또는 외부 인증 제공자로 신원 검증 | 서명 세션만 추가해서는 생기지 않음 |

서명은 암호화가 아닙니다. 비밀번호·토큰 등 비밀정보를 넣지 않습니다. 쿠키는 HttpOnly, SameSite=Lax, 경로 `/`, 수명 3,600초이고 Secure 기본값은 켜져 있습니다. 실습 의존성의 Starlette 1.10.0에서는 세션 변경 시 쿠키를 발급하므로 일반 조회만으로 만료가 연장되지 않습니다. 열린 WebSocket도 발급 시각+1시간이 지나면 닫습니다. 대화명을 바꾸면 새 sid를 발급하고 해당 프로세스의 이전 연결을 닫습니다.

`POST /session/clear`는 현재 브라우저 쿠키와 현재 연결을 정리합니다. **이미 복사된 쿠키의 서버 측 개별 폐기는 구현하지 않았습니다.** 복사본은 만료 전까지 재사용할 수 있습니다. 서명키 변경은 모든 기존 쿠키를 무효화합니다. 이 차이를 pytest에서 확인합니다.

실습 HTTP 변경 요청과 WebSocket 핸드셰이크에는 설정된 Origin의 정확한 일치를 요구합니다. 누락·null·다른 출처는 거절합니다. SameSite에만 의존하지 않는 교육용 CSRF 방어이며 Origin을 보내지 않는 CLI도 직접 헤더를 지정해야 합니다. 본인 인증이나 봇 차단 기능은 아닙니다.

## 채팅 범위

카카오톡의 방 단위 메시징을 학습할 수 있는 **익명 공개 그룹 채팅**입니다. 카카오톡 서비스와 연동하지 않습니다.

- 공개 방 목록·생성·참여·나가기, 참여자에게 WebSocket 실시간 전달
- SQLite의 `chat_rooms`, `chat_members`, `chat_messages`에 방·익명 참여 상태·메시지 저장
- 이력은 ID 오름차순 100개씩 `after` 커서로 조회하며, UI는 연결 이후 이력을 가져와 실시간 메시지와 ID로 중복 제거·정렬
- 이름은 클라이언트 메시지에서 받지 않고 서명된 세션에서 가져옴. 다른 이름 필드는 거절
- 방별 저장/전달 순서를 lock으로 직렬화, DB commit 이후 전송, `BEGIN IMMEDIATE`로 저장 상한을 원자적으로 검사
- HTML은 방명록에서 escape, 채팅 UI에서는 `textContent` 사용. SQL은 매개변수 바인딩
- 방 50개, 방당 참여 기록 100개·메시지 1,000개, 메시지 1~1,000자, 앱 수신 프레임 8,192바이트, 연결당 전송 간격 0.25초, 느린 전송 2초 제한
- 잘못된 JSON은 오류 이벤트 후 연결 유지, 바이너리는 1003, 큰 프레임은 1009, 참여·세션 만료는 1008, DB 장애는 1011. HTTP DB 장애는 기존 503 안내 사용

모든 방은 누구나 참여할 수 있고 새 참여자도 과거 이력을 볼 수 있습니다. `chat_members`는 방 참여 기록이지 서버 세션 저장소가 아닙니다. 실제 계정, 친구·초대·비공개 대화방, 읽음 표시, 첨부파일, 푸시 알림, 종단간 암호화, 신고/차단은 구현하지 않습니다.

실시간 연결 목록과 lock은 메모리에 있으므로 **workers=1 한 프로세스**에서만 검증합니다. 다중 worker/인스턴스에는 Redis 등의 브로커와 공유 세션/권한 설계가 필요합니다. 연결 종료 중 전달되지 않은 메시지는 재입장 시 DB 이력으로 보충하며 exactly-once 전달 보장은 없습니다. 연결별 속도 제한은 재연결로 우회할 수 있습니다. 만료된 sid의 참여 기록은 자동 청소하지 않아 상한에 도달할 수 있습니다. 실습 종료 후 실습 DB를 초기화하거나 후속 학습에서 만료·폐기를 구현하세요. SQLite는 실행 환경의 디스크 지속성을 바꾸지 않습니다.

## 코드 위치와 의존성

| 파일 | 변경 |
| --- | --- |
| `main.py` | 세션이 있는 요청만 서명 검증된 이름 사용, 이름 변경 시 새 sid, ContextVar로 요청별 DB 분리 |
| `templates/index.html` | 실습 앱에서만 채팅 이동 링크 표시 |
| `lab_main.py` | 앱 팩터리, 실습 DB 격리, 쿠키·Origin 설정, 방 API, WebSocket, 저장 상한 |
| `templates/chat.html`, `static/chat.js` | 공개 채팅 화면과 실시간/이력 처리 |
| `requirements-lab.txt` | 기존 개발 의존성 + itsdangerous 2.2.0, websockets 16.1.1, 검증한 Starlette 1.10.0 고정 |
| `test_app.py` | 기존 닉네임 선택 흐름에 맞게 회귀 테스트 수정 |
| `test_lab.py`, `test_lab_network.py` | 세션·예외·동시 요청·실제 네트워크 테스트 |

세션 기능만 살펴볼 때는 `main.py`의 세션 분기와 `create_lab_app`의 `SessionMiddleware` 부분부터 읽으세요. 채팅은 별도 확장입니다. 별도 가상환경에 `requirements-lab.txt`를 설치합니다. 기존 배포 가상환경에는 설치하지 않습니다.

## 실행 (Windows PowerShell)

저장소 폴더에서 실행합니다. 기존 개발 서버와 다른 포트를 사용하세요.

```powershell
git fetch origin
git switch lab/signed-session-chat
py -3.12 -m venv .venv-lab
.\.venv-lab\Scripts\Activate.ps1
python -m pip install -r requirements-lab.txt
$env:GUESTBOOK_SESSION_SECRET = (python -c "import secrets; print(secrets.token_urlsafe(48))")
$env:GUESTBOOK_LAB_DB = "$PWD\data\session-lab.sqlite3"
$env:GUESTBOOK_LAB_ORIGIN = "http://127.0.0.1:8001"
$env:GUESTBOOK_LAB_HTTPS_ONLY = "0"
python -m uvicorn lab_main:from_environment --factory --host 127.0.0.1 --port 8001 --workers 1 --ws-max-size 8192
```

## 실행 (bash)

```bash
git fetch origin
git switch lab/signed-session-chat
python3.12 -m venv .venv-lab
source .venv-lab/bin/activate
python -m pip install -r requirements-lab.txt
export GUESTBOOK_SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export GUESTBOOK_LAB_DB="$PWD/data/session-lab.sqlite3"
export GUESTBOOK_LAB_ORIGIN=http://127.0.0.1:8001
export GUESTBOOK_LAB_HTTPS_ONLY=0
python -m uvicorn lab_main:from_environment --factory --host 127.0.0.1 --port 8001 --workers 1 --ws-max-size 8192
```

`http://127.0.0.1:8001/`에서 대화명을 선택하고 채팅 링크를 누릅니다. 다른 브라우저/시크릿 창으로 두 번째 방문자를 열어 방에 참여하세요. `localhost`와 `127.0.0.1`을 섞으면 Origin·쿠키가 달라지므로 같은 주소를 사용합니다.

HTTP에서 Secure를 끄는 설정은 로컬 실습용입니다. 별도 HTTPS 실습 환경에서는 Origin을 실제 https 출처로 지정하고 `GUESTBOOK_LAB_HTTPS_ONLY=1`로 설정합니다. 32바이트 미만 키는 시작 시 거절됩니다. 재시작 후 쿠키를 유지하려면 같은 비밀키를 환경변수로 안전하게 공급하세요. 키를 소스·커밋·로그에 넣지 않습니다.

실습 DB는 기본 `data/session-lab.sqlite3`입니다. 기존 `GUESTBOOK_DB`는 변경하지 않고 ContextVar로 실습 요청만 다른 DB를 사용합니다. 기존 DB와 같은 경로를 지정하면 시작을 거절합니다. 기존 데이터가 필요하면 **원본이 아닌 복사본**을 실습 DB로 지정하세요. 기존 entries 스키마는 바꾸지 않고 채팅 테이블만 추가합니다. 실습을 중단하면 기존 `python -m uvicorn main:app ...` 실행으로 돌아갈 수 있습니다.

## API 예시

| 경로 | 의미 |
| --- | --- |
| `POST /nickname` (`name` 폼) | 익명 세션 시작/이름 변경 |
| `POST /session/clear` | 현재 세션 쿠키 지우기 |
| `GET /chat` | 채팅 UI |
| `GET /chat/rooms` | 공개 방 목록 |
| `POST /chat/rooms` (`title` 폼) | 방 생성 및 생성자 참여 |
| `POST /chat/rooms/{id}/join`, `/leave` | 참여/나가기 |
| `GET /chat/rooms/{id}/messages?after=0` | 참여자의 이력 조회 |
| `WS /chat/rooms/{id}/ws` | 세션 쿠키+Origin으로 연결, `{"message":"안녕"}` 전송 |

## 검증

```bash
python -m pytest -q --tb=short
```

테스트는 임시 디렉터리의 DB만 사용합니다. `test_lab_network.py`는 임시 포트로 Uvicorn 하위 프로세스를 띄우고 종료합니다. 세부 결과와 검증 한계는 `SESSION_LAB_VERIFICATION.md`를 참고하세요.

참고: [Starlette SessionMiddleware](https://www.starlette.io/middleware/#sessionmiddleware), [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/), [WebSocket 테스트](https://fastapi.tiangolo.com/advanced/testing-websockets/).
