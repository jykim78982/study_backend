---
tags: [스프링부트, JPA, Hibernate, PostgreSQL, YAML, 실습]
---

> 🔗 관련 노트: [[078_ORM과 JPA — 개념부터 API 설계 관점까지]] · [[023_ORM 개념과 주요 프레임워크 — JDBC에서 JPA까지 참고자료]] · [[038_Spring Boot 3계층 실습 — JdbcTemplate로 Menu API 만들기]] · [[043_Docker로 팀 공용 PostgreSQL 개발 DB 만들기]]

# JPA 추가하기 — MenuRepository로 첫 API 만들기

**대상**: JdbcTemplate 실습을 마치고 Spring Boot 기본 구조와 3계층 구조를 아는 사람

**목표**: 스프링 부트 webmvc 프로젝트에 JPA를 추가하고 `MenuRepository`를 통해 `/api/v1/admin/menus` API를 구현한다

**완성물**: `POST /api/v1/admin/menus`로 데이터를 저장하고 `GET /api/v1/admin/menus`로 조회하는 실행 가능한 애플리케이션

**준비물**

- Spring Boot 4.1, Java 21, Gradle
- Docker가 실행 중이고 PostgreSQL 컨테이너가 떠 있는 상태
- `application.properties`만 써봤고 YAML 형식은 처음인 상태

> 원문 코드의 패키지명 `com.new-cafe.backend`는 하이픈(`-`)이 들어가서 자바 패키지명으로 쓸 수 없다(컴파일 에러). 이 노트에서는 `com.newcafe.backend`로 통일했고, import 경로도 실제 폴더 구조(`entity`, `repository`, `api.v1.admin`)에 맞춰 정리했다.

## 1. JPA 의존성 추가

새로 시작한 조별 ncafe 프로젝트에 JPA 라이브러리를 설정하고 데이터베이스를 사용해볼 차례다. 가장 먼저 `build.gradle`에 `spring-boot-starter-data-jpa`를 추가한다. 이 의존성이 JPA 구현체(Hibernate)와 Spring Data JPA를 함께 가져온다.

**1-1. build.gradle 수정**

파일: `build.gradle`

```groovy
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    runtimeOnly 'org.postgresql:postgresql'
    compileOnly 'org.projectlombok:lombok'
    annotationProcessor 'org.projectlombok:lombok'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}
```

> Spring Boot 4부터는 웹 스타터 이름이 `spring-boot-starter-webmvc`로 바뀌었다. 프로젝트를 만들 때 이미 들어간 웹 스타터는 그대로 두고, `data-jpa`와 `postgresql` 두 줄만 추가하면 된다.

**1-2. Gradle 동기화**

IDE의 Gradle 패널에서 "Sync"를 누르거나 터미널에서 아래 명령을 실행한다.

```bash
./gradlew dependencies --configuration runtimeClasspath | grep jpa
```

Windows는 `gradlew.bat dependencies --configuration runtimeClasspath | findstr jpa`

**✅ 확인**

- 터미널에 `org.hibernate.orm:hibernate-core`와 `org.springframework.data:spring-data-jpa`가 출력된다.
- IDE의 External Libraries에 `hibernate-core`가 보인다.

**🎓 코멘트**: `spring-boot-starter-data-jpa`는 JPA 스펙을 구현하는 Hibernate와, JPA 리포지토리를 자동 생성하는 Spring Data JPA를 한 번에 가져온다. JdbcTemplate 실습 때처럼 `spring-boot-starter-jdbc`만으로는 엔티티 매핑이나 리포지토리 인터페이스 자동 생성이 안 된다. 이 단계에서는 의존성만 추가했고 아직 코드가 없으므로 에러는 나지 않는다.

