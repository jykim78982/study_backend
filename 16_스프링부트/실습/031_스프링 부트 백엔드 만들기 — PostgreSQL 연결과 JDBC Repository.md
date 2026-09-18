---
tags: [웹, 스프링부트, Java, PostgreSQL, JDBC, 실습]
---

> 🔗 관련 노트: [[030_스프링 부트 백엔드 만들기 — ncafe 프로젝트의 첫 API]] · [[032_Next.js 실무형 메뉴 목록 페이지 만들기 — SSR, 상태, 이벤트, 컴포넌트 분리 실습]] · [[033_ncafe 메뉴·카테고리 API 만들기 — DTO와 DI]]

# 스프링 부트 백엔드 만들기 — PostgreSQL 연결과 JDBC Repository

**대상**: 이전 따라하기에서 `ncafe/backend` 프로젝트를 생성하고 목업 데이터로 `/api/menus` API를 만든 학생

**목표**: PostgreSQL 데이터베이스에 연결하고, Spring JDBC를 이용해 `MenuRepository`를 만들어 실제 DB 데이터를 조회하는 API를 만든다

**완성물**: `ncafe/backend` 프로젝트에서 `GET /api/menus` 요청 시 PostgreSQL의 `menus` 테이블 데이터를 JSON으로 반환하는 상태

**필수 준비물**

- Java 17 이상(JDK 설치 확인: `java -version`)
- Maven 3.8 이상
- PostgreSQL 데이터베이스 접근 권한
- Postman 또는 브라우저

**전제**

- `ncafe/backend` 프로젝트는 이미 생성되어 있고, `Menu` 엔티티와 `MenuController`가 존재한다([[030_스프링 부트 백엔드 만들기 — ncafe 프로젝트의 첫 API]]).
- `menus` 테이블은 이미 PostgreSQL에 존재한다고 가정한다.
- 아직 DI/IoC 컨테이너 개념을 배우지 않았으므로, Repository 객체는 컨트롤러에서 `new`로 직접 생성한다.

## 1. PostgreSQL JDBC 드라이버 추가

Spring JDBC가 PostgreSQL과 통신하려면 JDBC 드라이버가 필요하다. `pom.xml`에 `postgresql` 의존성을 추가한다.

### 1-1. `pom.xml` 열기

VSCode에서 `ncafe/backend/pom.xml` 파일을 연다.

### 1-2. `dependencies` 태그 안에 `postgresql` 추가

`<dependencies>` 태그 안에 아래 코드를 추가한다.

파일: `pom.xml`

```xml
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
    <scope>runtime</scope>
</dependency>
```

참고: Spring Boot Starter Parent가 버전 관리를 해주므로 `<version>` 태그를 생략할 수 있다.

### 1-3. Maven 의존성 다운로드

터미널에서 `ncafe/backend` 폴더로 이동하고 실행한다.

```
cd ncafe/backend
mvn clean install
```

Windows/Mac 공통: 처음 실행 시 인터넷에서 의존성을 다운로드하므로 시간이 걸릴 수 있다.

**✅ 확인**

- 터미널에 `BUILD SUCCESS`가 출력된다.
- `~/.m2/repository/org/postgresql/postgresql/` 폴더에 드라이버 jar 파일이 다운로드되었는지 확인한다.

**🎓 newlec 쌤의 코멘트**

