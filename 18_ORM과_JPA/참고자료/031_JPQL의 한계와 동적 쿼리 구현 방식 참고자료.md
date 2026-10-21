---
tags: [JPA, SpringDataJPA, JPQL, 동적쿼리, EntityManager, CustomRepository, 참고자료]
---

> 🔗 관련 노트: [[081_JPQL과 @Query — 쿼리 메서드 이름 대신 쿼리를 직접 쓰기]] · [[025_JPQL — 쿼리 메서드의 한계를 해결하기 위한 쿼리 언어 참고자료]] · [[079_Spring Data JPA 리포지토리와 엔티티 매핑 — 쿼리 메서드, 연관관계, 복합키]] · [[024_Spring Data JPA 쿼리 메서드 — 이름 규칙과 연산자 키워드 참고자료]]

# JPQL의 한계와 동적 쿼리 구현 방식

## 1. JPQL의 한계

JPQL은 엔티티 객체 모델을 기반으로 정밀한 쿼리를 작성할 수 있게 해 주지만, 기본적으로 **문자열 형태의 정적 쿼리(Static Query)**라는 근본적인 한계가 있다.

- **문자열 기반의 정적 쿼리**: `@Query` 어노테이션에 작성하는 JPQL은 코드를 작성하는 시점에 완전히 결정된다. 실행 시점에 조건에 따라 쿼리 구조를 바꾸기 어렵다.
- **동적 조건 조합의 어려움**: 검색 조건이 입력되었는지에 따라 WHERE 절의 조건식을 넣거나 빼는 로직(`if`)을 문자열 어노테이션 안에서 표현할 수 없다.
- **문자열 연결 시 생기는 문제**:
  - **가독성·유지보수성 저하**: 조건문(`if`)으로 JPQL 문자열을 이어 붙이면 공백 누락, 오타, 구문 오류가 생기기 쉽다.
  - **컴파일 타임 오류 검출 불가**: 오타나 잘못된 엔티티 필드명이 쿼리 문자열에 들어가도 컴파일 시점에 잡지 못하고, 그 메서드가 호출되는 **런타임**에 예외가 발생한다.
  - **SQL 인젝션 위험**: 파라미터 바인딩이 아니라 문자열 더하기(`+`)로 조건 값을 직접 조립하면 SQL 인젝션 공격에 노출될 위험이 커진다.

> **추가 설명 — 정적 쿼리와 동적 쿼리**:
>
> | | 정적 쿼리 | 동적 쿼리 |
> |---|---|---|
> | 쿼리 모양 | 항상 똑같다. **값만** 바뀐다 | 실행할 때마다 **조건 자체가** 붙었다 빠졌다 한다 |
> | 예 | "카테고리가 ○○인 메뉴" | "검색어가 있으면 검색어로, 카테고리를 골랐으면 카테고리로, 둘 다 없으면 전체" |
> | 만드는 방법 | 쿼리 메서드, `@Query` | 실행 중에 쿼리를 **조립**해야 한다 |
>
> ```java
> // 정적 쿼리 — :categoryName 자리의 값만 바뀌고, WHERE 절의 모양은 항상 같다
> @Query("SELECT m FROM Menu m WHERE m.category.name = :categoryName")
> List<Menu> findByCategoryName(@Param("categoryName") String categoryName);
> ```
>
> 어노테이션 안의 문자열은 상수라서, 그 안에 "`categoryName`이 `null`이면 이 줄은 빼라" 같은 `if` 로직을 넣을 수 없다. 이것이 정적 쿼리의 한계다.

> **추가 설명 — 문자열 더하기가 왜 인젝션에 위험한가**: 사용자 입력을 쿼리 문자열에 그대로 붙인다고 해 보자.
>
> ```java
> String jpql = "SELECT m FROM Menu m WHERE m.name = '" + keyword + "'";
> ```
>
> 사용자가 검색창에 `x' OR '1'='1`을 입력하면 쿼리는 `... WHERE m.name = 'x' OR '1'='1'`이 되어, 조건이 항상 참이 되고 **모든 데이터가 조회**된다. 사용자 입력이 "값"이 아니라 "쿼리의 일부"로 해석되어 버리는 것이다. 파라미터 바인딩(`:keyword` + `setParameter`)을 쓰면 입력값은 끝까지 **값**으로만 취급되어 이런 일이 생기지 않는다.

