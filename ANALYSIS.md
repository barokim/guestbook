# Day1~Day8 분석과 방명록 설계

## 분석 범위

학습 폴더의 직접 작성 코드와 설명 문서를 중심으로 확인했습니다. 가상환경과 설치 패키지는 학습 코드로 계산하지 않았습니다. Day4는 현재 파일이 없어 추정하지 않았습니다. 기존 학습 코드는 수정하지 않았습니다. 아래 오류 언급은 코드 읽기에 근거하며 해당 학습 파일들을 모두 실행한 결과는 아닙니다.

## 날짜별 문법과 알고리즘

| 날짜 | 확인한 자료 예시 | 문법·구조 | 알고리즘·처리 흐름 |
| --- | --- | --- | --- |
| Day1 | `Day1.py`, `day1_2.py`~`day1_5.py`, `day1_practice.py` | 변수, int/input/print, 비교, if/elif/else, 리스트·append, for/range, while/break, 중첩 반복, f-string, import | 합격 판정, 짝수 필터링, 구구단의 이중 반복, 업다운 게임의 상태·점수 갱신 |
| Day2 | `오전/*.py`, `even_sum_and_count/main.py`, `smart_fizzbuzz_analyzer/main.py`, `mask_bad_words.py` | and/or/not, 단락 평가, None 검사, in, dict·items·get, 함수·return, 조건 표현식, 컴프리헨션, zip, 정규표현식, assert | 권한 분기, 짝수 합·개수 누적, FizzBuzz의 배타적 분류, 겹치는 금지어의 마스킹 |
| Day3 | `오전/day3_1.py`~`day3_4.py`, `오후/day3_6.py`, `day3_7*`, `day3_8*` | 클래스, __init__/self, 속성·메서드, property/setter, 상속, 예외·raise, enumerate, 타입 힌트, dataclass, Enum, Decimal | 원두·잔액 등 객체 상태 관리, 할인 후 쿠폰 적용, 입력 검증 후 점수 정규화, 함수·객체 단위 리팩토링 |
| Day4 | 빈 폴더 | 확인 불가 | 확인 불가 |
| Day5 | `Day5_오전/05.FastAPI_unicorn/fastapi_win_vscode/labs/lesson01.py`~`lesson08/` | FastAPI, 데코레이터, GET/POST/PUT/PATCH/DELETE, Annotated, Path/Query, BaseModel, APIRouter | 정적·동적 경로 선택, ID 조회, 입력 검증, CRUD, 조건 필터, skip/limit 페이지 처리, 계층 분리 |
| Day6 | `06_Pydantic_데이터검증_FastAPI/`, `ch08_project/` | BaseModel/Field, ConfigDict, field_validator/model_validator, 중첩 모델, model_validate, model_dump, exclude_unset | 문자열 정리, 범위·필드 간 규칙 검증, 직렬화, PATCH 병합 후 재검증, 회원·작업 CRUD |
| Day7 | `01/demo.py`, `02/main.py`, `03/main.py`, `async_shop/` | async/await, asyncio, AsyncClient, async with, gather/as_completed, HTTP 예외·타임아웃 | 순차 대기와 동시 대기 비교, 외부 API 데이터 취합, 완료 순서 처리 |
| Day8 | 각 차시 `main.py`, `solution.py`, `test_api.py`, README | Swagger/OpenAPI, 매개변수·본문 제약, HTTPException, response_model, pytest 매개변수화 | 문서와 실제 응답 대조, 경곗값 검사, 오류 재현→최소 수정→회귀 검사, 공개 응답 필드 제한 |

## 알고리즘에서 연결되는 원리

1. **조건 순서:** FizzBuzz는 3·5의 공배수부터 확인해야 한 번만 분류됩니다. 방명록도 본문 크기·폼 구조·문자 길이를 확인한 뒤 저장합니다.
2. **누적과 순회:** 짝수 합·개수 계산은 입력 n에 비례하는 순회이며 보조 상태는 일정합니다. 방명록에서는 조회한 최대 10개 행만 순회하여 HTML 목록을 만듭니다.
3. **입력 정리와 검증:** Day3 점수 전처리는 bool, 변환 실패, NaN·무한대, 범위를 구분합니다. 방명록은 문자열의 앞뒤 공백을 제거한 후 빈 값과 길이를 검증합니다.
4. **상태 변경의 일관성:** Day3 객체 상태와 Day6 PATCH 재검증처럼, 저장 전 조건을 만족해야 합니다. SQLite에서는 건수 확인과 INSERT를 같은 트랜잭션으로 묶어 1,000건 상한을 동시에 넘지 않게 합니다.
5. **작은 결과 조회:** Day5의 skip/limit에 해당하는 SQL `LIMIT/OFFSET`으로 페이지를 나눕니다. OFFSET이 커지면 조회 비용이 증가하므로 무한히 확장 가능한 알고리즘으로 설명하지 않습니다. 최대 1,000건의 작은 방명록을 전제로 합니다.
6. **실제 결과 확인:** Day8처럼 상태 코드뿐 아니라 한글·줄바꿈·목록 순서·필드 검증·DB 파일 보존을 확인합니다.

