---
tags: [JPA, SpringDataJPA, JPQL, Query, 참고자료]
---

> 🔗 관련 노트: [[081_JPQL과 @Query — 쿼리 메서드 이름 대신 쿼리를 직접 쓰기]] · [[024_Spring Data JPA 쿼리 메서드 — 이름 규칙과 연산자 키워드 참고자료]] · [[080_JPA 연관관계 매핑과 쿼리 메서드 조인 — 1대N, 1대1, 복합키]]

# JPQL — 쿼리 메서드의 한계를 해결하기 위한 쿼리 언어

## 1. 쿼리 메서드의 한계

Spring Data JPA의 쿼리 메서드(Query Method)는 메서드 이름에 포함된 조건을 파싱하여 쿼리를 자동으로 생성하는 편리한 기능이지만, 다음과 같은 복잡한 쿼리를 처리하는 데에는 한계가 있다.

- **복잡한 조인(JOIN) 조합**: 여러 엔티티를 동시에 조인하거나, 조인 방향을 자유롭게 지정해야 하는 경우.
- **서브쿼리(Subquery)**: `EXISTS`, `IN`, 또는 스칼라 서브쿼리를 포함해야 하는 경우.
- **집계 함수와 그룹화**: `GROUP BY`, `HAVING` 절을 사용하여 집계 결과를 필터링하거나 정렬해야 하는 경우.
- **벌크 업데이트/삭제**: `UPDATE`, `DELETE` 문법을 사용하여 데이터베이스에 직접 영향을 주는 쿼리.
- **복잡한 WHERE 조건**: 논리 연산자(`AND`, `OR`, `NOT`)가 복잡하게 얽혀 있거나, `LIKE`, `BETWEEN` 등 특수 연산자가 여러 개 조합되는 경우.

이러한 한계를 직관적으로 이해하기 위해, 쿼리 메서드로 표현하기 어려운 복잡한 조건(서브쿼리, 복합 조인, 집계 등)을 포함하는 가상의 메서드 시그니처를 살펴보자.

```java
// 쿼리 메서드로는 표현 불가능하거나 가독성이 극도로 떨어지는 복잡한 쿼리 예시
// 1. 서브쿼리(AVG)를 이용한 필터링
// 2. LEFT JOIN과 IS NULL 조합
// 3. 복합 WHERE 조건
List<Menu> findMenusByCategoryNameAndPriceGreaterThanAndExistsReviewWithRatingGreaterThanAndOrderByPriceDesc(
    String categoryName,
    int minPrice,
    double minAvgRating
);
```

위와 같이 메서드 이름이 길어지고 조건이 복잡해지면 가독성이 급격히 저하되며, 일부 문법(서브쿼리, 벌크 업데이트 등)은 쿼리 메서드 문법 자체로 표현이 불가능하다.

> 위 메서드는 "이렇게까지 길어진다"를 보여주기 위한 가상의 예시다. 실제로는 `ExistsReviewWithRatingGreaterThan` 같은 키워드가 없고, `OrderBy` 앞에는 `And`를 붙이지 않으므로 애플리케이션 시작 시 이름 분석 에러가 난다.

이러한 한계를 극복하고 정밀한 데이터 접근을 수행하기 위해 JPA에서는 쿼리 언어(JPQL)를 제공하고 있다.

## 2. JPQL이란

JPQL(Java Persistence Query Language)은 **엔티티와 엔티티 필드를 기준으로** 쿼리를 작성하는 표준 언어이다.

JPQL은 SQL과 문법 구조가 유사하지만, 쿼리를 작성할 때 사용하는 대상이 다르다. SQL은 데이터베이스의 **테이블**과 **컬럼** 이름을 사용하지만, JPQL은 JPA 엔티티의 **클래스**와 **필드** 이름을 사용한다. 즉, 데이터베이스의 물리적 구조가 아닌, 애플리케이션의 객체 모델 기준으로 쿼리를 작성한다는 의미이다.

### 2-1. SELECT 문의 기본 규칙

JPQL의 기본 문법인 `SELECT` 절은 이미 SQL에서 사용하던 구문과 거의 동일하다. 다만 조회할 때 사용하는 대상이 엔티티와 엔티티의 속성명이라는 점만 차이가 있다.

