---
tags: [데이터베이스, JPA, SpringDataJPA, 엔티티, 연관관계, 쿼리메서드]
---

> 🔗 관련 노트: [[078_ORM과 JPA — 개념부터 API 설계 관점까지]] · [[041_JOIN — INNER·OUTER와 주인공 개념]] · [[069_데이터베이스 정규화 — 1차부터 4차까지]]

# Spring Data JPA 리포지토리와 엔티티 매핑 — 쿼리 메서드, 연관관계, 복합키

`MenuRepository`를 인터페이스로만 선언했는데도 컨트롤러에서 데이터가 조회되는 이유부터 시작해서, 쿼리 메서드, 엔티티 매핑 어노테이션, 테이블 간 연관관계, 복합키, 그리고 쿼리 메서드로 감당이 안 되는 복잡한 조회까지 정리한다.

## 0. 먼저 정의부터 — JPA와 ORM을 한 문장으로

면접에서 "JPA가 뭐예요?", "ORM이 뭐예요?"라고 물었을 때 바로 나와야 하는 문장이다.

- **ORM**: 엔티티 객체 정보를 이용해 SQL을 만들어주는 기술. 핵심은 "개발자는 엔티티만 바라보고, DB는 ORM이 알아서 관리한다"는 것이다. 엔티티를 바꾸면 DB가 바뀌고, 엔티티를 다루면 SQL이 만들어진다. 마이크로소프트가 같은 개념의 자기 도구를 "Entity Framework"라고 이름 붙인 것도 그래서다.
- **JPA**: ORM 프레임워크를 사용하기 위한 **자바 표준 인터페이스**. 구현체가 아니라 규격이다. 실제 구현은 Hibernate 같은 ORM 프레임워크가 한다.
- **Spring Data JPA**: JPA 위에 스프링이 얹은 계층으로, 리포지토리 인터페이스만 선언하면 구현체를 자동으로 만들어준다. 흔히 "스프링 JPA"라고 뭉뚱그려 부르지만, JPA 자체는 스프링이 아니라 자바(Jakarta EE) 표준이고, 스프링이 만든 것은 Spring Data JPA다.

"매핑"이라는 단어 자체가 핵심은 아니다. "연결해주는 기술"처럼 말하면 커넥션 도구로 오해받는다. **"엔티티로 SQL을 만들어주는 기술"**이라고 말하는 것이 정확하다.

## 1. 구현한 적 없는 리포지토리는 누가 만들었나

```java
public interface MenuRepository extends JpaRepository<Menu, Long> {
}
```

`MenuRepository`를 구현하는 클래스(`implements MenuRepository`)는 한 번도 만들지 않았다. 그런데 컨트롤러에 주입해서 쓰면 데이터가 나온다. 이게 가능한 이유는 **IoC 컨테이너** 때문이다.

**IoC 컨테이너란**: IoC(Inversion of Control, 제어의 역전)는 원래 내가 해야 할 일(객체를 생성하고 조립하는 일)을 다른 쪽에 위탁하는 방식이다. IoC 컨테이너는 그 **객체 생성·조립을 대신 맡아주는 컨테이너**다. 단순히 객체를 만들어주는 데서 끝나지 않고, 만든 객체를 **담아두는 곳**이라는 점이 중요하다. 컨트롤러·서비스·리포지토리 같은 여러 계층의 객체가 모두 여기 담겨 있고, 필요한 쪽은 직접 `new`로 만들지 않고 여기서 **가져다 쓴다**. 그래서 IoC 컨테이너는 일종의 공유창고라고 볼 수 있다.

**누가 리포지토리를 구현했나**: 역할을 나누면 이렇다.

| 역할 | 담당 |
|---|---|
| 리포지토리 인터페이스와 기본 메서드 목록 **정의** | Spring Data JPA (`JpaRepository`, `CrudRepository` 등) |
| 인터페이스를 보고 **구현체(프록시) 생성 후 IoC 컨테이너에 등록** | Spring Data JPA |
| 그 구현체 안에서 실제로 **SQL을 만들고 실행** | Hibernate의 `EntityManager` |

> 강의에서는 "Hibernate의 엔티티 매니저가 구현체를 만들어 IoC 컨테이너에 담는다"고 설명했다. 정확히는 **구현체(프록시)를 만들어 빈으로 등록하는 것은 Spring Data JPA**이고, 그 구현체가 내부에서 Hibernate의 `EntityManager`를 사용해 SQL을 실행하는 구조다. 또 리포지토리 빈은 누가 주입받을 때 그때그때 만들어지는 게 아니라, 기본적으로 **애플리케이션이 시작될 때** 미리 만들어져 컨테이너에 등록된다.