## 원본에서 구분해야 할 부분

- `Day1/day1_5.py`: 루프 전 입력이 비교에 사용되지 않습니다. 정답을 맞히는 일반 분기에 종료가 없으며, 점수 0 검사도 앞선 크기 비교의 elif로 연결되어 종료 조건이 의도대로 작동하지 않을 수 있습니다. `day1_practice.py`에는 다른 흐름으로 정리한 참고 코드가 있습니다.
- `Day2/오전/day2_6.py`의 “딕셔너리는 순서의 개념이 없다”는 주석은 보정이 필요합니다. 학습 환경의 Python 딕셔너리는 삽입 순서를 유지하지만, 리스트처럼 위치 정수로 값을 조회하는 구조는 아닙니다.
- `Day3/오전/day3_2.py`의 `__변수`는 이름 맹글링입니다. 접근 권한을 강제하는 보안 장치로 해석하지 않습니다.
- `Day7/01/demo.py`에는 async 함수 안에 `time.sleep(2)`가 들어 있습니다. 이 구간은 이벤트 루프를 막습니다. async 선언만으로 모든 대기가 비동기가 되지는 않습니다.
- `Day7/03/main.py`의 `/labels`는 as_completed 결과를 완료 순서로 모은 뒤 원래 IDs와 zip합니다. 응답 순서가 바뀌면 ID와 데이터가 잘못 대응할 수 있습니다. 완료 결과에 ID를 함께 보관하거나 요청 순서를 보존하는 수집 방식이 필요합니다.
- Day8 자료는 의도한 결함을 포함합니다. 할인 경곗값, HTTPException을 삼키는 넓은 except, 내부 필드가 포함된 응답 모델은 업무 계약·정답 코드·제공 테스트와 비교해야 합니다. 시작 코드의 동작을 그대로 정답으로 채택하지 않았습니다.

## 방명록에 적용한 범위

| 구현 요소 | 학습 내용과 연결 |
| --- | --- |
| `EntryInput` | Day3 클래스·타입 힌트, Day6 BaseModel·Field·ConfigDict |
| `home`, `create_entry` | Day5 라우팅과 GET/POST |
| 필수값·길이·오류 분기 | Day1~2 조건문, Day6 입력 검증 |
| 기록을 HTML 조각으로 만드는 for문 | Day1 리스트·반복·문자열, Day2 join 활용 |
| 요청 본문의 async 읽기 | Day7 async/await |
| SQLite 작업의 run_in_threadpool | 이미 설치된 FastAPI의 보조 함수. 동기 DB 작업이 async 요청의 이벤트 루프를 직접 막지 않도록 실행 |
| 페이지 계산·LIMIT/OFFSET | Day5 skip/limit 페이지 처리 |
| 오류·경계·회귀 테스트 | Day8 pytest·TestClient |

사용자가 명시한 SQLite는 Python 내장 `sqlite3`로 구현했습니다. `CREATE TABLE`, `INSERT`, `SELECT`, `COUNT`, `ORDER BY`, `LIMIT/OFFSET`은 그 요구를 충족하기 위한 최소 SQL입니다. SQL 값은 문자열로 이어붙이지 않고 매개변수로 전달합니다. 새 외부 라이브러리나 검색·추천·암호화 등 별도 알고리즘은 추가하지 않았습니다.

## 참고 공식 문서

- [Python 3.12 sqlite3](https://docs.python.org/3.12/library/sqlite3.html)
- [HTMLResponse 등 FastAPI 응답](https://fastapi.tiangolo.com/advanced/custom-response/)
- [Python dict와 삽입 순서](https://docs.python.org/3.12/library/stdtypes.html#mapping-types-dict)
- [Python 이름 맹글링](https://docs.python.org/3.12/tutorial/classes.html#private-variables)
