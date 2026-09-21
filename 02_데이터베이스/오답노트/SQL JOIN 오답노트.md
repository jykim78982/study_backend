# SQL JOIN 오답노트

### 1. LEFT JOIN 시 반환되는 총 레코드 수

**문제**: menus 테이블의 전체 레코드 수는 61개다. categories(부모)와 menus(자식)를 `menus m LEFT JOIN categories c ON m.category_id = c.id` 형태로 결합했을 때 반환되는 총 레코드 수는? (단, category_id는 유효한 외래키 관계를 만족함)

1. 0개
2. 30개
3. 61개
4. 알 수 없음

**정답: 3번**

- `LEFT JOIN`(왼쪽 외부 조인)은 조인 조건의 만족 여부와 상관없이 **왼쪽(기준) 테이블의 모든 행을 무조건 유지**한다.
- 여기서 기준(왼쪽) 테이블은 `menus`(61개)이고, 오른쪽은 부모 테이블 `categories`다.
- `menus.category_id`는 유효한 외래키이므로 각 메뉴는 카테고리 1개에 매칭되거나 `NULL`이 될 수 있지만, 어느 쪽이든 **자식 테이블의 행 수 자체는 늘거나 줄지 않고 그대로 61개**로 유지된다.

### 2. 부모 테이블의 한글명(kor_name)을 함께 조회하기

**문제**: menus 테이블을 기준으로 부모 테이블인 categories의 한글명(kor_name)을 함께 조회하는 SQL 쿼리로 가장 올바른 것은?

1. `SELECT m.*, c.kor_name AS category_name FROM menus m JOIN categories c ON m.category_id = c.id;`
2. `SELECT m.*, c.kor_name FROM menus m, categories c WHERE m.id = c.id;`
3. `SELECT m.*, (SELECT kor_name FROM categories) FROM menus m;`
4. `SELECT menus.*, categories.kor_name FROM menus UNION SELECT kor_name FROM categories;`

**정답: 1번**

- 자식 테이블(`menus`)의 외래키는 `category_id`이고, 부모 테이블(`categories`)의 기본키는 `id`다. 따라서 올바른 조인 조건은 `m.category_id = c.id`다.
- **2번이 오답인 이유**: `WHERE m.id = c.id`처럼 메뉴의 PK(`m.id`)와 카테고리의 PK(`c.id`)를 직접 연결한 잘못된 조인 키다. 두 테이블의 기본키끼리 비교하는 것은 이 관계와 무관하다.
- **3번이 오답인 이유**: 서브쿼리 `(SELECT kor_name FROM categories)`는 여러 행을 반환할 수 있어 단일행 서브쿼리 에러가 발생한다.
- **4번이 오답인 이유**: `UNION`은 컬럼 개수·성격이 비슷한 두 결과집합을 위아래로 이어 붙이는 연산이지, 서로 다른 테이블의 컬럼을 옆으로 결합하는 조인과는 다른 목적이다.

### 3. 메뉴가 0개인 카테고리도 포함해서 카테고리별 메뉴 수 집계

**문제**: 카테고리 테이블을 기준으로 각 카테고리별 메뉴의 수를 함께 출력하되, 등록된 메뉴가 0개인 카테고리도 목록에 포함시키는 올바른 SQL 쿼리는?

1. `SELECT c.id, c.kor_name, COUNT(m.id) AS menu_count FROM categories c LEFT JOIN menus m ON c.id = m.category_id GROUP BY c.id, c.kor_name;`
2. `SELECT c.id, c.kor_name, COUNT(*) AS menu_count FROM categories c INNER JOIN menus m ON c.id = m.category_id GROUP BY c.id;`
3. `SELECT c.kor_name, SUM(m.id) FROM categories c RIGHT JOIN menus m ON c.id = m.category_id;`
4. `SELECT c.id, COUNT(m.id) FROM categories c, menus m WHERE c.id = m.category_id;`

**정답: 1번**

- 메뉴가 0개인 카테고리도 누락 없이 출력하려면 **카테고리(`categories c`)를 기준으로 `LEFT JOIN`**을 걸어야 한다.
- 건수를 셀 때는 `COUNT(*)`가 아니라 `COUNT(m.id)`를 써야 한다. `COUNT(*)`는 매칭되는 메뉴가 없어 `NULL`로 채워진 행도 1건으로 세어버리지만, `COUNT(m.id)`는 `NULL`을 무시하므로 메뉴가 없는 카테고리의 건수가 정확히 0으로 집계된다.
- **2번이 오답인 이유**: `INNER JOIN`을 쓰면 메뉴가 0개인 카테고리는 결과에서 아예 제외(드롭)된다.
- **3번이 오답인 이유**: `RIGHT JOIN`은 메뉴(`menus`)를 기준으로 조인하므로 메뉴가 없는 카테고리가 다시 빠질 수 있고, `SUM(m.id)`는 메뉴 ID 값들의 합을 구할 뿐 개수를 세는 로직이 아니다.
- **4번이 오답인 이유**: 콤마(`,`) 조인은 사실상 `INNER JOIN`과 같아서, 메뉴가 없는 카테고리는 결과에서 누락된다.

tags: #데이터베이스 #SQL #JOIN #LEFTJOIN

> 🔗 관련 노트: [[041_JOIN — INNER·OUTER와 주인공 개념]]
