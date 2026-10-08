---
tags: [JPA, SpringDataJPA, JPQL, Query, 쿼리메서드]
---

> 🔗 관련 노트: [[080_Spring Data JPA 리포지토리와 엔티티 매핑 — 쿼리 메서드, 연관관계, 복합키]] · [[081_JPA 연관관계 매핑과 쿼리 메서드 조인 — 1대N, 1대1, 복합키]] · [[024_Spring Data JPA 쿼리 메서드 — 이름 규칙과 연산자 키워드 참고자료]]

# JPQL과 @Query — 쿼리 메서드 이름 대신 쿼리를 직접 쓰기

쿼리 메서드는 이름만 지으면 SQL이 만들어져서 편하지만, 조건이 늘어나면 이름이 감당할 수 없이 길어진다. 이럴 때 메서드 이름은 짧게 두고, 쿼리는 `@Query`에 **JPQL**로 직접 적는 방법을 정리한다.

## 1. 쿼리 메서드 이름이 길어지는 문제

카테고리를 정렬 순서(`sortOrder`)대로 전부 가져오는 메서드는 이렇게 쓴다.

```java
List<Category> findAllByOrderBySortOrderAsc();
```

- `findAll`: 전부 달라는 것
- `By`: 조건의 시작. 조건이 없어도 뒤에 `OrderBy`를 붙이려면 `By`를 먼저 쓴다.
- `OrderBySortOrderAsc`: `sortOrder` 필드 기준 오름차순 정렬

이 정도면 괜찮다. 그런데 검색 조건이나 정렬 기준이 늘어나면 메서드 하나의 이름이 화면 오른쪽 끝까지 길어진다. 목록 조회처럼 조건이 복잡한 경우에는 이 방식이 현실성이 떨어진다.

또 메서드 이름 규칙 자체가 **약속**이라서 키워드를 다 외우기도 쉽지 않다. SQL을 쓰지 않으려고 쿼리 메서드를 택했는데, 이름 규칙 때문에 또 고생하는 셈이 된다. 간단한 조건을 이름 몇 단어로 해결할 때는 쿼리 메서드가 아주 좋지만, SQL을 이미 아는 입장에서는 복잡한 조건까지 이름으로 표현하는 게 오히려 불편하다.

## 2. @Query — 이름 규칙 대신 쿼리를 붙인다

메서드 이름이 쿼리를 만드는 도구였다면, 규칙을 지키지 않은 이름은 쿼리를 만들 수 없다. 이때 메서드 위에 **"쿼리는 내가 줄게"**라고 `@Query`를 붙이면, 이름 규칙이 맞지 않아도 그 쿼리로 SQL을 만든다.

```java
public interface MemberRepository extends JpaRepository<Member, Integer> {

    @Query("from Member where username = :username")
    Member findByUserName(@Param("username") String userName);
}
```

그렇다고 이름을 아무렇게나 지으라는 뜻은 아니다. 목적은 **이름을 짧고 읽기 좋게 유지하면서**, 조건은 쿼리로 정확하게 주는 것이다.

> **Spring Data JPA가 쿼리를 찾는 순서 (Query Lookup Strategy)**: 기본 전략(`CREATE_IF_NOT_FOUND`)에서는 먼저 메서드에 `@Query`로 **직접 정의한 쿼리가 있는지** 찾고, 있으면 그걸 쓴다. 없을 때만 메서드 이름을 분석해서 쿼리를 만든다(derived query). 그래서 `@Query`가 붙은 메서드는 이름이 `findByUserName`처럼 규칙에 맞든 안 맞든 이름 분석을 하지 않는다.

## 3. JPQL 문법 — SQL과 비슷하지만 대상이 다르다

`@Query`에 쓰는 언어는 DBMS의 SQL이 아니라 **JPQL**(Java Persistence Query Language)이다. 우리가 배운 표준 SQL(ANSI SQL)의 구문 규칙을 그대로 따르면서, 어떤 DBMS에서도 호환되는 쿼리를 만들기 위한 언어다. 연산자, `WHERE`, `ORDER BY`, `JOIN` 등은 SQL과 거의 같다. 다른 점은 다음과 같다.