그 외에도 주의할 점이 있는데, `SELECT *`와 같은 와일드카드(`*`)를 사용할 수 없다. 그리고 엔티티 클래스 이름(예: `Menu`)을 직접 필드 경로로 사용할 수 없다.

```sql
SELECT Menu.price FROM Menu  -- 오류 : 엔티티 클래스 이름을 직접 필드 경로로 사용할 수 없다.
```

반드시 `FROM` 절에서 별칭(예: `m`)을 선언하고, 별칭을 이용해서 필드에 접근해야 한다.

```sql
-- 엔티티 전체 조회
SELECT m FROM Menu m            -- 별칭을 이용한 조회

-- 특정 필드만 조회 : 별칭을 이용한 필드 선택
SELECT m.name, m.price FROM Menu m
```

> `m.price`처럼 별칭에서 점(`.`)으로 필드를 따라가는 것을 **경로 표현식(path expression)**이라고 한다. `m.category.name`처럼 연관 엔티티를 따라 이어갈 수도 있고, 이때 Hibernate가 조인을 자동으로 넣는다(묵시적 조인).

### 2-2. 매개변수 처리

`WHERE` 절은 필터링 조건을, `ORDER BY` 절은 정렬 기준을 제공한다. `LIMIT`와 `OFFSET`는 페이지네이션을 위해 사용되며, Hibernate는 이를 `setMaxResults`와 `setFirstResult`로 지원한다.

> **보충 — LIMIT/OFFSET**: `LIMIT`, `OFFSET`은 JPA 표준 JPQL 문법에는 없다(Hibernate 6의 HQL에서는 쓸 수 있다). Spring Data JPA의 `@Query`에서는 쿼리 문자열에 쓰는 대신 메서드 파라미터로 `Pageable`을 넘기는 방식이 일반적이다. `PageRequest.of(0, 10)`을 넘기면 Spring Data가 내부적으로 `setFirstResult(0)`, `setMaxResults(10)`을 호출해준다.

이러한 JPQL 문법을 실제 Repository 인터페이스에 적용할 때는 `@Query` 어노테이션을 이용해서 쿼리를 적용할 수 있다.

```java
public interface MenuRepository extends JpaRepository<Menu, Long> {

    // 엔티티 전체 조회
    @Query("SELECT m FROM Menu m")
    List<Menu> findAllMenus();

    // 특정 필드만 조회 (프로젝션)
    @Query("SELECT m.name, m.price FROM Menu m")
    List<Object[]> findNameAndPrice();
}
```

> 필드를 골라 조회하면 한 행이 `Object[]`(값 배열)로 온다. `row[0]`이 이름, `row[1]`이 가격처럼 순서로 꺼내야 해서 실수하기 쉽다. 실무에서는 `SELECT new com.newcafe.backend.dto.MenuNamePrice(m.name, m.price) FROM Menu m`처럼 DTO로 바로 받거나, 인터페이스 프로젝션을 쓰는 편이 안전하다.

사용자가 가격을 입력받아 그 가격보다 높은 메뉴를 검색하는 JPQL 쿼리를 작성해 보자. 쿼리 메서드와 달리 JPQL을 사용할 때는 메서드 이름의 규칙을 따를 필요가 없으므로, 메서드 이름을 자유롭게 정의할 수 있다.

```java
public interface MenuRepository extends JpaRepository<Menu, Long> {

    List<Menu> findAll(Integer inputPrice);
}
```

이 메서드에 `@Query` 어노테이션을 붙여 JPQL 쿼리를 설정하면 된다.

```java
public interface MenuRepository extends JpaRepository<Menu, Long> {

    @Query("SELECT m FROM Menu m WHERE m.price > :price ORDER BY m.price DESC")
    List<Menu> findAll(Integer inputPrice);   // ❌ :price와 inputPrice 이름이 달라 연결되지 않는다
}
```

이때 주의할 점은 **쿼리 내의 파라미터 이름과 메서드 인수의 매개변수 이름이 일치해야 한다**는 것이다. 위 코드는 쿼리에는 `:price`, 메서드에는 `inputPrice`라서 값이 연결되지 않고 에러가 난다. 콜론(`:`) 접두사를 사용하는 쿼리 파라미터 이름이 메서드 인수의 이름과 다르면, `@Param` 어노테이션을 사용하여 명시적으로 매핑해 주어야 한다.

