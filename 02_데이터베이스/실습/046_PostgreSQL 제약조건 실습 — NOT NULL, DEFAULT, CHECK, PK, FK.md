---
tags: [데이터베이스, PostgreSQL, 제약조건, 무결성, IDENTITY, UUID, 정규식, 실습]
---

> 🔗 관련 노트: [[086_제약 조건 — 도메인·엔티티·릴레이션 제약과 정규식]] · [[027_제약조건 — 도메인·체크·엔티티·관계 제약과 JPA·스프링에서의 활용 참고자료]]

# PostgreSQL 제약조건 실습 — NOT NULL, DEFAULT, CHECK, PK, FK

이번 실습에서는 제약조건을 이해한 후에, 실제로 테이블에 제약조건을 설정했을 때 그 조건이 잘 지켜지는지 확인해 본다.

**대상**: 제약조건 노트를 읽었고, PostgreSQL 기본 문법(`CREATE TABLE`, `INSERT`, `SELECT`)을 아는 학생

**목표**: 도메인, 체크, 엔티티, 관계 제약을 PostgreSQL에서 순서대로 적용하고 에러 메시지를 확인한다

**완성물**: `categories_N`, `menus_N` 테이블에 모든 제약을 적용하고, 유효/무효 데이터로 검증한 뒤 테이블을 삭제한 상태

> `N`은 공유 DB에서 다른 학생의 테이블과 겹치지 않도록 붙이는 **자기 번호**다. 이 노트에서는 `1`을 사용한다.

> **추가 설명 — 이 실습은 앞 단계의 결과를 이어서 쓴다**: 각 단계는 앞 단계에서 넣은 데이터와 제약이 그대로 남아 있다는 가정으로 진행된다. 원문 그대로 실행하면 5단계의 IDENTITY 번호와 8단계·11단계의 PK 테스트에서 예상과 다른 결과가 나온다. 해당 위치에 바로잡은 SQL을 함께 적어두었다.

## 1. 제약 없는 테이블 만들기

가장 먼저 아무 제약도 없는 테이블을 만들고 데이터를 넣는다. 이 상태가 "문제 발견"의 기준선이 된다.

**1-1. categories_1 테이블 생성**

파일: `sql/01_create_categories.sql`

```sql
CREATE TABLE categories_1 (
    id INTEGER,
    name VARCHAR(50),
    slug VARCHAR(50),
    created_at TIMESTAMP
);
```

**1-2. menus_1 테이블 생성**

파일: `sql/02_create_menus.sql`

```sql
CREATE TABLE menus_1 (
    id INTEGER,
    name VARCHAR(50),
    price INTEGER,
    status VARCHAR(10),
    category_id INTEGER,
    created_at TIMESTAMP
);
```

**1-3. 초기 데이터 입력**

파일: `sql/03_insert_initial.sql`

```sql
INSERT INTO categories_1 (id, name, slug, created_at) VALUES
(1, 'Coffee', 'coffee', NOW()),
(2, 'Tea', 'tea', NOW());

INSERT INTO menus_1 (id, name, price, status, category_id, created_at) VALUES
(1, 'Americano', 4000, 'on', 1, NOW()),
(2, 'Green Tea', 3000, 'on', 2, NOW());
```

**1-4. 데이터 확인**

파일: `sql/04_select_initial.sql`

```sql
SELECT * FROM categories_1;
SELECT * FROM menus_1;
```

**✅ 확인**

- `categories_1`에 2행, `menus_1`에 2행이 보인다.
- 모든 컬럼에 값이 들어 있다.

**🎓 코멘트**: 이 단계의 테이블은 "빈 캔버스"다. 아직 어떤 규칙도 없다. 다음 단계에서 이 빈 캔버스에 문제를 의도적으로 만들어 본다. 실무에서는 이렇게 제약 없는 테이블을 만들지 않지만, 학습을 위해 "제약이 없으면 무엇이 깨지는가"를 먼저 보여주는 것이 중요하다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `relation "categories_1" already exists` | 이전 실행 잔재 | `DROP TABLE IF EXISTS categories_1, menus_1;` 후 재시도 |

**📝 핵심**: 제약 없는 테이블은 NULL을 포함한 모든 값을 허용한다. `NOW()`는 현재 시각을 반환하는 PostgreSQL 함수다.

## 2. NULL이 들어가는 문제 확인하기

제약이 없으므로 NULL을 넣을 수 있다. 이 데이터가 왜 문제인지 확인한다.

**2-1. NULL 데이터 삽입**

파일: `sql/05_insert_null.sql`

```sql
INSERT INTO categories_1 (id, name, slug, created_at) VALUES
(3, NULL, 'mystery', NOW());

INSERT INTO menus_1 (id, name, price, status, category_id, created_at) VALUES
(3, 'Mystery Drink', NULL, NULL, NULL, NOW());
```

**2-2. 데이터 확인**

파일: `sql/06_select_null.sql`

```sql
SELECT * FROM categories_1 WHERE id = 3;
SELECT * FROM menus_1 WHERE id = 3;
```

**✅ 확인**

- `categories_1`의 3행에서 `name`이 NULL이다.
- `menus_1`의 3행에서 `price`, `status`, `category_id`가 NULL이다.
- 에러 없이 INSERT가 성공했다.

**🎓 코멘트**: `name`이 NULL인 카테고리는 "이름 없는 카테고리"다. `price`가 NULL인 메뉴는 "가격 미정"일 수도 있지만, 대부분의 비즈니스 로직에서는 계산이 깨진다. 이 NULL이 "의도된 빈 값"인지 "누락된 값"인지를 구별할 수 없다. 이것이 신뢰할 수 없는 데이터의 시작이다.

