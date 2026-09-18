---
tags: [웹, 스프링부트, Java, PostgreSQL, JDBC, DTO, DI, 실습]
---

> 🔗 관련 노트: [[030_스프링 부트 백엔드 만들기 — ncafe 프로젝트의 첫 API]] · [[031_스프링 부트 백엔드 만들기 — PostgreSQL 연결과 JDBC Repository]] · [[065_스프링의 정체성 — DI 컨테이너, IoC, 인터페이스와 병렬 개발]]

# ncafe 메뉴·카테고리 API 만들기 — DTO와 DI

[[031_스프링 부트 백엔드 만들기 — PostgreSQL 연결과 JDBC Repository]]에서는 아직 DI를 배우지 않아 컨트롤러에서 `DataSource`·`JdbcTemplate`을 직접 `new`로 조립하고, `Menu` 엔티티를 그대로 컨트롤러가 반환했다. 이번 실습은 그 두 가지를 모두 바로잡는다 — 엔티티(`Category`, `Menu`)와 화면 전용 DTO(`CategoryDTO`, `MenuSummaryDTO`)를 분리하고, `@Autowired`로 `Repository`를 주입받아 `GET /api/categories`·`GET /api/menus`가 프론트엔드 `MenuCard`가 요구하는 형태의 JSON을 반환하도록 만든다.

## 0. 준비물

- Java 17 이상, Spring Boot 3.x, PostgreSQL 14+
- `ncafe` 데이터베이스에 `categories`, `menus`(그리고 `favoriteCount` 집계에 쓰이는 `favorites`) 테이블이 이미 만들어져 있어야 한다.
- `application.properties`에 데이터베이스 접속 정보가 설정되어 있어야 한다.

## 1. 프로젝트 폴더 구조 만들기

패키지 루트: `src/main/java/com/newlecture/backend/`

```
mkdir -p src/main/java/com/newlecture/backend/{controller,entity,repository,repository/jdbc,dto}
```

Windows PowerShell에서는 `mkdir -p` 옵션이 없으므로, 폴더를 하나씩 만들거나 `New-Item -ItemType Directory -Force -Path`를 사용한다.

```powershell
New-Item -ItemType Directory -Force -Path src/main/java/com/newlecture/backend/controller
New-Item -ItemType Directory -Force -Path src/main/java/com/newlecture/backend/entity
New-Item -ItemType Directory -Force -Path src/main/java/com/newlecture/backend/repository
New-Item -ItemType Directory -Force -Path src/main/java/com/newlecture/backend/repository/jdbc
New-Item -ItemType Directory -Force -Path src/main/java/com/newlecture/backend/dto
```

다른 디렉터리에서 실행하면 엉뚱한 위치에 폴더 구조가 통째로 새로 생겨버릴 수 있으므로, 신경 쓰인다면 IDE에서 직접 폴더를 만들어도 된다.

`application.properties`(`src/main/resources/application.properties`)에는 데이터베이스 접속 정보를 채운다.

```
spring.datasource.url=jdbc:postgresql://host:5432/dbname
spring.datasource.username=여기에 실제 계정
spring.datasource.password=여기에 실제 비밀번호
spring.datasource.driver-class-name=org.postgresql.Driver
```

**정리**

- Spring Boot 프로젝트는 `controller`(HTTP 요청 처리), `entity`(테이블과 1:1 대응), `repository`(데이터 접근 로직), `dto`(화면에 보여줄 데이터) 패키지로 나눈다.
- 이 구조를 지켜두면 나중에 서비스 계층(`service`)을 추가할 때도 기존 파일을 옮길 필요가 없다.

## 2. 엔티티 — 데이터베이스 테이블의 "Java 버전"

엔티티는 데이터베이스 테이블과 **1:1로 대응**하는 클래스다. 화면에 보여줄 때만 필요한 필드(`categoryName`, `count` 등 테이블에 없는 값)는 절대 엔티티에 넣지 않는다 — 그런 값은 3단계의 DTO가 담당한다.

### 2-1. `Category` 엔티티

`src/main/java/com/newlecture/backend/entity/Category.java`

```java
package com.newlecture.backend.entity;

public class Category {
    private Long id;
    private String name;
    private Integer sortOrder;

    public Category() {}

    public Category(Long id, String name, Integer sortOrder) {
        this.id = id;
        this.name = name;
        this.sortOrder = sortOrder;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public Integer getSortOrder() { return sortOrder; }
    public void setSortOrder(Integer sortOrder) { this.sortOrder = sortOrder; }
}
```

