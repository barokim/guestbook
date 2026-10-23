# Render 단일 파일 배포본

`templates/index.html` 누락 오류에 대응해 HTML과 CSS를 main.py에 포함했습니다.
기존 학습용 소스로부터 `../prepare_render.py`가 생성한 파일입니다.
학습용 main.py 또는 HTML/CSS를 수정했다면 생성 스크립트를 다시 실행하세요.

## GitHub에서 기존 파일 교체

1. Render 서비스에 연결한 저장소와 브랜치를 확인합니다.
2. **현재 실행되는 기존 main.py를 이 폴더의 main.py로 교체**하고 커밋합니다.
3. requirements.txt도 같은 위치에 있어야 합니다. 기존과 같은 세 패키지를 사용합니다.
4. Render에서 Manual Deploy → Deploy latest commit을 실행합니다.
5. 배포 로그에 `RENDER_SINGLE_FILE_V1: embedded HTML/CSS loaded`가 있는지 확인합니다.

새 main.py를 다른 하위 폴더에만 올리면 기존 파일이 계속 실행될 수 있습니다.
로그에 `templates/index.html`을 읽는 기존 코드가 나오면 커밋·브랜치·실행 위치를 확인하세요.

## Render 설정

이 폴더의 main.py와 requirements.txt를 GitHub 저장소 최상위에 올렸다면:

- Runtime: Python 3
- Root Directory: 비움
- Build Command: pip install -r requirements.txt
- Start Command: python -m uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
- Environment: PYTHON_VERSION=3.12.14
- Health Check Path: /health
- Compute: Free

저장소의 하위 폴더에 파일을 올렸다면 Root Directory는 그 폴더 경로로 맞춥니다.
파일 교체만 했다면 기존 실행 위치와 명령은 유지할 수 있습니다.
SQLite는 Python 내장 sqlite3를 사용합니다. Render 무료 파일 DB는 절전·재시작·재배포 시 사라집니다.