> **추가 설명 — 계산이 어떻게 깨지나**: NULL이 섞인 연산의 결과는 NULL이다. `price * 2`는 NULL이 되고, `SUM(price)`는 NULL을 건너뛰어 합계가 조용히 작아진다. `WHERE price > 1000`과 `WHERE price <= 1000` 어느 쪽에도 이 행은 나오지 않는다. 에러가 나지 않고 결과만 틀어지기 때문에 더 찾기 어렵다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| NULL을 넣으려 했는데 `'0'`이 저장됨 | NULL 대신 숫자 `0`을 넣음 | NULL은 NULL로 쓴다. `0`은 값이다. |

> 원문 표에는 이때 `column "name" is of type character varying but expression is of type integer` 에러가 난다고 되어 있지만, PostgreSQL은 INSERT의 값을 문자열 컬럼에 넣을 때 숫자를 문자열로 자동 변환한다. 그래서 에러 없이 **문자열 `'0'`이 저장**된다. 에러가 안 나서 실수를 알아채기 더 어렵다.

**📝 핵심**: 제약이 없으면 NULL은 합법이다. NULL은 "값이 없다"는 의미이지 `0`이나 빈 문자열이 아니다.

## 3. NOT NULL — 필수 컬럼에 NULL 막기

필수 컬럼에 NULL이 들어오지 못하도록 `NOT NULL` 제약을 추가한다. 다만 이전 단계에서 NULL 값을 삽입한 행이 남아 있으면, 제약 적용 시 `column "name" contains null values` 에러가 발생한다. 따라서 제약 적용 전에 기존 NULL 데이터를 처리해야 한다. NULL 행을 삭제하거나, 해당 컬럼에 유효한 값을 채워 넣은 후 제약을 적용한다.

**NULL 데이터 처리 예시**

```sql
-- 방법 1: NULL 값이 포함된 행 삭제
DELETE FROM categories_1 WHERE name IS NULL;

-- 방법 2: NULL 값에 유효한 값 채우기
UPDATE categories_1 SET name = 'unknown' WHERE name IS NULL;
```

> **추가 설명 — menus_1도 정리해야 한다**: 원문 예시는 `categories_1`만 정리하지만, 2단계에서 `menus_1`의 3행에도 `price`와 `status`를 NULL로 넣었다. 그대로 3-2를 실행하면 `column "price" contains null values` 에러가 난다. `menus_1`도 함께 정리한다.
>
> ```sql
> -- 방법 1: 행 삭제
> DELETE FROM menus_1 WHERE price IS NULL OR status IS NULL;
>
> -- 방법 2: 값 채우기 (6단계의 CHECK 조건도 통과하는 값으로)
> UPDATE menus_1 SET price = 1000, status = 'off' WHERE id = 3;
> ```

**3-1. categories_1에 NOT NULL 적용**

파일: `sql/07_add_not_null_categories.sql`

```sql
ALTER TABLE categories_1
ALTER COLUMN name SET NOT NULL,
ALTER COLUMN slug SET NOT NULL;
```

**3-2. menus_1에 NOT NULL 적용**

파일: `sql/08_add_not_null_menus.sql`

```sql
ALTER TABLE menus_1
ALTER COLUMN name SET NOT NULL,
ALTER COLUMN price SET NOT NULL,
ALTER COLUMN status SET NOT NULL;
```

**3-3. NULL INSERT 시도**

파일: `sql/09_insert_null_after_notnull.sql`

```sql
INSERT INTO categories_1 (id, name, slug, created_at) VALUES
(4, NULL, 'test', NOW());
```

**✅ 확인**

- 에러 메시지: `null value in column "name" of relation "categories_1" violates not-null constraint`
- INSERT가 실패한다.

**🎓 코멘트**: NOT NULL은 "이 컬럼에는 반드시 값이 있어야 한다"는 약속이다. 이 약속이 깨지면 데이터 무결성이 무너진다. `created_at`은 보통 NOT NULL이지만, 이 단계에서는 아직 DEFAULT와 함께 다루지 않으므로 생략한다. 실무에서는 `created_at`도 `NOT NULL` + `DEFAULT NOW()`로 만든다.

> **추가 설명 — `category_id`에는 왜 NOT NULL을 안 걸까**: 메뉴가 반드시 카테고리에 속해야 한다면 걸어야 한다. 이 실습에서는 "카테고리 미지정 메뉴"를 허용하는 설계로 두었다. 10단계의 FK는 NULL을 검사하지 않으므로, NOT NULL이 없으면 `category_id`가 비어 있는 메뉴가 계속 들어갈 수 있다는 점을 기억해 둔다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `column "name" contains null values` | 기존 NULL 데이터가 남아 있어 제약 적용 실패 | 기존 NULL 행을 삭제하거나 값을 채운 후 제약 적용 |

**📝 핵심**: NOT NULL은 컬럼 레벨 제약이다. 기존 NULL 데이터가 있으면 제약 적용이 실패한다.

## 4. DEFAULT — 생략한 컬럼에 기본값 채우기

`created_at` 같은 컬럼은 사용자가 매번 입력하면 안 된다. DEFAULT로 기본값을 설정한다.

**4-1. categories_1에 DEFAULT 적용**

파일: `sql/10_add_default_categories.sql`

```sql
ALTER TABLE categories_1
ALTER COLUMN created_at SET DEFAULT NOW();
```

**4-2. menus_1에 DEFAULT 적용**

파일: `sql/11_add_default_menus.sql`

```sql
ALTER TABLE menus_1
ALTER COLUMN created_at SET DEFAULT NOW();
```

**4-3. created_at 생략하고 INSERT**

파일: `sql/12_insert_without_created_at.sql`

