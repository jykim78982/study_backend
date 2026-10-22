---
tags: [스프링부트, JPA, SpringDataJPA, 쿼리메서드, JPQL, 참고자료]
---

> 🔗 관련 노트: [[044_JPA 추가하기 — MenuRepository로 첫 API 만들기]] · [[045_JPA 기본 메서드 실습 — Postman으로 CRUD 완성하기]] · [[023_ORM 개념과 주요 프레임워크 — JDBC에서 JPA까지 참고자료]]

# Spring Data JPA 쿼리 메서드 — 이름 규칙과 연산자 키워드

Spring Data JPA의 **쿼리 메서드(Query Method)**는 리포지토리 인터페이스에 선언한 **메서드 이름을 분석해서 JPQL을 자동으로 만들어주는 기능**이다. 구현 코드는 한 줄도 쓰지 않고, 이름만 규칙에 맞게 지으면 된다.

```java
public interface MenuRepository extends JpaRepository<Menu, Long> {
    List<Menu> findByPriceLessThanEqual(Integer price);   // 선언만 하면 끝
}
```

## 0. 이름은 어떻게 해석되는가

메서드 이름은 크게 세 덩어리로 쪼개서 해석된다.

```
find  By  KorName Containing  And  Price LessThanEqual  OrderBy Price Desc
└주어┘└구분┘└──── 조건 1 ────┘└접속┘└────── 조건 2 ──────┘└───── 정렬 ─────┘
```

| 부분 | 역할 | 예 |
|---|---|---|
| 주어(동작) | 무엇을 할지 | `find`, `read`, `get`, `query`, `stream`, `count`, `exists`, `delete`, `remove` |
| `By` | 여기서부터 조건이 시작된다는 구분자 | `By` |
| 조건 | **엔티티 필드명** + 연산자 키워드 | `KorNameContaining`, `PriceLessThanEqual` |
| 접속어 | 조건끼리 연결 | `And`, `Or` |
| 정렬 | 결과 정렬 | `OrderByPriceDesc` |

> **추가 설명 — 필드명은 컬럼명이 아니라 엔티티 필드명이다**: 조건에 들어가는 이름은 DB 컬럼(`kor_name`)이 아니라 **자바 엔티티의 필드명(`korName`)**을 첫 글자만 대문자로 쓴 것(`KorName`)이다. 메서드 이름에서 만들어지는 것도 SQL이 아니라 엔티티·필드 이름으로 쓰인 **JPQL**이고, 그걸 Hibernate가 다시 테이블·컬럼 이름의 SQL로 바꿔서 실행한다. 필드명에 오타가 있으면 애플리케이션 시작 시점에 `No property 'xxx' found for type 'Menu'` 에러가 나므로, 잘못된 이름이 실행 중에 숨어 있을 일은 없다.

> **추가 설명 — 파라미터는 순서대로 대응된다**: 조건이 등장하는 순서대로 메서드 파라미터가 `?1`, `?2`…에 들어간다. `findByKorNameAndPrice(String korName, Integer price)`에서 파라미터 순서를 바꿔 쓰면 타입이 안 맞아 에러가 나거나, 같은 타입이면 엉뚱한 값이 비교된다.

## 1. 조건 검색 (비교)

| 키워드 | 메서드 예시 | 생성되는 조건 | 비고 |
|---|---|---|---|
| `Is`, `Equals` | `findByUsername(String name)` | `WHERE u.username = ?1` | 생략 가능(`findByUsername`과 같음) |
| `Not` | `findByUsernameNot(String name)` | `WHERE u.username <> ?1` | 불일치 |
| `GreaterThan` | `findByAgeGreaterThan(int age)` | `WHERE u.age > ?1` | 초과 |
| `GreaterThanEqual` | `findByAgeGreaterThanEqual(int age)` | `WHERE u.age >= ?1` | 이상 |
| `LessThan` | `findByAgeLessThan(int age)` | `WHERE u.age < ?1` | 미만 |
| `LessThanEqual` | `findByAgeLessThanEqual(int age)` | `WHERE u.age <= ?1` | 이하 |
| `Between` | `findByAgeBetween(int min, int max)` | `WHERE u.age BETWEEN ?1 AND ?2` | 양 끝 포함(이상·이하) |
| `Before` | `findByCreatedAtBefore(LocalDateTime t)` | `WHERE u.createdAt < ?1` | 날짜·시간용 미만 |
| `After` | `findByCreatedAtAfter(LocalDateTime t)` | `WHERE u.createdAt > ?1` | 날짜·시간용 초과 |