> 원문 바로잡기 — 원문은 `@Query`의 JPQL이 "빌드 타임이나 메서드 정의 시점에 결정"되고 오류는 "메서드가 호출되는 런타임"에 난다고 했다. 정확히 나누면 이렇다.
>
> | | 쿼리가 정해지는 때 | 문법·필드명 오류를 발견하는 때 |
> |---|---|---|
> | `@Query`의 정적 JPQL | 코드를 작성할 때 | **애플리케이션 시작 시점** — Spring Data JPA가 부팅하면서 미리 파싱해 보고, 틀리면 실행 자체가 실패한다 |
> | 문자열로 조립한 동적 JPQL | 실행 중 조건에 따라 | **그 메서드가 호출될 때** — 조립이 끝나야 비로소 문법 검사를 할 수 있다 |
>
> 둘 다 컴파일 시점에는 오류를 못 잡는다는 점은 같다. 다만 정적 JPQL은 적어도 부팅 시점에는 걸러지는 반면, 동적 JPQL은 **그 조건 조합이 실제로 실행되기 전까지** 오류가 숨어 있을 수 있다.

> **추가 설명 — 정적 JPQL로 흉내 내는 방법**: 선택 조건 몇 개 정도는 `@Query` 안에서도 `(:keyword IS NULL OR m.name LIKE :keyword)`처럼 "값이 없으면 이 조건은 참"이 되게 쓰는 방식으로 흉내 낼 수 있다. 하지만 조건마다 이런 식이 붙어 쿼리가 읽기 어려워지고, DB가 인덱스를 제대로 쓰지 못하는 경우가 많다. PostgreSQL에서는 `null` 파라미터의 타입을 추론하지 못해 `could not determine data type of parameter` 오류가 나기도 한다. 그래서 조건이 많아지면 결국 아래처럼 쿼리를 조립하는 방식으로 넘어간다.

## 2. 동적 쿼리가 필요한 경우

실무 애플리케이션의 검색 기능에서는 사용자 입력에 따라 조회 조건이 바뀌는 **동적 쿼리(Dynamic Query)**가 필수다.

가장 대표적인 예는 쇼핑몰이나 음식 주문 서비스의 **복합 검색 필터**다.

**상품 검색 필터 시나리오**:

- 검색어(메뉴명) 입력 여부 (선택)
- 카테고리 선택 여부 (선택)
- 최소/최대 가격 범위 지정 여부 (선택)
- 재고 유무 필터 체크 여부 (선택)

사용자가 검색 조건을 하나도 입력하지 않으면 모든 상품을 조회해야 하고, '카테고리'와 '최대 가격'만 입력했다면 그 두 조건만 WHERE 절에 들어가야 한다.

```sql
-- 조건 1: 전체 조회
SELECT m FROM Menu m

-- 조건 2: 카테고리와 최대 가격만 입력된 경우
SELECT m FROM Menu m WHERE m.category.name = :categoryName AND m.price <= :maxPrice

-- 조건 3: 모든 조건이 입력된 경우
SELECT m FROM Menu m WHERE m.name LIKE :keyword AND m.category.name = :categoryName AND m.price <= :maxPrice
```

입력 조건의 조합 수가 늘어날수록, 정적 JPQL 메서드를 조합마다 따로 작성하는 방식은 불가능에 가까워진다.

> **추가 설명 — 조합이 얼마나 늘어나나**: 선택 조건이 n개면 "넣는다/뺀다"의 조합은 2ⁿ가지다. 위 시나리오의 조건 4개(최소·최대 가격을 따로 치면 5개)만으로도 16~32개의 메서드가 필요하다. 조건 하나가 추가될 때마다 메서드 수가 두 배가 된다.

## 3. JPQL로 동적 쿼리 구현

JPQL로 동적 쿼리를 구현하려면 **문자열을 동적으로 조립**하고, 그 쿼리를 **직접 실행할 주체**가 필요하다.