```sql
INSERT INTO categories_1 (id, name, slug) VALUES
(5, 'Juice', 'juice');

INSERT INTO menus_1 (id, name, price, status, category_id) VALUES
(4, 'Orange Juice', 5000, 'on', 5);
```

**4-4. created_at 확인**

파일: `sql/13_select_created_at.sql`

```sql
SELECT id, name, created_at FROM categories_1 WHERE id = 5;
SELECT id, name, created_at FROM menus_1 WHERE id = 4;
```

**✅ 확인**

- `created_at`에 현재 시각이 자동으로 들어왔다.
- INSERT 문에서 `created_at`을 명시하지 않아도 성공했다.

**🎓 코멘트**: DEFAULT는 "값을 안 주면 이 값을 쓴다"는 규칙이다. `NOW()`는 INSERT 시점에 평가되므로 고정된 값이 아니라 그때그때의 시각이 들어간다. 실무에서는 `created_at`에 `DEFAULT NOW()`를 붙이는 것이 표준이다.

> 원문은 "여러 행을 한 번에 넣어도 각 행마다 현재 시각이 들어간다"고 설명하지만, PostgreSQL의 `NOW()`는 **트랜잭션이 시작된 시각**을 돌려준다. 그래서 한 INSERT 문(또는 한 트랜잭션)으로 여러 행을 넣으면 모든 행에 **같은 시각**이 들어간다. 매 호출마다 실제 현재 시각이 필요하면 `clock_timestamp()`를 쓴다.

> **추가 설명 — NULL을 직접 넣으면 기본값이 안 들어간다**: DEFAULT는 컬럼을 **생략**했을 때만 적용된다. `INSERT INTO categories_1 (id, name, slug, created_at) VALUES (9, 'X', 'x', NULL);`처럼 NULL을 명시하면 `created_at`에 NULL이 저장된다. 이것까지 막으려면 `created_at`에 NOT NULL도 함께 건다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `column "created_at" is of type timestamp without time zone but default expression is of type integer` | DEFAULT에 숫자 `0`을 씀 | `DEFAULT NOW()`로 쓴다. |

**📝 핵심**: DEFAULT는 INSERT 시 생략된 컬럼에 값을 채운다. `NOW()`는 함수이므로 INSERT 시점에 평가된다.

## 5. id 자동 생성 — IDENTITY, now(), UUID

`id` 컬럼에 고정 기본값(예: `DEFAULT 1`)이 남아 있으면 `ALTER COLUMN ... ADD GENERATED ALWAYS AS IDENTITY` 실행 시 오류가 발생한다. 이 오류를 피하려면 먼저 기존 기본값을 제거한 뒤 IDENTITY 속성을 부여해야 한다. 아래 세 가지 방식을 비교한다.

**기존 기본값 제거 예제**

```sql
ALTER TABLE categories_1 ALTER COLUMN id DROP DEFAULT;
```

**5-1. IDENTITY 방식 (categories_1)**

파일: `sql/14_identity_categories.sql`

`GENERATED ALWAYS AS IDENTITY` 속성을 추가할 때 `id` 컬럼에 NOT NULL 제약 조건이 없으면 오류가 발생한다. IDENTITY 컬럼은 NULL 값을 허용할 수 없기 때문이다. 이를 방지하기 위해 NOT NULL 제약 조건을 먼저 추가한 뒤 IDENTITY 속성을 부여한다.

```sql
ALTER TABLE categories_1
ALTER COLUMN id DROP DEFAULT,
ALTER COLUMN id SET NOT NULL,
ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY;
```

> **원문 바로잡기 — 번호가 1부터 시작한다**: 기존 컬럼에 IDENTITY를 붙이면 번호 생성기(시퀀스)는 **기존 데이터와 상관없이 1부터** 시작한다. 이미 `id` 1, 2, 5가 있는데 다음 INSERT가 `id = 1`을 받는다. 아직 PK가 없어서 에러 없이 **중복 id가 들어가고**, 8단계에서 PK를 걸 때 `could not create unique index "pk_categories_id"` / `Key (id)=(1) is duplicated` 에러로 실패한다. 원문의 "자동으로 증가한다(예: 6, 7, ...)"가 나오려면, IDENTITY를 붙인 직후 시작 번호를 기존 최댓값 다음으로 옮겨야 한다.
>
> ```sql
> -- 현재 최대 id가 5이므로 6부터 시작
> ALTER TABLE categories_1 ALTER COLUMN id RESTART WITH 6;
> ```
>
> 처음부터 `ADD GENERATED ALWAYS AS IDENTITY (START WITH 6)`처럼 시작 번호를 지정해도 된다.

**5-2. now() 기반 timestamp id (menus_1)**

파일: `sql/15_timestamp_id_menus.sql`

```sql
ALTER TABLE menus_1
ALTER COLUMN id DROP DEFAULT,
ALTER COLUMN id SET DEFAULT (EXTRACT(EPOCH FROM NOW())::BIGINT);
```

> **추가 설명 — epoch 값이란**: `EXTRACT(EPOCH FROM NOW())`는 1970-01-01 00:00:00(UTC)부터 지금까지 흐른 **초**다. 2026년 기준 약 17억 9천만이라 `INTEGER`(최대 약 21억)에 아직 들어가지만, 2038년에 넘친다(**2038년 문제**). 또 같은 초(같은 트랜잭션)에 두 행을 넣으면 **같은 id**가 나온다. PK를 건 뒤에는 두 번째 INSERT가 중복 키 에러로 실패한다. 세 방식을 비교하기 위한 예시일 뿐, 실제로 쓰는 방식은 아니다.

**5-3. UUID 방식 (새 테이블 categories_uuid)**

파일: `sql/16_uuid_categories.sql`

```sql
CREATE TABLE categories_uuid (
    id UUID DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    slug VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO categories_uuid (name, slug) VALUES ('Test', 'test');
SELECT id, name FROM categories_uuid;
```