**언제, 어떻게 만들어지나**: 애플리케이션이 시작되어 스프링 컨테이너가 초기화될 때, Spring Data JPA는 `Repository`를 상속한 인터페이스들을 찾아낸다. 그리고 인터페이스마다 **JDK 동적 프록시(Dynamic Proxy)**를 만들어 빈으로 등록한다. 동적 프록시는 클래스 파일 없이 **실행 중에 인터페이스만 보고 만들어지는 구현 객체**다. 이 프록시에 메서드 호출이 들어오면 이렇게 나눠 처리한다.

- `save`, `findById` 같은 **기본 메서드** → Spring Data JPA가 미리 만들어둔 기본 구현 클래스(`SimpleJpaRepository`)에 넘긴다.
- 내가 추가한 **쿼리 메서드** → 시작할 때 메서드 이름을 분석해서 만들어둔 쿼리를 실행한다.

그래서 `@Autowired`나 생성자 주입으로 받는 시점에는 이미 구현체가 컨테이너 안에 준비되어 있고, 우리는 가져다 쓰기만 하면 된다.

> 강의 자료에는 "`@Repository` 어노테이션이 붙은 인터페이스가 등록되면서 발견된다"고 되어 있지만, Spring Data JPA 리포지토리 인터페이스에는 `@Repository`를 **붙이지 않아도 된다.** `JpaRepository`(거슬러 올라가면 `Repository`)를 상속했다는 사실만으로 스캔 대상이 된다. 붙여도 오류는 아니지만 필요는 없다.

## 2. JpaRepository가 물려받는 것들

`JpaRepository`는 혼자 있는 인터페이스가 아니라 여러 인터페이스를 상속(`extends`)한다. 인터페이스끼리는 `extends` 키워드로 여러 개를 동시에 상속할 수 있고, 상속받은 쪽은 부모들의 기능을 전부 합친 것이 된다.

```
Repository
 └─ CrudRepository            save, findById, findAll, deleteById, count, existsById ...
     └─ ListCrudRepository     (반환 타입을 List로)
 └─ PagingAndSortingRepository  findAll(Sort), findAll(Pageable)
JpaRepository  ← 위 계열 + QueryByExampleExecutor + JPA 전용 메서드(flush, saveAndFlush, deleteAllInBatch, getReferenceById ...)
```

- **CrudRepository**: 가장 많이 쓴다. 이름 그대로 CRUD다.
  - `save`: **INSERT와 UPDATE를 둘 다 한다.** 넘긴 엔티티에 id가 없으면 INSERT, id가 있으면 UPDATE. 그래서 `update` 메서드는 따로 없다.
  - `findById`: 하나 조회 / `findAll`: 목록 조회 / `deleteById`: 삭제
- **QueryByExampleExecutor**: 예시 객체를 만들어 넘기면 그와 같은 조건의 데이터가 있는지(`exists`), 그 조건에 맞는 목록(`findAll`)을 찾는 기능.
- **JPA 전용 메서드**: `flush`, `getReferenceById`(id로 참조만 얻기) 등. 잘 쓰지 않는다.

> 강의에서는 `JpaRepository`가 `JpaSpecificationExecutor`를 상속한다고 설명했지만, `JpaSpecificationExecutor`는 기본 상속 목록에 없다. 동적 조건 검색(Specification)이 필요할 때 리포지토리에 **직접 추가로 상속**시키는 인터페이스다. 조건에 맞는 데이터 존재 여부를 확인하는 기능은 `QueryByExampleExecutor`에 있다. 또 강의에 나온 `getById`는 현재 사용 중단(deprecated)되었고 `getReferenceById`로 바뀌었다.

**그러면 굳이 MenuRepository를 왜 만드나**: 기본 메서드만으로 충분하다면 `MenuRepository`를 만들지 않고 `JpaRepository<Menu, Long>`이나 그 부모 인터페이스를 그대로 가져다 써도 된다. 그런데도 인터페이스를 따로 선언하는 이유는 **기본 메서드 외에 내 기능을 추가하기 위해서**다. 스프링이 정의해둔 메서드만 구현해주는 게 아니라, 내가 인터페이스에 추가로 선언한 메서드까지 구현해준다.

## 3. 기본 메서드는 어떤 SQL이 되나

`save`, `findAll`, `findById` 같은 기본 메서드를 호출하면 Spring Data JPA는 내부에서 `EntityManager`의 JPA 표준 API를 호출하고, Hibernate가 엔티티 매핑 정보(`@Table`, `@Column` 등)를 보고 SQL을 만든다. `show-sql`을 켜두면 콘솔에서 확인할 수 있다.

