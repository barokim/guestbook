# 검증 결과

## Render 화면 파일 누락에 대한 추가 검증

2026-10-23: `templates/index.html` 누락이 반복되어 `prepare_render.py`로 HTML/CSS를 포함한 `render-upload/main.py`를 생성했습니다. 새 외부 패키지는 추가하지 않았습니다.

`render-upload` 작업 디렉터리에 templates/static 폴더가 모두 없음을 확인한 뒤, 해당 디렉터리의 main 모듈을 먼저 불러오고 기존 test_app.py를 importlib 모드로 실행했습니다. 결과는 **24 passed, 2 warnings**입니다. 경고는 pytest의 이미 불러온 anyio 재작성 안내와 기존 Starlette/httpx 사용 중단 예정 안내입니다.

로컬에서 화면·CSS·저장·검증·페이지 처리·동시 저장 상한을 확인했습니다. 실제 GitHub 파일 교체와 Render 배포는 수행하지 않았습니다. 새 배포본이 실행되면 로그에 `RENDER_SINGLE_FILE_V1: embedded HTML/CSS loaded`가 출력됩니다. 원본 학습용 main.py와 HTML/CSS는 유지했습니다.

확인일: 2026-10-23 (한국 시간 기준).

## 환경

- Windows, Python 3.12.14
- FastAPI 0.150.0, Pydantic 2.14.1, Uvicorn 0.54.0
- pytest 9.1.1, httpx 0.28.1
- 기존 `C:\AIO4\.venv`를 사용했습니다. 추가 패키지를 설치하지 않았습니다.

## 자동 검사

실행 위치: `C:\AIO4\Day1-Day8`

```powershell
..\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider test_app.py
```

결과: **24 passed, 1 warning**.

검사 내용:

- 빈 목록·한글 HTML·CSS·상태 확인 경로.
- POST 후 303 이동, 이름 공백 정리, 한글·여러 줄 내용 보존, 한국 시간 저장.
- 다른 클라이언트에서 같은 SQLite 파일의 글 조회.
- 업무 테이블이 `entries` 하나임을 실제 SQLite 메타데이터로 확인.
- 공백·누락·길이 초과의 거절, 최대 길이의 정상 저장.
- HTML 태그의 문자 표시, SQL 구문을 포함한 입력의 안전한 저장.
- 검증 실패 시 입력 보존과 HTML 이스케이프.
- 최신순, 10개 단위 페이지 조회, 마지막 페이지를 넘은 요청 처리.
- 잘못된 페이지 번호·폼 구조·인코딩·본문 크기·Content-Type의 거절.
- 동시 저장 4건에서 상한 2건을 넘지 않는 트랜잭션 검사.
- DB 장애 시 503 안내와 내부 오류 상세 비공개.

경고는 현재 설치된 Starlette TestClient가 httpx 사용 중단 예정을 안내하는 내용입니다. 현재 검사는 모두 통과했습니다. 새 의존성은 사용자와 상의하기 전 추가하지 않는 규칙에 따라 httpx2를 설치하거나 버전을 임의 변경하지 않았습니다.

## 실제 서버 HTTP 확인

`127.0.0.1:8765`에서 Uvicorn을 띄우고 httpx로 실제 네트워크 요청을 보냈습니다. TestClient 검사와 별도로 확인했습니다.

- GET `/`: 200, 빈 목록 안내 확인.
- POST `/entries`: 한글·줄바꿈 글 저장, 303 응답 확인.
- GET `/`: 저장한 한글·줄바꿈 내용 확인.
- GET `/static/style.css`: 200.
- GET `/health`: `{"status":"ok"}`.
- 서버 프로세스를 종료하고 같은 SQLite 파일 경로로 다시 시작한 뒤 글 보존 확인.

서버 검사 DB는 `data/preview.sqlite3`입니다. 실제 기본 방명록 파일 `data/guestbook.sqlite3`에 검사 글을 넣지 않았습니다. 검사용 서버는 확인 후 종료했습니다.

## 확인하지 않은 범위

- 연결 가능한 브라우저 목록이 비어 있어 PC·모바일의 실제 렌더링과 시각 검수는 수행하지 못했습니다. 반응형 CSS와 HTML 폼 구조는 준비되어 있습니다.
- Render 계정 생성·소스 업로드·공개 배포·실제 무료 사용량은 확인하지 않았습니다. 무료 요금제 조건은 공식 문서를 확인하여 `DEPLOYMENT.md`에 기록했습니다.
- 깨끗한 새 가상환경에서 패키지를 재설치하는 검사는 하지 않았습니다. 현재 환경에서 확인한 직접 의존성 버전을 지정했습니다.
- 트래픽 부하·공격적 스팸·장기간 운영·백업 복원 검증은 기본 구현 범위에 포함하지 않았습니다.
