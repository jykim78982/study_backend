---
tags: [JPA, ORM, 엔티티매핑, 오답노트]
---

> 🔗 관련 노트: [[078_ORM과 JPA — 개념부터 API 설계 관점까지]] · [[023_ORM 개념과 주요 프레임워크 — JDBC에서 JPA까지 참고자료]] · [[079_Spring Data JPA 리포지토리와 엔티티 매핑 — 쿼리 메서드, 연관관계, 복합키]] · [[JPA 엔티티 상속 매핑 오답노트]]

# ORM 개념과 엔티티 매핑 오답노트

### 1. ORM에 대한 잘못된 설명

**문제**: ORM(Object-Relational Mapping) 개념에 대한 설명으로 가장 올바르지 않은 것은 무엇인가?

1. 객체지향 언어의 객체와 관계형 데이터베이스의 테이블을 매핑하는 기술이다.
2. 개발자가 직접 SQL을 작성하지 않아도 패러다임 불일치 문제를 해결해 준다.
3. JPA는 자바 진영의 ORM 기술 표준 명세이다.
4. ORM을 사용하면 데이터베이스에 직접 접근할 수 없으므로 SQL 튜닝이 완전히 불가능해진다.

**정답: 4번**

**ORM은 SQL을 대신 써 줄 뿐, SQL을 막지 않는다**

ORM이 하는 일은 객체를 다루는 코드를 보고 **SQL을 대신 만들어** 실행해 주는 것이다. 결국 DB에 가는 것은 SQL이므로, 그 SQL을 보고 고칠 방법이 모두 열려 있다.

| 튜닝 방법 | 설명 |
|---|---|
| 생성된 SQL 확인 | `spring.jpa.show-sql=true`, `logging.level.org.hibernate.SQL=debug`로 JPA가 만든 SQL을 본다 |
| JPQL | `@Query("select m from Member m join fetch m.team")`처럼 쿼리를 직접 쓴다(fetch join으로 N+1 해결 등) |
| 네이티브 쿼리 | `@Query(value = "SELECT ...", nativeQuery = true)`로 DB 고유 SQL을 그대로 쓴다 |
| 쿼리 힌트 | `@QueryHints`로 DB·하이버네이트에 힌트를 준다 |
| 조회 도구 | QueryDSL, JdbcTemplate 등을 함께 쓴다 |

"완전히 불가능"은 틀렸다. 오히려 ORM이 만드는 SQL을 **확인하지 않고 쓰는 것**이 성능 문제의 흔한 원인(N+1 문제 등)이다.

> **2번이 맞는 이유**: 객체는 상속·참조·그래프 탐색을 쓰고, 테이블은 외래 키·조인을 쓴다. 이 차이를 **패러다임 불일치**라고 하며, ORM은 개발자가 객체답게 코드를 짜면 그에 맞는 SQL을 만들어 이 차이를 메워 준다. **3번**: JPA는 인터페이스 모음(표준 명세)이고, 실제 구현체는 하이버네이트 등이다.

**정리**: ORM은 SQL을 자동으로 만들어 줄 뿐, 생성된 SQL 확인·JPQL·네이티브 쿼리·힌트로 튜닝할 수 있다.

---

### 2. 엔티티 매핑 어노테이션에 대한 올바른 설명

**문제**: JPA에서 엔티티 클래스와 데이터베이스 테이블을 매핑할 때 사용하는 어노테이션에 대한 설명으로 올바른 것은 무엇인가?

1. `@Entity`가 붙은 클래스는 기본 생성자(Default Constructor)가 반드시 존재해야 한다.
2. `@Table` 어노테이션을 생략하면 예외가 발생하며 애플리케이션이 실행되지 않는다.
3. `@Id`는 식별자 필드에 사용되며, 자동 증가는 지정할 수 없다.
4. `@Column` 어노테이션을 붙이지 않은 필드는 데이터베이스 테이블 매핑에서 제외된다.

**정답: 1번**

**1번 — 기본 생성자가 필요한 이유**

JPA는 DB에서 행을 읽어 올 때 **어떤 생성자에 무슨 값을 넣어야 할지 모른다.** 그래서 리플렉션으로 **매개변수 없는 생성자**를 호출해 빈 객체를 만든 뒤, 필드에 값을 채운다. 지연 로딩용 **프록시**(엔티티를 상속한 가짜 객체)를 만들 때도 이 생성자가 필요하다.

```java
@Entity
@NoArgsConstructor(access = AccessLevel.PROTECTED)   // JPA용 기본 생성자, 밖에서 new로 빈 객체를 못 만들게 protected
public class Member {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;

    public Member(String name) { this.name = name; }   // 다른 생성자를 만들면 기본 생성자가 자동으로 안 생긴다
}
```

- `public` 또는 `protected`여야 한다(`private`이면 프록시가 상속하지 못한다).
- 다른 생성자를 하나라도 만들면 자바가 기본 생성자를 자동으로 만들어 주지 않으므로, 직접 쓰거나 `@NoArgsConstructor`를 붙인다.

**나머지 보기가 틀린 이유**

| 보기 | 실제 동작 |
|---|---|
| 2. `@Table` 생략 시 예외 | 생략하면 **엔티티 이름**(기본은 클래스 이름)을 테이블 이름으로 쓴다. 스프링 부트는 `OrderItem` → `order_item`처럼 스네이크 케이스로 바꾼다. `@Table`은 이름이 다를 때(`@Table(name = "orders")`)만 붙인다 |
| 3. `@Id`는 자동 증가 불가 | `@GeneratedValue`를 함께 붙여 자동 생성 전략을 정한다(`IDENTITY`: DB의 자동 증가, `SEQUENCE`: 시퀀스, `AUTO`: DB에 맞게) |
| 4. `@Column` 없으면 매핑 제외 | 엔티티의 필드는 **기본적으로 모두** 컬럼으로 매핑된다. `@Column`은 이름·길이·`nullable` 등을 바꿀 때만 붙인다. 매핑에서 빼려면 **`@Transient`** |

```java
@Column(name = "user_name", length = 50, nullable = false)
private String name;        // 컬럼 설정을 바꿀 때만 @Column

private int age;            // @Column 없어도 age 컬럼으로 매핑된다

@Transient
private String tempToken;   // 테이블에 매핑하지 않는다
```

> **헷갈리기 쉬운 점**: `@Transient`는 `jakarta.persistence.Transient`(어노테이션)이고, 자바 키워드 `transient`(직렬화 제외)와는 다르다. JPA에서 매핑을 빼려면 어노테이션 쪽을 쓴다.

**정리**: 엔티티는 JPA가 리플렉션과 프록시로 객체를 만들기 때문에 `public`/`protected` **기본 생성자**가 필수다. `@Table`·`@Column`은 기본값을 바꿀 때만 쓰는 선택 사항이고, 자동 증가는 `@GeneratedValue`, 매핑 제외는 `@Transient`로 한다.