**5-4. IDENTITY INSERT 테스트**

파일: `sql/17_insert_identity.sql`

```sql
INSERT INTO categories_1 (name, slug) VALUES ('Smoothie', 'smoothie');
SELECT id, name FROM categories_1 WHERE name = 'Smoothie';
```

**✅ 확인**

- `categories_1`의 `id`가 자동으로 증가한다(5-1의 `RESTART WITH 6`을 실행했다면 6, 7, ...).
- `menus_1`의 `id`가 epoch 초 단위로 생성된다.
- `categories_uuid`의 `id`가 36자리의 UUID 문자열(`a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11` 형태)로 보인다.

**🎓 코멘트**: IDENTITY는 PostgreSQL 10 이후의 표준 방식이다. SERIAL은 구식이다. now() 기반 id는 분산 환경에서 충돌할 수 있다. UUID는 무한히 확장 가능하지만 인덱스 성능이 떨어진다. 실무에서는 단일 노드에서는 IDENTITY, 분산 환경에서는 UUID를 고려한다.

> **추가 설명 — 세 방식 비교**
>
> | 방식 | 장점 | 단점 |
> |---|---|---|
> | IDENTITY | 작고(4~8바이트) 순서대로 쌓여 인덱스에 유리 | DB 한 곳에서만 번호를 발급할 수 있다. id로 데이터 개수나 순서가 드러난다 |
> | now() epoch | 만들기 쉽다 | 같은 초에 중복 발생, 2038년 문제. 실무에서 쓰지 않는다 |
> | UUID | DB에 묻지 않고 어디서든 겹칠 걱정 없이 만들 수 있다. id를 추측하기 어렵다 | 16바이트로 크다. 무작위 값이라 인덱스 곳곳에 끼워 넣어져 INSERT 성능이 떨어진다 |
>
> "UUID는 무한히 확장 가능"은 **중앙에서 번호를 발급하지 않아도 여러 서버가 각자 만들 수 있다**는 뜻이다. 화면에는 36자로 보이지만 실제 저장은 16바이트다. 무작위성 때문에 생기는 인덱스 문제를 줄이려고 시간 순으로 정렬되는 **UUID v7**도 쓰이며, PostgreSQL 18부터 `uuidv7()` 함수가 내장되었다.

> **추가 설명 — `GENERATED ALWAYS` vs `BY DEFAULT`**: `ALWAYS`는 id를 직접 넣는 것을 **거부**하고, `BY DEFAULT`는 값을 생략했을 때만 자동 생성하고 직접 넣는 것도 허용한다. 이 차이가 8단계와 11단계의 PK 테스트에 영향을 준다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `column "id" is of type integer but expression is of type uuid` | UUID 값을 INTEGER 컬럼에 넣음 | 컬럼 타입을 UUID로 변경하거나 IDENTITY 사용 |
| `column "id" of relation "categories_1" must be declared NOT NULL before identity can be added` | NOT NULL 없이 IDENTITY 추가 | `SET NOT NULL`을 먼저 실행 |

**📝 핵심**: IDENTITY는 자동 증가를 위한 표준 방식이다. `gen_random_uuid()`는 PostgreSQL 13 이상에서 확장 설치 없이 사용할 수 있다.

## 6. CHECK — 값의 범위 제한하기

"값은 들어왔다. 그런데 `price = -100`, `status = 'maybe'` 같은 값도 들어갈 수 있다."

> 원문에는 `status = 'off'`가 문제 값의 예로 나오지만, 아래 6-2에서 `'off'`는 **허용하는** 값이다. 막아야 할 값의 예는 `'maybe'`처럼 정해진 목록 밖의 값이다.

**6-1. price CHECK 적용**

파일: `sql/18_check_price.sql`

```sql
ALTER TABLE menus_1
ADD CONSTRAINT chk_price_positive CHECK (price > 0);
```

**6-2. status CHECK 적용**

파일: `sql/19_check_status.sql`

```sql
ALTER TABLE menus_1
ADD CONSTRAINT chk_status_valid CHECK (status IN ('on', 'off'));
```

**6-3. 범위를 벗어난 INSERT 시도**

파일: `sql/20_insert_invalid_check.sql`

```sql
INSERT INTO menus_1 (name, price, status, category_id) VALUES
('Negative Price', -100, 'on', 1);

INSERT INTO menus_1 (name, price, status, category_id) VALUES
('Invalid Status', 1000, 'maybe', 1);
```

**✅ 확인**

- 첫 번째 INSERT 에러: `new row for relation "menus_1" violates check constraint "chk_price_positive"`
- 두 번째 INSERT 에러: `new row for relation "menus_1" violates check constraint "chk_status_valid"`
- 두 INSERT 모두 실패한다.

**🎓 코멘트**: CHECK는 "이 컬럼의 값은 이 조건을 만족해야 한다"는 규칙이다. `IN ('on', 'off')`는 ENUM과 유사하지만, 테이블 레벨 제약으로 걸면 여러 컬럼을 함께 검증할 수도 있다. `price > 0`은 음수 가격을 막는 최소한의 방어다.

> **추가 설명 — CHECK는 NULL을 통과시킨다**: `price`가 NULL이면 `price > 0`의 결과는 거짓이 아니라 "모름(UNKNOWN)"이라 CHECK를 **통과**한다. 이 실습에서 NULL을 막을 수 있는 것은 3단계에서 건 NOT NULL 덕분이다. CHECK와 NOT NULL은 함께 써야 한다.