```java
public interface MenuRepository extends JpaRepository<Menu, Long> {

    @Query("SELECT m FROM Menu m WHERE m.price > :price ORDER BY m.price DESC")
    List<Menu> findAll(@Param("price") Integer inputPrice);
}
```

> 이름은 자유롭게 지어도 되지만, `findAll`은 `JpaRepository`에 이미 있는 메서드 이름이라 파라미터만 다른 **오버로딩**이 된다. 동작은 하지만 읽는 사람이 기본 `findAll()`과 헷갈리기 쉬우므로 `findByPriceAbove`처럼 의도가 드러나는 이름이 낫다.

### 2-3. JPQL에서 사용할 수 있는 연산자

JPQL에서도 SQL과 동일한 비교 연산자(`=`, `<>`, `<`, `>`, `<=`, `>=`)와 논리 연산자(`AND`, `OR`, `NOT`)를 그대로 사용할 수 있다.

- `LIKE`: 문자열 패턴 매칭. `%`는 임의의 문자열(0글자 이상), `_`는 한 글자를 의미한다.
- `IS NULL` / `IS NOT NULL`: 널 값 확인.
- `BETWEEN`: 범위 지정. `BETWEEN a AND b`는 `>= a AND <= b`와 동일하다.
- `IN`: 여러 값 중 하나와 일치하는지 확인.

```sql
SELECT m FROM Menu m
WHERE m.name LIKE '%치킨%'
AND m.category IS NOT NULL
AND m.price BETWEEN 10000 AND 20000
AND m.id IN (1, 2, 3)
```

> 표준 JPQL의 "같지 않다"는 `<>`다. `!=`는 Hibernate가 추가로 받아주는 표기다.

## 3. SELECT 구절

SQL로 `SELECT`에 사용하던 구절들도 거의 동일하게 사용할 수 있다. 그 내용들을 하나씩 확인해보기로 하자.

### 3-1. JOIN 쿼리

엔티티 간 연관 관계를 따라 데이터를 조회할 때 `JOIN`을 사용한다. SQL과 달리 `ON` 조건을 쓰지 않고, **`JOIN` 뒤에 연관 필드 경로**(`m.category`)를 적는다. 조인 조건은 엔티티 매핑 정보에서 가져온다.

- `JOIN`: 내부 조인(Inner Join)의 기본 형태. `INNER JOIN`과 같다.
- `INNER JOIN`: 양쪽 엔티티가 모두 존재해야만 조회되는 조인.
- `LEFT JOIN`: 오른쪽(연관) 엔티티가 없어도 **왼쪽 엔티티는 결과에 포함**하는 조인. 예를 들어 `Menu m LEFT JOIN m.category c`는 카테고리가 없는 메뉴도 조회하고, 이때 `c`는 `NULL`이 된다.
- `FETCH JOIN`: 연관된 엔티티를 **이 쿼리에서 함께** 로드하여 N+1 문제를 방지한다.

```sql
-- 카테고리 정보를 함께 조회 (N+1 방지)
SELECT m FROM Menu m
JOIN FETCH m.category
WHERE m.price > 10000
```

다대다(N:M)나 일대다(1:N) 관계에서도 동일한 문법을 적용하며, `JOIN` 뒤에 연관 필드 이름을 적는다.

> **보충 — FETCH JOIN**
> - 원본 자료의 예시는 `SELECT m, c FROM Menu m JOIN FETCH m.category c`였다. 하지만 fetch join은 "메뉴를 가져오면서 카테고리를 **메뉴 안에 채워 넣는** 것"이라서 `SELECT m`만 해도 `m.getCategory()`에 이미 값이 들어 있다. `SELECT m, c`로 따로 받으면 결과가 `Object[]`가 되어 오히려 다루기 불편하다. 또 JPA 표준은 fetch join 대상에 별칭(`c`)을 붙이는 것을 허용하지 않는다(Hibernate는 허용).
> - fetch join은 엔티티의 fetch 설정(`LAZY`)을 바꾸는 것이 아니라, **이 쿼리에서만** 연관 엔티티를 조인으로 한꺼번에 가져오는 것이다.
> - **N+1 문제**: 메뉴 N개를 조회한 뒤 각 메뉴의 카테고리에 접근할 때마다 카테고리 조회 SQL이 한 번씩 더 나가서, 쿼리가 1 + N번 실행되는 문제.