> `Before`/`After`는 `LessThan`/`GreaterThan`과 같은 SQL을 만든다. 날짜 필드에서 의미를 더 자연스럽게 읽히게 하려는 별칭이다.

## 2. 문자열 검색

| 키워드 | 메서드 예시 | 생성되는 조건 | 비고 |
|---|---|---|---|
| `Like` | `findByNameLike(String name)` | `WHERE u.name LIKE ?1` | `%`를 **직접 붙여서** 넘겨야 함(`"%라떼%"`) |
| `NotLike` | `findByNameNotLike(String name)` | `WHERE u.name NOT LIKE ?1` | |
| `StartingWith` | `findByNameStartingWith(String prefix)` | `WHERE u.name LIKE ?1%` | 특정 단어로 시작 |
| `EndingWith` | `findByNameEndingWith(String suffix)` | `WHERE u.name LIKE %?1` | 특정 단어로 끝남 |
| `Containing` | `findByNameContaining(String str)` | `WHERE u.name LIKE %?1%` | 특정 단어 포함(검색창에 가장 많이 씀) |
| `IgnoreCase` | `findByNameIgnoreCase(String name)` | `WHERE UPPER(u.name) = UPPER(?1)` | 대소문자 무시 |

> **추가 설명 — Like와 Containing의 차이**: `Like`는 넘긴 문자열을 그대로 패턴으로 쓰기 때문에 `%`를 호출하는 쪽에서 붙여야 한다. 반면 `Containing`, `StartingWith`, `EndingWith`는 `%`를 **알아서 붙여주고**, 사용자가 입력한 값 안의 `%`, `_` 같은 특수문자는 **이스케이프 처리**해준다. 사용자 검색어를 받는 기능이라면 `Containing`을 쓰는 것이 안전하다.

> **추가 설명 — IgnoreCase 조합**: `findByEngNameContainingIgnoreCase(String keyword)`처럼 다른 키워드 뒤에 붙일 수 있다. 모든 문자열 조건에 일괄 적용하려면 `findByKorNameAndEngNameAllIgnoreCase(...)`처럼 `AllIgnoreCase`를 끝에 붙인다. 한글은 대소문자가 없으므로 영문 필드에서 의미가 있다.

## 3. Null, 컬렉션, Boolean

| 키워드 | 메서드 예시 | 생성되는 조건 | 비고 |
|---|---|---|---|
| `IsNull`, `Null` | `findByEmailIsNull()` | `WHERE u.email IS NULL` | 파라미터 없음 |
| `IsNotNull`, `NotNull` | `findByEmailIsNotNull()` | `WHERE u.email IS NOT NULL` | 파라미터 없음 |
| `In` | `findByAgeIn(Collection<Integer> ages)` | `WHERE u.age IN (?1)` | 목록 중 하나와 일치 |
| `NotIn` | `findByAgeNotIn(Collection<Integer> ages)` | `WHERE u.age NOT IN (?1)` | 목록에 없음 |
| `True` | `findByActiveTrue()` | `WHERE u.active = true` | Boolean 필드, 파라미터 없음 |
| `False` | `findByActiveFalse()` | `WHERE u.active = false` | Boolean 필드, 파라미터 없음 |

> **추가 설명 — 파라미터에 null을 넘기면?**: `findByEmail(null)`처럼 일반 조건에 `null`을 넘기면 Spring Data JPA가 이를 `email IS NULL`로 바꿔준다. 다만 "검색 조건이 비어 있으면 그 조건은 무시하고 전체를 조회"하는 동작은 **해주지 않는다.** 검색 조건이 있을 때만 붙는 동적 쿼리가 필요하면 쿼리 메서드가 아니라 `Specification`, Querydsl, 또는 조건별로 메서드를 나눠 호출하는 방식을 써야 한다.

## 4. 다중 조건 조합

| 키워드 | 메서드 예시 | 생성되는 조건 |
|---|---|---|
| `And` | `findByUsernameAndAge(String name, int age)` | `WHERE u.username = ?1 AND u.age = ?2` |
| `Or` | `findByUsernameOrAge(String name, int age)` | `WHERE u.username = ?1 OR u.age = ?2` |