```java
Menu saved = menuRepository.save(new Menu("아메리카노", "Americano", 4500));
List<Menu> all = menuRepository.findAll();
Menu found = menuRepository.findById(1L).orElseThrow();
```

| 호출 | 내부 동작 | 만들어지는 SQL |
|---|---|---|
| `save` (id 없음) | `persist` | `insert into menus (eng_name, kor_name, price) values (?, ?, ?)` |
| `save` (id 있음) | `merge` | `select ... where m1_0.id=?`로 기존 데이터를 읽고, 바뀐 값이 있으면 `update menus set ... where id=?` |
| `findAll` | 엔티티 전체 조회 | `select m1_0.id, m1_0.eng_name, m1_0.kor_name, m1_0.price from menus m1_0` |
| `findById` | 기본키로 조회 | `select m1_0.id, ... from menus m1_0 where m1_0.id=?` |

**save가 INSERT와 UPDATE를 가르는 기준**: 넘겨받은 엔티티가 새것인지 판단해서, 새것이면 `persist`(영속성 컨텍스트에 등록 → INSERT), 아니면 `merge`(기존 데이터에 합치기 → UPDATE)를 호출한다. 판단 기준은 기본적으로 id 필드다. `Long`처럼 참조 타입이면 `null`일 때, `long`처럼 기본 타입이면 `0`일 때 새 엔티티로 본다. id 필드를 `long`이 아니라 `Long`으로 선언하는 이유 중 하나다.

> **강의 자료 보충 — INSERT가 나가는 시점**: 자료에는 `persist`가 "플러시 시점에 INSERT SQL을 생성한다"고 되어 있다. 일반적으로는 맞지만 `@GeneratedValue(strategy = GenerationType.IDENTITY)`는 예외다. IDENTITY는 DB가 INSERT를 실행해야 id 값이 정해지기 때문에, Hibernate는 `persist` 하는 **즉시** INSERT를 보낸다. 그래서 `save()`가 돌려준 엔티티에는 이미 id가 채워져 있다.

> **강의 자료 보충 — 별칭 모양**: 자료에 나온 `menu0_` 같은 테이블 별칭은 Hibernate 5 형식이다. Spring Boot 3(Hibernate 6)에서는 `m1_0`처럼 찍힌다. 별칭 모양만 다르고 SQL의 의미는 같다.

이처럼 기본 메서드는 SQL을 직접 쓰지 않아도 엔티티 구조를 보고 SQL을 만든다. 그리고 이름으로 SQL을 만드는 방식은 미리 정의된 메서드에만 해당하지 않는다. 정해진 패턴만 지키면 **내가 지은 메서드 이름으로도** SQL이 만들어진다.

## 4. 쿼리 메서드 — SQL 대신 메서드 이름을 정의한다

그렇다고 아무 이름이나 선언하면 되는 건 아니고, 규칙이 있다. 메서드 이름을 분석해서 SQL을 만들기 때문이다.

`findAllByKorNameContaining(String keyword)`를 조각별로 나누면 이렇다.

| 조각 | `find` | `All` | `By` | `KorName` | `Containing` |
|---|---|---|---|---|---|
| 역할 | 동작(조회) | 여러 건 | 조건 시작 구분자 | 비교할 필드 | 비교 방식 |
| 만들어지는 SQL | `SELECT ... FROM menus` | (SQL에는 영향 없음) | `WHERE` | `kor_name` | `LIKE %?%` |

합치면 `SELECT ... FROM menus WHERE kor_name LIKE '%keyword%'`가 된다.

`All`은 "조건에 맞는 메뉴를 **전부(여러 건)** 찾는다"는 의도를 이름에 드러내는 조각이다. 다만 SQL을 바꾸지는 않고, 실제로 여러 건을 받을지 한 건을 받을지는 반환 타입(`List<Menu>` / `Optional<Menu>`)이 정한다. 그래서 `findByKorNameContaining`처럼 `All`을 빼도 반환 타입이 `List`면 똑같이 여러 건을 돌려준다.

- `find`: SELECT 문을 만든다. `findAll`이면 모든 컬럼을 테이블에서 조회한다.
- `By`: 여기서부터 WHERE 절이다.
- `By` 뒤의 이름: 비교할 **엔티티 필드명**이다. 비교 방식을 생략하면 같다(`=`)는 뜻이다.
- 조건이 여러 개면 `And`, `Or`로 잇고, 파라미터는 조건이 나오는 순서대로 넣는다.