> **추가 설명 — 기존 데이터도 검사한다**: `ADD CONSTRAINT ... CHECK`는 이미 들어 있는 행도 검사한다. 3단계에서 `menus_1`의 3행을 `status = 'unknown'`처럼 목록 밖의 값으로 채웠다면 `check constraint "chk_status_valid" of relation "menus_1" is violated by some row` 에러로 제약 추가가 실패한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `syntax error at or near "IN"` | CHECK 문법 오류 | `CHECK (status IN ('on', 'off'))`로 정확히 쓴다. |

**📝 핵심**: CHECK는 컬럼의 값 범위를 제한한다. 제약 이름(`chk_price_positive`)은 에러 메시지에 표시되므로 의미 있게 짓는다.

## 7. 정규식 CHECK — 문자열 패턴 검증하기

`slug`에 대문자·공백이 섞여도 단순 비교로는 못 잡는다. 정규식으로 보완한다.

> **추가 설명 — slug란**: URL에 들어가는 사람이 읽을 수 있는 식별 문자열이다. `/categories/cold-brew`의 `cold-brew` 부분이다. 주소에 쓰이므로 소문자, 숫자, 하이픈(`-`)만 쓰는 것이 관례다.

**7-1. slug 정규식 CHECK 적용**

파일: `sql/21_check_slug_regex.sql`

```sql
ALTER TABLE categories_1
ADD CONSTRAINT chk_slug_pattern CHECK (slug ~ '^[a-z0-9-]+$');
```

**7-2. 유효한 slug INSERT**

파일: `sql/22_insert_valid_slug.sql`

```sql
INSERT INTO categories_1 (name, slug) VALUES ('Cold Brew', 'cold-brew');
```

**7-3. 무효한 slug INSERT**

파일: `sql/23_insert_invalid_slug.sql`

```sql
INSERT INTO categories_1 (name, slug) VALUES ('Bad Slug', 'Cold Brew');

INSERT INTO categories_1 (name, slug) VALUES ('Bad Slug 2', 'bad_slug');
```

**✅ 확인**

- `cold-brew` INSERT 성공.
- `Cold Brew` INSERT 에러: `new row for relation "categories_1" violates check constraint "chk_slug_pattern"` (대문자와 공백)
- `bad_slug` INSERT 에러: 같은 에러 메시지 (밑줄 `_`은 허용 목록에 없음)

**🎓 코멘트**: `~`는 PostgreSQL의 정규식 매칭 연산자다. `^[a-z0-9-]+$`는 "소문자, 숫자, 하이픈만 포함하고, 하나 이상"이라는 뜻이다. `^`는 시작, `$`는 끝을 의미한다. 실무에서는 slug에 대문자를 허용하지 않는 것이 URL 관례에 부합한다.

> **추가 설명 — 패턴 뜯어보기와 더 엄격한 버전**
>
> | 조각 | 의미 |
> |---|---|
> | `^` / `$` | 문자열의 시작 / 끝. 둘 다 있어야 "전체가" 패턴과 일치해야 한다 |
> | `[a-z0-9-]` | 소문자, 숫자, 하이픈 중 한 글자. 대괄호 맨 끝의 `-`는 범위가 아니라 하이픈 문자 그 자체다 |
> | `+` | 앞의 것이 1번 이상 |
>
> 이 패턴은 `-coffee`, `coffee-`, `cold--brew`처럼 하이픈이 앞뒤에 오거나 연속되는 값도 통과시킨다. 이것까지 막으려면 "단어(하이픈) 단어" 구조로 쓴다.
>
> ```sql
> CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$')
> ```
>
> `^`와 `$`를 빼면 "어딘가에 한 글자라도 맞으면" 통과하므로 `'Cold Brew'`도 통과해 버린다. PostgreSQL에는 대소문자를 무시하는 `~*`, 일치하지 않음을 뜻하는 `!~`도 있다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| 정규식 연산자 관련 문법 에러 | `~`는 PostgreSQL 전용 연산자 | 다른 DBMS를 사용 중인지 확인한다. Oracle은 `REGEXP_LIKE(slug, '^[a-z0-9-]+$')`, MySQL은 `slug REGEXP '^[a-z0-9-]+$'`를 쓴다. |

**📝 핵심**: `~`는 정규식 매칭에 사용한다. `^[a-z0-9-]+$`는 소문자·숫자·하이픈만 허용하는 패턴이다.

## 8. PRIMARY KEY — 같은 행의 중복 막기

"이제 모든 컬럼은 유효한 도메인 범위의 값을 가진다. 그렇다면 정말 결함 없는 걸까?" 아니다. 같은 레코드가 세 번 들어오면?

**8-1. categories_1에 PRIMARY KEY 적용**

파일: `sql/24_primary_key_categories.sql`

```sql
ALTER TABLE categories_1
ADD CONSTRAINT pk_categories_id PRIMARY KEY (id);
```

**8-2. menus_1에 PRIMARY KEY 적용**

파일: `sql/25_primary_key_menus.sql`

```sql
ALTER TABLE menus_1
ADD CONSTRAINT pk_menus_id PRIMARY KEY (id);
```

**8-3. 동일 PK INSERT 시도**

파일: `sql/26_insert_duplicate_pk.sql`

```sql
INSERT INTO categories_1 (id, name, slug) VALUES (1, 'Duplicate Coffee', 'coffee-dup');
```

**✅ 확인**

- 에러 메시지: `cannot insert a non-DEFAULT value into column "id"` / `Column "id" is an identity column defined as GENERATED ALWAYS.`
- INSERT가 실패한다.