### 3-1. EntityManager와 StringBuilder를 이용한 동적 쿼리 조립

`StringBuilder`로 조건 유무에 따라 JPQL 문자열을 조립하고, `EntityManager`로 파라미터를 바인딩해 쿼리를 실행한다.

```java
public List<Menu> findAll(String keyword, String categoryName, Integer maxPrice) {
    StringBuilder jpql = new StringBuilder("SELECT m FROM Menu m WHERE 1=1");
    Map<String, Object> params = new HashMap<>();

    if (keyword != null && !keyword.isBlank()) {
        jpql.append(" AND m.name LIKE :keyword");
        params.put("keyword", "%" + keyword + "%");
    }

    if (categoryName != null && !categoryName.isBlank()) {
        jpql.append(" AND m.category.name = :categoryName");
        params.put("categoryName", categoryName);
    }

    if (maxPrice != null) {
        jpql.append(" AND m.price <= :maxPrice");
        params.put("maxPrice", maxPrice);
    }

    TypedQuery<Menu> query = em.createQuery(jpql.toString(), Menu.class);
    for (String key : params.keySet()) {
        query.setParameter(key, params.get(key));
    }

    return query.getResultList();
}
```

- `WHERE 1=1`을 두어, 뒤에 붙는 조건들이 모두 똑같이 `AND`로 시작할 수 있게 한다. `1=1`은 항상 참이라 결과에 영향을 주지 않는다.
- 조건에 맞을 때만 JPQL 구문을 이어 붙이고, 바인딩할 파라미터를 `Map`에 모아 두었다가 한꺼번에 설정한다.

> **추가 설명 — 코드 한 줄씩 읽기**:
>
> | 코드 | 하는 일 |
> |---|---|
> | `new StringBuilder("SELECT m FROM Menu m WHERE 1=1")` | 쿼리의 뼈대를 만든다. `String`을 `+=`로 이어 붙이면 붙일 때마다 새 문자열 객체가 생기지만, `StringBuilder`는 하나의 버퍼에 계속 덧붙이므로 조립용으로 알맞다 |
> | `Map<String, Object> params` | "어떤 이름의 파라미터에 어떤 값을 넣을지"를 모아 두는 상자다. 조건이 붙을 때만 값이 들어간다 |
> | `keyword != null && !keyword.isBlank()` | 값이 아예 없거나(`null`) 공백뿐인 문자열(`""`, `"  "`)이면 "입력하지 않은 것"으로 보고 조건을 붙이지 않는다 |
> | `"%" + keyword + "%"` | `LIKE`의 와일드카드다. `%`는 "아무 글자나 0개 이상"이라는 뜻이라, `%아메%`는 "아메"가 **어디든 들어간** 이름을 찾는다. 여기서 `+`는 쿼리가 아니라 **바인딩할 값**을 만드는 것이라 인젝션과 상관없다 |
> | `em.createQuery(jpql.toString(), Menu.class)` | 다 조립한 문자열로 쿼리 객체를 만든다. 두 번째 인자로 결과 타입을 알려 주면 `TypedQuery<Menu>`가 되어, 결과를 형변환 없이 `List<Menu>`로 받을 수 있다 |
> | `query.setParameter(key, value)` | `:keyword` 같은 자리에 실제 값을 채운다 |
> | `query.getResultList()` | 이때 비로소 SQL로 바뀌어 DB에 실행되고, 결과가 엔티티 목록으로 돌아온다 |
>
> 여기서 `em`(`EntityManager`)은 JPA에서 엔티티를 저장·조회하는 핵심 객체다. 이 메서드만 봐서는 어디서 왔는지 보이지 않는데, 3-2의 `MenuRepositoryImpl`처럼 **생성자로 주입**받아 쓴다. Spring Data JPA의 `save()`, `findById()`도 내부에서는 이 `EntityManager`를 부른다.