```java
List<Menu> findByPrice(Integer price);                          // WHERE price = ?
List<Menu> findByPriceAndHit(Integer price, Integer hit);       // WHERE price = ? AND hit = ?
List<Menu> findByKorNameContaining(String keyword);             // WHERE kor_name LIKE %?%
```

이렇게 SQL을 대신해서 정의하는 메서드를 **쿼리 메서드**라고 부른다. 쿼리(SQL)를 만들기 위한 메서드라는 뜻이다. 메서드 이름에서 쿼리를 이끌어낸다고 해서 영어로는 **derived query**라고도 한다.

**자주 쓰는 키워드 조합**:

```java
Menu findFirstByPriceGreaterThan(Integer price);                   // WHERE price > ?  LIMIT 1
List<Menu> findByPriceBetween(Integer min, Integer max);           // WHERE price BETWEEN ? AND ?
List<Menu> findByPriceIn(List<Integer> prices);                    // WHERE price IN (?, ?, ...)
List<Menu> findByPriceNot(Integer price);                          // WHERE price <> ?
List<Menu> findByKorNameLike(String pattern);                      // WHERE kor_name LIKE ?  (%는 직접 붙여서 넘김)
List<Menu> findByPriceGreaterThanOrderByPriceDesc(Integer price);  // WHERE price > ? ORDER BY price DESC
long countByPrice(Integer price);                                  // SELECT COUNT(*) ... WHERE price = ?
boolean existsByKorName(String korName);                           // 있으면 true
```

> `First`/`Top`은 같은 뜻이다(`findTop10By...` == `findFirst10By...`). 숫자를 생략하면 1건이다. PostgreSQL + Hibernate 6에서는 콘솔에 `LIMIT` 대신 `fetch first ? rows only`로 찍힐 수 있는데, 같은 의미의 표준 SQL 문법이다.

**메서드 이름의 전체 모양**: 이름은 "무엇을 할지(주어)"와 "어떤 조건으로(술어)"를 `By`를 기준으로 나눠 해석한다.

```
find     First3     By   KorName Containing  And  Price LessThan   OrderBy Price Desc
└동작┘   └개수 제한┘ └구분┘ └────────── 조건(WHERE) ──────────────┘  └──── 정렬 ────┘
```

| 자리 | 들어갈 수 있는 것 |
|---|---|
| 동작 | `find`, `read`, `get`, `query`(조회) / `count`(개수) / `exists`(존재 여부) / `delete`, `remove`(삭제) |
| 수식어 (선택) | `Distinct`, `First`·`Top` + 숫자 |
| 조건 | 엔티티 필드명 + 연산자 키워드, 여러 개면 `And`·`Or`로 연결 |
| 정렬 (선택) | `OrderBy` + 필드명 + `Asc`·`Desc` |

**이름 분석은 시작할 때 한다**: 쿼리 메서드 이름은 호출할 때가 아니라 **애플리케이션이 시작되어 프록시를 만들 때** 분석된다. 그래서 필드명 오타나 규칙에 맞지 않는 이름이 있으면 서버가 뜨는 단계에서 바로 에러가 난다(`No property 'korNmae' found for type 'Menu'`). 잘못된 메서드가 숨어 있다가 실행 중에 터지는 일은 없다.

> **강의 내용 바로잡기 — find vs findAll, 그리고 부분 검색**
> - 강의에서는 "`findBy`는 하나, 여러 개는 `findAllBy`"라고 했지만, Spring Data JPA에서 `findBy`와 `findAllBy`는 **같은 뜻**이다(`All`은 무시된다). 하나를 받을지 여러 개를 받을지는 이름이 아니라 **반환 타입**(`Optional<Menu>` vs `List<Menu>`)이 결정한다.
> - "아메"로 "아메리카노"를 찾으려면 `findAllByKorName`이 아니라 `findByKorNameContaining`이어야 한다. 비교 방식을 생략한 `findByKorName`은 정확히 일치(`=`)하는 것만 찾는다.

**"SQL 안 써도 된다더니 사기 아닌가?"**: 결국 메서드 이름으로 SQL을 만드는 거라면, SQL을 그냥 쓰는 것과 뭐가 다른가 하는 의문이 들 수 있다. 하지만 기존 방식에서도 SQL을 실행하려면 어차피 **메서드를 만들어야 했다.** 거기에 구현 클래스를 만들고, JDBC 코드를 쓰고, SQL을 써야 했다. 쿼리 메서드는 **어차피 만들 메서드의 이름만 규칙에 맞추면** 구현 클래스도 SQL도 필요 없다. 충분히 가치가 있다.