JDBC 드라이버는 데이터베이스 벤더(여기서는 PostgreSQL)가 제공하는 Java 라이브러리다. 이 드라이버가 없으면 Java 애플리케이션이 PostgreSQL 프로토콜로 통신할 수 없다. Spring JDBC는 이 드라이버를 추상화해서 더 편하게 사용할 수 있게 해주는 도구다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Could not resolve dependencies` | 인터넷 연결 문제 또는 Maven 설정 오류 | `mvn -U clean install`로 강제 업데이트 시도 |
| `postgresql`이 runtime scope가 아님 | `scope` 태그 누락 | `<scope>runtime</scope>` 추가 |

**📝 이 단계의 핵심**

- PostgreSQL JDBC 드라이버는 `runtime` scope로 추가한다.
- 의존성 추가 후 `mvn clean install`로 로컬 저장소에 다운로드한다.

## 2. 데이터베이스 연결 정보 설정

Spring JDBC가 데이터베이스에 연결하려면 주소, 포트, 사용자명, 비밀번호를 설정해야 한다. `application.properties` 파일을 수정한다.

### 2-1. `application.properties` 열기

파일: `src/main/resources/application.properties`

### 2-2. 데이터베이스 연결 정보 추가

파일 끝에 아래 내용을 추가한다.

```
spring.datasource.url=jdbc:postgresql://host:5432/dbname
spring.datasource.username=여기에 실제 계정
spring.datasource.password=여기에 실제 비밀번호
spring.datasource.driver-class-name=org.postgresql.Driver
```

주의: `여기에 실제 계정`과 `여기에 실제 비밀번호`는 실제 계정에 맞게 교체한다.

**✅ 확인**

- `application.properties` 파일에 4줄의 데이터베이스 설정이 추가되었다.
- 파일 저장 후 VSCode에서 저장 아이콘이 사라졌는지 확인한다.

**🎓 newlec 쌤의 코멘트**

`spring.datasource.*` 속성은 Spring Boot가 자동으로 데이터 소스(`DataSource`)를 생성할 때 사용한다. `url`은 JDBC 연결 문자열로, 프로토콜(`jdbc:postgresql`), 호스트, 포트, 데이터베이스 이름을 포함한다. 이 설정이 없으면 Spring Boot가 기본 H2 메모리 DB를 사용하려 하거나 에러가 발생한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Access denied for user` | 사용자명/비밀번호 오류 | 실제 계정 정보로 교체 |
| `Connection refused` | 네트워크 방화벽 또는 서버 접근 불가 | 데이터베이스 서버에 접근 가능한지 확인 |
| `Unknown database` | 데이터베이스 이름 오타 | 실제 DB 이름과 대소문자 일치 확인 |

**📝 이 단계의 핵심**

- `spring.datasource.url`은 `jdbc:postgresql://host:port/dbname` 형식이다.
- 사용자명과 비밀번호는 실제 계정에 맞게 반드시 교체해야 한다.

## 3. `MenuRepository` — 인터페이스와 JDBC 구현체

이제 실제 데이터베이스에서 데이터를 조회하는 `MenuRepository`를 만든다. 아직 DI를 배우지 않았으므로, 인터페이스와 구현체를 직접 만들고 컨트롤러에서 `new`로 생성하는 방식으로 진행한다.

### 3-1. `MenuRepository` 인터페이스 만들기

파일: `src/main/java/com/newlecture/backend/repository/MenuRepository.java`

```java
package com.newlecture.backend.repository;

import com.newlecture.backend.entity.Menu;
import java.util.List;

public interface MenuRepository {
    List<Menu> findAll();
    List<Menu> findByName(String name);
    List<Menu> findByCategory(Integer categoryId);
    List<Menu> findByPriceRange(Integer minPrice, Integer maxPrice);
}
```

설명: 인터페이스는 "데이터를 어떻게 조회할지"를 정의한다. 구현체는 나중에 JDBC로 채운다.

### 3-2. `JdbcMenuRepository` 구현체 만들기

파일: `src/main/java/com/newlecture/backend/repository/JdbcMenuRepository.java`

```java
package com.newlecture.backend.repository;

import com.newlecture.backend.entity.Menu;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDate;
import java.util.List;

public class JdbcMenuRepository implements MenuRepository {

    private final JdbcTemplate jdbcTemplate;

    public JdbcMenuRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public List<Menu> findAll() {
        String sql = "SELECT id, kor_name, eng_name, price, description, img_src, category_id, create_time FROM menus ORDER BY id";
        return jdbcTemplate.query(sql, new MenuRowMapper());
    }

    @Override
    public List<Menu> findByName(String name) {
        String sql = "SELECT id, kor_name, eng_name, price, description, img_src, category_id, create_time FROM menus WHERE kor_name LIKE ? OR eng_name LIKE ?";
        return jdbcTemplate.query(sql, new MenuRowMapper(), "%" + name + "%", "%" + name + "%");
    }

    @Override
    public List<Menu> findByCategory(Integer categoryId) {
        String sql = "SELECT id, kor_name, eng_name, price, description, img_src, category_id, create_time FROM menus WHERE category_id = ?";
        return jdbcTemplate.query(sql, new MenuRowMapper(), categoryId);
    }

    @Override
    public List<Menu> findByPriceRange(Integer minPrice, Integer maxPrice) {
        String sql = "SELECT id, kor_name, eng_name, price, description, img_src, category_id, create_time FROM menus WHERE price BETWEEN ? AND ?";
        return jdbcTemplate.query(sql, new MenuRowMapper(), minPrice, maxPrice);
    }

    private static class MenuRowMapper implements RowMapper<Menu> {
        @Override
        public Menu mapRow(ResultSet rs, int rowNum) throws SQLException {
            Menu menu = new Menu();
            menu.setId(rs.getInt("id"));
            menu.setKorName(rs.getString("kor_name"));
            menu.setEngName(rs.getString("eng_name"));
            menu.setPrice(rs.getInt("price"));
            menu.setDescription(rs.getString("description"));
            menu.setImgSrc(rs.getString("img_src"));
            menu.setCategoryId(rs.getInt("category_id"));
            menu.setCreateTime(rs.getDate("create_time").toLocalDate());
            return menu;
        }
    }
}
```