### 3-2. GROUP BY와 HAVING

집계 함수(`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`)를 사용할 때는 `GROUP BY` 절로 그룹을 지정해야 한다. `WHERE` 절은 그룹화 **이전**의 행을 필터링하는 반면, `HAVING` 절은 그룹화 **이후**의 집계 결과를 필터링한다.

```sql
SELECT c.name, COUNT(m.id)
FROM Menu m
JOIN m.category c
GROUP BY c.name
HAVING COUNT(m.id) > 5
```

위 쿼리는 메뉴가 5개 넘게 들어 있는 카테고리의 이름과 메뉴 수를 조회한다.

### 3-3. 서브쿼리

JPQL은 `WHERE`, `HAVING` 절에서 서브쿼리를 지원하고, `EXISTS`, `IN`과 함께 쓸 수 있다. 이는 쿼리 메서드로 표현하기 어려운 복잡한 조건을 처리할 수 있게 한다.

- **스칼라 서브쿼리**: 값 하나를 반환하는 쿼리를 내부에서 실행해 비교에 사용.
- `EXISTS`: 서브쿼리가 결과 행을 반환하는지 여부만 확인.
- `IN` 서브쿼리: 특정 값이 서브쿼리의 결과 집합에 포함되는지 확인.

```sql
-- 평균 가격보다 비싼 메뉴 조회
SELECT m FROM Menu m
WHERE m.price > (SELECT AVG(m2.price) FROM Menu m2)
```

> JPA 표준 JPQL은 서브쿼리를 `WHERE`, `HAVING` 절에서만 허용한다. `SELECT` 절이나 `FROM` 절의 서브쿼리는 Hibernate 6가 지원하는 확장 문법이다.

## 4. 수정 쿼리

데이터 수정을 위한 쿼리를 만들 때도 SQL에서와 거의 동일하다. 다만 수정하는 쿼리를 사용할 때는 `@Modifying` 어노테이션을 추가로 사용한다는 것 외에는 큰 차이가 없다.

### 4-1. UPDATE와 DELETE 쿼리

JPQL은 `UPDATE`와 `DELETE` 문법을 통해 **벌크(Bulk)** 업데이트와 삭제를 수행한다. 이 쿼리는 영속성 컨텍스트를 거치지 않고 데이터베이스에 직접 SQL을 실행하므로, 여러 건을 한 번에 바꿀 때 성능이 우수하다.

- **리턴값**: `UPDATE`와 `DELETE` 쿼리는 실제로 수정되거나 삭제된 데이터의 개수를 돌려준다.
- **주의**: 이 쿼리는 데이터베이스를 바로 바꾸지만, 프로그램 안에서 이미 불러온 데이터(엔티티)는 옛날 값 그대로 남아 있다. 자세한 내용은 4-3에서 다룬다.

> **벌크 연산과 엔티티 단위 수정의 차이**: `save()`나 엔티티 값을 바꾸는 방식은 엔티티를 한 건씩 조회하고 수정한다. 100건이면 100번 처리된다. 벌크 쿼리는 `UPDATE ... WHERE ...` 한 문장으로 조건에 맞는 행을 한꺼번에 바꾼다.

### 4-2. UPDATE 쿼리

`UPDATE` 쿼리는 기존에 존재하는 엔티티의 필드 값을 수정할 때 사용한다. `SET` 절에서 수정할 필드와 새로운 값을 지정하고, `WHERE` 절로 대상 엔티티를 필터링한다.

```sql
UPDATE Menu m
SET m.price = m.price * 1.1
WHERE m.category.name = '치킨'
```

위 예시는 '치킨' 카테고리에 속하는 모든 메뉴의 가격을 현재 가격의 1.1배(10% 인상)로 수정하는 쿼리이다. `SET` 절에서는 `m.price = m.price * 1.1`처럼 기존 값을 참조하여 계산할 수도 있고, 고정 값(`m.price = 15000`)을 직접 지정할 수도 있다.