**연산자 키워드를 다 외워야 하나**: 외울 필요 없다. `Containing`, `Between`, `OrderBy` 같은 키워드는 **레퍼런스**다. 머릿속에 남겨야 할 것은 "쿼리 메서드가 무엇인지"와 "연산자·정렬·개수 제한 같은 키워드가 존재한다"는 사실, 그리고 "이런 건 쿼리 메서드로 될 것이다"라는 감각이다. 필요할 때 찾아보거나 AI에게 물어보고, AI가 이상하게 만들어내면 그때 레퍼런스를 펼쳐 "그런 키워드가 없구나"를 확인하면 된다.

**이미 있는 건 정의하지 않는다**: 한 건 조회(`findById`)나 수정(`save`)을 위한 메서드를 `MenuRepository`에 다시 선언할 필요는 없다. 부모 인터페이스인 `CrudRepository`가 이미 정의하고 있기 때문이다. 우리는 거기 없는 것만 추가하면 된다.

## 5. 엔티티 매핑 어노테이션

```java
@Entity
@Table(name = "menus")
public class Menu {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "kor_name")
    private String korName;
    ...
}
```

**@Entity — 필수**: "이 클래스가 엔티티다"라고 엔티티 매니저에게 알려준다. 리포지토리를 구현하려고 엔티티 매니저가 이 클래스에 갔는데 `@Entity`가 없으면 "엔티티가 정의되지 않았다"며 실패한다.

**@Id — 필수**: 식별자(기본키)로 쓸 필드를 지정한다. 기본키이므로 중복과 NULL을 허용하지 않는 제약 조건을 갖는다.

**@Table — 선택**: 없어도 오류는 나지 않는다. 다만 클래스명 `Menu`를 기준으로 테이블 이름이 `menu`가 된다. PostgreSQL 쪽 관례는 복수형(`menus`)이므로, 엔티티 매니저가 `CREATE TABLE`을 할 때 클래스명이 아니라 내가 지정한 이름을 쓰라고 알려주는 용도다. DBMS마다 관례가 다르다는 점도 기억해둔다(오라클은 옛날 방식대로 대문자 + 언더바를 쓴다).

**@GeneratedValue — id 자동 생성**: 테이블을 직접 만들지 않지만, 모든 DBMS에는 "이 컬럼 값은 넘겨주지 마, 내가 알아서 하나씩 올릴게"라는 기능이 있다. `IDENTITY` 전략을 쓰면 PostgreSQL에서 `generated by default as identity` 컬럼이 만들어져, 기본값이 자동으로 증가하는 정수형이 된다. `Long` 필드이므로 컬럼 타입은 `bigint`가 된다.

> 자동 증가를 지원하는 방식은 DBMS마다 다르다. 오라클은 시퀀스(sequence)라는 별도 객체를 만들어서 값을 뽑아 쓴다. 그래서 `GenerationType`에는 `IDENTITY`, `SEQUENCE` 등 여러 종류가 있다. PostgreSQL은 IDENTITY 컬럼과 시퀀스를 둘 다 지원하므로 `SEQUENCE` 전략도 쓸 수 있지만, 이 프로젝트에서는 `IDENTITY`로 통일한다.

**@Column — 컬럼명이 다를 때**: 엔티티 필드명과 실제 컬럼명을 맞춰준다.

> 강의에서는 `@Column`이 없으면 컬럼이 `korname`처럼 전부 소문자로 붙어서 만들어진다고 설명했다. 이는 Hibernate만 단독으로 썼을 때의 동작이다. **Spring Boot는 기본 네이밍 전략(`CamelCaseToUnderscoresNamingStrategy`)으로 `korName`을 `kor_name`으로 자동 변환**하므로, 단순히 카멜 ↔ 스네이크 차이라면 `@Column`이 없어도 된다. `@Column`은 이름이 규칙과 전혀 다를 때나 `nullable`, `length` 같은 제약을 줄 때 쓴다.

> **Lombok @Data를 엔티티에 쓸 때 주의**: 강의에서 `@Getter`, `@Setter` 대신 `@Data` 하나로 줄일 수 있다고 했는데, `@Data`는 `equals`, `hashCode`, `toString`까지 만든다. 뒤에서 다룰 **양방향 연관관계**(메뉴 ↔ 카테고리)가 생기면 `toString`이 메뉴 → 카테고리 → 메뉴 목록 → 카테고리…를 끝없이 호출하다 `StackOverflowError`가 난다. 엔티티에는 `@Getter` 정도만 붙이고 `@Data`는 피하는 것이 일반적이다.

## 6. 컨벤션, 기계가 만들어도 지켜야 할까

