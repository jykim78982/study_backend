# SQL 집계와 그룹화 오답노트

### 1. 집계 함수 사용에 관한 설명

**문제**: 집계 함수 사용과 관련된 설명으로 옳지 않은 것은?

1. 집계된 결과와 일반 컬럼을 함께 `SELECT`하려면 그 일반 컬럼은 `GROUP BY`에 포함되어야 한다.
2. 집계 이전의 행 조건은 `HAVING` 절에서 처리한다.
3. 대표적 집계 함수로 `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`가 있다.
4. `COUNT(column)`는 해당 컬럼의 `NULL`을 제외하고 계산한다.

**정답: 2번**

- **1번(올바른 설명)**: `GROUP BY`를 쓰면 데이터가 그룹 단위로 압축되고, `SUM()`·`AVG()` 같은 집계 함수는 그룹당 결과값 하나만 만든다. 집계되지 않은 일반 컬럼을 그냥 `SELECT`에 쓰면, 그룹화된 한 행에 원본의 여러 행 값 중 무엇을 출력할지 DB가 판단할 수 없어 오류가 난다. 그래서 집계 함수를 쓰지 않은 일반 컬럼은 반드시 `GROUP BY`에 기준 컬럼으로 명시해야 한다(`040` 노트 8절).

  ```sql
  -- 에러 발생 (dept_id가 GROUP BY에 없음)
  SELECT dept_id, AVG(salary)
  FROM employees;

  -- 정상 작동 (dept_id를 GROUP BY에 포함)
  SELECT dept_id, AVG(salary)
  FROM employees
  GROUP BY dept_id;
  ```

- **2번(정답/틀린 설명)**: SQL 실행 순서는 `FROM → WHERE → GROUP BY → HAVING → SELECT`다(`040` 노트 9절). `WHERE`는 그룹화가 이루어지기 전, 원본 테이블의 개별 행을 대상으로 조건을 검사한다. `HAVING`은 `GROUP BY`로 그룹화·집계가 끝난 뒤, 그 집계 결과값(`SUM > 1000` 등)을 대상으로 조건을 검사한다. 즉 **집계 이전의 원본 행을 필터링하는 조건은 `HAVING`이 아니라 `WHERE` 절에서 처리해야 하므로 2번 설명은 틀렸다.**

### 2. SQL SELECT 문 작성 시 표준 작성 순서

**문제**: SQL SELECT 문 작성 시 표준 작성 순서로 올바른 것은?

1. `SELECT → FROM → WHERE → GROUP BY → HAVING → ORDER BY`
2. `SELECT → WHERE → FROM → GROUP BY → HAVING → ORDER BY`
3. `SELECT → FROM → GROUP BY → WHERE → HAVING → ORDER BY`
4. `FROM → SELECT → WHERE → GROUP BY → HAVING → ORDER BY`

**정답: 1번**

- 개발자가 쿼리문을 직접 타이핑할 때 지켜야 하는 문법적 순서는 `SELECT → FROM → WHERE → GROUP BY → HAVING → ORDER BY`로 엄격히 정해져 있다.
- 기억법: **셀-프-웨-그-하-오** (SELECT-FROM-WHERE-GROUP BY-HAVING-ORDER BY)
- 이 문법 순서는 바로 아래 3번 문제의 **내부 실행 순서**와는 다르다는 점에 주의해야 한다.

### 3. SQL SELECT 문의 내부 실행 순서

**문제**: SQL SELECT 문의 내부 실행 순서로 올바른 것은?

1. `SELECT → FROM → WHERE → GROUP BY → HAVING → ORDER BY`
2. `FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY`
3. `FROM → SELECT → WHERE → GROUP BY → HAVING → ORDER BY`
4. `WHERE → FROM → GROUP BY → HAVING → SELECT → ORDER BY`

**정답: 2번**

문법적으로 타이핑하는 순서(2번 문제)와 데이터베이스 엔진이 실제로 처리하는 순서는 다르다.

| 순서 | 절 | 하는 일 |
|---|---|---|
| 1 | `FROM` (+JOIN) | 대상 테이블을 가져온다 |
| 2 | `WHERE` | 행 단위로 조건 필터링 |
| 3 | `GROUP BY` | 지정한 컬럼으로 그룹화 |
| 4 | `HAVING` | 그룹화된 결과를 조건 필터링 |
| 5 | `SELECT` | 최종 컬럼만 추출하고 별칭(Alias) 부여 |
| 6 | `ORDER BY` | 추출된 결과를 정렬 |

**핵심 포인트**: `SELECT`가 `WHERE`·`GROUP BY`보다 나중에 실행되므로, `WHERE` 절 안에서는 `SELECT` 절에서 붙인 별칭(Alias)을 사용할 수 없다.

### 4. 월별로 가장 많이 등록된 월 조회 (PostgreSQL)

**문제**: 메뉴가 월별로 가장 많이 등록된 월을 조회하기 위한 SQL 쿼리로 가장 올바른 것은?

1. `SELECT EXTRACT(MONTH FROM create_time) AS month, COUNT(*) AS cnt FROM menus WHERE EXTRACT(YEAR FROM create_time) = 2024 GROUP BY month ORDER BY cnt DESC LIMIT 1;`
2. `SELECT MONTH(create_time), MAX(id) FROM menus GROUP BY create_time;`
3. `SELECT create_time, COUNT(*) FROM menus WHERE COUNT(*) = MAX(COUNT(*));`
4. `SELECT EXTRACT(MONTH FROM create_time) FROM menus ORDER BY create_time DESC LIMIT 1;`

**정답: 1번**

- PostgreSQL에서 날짜·시간 값에서 월만 뽑아낼 때는 `EXTRACT(MONTH FROM 컬럼명)`을 쓴다. 이렇게 추출한 `month`로 `GROUP BY`하고 `COUNT(*)`로 건수를 집계한 뒤, `ORDER BY cnt DESC LIMIT 1`로 건수가 가장 많은 월 하나만 가져온다.
- **2번이 오답인 이유**: `MONTH()`는 MySQL 계열 함수이고, `MAX(id)`는 "가장 많이 등록된 월"을 구하는 로직이 아니다.
- **3번이 오답인 이유**: `WHERE` 절에는 `COUNT(*)` 같은 집계 함수를 직접 쓸 수 없다. 집계 결과에 대한 조건은 `HAVING`에서 처리해야 한다(1번 문제 참고).
- **4번이 오답인 이유**: `create_time` 기준으로 정렬해 1건만 자르면 "가장 최근에 등록된 메뉴 1건의 월"만 나올 뿐, 월별로 집계한 결과가 아니다.

tags: #데이터베이스 #SQL #GROUPBY #HAVING #집계함수

> 🔗 관련 노트: [[040_SQL 필터링·집계·정렬·매핑과 GET 파라미터 처리]]
