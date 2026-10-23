# 무료 배포 서비스 비교와 추천

추가 조사: Python 내장 SQLite 파일 유지 조건에 맞춘 새 후보와 추천(alwaysdata)은 [SQLITE_HOSTING_RESEARCH.md](SQLITE_HOSTING_RESEARCH.md)를 참고하세요. 아래는 앞선 서비스 비교 기록입니다.

조사일: 2026-10-23, 한국 시간. 공식 요금·기능·배포 문서를 기준으로 확인했습니다. 실제 계정별 가입 가능 여부나 배포 성공을 확인한 결과는 아닙니다.

대상은 현재 작성한 FastAPI + Pydantic + HTML/CSS + Python 내장 SQLite 방명록입니다. 무료 여부뿐 아니라 SQLite 파일을 재시작 후에도 유지하는지가 핵심입니다.

## 비교

| 서비스 | 현재 무료 조건 | SQLite 보존 | 장점 | 단점·주의 | 이 앱에 대한 판단 |
| --- | --- | --- | --- | --- | --- |
| PythonAnywhere | 무료 웹 앱 1개, 작업자 1개, 파일 공간 512 MiB. 일반 무료 웹 앱은 1개월 만료·연장 방식 | 계정 파일 공간에 저장 가능 | Python 중심, 파일 업로드와 콘솔 제공, 외부 DB가 필요 없음 | FastAPI용 ASGI는 실험 기능. 장기 요금·인터페이스 미확정, 제한적인 관리 화면 | **조건부 1순위**: 해당 무료 계정에서 ASGI 생성 가능 여부를 먼저 확인 |
| Railway | 신규 30일/$5 체험 후 Free 월 $1 사용 크레딧, RAM 최대 0.5 GB, Volume 최대 0.5 GB | 볼륨 경로에 저장하면 가능 | FastAPI 배포 경로와 저장 볼륨 지원 | 월 $1 이내 지속 운영 보장 없음. Trial 볼륨은 크레딧 만료 30일 후 삭제 안내가 있어 보존 조건 확인 필수 | 기술적 적합성은 높지만 무료 장기 운영 조건에 불확실성 |
| Render | Free Web Service, 작업공간 월 750 실행 시간, 15분 무요청 시 절전 | 불가: 절전·재시작·재배포 때 로컬 파일 유실 | Git 연결 배포가 간단하고 기존 render.yaml 사용 가능 | 무료 영구 디스크 없음. Free Postgres도 30일 만료 | **시연용 추천**, 글 보존용 운영에는 부적합 |
| Koyeb | 조직당 Free 인스턴스 1개, RAM 512 MB·0.1 vCPU·로컬 디스크 2 GB, 1시간 무요청 시 절전 | 불가: Free에 영구 Volume 연결 불가 | 작은 Python 웹 앱 실행 가능 | 무료 지역 제한, 가입·카드 입력 때 선택 요금제 확인 필요 | 현재 SQLite 방명록에는 비추천 |
| Vercel | Hobby 무료 범위에서 Python/FastAPI 실행 가능 | 불가: 함수 파일시스템은 읽기 전용, /tmp는 임시 공간 | FastAPI 배포 지원과 자동 확장 | 쓰기 가능한 영구 로컬 DB 없음 | 외부 DB로 구조를 변경해야 하므로 현재 조건에 부적합 |
| Oracle Cloud | Always Free VM과 저장 자원, 한도 내 무료 | VM의 지속 디스크에서 가능 | 기존 Python·SQLite 구조 유지 가능 | 서버·방화벽·HTTPS·프로세스 직접 운영. 가입 카드 확인, 자원 부족·유휴 VM 회수 가능 | 단순한 초급 앱 배포에는 운영 부담이 큼 |
| Hugging Face Spaces | Static은 무료. CPU Basic 시간당 요금은 무료지만 새 Docker/Gradio Space 생성은 유료 플랜 요구 | 기본 실행 디스크는 비영구 | 데모·컨테이너 제공 | 무료 계정의 새 FastAPI Docker 배포를 무조건 무료라고 안내할 수 없음 | 신규 무료 배포 대상으로 제외 |
| Fly.io | 새 계정 체험: 최대 7일 또는 총 VM 실행 2시간 | 볼륨 사용 가능하나 체험 한정 | 컨테이너·볼륨 구조 제공 | 장기 무료 플랜이 아닌 짧은 체험 | 지속 무료 배포 대상으로 제외 |

공식 근거:

- PythonAnywhere: [무료 계정](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/), [파일 공간](https://help.pythonanywhere.com/pages/DiskQuota/), [ASGI 배포](https://help.pythonanywhere.com/pages/ASGICommandLine/), [만료·연장 안내](https://blog.pythonanywhere.com/129/)
- Railway: [현재 요금표](https://railway.com/pricing), [플랜](https://docs.railway.com/pricing/plans), [볼륨](https://docs.railway.com/volumes/reference), [Trial 데이터 보존](https://docs.railway.com/pricing/free-trial)
- Render: [무료 서비스 제한](https://render.com/docs/free)
- Koyeb: [인스턴스](https://www.koyeb.com/docs/reference/instances), [볼륨 제한](https://www.koyeb.com/docs/reference/volumes), [가입·결제 FAQ](https://www.koyeb.com/docs/faqs/pricing)
- Vercel: [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi), [함수 파일시스템](https://vercel.com/docs/functions/runtimes)
- Oracle: [Always Free 자원](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm), [가입·카드 FAQ](https://www.oracle.com/cloud/free/faq/)
- Hugging Face: [Spaces Overview](https://huggingface.co/docs/hub/spaces-overview)
- Fly.io: [무료 체험](https://fly.io/docs/about/free-trial/)

## 추천 판단

기존 기술·SQLite 보존·간단한 구성을 우선하면 **PythonAnywhere를 먼저 검토**하는 것이 적합합니다. 앱 코드나 DB 구조를 바꿀 필요가 없고, CSS는 이미 FastAPI StaticFiles로 제공하므로 별도 정적 파일 매핑 없이 처리할 수 있습니다. 이는 현재 코드와 공식 기능을 비교한 판단입니다.

다만 ASGI는 실험 기능입니다. 무료 계정의 ASGI 사용 가능 여부와 관리 방식·만료 조건을 실제 계정에서 확인하기 전에는 “계속 무료로 운영 가능”이라고 확정하지 않습니다. 일반 무료 웹 앱의 1개월 연장 정책이 ASGI 관리 화면에서도 같은 방식으로 노출되는지는 별도 확인해야 합니다.

무료 ASGI를 사용할 수 없다면, **시연은 Render**, SQLite를 보존하며 Linux 운영까지 배우려면 **Oracle Always Free**, 작은 사용량과 볼륨 보존 정책을 확인할 수 있다면 **Railway Free**를 후속 후보로 둡니다. 이번 비교에서는 모든 조건을 무조건 충족하는 장기 무료 서비스를 확정하지 않았습니다.

## PythonAnywhere 배포 절차

아래는 현재 프로젝트에 맞춘 절차입니다. 명령의 `YOURUSERNAME`을 본인의 계정명으로 바꾸세요. 미국 서비스 도메인 기준이며 EU 계정은 도메인이 다릅니다.

### 1. 계정과 코드 준비

무료 Beginner 계정을 만들고 해당 계정에서 ASGI 사이트를 생성할 수 있는지 확인합니다. 기존 웹 앱이 있다면 도메인 충돌을 피할 수 있는지 확인합니다. Account의 API Token 메뉴에서 토큰을 생성합니다. 토큰을 소스나 공개 문서에 넣지 않습니다. [ASGI 공식 안내](https://help.pythonanywhere.com/pages/ASGICommandLine/)

Files 화면을 이용해 다음 구조로 업로드합니다. Windows 가상환경·검사용 DB는 올리지 않습니다.

```text
/home/YOURUSERNAME/guestbook/
├── main.py
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    └── style.css
```

### 2. 기존 앱 의존성 설치

PythonAnywhere Bash 콘솔에서 실행하는 명령입니다. 로컬 PowerShell 명령과 구분하세요. Python 3.12가 없는 오래된 계정은 제공 Python 버전과 시스템 이미지를 먼저 확인합니다.

```bash
mkdir -p /home/YOURUSERNAME/.virtualenvs
python3.12 -m venv /home/YOURUSERNAME/.virtualenvs/guestbook
/home/YOURUSERNAME/.virtualenvs/guestbook/bin/python -m pip install --no-cache-dir -r /home/YOURUSERNAME/guestbook/requirements.txt
```

앱에 필요한 외부 라이브러리는 기존 requirements의 세 가지입니다. Windows `.venv`를 복사하지 않고 Linux에서 새로 만듭니다. 디스크 사용량에는 소스뿐 아니라 가상환경·패키지·캐시도 포함됩니다. [디스크 할당량](https://help.pythonanywhere.com/pages/DiskQuota/)

### 3. 배포용 관리 도구 설치

공식 절차는 `pythonanywhere` 패키지가 제공하는 `pa` 명령을 사용합니다.

```bash
pip install --user --upgrade pythonanywhere
```

이 패키지는 앱 자체의 의존성이 아닌 **호스팅 관리용 추가 도구**입니다. 이번 조사에서 설치하지 않았습니다. 실제 설치 작업은 Codex.md의 새 라이브러리 사전 협의 규칙에 따라 사용자와 결정한 후 진행합니다. [공식 설치·명령 안내](https://help.pythonanywhere.com/pages/ASGICommandLine/)

### 4. 사이트 생성

```bash
pa website create --domain YOURUSERNAME.pythonanywhere.com --command 'env GUESTBOOK_DB=/home/YOURUSERNAME/guestbook-data/guestbook.sqlite3 /home/YOURUSERNAME/.virtualenvs/guestbook/bin/uvicorn --app-dir /home/YOURUSERNAME/guestbook --uds ${DOMAIN_SOCKET} main:app --workers 1'
```

`GUESTBOOK_DB`는 이미 앱이 지원합니다. DB를 코드 폴더 밖에 두어 소스 교체와 분리합니다. `${DOMAIN_SOCKET}`은 플랫폼이 제공하는 값이므로 그대로 유지하고 전체 실행 명령의 작은따옴표도 유지합니다. Uvicorn과 작업자 1개를 사용합니다. [공식 실행 방식](https://help.pythonanywhere.com/pages/ASGICommandLine/)

### 5. 확인과 수정 반영

```bash
pa website get --domain YOURUSERNAME.pythonanywhere.com
pa website reload --domain YOURUSERNAME.pythonanywhere.com
```

HTTPS 주소에서 이름·글을 등록하고 `/health`도 확인합니다. reload 후 글이 남는지 검사합니다. 실패하면 get 결과의 error log를 확인합니다. 일반 WSGI 설정 화면에 FastAPI를 넣는 방식과 구분하세요. [공식 관리 명령](https://help.pythonanywhere.com/pages/ASGICommandLine/)

월별 만료·연장 안내와 파일 공간을 확인하고 주기적으로 DB를 백업합니다. 앱이 중지된 상태에서 DB 파일을 다운로드하거나 SQLite의 backup API를 사용하면 실행 중 파일의 불완전한 복사를 피할 수 있습니다.

## Render로 빠르게 시연하기

GitHub에 이 프로젝트를 올린 뒤 Render의 New → Web Service에서 연결합니다. 기존 저장소 전체를 올렸다면 아래 값을 사용합니다. [공식 Web Service 배포 안내](https://render.com/docs/web-services)

| 항목 | 값 |
| --- | --- |
| Root Directory | `Day1-Day8` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1` |
| Instance Type | `Free` |
| Health Check Path | `/health` |

이 폴더만 별도 저장소 루트로 올렸다면 Root Directory는 비워둡니다. 기존 `render.yaml`을 사용할 때도 rootDir를 맞춥니다. DB 데이터 보존용 배포가 아니라는 점은 동일합니다.

## Railway를 검토할 경우의 설정

GitHub 저장소 배포 후 앱 서비스에 Volume을 연결하고 Mount Path를 `/data`, 환경변수 `GUESTBOOK_DB=/data/guestbook.sqlite3`로 지정합니다. Root Directory는 기존 저장소 전체 기준 `/Day1-Day8`, 실행 명령은 Render와 같은 Uvicorn 명령을 사용할 수 있습니다. Networking에서 Generate Domain을 선택합니다. [FastAPI 배포](https://docs.railway.com/guides/fastapi), [볼륨](https://docs.railway.com/volumes/reference)

월 $1은 무제한 실행권이 아닌 사용 크레딧입니다. Trial 볼륨의 만료 후 삭제 안내를 확인하고, 장기 무료 사용에서도 보존되는지 확인하기 전에는 실제 방명록 데이터를 맡기지 않습니다. [Trial 보존 정책](https://docs.railway.com/pricing/free-trial)

## 이번에 수행한 범위

공식 문서 조사와 프로젝트에 맞춘 배포 절차 작성만 수행했습니다. 호스팅 가입·추가 패키지 설치·계정 연결·외부 업로드·공개 배포·유료 전환·앱 코드 변경은 수행하지 않았습니다.
