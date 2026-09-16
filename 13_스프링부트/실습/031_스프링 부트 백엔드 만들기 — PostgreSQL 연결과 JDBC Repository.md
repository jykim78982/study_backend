---
tags: [웹, 스프링부트, Java, PostgreSQL, JDBC, 실습]
---

> 🔗 관련 노트: [[030_스프링 부트 백엔드 만들기 — ncafe 프로젝트의 첫 API]] · [[032_Next.js에서 스프링 부트 API 연동 — 메뉴 목록과 검색 폼 만들기 실습]]

# 스프링 부트 백엔드 만들기 — PostgreSQL 연결과 JDBC Repository

`ncafe/backend`가 목업 데이터 대신 PostgreSQL의 `menus` 테이블을 실제로 조회하도록, JDBC 드라이버 추가부터 `MenuRepository`·`JdbcMenuRepository` 작성, 쿼리 파라미터 기반 검색까지 연결한 실습이다. 아직 DI/IoC 컨테이너를 배우지 않았기 때문에, 이번 단계의 `MenuController`는 필요한 객체를 생성자 안에서 직접 `new`로 만든다 — DI를 배우면 이 방식은 곧 대체된다.

## 1. PostgreSQL JDBC 드라이버 추가

`pom.xml`의 `<dependencies>` 안에 PostgreSQL 드라이버를 추가한다.

```xml
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
    <scope>runtime</scope>
</dependency>
```

Spring Boot Starter Parent가 버전을 관리해주므로 `<version>`은 생략할 수 있다. 추가 후 `ncafe/backend`에서 의존성을 내려받는다.

```
cd ncafe/backend
mvn clean install
```

JDBC 드라이버는 데이터베이스 벤더(PostgreSQL)가 제공하는 자바 라이브러리로, 이게 없으면 자바 애플리케이션이 PostgreSQL 프로토콜로 통신할 수 없다. Spring JDBC는 이 드라이버를 감싸서 더 편하게 쓸 수 있게 해준다.

## 2. 데이터베이스 연결 정보 설정

`src/main/resources/application.properties`에 연결 정보를 추가한다.

```
spring.datasource.url=jdbc:postgresql://host:5432/dbname
spring.datasource.username=여기에 실제 계정
spring.datasource.password=여기에 실제 비밀번호
spring.datasource.driver-class-name=org.postgresql.Driver
```

`spring.datasource.*` 속성은 Spring Boot가 자동으로 `DataSource`를 만들 때 쓰는 값이다. 이 설정이 없으면 Spring Boot가 기본 H2 메모리 DB를 쓰려 하거나 오류가 난다.

## 3. `MenuRepository` — 인터페이스와 JDBC 구현체

인터페이스는 "데이터를 어떻게 조회할지"의 목록만 정의하고, 실제 SQL은 구현체가 담당한다.

```java
package com.newlecture.backend.repository;

import com.newlecture.backend.entity.Menu;
import java.util.List;

public interface MenuRepository {
    List<Menu> findAll();
    List<Menu> findByName(String name);
    List<Menu> findByCategory(Integer categoryId);
    List<Menu> findByPriceRange(
        Integer minPrice, Integer maxPrice);
}
```

