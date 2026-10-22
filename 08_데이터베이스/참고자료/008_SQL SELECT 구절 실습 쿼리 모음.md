---
tags: [데이터베이스, SQL, WHERE, GROUP BY, HAVING, ORDER BY, FILTER, 실습]
---

> 🔗 관련 노트: [[011_SQL SELECT 구절 연습]]

# SQL SELECT 구절 실습 쿼리 모음

[[011_SQL SELECT 구절 연습]]에서 다루는 각 단계의 실제 쿼리와 실행 결과. 개념 설명은 그 노트를 참고.

## 0. 실습 환경

```sql
DROP TABLE IF EXISTS menus;
CREATE TABLE menus(
    id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
    kor_name varchar(255),
    eng_name varchar(255),
    price integer,
    description varchar(2000),
    img_src varchar(255),
    category_id integer,
    create_time date,
    PRIMARY KEY(id)
);
```

```sql
INSERT INTO menus (kor_name, eng_name, price, description, img_src, category_id, create_time) VALUES
('에스프레소', 'Espresso', 3800, '고압 추출한 원두 본연의 진한 샷', '/img/espresso.png', 1, '2026-01-05'),
('아메리카노', 'Americano', 4500, '에스프레소에 정제수를 더한 깔끔한 커피', '/img/americano.png', 1, '2026-01-05'),
('카페라떼', 'Cafe Latte', 5000, '스팀 밀크와 에스프레소의 조화', '/img/latte.png', 1, '2026-01-10'),
('바닐라빈라떼', 'Vanilla Bean Latte', 5800, '마다가스카르 바닐라빈 시럽이 들어간 달콤한 라떼', '/img/vanilla.png', 1, '2026-01-15'),
('카푸치노', 'Cappuccino', 5000, '풍부한 벨벳 밀크폼과 시나몬 파우더', NULL, 1, '2026-01-20'),
('콜드브루', 'Cold Brew', 5500, '14시간 동안 저온 침출한 부드러운 커피', '/img/coldbrew.png', 1, '2026-02-01'),
('자몽허니블랙티', 'Grapefruit Honey Black Tea', 5800, '자몽 과육과 얼그레이 홍차의 블렌딩', '/img/jahotea.png', 2, '2026-02-05'),
('유자민트티', 'Citron Mint Tea', 5500, '고흥 유자청과 상쾌한 페퍼민트 허브티', NULL, 2, '2026-02-10'),
('말차라떼', 'Matcha Latte', 6000, '유기농 보성 녹차 말차 파우더를 사용한 음료', '/img/matcha.png', 2, '2026-02-15'),
('레몬에이드', 'Lemon Ade', 5800, '생레몬 착즙 탄산 음료', '/img/lemonade.png', 3, '2026-03-01'),
('샤인머스캣에이드', 'Shine Muscat Ade', 6500, '샤인머스캣 청과 탄산수', '/img/shinemuscat.png', 3, '2026-03-05'),
('뉴욕치즈케이크', 'New York Cheesecake', 6800, '크림치즈 함량 70% 이상의 조각 케이크', '/img/cheesecake.png', 4, '2026-03-10'),
('초코퍼지브라우니', 'Chocolate Fudge Brownie', 5200, '다크 초콜릿 기반의 꾸덕한 브라우니', NULL, 4, '2026-03-12'),
('플레인스콘', 'Plain Scone', 3500, '프랑스산 고메 버터로 구워낸 전통 스콘', '/img/scone.png', 4, '2026-03-15'),
('딸기티라미수', 'Strawberry Tiramisu', 7200, '제철 딸기와 마스카포네 크림', '/img/strawberry_tiramisu.png', 4, '2026-03-20');
```

## 1부. `WHERE` — 행 단위 필터링

### 1단계. 단일 비교 연산자

```sql
SELECT * FROM menus
WHERE price >= 6000;
```

15건 중 단가 6,000원 이상인 4건(말차라떼, 샤인머스캣에이드, 뉴욕치즈케이크, 딸기티라미수)만 통과.

### 2단계. 논리 연산자 결합

```sql
SELECT * FROM menus
WHERE (category_id = 1 OR category_id = 2)
  AND price < 5000;
```

카테고리 1(커피)·2(티)의 합집합 중, 가격 5,000원 미만 조건까지 동시에 만족하는 2건(에스프레소, 아메리카노)만 통과.

### 3단계. 범위 및 이산 집합 검색

```sql
SELECT * FROM menus
WHERE category_id IN (1, 4)
  AND price BETWEEN 5000 AND 6000;
```

카테고리 1·4 중 가격이 5000~6000원(경계 포함) 사이인 5건(카페라떼, 바닐라빈라떼, 카푸치노, 콜드브루, 초코퍼지브라우니)이 통과.

### 4단계. 3치 논리 결측치 검증

```sql
SELECT * FROM menus
WHERE img_src IS NULL;
```

`img_src`가 비어있는 3건(카푸치노, 유자민트티, 초코퍼지브라우니)을 필터링.

### 5단계. 와일드카드 문자열 패턴 매칭

```sql
SELECT * FROM menus
WHERE eng_name ILIKE '%tea%'
   OR kor_name LIKE '%라떼%';
```