**1) 테이블·컬럼이 아니라 엔티티·필드 이름을 쓴다**

```
@Entity
public class Member {          ← "from Member"의 Member는 이 엔티티 이름
    @Column(name = "user_name")
    private String username;   ← "where username"의 username은 이 필드 이름
}
```

DB 테이블이 `members`이고 컬럼이 `user_name`이어도, JPQL에는 `Member`, `username`을 쓴다. JPQL에서 "테이블처럼" 쓰이는 것은 엔티티이고, "컬럼처럼" 쓰이는 것은 엔티티 필드다. Hibernate가 이걸 실제 테이블·컬럼 이름의 SQL로 바꿔서 실행한다.

**2) `select *` 대신 별칭을 쓴다**

```java
@Query("select m from Member m where m.username = :username")
```

- `Member m`: SQL처럼 엔티티 뒤에 공백을 두고 별칭(`m`)을 붙인다.
- `select m`: 별칭만 쓰면 **그 엔티티의 모든 필드**를 가져온다는 뜻이다. JPQL에서는 `select *`를 쓸 수 없다.
- 필요한 필드만 고를 수도 있다(`select m.username, m.email ...`).
- 엔티티 이름을 별칭처럼 쓸 수는 없다. `select Member.username from Member`는 오류다. 필드에는 반드시 FROM 절에서 선언한 별칭으로 접근한다.

`m.username`처럼 별칭에서 점(`.`)으로 필드를 따라가는 것을 **경로 표현식(path expression)**이라고 한다. `m.team.name`처럼 연관 엔티티를 따라 이어갈 수도 있는데, 이때 Hibernate가 SQL에 조인을 자동으로 넣어준다(**묵시적 조인**).

**3) `select`는 생략할 수 있다(Hibernate 한정)**

앞의 `"from Member where username = :username"`처럼 `select`를 아예 빼도 동작한다. 생략하면 `select m`처럼 엔티티 전체를 가져온다.

> 정확히는 `select` 생략과 별칭 생략은 **JPQL 표준이 아니라 Hibernate의 HQL 확장 문법**이다. Hibernate를 쓰는 Spring Boot에서는 동작하지만, 표준 JPQL 규칙대로라면 `select m from Member m where m.username = :username`처럼 `select`와 별칭을 모두 써야 한다. 다른 사람이 읽기에도 이쪽이 명확하다.

**4) 나머지 구절은 SQL과 거의 같다 — 몇 가지 차이만 기억한다**

| 구절 | JPQL에서 | SQL과 다른 점 |
|---|---|---|
| 연산자 | `=`, `<>`, `<`, `>`, `AND`, `OR`, `NOT`, `LIKE`, `BETWEEN`, `IN`, `IS NULL` | 표준의 "같지 않다"는 `<>`다(`!=`는 Hibernate가 받아주는 표기) |
| 조인 | `from Menu m join m.category c` | `ON` 조건 대신 **연관 필드 경로**를 적는다. 조인 조건은 매핑 정보에서 가져온다 |
| `LEFT JOIN` | `from Menu m left join m.category c` | 카테고리가 없는 메뉴도 결과에 남고, 이때 `c`는 `NULL`이다 |
| `JOIN FETCH` | `select m from Menu m join fetch m.category` | SQL에는 없는 개념. 연관 엔티티를 **이 쿼리에서만** 함께 가져와 N+1 문제를 막는다 |
| 집계 | `select c.name, count(m) ... group by c.name having count(m) > 5` | 같다. `WHERE`는 그룹화 전, `HAVING`은 그룹화 후 필터 |
| 서브쿼리 | `where m.price > (select avg(m2.price) from Menu m2)` | 표준은 `WHERE`, `HAVING` 절에서만 허용(`SELECT`·`FROM` 절은 Hibernate 6 확장) |
| 개수 제한 | — | `LIMIT`/`OFFSET`은 표준 JPQL에 없다. 메서드 파라미터로 `Pageable`을 넘겨 처리한다 |