> `And`와 `Or`를 섞으면 SQL처럼 `And`가 먼저 묶인다. `findByAAndBOrC`는 `(A AND B) OR C`로 해석되고, 괄호로 순서를 바꿀 방법은 없다. 이런 조합이 필요하면 `@Query`로 직접 쓰는 편이 명확하다.

## 5. 정렬, 개수 제한, 중복 제거

| 키워드 | 메서드 예시 | 설명 및 생성 SQL |
|---|---|---|
| `OrderBy` | `findByAgeOrderByUsernameDesc(int age)` | `ORDER BY u.username DESC` |
| `OrderBy` (여러 기준) | `findByAgeOrderByUsernameAscIdDesc(int age)` | `ORDER BY u.username ASC, u.id DESC` |
| `First`, `Top` | `findFirst3ByOrderByAgeDesc()` | `LIMIT 3` (상위 N개) |
| `First`, `Top` (숫자 없음) | `findFirstByOrderByCreatedAtDesc()` | `LIMIT 1` (가장 최근 1건) |
| `Distinct` | `findDistinctByUsername(String name)` | `SELECT DISTINCT ...` |

> **추가 설명 — 정렬 기준을 호출하는 쪽에서 정하고 싶을 때**: 이름에 `OrderBy`를 박아 넣으면 정렬이 고정된다. 화면에서 정렬 기준을 바꿀 수 있어야 한다면 `Sort` 파라미터를 받는다.
>
> ```java
> List<Menu> findByPriceLessThan(Integer price, Sort sort);
>
> // 호출
> menuRepository.findByPriceLessThan(5000, Sort.by(Sort.Direction.DESC, "price"));
> ```
>
> 아무 조건 없이 전체를 정렬만 하고 싶다면 `findAll(Sort sort)`가 이미 `JpaRepository`에 있다. 조건 없이 `findAllByOrderByPriceDesc()`라고 써도 된다(`By` 뒤에 조건 없이 바로 `OrderBy`).

## 6. 연관 관계 따라 검색

엔티티 안의 연관 객체 필드를 타고 들어가서 검색할 수도 있다.

```java
// User 엔티티가 Team 객체를 가지는 경우 (user.team.name)
List<User> findByTeamName(String teamName);
```

생성 JPQL: `SELECT u FROM User u JOIN u.team t WHERE t.name = ?1`

> **추가 설명 — 이름이 애매할 때는 `_`로 끊는다**: `findByTeamName`은 먼저 `User`에 `teamName` 필드가 있는지 찾고, 없으면 `team.name`으로 해석한다. 만약 `User`에 `teamName` 필드도 있고 `team.name`도 있다면 의도와 다르게 해석될 수 있다. 이럴 때는 `findByTeam_Name`처럼 밑줄로 경계를 명시한다.

## 7. 개수, 존재 여부, 삭제

| 키워드 | 메서드 예시 | 반환 | 설명 |
|---|---|---|---|
| `countBy` | `countByStatus(String status)` | `long` | 조건에 맞는 데이터 개수 |
| `existsBy` | `existsByEmail(String email)` | `boolean` | 조건에 맞는 데이터가 하나라도 있는지(회원가입 중복 확인 등) |
| `deleteBy`, `removeBy` | `deleteByUsername(String name)` | `void` 또는 `long`(삭제 건수) | 조건에 맞는 데이터 삭제 |

> **추가 설명 — deleteBy는 한 번에 지우지 않는다**: `deleteByUsername`은 `DELETE FROM ... WHERE ...` 한 방이 아니라, **먼저 조건으로 엔티티들을 조회한 뒤 한 건씩 `remove`**한다. 100건이면 SELECT 1번 + DELETE 100번이 나간다. 또 데이터를 변경하는 작업이므로 호출하는 서비스 메서드에 `@Transactional`이 있어야 한다(없으면 `TransactionRequiredException`). 대량 삭제가 필요하면 아래처럼 직접 쓴다.
>
> ```java
> @Modifying
> @Transactional
> @Query("DELETE FROM Menu m WHERE m.price < :price")
> int deleteCheapMenus(@Param("price") Integer price);
> ```

## 8. 반환 타입 고르기 (추가)

같은 조건이라도 반환 타입에 따라 동작이 달라진다.

