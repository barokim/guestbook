# 작은 방명록

Day1~Day8에서 배운 문법을 연결해 만든 기본 방명록입니다. 이름과 내용을 작성하면 SQLite에 저장하고, 최신 글부터 10개씩 보여줍니다. 로그인·수정·삭제는 기본 범위에 포함하지 않았습니다.

처음 Render에 배포한다면 아래의 [Render 첫 배포 가이드](#render-첫-배포-가이드)를 순서대로 따라가세요.

## 실행

Windows PowerShell에서 기존 학습 가상환경을 그대로 사용할 수 있습니다.

```powershell
cd C:\AIO4\Day1-Day8
..\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

브라우저에서 http://127.0.0.1:8000 을 엽니다. 종료는 터미널에서 `Ctrl+C`입니다.

별도 환경을 만들 때:

```powershell
cd C:\AIO4\Day1-Day8
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

`requirements.txt`는 현재 학습 가상환경에서 확인한 FastAPI·Pydantic·Uvicorn 버전을 사용합니다. 새 외부 라이브러리를 추가하지 않았습니다. 개발 검사는 기존에 학습한 pytest·httpx를 사용합니다. HTML 폼은 파이썬 표준 `urllib.parse`로 읽고, HTML은 표준 `string.Template`과 `html.escape`로 생성합니다. JavaScript, 프런트엔드 프레임워크, Jinja2, python-multipart, ORM은 필요하지 않습니다.

## 파일

| 파일 | 역할 |
| --- | --- |
| `main.py` | 입력 검증, HTML 응답, SQLite 저장·조회 |
| `templates/index.html` | HTML 폼과 목록의 화면 구조 |
| `static/style.css` | PC·모바일 화면 스타일 |
| `test_app.py` | 저장·검증·보존·출력·페이지 이동 검사 |
| `ANALYSIS.md` | Day1~Day8 분석 및 구현과의 연결 |
| `DEPLOYMENT.md` | 무료 배포 조건과 배포 절차 |
| `render.yaml` | Render Free 체험 배포 설정 |
| `VERIFICATION.md` | 실제 확인 결과와 확인하지 않은 범위 |

Codex.md의 출력 위치 문구에 따라 `Day1-Day8`에 작성했습니다. 지침 파일 `Day1_Day8/Codex.md`는 원본 위치에 보존했습니다.

## 사용 규칙

- 이름: 앞뒤 공백 제거 후 1~20자.
- 내용: 앞뒤 공백 제거 후 1~1,000자. 본문 줄바꿈은 유지합니다.
- 최신 등록 순서로 10개씩 조회합니다. 페이지가 마지막을 넘으면 마지막 페이지를 보여줍니다.
- 게시물은 최대 1,000개입니다. 가득 차면 기존 글을 지우지 않고 새 작성을 거절합니다.
- 요청 본문은 16 KiB로 제한합니다. 한글 1,000자가 URL 인코딩되어도 정상 입력 가능합니다.
- 등록 후 `303`으로 목록에 이동하므로 일반적인 새로고침은 글을 다시 저장하지 않습니다. 빠른 연속 클릭이나 POST 재시도에 대한 중복 저장 방지까지 제공하지는 않습니다.
- 날짜는 서버 위치와 무관하게 한국 시간(UTC+9)으로 저장하고 표시합니다.

## 데이터 구조

기본 파일은 `data/guestbook.sqlite3`이며 첫 조회 또는 작성 시 자동 생성됩니다. 업무 테이블은 `entries` 하나뿐입니다. 외래 키·관계 테이블·회원 테이블이 없습니다. `AUTOINCREMENT`를 사용하지 않아 별도의 `sqlite_sequence` 테이블도 생성하지 않습니다.

| 열 | SQLite 타입 | 설명 |
| --- | --- | --- |
| `id` | INTEGER PRIMARY KEY | 등록 순서와 식별자 |
| `name` | TEXT NOT NULL | 이름 |
| `message` | TEXT NOT NULL | 내용 |
| `created_at` | TEXT NOT NULL | 시간대가 포함된 ISO 날짜 |

다른 위치를 사용하려면 서버를 실행하기 전에 경로를 지정하세요.

```powershell
$env:GUESTBOOK_DB = 'C:\AIO4\Day1-Day8\data\guestbook.sqlite3'
```

로컬에서는 같은 파일을 사용하는 한 서버를 재실행해도 데이터가 유지됩니다. SQLite는 설치된 Python의 `sqlite3` 모듈을 사용합니다. SQL 값은 `?` 매개변수로 전달하고, 사용자 입력은 HTML 이스케이프 후 표시합니다. 저장 건수 확인과 INSERT는 같은 트랜잭션으로 수행합니다.

## 검사

기존 학습 가상환경에서:

```powershell
cd C:\AIO4\Day1-Day8
..\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider test_app.py
```

별도 가상환경이라면 `requirements-dev.txt`를 먼저 설치합니다. 테스트 DB는 임시 디렉터리에 생성하여 실제 방명록과 분리합니다. 일상적인 수동 확인은 빈 화면 확인 → 한글·줄바꿈 등록 → 새로고침 → 서버 재실행 → 목록 유지 순서로 진행하세요.

무료 호스팅의 SQLite 파일 보존 조건은 별도입니다. 배포 전에 `DEPLOYMENT.md`를 확인하세요.

## Render 첫 배포 가이드

확인 기준일: **2026-10-23**. Render의 현재 공식 문서와 이 프로젝트의 소스·설정 파일을 대조해 작성했습니다. 대시보드 공개 주소는 JavaScript 앱이어서 문서 조회 도구로 가입 후 화면 내부를 읽을 수 없었습니다. 아래 메뉴 이름은 공식 문서 기준이며, 계정별 첫 화면·버튼 위치는 다를 수 있습니다. 이 가이드 작성 과정에서 실제 가입·업로드·공개 배포를 수행하지는 않았습니다.

배포 흐름은 **GitHub에 코드 올리기 → Render 가입 → 저장소 연결 → Free Web Service 설정 → 배포 확인**입니다. 아래 PowerShell 명령은 사용자가 직접 실행할 절차이며, Render 입력란에 넣을 명령과 구분했습니다.

### 0. 무료 배포와 데이터 보존 조건 확인

이번 배포는 **FastAPI + Python 내장 SQLite + HTML/CSS**를 그대로 사용합니다. DB 서비스나 유료 디스크를 별도로 만들지 않습니다.

**Render Free는 SQLite 파일을 보존하지 않습니다.** 절전·재시작·재배포 시 작성 글이 사라집니다. 로컬 PC의 DB 파일은 그대로지만 Render에서 새로 작성한 글은 별개의 데이터입니다. 이번 가이드는 무료 학습·시연 배포용입니다. [공식 무료 서비스 제한](https://render.com/docs/free)

### 1. GitHub에 방명록 코드 올리기

현재 작업 폴더의 Git 연결은 다음과 같습니다. 본인 저장소인지 GitHub에 로그인해 확인하세요.

- 저장소: [barokim/AIO4_KBR](https://github.com/barokim/AIO4_KBR)
- 브랜치: `main`
- 배포할 하위 폴더: **`Day1-Day8`**

`Day1_Day8`는 지침 파일이 있는 다른 폴더입니다. Render에는 `main.py`가 있는 **하이픈 폴더 `Day1-Day8`**를 지정합니다.

GitHub에서 아래 경로가 보여야 Render가 코드를 가져올 수 있습니다. PC에만 파일이 있거나 커밋만 하고 push하지 않았다면 아직 배포할 수 없습니다.

```text
AIO4_KBR/
└── Day1-Day8/
    ├── .gitignore
    ├── README.md
    ├── main.py
    ├── requirements.txt
    ├── render.yaml
    ├── templates/
    │   └── index.html
    └── static/
        └── style.css
```

**PC의 PowerShell**에서 연결과 변경 내용을 먼저 확인합니다.

```powershell
cd C:\AIO4
git remote -v
git branch --show-current
git status --short -- Day1-Day8
```

위 저장소와 `main` 브랜치가 맞으면 방명록 폴더를 추가하고 내용을 확인합니다.

```powershell
git add -- Day1-Day8
git diff --cached --stat -- Day1-Day8
```

목록에 `main.py`, HTML, CSS, requirements와 문서가 포함되는지 확인합니다. 이 폴더의 `.gitignore`는 `.venv`, 캐시, `data/`, `*.sqlite3`를 제외합니다. 준비가 되면 방명록 경로를 지정해 커밋하고 올립니다.

```powershell
git commit --only -m "Add guestbook for Render deployment" -- Day1-Day8
git push origin main
```

GitHub에서 `Day1-Day8/main.py`를 열어 업로드 결과를 확인합니다. GitHub 인증 창이 나타나면 본인 계정으로 인증합니다. 이미 같은 코드가 올라가 있다면 커밋할 변경이 없다는 안내가 나올 수 있습니다.

### 2. Render에 처음 가입하기

1. 브라우저에서 [Render 대시보드](https://dashboard.render.com/)를 엽니다.
2. 가입 화면에서 GitHub 로그인 방식을 선택하면 기존 GitHub 계정으로 가입할 수 있습니다. 이메일 등 다른 로그인 방식으로 가입했어도 이후 GitHub 저장소를 연결할 수 있습니다.
3. 표시되는 계정 확인·약관·초기 설정을 완료해 대시보드로 이동합니다.

Render 로그인과 **배포할 GitHub 저장소에 대한 접근 권한 연결**은 별도로 확인해야 합니다. [공식 Git 계정 로그인·연결 안내](https://render.com/docs/git-provider)

### 3. GitHub 저장소 연결과 Web Service 생성

1. 대시보드에서 **`+ New` → `Web Service`**를 선택합니다. 이 앱은 Python 서버를 실행하므로 Web Service가 필요합니다.
2. 코드 소스로 **`Git Provider`**를 선택합니다.
3. GitHub가 연결되지 않았다면 연결 절차를 진행합니다. 저장소 접근 범위를 선택하는 화면에서는 배포할 `AIO4_KBR` 저장소를 포함합니다.
4. 목록에서 **`barokim/AIO4_KBR`**을 선택하고 `Connect`로 진행합니다.

저장소가 보이지 않으면 **Account Settings → Account Security → Git Deployment Credentials → Add credential**에서 GitHub 연결을 확인합니다. 기존 연결이 있다면 GitHub의 Render 앱 설정에서 해당 저장소가 접근 목록에 포함됐는지 확인하세요. [공식 Git Provider 연결·문제 해결](https://render.com/docs/git-provider)

### 4. 배포 설정 입력

기존 `AIO4_KBR` 저장소의 `Day1-Day8` 폴더를 배포하는 기준입니다.

| 입력 항목 | 입력할 값 | 설명 |
| --- | --- | --- |
| Name | `little-guestbook` 등 원하는 이름 | 중복이라면 다른 이름 사용 |
| Language / Runtime | **Python 3** | Python 서버 환경 |
| Branch | **`main`** | GitHub에 올린 브랜치 |
| Region | 계정 화면에서 제공되는 지역 중 선택 | 처음 선택한 지역을 기록 |
| Root Directory | **`Day1-Day8`** | `main.py`와 이 앱의 requirements가 있는 폴더 |
| Build Command | `pip install -r requirements.txt` | 앱 실행 패키지 설치 |
| Start Command | 아래 명령 전체 | Uvicorn 서버 시작 |
| Instance Type / Compute | **Free, $0** | 서비스의 무료 실행 플랜 |

**Start Command 입력란**에 아래 한 줄을 붙여넣습니다.

```text
python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
```

이 명령은 Render의 Linux 서버에서 실행합니다. `$PORT`는 Render가 제공하는 환경변수이므로 문자 그대로 입력하세요. 로컬 PowerShell의 `.venv\Scripts\python.exe` 경로나 개발용 `--reload`는 넣지 않습니다. [공식 FastAPI 배포](https://render.com/docs/deploy-fastapi), [공개 서버의 포트 조건](https://render.com/docs/web-services)

Root Directory를 지정하면 빌드·실행 명령은 그 폴더에서 수행됩니다. 이 설정이 빠지면 저장소 최상위의 다른 `requirements.txt`가 사용될 수 있습니다. **앱 폴더의 내용만 별도 저장소 루트에 올린 경우에는 Root Directory를 비워둡니다.** [공식 Root Directory 안내](https://render.com/docs/monorepo-support)

### 5. Python 버전과 상태 확인 경로 설정

환경변수 입력 영역에서 다음 값을 추가합니다.

| Key | Value |
| --- | --- |
| `PYTHON_VERSION` | `3.12.14` |

이는 이 앱을 검사한 Python 버전에 맞춘 값이며 기존 `render.yaml`과도 같습니다. Render 환경변수 방식은 `3.12`처럼 생략한 값이 아니라 전체 버전 번호를 요구합니다. [공식 Python 버전 설정](https://render.com/docs/python-version)

DB 관련 환경변수는 필수가 아닙니다. `GUESTBOOK_DB`를 생략하면 앱이 서버 안에 `data/guestbook.sqlite3`를 자동 생성합니다. Windows의 `C:\...` 경로를 Render에 입력하지 마세요.

Health Check Path 항목이 생성 화면에 보이면 **`/health`**를 입력합니다. 보이지 않으면 생성 후 서비스의 **Settings → Health Checks → Edit**에서 설정합니다. 이 앱의 `/health`는 SQLite 조회 후 `{"status":"ok"}`를 반환합니다. [공식 Health Check 설정](https://render.com/docs/health-checks)

### 6. 첫 배포 실행과 로그 확인

설정을 확인하고 화면 하단의 **Deploy 버튼**으로 배포를 시작합니다. 첫 배포 가이드는 서비스의 Deploys 화면에서 진행 상황을 확인하도록 안내합니다. [공식 첫 배포 절차](https://render.com/docs/your-first-deploy)

로그에서는 다음 흐름을 확인합니다. 실제 문구·소요 시간은 환경에 따라 다릅니다.

| 단계 | 확인할 내용 |
| --- | --- |
| 코드 가져오기 | 선택한 저장소·브랜치·커밋이 맞는지 |
| 패키지 설치 | requirements의 세 패키지와 의존성 설치가 완료되는지 |
| 서버 시작 | `Application startup complete` 등 시작 완료 로그가 나오는지 |
| 배포 상태 | **Live** 상태로 바뀌는지 |

실패하면 해당 배포의 로그에서 첫 오류를 확인합니다. 이미 실행 중인 앱의 오류는 서비스의 Logs 화면에서 봅니다. [공식 로그·배포 오류 해결](https://render.com/docs/troubleshooting-deploys)

### 7. 공개 주소에서 방명록 확인

서비스 화면에 표시된 **실제 `https://...onrender.com` 주소**를 엽니다. 아래 주소는 설명용 예시이며 생성된 주소를 그대로 사용해야 합니다. Render는 Web Service에 고유 공개 주소를 제공합니다. [공식 Web Service 안내](https://render.com/docs/web-services)

```text
https://실제-서비스-주소.onrender.com/
https://실제-서비스-주소.onrender.com/health
```

다음 순서로 직접 확인하세요.

1. 첫 화면에서 이름·내용 작성 폼과 빈 목록이 보입니다.
2. 한글 이름과 두 줄 이상의 내용을 작성합니다.
3. 작성 완료 안내와 최신 목록에 글이 나타납니다.
4. 새로고침해 같은 글이 중복 등록되지 않는지 봅니다.
5. `/health`에서 `{"status":"ok"}`가 보입니다.
6. 휴대폰에서도 글자와 입력칸을 확인합니다.

이 앱은 `/docs`와 `/openapi.json`을 비활성화했습니다. 해당 주소의 404는 배포 실패가 아닙니다. 로컬 PC의 기존 글도 자동 업로드되지 않습니다.

### 8. 수정한 코드를 다시 배포하기

로컬 수정 후 1단계와 같은 방식으로 변경한 방명록 파일을 커밋·push합니다. Git Provider로 연결한 서비스는 **Settings → Auto-Deploy → On Commit**일 때 연결 브랜치의 새 커밋을 자동 배포합니다. 수동 배포는 서비스의 **Manual Deploy** 메뉴를 이용합니다. [공식 재배포 안내](https://render.com/docs/deploys)

**재배포 후 SQLite 글이 사라지는 것은 무료 파일시스템의 제약입니다.** 데이터가 필요한 실제 운영용으로 전환할 때는 저장 방식을 별도로 결정해야 합니다.

### 자주 막히는 부분

| 증상 | 먼저 확인할 항목 |
| --- | --- |
| 저장소 목록에 앱이 없음 | Render의 GitHub 연결, Render 앱의 저장소 접근 범위 |
| GitHub에 방명록 파일이 없음 | PC의 커밋·push 여부, `main` 브랜치 |
| `requirements.txt`를 못 찾음 | Root Directory가 `Day1-Day8`인지 |
| `Could not import module main` | 같은 폴더에 `main.py`가 있는지, Start Command가 `main:app`인지 |
| Python·패키지 설치 실패 | `PYTHON_VERSION=3.12.14`, 앱 폴더의 requirements, 로그의 첫 오류 |
| 포트 감지 실패·접속 불가 | `--host 0.0.0.0 --port $PORT`가 그대로 있는지 |
| `templates/index.html` 또는 CSS가 없음 | 해당 폴더까지 커밋·push했는지, 파일명 대소문자 |
| `/health`가 503 | 런타임 로그의 SQLite 오류, Windows 경로를 환경변수에 넣었는지 |
| 첫 접속이 오래 걸림 | 무료 서비스의 절전 복귀 가능성 |
| `/docs`가 404 | 이 앱은 Swagger UI를 비활성화했으므로 정상 |
| 글이 사라짐 | 절전·재시작·재배포 여부와 무료 저장 한계 |
| 수정이 반영되지 않음 | 연결 브랜치·업로드 커밋·Auto-Deploy·최근 배포 결과 |

일반적인 실패 조사는 [Render 공식 문제 해결 문서](https://render.com/docs/troubleshooting-deploys)를 참고하세요. 표의 파일 경로와 `/docs` 동작은 현재 앱 코드를 기준으로 작성했습니다.

### 무료 범위에서 유지하기

- 서비스의 실행 플랜을 **Free**로 확인합니다. 계정의 워크스페이스 요금과 서비스 실행 요금은 별개입니다.
- 15분 동안 방문 요청이 없으면 절전 상태가 되며, 다음 접속에 약 1분이 걸릴 수 있습니다.
- 작업공간 전체에 월 750 무료 실행 시간이 제공됩니다. 여러 무료 서비스를 만들면 시간을 나눠 사용합니다.
- 전송량·빌드 사용량도 대시보드 Billing에서 확인합니다. 결제수단이 있으면 초과 사용량에 추가 비용이 생길 수 있습니다.
- 이 안내에서는 유료 디스크·관리형 DB·유료 도메인을 추가하지 않습니다.

제한과 과금 조건은 [Render 공식 Free 문서](https://render.com/docs/free)에서 배포 시점에도 확인하세요.

### 기존 render.yaml을 사용할 때

위 절차는 **대시보드에서 값을 직접 입력하는 방식**입니다. `render.yaml`은 Blueprint 방식의 설정 파일이므로 일반 Web Service 생성 화면에서 자동 적용됐다고 가정하지 마세요.

Blueprint 방식으로 진행한다면 파일 경로를 `Day1-Day8/render.yaml`로 지정합니다. 이 파일의 `rootDir: Day1-Day8`는 기존 저장소 구조를 기준으로 합니다. 앱 내용만 별도 저장소 루트에 올렸다면 `rootDir` 줄을 제거해야 합니다. 처음에는 위의 대시보드 방식으로 진행하면 필요한 설정을 하나씩 확인하기 쉽습니다. [공식 Blueprint 설정](https://render.com/docs/blueprint-spec)