> **추가 설명 — 세 가지 이름의 관계**
>
> | 이름 | 정체 | 역할 |
> |---|---|---|
> | JPA | 표준 규격(인터페이스·어노테이션) | `@Entity`, `@Id` 같은 매핑 설정 방법을 정의 |
> | Hibernate | JPA 구현체 | 엔티티를 읽어 실제 SQL을 만들고 실행 |
> | Spring Data JPA | 스프링의 추가 계층 | 리포지토리 **인터페이스만 선언하면 구현체를 자동 생성** |
>
> 4단계에서 "인터페이스만 만들었는데 동작하는" 마법은 Hibernate가 아니라 Spring Data JPA가 해주는 일이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Could not resolve org.springframework.boot:spring-boot-starter-data-jpa` | Gradle 캐시 문제 또는 네트워크 차단 | `./gradlew clean` 후 다시 동기화, 또는 프록시 설정 확인 |
| `Lombok annotation processor not found` | Lombok 의존성 누락 | `compileOnly`와 `annotationProcessor` 두 줄 모두 확인 |

**📝 핵심**: `spring-boot-starter-data-jpa`가 Hibernate와 Spring Data JPA를 함께 가져온다. 의존성 추가 후 반드시 Gradle 동기화를 해야 IDE가 인식한다.

## 2. application.yml로 DB·JPA 설정

이전 프로젝트에서는 DB 연결 설정을 `application.properties`에 작성했지만, 이번에는 `application.yml`을 사용한다. 두 파일은 같은 역할을 하지만, 최근에는 yml을 더 선호한다. YAML은 들여쓰기(공백)로 계층 구조를 표현하기 때문에, properties에서 반복해서 적어야 했던 상위 계층 이름이 깔끔하게 사라진다.

**2-1. application.yml 만들기**

파일: `src/main/resources/application.yml`

```yaml
spring:
  # 데이터베이스 연결을 위한 접속 정보
  datasource:
    # 접속 주소 (호스트, 포트, 데이터베이스 이름)
    url: jdbc:postgresql://cloud.newlecture.com:5441/ncafedb
    username: ncafe
    password: your_password_here
    driver-class-name: org.postgresql.Driver
  # JPA 설정 ===============================
  jpa:
    hibernate:
      # 테이블 스키마 자동 생성/갱신 모드
      ddl-auto: update
    # 실행되는 SQL을 콘솔에 출력
    show-sql: true
    properties:
      hibernate:
        # 출력되는 SQL을 보기 좋게 줄바꿈
        format_sql: true
```

이 설정만으로 Repository 객체를 직접 생성할 필요가 없어진다.

> 포트는 조별로 다르다. 1조: 5441, 2조: 5442, 3조: 5443, 4조: 5444. 자신의 조에 맞게 url의 포트를 바꾼다.

> **추가 설명 — 비밀번호를 파일에 직접 쓰지 말자**: `application.yml`은 보통 git에 함께 올라가므로, 실제 비밀번호를 그대로 적으면 저장소에 비밀번호가 노출된다. `password: ${DB_PASSWORD}`처럼 환경 변수를 참조하게 하고 실제 값은 실행 환경에서 넣어주는 방식을 쓰는 것이 안전하다.

**2-2. properties와 YAML 차이**

properties에서는 같은 접두어를 매번 반복해야 한다.

```properties
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true
```

YAML에서는 반복되는 부분을 들여쓰기로 해결하고, 달라지는 부분만 쓴다.

```yaml
spring:
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: true
```

- `.`(점)이 한 단계 들여쓰기(공백 2개)로 바뀐다.
- 값은 `=` 대신 `:`(콜론 + 공백)으로 쓴다.
- 탭은 절대 쓰지 않는다. 반드시 공백만 쓴다.

**✅ 확인**

- `src/main/resources/application.yml` 파일이 존재한다.
- IDE의 YAML 에디터에 에러 마커가 없다.
- `spring.datasource.url`에 자신의 조 포트가 들어 있다.

**🎓 코멘트**: `ddl-auto: update`는 엔티티 클래스가 바뀌면 테이블 스키마를 자동으로 갱신한다. 개발 단계에서는 편하지만, 운영 환경에서는 `validate` 또는 `none`으로 바꿔야 한다. `show-sql: true`는 실행되는 SQL을 콘솔에 출력해 디버깅할 때 유용하고, `format_sql: true`는 그 SQL을 보기 좋게 줄바꿈해준다. YAML의 들여쓰기는 의미가 있는 문법이라, 공백 하나만 틀어져도 설정이 무시되거나 에러가 난다.

> **추가 설명 — ddl-auto 옵션 정리**
>
> | 값 | 동작 | 용도 |
> |---|---|---|
> | `create` | 시작할 때마다 테이블을 지우고 새로 만듦(데이터 삭제) | 테스트 |
> | `create-drop` | `create` + 종료 시 테이블 삭제 | 테스트 |
> | `update` | 엔티티와 비교해 없는 테이블·컬럼만 추가(기존 컬럼은 지우지 않음) | 개발 |
> | `validate` | 엔티티와 테이블이 맞는지 검사만 하고, 다르면 실행 실패 | 운영 |
> | `none` | 아무것도 하지 않음 | 운영 |
>
> 조 전체가 같은 DB를 공유하는 상황에서 누군가 `create`로 실행하면 팀원들의 데이터가 전부 사라진다. 팀 공용 DB에서는 `update` 이상으로 위험한 옵션을 쓰지 않도록 주의한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Failed to load application config` | YAML 들여쓰기 오류(탭 사용, 공백 수 불일치) | 탭을 공백으로 바꾸고, 같은 계층은 같은 공백 수인지 확인 |
| `Connection refused` | 포트가 자신의 조와 다름 | url의 포트를 자신의 조 포트(5441~5444)로 수정 |
| `password authentication failed for user "ncafe"` | 비밀번호 오류 | password 값을 실제 비밀번호로 교체 |