## 4. 파라미터 바인딩 — :이름과 @Param

```java
@Query("from Member where username = :username")
Member findByUserName(@Param("username") String userName);
```

- `:username`: 콜론(`:`)이 붙은 것은 엔티티 필드가 아니라 **메서드로 넘겨받은 값이 꽂힐 자리**다. 왼쪽 `username`은 엔티티 필드, 오른쪽 `:username`은 파라미터다.
- 이 자리에 어떤 메서드 파라미터를 넣을지는 **이름으로** 맞춘다. 그래서 `:username`과 메서드 파라미터 이름이 같아야 한다.
- 이 예시처럼 파라미터 이름(`userName`)이 쿼리의 이름(`username`)과 다르면, `@Param("username")`으로 "이 파라미터는 `username`이라는 이름으로 전달된다"고 알려줘야 한다.

정리하면 맞춰야 할 이름이 세 가지다.

| 쿼리 속 이름 | 맞춰야 하는 대상 |
|---|---|
| `from Member` | 엔티티 클래스 이름 |
| `where username` | 엔티티 필드 이름 |
| `= :username` | 메서드 파라미터 이름 (다르면 `@Param`으로 지정) |

> **보충**
> - Spring Boot의 Gradle·Maven 플러그인은 컴파일할 때 파라미터 이름을 보존하는 옵션(`-parameters`)을 켜두기 때문에, 파라미터 이름이 `:username`과 **똑같으면** `@Param`을 생략해도 동작한다. 다만 이름을 바꾸다 실수하기 쉬우므로 `@Param`을 명시하는 습관이 안전하다.
> - 반환 타입이 `Member`인데 결과가 두 건 이상이면 예외가 나고, 없으면 `null`이 온다. 단건 조회는 `Optional<Member>`로 받는 것이 좋다.

**위치 기반 파라미터도 있다**: 이름 대신 `?1`, `?2`처럼 **순서 번호**로 받을 수도 있다.

```java
@Query("select m from Menu m where m.price between ?1 and ?2")
List<Menu> findInRange(int min, int max);        // 첫 번째 인수 → ?1, 두 번째 → ?2
```

하지만 파라미터 순서를 바꾸거나 하나를 추가하면 번호가 어긋나기 쉽다. 이름 기반(`:name`)이 읽기 쉽고 순서와 무관하게 안전해서 실무에서는 주로 이름 기반을 쓴다.

## 5. LIKE 검색 키워드와 특수문자 처리

쿼리 메서드의 문자열 검색 키워드는 이름이 여러 형태로 준비되어 있고, 같은 뜻이다.

| 의미 | 같은 뜻의 키워드 |
|---|---|
| ~로 시작 | `IsStartingWith`, `StartingWith`, `StartsWith` |
| ~로 끝남 | `IsEndingWith`, `EndingWith`, `EndsWith` |
| ~를 포함 | `IsContaining`, `Containing`, `Contains` |
| ~를 포함하지 않음 | `IsNotContaining`, `NotContaining`, `NotContains` |

이 키워드들로 만든 쿼리에 넘긴 값은 **정제(sanitize)**된다. 즉 사용자가 입력한 값 안에 `%`나 `_`처럼 LIKE에서 와일드카드로 쓰이는 문자가 있으면, 이를 **이스케이프 처리해서 글자 그대로** 비교한다. "100%"를 검색했을 때 `%`가 "아무 글자나"로 해석되지 않는다는 뜻이다. 이스케이프 문자는 `@EnableJpaRepositories`의 `escapeCharacter` 속성으로 바꿀 수 있다.

> `@Query`에 `like :keyword`처럼 직접 쓰면 이 정제가 자동으로 일어나지 않는다. 직접 쓴 쿼리에서 같은 처리를 하려면 SpEL 표현식(`:#{escape([0])}`와 `escape :#{escapeCharacter()}`)을 써야 한다.