주의: 이 클래스는 아직 `JdbcTemplate`을 주입받지 못한다. 다음 단계에서 컨트롤러에서 직접 생성하도록 수정한다.

**✅ 확인**

- `MenuRepository.java` 인터페이스가 생성되었다.
- `JdbcMenuRepository.java` 구현체가 생성되었다.
- (아직 실행은 안 함)

**🎓 newlec 쌤의 코멘트**

`JdbcTemplate`은 Spring JDBC의 핵심 클래스다. `query()` 메서드에 SQL 문과 `RowMapper`를 전달하면, 결과셋을 Java 객체(`Menu`)로 변환해준다. `RowMapper`는 `ResultSet`의 한 행을 `Menu` 객체로 매핑하는 역할을 한다. 아직 DI를 배우지 않았으므로, `JdbcTemplate`은 컨트롤러에서 직접 생성해서 전달해야 한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `cannot find symbol: class JdbcTemplate` | `spring-boot-starter-jdbc` 의존성 누락 | `pom.xml`에 `spring-boot-starter-jdbc` 추가 |
| `RowMapper` 인터페이스 구현 오류 | `mapRow` 메서드 시그니처 불일치 | `public Menu mapRow(ResultSet rs, int rowNum) throws SQLException`으로 정확히 작성 |

**📝 이 단계의 핵심**

- `JdbcTemplate.query()`는 SQL과 `RowMapper`를 받아 `List`를 반환한다.
- `RowMapper`는 `ResultSet` 행을 Java 객체로 변환하는 함수형 인터페이스다.

## 4. `spring-boot-starter-jdbc` 의존성 추가

`JdbcTemplate`을 사용하려면 `spring-boot-starter-jdbc` 의존성이 필요하다.

### 4-1. `pom.xml` 수정

파일: `pom.xml`

`<dependencies>` 안에 아래 코드를 추가한다.

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-jdbc</artifactId>
</dependency>
```

### 4-2. Maven 의존성 다운로드

```
mvn clean install
```

**✅ 확인**

- 터미널에 `BUILD SUCCESS`가 출력된다.
- `JdbcTemplate` 클래스가 더 이상 빨간색 에러가 아닌지 확인한다.

**🎓 newlec 쌤의 코멘트**

`spring-boot-starter-jdbc`는 `JdbcTemplate`, `DataSource` 등 JDBC 관련 클래스들을 한 번에 가져오는 스타터다. 이 의존성이 없으면 `JdbcTemplate`을 import할 때 에러가 발생한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `JdbcTemplate` import 에러 | `spring-boot-starter-jdbc` 누락 | 위 코드 추가 후 `mvn clean install` |

**📝 이 단계의 핵심**

- `spring-boot-starter-jdbc`는 `JdbcTemplate`을 사용할 때 필수다.

## 5. `MenuController` — DI 없이 직접 조립하기

이제 `MenuController`를 수정해서 `JdbcMenuRepository`를 직접 생성하고, 실제 DB 데이터를 조회하도록 바꾼다.

### 5-1. `MenuController.java` 수정

파일: `src/main/java/com/newlecture/backend/controller/MenuController.java`

```java
package com.newlecture.backend.controller;

import com.newlecture.backend.entity.Menu;
import com.newlecture.backend.repository.JdbcMenuRepository;
import com.newlecture.backend.repository.MenuRepository;
import org.springframework.boot.jdbc.autoconfigure.DataSourceProperties;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.sql.DataSource;
import java.util.List;

