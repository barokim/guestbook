# SQLite 파일 DB를 유지하는 무료 배포 서비스 추가 조사

조사 기준일: 2026-10-23, 한국 시간.

이번 조건은 **Python 표준 sqlite3 + 서버의 .sqlite3 파일 + 기존 FastAPI 앱 유지**입니다. 외부 DB, Cloudflare D1, 파일을 객체 저장소에 복사하는 동기화 구성은 추천에서 제외했습니다. 아래는 공식 문서 조사이며 실제 호스팅 가입·배포를 완료한 결과가 아닙니다.

## 추가 후보 비교

| 서비스 | 무료 조건 | SQLite 파일 보존·운영 | 장점 | 제약과 판단 |
| --- | --- | --- | --- | --- |
| **alwaysdata Free** | 개인·비영리, SSD 1GB·RAM 256MB·CPU ¼·최근 3일 백업 | 계정 파일 공간에 보관. Python·ASGI 웹 실행 공식 지원 | VM 운영 없이 기존 FastAPI와 파일 경로 구성 유지 가능 | 계정 주소 사용, 가입 카드 검증, 관리자 주기적 로그인. 이번 추가 후보 중 **우선 추천** |
| **Google Compute Engine** | 미국 지정 지역 e2-micro 1대 상당 시간, 표준 영구 디스크 30GB 무료 범위 | VM의 영구 디스크에서 sqlite3 사용 가능 | 대중적 클라우드, 일반 Linux 환경 | 공인 IPv4 별도 비용. 무료 VM이라고 공개 서비스 전체가 무료인 것은 아님 |
| **AWS EC2** | 2025-07-15 이후 신규 계정은 가입 $100 + 활동 최대 $100 크레딧, 최대 6개월 또는 소진 시까지 | EBS 파일에 저장 가능 | AWS 학습과 기간 한정 프로젝트에 적합 | 장기 무료 아님. 계정 종료·크레딧·디스크 삭제 정책 확인 필요 |
| **Amazon Lightsail** | 현행 AWS Free Tier 크레딧으로 체험 | VM 디스크에 저장 가능 | EC2보다 단순한 서버 구성 | 신규 고객의 과거 단기 무료체험은 종료됨. 크레딧 이후 최소 플랜부터 유료 |
| **Azure App Service Free** | F1 무료 요금제 | Linux 공유 파일시스템의 잠금 문제로 SQLite 운영에 부적합 | Python 앱 배포 환경은 제공 | 공식 문서가 파일 DB 문제를 명시하므로 제외 |
| **Northflank Sandbox** | 무료 서비스 2개·DB 1개·Cron 2개 | 지속 볼륨은 제공하지만 무료 포함량 확인 안 됨 | 무료 서비스가 상시 실행 | 디스크 공시가 $0.15/GB/월. 무료 SQLite 보존을 확정할 근거 부족 |
| **HelioHost** | 무료 파일 공간 1000MB·SQLite 제공 | 파일 저장은 가능. 무료 서버의 FastAPI/ASGI 배포 절차 미확인 | SQLite 제공을 공식적으로 명시 | 패키지가 설치돼 있다는 사실만으로 Uvicorn 지속 실행을 보장할 수 없어 보류 |
| **Replit** | 무료·체험 범위는 계정의 현재 요금제 확인 필요 | 공식 문서가 배포 파일시스템에 저장한 데이터에 의존하지 않도록 안내 | 편집·실행·게시 통합 환경 | 현재 로컬 SQLite 파일 보존 조건에 부적합 |

AWS·GCP·Azure는 대중적인 클라우드이지만, 그 사실과 이번 앱의 장기 무료 운영 적합성은 구분했습니다. alwaysdata를 대형 클라우드와 같은 인지도라고 평가하는 것은 아닙니다.

## 추천: alwaysdata Free

현재 공식 요금표는 과거 안내의 100MB가 아니라 **1GB**를 명시합니다. 계정 파일 공간, Python 3.12 지원, ASGI/User program 실행, 파일 백업 기능을 종합하면 기존 앱을 적게 바꾸고 배포할 수 있는 가장 유망한 추가 후보입니다. 실제 호스트에서 현재 sqlite3의 쓰기·잠금·재시작 보존 검사가 필요하다는 한계는 남아 있습니다.