이제 `CREATE TABLE`은 엔티티 설정으로 끝나고, SELECT·INSERT·UPDATE는 쿼리 메서드로 끝난다. 사람이 DB 테이블이나 컬럼을 직접 손댈 일이 사라지고 있다. 그러면 "사람이 보기 좋으라고 만든" 명명 컨벤션을 굳이 지켜야 하는가라는 질문이 생긴다. 사람이 손대지도 않고 들여다볼 일도 없다면, 오히려 사람이 개입하지 않는 쪽이 맞지 않느냐는 것이다.

결론은 **지키는 것이 맞다.** 아무리 기계가 만든 결과물이라도 그 결과물을 **내가 확인할 수 있어야** 하기 때문이다. 직접 작성하지 않아도 내가 볼 것이므로, 잘 볼 수 있게 만들어둬야 한다. 다만 컨벤션을 안 지키는 사람에게 그걸 강요할 명분은 점점 약해지고 있다. 그래서 더더욱 대충 넘기지 말고 꼼꼼히 정해두는 습관이 필요하다.

## 7. 연관관계 — JOIN을 객체로 표현한다

DB는 정규화로 **중복을 제거**해서, 화면에 보여줄 데이터가 여러 테이블에 흩어져 있다. 메뉴 관리 화면만 해도 메뉴 테이블에 없는 카테고리 이름이 필요하다. SQL에서는 이걸 JOIN으로 가져왔는데, JPA는 이 관계를 **엔티티 간의 관계**로 표현한다.

**누가 누구를 참조하나**: 카테고리 하나에 메뉴가 여러 개 속하므로 **카테고리가 부모, 메뉴가 자식**이다. 참조키(외래키)는 **언제나 자식이 가진다.** 부모가 자식을 참조하는 일은 없다. 그래서 `menus` 테이블에 `category_id` 컬럼이 생긴다.

**JPA의 특이한 점 — id가 아니라 부모 객체를 통째로 갖는다**:

```java
// SQL식 사고: 외래키 값만 갖는다
private Long categoryId;

// JPA식: 부모 엔티티 자체를 갖는다
private Category category;
```

그래서 카테고리 이름이 필요하면 별도 컬럼을 꺼내는 게 아니라 `menu.getCategory().getName()`처럼 **객체 관계를 따라** 가져온다.

**설정 방법**:

```java
@Entity
@Table(name = "menus")
public class Menu {                 // 자식 (N쪽)

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id")
    private Category category;
}

@Entity
@Table(name = "categories")
public class Category {             // 부모 (1쪽)

    @OneToMany(mappedBy = "category")
    private List<Menu> menus = new ArrayList<>();
}
```

- **부모 쪽 `@OneToMany`**: "나(1)는 메뉴(N) 쪽과 관계를 맺는다." 자식 목록은 `List<Menu>`로 가진다. `mappedBy`에는 **자식 엔티티(`Menu`)가 부모를 담고 있는 필드명**(`category`)을 적는다. 이걸로 두 쪽이 한 쌍의 관계라는 것이 연결된다.
- **자식 쪽 `@ManyToOne`**: 부모 쪽에서 1:N이라고 했으니 자식 쪽은 반대로 "나는 N쪽이다(Many To One)".
- **`@JoinColumn`**: SQL에서 `A INNER JOIN B ON a.x = b.y`처럼 조인 컬럼을 알려줬던 것과 같다.

> 강의에서는 `@JoinColumn`에 "카테고리 테이블에 있는 속성명"을 적는다고 했지만, 정확히는 **자식 테이블(`menus`)에 있는 외래키 컬럼명**(`category_id`)을 적는다. 이 외래키가 부모 테이블의 어떤 컬럼을 가리키는지는 생략하면 부모의 기본키(`categories.id`)로 정해진다. 엔티티 필드명이 아니라 실제 테이블의 컬럼명을 적는다는 점은 강의 설명과 같다.

부모 쪽에서 자식 목록을 쓸 때는 `category.getMenus()`를 반복문이나 스트림으로 돌리거나, `size()`로 개수를 구하는 식으로 활용한다.

**연관관계의 주인 — 외래키를 가진 쪽**: 양쪽에 다 관계를 적어두었지만, 실제 DB의 외래키(`menus.category_id`)를 관리하는 쪽은 하나뿐이다. 이 쪽을 **연관관계의 주인**이라고 부르고, 보통 **외래키를 가진 자식 쪽**(`@JoinColumn`이 붙은 `Menu.category`)이 주인이 된다. `mappedBy`가 붙은 부모 쪽(`Category.menus`)은 "나는 주인이 아니고, 상대 쪽 `category` 필드에 매핑되어 있다"는 뜻이라 **읽기 전용**이다. 그래서 메뉴의 카테고리를 바꾸려면 `category.getMenus().add(menu)`가 아니라 `menu.setCategory(category)`처럼 **주인 쪽 값을 바꿔야** 외래키가 실제로 갱신된다.