@RestController
@RequestMapping("/api")
public class MenuController {

    private final MenuRepository menuRepository;

    public MenuController() {
        // DI를 배우지 않았으므로, 여기서 직접 객체를 생성한다.
        // 실제 프로젝트에서는 @Autowired 또는 생성자 주입을 사용한다.
        this.menuRepository = new JdbcMenuRepository(new JdbcTemplate(createDataSource()));
    }

    private DataSource createDataSource() {
        // application.properties 값을 직접 읽어오는 대신, Spring이 자동으로
        // 생성한 DataSource를 가져오는 것이 더 좋다.
        // 하지만 DI를 배우지 않았으므로, 여기서는 임시로 JdbcTemplate을 생성한다.
        // 다음 단계(DI/IoC)를 배우면 이 메서드는 삭제하고, 생성자에서
        // JdbcTemplate을 주입받는 방식으로 변경한다.
        DataSourceProperties props = new DataSourceProperties();
        props.setUrl("jdbc:postgresql://host:5432/dbname");
        props.setUsername("여기에 실제 계정");
        props.setPassword("여기에 실제 비밀번호");
        props.setDriverClassName("org.postgresql.Driver");
        return props.initializeDataSourceBuilder().build();
    }

    @GetMapping("/menus")
    public List<Menu> list(
            @RequestParam(required = false) String name,
            @RequestParam(required = false) Integer category,
            @RequestParam(required = false) Integer minPrice,
            @RequestParam(required = false) Integer maxPrice) {

        if (name != null && !name.isEmpty()) {
            return menuRepository.findByName(name);
        } else if (category != null) {
            return menuRepository.findByCategory(category);
        } else if (minPrice != null && maxPrice != null) {
            return menuRepository.findByPriceRange(minPrice, maxPrice);
        } else {
            return menuRepository.findAll();
        }
    }
}
```

주의: 위 코드는 DI를 배우지 않은 상태에서의 임시 구현이다. `createDataSource()` 메서드는 `application.properties` 값을 하드코딩하고 있다. 다음 단계([[033_ncafe 메뉴·카테고리 API 만들기 — DTO와 DI]])에서 더 깔끔한 방식으로 수정한다. `DataSourceProperties`의 패키지 경로(`org.springframework.boot.jdbc.autoconfigure`)는 Spring Boot 버전에 따라 달라질 수 있다 — import 오류가 나면 IDE의 자동 완성으로 실제 설치된 버전의 경로를 확인한다.

**✅ 확인**

- `MenuController.java` 파일이 수정되었다.
- 컴파일 에러가 없으면 성공이다.

**🎓 newlec 쌤의 코멘트**

아직 DI를 배우지 않았으므로, `JdbcTemplate`을 직접 생성해야 한다. `DataSource`는 데이터베이스 연결을 관리하는 객체다. `JdbcTemplate`은 `DataSource`를 받아 SQL을 실행한다. 지금은 `application.properties` 값을 코드에 하드코딩했지만, 나중에 DI를 배우면 Spring이 자동으로 이 값을 읽어와서 `JdbcTemplate`을 생성해준다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `NullPointerException` | `JdbcTemplate`이 `null` | `createDataSource()`가 정상적으로 작동하는지 확인 |
| `Connection refused` | DB 연결 정보 오류 | `createDataSource()`의 URL, username, password 확인 |

**📝 이 단계의 핵심**

- DI를 배우지 않은 상태에서는 `JdbcTemplate`을 직접 생성해야 한다.
- `DataSource`는 데이터베이스 연결 정보를 포함한다.

## 6. 실행과 확인

이제 서버를 실행하고, Postman에서 실제 DB 데이터를 조회하는지 테스트한다.

### 6-1. 서버 실행

터미널에서 실행한다.

```
cd ncafe/backend
mvn spring-boot:run
```

Windows/Mac 공통: 서버가 정상적으로 시작되면 `Tomcat started on port(s): 8080`이 출력된다.

### 6-2. Postman에서 `GET /api/menus` 요청

Postman에서 `GET http://localhost:8080/api/menus`를 요청한다.

### 6-3. 응답 확인

Postman에서 JSON 배열이 반환되는지 확인한다.