**📝 핵심**: YAML은 `.`을 들여쓰기로, `=`를 `:`로 바꾼다. `ddl-auto: update`는 개발용이고, 운영에서는 `validate`로 바꾼다.

## 3. Entity 클래스 작성

JPA·Hibernate 설정이 끝났으면, 프레임워크가 SQL을 만들 수 있도록 엔티티 클래스에 어노테이션으로 매핑 정보를 설정한다.

**3-1. Menu.java 만들기**

파일: `src/main/java/com/newcafe/backend/entity/Menu.java`

```java
package com.newcafe.backend.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "menus")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Menu {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "kor_name", nullable = false)
    private String korName;

    @Column(name = "eng_name", nullable = false)
    private String engName;

    @Column(name = "price", nullable = false)
    private Integer price;
}
```

JPA 엔티티는 데이터베이스 테이블과 1:1로 매핑되는 클래스다. `@Entity`와 `@Id`는 필수다. `@Entity`는 SQL을 만들 대상 클래스임을 선언하고, `@Id`는 수정·삭제 등에 쓸 식별 속성을 지정한다.

컬럼명이 다를 때는 `@Column`으로 맞출 수 있지만, 단순히 표기 컨벤션(카멜 ↔ 스네이크) 차이라면 쓸 필요가 없다.

> **추가 설명 — @Column(name=...)이 없어도 되는 이유**: Spring Boot는 기본적으로 `CamelCaseToUnderscoresNamingStrategy`라는 네이밍 전략을 사용해서, 필드명 `korName`을 컬럼명 `kor_name`으로 자동 변환한다. 그래서 위 코드의 `@Column(name = "kor_name")`은 사실 생략해도 결과가 같다. `@Column`은 이름이 규칙과 전혀 다를 때(예: 필드 `korName` ↔ 컬럼 `menu_title`)나 `nullable`, `length` 같은 제약을 지정할 때 쓴다. 이 변환 규칙을 바꾸고 싶다면 `spring.jpa.hibernate.naming.physical-strategy`로 다른 전략을 지정한다.

**3-2. 패키지 구조 확인**

- `entity/` 폴더가 없으면 IDE에서 우클릭 → New → Package로 만든다.
- import는 `jakarta.persistence`다. `javax.persistence`가 아니다.

