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

tags: #데이터베이스 #SQL #GROUPBY #HAVING #집계함수

> 🔗 관련 노트: [[040_SQL 필터링·집계·정렬·매핑과 GET 파라미터 처리]]