영문명에 대소문자 무관 'tea'가 들어가거나 한글명에 '라떼'가 들어간 5건(카페라떼, 바닐라빈라떼, 자몽허니블랙티, 유자민트티, 말차라떼) 추출.

### 6단계. 날짜 경계 조건 필터링

```sql
SELECT * FROM menus
WHERE create_time >= DATE '2026-02-01'
  AND create_time < DATE '2026-03-01';
```

2026년 2월 전체 구간(2/1 이상 3/1 미만)에 등록된 4건(콜드브루, 자몽허니블랙티, 유자민트티, 말차라떼) 필터링.

## 2부. `GROUP BY` / 집계 함수

### 7단계. 단일 컬럼 기준 그룹화와 단순 집계

```sql
SELECT
    category_id,
    COUNT(*),
    SUM(price),
    AVG(price)
FROM menus
GROUP BY category_id;
```

15개 행이 4개 카테고리 그룹으로 압축되고, 그룹별 건수·합계·평균이 계산된다.

### 8단계. 극값 계산

```sql
SELECT
    category_id,
    MIN(price),
    MAX(price)
FROM menus
GROUP BY category_id;
```

카테고리별 최저가·최고가 산출.

### 9단계. `COUNT(*)` vs `COUNT(컬럼)`

```sql
SELECT
    category_id,
    COUNT(*) AS 전체_건수,
    COUNT(img_src) AS 이미지_등록_건수
FROM menus
GROUP BY category_id;
```

카테고리 1·2·4번에 각 1건씩 있는 `img_src IS NULL` 데이터가 `COUNT(img_src)` 집계에서 정상적으로 누락되는 것을 확인.

### 10단계. PostgreSQL 조건부 집계 (`FILTER`)

```sql
SELECT
    category_id,
    COUNT(*) AS 전체_메뉴수,
    COUNT(*) FILTER (WHERE price >= 5500) AS 고가_메뉴수,
    AVG(price) FILTER (WHERE price >= 5500) AS 고가_평균가
FROM menus
GROUP BY category_id;
```

서브쿼리 없이 단일 그룹핑 안에서 조건별 서브셋 통계를 동시에 산출.

## 3부. `HAVING` — 그룹 집계 결과 필터링

### 11단계. 집계 기준 단순 조건 필터링

```sql
SELECT
    category_id,
    COUNT(*)
FROM menus
GROUP BY category_id
HAVING COUNT(*) >= 3;
```

4개 카테고리 중 메뉴 수 3개 이상인 1·2·4번만 남고, 2건뿐인 3번은 제외.

### 12단계. 통계값 연산 기반 그룹 필터링

```sql
SELECT
    category_id,
    AVG(price),
    MIN(price)
FROM menus
GROUP BY category_id
HAVING AVG(price) >= 5500
   AND MIN(price) >= 4000;
```

평균가 5,500원 이상이면서 최저가도 4,000원 이상인 2·3번 그룹만 통과(4번은 최저가가 3,500원이라 탈락).

### 13단계. `WHERE`(사전 필터)와 `HAVING`(사후 필터) 결합

```sql
SELECT
    category_id,
    COUNT(*),
    AVG(price)
FROM menus
WHERE price >= 4000
GROUP BY category_id
HAVING COUNT(*) >= 3;
```

`WHERE`가 4,000원 미만 행(에스프레소 3,800원, 플레인스콘 3,500원)을 먼저 버리고, 남은 13건을 그룹화한 뒤 `HAVING`이 3건 이상인 1·2·4번 그룹만 최종 통과시킨다.

## 4부. `SELECT` — 프로젝션 및 데이터 매핑

### 14단계. 컬럼 프로젝션 및 산술 연산 매핑

```sql
SELECT
    id,
    kor_name,
    price,
    ROUND(price * 0.1) AS tax_amount,
    price + ROUND(price * 0.1) AS gross_price
FROM menus
WHERE category_id = 1;
```

각 행의 `price`를 참조해 세액(`tax_amount`)과 총합(`gross_price`)을 계산해 새 컬럼으로 매핑.

### 15단계. 문자열 결합 및 변환 함수

```sql
SELECT
    id,
    UPPER(eng_name) AS upper_eng_name,
    kor_name || ' [' || price || '원]' AS menu_tag,
    LENGTH(description) AS desc_length
FROM menus
WHERE category_id = 3;
```

`UPPER()`로 영문 대문자화, `||`로 한글명+단가 레이블 생성, `LENGTH()`로 설명 글자 수 계산.

### 16단계. 결측치 대체 매핑

```sql
SELECT
    kor_name,
    COALESCE(img_src, '/static/img/no_image.png') AS final_img_path
FROM menus
WHERE category_id IN (1, 2);
```

`img_src`가 `NULL`인 행에 `COALESCE`로 대체 이미지 경로를 채워서 출력.

### 17단계. 조건 분기 매핑