> **추가 설명 — 입력에 따라 만들어지는 쿼리**: 같은 메서드라도 입력값에 따라 최종 문자열이 달라진다.
>
> | 호출 | 조립된 JPQL | 바인딩되는 값 |
> |---|---|---|
> | `findAll(null, null, null)` | `SELECT m FROM Menu m WHERE 1=1` | 없음 → 전체 조회 |
> | `findAll(null, "커피", 5000)` | `... WHERE 1=1 AND m.category.name = :categoryName AND m.price <= :maxPrice` | `커피`, `5000` |
> | `findAll("아메", "커피", 5000)` | `... WHERE 1=1 AND m.name LIKE :keyword AND m.category.name = :categoryName AND m.price <= :maxPrice` | `%아메%`, `커피`, `5000` |
>
> 2절에서 조합마다 따로 만들어야 했던 쿼리들을 **메서드 하나**가 모두 만들어 낸다. 이것이 동적 쿼리다.

> **추가 설명 — 문자열을 이어 붙이는데 왜 인젝션이 안전한가**: 이 코드가 이어 붙이는 것은 `" AND m.name LIKE :keyword"`처럼 **개발자가 정한 고정 문자열**뿐이다. 사용자가 입력한 값(`keyword`)은 쿼리 문자열에 들어가지 않고 `setParameter()`로 **따로 바인딩**된다. 그래서 1절에서 말한 인젝션 위험이 생기지 않는다. 반대로 `" AND m.name LIKE '%" + keyword + "%'"`처럼 값을 문자열에 직접 넣으면 위험해진다.

### 3-2. Repository 구조 확장 (Custom Repository 구현)

Spring Data JPA 인터페이스(`JpaRepository`)의 추상 메서드와 `@Query` 어노테이션은 **정적 쿼리만** 지원한다. 그래서 `StringBuilder`와 `EntityManager`를 쓰는 로직을 직접 작성하려면 **사용자 정의 리포지토리(Custom Repository)** 패턴을 적용해야 한다.

> **추가 설명 — 왜 MenuRepository에 바로 못 넣나**: `MenuRepository`는 **인터페이스**라서 메서드 몸통(`{ ... }`)을 쓸 수 없다. 인터페이스에 선언만 해 두면 Spring Data JPA가 대신 구현해 주는데, 그 방법은 두 가지뿐이다. 메서드 이름을 분석하거나(쿼리 메서드), `@Query`에 적힌 고정 문자열을 쓰는 것이다. 3-1처럼 `if`로 문자열을 조립하는 코드는 이 두 방식 어디에도 들어갈 수 없다. 그래서 **몸통을 직접 쓸 수 있는 클래스**를 하나 만들고, 그 클래스를 `MenuRepository`에 연결하는 방법이 필요하다. 그 연결 방법이 Custom Repository 패턴이다.

```
       +-----------------------+      +---------------------------+
       | JpaRepository<T, ID>  |      |   CustomMenuRepository    |
       +-----------------------+      +---------------------------+
                   ^                                ^
                   |                                |
                   +---------------++---------------+
                                   | (extends)
                      +--------------------------+
                      |      MenuRepository      |
                      +--------------------------+
                                   :
                                   : (implements)
                      +--------------------------+
                      |    MenuRepositoryImpl    |
                      +--------------------------+
```

(그림) Custom 리포지토리의 상속 관계

> 그림의 점선(`implements`)은 `MenuRepositoryImpl`이 `MenuRepository`를 구현한다는 뜻이 아니다. 아래 3)에서 보듯 `MenuRepositoryImpl`은 **`CustomMenuRepository`만** 구현한다. 점선은 "Spring Data JPA가 `MenuRepository`의 커스텀 메서드 호출을 이 클래스로 연결해 준다"는 관계로 읽으면 된다.

**1) 기본 JpaRepository와 사용자 정의 인터페이스 결합**

가장 먼저 통합 인터페이스인 `MenuRepository`를 정의한다. 기존 `MenuRepository`가 `JpaRepository`와, 직접 작성할 `CustomMenuRepository`를 **동시에 상속**하도록 설정한다.