사용 예시:

```java
public interface MenuRepository extends JpaRepository<Menu, Long> {

    // 특정 카테고리의 메뉴 가격을 10% 인상
    @Modifying
    @Transactional
    @Query("UPDATE Menu m SET m.price = m.price * 1.1 WHERE m.category.name = :categoryName")
    int updatePriceByCategoryName(@Param("categoryName") String categoryName);
}
```

> **보충**
> - `price`가 `Integer` 필드인데 `* 1.1`을 하면 계산 결과가 소수(실수)가 된다. Hibernate 6는 `SET`의 값 타입이 필드 타입과 맞지 않으면 에러를 낼 수 있으므로, 정수 필드라면 `m.price * 11 / 10`처럼 정수 연산으로 쓰거나 금액은 `BigDecimal` 필드로 두는 것이 안전하다.
> - JPA 표준은 벌크 `UPDATE`/`DELETE`에서 조인을 허용하지 않는다. `WHERE m.category.name = ...`처럼 연관 엔티티를 따라가는 조건은 Hibernate가 내부적으로 서브쿼리로 바꿔 처리해주지만, 표준대로 쓰려면 `WHERE m.category.id IN (SELECT c.id FROM Category c WHERE c.name = :categoryName)`처럼 서브쿼리로 직접 쓴다.

### 4-3. DELETE 쿼리

`DELETE` 쿼리는 엔티티를 데이터베이스에서 영구적으로 삭제할 때 사용한다. `WHERE` 절로 삭제할 대상 엔티티를 지정한다.

```sql
DELETE FROM Menu m
WHERE m.price < 5000
```

위 예시는 가격이 5,000원 미만인 모든 메뉴를 삭제하는 쿼리이다. `WHERE` 절이 없으면 해당 엔티티의 모든 데이터가 삭제되므로, 실수 방지를 위해 항상 `WHERE` 조건을 명시하는 것이 안전하다.

사용 예시:

```java
public interface MenuRepository extends JpaRepository<Menu, Long> {

    // 특정 가격 미만의 메뉴 삭제
    @Modifying
    @Transactional
    @Query("DELETE FROM Menu m WHERE m.price < :minPrice")
    int deleteMenusByPriceLessThan(@Param("minPrice") int minPrice);
}
```

> **보충**
> - 원본 자료는 `DELETE Menu m WHERE ...`처럼 `FROM`을 생략했다. Hibernate는 받아주지만 JPA 표준 문법은 `DELETE FROM Menu m`이다.
> - 벌크 삭제는 엔티티에 설정한 `cascade`나 `orphanRemoval`을 적용하지 않는다. 삭제하려는 메뉴를 리뷰 같은 다른 테이블이 외래키로 참조하고 있으면, DB의 외래키 제약조건 때문에 오류가 난다.

이러한 벌크 업데이트와 삭제 쿼리를 Repository 인터페이스에 적용할 때는 `@Modifying`과 `@Transactional` 어노테이션을 함께 사용해야 한다. 또한, 쿼리에서 사용하는 파라미터는 `:name` 형태로 선언하고 `@Param`으로 메서드 인자와 연결한다.

### 4-4. 벌크 쿼리와 영속성 컨텍스트

**주의**: 이 쿼리는 데이터베이스의 값만 바로 바꾸고, 프로그램 안에서 이미 불러온 데이터(엔티티)는 그대로 남아 있다.

**자세한 설명**: JPA는 성능을 위해 영속성 컨텍스트(Persistence Context)라는 1차 캐시를 사용하며, 여기서 엔티티를 관리한다. `@Query`로 작성한 벌크 업데이트(UPDATE) 쿼리는 이 영속성 컨텍스트를 우회하여 데이터베이스에 SQL을 직접 실행한다.

이 때문에 데이터베이스의 값은 변경되었지만, 영속성 컨텍스트에 이미 로드되어 있는 엔티티 객체의 값은 여전히 구 값(old value)을 유지하게 된다. 이 상태에서 같은 엔티티를 다시 조회하면, JPA는 DB에서 새로 읽어오지 않고 1차 캐시에 있는 **옛날 값의 객체를 그대로 돌려준다.** 데이터베이스의 실제 값과 메모리 상의 엔티티 값이 달라지는 데이터 불일치 문제가 발생하는 것이다.