```sql
SELECT
    kor_name,
    price,
    CASE
        WHEN category_id = 1 THEN 'Coffee'
        WHEN category_id = 2 THEN 'Tea'
        WHEN category_id = 3 THEN 'Ade'
        WHEN category_id = 4 THEN 'Dessert'
        ELSE 'Etc'
    END AS category_code,
    CASE
        WHEN price >= 6500 THEN 'High'
        WHEN price >= 5000 THEN 'Middle'
        ELSE 'Low'
    END AS price_grade
FROM menus;
```

`CASE`로 카테고리 ID를 라벨로, 가격을 등급으로 실시간 분류.

## 5부. `ORDER BY` / 페이징 — 최종 정렬 및 출력 제어

### 18단계. 복합 정렬

```sql
SELECT category_id, kor_name, price, create_time
FROM menus
ORDER BY category_id ASC, price DESC;
```

카테고리 오름차순으로 먼저 배치하고, 같은 카테고리 안에서는 비싼 메뉴부터 내림차순 정렬.

### 19단계. `SELECT` 별칭을 `ORDER BY`에서 참조

```sql
SELECT
    kor_name,
    price + ROUND(price * 0.1) AS total_price
FROM menus
ORDER BY total_price DESC;
```

`ORDER BY`는 `SELECT`보다 논리적으로 나중에 실행되므로, `SELECT`에서 정의한 `total_price` 별칭을 그대로 정렬 기준으로 쓸 수 있다.

### 20단계. `NULL` 값의 정렬 위치 제어

```sql
SELECT id, kor_name, img_src
FROM menus
ORDER BY img_src ASC NULLS FIRST;
```

`NULLS FIRST`로 이미지 미등록 3건을 최상단에 노출.

### 21단계. 결과 집합 분할 및 페이징

```sql
-- 페이지당 4건씩 조회할 때의 2번째 페이지 (OFFSET 4, LIMIT 4)
SELECT id, kor_name, price
FROM menus
ORDER BY id ASC
LIMIT 4 OFFSET 4;
```

`OFFSET 4`로 1~4번 레코드를 건너뛰고, `LIMIT 4`로 5~8번 레코드 4건을 추출.

## 6. 심화 — `FILTER` 절

### 심화 1단계. `CASE WHEN` 조건부 집계 vs `FILTER` 절 문법 비교

```sql
SELECT
    category_id,
    COUNT(*) AS 전체건수,
    -- 1. 기존 CASE WHEN 방식
    COUNT(CASE WHEN price >= 5500 THEN 1 END) AS 고가메뉴수_CASE방식,
    -- 2. PostgreSQL FILTER 절 방식
    COUNT(*) FILTER (WHERE price >= 5500) AS 고가메뉴수_FILTER방식
FROM menus
GROUP BY category_id
ORDER BY category_id ASC;
```

두 방식이 동일한 결과를 산출한다는 것을 확인. `FILTER (WHERE 조건)`은 `CASE WHEN ... THEN 1 ELSE NULL END`를 생략할 수 있어 더 직관적이다.

### 심화 2단계. 다중 집계 함수와 `FILTER` 결합

```sql
SELECT
    category_id,
    -- 카테고리 전체 평균가
    ROUND(AVG(price), 0) AS 전체_평균가,
    -- 5,500원 이상 메뉴들만의 평균가
    ROUND(AVG(price) FILTER (WHERE price >= 5500), 0) AS 프리미엄_평균가,
    -- 이미지가 등록된 메뉴들의 가격 합계
    SUM(price) FILTER (WHERE img_src IS NOT NULL) AS 정상등록_가격합계
FROM menus
GROUP BY category_id
ORDER BY category_id ASC;
```

`COUNT`뿐 아니라 `SUM`, `AVG` 등 모든 집계 함수 뒤에 서로 다른 조건을 붙여, 단일 쿼리로 복합 보고서를 만들 수 있다.

### 심화 3단계. `HAVING` 절과의 결합

```sql
SELECT
    category_id,
    COUNT(*) AS 전체메뉴수,
    COUNT(*) FILTER (WHERE price >= 5500) AS 고가메뉴수
FROM menus
GROUP BY category_id
HAVING COUNT(*) FILTER (WHERE price >= 5500) >= 3;
```

그룹 전체 집계가 아니라 그룹 내부의 조건부 집계 결과(5,500원 이상 메뉴 수)를 기준으로 그룹 자체를 필터링 — 5,500원 이상 메뉴가 3개 이상인 2번 카테고리만 남는다.

### 대체 표기법 정리 — DBMS 호환성이 필요할 때

`FILTER`는 PostgreSQL(및 SQL:2003 표준) 전용이라, MySQL·Oracle 등에서는 `CASE WHEN`으로 1:1 치환해야 한다.

| PostgreSQL (`FILTER`) | 범용 표준 SQL (`CASE WHEN`) |
|---|---|
| `COUNT(*) FILTER (WHERE price >= 5000)` | `COUNT(CASE WHEN price >= 5000 THEN 1 END)` |
| `SUM(price) FILTER (WHERE category_id = 1)` | `SUM(CASE WHEN category_id = 1 THEN price ELSE 0 END)` |
| `AVG(price) FILTER (WHERE img_src IS NOT NULL)` | `AVG(CASE WHEN img_src IS NOT NULL THEN price END)` |