자바 구조상 `MenuRepository`를 직접 구현하는 클래스를 만들지 않는 것은 정상이다. Spring Data JPA가 애플리케이션 실행 시점에 `MenuRepository`의 **프록시 구현체를 동적으로 생성**하기 때문이다. 이 프록시 객체는 `JpaRepository`의 기본 CRUD 메서드 호출은 내장 로직으로 처리하고, `CustomMenuRepository`에 정의된 커스텀 메서드 호출은 뒤에 나올 `MenuRepositoryImpl` 구현체로 **위임**한다.

이렇게 하면 서비스 계층은 `MenuRepository` 하나만 주입받아 기본 CRUD 메서드와 동적 쿼리 메서드를 모두 쓸 수 있다.

```java
public interface MenuRepository extends JpaRepository<Menu, Long>, CustomMenuRepository {
    // 기본 JpaRepository 기능 및 정적 @Query 사용 가능
}
```

```
[서비스] → MenuRepository (프록시 하나)
              ├─ save(), findById() 등   → Spring Data JPA 내장 구현 (SimpleJpaRepository)
              └─ findAll(keyword, ...)   → MenuRepositoryImpl (직접 작성한 구현)
```

> **추가 설명 — MenuRepository의 구현체는 누가 만드나**: 스프링 중에서도 **Spring Data JPA**가 애플리케이션이 시작될 때 만든다.
>
> ```
> 애플리케이션 시작
>  1. JpaRepository를 상속한 인터페이스를 찾는다          → MenuRepository 발견
>  2. 이름 규칙에 맞는 커스텀 구현 클래스를 찾는다        → MenuRepositoryImpl 발견
>  3. MenuRepository 타입의 프록시 객체를 만든다
>  4. 그 프록시를 IoC 컨테이너에 빈으로 등록한다           → 서비스에 주입된다
> ```
>
> 이 프록시는 호출된 메서드에 따라 처리할 곳을 나눈다.
>
> | 호출된 메서드 | 처리하는 곳 |
> |---|---|
> | `save`, `findById`, `count` 같은 기본 CRUD | `SimpleJpaRepository` (Spring Data JPA에 들어 있는 클래스) |
> | 직접 만든 `findAll(keyword, ...)` | `MenuRepositoryImpl` |
> | `findByName` 같은 쿼리 메서드 | 시작할 때 메서드 이름을 분석해 미리 만들어 둔 쿼리 |
> | `@Query` 메서드 | 적어 둔 JPQL |
>
> `MenuRepository`가 인터페이스이므로 이 프록시는 **JDK 동적 프록시**(`Proxy.newProxyInstance`)로 만들어진다. AOP에서 `InvocationHandler`가 호출을 가로채 대상 객체로 넘겨주던 것과 같은 원리다. 서비스에서 `System.out.println(menuRepository.getClass())`를 찍어 보면 `jdk.proxy2.$Proxy123`처럼 **우리가 만든 적 없는 클래스 이름**이 나온다.

> **추가 설명 — 서비스에서는 이렇게 쓴다**: 서비스는 `MenuRepositoryImpl`이 아니라 **`MenuRepository`를 주입받는다.** 어떤 메서드가 어디서 처리되는지는 몰라도 된다.
>
> ```java
> @Service
> public class MenuService {
>
>     private final MenuRepository menuRepository;   // Impl이 아니라 MenuRepository
>
>     public MenuService(MenuRepository menuRepository) {
>         this.menuRepository = menuRepository;
>     }
>
>     public void example() {
>         menuRepository.save(new Menu("아메리카노", 4500));   // JpaRepository의 CRUD
>         menuRepository.findById(1L);                         // JpaRepository의 CRUD
>         menuRepository.findAll("아메", "커피", 5000);        // 직접 만든 동적 쿼리
>     }
> }
> ```

**2) 사용자 정의 인터페이스 작성**

`JpaRepository`가 제공하지 않는 커스텀 조회 메서드를 정의하기 위해 별도의 인터페이스를 작성한다. `CustomMenuRepository`처럼 접두어(`Custom`)나 접미어를 붙여, 기본 리포지토리 기능을 **확장하는 역할**임을 분명히 드러낸다.

`CustomMenuRepository`는 Spring Data JPA의 `Repository` 인터페이스를 상속하지 않는 **순수 자바 인터페이스**로 작성한다.