```java
@Transactional
public void raisePrice() {
    Menu menu = menuRepository.findById(1L).orElseThrow();   // price = 5000, 1차 캐시에 저장
    menuRepository.updatePriceByCategoryName("치킨");          // DB만 5500으로 바뀜
    Menu again = menuRepository.findById(1L).orElseThrow();  // 1차 캐시에서 꺼냄 → 여전히 5000!
}
```

**해결 방법 — flush가 아니라 clear**:

| 메서드 | 하는 일 | 이 문제를 해결하나 |
|---|---|---|
| `em.flush()` | 영속성 컨텍스트에 쌓인 **변경 사항을 DB로 보낸다** (메모리 → DB) | ❌ 메모리의 옛날 값을 새로 고쳐주지 않는다 |
| `em.clear()` | 영속성 컨텍스트를 **비운다** | ✅ 다음 조회 때 DB에서 새로 읽어온다 |
| `em.refresh(entity)` | 특정 엔티티를 **DB 값으로 다시 읽는다** (DB → 메모리) | ✅ 그 엔티티 하나만 |

Spring Data JPA에서는 `@Modifying`의 옵션으로 간단히 처리한다.

```java
@Modifying(flushAutomatically = true, clearAutomatically = true)
@Query("UPDATE Menu m SET m.price = :newPrice WHERE m.id = :id")
int updatePrice(@Param("id") Long id, @Param("newPrice") int newPrice);
```

- `flushAutomatically = true`: 벌크 쿼리 **실행 전에** flush한다. 아직 DB에 보내지 않은 변경 사항이 벌크 쿼리보다 먼저 반영되게 하려는 것이다.
- `clearAutomatically = true`: 벌크 쿼리 **실행 후에** 영속성 컨텍스트를 비운다. 이후 조회는 DB에서 최신 값을 읽는다.

> **원본 자료 바로잡기**: 원본에는 "쿼리 실행 후 `flush()`를 호출하면 프로그램 안의 데이터와 DB 데이터가 일치한다"고 되어 있다. 하지만 `flush()`는 메모리의 변경을 DB로 **내보내는** 것이지, DB에서 바뀐 값을 메모리로 **가져오는** 것이 아니다. 벌크 쿼리 후의 불일치는 `clear()`(또는 `clearAutomatically = true`)나 `refresh()`로 해결한다. flush는 오히려 벌크 쿼리 **전에** 필요한 작업이다.

**@Transactional 사용 시**: 스프링에서 영속성 컨텍스트는 기본적으로 트랜잭션 단위로 만들어지고, 트랜잭션이 끝나면 함께 사라진다. 따라서 벌크 쿼리를 실행한 트랜잭션이 끝난 뒤 **새로운 트랜잭션**에서 조회하면 빈 영속성 컨텍스트에서 시작하므로 DB의 최신 값을 가져온다. 즉, 트랜잭션 경계가 영속성 컨텍스트를 초기화하는 역할을 해서, 대부분의 경우 불일치 문제가 자연스럽게 해결된다.

**같은 트랜잭션 내**: 벌크 쿼리를 실행한 같은 트랜잭션 안에서 해당 엔티티를 다시 조회하거나 수정해야 한다면, 영속성 컨텍스트가 아직 살아 있으므로 여전히 구 값을 참조한다. 이 경우에는 `clearAutomatically = true`를 쓰거나 `em.clear()`를 직접 호출해야 한다.

> **보충 — OSIV**: Spring Boot는 기본으로 `spring.jpa.open-in-view=true`라서, 웹 요청 하나가 끝날 때까지 영속성 컨텍스트를 열어둔다. 이 경우 트랜잭션이 끝나도 같은 요청 안에서는 영속성 컨텍스트가 유지될 수 있으므로, "트랜잭션이 끝나면 비워진다"에만 기대지 말고 `clearAutomatically`를 명시하는 것이 확실하다.

## 5. JPQL 간단 정리

JPQL을 Repository 인터페이스에 바인딩하여 사용하려면 `@Query` 어노테이션을 사용한다. 가장 간단한 쿼리부터 차근차근 살펴보자.

**1. 가장 기본적인 SELECT 쿼리**