- [현재 무료 요금](https://www.alwaysdata.com/en/offers/): 월 €0, SSD 1GB, RAM 256MB, CPU ¼, 3일 백업.
- [상세 제한](https://help.alwaysdata.com/en/docs/admin-billing/billing/public-cloud-prices/): 비영리 용도, 계정의 alwaysdata.net 웹 주소만 사용. 파일·메일·DB가 디스크 용량을 함께 사용합니다.
- [Python 구성](https://help.alwaysdata.com/en/docs/web-hosting/languages/python/configuration/): Python 3.12와 venv 지원, ASGI는 User program에서 Uvicorn으로 실행.
- [User program](https://help.alwaysdata.com/en/docs/web-hosting/sites/http-servers/user-program/): 실행 명령·작업 디렉터리·환경변수 지정 지원.
- [실제 가입 화면](https://www.alwaysdata.com/en/register/): 신용카드 또는 체크카드 검증을 요구하며 검증 수수료가 없다고 안내합니다. 무료·카드 불필요 홍보 문구가 있더라도 실제 가입 화면의 요구를 확인해야 합니다.
- [휴면 정지 정책](https://help.alwaysdata.com/en/docs/admin-billing/profile/suspension/): 신규 1년 이내 계정은 120일마다 관리자 로그인. 1~4년은 6개월, 4년 이상은 연 1회. 미이행 정지는 로그인으로 해제됩니다.
- [파일 백업](https://help.alwaysdata.com/en/docs/web-hosting/backups/): 파일 등을 매일 백업. 제공 백업이 사용자의 별도 DB 백업 필요까지 없애는 것은 아닙니다.

요금표의 Free에서 금지한 Services는 Advanced > Services의 백그라운드 프로그램 기능입니다. Web > Sites의 User program과는 별도 기능입니다. [Services 문서](https://help.alwaysdata.com/en/docs/web-hosting/services/)

## 우리 앱에 맞춘 배포 순서

아래는 공식 User program 방식을 현재 프로젝트에 맞춘 설정안입니다. `ACCOUNT`는 실제 계정명으로 바꿉니다. 설치·업로드 명령을 이번 조사에서 실행한 것은 아닙니다.

1. Free 요금제와 개인·비영리 용도 조건을 확인합니다.
2. Environment > Python에서 3.12를 선택합니다. 이 호스팅은 기본 Python 버전을 고른 뒤 `python` 명령을 사용하도록 안내합니다.
3. SFTP 등으로 `/home/ACCOUNT/guestbook/`에 `main.py`, `requirements.txt`, `templates/index.html`, `static/style.css`를 올립니다. Windows의 `.venv`를 올리지 않습니다.
4. 호스팅 SSH 환경에서 다음 명령으로 기존 의존성을 설치합니다.

```bash
cd /home/ACCOUNT/guestbook
python -m venv .venv
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
.venv/bin/python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

기존 FastAPI·Pydantic·Uvicorn만 설치하며, 새 앱 라이브러리를 제안하지 않습니다. `sqlite3`는 pip 패키지로 설치하지 않습니다. Python 제공 모듈을 확인합니다.

5. Web > Sites > Add a site에서 아래 값을 지정합니다.

| 항목 | 설정 |
| --- | --- |
| Address | `ACCOUNT.alwaysdata.net` |
| Type | `User program` |
| Working directory | `/home/ACCOUNT/guestbook` |
| Environment | `GUESTBOOK_DB=/home/ACCOUNT/guestbook-data/guestbook.sqlite3` |
| Command | 아래 Uvicorn 명령 |

```bash
/home/ACCOUNT/guestbook/.venv/bin/python -m uvicorn main:app --host $IP --port $PORT --workers 1
```

`$IP`와 `$PORT`는 alwaysdata가 제공하는 값입니다. Render의 `0.0.0.0` 설정을 그대로 복사하지 않습니다. 상시 개발용 `--reload`는 사용하지 않습니다. DB는 코드 디렉터리 밖에 두고 디렉터리의 쓰기 권한도 확인합니다. 기존 앱이 이 환경변수와 상위 디렉터리 생성을 지원하므로 소스 변경이 필요하지 않습니다.

6. 공개 주소에서 한글·줄바꿈 글 등록, `/health`, 새로고침을 확인합니다. 사이트를 재시작하고 소스만 다시 업로드한 뒤에도 같은 글이 남는지 확인합니다. 동시에 글을 쓸 때 SQLite 잠금 오류가 없는지도 확인합니다.
7. 저장 공간·메모리 사용량을 확인하고 관리자 로그인과 DB 백업을 유지합니다. 무료 RAM 256MB에서의 실제 실행은 아직 측정하지 않았습니다.

## 대형 클라우드에서 확인한 추가 비용·제약

### Google Compute Engine

Free Tier는 지정 미국 리전의 e2-micro와 30GB 표준 영구 디스크를 포함합니다. SSD 또는 Balanced 디스크를 선택하면 무료 범위와 달라질 수 있습니다. [무료 자원 문서](https://docs.cloud.google.com/free/docs/free-cloud-features)

일반 VM의 공인 IPv4는 **$0.005/시간, 계정당 월 1시간 무료**입니다. 30일 상시 운영이라면 IPv4 비용만 대략 `(720 - 1) × 0.005 = $3.595`입니다. 세금·환율·다른 사용량은 제외한 계산입니다. IPv6 자체는 무료지만 접속 환경과 공개 경로 구성이 달라지므로 초보자용 완전 무료 대안으로 단정하지 않습니다. [네트워크 요금](https://cloud.google.com/vpc/network-pricing)

### AWS EC2와 Lightsail

예전 EC2의 12개월 무료 안내는 계정 생성일에 따라 다릅니다. 2025-07-15 이후 계정은 크레딧·최대 6개월 방식입니다. EBS에 파일 DB를 둘 수 있지만 이것이 장기 무료를 의미하지는 않습니다. [계정 생성일별 정책](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html)

Lightsail도 새 고객의 과거 단기 무료체험이 AWS Free Tier 크레딧으로 대체됐습니다. 오래된 '3개월 무료' 튜토리얼만으로 결정하지 않습니다. [현행 Billing FAQ](https://docs.aws.amazon.com/en_en/lightsail/latest/userguide/amazon-lightsail-frequently-asked-questions-faq-billing-and-account-management.html)

### Azure App Service

단순히 `/home` 파일이 남는 것만으로 SQLite 운영에 적합한 것은 아닙니다. Microsoft는 Linux App Service의 네트워크 공유 파일시스템에서 SQLite의 배타적 파일 잠금에 문제가 있다고 설명합니다. [공식 FAQ](https://learn.microsoft.com/en-us/troubleshoot/azure/app-service/faqs-app-service-linux-new)

Azure VM을 직접 운영하면 지속 디스크에 SQLite를 둘 수 있지만, 신규 고객의 기간 한정 무료 조건·공인 IP·서버 운영을 별도로 검토해야 합니다. [Azure 무료 서비스](https://azure.microsoft.com/en-us/pricing/free-services/)

## 나머지 후보 근거

- Northflank: [무료 Sandbox와 디스크 요금](https://northflank.com/pricing), [결제·자원 관리](https://northflank.com/docs/v1/application/billing/pricing-on-northflank). 무료 볼륨 포함 여부를 확인하지 못했으며, '무료 볼륨 지원 불가'로 단정하지 않았습니다.
- HelioHost: [제공 기능](https://wiki.helionet.org/What_HelioHost_Offers), [운영자의 FastAPI 패키지 설치 안내](https://helionet.org/index/topic/65846-solved-fastapi-python-package/). Python/SQLite와 ASGI 서비스 실행은 구분했습니다.
- Replit: [Publishing 문서](https://docs.replit.com/learn/projects-and-artifacts/replit-deployments)는 배포 파일시스템의 쓰기 데이터에 의존하지 않도록 안내합니다.
- GitHub Pages: [공식 문서](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)상 서버 측 Python을 지원하지 않아 제외했습니다.
- Streamlit Community Cloud: [공식 문서](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data)는 로컬 SQLite 보존을 보장하지 않으며, 현재 FastAPI 화면 구조와도 다릅니다.
- Google Cloud Run: [런타임 계약](https://docs.cloud.google.com/run/docs/container-contract)은 기본 파일시스템이 메모리 기반이고 인스턴스 종료 시 파일이 남지 않음을 설명합니다.
- Cloudflare D1: [공식 설명](https://developers.cloudflare.com/d1/)은 SQLite 문법을 사용하는 관리형 DB입니다. 현재 요구인 Python sqlite3로 로컬 파일에 연결하는 구성과는 다르므로 선택하지 않았습니다.

## 수행 범위

공식 문서 조사와 설정안 작성만 수행했습니다. 앱 소스·기존 DB 변경, 계정 생성, 카드 입력, 패키지 설치, 외부 업로드, 실제 배포는 진행하지 않았습니다. 문서만 변경했으므로 앱 테스트는 다시 실행하지 않았습니다.