```java
package com.newlecture.backend.repository;

import com.newlecture.backend.entity.Menu;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;

public class JdbcMenuRepository implements MenuRepository {

    private final JdbcTemplate jdbcTemplate;

    public JdbcMenuRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public List<Menu> findAll() {
        String sql = "SELECT id, kor_name, eng_name, "
            + "price, description, img_src, "
            + "category_id, create_time "
            + "FROM menus ORDER BY id";
        return jdbcTemplate.query(sql, new MenuRowMapper());
    }

    @Override
    public List<Menu> findByName(String name) {
        String sql = "SELECT id, kor_name, eng_name, "
            + "price, description, img_src, "
            + "category_id, create_time FROM menus "
            + "WHERE kor_name LIKE ? OR eng_name LIKE ?";
        String like = "%" + name + "%";
        return jdbcTemplate.query(
            sql, new MenuRowMapper(), like, like);
    }

    @Override
    public List<Menu> findByCategory(Integer categoryId) {
        String sql = "SELECT id, kor_name, eng_name, "
            + "price, description, img_src, "
            + "category_id, create_time FROM menus "
            + "WHERE category_id = ?";
        return jdbcTemplate.query(
            sql, new MenuRowMapper(), categoryId);
    }

    @Override
    public List<Menu> findByPriceRange(
            Integer minPrice, Integer maxPrice) {
        String sql = "SELECT id, kor_name, eng_name, "
            + "price, description, img_src, "
            + "category_id, create_time FROM menus "
            + "WHERE price BETWEEN ? AND ?";
        return jdbcTemplate.query(
            sql, new MenuRowMapper(), minPrice, maxPrice);
    }

    private static class MenuRowMapper
            implements RowMapper<Menu> {
        @Override
        public Menu mapRow(ResultSet rs, int rowNum)
                throws SQLException {
            Menu menu = new Menu();
            menu.setId(rs.getInt("id"));
            menu.setKorName(rs.getString("kor_name"));
            menu.setEngName(rs.getString("eng_name"));
            menu.setPrice(rs.getInt("price"));
            menu.setDescription(
                rs.getString("description"));
            menu.setImgSrc(rs.getString("img_src"));
            menu.setCategoryId(
                rs.getInt("category_id"));
            menu.setCreateTime(
                rs.getDate("create_time").toLocalDate());
            return menu;
        }
    }
}
```

`JdbcTemplate`은 Spring JDBC의 핵심 클래스로, `query()`에 SQL문과 `RowMapper`를 넘기면 결과셋을 자바 객체(`Menu`) 목록으로 변환해준다. `RowMapper`는 `ResultSet`의 한 행을 `Menu` 객체 하나로 매핑하는 역할만 담당한다.

`JdbcTemplate`을 쓰려면 `spring-boot-starter-jdbc` 의존성이 필요하다.

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-jdbc</artifactId>
</dependency>
```

## 4. `MenuController` — DI 없이 직접 조립하기

아직 `@Autowired`나 생성자 주입을 배우지 않았으므로, 컨트롤러의 생성자 안에서 `DataSourceProperties`로 `DataSource`를 만들고, 그 `DataSource`로 `JdbcTemplate`을 만들고, 그 `JdbcTemplate`으로 `JdbcMenuRepository`를 직접 조립한다.

```java
package com.newlecture.backend.controller;

import com.newlecture.backend.entity.Menu;
import com.newlecture.backend.repository.
    JdbcMenuRepository;
import com.newlecture.backend.repository.
    MenuRepository;
import org.springframework.boot.jdbc.autoconfigure.
    DataSourceProperties;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.
    GetMapping;
import org.springframework.web.bind.annotation.
    RequestMapping;
import org.springframework.web.bind.annotation.
    RequestParam;
import org.springframework.web.bind.annotation.
    RestController;

import javax.sql.DataSource;
import java.util.List;

@RestController
@RequestMapping("/api")
public class MenuController {

    private final MenuRepository menuRepository;

    public MenuController() {
        // DI를 배우지 않았으므로, 여기서 직접
        // 객체를 생성한다.
        // 실제 프로젝트에서는 @Autowired 또는
        // 생성자 주입을 사용한다.
        DataSourceProperties dataSourceProperties =
            new DataSourceProperties();
        // application.properties 에서 값을 읽어오는
        // 대신, 여기서는 간단히 JdbcTemplate을
        // 생성한다.
        // 더 정확한 방법은 다음 단계에서 설명한다.
        this.menuRepository = new JdbcMenuRepository(
            new JdbcTemplate(createDataSource()));
    }

    private DataSource createDataSource() {
        // application.properties 값을 직접 읽어오는
        // 대신, Spring이 자동으로 생성한 DataSource를
        // 가져오는 것이 더 좋다.
        // 하지만 DI를 배우지 않았으므로, 여기서는
        // 임시로 JdbcTemplate을 생성한다.
        // 실제로는 Spring Boot가 application.properties를
        // 읽고 DataSource를 자동 생성한다.
        // 따라서 이 메서드는 삭제하고, 생성자에서
        // JdbcTemplate을 주입받는 방식으로 변경해야
        // 한다.
        // 하지만 현재 단계에서는 JdbcTemplate을 직접
        // 생성해야 한다.

        // Spring Boot가 application.properties를 읽고
        // DataSource를 자동 생성하므로, 우리는
        // JdbcTemplate을 직접 생성할 때 DataSource를
        // 직접 만들어야 한다.
        DataSourceProperties props =
            new DataSourceProperties();
        props.setUrl(
            "jdbc:postgresql://host:5432/dbname");
        props.setUsername("여기에 실제 계정");
        props.setPassword("여기에 실제 비밀번호");
        props.setDriverClassName(
            "org.postgresql.Driver");
        return props.initializeDataSourceBuilder()
            .build();
    }