```java
public interface CustomMenuRepository {
    List<Menu> findAll(String keyword, String categoryName, Integer maxPrice);
}
```

> **추가 설명 — 왜 순수 자바 인터페이스여야 하나**: `CustomMenuRepository`가 `Repository`나 `JpaRepository`를 상속하면, Spring Data JPA는 이것도 **리포지토리 인터페이스**로 보고 따로 프록시를 만들려고 한다. 그러면 `findAll(keyword, categoryName, maxPrice)`를 쿼리 메서드 이름으로 분석하려다 실패한다. `CustomMenuRepository`는 리포지토리가 아니라 **"이 메서드는 내가 직접 구현하겠다"는 목록**일 뿐이라서, 아무것도 상속하지 않는 평범한 인터페이스로 둔다.

> **추가 설명 — 메서드 이름**: `findAll`은 `JpaRepository`에도 같은 이름의 메서드(`findAll()`, `findAll(Sort)` 등)가 있어서, 매개변수만 다른 **오버로딩**이 된다. 동작은 하지만 "전체 조회"와 "조건 검색"이 같은 이름이라 읽을 때 헷갈린다. 실무에서는 `search(...)`, `findByCondition(...)`처럼 조건 검색임이 드러나는 이름을 많이 쓴다.

**3) 사용자 정의 인터페이스 구현체 작성**

구현 클래스는 `CustomMenuRepository`만 구현(`implements`)하면 된다. Spring Data JPA는 이름이 정해진 규칙에 맞는 구현체를 **자동으로 찾아** 연결한다. 그래서 구현 클래스가 `JpaRepository`나 다른 Spring 인터페이스를 직접 상속하지 않아도, Spring Data JPA가 프록시 객체를 통해 기본 CRUD 기능과 커스텀 구현체의 메서드를 **하나의 리포지토리 빈**으로 합쳐 제공한다.

구현 클래스 이름은 기존 Repository 인터페이스 이름인 `MenuRepository` 뒤에 `Impl`을 붙인다. `EntityManager`를 주입받아 동적 쿼리 로직을 구현한다.

```java
@Repository
public class MenuRepositoryImpl implements CustomMenuRepository {

    private final EntityManager em;

    public MenuRepositoryImpl(EntityManager em) {
        this.em = em;
    }

    @Override
    public List<Menu> findAll(String keyword, String categoryName, Integer maxPrice) {
        StringBuilder jpql = new StringBuilder("SELECT m FROM Menu m WHERE 1=1");
        Map<String, Object> params = new HashMap<>();

        if (keyword != null && !keyword.isBlank()) {
            jpql.append(" AND m.name LIKE :keyword");
            params.put("keyword", "%" + keyword + "%");
        }

        if (categoryName != null && !categoryName.isBlank()) {
            jpql.append(" AND m.category.name = :categoryName");
            params.put("categoryName", categoryName);
        }

        if (maxPrice != null) {
            jpql.append(" AND m.price <= :maxPrice");
            params.put("maxPrice", maxPrice);
        }

        TypedQuery<Menu> query = em.createQuery(jpql.toString(), Menu.class);
        for (Map.Entry<String, Object> entry : params.entrySet()) {
            query.setParameter(entry.getKey(), entry.getValue());
        }

        return query.getResultList();
    }
}
```