> **추가 설명 — jakarta와 javax**: 원문에는 "Java 9 이후의 표준 패키지"라고 되어 있지만, 정확히는 **자바 버전이 아니라 Java EE가 Eclipse 재단으로 넘어가 Jakarta EE로 바뀌면서(Jakarta EE 9, 2020년) 패키지명이 `javax.*`에서 `jakarta.*`로 바뀐 것**이다. Spring Boot 3 이상은 `jakarta.persistence`를 쓰므로, 인터넷의 오래된 예제에서 `javax.persistence`를 복사하면 컴파일되지 않는다.

**✅ 확인**

- `Menu.java` 파일이 `entity/` 패키지에 있다.
- IDE에서 `@Entity`에 빨간 밑줄이 없다.
- `@GeneratedValue(strategy = GenerationType.IDENTITY)`가 id 필드에 붙어 있다.

**🎓 코멘트**: `@Entity`는 "이 클래스가 테이블과 매핑된다"는 선언이다. `@Table(name = "menus")`로 테이블 이름을 명시하지 않으면 클래스명 `Menu`를 따라 테이블 이름이 `menu`로 정해진다. 기존 DB에 `menus` 테이블이 있다면 이름이 어긋나므로, 원하는 이름을 명시하는 것이 안전하다. `@GeneratedValue(strategy = GenerationType.IDENTITY)`는 PostgreSQL의 IDENTITY(또는 SERIAL) 컬럼으로 id를 자동 생성한다. JdbcTemplate 실습 때처럼 ResultSet을 직접 읽지 않아도 JPA가 ResultSet을 `Menu` 객체로 바꿔준다.

> **추가 설명 — 엔티티에 Lombok을 쓸 때 주의**: JPA는 내부적으로 엔티티를 기본 생성자로 만들기 때문에 `@NoArgsConstructor`가 반드시 있어야 한다. `@Builder`는 모든 필드 생성자가 필요해서 `@AllArgsConstructor`와 함께 붙였다. 실무에서는 아무 데서나 값을 바꾸지 못하게 엔티티에 `@Setter`를 빼고, 기본 생성자를 `@NoArgsConstructor(access = AccessLevel.PROTECTED)`로 막는 경우가 많다. 이번 실습은 흐름을 익히는 게 목적이라 단순하게 갔다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `NoClassDefFoundError: jakarta/persistence/Entity` | `spring-boot-starter-data-jpa` 미설치 또는 Gradle 미동기화 | 1단계 의존성이 제대로 들어왔는지 확인 |
| `Entity 'Menu' does not have a primary key` | `@Id` 누락 | id 필드에 `@Id`와 `@GeneratedValue` 추가 |
| `relation "menus" does not exist` | `ddl-auto`가 `none` 또는 `validate`인 경우 | `application.yml`에서 `ddl-auto: update`인지 확인 |

**📝 핵심**: `@Entity` 클래스는 테이블과 1:1로 매핑된다. `@GeneratedValue(strategy = GenerationType.IDENTITY)`로 id를 자동 생성한다.

## 4. MenuRepository 인터페이스 추가

엔티티 설정이 끝나면 Repository는 구현할 필요가 없다. Spring Data JPA는 `JpaRepository` 인터페이스를 구현한 구현체를 이미 IoC 컨테이너에 준비해두고, 그것을 주입받아 쓰면 된다. `JpaRepository`를 상속한 인터페이스에는 `flush()`, `saveAndFlush()`, `saveAllAndFlush()`, `deleteAllInBatch()`, `deleteAllByIdInBatch()`, `getById()` 같은 메서드가 이미 모두 선언되어 있고(상위 인터페이스로부터 `save()`, `findAll()`, `findById()`, `deleteById()`, `count()` 등도 물려받는다), 그 구현은 Spring Data JPA가 대신 만들어준다.

그럼에도 `MenuRepository` 인터페이스를 따로 추가하는 이유는 **나중에 커스텀 메서드가 필요하기 때문**이다. 특이한 점은 클래스가 아니라 **인터페이스**를 추가한다는 것이다. "필요한 함수를 인터페이스에 이름만 선언해두면 Spring Data JPA가 알아서 구현해줄 테니, 뭐가 필요한지만 말해달라"는 방식이다.

**4-1. MenuRepository 만들기**

파일: `src/main/java/com/newcafe/backend/repository/MenuRepository.java`