> **원문 바로잡기 — 이 에러는 PK 위반이 아니다**: 위 에러는 `id`가 `GENERATED ALWAYS` IDENTITY 컬럼이라서 **id를 직접 넣는 것 자체를 거부**한 것이다. PK 검사까지 가지도 않았다. PK 중복을 직접 확인하려면 `OVERRIDING SYSTEM VALUE`로 IDENTITY를 무시하고 값을 넣어 본다.
>
> ```sql
> INSERT INTO categories_1 (id, name, slug)
> OVERRIDING SYSTEM VALUE
> VALUES (1, 'Duplicate Coffee', 'coffee-dup');
> -- 에러: duplicate key value violates unique constraint "pk_categories_id"
> --       Key (id)=(1) already exists.
> ```
>
> `menus_1`은 IDENTITY가 아니므로 `INSERT INTO menus_1 (id, name, price, status) VALUES (1, 'Dup', 1000, 'on');`으로도 같은 PK 중복 에러를 볼 수 있다.

> 5-1에서 `RESTART WITH 6`을 실행하지 않았다면 8-1 자체가 `could not create unique index "pk_categories_id"` 에러로 실패한다. 이미 중복 id가 들어가 있기 때문이다. 이 경우 `SELECT id, COUNT(*) FROM categories_1 GROUP BY id HAVING COUNT(*) > 1;`로 중복 행을 찾아 정리한 뒤 다시 실행한다.

**🎓 코멘트**: PRIMARY KEY는 "이 레코드를 유일하게 식별하는 값"이다. NULL을 허용하지 않고, 중복을 허용하지 않는다. `id`가 PRIMARY KEY이면, `id = 1`인 레코드는 단 하나만 존재한다. 이것이 "엔티티"의 정의다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `column "id" contains null values` | 기존 NULL id가 있어 PK 적용 실패 | NULL id 행을 삭제하거나 값을 채운 후 적용 |
| `could not create unique index ...` / `Key (id)=(...) is duplicated` | 기존 id가 중복됨 | 중복 행을 찾아 정리한 후 적용 |

**📝 핵심**: PRIMARY KEY는 UNIQUE + NOT NULL의 조합이다. PK는 테이블당 **하나만** 만들 수 있다(여러 컬럼을 묶은 복합 PK도 PK 하나다).

> 원문은 "테이블당 하나만 권장된다"고 했지만, 권장이 아니라 규칙이다. PK를 두 번 추가하면 `multiple primary keys for table "categories_1" are not allowed` 에러가 난다.

## 9. UNIQUE — PK가 아닌 컬럼의 중복 막기

`slug`는 URL에 사용되므로 중복되면 안 된다.

**9-1. categories_1에 UNIQUE 적용**

파일: `sql/27_unique_slug_categories.sql`

```sql
ALTER TABLE categories_1
ADD CONSTRAINT uq_categories_slug UNIQUE (slug);
```

**9-2. menus_1에 UNIQUE 적용**

파일: `sql/28_unique_slug_menus.sql`

```sql
ALTER TABLE menus_1
ADD CONSTRAINT uq_menus_name UNIQUE (name);
```

> `menus_1`에는 `slug` 컬럼이 없으므로, 메뉴는 **이름**이 겹치지 않도록 UNIQUE를 건다(파일 이름은 원문 그대로 두었다).

**9-3. 중복 slug INSERT 시도**

파일: `sql/29_insert_duplicate_slug.sql`

```sql
INSERT INTO categories_1 (name, slug) VALUES ('Another Coffee', 'coffee');
```

**✅ 확인**

- 에러 메시지: `duplicate key value violates unique constraint "uq_categories_slug"`
- INSERT가 실패한다.

**🎓 코멘트**: UNIQUE는 "이 컬럼의 값은 중복되면 안 된다"는 규칙이다. PRIMARY KEY와 달리 NULL을 허용한다(PostgreSQL은 NULL끼리를 서로 다른 값으로 취급하므로 NULL이 여러 개 들어갈 수 있다). slug가 중복되면 같은 주소(`/categories/coffee`)에 어떤 카테고리를 보여줘야 할지 정할 수 없다.

> 원문은 "slug가 중복되면 404 에러가 난다"고 했지만, 404는 대상을 **못 찾을** 때의 응답이다. slug가 중복되면 오히려 대상이 **둘 이상 찾아져서** 엉뚱한 카테고리가 보이거나, 단건 조회 코드에서 "결과가 2개 이상"이라는 서버 에러(500)가 난다.

> **추가 설명 — 지금 slug에는 NULL이 들어갈 수 없다**: 3단계에서 `slug`에 NOT NULL을 걸었으므로, "UNIQUE는 NULL을 허용한다"는 성질은 이 테이블에서는 드러나지 않는다. 업무상 필수이면서 겹치면 안 되는 값(대체 키)은 이처럼 `NOT NULL` + `UNIQUE`를 함께 거는 것이 일반적이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `duplicate key value violates unique constraint "uq_categories_slug"` | 기존 `'coffee'` slug가 있음 | 기존 행을 수정하거나 삭제 후 재시도 |
| `could not create unique index "uq_menus_name"` | UNIQUE를 추가하기 전에 이미 같은 이름의 메뉴가 들어가 있음 | 중복 행을 정리한 후 제약 적용 |

**📝 핵심**: UNIQUE는 중복을 막지만 NULL을 허용한다. slug는 UNIQUE여야 URL이 안정적이다.

## 10. FOREIGN KEY — 존재하지 않는 부모 참조 막기

"엔티티 중복은 사라졌다. 이제 문제는 없는 걸까?" 아니다. `menus_1`에 `category_id = 999`를 넣으면?

**10-1. menus_1에 FOREIGN KEY 적용**

파일: `sql/30_foreign_key_menus.sql`

```sql
ALTER TABLE menus_1
ADD CONSTRAINT fk_menus_category
FOREIGN KEY (category_id) REFERENCES categories_1 (id);
```

**10-2. 존재하지 않는 category_id INSERT**

파일: `sql/31_insert_invalid_fk.sql`

```sql
INSERT INTO menus_1 (name, price, status, category_id) VALUES
('Ghost Menu', 1000, 'on', 999);
```