## 6. 복잡한 조회 예시 — 서브쿼리와 조인

쿼리 메서드로는 만들기 어려운 목록 조회도 JPQL로는 SQL처럼 쓸 수 있다.

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
List<Object[]> findAll(@Param("categoryName") String categoryName,
                       @Param("minReviewCount") Long minReviewCount);
```

- `"""` ... `"""`: 자바 15부터 쓸 수 있는 **텍스트 블록**이다. 여러 줄 문자열을 `+`로 잇지 않고 그대로 쓸 수 있어 긴 쿼리에 편하다.
- `LEFT JOIN m.category c`: 조인 조건(`ON`)을 쓰지 않고 **엔티티의 연관 필드**(`m.category`)를 따라 조인한다. 조인 조건은 매핑 정보에서 가져온다.
- `r.menu = m`: 외래키 값끼리가 아니라 **엔티티끼리** 비교한다.
- SELECT 절의 서브쿼리로 메뉴별 평균 평점을, WHERE 절의 서브쿼리로 리뷰 수 조건을 건다.

> **보충**
> - `LEFT JOIN`을 했어도 `WHERE c.name = :categoryName` 조건이 있으면 카테고리가 없는 메뉴는 어차피 빠지므로 결과는 `INNER JOIN`과 같아진다.
> - 필드를 골라서 조회하면 결과가 `Object[]`(한 행 = 값 배열)로 와서, `row[0]`, `row[3]`처럼 순서로 꺼내야 해 실수하기 쉽다. 실무에서는 `select new com.newcafe.backend.dto.MenuSummary(m.id, m.name, ...)`처럼 **DTO로 바로 받는 생성자 표현식**이나 인터페이스 프로젝션을 쓰는 편이 안전하다.
> - SELECT 절 서브쿼리는 JPA 표준 JPQL에는 없고, Hibernate 6가 지원하는 확장이다.

## 7. 수정 쿼리 만들기 — updatePrice 예제

가격만 바꾸는 메서드를 따로 만든다고 가정해보자. 수정은 원래 `CrudRepository`의 `save`가 이미 해주므로 좋은 방법은 아니고, `@Query` 연습을 위한 예제다.

```java
int updatePrice(Long id, Integer newPrice);
```

이 메서드는 부모 인터페이스에 정의되어 있지도 않고, 이름도 쿼리 메서드 규칙(`find`, `count`, `delete`…)에 맞지 않는다. 그러니 쿼리를 직접 달아줘야 한다.

```java
@Modifying
@Transactional
@Query("update Menu m set m.price = :newPrice where m.id = :id")
int updatePrice(@Param("id") Long id, @Param("newPrice") Integer newPrice);
```

- `@Query`: JPQL로 UPDATE 문을 쓴다. 역시 테이블이 아니라 엔티티(`Menu`)와 필드(`price`)를 쓴다.
- `@Modifying`: 이 쿼리가 SELECT가 아니라 **데이터를 바꾸는** 쿼리라고 알려준다. 없으면 실행할 때 "SELECT가 아닌 쿼리는 실행할 수 없다"는 예외가 난다.
- `@Transactional`: 데이터를 바꾸는 작업은 **트랜잭션 안에서** 실행되어야 한다. 없으면 `TransactionRequiredException`이 난다. 보통은 리포지토리가 아니라 이 메서드를 호출하는 서비스 메서드에 붙인다.
- 반환 타입 `int`: 수정된 행 수다.

**벌크 쿼리와 영속성 컨텍스트**: 이렇게 `@Query`로 쓴 UPDATE·DELETE를 **벌크 연산**이라고 한다. 엔티티를 한 건씩 조회해서 고치는 게 아니라, 조건에 맞는 행을 SQL 한 문장으로 한꺼번에 바꾸기 때문이다. 대신 영속성 컨텍스트(1차 캐시)를 거치지 않고 DB에 바로 실행된다. 그래서 같은 트랜잭션 안에서 이미 조회해둔 `Menu` 객체는 옛날 가격을 그대로 들고 있고, 다시 `findById`를 해도 JPA는 DB가 아니라 1차 캐시의 옛날 객체를 돌려준다.

| 해결 방법 | 하는 일 |
|---|---|
| `@Modifying(clearAutomatically = true)` | 벌크 쿼리 **실행 후** 영속성 컨텍스트를 비운다. 다음 조회는 DB에서 최신 값을 읽는다 |
| `@Modifying(flushAutomatically = true)` | 벌크 쿼리 **실행 전** 아직 DB에 안 보낸 변경 사항을 먼저 보낸다(flush) |

> `flush()`는 메모리의 변경을 DB로 **내보내는** 것이지, DB에서 바뀐 값을 메모리로 **가져오는** 것이 아니다. 그래서 벌크 쿼리 후의 옛날 값 문제는 flush가 아니라 **clear**(영속성 컨텍스트 비우기)로 해결한다. 트랜잭션이 끝나면 영속성 컨텍스트도 함께 사라지므로, 다음 트랜잭션에서 조회할 때는 대부분 자연스럽게 최신 값을 읽는다.

> 벌크 DELETE는 엔티티에 설정한 `cascade`를 적용하지 않는다. 지우려는 메뉴를 다른 테이블이 외래키로 참조하고 있으면 DB 제약조건 때문에 오류가 난다. 또 표준 문법은 `delete from Menu m where ...`처럼 `from`을 쓴다.

이 예제에서 자연스럽게 다음 질문이 나온다. **수정 작업에는 왜 트랜잭션이 필요한가?** 이것이 다음 주제인 트랜잭션 처리로 이어진다.

## 8. 기본은 쿼리 메서드, 예외는 @Query

`@Query`를 쓸 수 있게 되면 "그냥 다 SQL로 쓰는 게 편하다"며 모든 메서드에 쿼리를 붙이고 싶어진다. 하지만 항상 **기본**이 있고, 기본을 쓰면서 예외를 다루는 것이 원칙이다.

| 상황 | 선택 |
|---|---|
| 단순 조회, 조건 한두 개 | **쿼리 메서드** (기본) |
| 이름이 너무 길어지거나 쿼리 메서드로 표현하기 어려운 조회 | `@Query` + JPQL (예외) |
| 특정 DBMS 기능이 꼭 필요한 경우 | `@Query(nativeQuery = true)` (최후 수단, DBMS 종속) |

JPQL을 쓰면 SQL과 거의 같은 문법을 쓰면서도 DBMS에 종속되지 않는다. 반대로 `nativeQuery`로 DBMS의 SQL을 그대로 쓰면, 엔티티만 바라보고 개발한다는 JPA의 장점이 사라진다.

## 9. JpaRepository에 이미 있는 메서드 중 바뀐 것

강의 화면에 나온 `JpaRepository`의 메서드 중 일부는 현재 이름이 바뀌었다.

| 강의 화면 | 현재 | 비고 |
|---|---|---|
| `getOne(ID id)` | `getReferenceById(ID id)` | 실제 조회 없이 참조(프록시)만 얻는다 |
| `deleteInBatch(Iterable<T>)` | `deleteAllInBatch(Iterable<T>)` | 여러 건을 DELETE 한 번으로 삭제 |
| `flush()`, `saveAndFlush()`, `saveAllAndFlush()`, `deleteAllByIdInBatch()`, `deleteAllInBatch()` | 그대로 | |

> 강의 예제의 `Member`는 id가 `int`(기본형), 리포지토리는 `JpaRepository<Member, Integer>`다. 동작은 하지만, `save`가 새 엔티티인지 판단할 때 기본형은 `0`을 기준으로 삼아서 헷갈리기 쉽다. id는 `Long`이나 `Integer` 같은 참조형으로 두는 것이 일반적이다.