```json
[
  {
    "id": 1,
    "korName": "아메리카노",
    "engName": "Americano",
    "price": 4500,
    "description": "진한 에스프레소와 물의 조화",
    "imgSrc": "/images/americano.png",
    "categoryId": 1,
    "createTime": "2026-09-15"
  },
  ...
]
```

**✅ 확인**

- Postman에서 200 OK 상태 코드가 보인다.
- Body에 PostgreSQL의 `menus` 테이블에서 조회된 데이터가 JSON 배열로 보인다.
- 데이터가 목업 데이터가 아니라 실제 DB 데이터인지 확인한다.

**🎓 newlec 쌤의 코멘트**

이제 API가 실제 데이터베이스에서 데이터를 조회한다. `JdbcTemplate`이 SQL을 실행하고, `RowMapper`가 결과를 `Menu` 객체로 변환하며, `@RestController`가 이를 JSON으로 변환한다. 이 흐름이 Spring JDBC의 기본 동작 방식이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| 500 Internal Server Error | DB 연결 실패 또는 SQL 오류 | 터미널에서 스택 트레이스 확인 |
| 빈 배열 반환 | `menus` 테이블이 비어 있음 | PostgreSQL에서 `SELECT * FROM menus;`로 데이터 존재 확인 |

**📝 이 단계의 핵심**

- 서버 실행 후 Postman으로 API를 테스트한다.
- 실제 DB 데이터가 JSON으로 반환되면 성공이다.

## 7. 검색 API 테스트

이제 검색 API를 테스트한다. Postman에서 쿼리 파라미터를 추가해서 다양한 조건으로 메뉴를 검색해본다.

### 7-1. 이름으로 검색

`GET http://localhost:8080/api/menus?name=아메리카노`를 요청한다.

### 7-2. 카테고리로 검색

`GET http://localhost:8080/api/menus?category=1`을 요청한다.

### 7-3. 가격 범위로 검색

`GET http://localhost:8080/api/menus?minPrice=4000&maxPrice=5000`을 요청한다.

**✅ 확인**

- 각 요청에 따라 필터링된 메뉴 목록이 JSON 배열로 반환된다.
- 이름 검색 시 `kor_name` 또는 `eng_name`에 해당 이름이 포함된 메뉴만 반환된다.
- 카테고리 검색 시 `category_id`가 일치하는 메뉴만 반환된다.
- 가격 범위 검색 시 `price`가 범위 안에 있는 메뉴만 반환된다.

**🎓 newlec 쌤의 코멘트**

쿼리 파라미터는 URL의 `?` 뒤에 `key=value` 형식으로 전달된다. `@RequestParam` 애노테이션이 이 값을 Java 메서드의 파라미터로 바인딩한다. `required = false`는 해당 파라미터가 없어도 에러가 안 나게 한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| 400 Bad Request | 쿼리 파라미터 형식 오류 | URL 인코딩 확인(특히 한글) |
| 빈 배열 반환 | 조건에 맞는 데이터가 없음 | PostgreSQL에서 직접 SQL로 확인 |

**📝 이 단계의 핵심**

- 쿼리 파라미터는 `@RequestParam`으로 바인딩한다.
- 다양한 조건으로 데이터를 필터링할 수 있다.

## 정리

1단계: `pom.xml`에 PostgreSQL 드라이버(`runtime` scope)를 추가한다.
2단계: `application.properties`에 `spring.datasource.*` 연결 정보를 설정한다.
3단계: `MenuRepository` 인터페이스와 `JdbcMenuRepository`(`JdbcTemplate`, `RowMapper`)를 구현한다.
4단계: `spring-boot-starter-jdbc` 의존성을 추가한다.
5단계: `MenuController`에서 DI 없이 `DataSource`→`JdbcTemplate`→`Repository`를 직접 조립한다.
6단계: 서버를 실행하고 Postman으로 `GET /api/menus`를 확인한다.
7단계: 쿼리 파라미터(이름·카테고리·가격 범위)로 검색 API를 테스트한다.

이번 조립 방식(컨트롤러에서 `new`로 직접 생성)은 DI/IoC 컨테이너를 배우기 전까지의 임시 방식이다. DI를 배우면 `DataSource`·`JdbcTemplate`·`Repository`를 스프링 컨테이너가 자동으로 만들어 주입해주는 방식으로 바뀐다([[033_ncafe 메뉴·카테고리 API 만들기 — DTO와 DI]] 참고).