`categories` 테이블의 `id`, `name`, `sort_order` 열이 그대로 `id`, `name`, `sortOrder` 필드가 된다(스네이크 케이스 → 카멜 케이스).

### 2-2. `Menu` 엔티티 (기존 파일 덮어쓰기)

`src/main/java/com/newlecture/backend/entity/Menu.java`

```java
package com.newlecture.backend.entity;

import java.time.LocalDateTime;

public class Menu {
    private Long id;
    private String slug;
    private Long categoryId;
    private String korName;
    private String engName;
    private Integer price;
    private String description;
    private String detail;
    private String status;
    private Boolean isNew;
    private String imgSrc;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public Menu() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getSlug() { return slug; }
    public void setSlug(String slug) { this.slug = slug; }
    public Long getCategoryId() { return categoryId; }
    public void setCategoryId(Long categoryId) { this.categoryId = categoryId; }
    public String getKorName() { return korName; }
    public void setKorName(String korName) { this.korName = korName; }
    public String getEngName() { return engName; }
    public void setEngName(String engName) { this.engName = engName; }
    public Integer getPrice() { return price; }
    public void setPrice(Integer price) { this.price = price; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public String getDetail() { return detail; }
    public void setDetail(String detail) { this.detail = detail; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Boolean getIsNew() { return isNew; }
    public void setIsNew(Boolean isNew) { this.isNew = isNew; }
    public String getImgSrc() { return imgSrc; }
    public void setImgSrc(String imgSrc) { this.imgSrc = imgSrc; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
```

**정리**

- 엔티티는 데이터베이스 테이블과 1:1로 대응하는 클래스다.
- 엔티티에는 화면 전용 필드(`categoryName` 등)를 넣지 않는다.

## 3. DTO — 화면에 필요한 필드만 담기

DTO(Data Transfer Object)는 "이 화면에는 이 데이터만 보여줘"라고 말하는 클래스다. 엔티티와 달리 여러 테이블의 값을 합치거나, 계산된 값(개수 등)을 담을 수 있다.

> 원래는 Lombok으로 생성자·Getter/Setter를 줄이는 게 일반적이지만, 환경에 따라 Lombok 설정 오류가 날 수 있어 이번 실습은 직접 코딩한다. Lombok 사용이 익숙하면 그걸 써도 무방하다.

### 3-1. `CategoryDTO`

`src/main/java/com/newlecture/backend/dto/CategoryDTO.java`

```java
package com.newlecture.backend.dto;

public class CategoryDTO {
    private Long id;
    private String name;
    private Integer count;

    public CategoryDTO() {}

    public CategoryDTO(Long id, String name, Integer count) {
        this.id = id;
        this.name = name;
        this.count = count;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public Integer getCount() { return count; }
    public void setCount(Integer count) { this.count = count; }
}
```

### 3-2. `MenuSummaryDTO`

`src/main/java/com/newlecture/backend/dto/MenuSummaryDTO.java`

```java
package com.newlecture.backend.dto;

import java.time.LocalDateTime;

public class MenuSummaryDTO {
    private Long id;
    private String slug;
    private String korName;
    private String engName;
    private Integer price;
    private Long categoryId;
    private String categoryName;
    private String status;
    private Boolean isNew;
    private String imgSrc;
    private Integer favoriteCount;
    private LocalDateTime createdAt;

    public MenuSummaryDTO() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getSlug() { return slug; }
    public void setSlug(String slug) { this.slug = slug; }
    public String getKorName() { return korName; }
    public void setKorName(String korName) { this.korName = korName; }
    public String getEngName() { return engName; }
    public void setEngName(String engName) { this.engName = engName; }
    public Integer getPrice() { return price; }
    public void setPrice(Integer price) { this.price = price; }
    public Long getCategoryId() { return categoryId; }
    public void setCategoryId(Long categoryId) { this.categoryId = categoryId; }
    public String getCategoryName() { return categoryName; }
    public void setCategoryName(String categoryName) { this.categoryName = categoryName; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Boolean getIsNew() { return isNew; }
    public void setIsNew(Boolean isNew) { this.isNew = isNew; }
    public String getImgSrc() { return imgSrc; }
    public void setImgSrc(String imgSrc) { this.imgSrc = imgSrc; }
    public Integer getFavoriteCount() { return favoriteCount; }
    public void setFavoriteCount(Integer favoriteCount) { this.favoriteCount = favoriteCount; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
```