> **추가 설명 — MenuRepository가 아니라 CustomMenuRepository를 implements 하는 이유**: `MenuRepository`는 `JpaRepository`까지 상속하고 있다. 그래서 `MenuRepository`를 `implements` 하면 자바 규칙상 `save`, `findById`, `deleteById`, `count` 같은 `JpaRepository`의 메서드 **수십 개를 전부** 직접 구현해야 한다. 구현하지 않으면 컴파일 오류가 난다.
>
> ```java
> public class MenuRepositoryImpl implements MenuRepository {        // ❌
>     public List<Menu> findAll(String keyword, ...) { ... }          // 만들고 싶은 건 이것 하나인데
>     public <S extends Menu> S save(S entity) { ... }                // 이것도
>     public Optional<Menu> findById(Long id) { ... }                 // 이것도 ... 전부 만들어야 한다
> }
> ```
>
> 기본 CRUD는 이미 `SimpleJpaRepository`가 가지고 있다. 그래서 구현 클래스는 **비어 있는 조각**인 `CustomMenuRepository`만 채우고, 나머지는 Spring Data JPA가 만든 프록시가 합쳐 준다. 이런 커스텀 인터페이스를 공식 문서에서는 **조각(fragment) 인터페이스**라고 부른다.
>
> ```
> MenuRepository  (완성품 — 구현은 Spring Data JPA가 프록시로 만든다)
>  ├─ JpaRepository 조각        → SimpleJpaRepository (이미 있음)
>  └─ CustomMenuRepository 조각 → MenuRepositoryImpl  (내가 채움)
> ```
>
> 인터페이스를 `implements` 해 두면 좋은 점이 하나 더 있다. 메서드 이름이나 매개변수를 잘못 쓰면 `@Override`에서 **컴파일 오류**가 나서, 인터페이스와 구현이 어긋나는 실수를 바로 잡을 수 있다.

> **추가 설명 — 구현 클래스 안에서 CRUD가 필요하면**: `MenuRepositoryImpl` 안에서 저장이나 단건 조회가 필요하면, `MenuRepository`를 다시 주입받지 말고 이미 가진 **`EntityManager`**를 쓴다.
>
> | JpaRepository | EntityManager |
> |---|---|
> | `findById(id)` | `em.find(Menu.class, id)` |
> | `save(새 엔티티)` | `em.persist(entity)` |
> | `delete(entity)` | `em.remove(entity)` |
>
> `MenuRepository`는 `MenuRepositoryImpl`을 조각으로 품고 만들어진다. 그런데 `MenuRepositoryImpl`이 다시 `MenuRepository`를 달라고 하면, 서로가 먼저 만들어지기를 기다리는 **순환 참조**가 된다.

> **추가 설명 — 이 패턴을 쓰지 않는 방법도 있다**: 동적 쿼리용 클래스를 `JpaRepository`와 아무 관계 없는 **별도 리포지토리**로 만들어도 된다.
>
> ```java
> @Repository
> public class MenuQueryRepository {            // 일반 클래스. 이름 규칙도 없다
>     private final EntityManager em;
>     public List<Menu> search(String keyword, String categoryName, Integer maxPrice) { ... }
> }
> ```
>
> | | Custom Repository 패턴 (이 자료) | 별도 클래스로 분리 |
> |---|---|---|
> | 서비스가 주입받는 것 | `MenuRepository` 하나 | `MenuRepository` + `MenuQueryRepository` 두 개 |
> | 필요한 파일 | 인터페이스 2개 + 구현 클래스 1개 | 클래스 1개 |
> | 이름 규칙(`Impl`) | 지켜야 한다 | 없다 |
> | 장점 | 서비스 입장에서 리포지토리가 하나라 깔끔하다 | 구조가 단순하고, 복잡한 조회 코드가 한곳에 모인다 |
>
> 실무에서는 둘 다 쓴다. 이 자료는 "`MenuRepository` 하나로 CRUD와 동적 쿼리를 모두 쓰게 하는 방법"을 소개한 것이다.

> **추가 설명 — 구현 클래스 이름 규칙은 두 가지다**:
>
> | 이름 | 기준 | 비고 |
> |---|---|---|
> | `MenuRepositoryImpl` | **통합 리포지토리** 인터페이스 이름 + `Impl` | 원문의 방식. 예전부터 쓰던 규칙으로 지금도 동작한다 |
> | `CustomMenuRepositoryImpl` | **사용자 정의(조각) 인터페이스** 이름 + `Impl` | Spring Data 공식 문서가 권장하는 최신 방식. 커스텀 인터페이스를 여러 개 붙일 때도 각각 따로 구현할 수 있다 |
>
> 어느 쪽이든 이름의 `Impl`이 빠지거나 철자가 다르면 Spring Data JPA가 구현체를 찾지 못하고, `findAll(keyword, ...)`을 **쿼리 메서드 이름으로 해석하려다** 애플리케이션 시작 시 오류가 난다. 또 `@Repository`는 없어도 이름 규칙만으로 찾아지지만, 붙여 두면 "이 클래스는 리포지토리 계층"이라는 표시가 되고 DB 예외를 스프링 예외로 바꿔 주는 처리도 적용된다.

