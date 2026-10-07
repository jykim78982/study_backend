---
tags: [데이터베이스, ORM, JPA, Hibernate, MyBatis, JDBC, 참고자료]
---

> 🔗 관련 노트: [[078_ORM과 JPA — 개념부터 API 설계 관점까지]] · [[038_JDBC API와 리포지토리 분리]]

# ORM 개념과 주요 프레임워크 — JDBC에서 JPA까지

## ORM의 정의와 필요성

ORM(Object-Relational Mapping)은 객체 지향 언어의 객체 모델과 관계형 데이터베이스의 테이블 구조를 매핑하는 기술이다. 더 구체적으로는 **Entity 객체 정보를 읽어서 SQL을 자동으로 생성해주는 기술**이다. 이 기술을 쓰면 개발자는 SQL 구문을 직접 작성할 필요가 없어진다.

| 장점 | 내용 |
|---|---|
| 생산성 향상 | 반복적인 SQL 작성과 결과셋 매핑 로직을 없애 개발 속도를 높인다 |
| 유지보수성 | 스키마가 바뀌어도 SQL을 일일이 고칠 필요 없이 객체 모델 중심으로 코딩할 수 있다 |
| 이식성 | 특정 DB 벤더에 종속되지 않고 표준 인터페이스로 다양한 RDBMS를 지원한다 |

## 1. Persistence API의 변천사

Persistence API란 데이터베이스 같은 영구 저장소를 이용하기 위한 API를 말한다. 자바에서 DB 접근 방식은 **JDBC → JdbcTemplate → MyBatis → ORM** 순서로 "개발자가 직접 써야 하는 코드"를 점점 줄이는 방향으로 발전해왔다.

### 1-1. JDBC — 모든 걸 직접 작성

초기에는 JDBC API로 연결 관리, Statement 생성, 결과셋 처리를 매번 직접 작성해야 했다.

```java
Class.forName("com.mysql.cj.jdbc.Driver");
String url = "jdbc:mysql://localhost:3306/mydb";

try (Connection con = DriverManager.getConnection(url, "root", "1234");
     Statement stmt = con.createStatement();
     ResultSet rs = stmt.executeQuery("SELECT id, name FROM users")) {

    while (rs.next()) {
        System.out.println(rs.getInt("id") + " : " + rs.getString("name"));
    }
}
```

`users` 데이터를 가져오는 코드인데, 다른 데이터를 가져올 때도 바뀌는 건 SQL뿐이고 나머지는 거의 복사·붙여넣기 수준으로 똑같다.

### 1-2. JdbcTemplate — 반복 코드를 라이브러리화

이 반복 코드를 줄이기 위해 Spring Framework는 JdbcTemplate을 만들어 연결 관리와 예외 처리를 자동화했다.

```java
jdbcTemplate.query("SELECT id, name FROM users", (rs, rowNum) -> {
    System.out.println(rs.getInt("id") + " : " + rs.getString("name"));
    return null;
});
```

연결·해제 코드가 전부 숨겨지고 `jdbcTemplate.query(...)` 한 줄로 같은 결과를 얻는다.

### 1-3. MyBatis — SQL만 적으면 구현은 자동

JdbcTemplate이 코드를 줄여주긴 했지만 실무에서는 MyBatis가 더 널리 쓰였다. template을 호출하는 코드조차 쓸 필요가 없기 때문이다.

```java
@Select("SELECT id, name FROM users")
List<User> findAll();
```

Repository 메서드에 SQL만 지정하면 구현은 자동으로 만들어진다. 이런 특징 때문에 MyBatis를 **SQL 매핑 프레임워크**라고 부른다.

### 1-4. ORM — SQL조차 쓰지 않는다

MyBatis는 오랫동안 사랑받았지만, ORM은 한 단계 더 나아가 **SQL도 작성할 필요가 없게** 만들었다.

테이블의 데이터를 자바 엔티티 객체로 옮기기 위해 개발자가 SQL을 쓰고 MyBatis로 값을 옮겨오다 보면, "엔티티 객체의 속성만 읽을 수 있다면 SQL 작성도 자동화할 수 있지 않을까?"라는 생각에 이르게 된다. 그래서 자바 객체를 읽어 SQL을 만들어주는 라이브러리가 등장했고, 이것을 **ORM 프레임워크**라고 부른다.

ORM을 쓰면 JDBC 코드도, SQL도 쓸 필요가 없다. 어떤 클래스가 엔티티라고만 설정하고, 속성명이 테이블과 다를 때만 컬럼명을 지정하면 된다.