| 반환 타입 | 결과가 없을 때 | 결과가 여러 건일 때 | 용도 |
|---|---|---|---|
| `Menu` | `null` | 예외(`IncorrectResultSizeDataAccessException`) | 결과가 반드시 하나인 경우 |
| `Optional<Menu>` | `Optional.empty()` | 예외 | 하나 또는 없음 (권장) |
| `List<Menu>` | 빈 리스트 `[]` | 전부 담김 | 여러 건 조회 |
| `Page<Menu>` | 빈 페이지 | 요청한 페이지만 | 페이징 + 전체 개수 필요 |
| `Slice<Menu>` | 빈 슬라이스 | 요청한 페이지만 | 페이징, 전체 개수 불필요("더보기") |

> 단건 조회는 `null` 체크를 잊기 쉬우므로 `Optional`을 반환하는 것이 권장된다. `List`는 결과가 없어도 `null`이 아니라 빈 리스트를 돌려주므로 null 체크가 필요 없다.

## 9. 페이징

메서드 파라미터에 `Pageable`을 넘기면 조건·정렬과 함께 페이징을 간단히 구현할 수 있다.

```java
Page<User> findByAgeGreaterThan(int age, Pageable pageable);

// 호출: 0번째 페이지(첫 페이지), 10개씩, 나이 내림차순
Page<User> page = userRepository.findByAgeGreaterThan(
        20, PageRequest.of(0, 10, Sort.by("age").descending()));

page.getContent();        // 현재 페이지 데이터 목록
page.getTotalElements();  // 조건에 맞는 전체 개수 (목록 화면의 "총 N개")
page.getTotalPages();     // 전체 페이지 수
```

> **추가 설명 — Page와 Slice**: `Page`는 "총 N개", "전체 몇 페이지"를 알려주기 위해 **데이터 조회 쿼리와 별도로 `COUNT` 쿼리를 한 번 더** 실행한다. 페이지 번호 버튼이 있는 관리자 목록 화면에는 `Page`가 맞다. 반대로 무한 스크롤이나 "더보기" 버튼처럼 다음 페이지가 있는지만 알면 되는 화면이라면 `COUNT` 쿼리가 없는 `Slice`가 더 가볍다. 페이지 번호는 **0부터 시작**한다는 점도 주의한다.

## 10. ncafe Menu 엔티티에 적용해보기 (추가)

`Menu`(`id`, `korName`, `engName`, `price`)를 기준으로 실제로 쓸 만한 예시다.

```java
public interface MenuRepository extends JpaRepository<Menu, Long> {

    // 메뉴 이름 검색 (검색창)
    List<Menu> findByKorNameContaining(String keyword);

    // 영문 이름 대소문자 무시 검색
    List<Menu> findByEngNameContainingIgnoreCase(String keyword);

    // 가격 범위 필터, 가격 낮은 순
    List<Menu> findByPriceBetweenOrderByPriceAsc(Integer min, Integer max);

    // 같은 이름의 메뉴가 이미 있는지 (등록 시 중복 확인)
    boolean existsByKorName(String korName);

    // 가장 비싼 메뉴 3개
    List<Menu> findTop3ByOrderByPriceDesc();

    // 이름 검색 + 페이징 (관리자 목록 화면)
    Page<Menu> findByKorNameContaining(String keyword, Pageable pageable);
}
```

## 11. 실무 팁

- **메서드 이름이 너무 길어지면 멈춘다**: 조건이 3~4개를 넘어가면 `findByUsernameAndAgeGreaterThanAndEmailContaining...`처럼 이름이 길어져 읽기 어렵다. 이때는 `@Query`로 JPQL을 직접 쓰거나 Querydsl을 쓰는 것이 깔끔하다.
- **검색 조건이 선택적이라면 쿼리 메서드로는 어렵다**: "카테고리를 고르면 카테고리로, 검색어를 넣으면 검색어로, 둘 다 비면 전체"처럼 조건이 들어오기도 하고 안 들어오기도 하는 화면은 쿼리 메서드 조합으로 풀면 메서드 수가 폭발한다. `Specification`이나 Querydsl 같은 동적 쿼리 도구를 쓴다.
- **실행된 SQL을 꼭 확인한다**: `show-sql: true`로 콘솔에 찍히는 SQL을 보면서, 이름이 의도대로 해석됐는지 확인하는 습관을 들인다. 이름은 그럴듯한데 조건이 엉뚱하게 묶이는 경우(`And`/`Or` 혼합 등)를 여기서 잡아낼 수 있다.
