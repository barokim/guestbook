guestbook: SQLite3 → Supabase PostgreSQL

대상 원본: https://github.com/barokim/guestbook/blob/main/main.py

적용
1. 저장소의 main.py를 제공한 main.py로 교체합니다.
2. schema.sql을 main.py와 같은 폴더에 추가합니다.
3. requirements.txt를 제공한 파일로 교체하고 설치합니다.
   python -m pip install -r requirements.txt
4. 기존 templates/와 static/ 폴더를 유지합니다.
5. 저장소의 기존 config.json은 host, port, dbname, user, password 형식으로
   그대로 읽을 수 있습니다. JSON은 Python 모듈이 아니므로 import 대신
   json.load()로 읽습니다. 실행 중 GitHub에서 다운로드하지 않습니다.
6. 비밀번호 교체 후 main.py 옆에 비공개 config.json을 배치하거나,
   GUESTBOOK_CONFIG 환경변수에 배포 서버의 비공개 JSON 파일 경로를 지정합니다.
   상대 경로는 main.py가 있는 폴더 기준입니다.
   config.example.json은 값이 비어 있는 양식이므로 실제 연결 정보를 넣어야 합니다.
7. 실행:
   python -m uvicorn main:app --reload
   배포 서버 예시:
   python -m uvicorn main:app --host 0.0.0.0 --port 8000

Supabase 설정
- Supabase의 Connect → Session pooler 정보를 config.json에 입력합니다.
- 앱 시작 시 schema.sql을 실행하여 public.entries를 준비합니다.
  설정된 DB 계정에는 테이블 생성/잠금/조회/삽입 권한이 필요합니다.
  기존 설정의 postgres 계정은 서버에서만 사용해야 합니다.
- 기존에 public.entries가 있으면 id, name, message, created_at 열이 제공된
  schema.sql과 호환되어야 합니다. CREATE TABLE IF NOT EXISTS는 기존 구조를
  변환하지 않습니다.
- RLS를 활성화하며 익명 API용 정책은 추가하지 않습니다.
  기존 테이블에 이미 정책이 있다면 해당 정책은 유지됩니다.
- 연결에 sslmode=require, 10초 연결 제한을 적용했습니다.
  pooler 호환성을 위해 자동 prepared statement는 사용하지 않습니다.
- 시작 시 연결/설정 오류가 있으면 서버 시작이 실패합니다.
  실행 중 DB 오류는 기존처럼 HTTP 503으로 처리합니다.

유지한 동작
- 대화명 쿠키, 입력 검증, HTML 이스케이프, 페이지당 10개 표시
- 새 글부터 표시, 한국 시각 표시, 저장 후 리다이렉트
- 테이블 잠금과 트랜잭션을 사용한 최대 1,000개 저장 제한
- /health에서 실제 DB 조회, 중복 health() 함수 제거

주의
- 공개 config.json에 포함된 기존 비밀번호는 Supabase에서 교체하세요.
  실제 config.json은 Git 추적에서 제외하고 배포 서버의 비공개 파일로 관리하세요.
  이미 공개된 비밀번호는 파일 삭제나 .gitignore 추가만으로 회수되지 않습니다.
- 기존 SQLite 파일의 데이터는 자동으로 복사하지 않습니다.
  이 변경 적용 후 새 글은 Supabase에 저장됩니다.
- 실제 Supabase 접속/테이블 생성은 실행하지 않았습니다.
  로컬 검증은 구문 검사와 모의 DB 기반 동작 검사입니다.
- GitHub에 커밋하거나 배포하지 않았습니다.

참고
https://supabase.com/docs/guides/database/connecting-to-postgres
https://www.psycopg.org/psycopg3/docs/basic/transactions.html
