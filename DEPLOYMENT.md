# 무료 배포 검토

2026-10-23 추가 조사: Python 내장 SQLite 파일 유지 조건의 새 후보와 현재 추천(alwaysdata)은 [SQLITE_HOSTING_RESEARCH.md](SQLITE_HOSTING_RESEARCH.md)를 참고하세요. 앞선 서비스 비교는 [HOSTING_RESEARCH.md](HOSTING_RESEARCH.md)에 있습니다. 아래 Render 설정은 데이터 보존을 보장하지 않는 체험용으로 유지합니다.

확인 기준일: 2026-10-23. 이번 작업은 배포 가능한 소스·설정·절차를 준비하는 범위이며, 호스팅 계정 생성이나 실제 공개 배포는 수행하지 않았습니다.

## 확인된 선택: Render Free 체험

Render는 Python Web Service의 Free 인스턴스를 제공합니다. 제공한 설정은 서비스 1개, 작업자 1개, `plan: free`이며 별도 DB 서비스, 유료 디스크, 유료 도메인, API 호출을 추가하지 않습니다. 다만 무료 서비스를 영구 데이터 보존용으로 간주하면 안 됩니다.

**중요한 제약:** Render Free의 파일시스템은 임시입니다. 절전·재시작·재배포 시 SQLite 파일과 작성 글이 사라질 수 있습니다. 데이터가 유지되는 방명록 운영을 완료한 것으로 안내하지 않습니다. 로컬 SQLite 영구 저장과 무료 호스팅의 파일 보존은 별개의 조건입니다.

공식 근거:

- [무료 서비스 범위·절전·임시 파일시스템·사용량 제한](https://render.com/docs/free)
- [Web Service 배포와 포트 설정](https://render.com/docs/web-services)
- [Blueprint의 plan·rootDir·buildCommand·startCommand](https://render.com/docs/blueprint-spec)

무료 서비스는 15분간 요청이 없으면 절전 상태가 되고 다음 요청의 시작이 지연될 수 있습니다. 작업공간의 무료 실행 시간·전송량·빌드 사용량을 함께 점검해야 합니다. 앱의 저장 건수 제한은 트래픽이나 비용에 대한 상한 보장이 아닙니다. Render의 결제수단 없는 계정은 무료 사용량 초과 시 과금 대신 서비스가 일시 중지될 수 있습니다. 기존 결제수단이 있는 계정은 사용량·지출 설정을 확인한 뒤 생성하세요. 이번 소스는 유료 전환이나 자동 결제를 실행하지 않습니다.

## 배포 절차

기존 저장소 전체를 연결하는 경우:

1. 실제 DB·가상환경·비밀정보를 제외하고 소스를 본인의 Git 저장소에 올립니다. 이 작업은 자동 수행하지 않았습니다.
2. Render에서 New → Web Service → 저장소 연결을 선택합니다.
3. Root Directory를 `Day1-Day8`, Runtime을 Python으로 지정합니다.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`
6. Instance Type을 **Free**로 확인하고 환경변수 `PYTHON_VERSION=3.12.14`를 지정합니다.
7. Health Check Path는 `/health`입니다. Persistent Disk나 관리형 DB는 추가하지 않습니다.
8. 배포 URL에서 글 등록과 새로고침을 확인합니다. 테스트 글은 보존되지 않을 수 있습니다.

Blueprint를 사용하면 파일 경로를 `Day1-Day8/render.yaml`로 지정합니다. `render.yaml`의 `rootDir`는 저장소 루트 기준입니다. **이 폴더의 내용만 별도 저장소의 루트에 올린다면 `rootDir: Day1-Day8` 줄을 삭제**하고 Blueprint Path를 `render.yaml`로 지정하세요.

## 현재 조건을 넘어서는 변경

무료 환경에서 영구 보존이 반드시 필요하다면, 무료·지속 가능한 파일 저장을 지원하는 다른 호스팅의 현재 조건을 추가 확인하거나 저장 기술을 변경해야 합니다. 외부 DB·유료 디스크·새 라이브러리를 임의로 도입하지 않았습니다. 그런 변경이 필요할 때는 Codex.md 규칙에 따라 사용자와 먼저 결정합니다.

공개 서비스에서 스팸을 제어하려면 별도의 운영 기능이 필요할 수 있습니다. 현재는 기본 방명록으로, 인증·관리자 삭제·봇 차단·요청 빈도 제한을 제공하지 않습니다. 전체 건수 상한만으로 악의적인 요청까지 차단할 수는 없습니다.