`MenuSummaryDTO`의 `categoryName`은 `menus` 테이블에 없는 값이다 — `categories` 테이블에서 가져와 `menus`의 데이터와 합쳐서 채운다(5·6단계의 SQL `JOIN`이 이 역할을 한다). `favoriteCount`도 마찬가지로 `favorites` 테이블을 세어서 만든 계산값이다.

**정리**

- DTO는 화면에 필요한 필드만 골라 담는 클래스다.
- 데이터베이스에 없는 필드(`categoryName`, `count`, `favoriteCount`)는 DTO에서만 다룬다.

## 4. Repository 인터페이스 — "무엇을 할 수 있는지"만 정의

Repository 인터페이스는 계약서다. "이 데이터를 이렇게 가져와줘"라는 메서드 시그니처만 정의하고, 실제 구현(JDBC냐 JPA냐)은 숨긴다. 이렇게 해두면 나중에 구현 기술을 바꿔도 인터페이스를 쓰는 쪽(컨트롤러) 코드는 그대로 유지된다.

### 4-1. `CategoryRepository`

`src/main/java/com/newlecture/backend/repository/CategoryRepository.java`

```java
package com.newlecture.backend.repository;

import com.newlecture.backend.dto.CategoryDTO;
import java.util.List;

public interface CategoryRepository {
    List<CategoryDTO> findAllWithCount();
}
```

### 4-2. `MenuRepository` (기존 파일과 다르면 덮어쓰기)

`src/main/java/com/newlecture/backend/repository/MenuRepository.java`

```java
package com.newlecture.backend.repository;

import com.newlecture.backend.dto.MenuSummaryDTO;
import java.util.List;

public interface MenuRepository {
    List<MenuSummaryDTO> findAll();
    List<MenuSummaryDTO> findByCategory(Long categoryId);
    List<MenuSummaryDTO> findByName(String name);
    List<MenuSummaryDTO> findByPriceRange(Integer minPrice, Integer maxPrice);
}
```

[[031_스프링 부트 백엔드 만들기 — PostgreSQL 연결과 JDBC Repository]]의 `MenuRepository`는 `Menu` 엔티티를 반환했지만, 이번에는 `MenuSummaryDTO`를 반환한다 — 컨트롤러가 클라이언트에 응답할 형태를 Repository 계약 단계에서부터 명확히 하는 것이다.

**정리**

- Repository 인터페이스는 "무엇을 할 수 있는지"만 정의한다.
- 구현체는 5·6단계에서 `JdbcTemplate`으로 만든다.

## 5. `JdbcCategoryRepository` — `CategoryRepository` 구현

`src/main/java/com/newlecture/backend/repository/jdbc/JdbcCategoryRepository.java`

```java
package com.newlecture.backend.repository.jdbc;

import com.newlecture.backend.dto.CategoryDTO;
import com.newlecture.backend.repository.CategoryRepository;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public class JdbcCategoryRepository implements CategoryRepository {

    private final JdbcTemplate jdbcTemplate;

    public JdbcCategoryRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public List<CategoryDTO> findAllWithCount() {
        String sql = """
            SELECT c.id, c.name, COUNT(m.id) AS count
            FROM categories c
            LEFT JOIN menus m ON c.id = m.category_id AND m.status != 'hidden'
            GROUP BY c.id, c.name
            ORDER BY c.sort_order
            """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> {
            CategoryDTO dto = new CategoryDTO();
            dto.setId(rs.getLong("id"));
            dto.setName(rs.getString("name"));
            dto.setCount(rs.getInt("count"));
            return dto;
        });
    }
}
```

`LEFT JOIN`으로 `menus`를 붙이고 `GROUP BY`로 묶어서, `menus`가 0개인 카테고리도 `count = 0`으로 함께 나오게 한다(`INNER JOIN`을 쓰면 메뉴가 없는 카테고리가 아예 결과에서 빠진다). `status != 'hidden'` 조건으로 숨김 처리된 메뉴는 개수에서 제외한다.

`@Repository`는 "이 클래스는 Spring이 관리하는 빈(bean)입니다"라고 알리는 어노테이션이다. Spring은 이 표시를 보고 `JdbcCategoryRepository` 객체를 자동으로 만들고, 생성자가 요구하는 `JdbcTemplate`을 알아서 주입한다. `JdbcTemplate` 자체도 Spring Boot가 `application.properties`의 접속 정보를 읽어 자동으로 빈으로 만들어주므로, 우리가 직접 `new JdbcTemplate(...)`을 할 필요가 없다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `JdbcCategoryRepository`가 빈으로 등록되지 않음 | `@Repository` 어노테이션 누락 | 클래스 위에 `@Repository` 추가 |
| `JdbcTemplate`이 `null` | `JdbcTemplate`이 빈으로 등록되지 않음 | `application.properties`에 데이터베이스 접속 정보 확인 |