가장 단순한 형태는 조건이 없는 전체 조회나, 단일 필드 조건이 있는 조회이다. `@Query` 안에 JPQL 문장을 그대로 적고, 파라미터는 `:name` 형태로 선언한 뒤 메서드 인수에 `@Param("name")`으로 연결한다.

```java
// 조건 없는 전체 조회
@Query("SELECT m FROM Menu m")
List<Menu> findAllMenus();

// 단일 필드 조건 조회
@Query("SELECT m FROM Menu m WHERE m.price > :minPrice")
List<Menu> findMenusByPriceGreaterThan(@Param("minPrice") int minPrice);
```

**2. 엔티티 매핑의 중요성**

위 예시에서 `m.price`를 사용할 수 있는 이유는 `Menu` 엔티티 클래스에 `price` 필드가 JPA 매핑되어 있기 때문이다. `@Query`로 작성한 JPQL은 엔티티 클래스에 선언된 `@Entity`, `@Id`, `@ManyToOne` 등 JPA 매핑 어노테이션을 반드시 기반으로 한다. 쿼리 문자열에 `m.category`와 같은 필드 경로를 사용하려면, `Menu` 엔티티에 `category` 필드가 존재하고 `@ManyToOne` 등으로 연관 관계가 설정되어 있어야만 쿼리가 정상적으로 실행된다. 엔티티에 매핑이 없으면 JPQL 파서가 필드를 인식하지 못해 예외가 발생한다.

> `@Entity` 클래스의 일반 필드는 `@Column`을 붙이지 않아도 **기본으로 매핑**된다. `@Column`은 컬럼 이름이나 제약을 바꿀 때 쓰는 것이다. 반대로 `@Transient`를 붙인 필드는 매핑에서 빠지므로 JPQL에서 쓸 수 없다. 또 `@Query`의 JPQL은 **애플리케이션 시작 시 검증**되므로, 없는 필드를 쓰면 서버가 뜨는 단계에서 에러가 난다.

**3. 파라미터 전달 방식**

파라미터는 크게 두 가지 방식으로 전달할 수 있다.

- **위치 기반**: `?1`, `?2`처럼 순서대로 매핑된다.
- **이름 기반**: `:name`, `:price`처럼 이름을 지정하여 매핑한다. (권장)

```java
@Query("SELECT m FROM Menu m WHERE m.price BETWEEN ?1 AND ?2")
List<Menu> findInRange(int min, int max);                      // 위치 기반: 첫 번째 인수 → ?1

@Query("SELECT m FROM Menu m WHERE m.price BETWEEN :min AND :max")
List<Menu> findInRange2(@Param("min") int min, @Param("max") int max);   // 이름 기반
```

이름 기반 파라미터는 가독성이 뛰어나고, 메서드 인수의 순서와 무관하게 안전하게 사용할 수 있어 실무에서 주로 사용한다.

**4. UPDATE/DELETE 쿼리 처리**

`SELECT`와 달리 `UPDATE`나 `DELETE` 쿼리는 데이터 변경을 수반하므로 추가적인 설정이 필요하다.

- `@Modifying` 어노테이션을 붙여야 한다.
- 트랜잭션이 필요하므로 `@Transactional`을 함께 사용해야 한다.
- 리턴 타입은 `int` 또는 `long`으로 설정하여 변경된 행 수를 반환받는다.

```java
// UPDATE 쿼리
@Modifying
@Transactional
@Query("UPDATE Menu m SET m.price = :newPrice WHERE m.id = :id")
int updatePrice(@Param("id") Long id, @Param("newPrice") int newPrice);
```

> `@Transactional`은 리포지토리 메서드에 붙여도 되지만, 보통은 이 메서드를 호출하는 **서비스 메서드**에 붙인다. 여러 작업을 하나의 트랜잭션으로 묶는 경계는 서비스의 업무 단위이기 때문이다.

**5. 종합 예시**

위 내용을 종합하면, 다음과 같이 다양한 쿼리를 하나의 Repository 인터페이스에 정의할 수 있다.