**필요할 때만 가져오기 — FetchType**: 메뉴 엔티티는 하나인데, 메뉴 관리 페이지·메뉴 조회 페이지·추천 메뉴 목록처럼 여러 곳에서 쓰인다. 어떤 곳은 카테고리가 필요하고 어떤 곳은 필요 없다. 필요 없는 곳에서까지 카테고리를 매번 채워오면 낭비다.

| FetchType | 동작 |
|---|---|
| `LAZY` | 쓸 때 가져온다. 코드에서 `menu.getCategory().getName()`처럼 실제로 접근하는 순간 그때 조회한다. |
| `EAGER` | 쓰든 안 쓰든 메뉴를 조회할 때 카테고리도 함께 가져온다. |

기본 방침은 `LAZY`로 두는 것이 좋다.

> 강의에서는 LAZY가 기본 옵션이라고 했지만, 기본값은 관계 종류마다 다르다. **`@OneToMany`는 기본이 LAZY지만, `@ManyToOne`은 기본이 EAGER**다. 그래서 위 코드처럼 `@ManyToOne(fetch = FetchType.LAZY)`를 **직접 적어줘야** 의도대로 동작한다.

## 8. 복합키 — 기본키가 두 개 이상일 때

2차 정규화를 다룰 때 "부분 함수 종속"이 나왔던 이유는, 키가 여러 컬럼으로 이루어진 **복합키**가 있기 때문이다. ncafe에서 회원과 메뉴 사이의 **좋아요, 추천, 주문**은 모두 다대다 관계다. 한 회원이 여러 메뉴를 좋아할 수 있고, 한 메뉴를 여러 회원이 좋아할 수 있다. 부모가 양쪽(회원, 메뉴)에 있는 셈이다.

좋아요 테이블은 `(member_id, menu_id)` 두 개가 합쳐져 기본키가 된다. 그런데 `@Id`를 어디에 붙여야 할까. 방법은 두 가지다.

**방법 1 — 키 묶음 클래스를 중첩시키기 (`@EmbeddedId`)**

```java
@Embeddable
public class LikeId implements Serializable {
    private Long memberId;
    private Long menuId;
    // equals, hashCode 필수
}

@Entity
@Table(name = "likes")
public class Like {

    @EmbeddedId
    private LikeId id;

    private LocalDateTime createdAt;   // 키 외의 추가 속성은 여기에
}
```

- `@Embeddable`: 독립된 엔티티가 아니라 **다른 엔티티 안에 중첩해서 들어갈 수 있는** 값 묶음이라는 표시다. 부모-자식 관계와는 다르다.
- `@EmbeddedId`: 그 중첩 가능한 묶음을 이 엔티티의 **기본키로** 쓰겠다는 표시다.

**방법 2 — 필드마다 `@Id`를 붙이기 (`@IdClass`)**

```java
@Entity
@IdClass(LikeId.class)
public class Like {
    @Id private Long memberId;
    @Id private Long menuId;
}
```

엔티티에 `@Id`를 여러 번 붙이고, 그 조합을 표현하는 키 클래스를 `@IdClass`로 따로 지정한다.

> 복합키 클래스는 두 방식 모두 `Serializable`을 구현하고 `equals`/`hashCode`를 반드시 재정의해야 한다. JPA가 키 객체끼리 같은지 비교할 때 이 메서드를 쓰기 때문이다.

> **헷갈리기 쉬운 이름들**: 키 묶음 클래스에 붙이는 건 `@Embeddable`(철자 주의: `@Embedable` 아님), 엔티티 쪽 필드에 붙이는 건 `@EmbeddedId`다. 비슷한 `@Embedded`는 주소(시·구·도로명)처럼 **일반 값 묶음을 컬럼으로 펼쳐 넣을 때** 쓰는 것이라, 이걸 붙이면 기본키가 되지 않는다(엔티티에 `@Id`가 없다는 에러가 난다). 날짜 필드 타입도 `DateTime`이 아니라 `LocalDateTime`이다.

**모든 다대다 테이블이 복합키에 맞는 것은 아니다**: 복합키 `(member_id, menu_id)`는 "이 회원과 이 메뉴의 조합은 **딱 한 번만** 존재한다"는 제약이 된다.