## 6. `JdbcMenuRepository` — `MenuRepository` 구현

`src/main/java/com/newlecture/backend/repository/jdbc/JdbcMenuRepository.java`

```java
package com.newlecture.backend.repository.jdbc;

import com.newlecture.backend.dto.MenuSummaryDTO;
import com.newlecture.backend.repository.MenuRepository;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public class JdbcMenuRepository implements MenuRepository {

    private final JdbcTemplate jdbcTemplate;

    public JdbcMenuRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public List<MenuSummaryDTO> findAll() {
        String sql = """
            SELECT m.id, m.slug, m.kor_name, m.eng_name, m.price,
                   m.category_id, c.name AS category_name, m.status,
                   m.is_new, m.img_src, m.created_at,
                   (SELECT COUNT(*) FROM favorites f WHERE f.menu_id = m.id) AS favorite_count
            FROM menus m
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE m.status != 'hidden'
            ORDER BY m.id
            """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> {
            MenuSummaryDTO dto = new MenuSummaryDTO();
            dto.setId(rs.getLong("id"));
            dto.setSlug(rs.getString("slug"));
            dto.setKorName(rs.getString("kor_name"));
            dto.setEngName(rs.getString("eng_name"));
            dto.setPrice(rs.getInt("price"));
            dto.setCategoryId(rs.getLong("category_id"));
            dto.setCategoryName(rs.getString("category_name"));
            dto.setStatus(rs.getString("status"));
            dto.setIsNew(rs.getBoolean("is_new"));
            dto.setImgSrc(rs.getString("img_src"));
            dto.setFavoriteCount(rs.getInt("favorite_count"));
            dto.setCreatedAt(rs.getTimestamp("created_at").toLocalDateTime());
            return dto;
        });
    }

    @Override
    public List<MenuSummaryDTO> findByCategory(Long categoryId) {
        String sql = """
            SELECT m.id, m.slug, m.kor_name, m.eng_name, m.price,
                   m.category_id, c.name AS category_name, m.status,
                   m.is_new, m.img_src, m.created_at,
                   (SELECT COUNT(*) FROM favorites f WHERE f.menu_id = m.id) AS favorite_count
            FROM menus m
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE m.status != 'hidden' AND m.category_id = ?
            ORDER BY m.id
            """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> {
            MenuSummaryDTO dto = new MenuSummaryDTO();
            dto.setId(rs.getLong("id"));
            dto.setSlug(rs.getString("slug"));
            dto.setKorName(rs.getString("kor_name"));
            dto.setEngName(rs.getString("eng_name"));
            dto.setPrice(rs.getInt("price"));
            dto.setCategoryId(rs.getLong("category_id"));
            dto.setCategoryName(rs.getString("category_name"));
            dto.setStatus(rs.getString("status"));
            dto.setIsNew(rs.getBoolean("is_new"));
            dto.setImgSrc(rs.getString("img_src"));
            dto.setFavoriteCount(rs.getInt("favorite_count"));
            dto.setCreatedAt(rs.getTimestamp("created_at").toLocalDateTime());
            return dto;
        }, categoryId);
    }

    @Override
    public List<MenuSummaryDTO> findByName(String name) {
        String sql = """
            SELECT m.id, m.slug, m.kor_name, m.eng_name, m.price,
                   m.category_id, c.name AS category_name, m.status,
                   m.is_new, m.img_src, m.created_at,
                   (SELECT COUNT(*) FROM favorites f WHERE f.menu_id = m.id) AS favorite_count
            FROM menus m
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE m.status != 'hidden' AND m.kor_name LIKE ?
            ORDER BY m.id
            """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> {
            MenuSummaryDTO dto = new MenuSummaryDTO();
            dto.setId(rs.getLong("id"));
            dto.setSlug(rs.getString("slug"));
            dto.setKorName(rs.getString("kor_name"));
            dto.setEngName(rs.getString("eng_name"));
            dto.setPrice(rs.getInt("price"));
            dto.setCategoryId(rs.getLong("category_id"));
            dto.setCategoryName(rs.getString("category_name"));
            dto.setStatus(rs.getString("status"));
            dto.setIsNew(rs.getBoolean("is_new"));
            dto.setImgSrc(rs.getString("img_src"));
            dto.setFavoriteCount(rs.getInt("favorite_count"));
            dto.setCreatedAt(rs.getTimestamp("created_at").toLocalDateTime());
            return dto;
        }, "%" + name + "%");
    }

    @Override
    public List<MenuSummaryDTO> findByPriceRange(Integer minPrice, Integer maxPrice) {
        String sql = """
            SELECT m.id, m.slug, m.kor_name, m.eng_name, m.price,
                   m.category_id, c.name AS category_name, m.status,
                   m.is_new, m.img_src, m.created_at,
                   (SELECT COUNT(*) FROM favorites f WHERE f.menu_id = m.id) AS favorite_count
            FROM menus m
            LEFT JOIN categories c ON m.category_id = c.id
            WHERE m.status != 'hidden' AND m.price >= ? AND m.price <= ?
            ORDER BY m.id
            """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> {
            MenuSummaryDTO dto = new MenuSummaryDTO();
            dto.setId(rs.getLong("id"));
            dto.setSlug(rs.getString("slug"));
            dto.setKorName(rs.getString("kor_name"));
            dto.setEngName(rs.getString("eng_name"));
            dto.setPrice(rs.getInt("price"));
            dto.setCategoryId(rs.getLong("category_id"));
            dto.setCategoryName(rs.getString("category_name"));
            dto.setStatus(rs.getString("status"));
            dto.setIsNew(rs.getBoolean("is_new"));
            dto.setImgSrc(rs.getString("img_src"));
            dto.setFavoriteCount(rs.getInt("favorite_count"));
            dto.setCreatedAt(rs.getTimestamp("created_at").toLocalDateTime());
            return dto;
        }, minPrice, maxPrice);
    }
}
```