```java
@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;

    // JPA 엔티티는 반드시 기본 생성자가 필요하다
    protected User() {}

    public User(String name) {
        this.name = name;
    }

    public Long getId() { return id; }
    public String getName() { return name; }
}
```

`@Entity`, `@Table`, `@Id` 같은 설정만으로 Repository에 JDBC 코드나 SQL을 전혀 작성하지 않아도 된다.

**단계별 비교**

| 방식 | 개발자가 작성하는 것 | 자동화되는 것 |
|---|---|---|
| JDBC | 연결·Statement·결과셋 처리·SQL 전부 | 없음 |
| JdbcTemplate | SQL + 결과 매핑 람다 | 연결 관리·예외 처리 |
| MyBatis | SQL(어노테이션/XML) | 메서드 구현·결과 매핑 |
| ORM(JPA) | 엔티티 클래스 + 매핑 설정 | SQL 생성·구현·결과 매핑 |

## 2. JPA와 Hibernate의 관계

ORM을 구현한 프레임워크는 Hibernate를 비롯해 EclipseLink, DataNucleus, OpenJPA, ObjectDB 등 여러 종류가 있다. 이들은 모두 엔티티만 준비하고 간단히 설정하면 Repository를 자동으로 구현해준다.

### 2-1. 구현체마다 달랐던 설정 방식

문제는 각 프레임워크가 엔티티에 붙이는 설정 방식이 서로 달랐다는 점이다. 그래서 ORM 프레임워크를 바꾸려면 엔티티 설정까지 전부 바꿔야 하는 부담이 있었다.

| 구분 | Hibernate 자체 | JPA 표준 |
|---|---|---|
| 패키지 | `org.hibernate.annotations.*` | `jakarta.persistence.*` (구버전은 `javax.persistence.*`) |
| 대표 예시(클래스 레벨) | `@DynamicInsert`, `@DynamicUpdate`, `@Where`, `@Proxy` | `@Entity`, `@Table`, `@Inheritance`, `@DiscriminatorColumn` |
| 역할 | SQL 생성 시 비효율 제거, 행 필터링, 지연 로딩 전략 | 엔티티 인식, 테이블 매핑, 상속 전략 |
| JPA 통일 후 | 여전히 Hibernate 전용(JPA 명세에 없음) | 표준 — 어떤 JPA 구현체에서도 동일하게 동작 |

> Java EE가 Jakarta EE로 넘어가면서 패키지명이 `javax.persistence`에서 `jakarta.persistence`로 바뀌었다. Spring Boot 3 이상은 `jakarta.persistence`를 쓴다.

### 2-2. JPA 설정으로 통일된 ORM 프레임워크들

JPA(Java Persistence API)는 Java EE(현 Jakarta EE) 표준으로, ORM에 대한 인터페이스와 어노테이션을 정의한다. Hibernate는 그 JPA 표준을 구현한 구체적인 프레임워크다.

- **JPA**: "무엇을 해야 하는지"를 정의하는 표준
- **Hibernate**: "어떻게 하는지"를 구현한 라이브러리

개발자는 JPA API로 코드를 작성하고, 런타임에는 Hibernate가 실제 처리를 맡는다. 전체 흐름은 다음과 같다.

1. **Entities(오브젝트 DBMS)**: `@Entity` 등 JPA 설정이 붙은 엔티티 클래스들
2. **EntityManagerFactory**: 엔티티 설정을 읽어 Repository가 쓸 기능을 만들어준다. 이 부분을 실제로 구현하는 것이 Hibernate, EclipseLink 같은 구현체다.
3. **Repository**: 자바 애플리케이션은 Repository만 상대하고, Repository가 생성된 SQL로 관계형 DBMS와 데이터를 주고받는다.

## 3. ORM의 동작 원리

ORM 프레임워크는 일반적으로 다음 단계로 동작한다.

1. **메타데이터 해석**: 엔티티 클래스의 어노테이션이나 XML 설정을 읽어 객체와 테이블 간 매핑 규칙을 파악한다.
2. **SQL 생성**: 객체의 상태 변경이나 조회 요청을 받아 내부적으로 SQL 문장을 생성한다.
3. **결과 매핑**: DB가 반환한 결과셋을 객체 인스턴스로 변환해 돌려준다.
4. **트랜잭션 관리**: 데이터 무결성을 위해 트랜잭션 경계를 관리하고, 필요하면 롤백한다.