```java
package com.newcafe.backend.repository;

import com.newcafe.backend.entity.Menu;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MenuRepository extends JpaRepository<Menu, Long> {
}
```

제네릭의 `<Menu, Long>`은 "**Menu 엔티티**를 다루고, 그 엔티티의 **id 타입은 Long**"이라는 뜻이다. 이것으로 Menu를 관리하기 위한 기본 구현이 끝난다.

**4-2. JdbcTemplate 방식과 비교**

JdbcTemplate 실습 때는 인터페이스와 구현 클래스를 둘 다 직접 만들어야 했다.

```java
public interface MenuRepository {
    void save(Menu menu);
    List<Menu> findAll();
}

@Repository
public class MenuRepositoryImpl implements MenuRepository {
    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Override
    public void save(Menu menu) {
        jdbcTemplate.update("INSERT INTO menu ...", ...);
    }

    @Override
    public List<Menu> findAll() {
        return jdbcTemplate.query("SELECT ...", rowMapper);
    }
}
```

JPA에서는 위의 구현 클래스 전체가 사라지고, 빈 인터페이스 하나만 남는다.

> **추가 설명 — 커스텀 메서드는 이름 규칙으로 만든다 (쿼리 메서드)**: 나중에 "가격이 특정 값 이하인 메뉴"가 필요하면 인터페이스에 아래처럼 **선언만** 추가한다.
>
> ```java
> List<Menu> findByPriceLessThanEqual(Integer price);
> List<Menu> findByKorNameContaining(String keyword);
> ```
>
> Spring Data JPA는 메서드 이름을 `find` + `By` + `필드명` + `조건` 규칙으로 해석해 `WHERE price <= ?`, `WHERE kor_name LIKE %?%` 같은 SQL을 자동으로 만든다. 이름이 규칙에 맞지 않으면 애플리케이션 시작 시 `Could not create query for method ...` 에러가 난다.

**✅ 확인**

- `MenuRepository.java` 파일이 `repository/` 패키지에 있다.
- `JpaRepository<Menu, Long>`을 상속한다.
- 인터페이스 안에 메서드가 없다(빈 인터페이스).

**🎓 코멘트**: `JpaRepository<T, ID>`는 `CrudRepository`를 확장한 인터페이스로, `save`, `findAll`, `findById`, `delete` 등 기본 CRUD 메서드를 제공한다. Spring Data JPA는 애플리케이션 시작 시 `MenuRepository` 인터페이스를 스캔하고, **프록시 객체**를 만들어 빈으로 등록한다. 그래서 주입받으면 바로 쓸 수 있다. RowMapper도 직접 작성하지 않는다 — JPA가 엔티티 필드와 컬럼 이름을 매핑해서 객체를 만든다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `No qualifying bean of type 'MenuRepository'` | 리포지토리가 컴포넌트 스캔 범위 밖에 있음 | `@SpringBootApplication` 클래스의 패키지(`com.newcafe.backend`)가 `MenuRepository` 패키지의 상위인지 확인 |
| `Could not create query for method ...` | 커스텀 메서드 이름이 규칙에 맞지 않음 | 지금은 커스텀 메서드가 없으므로, 이 에러가 나면 `Menu`에 `@Entity`가 제대로 붙었는지 확인 |

**📝 핵심**: `JpaRepository<Menu, Long>`을 상속하는 빈 인터페이스가 리포지토리의 전부다. Spring Data JPA가 프록시로 구현체를 자동 생성한다.

## 5. 컨트롤러에서 Repository 사용

컨트롤러에서 `MenuRepository`를 주입하고 `save`와 `findAll`을 호출한다. JdbcTemplate 실습 때 DAO를 주입하던 구조와 같지만, 구현체를 직접 만들지 않는다는 점이 다르다.

**5-1. MenuAdminController.java 만들기**

파일: `src/main/java/com/newcafe/backend/api/v1/admin/MenuAdminController.java`