네 메서드 모두 SQL 본문(`SELECT ... JOIN ... WHERE`)은 거의 같고, `WHERE` 절의 조건과 `RowMapper` 람다에 넘기는 파라미터만 다르다. `categoryName`은 `categories`와의 `LEFT JOIN`으로, `favoriteCount`는 `favorites` 테이블을 세는 서브쿼리로 채운다 — 이렇게 하면 SQL 한 번으로 화면에 필요한 데이터를 모두 가져올 수 있다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `categoryName`이 `null` | `LEFT JOIN`이 아닌 `INNER JOIN` 사용 | `LEFT JOIN`으로 변경 |
| `favoriteCount`가 항상 `0` | 서브쿼리 누락 또는 `menu_id` 조건 오류 | 서브쿼리와 조건 확인 |

## 7. `CategoryController` — `@Autowired`로 주입받기

`src/main/java/com/newlecture/backend/controller/CategoryController.java`

```java
package com.newlecture.backend.controller;

import com.newlecture.backend.dto.CategoryDTO;
import com.newlecture.backend.repository.CategoryRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api")
public class CategoryController {

    private final CategoryRepository categoryRepository;

    @Autowired
    public CategoryController(CategoryRepository categoryRepository) {
        this.categoryRepository = categoryRepository;
    }

    @GetMapping("/categories")
    public List<CategoryDTO> list() {
        return categoryRepository.findAllWithCount();
    }
}
```

`@Autowired`는 "이 의존성을 Spring이 자동으로 주입해줘"라는 요청이다. 생성자 매개변수로 `CategoryRepository`(인터페이스)를 받으면, Spring 컨테이너는 그 인터페이스를 구현한 빈(`JdbcCategoryRepository`)을 찾아서 넣어준다 — 컨트롤러는 구현체가 JDBC인지, 나중에 JPA로 바뀌는지 전혀 몰라도 된다. 이게 [[065_스프링의 정체성 — DI 컨테이너, IoC, 인터페이스와 병렬 개발]]에서 다룬 DI/IoC가 실제 코드에 적용된 모습이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `CategoryRepository`가 `null` | `@Autowired` 누락 | 생성자 위에 `@Autowired` 추가 |
| `JdbcCategoryRepository`가 빈으로 등록되지 않음 | `@Repository` 누락 | `JdbcCategoryRepository`에 `@Repository` 추가 |

## 8. `MenuController` — 쿼리 파라미터로 조건 분기

`src/main/java/com/newlecture/backend/controller/MenuController.java`