> **추가 설명 — `m.category.name`은 조인이다**: JPQL에서 `m.category.name`처럼 연관 엔티티의 필드에 점(`.`)으로 접근하면, Hibernate가 SQL로 바꿀 때 `menu`와 `category` 테이블을 **내부 조인**한다(묵시적 조인). 이 예제에서는 카테고리 조건이 있을 때만 이 구문이 붙으므로 문제가 없지만, 묵시적 조인이 여러 곳에 숨어 있으면 어떤 조인이 일어나는지 알아보기 어려워진다. 그래서 명시적으로 `JOIN m.category c`라고 쓰는 것을 선호하는 경우가 많다.

## 4. 이 방식의 한계와 향후 과제

`StringBuilder`와 `EntityManager`를 조합해 JPQL로 동적 쿼리를 작성할 수는 있지만, 실무에서 큰 로직에 적용하기에는 문제가 많다.

- **문자열 조립 시 오타 위험**: 공백 하나가 빠지거나(`AND` 앞뒤 공백 등) 엔티티 필드명을 잘못 적어도 컴파일 시점에 검증할 수 없다.
- **복잡도 증가**: 조건이 많아질수록 `StringBuilder.append()` 코드가 비대해지고, `WHERE 1=1` 같은 임의 구문과 파라미터 매핑 코드가 반복되어 가독성이 급격히 떨어진다.
- **유지보수성 저하**: 엔티티 필드명이 바뀌면 JPQL 문자열 안의 필드명을 일일이 찾아 고쳐야 한다. IDE의 이름 바꾸기(리팩터링) 기능도 문자열 안까지는 따라가지 않는다.

> **추가 설명 — 공백 하나로 생기는 오류**: 조건 문자열 앞의 공백을 하나 빠뜨렸다고 하자.
>
> ```java
> jpql.append("AND m.price <= :maxPrice");     // 앞에 공백이 없다
> // 결과: SELECT m FROM Menu m WHERE 1=1AND m.price <= :maxPrice
> ```
>
> `1=1AND`가 붙어 버려 문법 오류가 난다. 그런데 이 줄은 `maxPrice`가 입력된 경우에만 실행되므로, 가격 조건 없이 테스트하면 **오류가 드러나지 않는다.** 나중에 사용자가 가격을 넣는 순간 처음으로 터진다. 1절에서 말한 "그 조건 조합이 실행되기 전까지 오류가 숨어 있다"가 바로 이런 경우다.

이런 문자열 기반 동적 쿼리의 한계를 넘으려면, 자바 코드로 쿼리를 안전하게 조립할 수 있는 **타입 안전(Type-safe) 쿼리 빌더** 도구가 필요하다.

> **추가 설명 — 타입 안전 쿼리 빌더의 후보**:
>
> | 도구 | 정체 | 특징 |
> |---|---|---|
> | **Criteria API** | JPA 표준 | 쿼리를 자바 코드(API 호출)로 조립한다. 컴파일 시점에 오류를 잡을 수 있지만 코드가 길고 읽기 어려워 잘 쓰지 않는다 |
> | **Specification** | Spring Data JPA | Criteria API를 조건 단위로 쪼개 조합하기 쉽게 감싼 것이다 |
> | **Querydsl** | 오픈소스 | 엔티티를 바탕으로 `QMenu` 같은 클래스를 자동 생성하고, `menu.name.contains(keyword)`처럼 SQL에 가까운 자바 코드로 쿼리를 쓴다. 조건이 `null`이면 그 조건을 자동으로 빼 주어 동적 쿼리에 특히 강하다 |
>
> 이 중 실무에서 동적 쿼리에 가장 많이 쓰는 것은 **Querydsl**이다. 위의 `StringBuilder` 코드를 Querydsl로 바꾸면 `WHERE 1=1`도, 파라미터 `Map`도, 공백 실수도 사라진다.