**✅ 확인**

- 에러 메시지: `insert or update on table "menus_1" violates foreign key constraint "fk_menus_category"`
- INSERT가 실패한다.

**🎓 코멘트**: FOREIGN KEY는 "이 값은 다른 테이블의 PK나 UNIQUE 값에 존재해야 한다"는 규칙이다. `category_id = 999`는 `categories_1`에 없으므로 에러가 난다. 이것이 "참조(관계) 무결성"이다. 부모가 없으면 자식이 존재할 수 없다.

> **추가 설명 — 단, NULL은 통과한다**: FK는 값이 **있을 때만** 부모를 확인한다. `category_id`가 NULL이면 검사하지 않고 통과한다. "부모가 없는 자식"을 완전히 막으려면 `category_id`에 NOT NULL도 함께 걸어야 한다.

> **추가 설명 — 부모 쪽에서도 막힌다**: FK는 자식 INSERT만 검사하는 것이 아니다. 메뉴가 연결된 카테고리를 지우려 하면 기본 동작(`NO ACTION`)에 따라 거부된다.
>
> ```sql
> DELETE FROM categories_1 WHERE id = 1;
> -- 에러: update or delete on table "categories_1" violates foreign key constraint
> --       "fk_menus_category" on table "menus_1"
> ```
>
> 부모가 지워질 때 자식을 어떻게 할지는 `ON DELETE CASCADE`(같이 삭제), `ON DELETE SET NULL`(연결만 끊기) 같은 옵션으로 정할 수 있다.

> **추가 설명 — FK 컬럼에는 인덱스를 직접 만든다**: PostgreSQL은 PK와 UNIQUE에는 인덱스를 자동으로 만들지만 **FK 컬럼에는 만들지 않는다.** 조인과 부모 삭제 시 검사가 빨라지도록 `CREATE INDEX idx_menus_1_category_id ON menus_1 (category_id);`를 만들어 두는 것이 좋다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `there is no unique constraint matching given keys for referenced table "categories_1"` | 참조 대상 컬럼에 PK나 UNIQUE가 없음 | `categories_1.id`에 PK가 있는지 확인 |
| `insert or update on table "menus_1" violates foreign key constraint` (FK 추가 시) | 이미 없는 카테고리를 가리키는 메뉴가 있음 | 해당 행의 `category_id`를 고치거나 삭제 후 적용 |

**📝 핵심**: FOREIGN KEY는 두 테이블을 연결한다. 참조 대상 컬럼에는 PK나 UNIQUE가 있어야 한다.

## 11. 최종 검증 — 유효/무효 데이터로 모든 제약 확인하기

모든 제약을 적용한 상태에서 유효/무효 데이터를 넣고 에러 메시지를 확인한다.

**11-1. 유효 데이터 INSERT**

파일: `sql/32_insert_valid_final.sql`

```sql
INSERT INTO categories_1 (name, slug) VALUES ('Dessert', 'dessert');

INSERT INTO menus_1 (name, price, status, category_id) VALUES
('Cheesecake', 7000, 'on', (SELECT id FROM categories_1 WHERE slug = 'dessert'));
```

> 카테고리 id가 IDENTITY로 자동 생성되어 미리 알 수 없으므로, 서브쿼리로 slug를 이용해 id를 찾아 넣는다. slug에 UNIQUE가 걸려 있어서 이 서브쿼리는 항상 한 행만 돌려준다.

**11-2. NOT NULL 위반**

파일: `sql/33_test_not_null.sql`

```sql
INSERT INTO categories_1 (name, slug) VALUES (NULL, 'test-null');
```

**11-3. CHECK 위반**

파일: `sql/34_test_check.sql`

```sql
INSERT INTO menus_1 (name, price, status, category_id) VALUES
('Bad Price', -50, 'on', 1);
```

**11-4. PK 위반**

파일: `sql/35_test_pk.sql`

```sql
INSERT INTO categories_1 (id, name, slug)
OVERRIDING SYSTEM VALUE
VALUES (1, 'Dup PK', 'dup-pk');
```

> 원문은 `OVERRIDING SYSTEM VALUE` 없이 `INSERT INTO categories_1 (id, name, slug) VALUES (1, 'Dup PK', 'dup-pk');`로 되어 있다. 그대로 실행하면 8-3과 마찬가지로 `GENERATED ALWAYS` 에러가 나서 PK 위반 메시지를 볼 수 없다.

**11-5. FK 위반**

파일: `sql/36_test_fk.sql`

```sql
INSERT INTO menus_1 (name, price, status, category_id) VALUES
('Orphan Menu', 1000, 'on', 9999);
```

**11-6. 최종 데이터 확인**

파일: `sql/37_select_final.sql`

```sql
SELECT * FROM categories_1 ORDER BY id;
SELECT * FROM menus_1 ORDER BY id;
```

**✅ 확인**

- 11-1: INSERT 성공.
- 11-2: `null value in column "name" of relation "categories_1" violates not-null constraint` 에러.
- 11-3: `violates check constraint "chk_price_positive"` 에러.
- 11-4: `duplicate key value violates unique constraint "pk_categories_id"` 에러.
- 11-5: `violates foreign key constraint "fk_menus_category"` 에러.
- 11-6: 유효한 데이터만 테이블에 남아 있다.

> 11-6에서 `categories_1`의 id가 중간중간 비어 있을 수 있다. IDENTITY는 INSERT가 실패해도 **이미 뽑은 번호를 되돌리지 않기** 때문이다(7-3, 9-3, 11-2에서 실패한 INSERT가 번호를 소비했다). id는 식별용이지 개수를 세는 용도가 아니므로 문제가 아니다.