| 테이블 | 같은 회원·같은 메뉴 조합이 여러 번 생길 수 있나 | 키 선택 |
|---|---|---|
| 좋아요 | 없다. 한 회원은 한 메뉴에 좋아요를 한 번만 누른다 | 복합키가 잘 맞는다 |
| 추천 | 서비스 규칙에 따라 다르다. 한 번만 허용하면 복합키 | 규칙 확인 후 결정 |
| 주문 | 있다. 같은 회원이 같은 메뉴를 어제도 오늘도 주문한다 | 복합키로 하면 두 번째 주문이 중복키 에러로 막힌다. **주문은 자체 id(대리키)**를 두고, 회원·메뉴는 외래키로만 둔다 |

주문은 보통 "주문(언제, 누가)"과 "주문 항목(어떤 메뉴를 몇 개)"으로 테이블을 나누고, 둘 다 자체 id를 갖게 설계한다. 복합키는 **"조합 자체가 곧 유일한 식별자"**인 경우에만 쓴다.

## 9. 쿼리 메서드로 감당이 안 될 때 — JPQL, Criteria API, Querydsl

어떤 주인공(예: 메뉴)을 가진 페이지는 보통 **목록, 상세, 등록, 수정, 삭제(확인)** 다섯 개 정도다. 이 중 상세·등록·수정·삭제는 복잡하지 않다. 정말 복잡해지는 건 **목록**이다. 쇼핑몰 목록 화면을 떠올리면 검색 기준이 매우 많다. 그러다 보면 SELECT 절에 `FROM`의 테이블과 상관없는 값이 서브쿼리로 들어가고, `FROM` 절에 JOIN이 여러 개 붙고, `WHERE` 절도 복잡해진다.

이런 쿼리는 쿼리 메서드로 만들기 어렵다. 쿼리 메서드로 해결되는 게 대략 80%라면, **안 되는 20%는 무시할 수 없을 만큼 큰 비율**이다. 결국 SQL이 필요해진다. 하지만 SQL을 직접 쓰면 특정 DBMS 문법에 다시 종속되고, "엔티티만 바라보고 개발한다"는 JPA의 의미가 무너진다. 그래서 DBMS에 종속되지 않으면서 복잡한 쿼리를 쓸 수 있는 도구가 제공된다.

| 도구 | 정체 | 특징 |
|---|---|---|
| **JPQL** (Java Persistence Query Language) | JPA 표준 | SQL과 비슷한 문법이지만 **테이블이 아니라 엔티티와 필드명**을 대상으로 쓴다. Hibernate가 DBMS에 맞는 SQL로 바꿔준다. |
| **Criteria API** | JPA 표준 | 같은 쿼리를 문자열이 아니라 **자바 코드(API 호출)**로 조립한다. 오타를 컴파일 시점에 잡을 수 있지만 코드가 길고 읽기 어렵다. |
| **Querydsl** | 오픈소스(비표준) | 자바 코드로 쿼리를 쓰되 Criteria API보다 훨씬 SQL에 가깝게 읽힌다. 동적 조건 검색에 강하다. |

```java
// JPQL 예시 — 테이블명(menus)이 아니라 엔티티명(Menu)과 필드명(korName)을 쓴다
@Query("SELECT m FROM Menu m JOIN m.category c WHERE c.name = :categoryName AND m.price <= :maxPrice")
List<Menu> findByCategoryAndMaxPrice(@Param("categoryName") String categoryName,
                                     @Param("maxPrice") Integer maxPrice);
```

**권장 순서**: 기본 조회는 쿼리 메서드로 처리하고, 쿼리 메서드로 안 되는 20%는 **JPQL을 먼저** 시도한다. SQL과 모양이 비슷해서 이해하기 편하기 때문이다. JPQL로 부족하면 **Querydsl**을 선택적으로 쓴다. **Criteria API는 API 호출로 조립한 결과물이 읽기 어려워 많은 사람들이 잘 쓰지 않는다.** 결국 복잡한 쿼리는 **JPQL과 Querydsl 사이를 오가며 조율**하는 것이 기본이다.

```
쿼리 메서드 (80%) → 안 되면 JPQL → 그래도 안 되면 Querydsl
                       (Criteria API는 잘 안 씀)
```

특정 DBMS 문법을 직접 쓰는 네이티브 쿼리(`@Query(nativeQuery = true)`)는 DBMS 종속을 감수해야 하는 최후 수단이다. 도구를 고를 때는 동작 여부뿐 아니라 **나중에 읽는 사람이 조회 의도를 쉽게 알아볼 수 있는가**도 중요한 기준이다. 쿼리 메서드 이름이 지나치게 길어져 읽기 어려워졌다면, 그것 자체가 JPQL로 넘어갈 신호다.