```java
package com.newcafe.backend.api.v1.admin;

import com.newcafe.backend.entity.Menu;
import com.newcafe.backend.repository.MenuRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/admin/menus")
@RequiredArgsConstructor
public class MenuAdminController {

    private final MenuRepository menuRepository;

    @PostMapping
    public Menu createMenu(@RequestBody Menu menu) {
        return menuRepository.save(menu);
    }

    @GetMapping
    public List<Menu> findAllMenus() {
        return menuRepository.findAll();
    }
}
```

> 원문은 파일명이 `MenuAdminController.java`인데 클래스명이 `MenuController`로 되어 있었다. 자바에서 public 클래스명은 파일명과 같아야 하므로 `MenuAdminController`로 맞췄다.

**5-2. JdbcTemplate 실습 때와 차이**

- `@Autowired private MenuDao menuDao;` → `private final MenuRepository menuRepository;`
- `menuDao.save(menu)` → `menuRepository.save(menu)`
- `menuDao.findAll()` → `menuRepository.findAll()`
- 호출 모양은 같지만, `MenuRepository`는 인터페이스이고 실제 구현체는 프록시다.

**✅ 확인**

- `MenuAdminController.java` 파일이 `api/v1/admin/` 패키지에 있다.
- `@RequiredArgsConstructor`로 `MenuRepository`를 주입한다.
- `@PostMapping`과 `@GetMapping`이 `/api/v1/admin/menus`에 매핑된다.

**🎓 코멘트**: `@RequiredArgsConstructor`는 `final` 필드를 받는 생성자를 자동으로 만들어, 생성자 주입이 되게 한다. 생성자가 하나뿐이면 `@Autowired`도 생략할 수 있다. `menuRepository.save(menu)`는 id가 null이면 INSERT, id가 있으면 UPDATE를 한다. `findAll()`은 테이블 전체를 조회해 `List<Menu>`로 돌려준다. RowMapper로 ResultSet을 변환하는 코드는 어디에도 없다.

> **추가 설명 — 이번 실습에서 일부러 생략한 것들**: 이 컨트롤러는 JPA 동작을 빠르게 확인하려고 3계층 원칙 두 가지를 잠시 어겼다.
>
> 1. **서비스 계층 생략**: 컨트롤러가 리포지토리를 직접 호출한다. 실제로는 `컨트롤러 → 서비스 → 리포지토리` 순서로 호출하고, 업무 로직은 서비스에 둔다.
> 2. **엔티티를 그대로 요청·응답에 사용**: `@RequestBody Menu`, 반환값 `Menu`처럼 엔티티를 API에 그대로 노출했다. 이렇게 하면 클라이언트가 보낸 JSON이 엔티티에 바로 들어가 의도하지 않은 필드(예: id)까지 바뀔 수 있고, 엔티티 구조를 바꾸는 순간 API 응답 형태도 같이 바뀐다. 실제로는 `MenuCreateRequestDto`, `MenuListResponseDto`처럼 DTO로 받고 내보내야 한다.
>
> 다음 단계에서 서비스와 DTO를 끼워 넣어 제대로 된 3계층 구조로 정리하게 된다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Required type is provided from more than one bean` | `MenuRepository` 빈이 두 개 이상 등록됨 | 같은 이름의 리포지토리 인터페이스·구현 클래스가 남아 있지 않은지 확인(JdbcTemplate 시절 `MenuRepositoryImpl` 등) |
| `Cannot resolve method 'save' in 'MenuRepository'` | `JpaRepository`를 상속하지 않았거나 import 누락 | `import org.springframework.data.jpa.repository.JpaRepository;` 확인 |

**📝 핵심**: `MenuRepository`는 인터페이스지만 `save`, `findAll`을 바로 호출할 수 있다. `@RequiredArgsConstructor`로 `final` 필드 주입을 간결하게 한다.

## 6. 실행하고 확인하기

애플리케이션을 실행하고, curl로 POST와 GET을 호출해서 PostgreSQL에 데이터가 저장되고 조회되는지 확인한다.

**6-1. 애플리케이션 실행**

파일: `src/main/java/com/newcafe/backend/BackendApplication.java`

```java
package com.newcafe.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class BackendApplication {
    public static void main(String[] args) {
        SpringApplication.run(BackendApplication.class, args);
    }
}
```

```bash
./gradlew bootRun
```

Windows는 `gradlew.bat bootRun`

**6-2. POST로 메뉴 저장**

다른 터미널에서 실행한다.

```bash
curl -X POST http://localhost:8080/api/v1/admin/menus \
  -H "Content-Type: application/json" \
  -d '{"korName":"아메리카노","engName":"Americano","price":4500}'