**🎓 코멘트**: 이 단계가 핵심이다. 각 제약이 실제로 작동하는지 에러 메시지로 확인한다. 에러 메시지에 제약 이름(`chk_price_positive`, `pk_categories_id`, `fk_menus_category`)이 표시되므로, 어떤 제약이 깨졌는지 바로 알 수 있다. 실무에서는 이 에러 메시지를 로그로 기록하고 모니터링한다.

> **추가 설명 — 위반별 SQLSTATE 코드**: PostgreSQL은 에러마다 5자리 코드를 붙인다. 애플리케이션(스프링 등)은 이 코드로 어떤 종류의 위반인지 구분한다.
>
> | 위반 | SQLSTATE |
> |---|---|
> | NOT NULL | `23502` |
> | FOREIGN KEY | `23503` |
> | UNIQUE / PRIMARY KEY | `23505` |
> | CHECK | `23514` |

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| 한 INSERT에서 에러를 고쳤더니 다른 제약 에러가 또 남 | 한 행이 여러 제약을 동시에 어김 | PostgreSQL은 **처음 걸린 제약 하나만** 보고하고 멈춘다. 에러 메시지의 제약 이름을 보고 하나씩 고친다. |

> 원문 표의 `cannot insert into table "menus_1"`이라는 메시지는 PostgreSQL이 제약 위반으로 내는 메시지가 아니다. 제약 위반은 항상 위에서 본 것처럼 어떤 제약이 깨졌는지 이름을 담은 메시지로 나온다.

**📝 핵심**: 각 제약은 독립적으로 작동한다. 에러 메시지에 제약 이름이 표시된다.

## 12. 정리 — 연습 테이블 삭제하기

실습을 마쳤으므로 연습 테이블을 삭제한다.

**12-1. menus_1 삭제**

파일: `sql/38_drop_menus.sql`

```sql
DROP TABLE menus_1;
```

**12-2. categories_1 삭제**

파일: `sql/39_drop_categories.sql`

```sql
DROP TABLE categories_1;
```

**12-3. categories_uuid 삭제**

파일: `sql/40_drop_uuid.sql`

```sql
DROP TABLE categories_uuid;
```

> **추가 설명 — 왜 menus_1부터 지우나**: `menus_1`이 FK로 `categories_1`을 참조하고 있다. 부모인 `categories_1`을 먼저 지우려 하면 `cannot drop table categories_1 because other objects depend on it` 에러가 난다. 자식부터 지우거나, 두 테이블을 `DROP TABLE menus_1, categories_1;`처럼 한 번에 지운다. `DROP TABLE categories_1 CASCADE;`는 **FK 제약만** 함께 지우고 `menus_1` 테이블은 남긴다.

**✅ 확인**

- `SELECT * FROM categories_1;` 실행 시 `relation "categories_1" does not exist` 에러.
- `SELECT * FROM menus_1;` 실행 시 `relation "menus_1" does not exist` 에러.
- `SELECT * FROM categories_uuid;` 실행 시 `relation "categories_uuid" does not exist` 에러.

**🎓 코멘트**: 연습 테이블은 학습용이다. 공유 인스턴스에서는 남의 테이블을 건드리지 않도록 `N`을 붙여 구분한다. 실습이 끝나면 `DROP TABLE`로 정리한다. `DROP TABLE`은 되돌릴 수 없으므로, 필요한 데이터는 삭제 전에 백업한다.

> 원문은 "삭제 전 SELECT로 데이터를 백업한다"고 했지만, `SELECT`는 화면에 보여줄 뿐 데이터를 따로 저장하지 않는다. 백업은 `CREATE TABLE categories_1_backup AS SELECT * FROM categories_1;`처럼 복사본 테이블을 만들거나, `pg_dump -t categories_1`로 파일에 내보내는 방식으로 한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `table "menus_1" does not exist` | 이미 삭제됨 | 무시한다. 이미 삭제된 상태다. 스크립트를 반복 실행한다면 `DROP TABLE IF EXISTS menus_1;`로 쓴다. |

**📝 핵심**: `DROP TABLE`은 테이블을 영구 삭제한다. 공유 환경에서는 연습 테이블을 반드시 정리한다.

## 전체 정리

| 단계 | 핵심 |
|---|---|
| 1 | 제약 없는 테이블은 NULL 포함 모든 값을 허용한다. |
| 2 | NULL은 "값이 없다"는 의미이며, 신뢰할 수 없는 데이터의 시작이다. |
| 3 | NOT NULL은 필수 컬럼에 NULL을 차단한다. |
| 4 | DEFAULT는 INSERT 시 생략된 컬럼에 기본값을 채운다. |
| 5 | IDENTITY, now(), UUID는 id 생성의 세 가지 방식이다. |
| 6 | CHECK는 값의 범위를 제한한다. |
| 7 | 정규식 `~`는 문자열 패턴을 검증한다. |
| 8 | PRIMARY KEY는 레코드를 유일하게 식별한다. |
| 9 | UNIQUE는 중복을 막지만 NULL을 허용한다. |
| 10 | FOREIGN KEY는 관계 무결성을 보장한다. |
| 11 | 각 제약은 독립적으로 작동하며, 에러 메시지에 제약 이름이 표시된다. |
| 12 | 연습 테이블은 `DROP TABLE`로 정리한다. |

| 범주 | 이 실습에서 건 제약 |
|---|---|
| 도메인 | `NOT NULL`(3단계), `DEFAULT`(4단계) |
| 체크 | `chk_price_positive`, `chk_status_valid`(6단계), `chk_slug_pattern`(7단계) |
| 엔티티 | `pk_categories_id`, `pk_menus_id`(8단계), `uq_categories_slug`, `uq_menus_name`(9단계) |
| 관계 | `fk_menus_category`(10단계) |
