# JPA 리포지토리와 조회 도구 오답노트

### 1. JpaRepository 기본 메서드 설명

**문제**: 다음 중 `JpaRepository`의 기본 제공 메서드 설명으로 옳지 **않은** 것은?

1. `findById()`는 `Optional`로 결과를 반환한다.
2. `deleteById()`는 복합 키를 자동으로 변환해 삭제한다.
3. `save()`는 식별자와 영속성 상태에 따라 등록 또는 수정에 사용된다.
4. `findAll()`은 엔티티 목록을 조회한다.

**정답: 2번**

`deleteById(ID id)`는 **식별자 하나**를 받아 그 엔티티를 삭제하는 기본 메서드다. 여기서 "식별자 하나"란 리포지토리를 선언할 때 두 번째 타입으로 지정한 `ID` 타입의 값이다.

```java
public interface MenuRepository extends JpaRepository<Menu, Long> {}     // ID = Long
public interface LikeRepository extends JpaRepository<Like, LikeId> {}   // ID = LikeId (복합키 클래스)
```

복합키를 쓰는 엔티티라도 `deleteById`를 못 쓰는 것은 아니다. 다만 `memberId`, `menuId` 값을 따로 넘기면 스프링이 알아서 키 객체로 **변환해주지 않는다.** 개발자가 복합키 클래스(`@EmbeddedId`나 `@IdClass`에 쓰는 `LikeId`)의 객체를 **직접 만들어서** 넘겨야 한다.

```java
// ❌ 이런 메서드는 없다 — 값 두 개를 받아 키로 바꿔주지 않는다
likeRepository.deleteById(1L, 2L);

// ✅ 복합키 객체를 직접 만들어 넘긴다
likeRepository.deleteById(new LikeId(1L, 2L));

// ✅ 또는 먼저 조회한 뒤 엔티티째 삭제한다
likeRepository.findById(new LikeId(1L, 2L)).ifPresent(likeRepository::delete);
```

이 객체로 엔티티를 제대로 찾으려면 복합키 클래스가 `equals()`/`hashCode()`를 값 기준으로 재정의하고 `Serializable`을 구현해야 한다. 그래서 "복합 키 처리는 별도 설계가 필요하다"는 것이다.

> **보충 — deleteById의 실제 동작**: `deleteById`는 바로 `DELETE` 한 번을 보내는 게 아니라, 먼저 `findById`로 엔티티를 조회한 다음 `delete(entity)`를 호출한다. 그래서 `SELECT` 후 `DELETE`가 나간다. 또 Spring Data JPA 3 이상에서는 해당 id가 없으면 예외 없이 **조용히 아무것도 하지 않는다**(2.x에서는 `EmptyResultDataAccessException`이 났다).

**나머지 보기가 옳은 이유**:

- **1번 `findById()`**: 단건 조회는 데이터가 없을 수 있으므로 `null` 대신 `Optional<T>`로 감싸서 돌려준다. 호출하는 쪽에서 `orElseThrow()`, `orElse()` 등으로 없는 경우를 반드시 처리하게 만든다.
- **3번 `save()`**: 엔티티가 새것인지 판단해서(기본적으로 id가 `null`이면 새것) 새것이면 `persist()`로 INSERT, 아니면 `merge()`로 UPDATE를 수행한다. 그래서 `update` 메서드가 따로 없다.
- **4번 `findAll()`**: 엔티티 전체 목록을 `List<T>`로 조회한다. 데이터가 없으면 `null`이 아니라 빈 리스트를 돌려준다.

**한 줄 요약**: `deleteById`는 리포지토리에 지정한 `ID` 타입 값 하나를 받는다. 복합키라면 복합키 객체를 직접 만들어 넘겨야 하고, 스프링이 값들을 키로 자동 변환해주지 않는다.

---

### 2. 동적이고 복잡한 조회에 권장되는 도구

**문제**: 조회 요구사항이 매우 동적이고 복잡해 가독성 있는 자바 코드로 작성하고 싶을 때 권장되는 도구는 무엇인가?

1. `JpaRepository`의 기본 `save()`
2. QueryDSL
3. `@Column` 네이밍 전략
4. 간단한 쿼리 메서드

**정답: 2번**