```

**6-3. GET으로 메뉴 조회**

```bash
curl http://localhost:8080/api/v1/admin/menus
```

**6-4. PostgreSQL에서 확인**

```bash
docker exec -it <postgres_container_name> psql -U ncafe -d ncafedb
```

```sql
SELECT * FROM menus;
```

> 원문에는 `create table menu`, `SELECT * FROM menu;`로 되어 있지만, 3단계에서 `@Table(name = "menus")`로 지정했으므로 실제 테이블 이름은 `menus`다.

**✅ 확인**

- 애플리케이션 시작 시 콘솔에 `Hibernate: create table menus (...)`가 출력된다.
- POST 응답에 `"id": 1` 이상의 숫자가 보인다.
- GET 응답에 `[{"id":1,"korName":"아메리카노","engName":"Americano","price":4500}]`이 보인다.
- psql에서 `SELECT * FROM menus;` 결과에 한 줄의 데이터가 보인다.

**🎓 코멘트**: `Hibernate: create table menus (...)`는 `ddl-auto: update`가 테이블을 만들었다는 증거다. POST 응답의 id는 PostgreSQL의 IDENTITY 컬럼이 자동 생성한 값이다. 데이터는 두 번 변환된다 — **JPA가 ResultSet을 `Menu` 객체로**, **Spring MVC(Jackson)가 `Menu` 객체를 JSON으로** 바꾼다.

> **추가 설명 — 콘솔에 찍힌 SQL을 읽어보자**: `show-sql`, `format_sql`을 켜 두었기 때문에 POST 호출 시 콘솔에 `insert into menus (eng_name, kor_name, price) values (?, ?, ?)`가, GET 호출 시 `select m1_0.id, m1_0.eng_name, ... from menus m1_0`가 찍힌다. 개발자가 한 줄도 쓰지 않은 SQL을 Hibernate가 엔티티 정보만 보고 만들어냈다는 것을 직접 확인할 수 있다. 이 SQL을 읽을 수 있어야 나중에 성능 문제나 예상과 다른 쿼리를 잡아낼 수 있다 — ORM을 써도 SQL 지식이 필요한 이유다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Connection refused` (curl) | 애플리케이션이 뜨지 않음 | `bootRun` 에러 로그 확인, 8080 포트 사용 중인지 확인 |
| `404 Not Found` | URL 경로 오류 | curl URL이 `/api/v1/admin/menus`인지 확인 |
| `500 Internal Server Error` | DB 연결 실패 또는 엔티티 매핑 오류 | 콘솔 스택 트레이스와 `application.yml`의 DB 설정 확인 |
| `psql: FATAL: database "ncafedb" does not exist` | 컨테이너에 DB가 없음 | 컨테이너를 다시 시작하거나 `createdb`로 DB 생성 |

**📝 핵심**: `ddl-auto: update`가 테이블을 자동 생성한다. POST로 저장하고 GET으로 조회하면 PostgreSQL에 데이터가 실제로 들어 있다.

## 마무리

1. `spring-boot-starter-data-jpa` 의존성 추가
2. `application.yml`로 DB와 JPA 설정. YAML은 들여쓰기로 계층을 표현
3. `@Entity` 클래스 작성. `@Id`와 `@GeneratedValue`로 PK 자동 생성
4. `JpaRepository<Menu, Long>`을 상속한 인터페이스 하나. 구현체 불필요
5. 컨트롤러에서 `MenuRepository`를 주입하고 `save`, `findAll` 직접 호출
6. 실행 후 curl로 POST/GET 호출, PostgreSQL에 저장·조회 확인