    @GetMapping("/menus")
    public List<Menu> list(
            @RequestParam(required = false) String name,
            @RequestParam(required = false)
                Integer category,
            @RequestParam(required = false)
                Integer minPrice,
            @RequestParam(required = false)
                Integer maxPrice) {

        if (name != null && !name.isEmpty()) {
            return menuRepository.findByName(name);
        } else if (category != null) {
            return menuRepository.findByCategory(
                category);
        } else if (minPrice != null
                && maxPrice != null) {
            return menuRepository.findByPriceRange(
                minPrice, maxPrice);
        } else {
            return menuRepository.findAll();
        }
    }
}
```

`DataSourceProperties`의 패키지 경로(`org.springframework.boot.jdbc.autoconfigure`)는 Spring Boot 버전에 따라 달라질 수 있다 — import 오류가 나면 IDE의 자동 완성으로 실제 설치된 버전의 경로를 확인한다.

`@RequestParam(required = false)`로 받은 `name`/`category`/`minPrice`·`maxPrice` 중 어떤 값이 들어왔는지에 따라 호출할 `Repository` 메서드를 분기한다. 쿼리 파라미터는 URL의 `?` 뒤에 `key=value` 형태로 오는 값이며, `required = false`는 그 파라미터가 없어도 오류가 나지 않게 한다.

## 5. 실행과 확인

```
cd ncafe/backend
mvn spring-boot:run
```

`Tomcat started on port(s): 8080`이 뜨면 성공이다. Postman에서 `GET http://localhost:8080/api/menus`를 요청하면, 이제 목업 배열이 아니라 PostgreSQL `menus` 테이블의 실제 데이터가 JSON으로 온다.

검색 조건도 쿼리 파라미터로 함께 테스트한다.

| 검색 조건 | 요청 예시 |
|---|---|
| 이름 | `GET /api/menus?name=아메리카노` |
| 카테고리 | `GET /api/menus?category=1` |
| 가격 범위 | `GET /api/menus?minPrice=4000&maxPrice=5000` |

## 6. 자주 하는 실수

| 증상 | 원인 | 해결 |
|---|---|---|
| `Could not resolve dependencies` | 인터넷 연결 문제 또는 Maven 설정 오류 | `mvn -U clean install`로 강제 업데이트 |
| `cannot find symbol: class JdbcTemplate` | `spring-boot-starter-jdbc` 의존성 누락 | `pom.xml`에 해당 의존성 추가 |
| `Access denied for user` | 사용자명·비밀번호 오류 | 실제 계정 정보로 교체 |
| `Connection refused` | 네트워크·방화벽 문제로 DB 서버 접근 불가 | DB 서버 접근 가능 여부 확인 |
| 500 Internal Server Error | DB 연결 실패 또는 SQL 오류 | 터미널의 스택 트레이스 확인 |
| 빈 배열 반환 | 테이블이 비어 있거나 검색 조건에 맞는 데이터가 없음 | `SELECT * FROM menus;`로 데이터 존재 확인 |

## 7. 정리

| 단계 | 내용 |
|---|---|
| 1 | `pom.xml`에 PostgreSQL 드라이버(`runtime` scope) 추가 |
| 2 | `application.properties`에 `spring.datasource.*` 연결 정보 설정 |
| 3 | `MenuRepository` 인터페이스 + `JdbcMenuRepository`(`JdbcTemplate`, `RowMapper`) 구현 |
| 4 | `spring-boot-starter-jdbc` 의존성 추가 |
| 5 | `MenuController`에서 DI 없이 `DataSource`→`JdbcTemplate`→`Repository`를 직접 조립 |
| 6 | Postman으로 `GET /api/menus`와 쿼리 파라미터 검색 확인 |

이번 조립 방식(컨트롤러에서 `new`로 직접 생성)은 DI/IoC 컨테이너를 배우기 전까지의 임시 방식이다. DI를 배우면 `DataSource`·`JdbcTemplate`·`Repository`를 스프링 컨테이너가 자동으로 만들어 주입해주는 방식으로 바뀐다.