```java
package com.newlecture.backend.controller;

import com.newlecture.backend.dto.MenuSummaryDTO;
import com.newlecture.backend.repository.MenuRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api")
public class MenuController {

    private final MenuRepository menuRepository;

    @Autowired
    public MenuController(MenuRepository menuRepository) {
        this.menuRepository = menuRepository;
    }

    @GetMapping("/menus")
    public List<MenuSummaryDTO> list(
            @RequestParam(required = false) String name,
            @RequestParam(required = false) Long category,
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

`list` 메서드는 `name`·`category`·`minPrice`+`maxPrice` 중 어떤 파라미터가 들어왔는지에 따라 호출할 `Repository` 메서드를 분기한다. 아무 조건도 없으면 `findAll()`을 호출한다. `@RequestParam(required = false)`가 없으면 해당 파라미터가 없는 요청은 400 오류가 나므로, 옵셔널 파라미터에는 반드시 `required = false`를 붙인다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `category` 파라미터가 요청에 없을 때 오류 | `@RequestParam`의 `required`가 기본값(`true`) | `required = false`로 변경 |
| `minPrice`/`maxPrice` 둘 중 하나만 왔을 때 예상과 다른 결과 | 두 값이 모두 있어야만 `findByPriceRange` 분기로 들어감 | 조건문(`minPrice != null && maxPrice != null`) 확인 |

## 9. 실행과 확인

```
mvn spring-boot:run
```

Windows에서는 `mvnw spring-boot:run`을 쓸 수도 있다. `Tomcat started on port(s): 8080`이 뜨면 성공이다.

```
curl http://localhost:8080/api/categories
curl http://localhost:8080/api/menus
curl "http://localhost:8080/api/menus?category=1"
curl "http://localhost:8080/api/menus?name=라떼"
```

- `GET /api/categories`가 카테고리 목록(각 카테고리의 `count` 포함)을 JSON으로 반환한다.
- `GET /api/menus`가 메뉴 목록(`categoryName`, `favoriteCount` 포함)을 JSON으로 반환한다.
- `GET /api/menus?category=1`이 해당 카테고리의 메뉴만 반환한다.
- `GET /api/menus?name=라떼`가 이름에 "라떼"가 포함된 메뉴만 반환한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Connection refused` | 애플리케이션이 실행되지 않음 | `mvn spring-boot:run` 실행 여부 확인 |
| 500 Internal Server Error | 데이터베이스 접속 실패 | `application.properties`의 접속 정보 확인 |
| 404 Not Found | URL 오탈자 | URL 확인(`/api/categories`, `/api/menus`) |

## 10. 정리

| 단계 | 내용 |
|---|---|
| 1 | 패키지 구조(`controller`/`entity`/`repository`/`repository.jdbc`/`dto`) 생성, `application.properties` 접속 정보 설정 |
| 2 | 테이블과 1:1 대응하는 `Category`/`Menu` 엔티티 작성 |
| 3 | 화면 전용 필드(`count`, `categoryName`, `favoriteCount`)를 담는 `CategoryDTO`/`MenuSummaryDTO` 작성 |
| 4 | `CategoryRepository`/`MenuRepository` 인터페이스로 "무엇을 할 수 있는지"만 선언 |
| 5 | `JdbcCategoryRepository` — `LEFT JOIN` + `GROUP BY`로 카테고리별 메뉴 수 집계 |
| 6 | `JdbcMenuRepository` — `LEFT JOIN`으로 `categoryName`, 서브쿼리로 `favoriteCount` 채우기 |
| 7 | `CategoryController` — `@Autowired` 생성자 주입으로 `CategoryRepository` 사용 |
| 8 | `MenuController` — 쿼리 파라미터(`name`/`category`/`minPrice`+`maxPrice`)로 조건 분기 |
| 9 | `mvn spring-boot:run` 실행, `curl`/Postman으로 API 확인 |

이번 실습으로 [[031_스프링 부트 백엔드 만들기 — PostgreSQL 연결과 JDBC Repository]]에서 남겨뒀던 두 가지 임시 처리(엔티티를 그대로 응답으로 반환하던 것, 컨트롤러에서 `DataSource`를 손수 조립하던 것)가 모두 정리됐다. `@Repository`로 등록된 구현체를 `@Autowired`가 자동으로 찾아 주입해주므로, 컨트롤러는 `MenuRepository`·`CategoryRepository`라는 인터페이스만 알면 되고, 실제 구현이 JDBC인지 이후 JPA로 바뀌는지는 전혀 신경 쓸 필요가 없다.