```java
public interface MenuRepository extends JpaRepository<Menu, Long> {

    // 1. 기본 SELECT 쿼리
    @Query("SELECT m FROM Menu m WHERE m.price > :minPrice")
    List<Menu> findMenusByPriceGreaterThan(@Param("minPrice") int minPrice);

    // 2. UPDATE 쿼리 (벌크 업데이트)
    @Modifying
    @Transactional
    @Query("UPDATE Menu m SET m.price = :newPrice WHERE m.id = :id")
    int updatePrice(@Param("id") Long id, @Param("newPrice") int newPrice);
}
```

네이티브 SQL(`nativeQuery = true`)은 데이터베이스 특유의 함수나 구문을 사용할 때만 사용하며, 기본적으로는 JPQL을 사용하는 것이 유지보수성이 높다.

## 6. 실전: 복합 목록 쿼리

실제 서비스에서는 목록 조회 시 여러 조건의 필터링, 조인, 그리고 서브쿼리를 통한 집계 값 채우기가 동시에 요구된다. 예를 들어, "카테고리가 '치킨'이고, 리뷰 개수가 10개 이상인 메뉴를 가격 내림차순으로 조회하되, 각 메뉴의 평균 별점도 함께 반환"하는 쿼리를 작성해 본다.

**쿼리 메서드의 한계**:

- `findMenuByCategoryNameAnd...` 형태로 메서드 이름을 생성하면, 서브쿼리(`AVG(rating)`)를 메서드 이름으로 표현할 수 없다.
- 조인과 집계 서브쿼리를 동시에 처리하는 복합 로직은 쿼리 메서드로는 불가능하다.

**JPQL 구현**:

```java
@Query("""
    SELECT
        m.id,
        m.name,
        m.price,
        c.name AS categoryName,
        (SELECT AVG(r.rating) FROM Review r WHERE r.menu = m) AS avgRating
    FROM Menu m
    LEFT JOIN m.category c
    WHERE c.name = :categoryName
    AND (SELECT COUNT(r2.id) FROM Review r2 WHERE r2.menu = m) >= :minReviewCount
    ORDER BY m.price DESC
""")
List<Object[]> findComplexMenuList(@Param("categoryName") String categoryName,
                                   @Param("minReviewCount") int minReviewCount);
```

**해설**:

- **SELECT 절**: `m.id`, `m.name`, `m.price` 외에 카테고리 이름(`c.name`)과 서브쿼리로 계산된 평균 별점(`avgRating`)을 함께 조회한다.
- **FROM & JOIN**: `Menu` 엔티티를 `category`와 `LEFT JOIN`한다.
- **WHERE 절**:
  - `c.name = :categoryName`: 카테고리 필터.
  - `AND (SELECT COUNT(r2.id) FROM Review r2 WHERE r2.menu = m) >= :minReviewCount`: 서브쿼리를 사용하여 리뷰 개수가 특정 값 이상인 메뉴만 필터링.
- **ORDER BY**: 가격 내림차순 정렬.

이처럼 JPQL은 쿼리 메서드로는 표현할 수 없는 서브쿼리 + JOIN + 필터 + 집계가 결합된 복합 쿼리를 하나의 문자열로 명확하게 정의할 수 있게 한다.

> **원본 자료 바로잡기**
> - 원본 해설에는 "`LEFT JOIN`하여 카테고리가 없는 메뉴도 누락되지 않도록 한다"고 되어 있다. 하지만 `WHERE c.name = :categoryName` 조건 때문에 카테고리가 없는(`c`가 `NULL`인) 메뉴는 결국 빠진다. 이 쿼리의 결과는 `INNER JOIN`과 같다. 카테고리 없는 메뉴까지 남기려면 조건을 `LEFT JOIN m.category c ON c.name = :categoryName`처럼 조인 조건으로 옮기거나 `OR c IS NULL`을 붙여야 한다.
> - 원본 마지막 문장의 "`@Query`를 통해 **타입 안정성**을 유지"는 정확하지 않다. JPQL은 문자열이라 오타를 컴파일 시점에 잡지 못하고(애플리케이션 시작 시 검증), 결과도 `Object[]`라 타입 정보가 없다. 타입 안정성이 필요하면 DTO 생성자 표현식이나 QueryDSL을 쓴다.
> - `SELECT` 절의 서브쿼리는 JPA 표준이 아니라 Hibernate 6 확장 문법이다.