**동적 쿼리란**: 검색어가 있는지, 날짜 범위를 골랐는지, 카테고리 필터를 켰는지에 따라 **WHERE 조건이 붙었다 빠졌다 하는 쿼리**다. 쇼핑몰 목록 화면처럼 검색 조건이 많은 화면에서 거의 반드시 필요하다.

**QueryDSL이 적합한 이유**:

- 엔티티를 바탕으로 자동 생성되는 **Q클래스**(`QMenu` 등)를 이용해, 쿼리를 문자열이 아니라 **자바 메서드 체이닝**으로 쓴다.
- 필드명 오타나 타입이 맞지 않는 비교 같은 문법 오류를 **컴파일 시점에** 잡아준다. 문자열로 쓰는 JPQL은 실행해봐야(또는 앱이 시작돼야) 오류를 알 수 있다.
- `BooleanBuilder`나 `BooleanExpression`으로 "값이 있을 때만 조건을 붙이는" 코드를 `if`문처럼 직관적으로 쓸 수 있다.

```java
QMenu menu = QMenu.menu;
BooleanBuilder where = new BooleanBuilder();

if (keyword != null)    where.and(menu.korName.contains(keyword));
if (categoryId != null) where.and(menu.category.id.eq(categoryId));
if (maxPrice != null)   where.and(menu.price.loe(maxPrice));

List<Menu> result = queryFactory
        .selectFrom(menu)
        .where(where)            // 들어온 조건만 붙는다
        .orderBy(menu.price.asc())
        .fetch();
```

검색어만 넣으면 `WHERE kor_name LIKE ?` 하나만, 셋 다 넣으면 조건 세 개가 붙은 SQL이 만들어진다.

**나머지 보기가 오답인 이유**:

- **1번 `save()`**: 저장·수정용 메서드라서 조회나 동적 쿼리와는 관계가 없다.
- **3번 `@Column` 네이밍 전략**: 엔티티 필드와 DB 컬럼 이름을 연결하는 **매핑 설정**일 뿐, 쿼리를 작성하는 도구가 아니다.
- **4번 간단한 쿼리 메서드**: `findByTitleAndStatus(...)`처럼 이름으로 쿼리를 만드는 기능이다. 조건이 몇 개만 늘어도 이름이 매우 길어지고, **이름에 적힌 조건은 항상 붙는다.** 파라미터가 `null`이면 조건을 빼주는 게 아니라 `IS NULL` 비교로 바뀐다. "값이 있을 때만 조건을 붙이는" 동적 쿼리를 하려면 조건 조합마다 메서드를 따로 만들어야 해서 사실상 불가능하다.

> **보충 — 조회 도구를 고르는 순서**: 단순 조회는 쿼리 메서드, 쿼리 메서드로 안 되는 복잡한 쿼리는 JPQL(`@Query`), 조건이 동적으로 바뀌는 복잡한 조회는 QueryDSL 순서로 생각한다. JPA 표준인 Criteria API도 자바 코드로 동적 쿼리를 만들 수 있지만, 코드가 길고 읽기 어려워서 잘 쓰지 않는다. 문제에서 "**가독성 있는** 자바 코드"라고 한 것이 Criteria API가 아니라 QueryDSL을 가리키는 단서다.
>
> QueryDSL은 JPA 표준이 아닌 오픈소스 라이브러리라서, Q클래스를 생성하는 빌드 설정(어노테이션 프로세서)을 따로 해줘야 한다. Spring Boot 3에서는 `jakarta` 버전 의존성을 써야 한다.

**한 줄 요약**: 조건이 붙었다 빠졌다 하는 복잡한 조회는 Q클래스와 메서드 체이닝으로 읽기 쉽게 쓰고, 오류를 컴파일 시점에 잡아주는 QueryDSL이 적합하다.

tags: #JPA #SpringDataJPA #QueryDSL #쿼리메서드 #복합키

> 🔗 관련 노트: [[080_Spring Data JPA 리포지토리와 엔티티 매핑 — 쿼리 메서드, 연관관계, 복합키]] · [[081_JPA 연관관계 매핑과 쿼리 메서드 조인 — 1대N, 1대1, 복합키]] · [[045_JPA 기본 메서드 실습 — Postman으로 CRUD 완성하기]]
