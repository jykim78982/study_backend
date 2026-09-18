---
tags: [웹, 스프링부트, Java, PostgreSQL, JDBC, DTO, DI, 실습]
---

> 🔗 관련 노트: [[030_스프링 부트 백엔드 만들기 — ncafe 프로젝트의 첫 API]] · [[031_스프링 부트 백엔드 만들기 — PostgreSQL 연결과 JDBC Repository]] · [[065_스프링의 정체성 — DI 컨테이너, IoC, 인터페이스와 병렬 개발]] · [[032_Next.js 실무형 메뉴 목록 페이지 만들기 — SSR, 상태, 이벤트, 컴포넌트 분리 실습]]

# ncafe 메뉴·카테고리 API 만들기 — DTO와 DI

**대상**: Spring Boot로 엔티티를 Controller에서 직접 반환하던 사람

**목표**: `GET /api/categories`와 `GET /api/menus`를 DTO 기반으로 만들고, `@Autowired`로 Repository를 주입받는다

**완성물**: `localhost:8080/api/categories`와 `localhost:8080/api/menus`가 프론트엔드 `MenuCard`가 요구하는 JSON을 반환하는 Spring Boot 프로젝트

**필수 준비물**

- Java 17 이상, Spring Boot 3.x, PostgreSQL 14+
- `ncafe` 데이터베이스에 `categories`, `menus` 테이블이 이미 생성되어 있어야 한다.
- `application.properties`에 데이터베이스 접속 정보가 설정되어 있어야 한다.

## 1. 프로젝트 폴더 구조 만들기

Spring Boot 프로젝트의 기본 골격을 만들고, 이번 실습에서 만들 파일들의 위치를 확인한다.

파일: `src/main/java/com/newlecture/backend/`

주의: 디렉토리를 잘못 잡고 실행하면 엉뚱한 곳에 폴더가 와르르 만들어질 수 있다. 신경 쓰인다면 직접 만들어도 된다.

```
mkdir -p src/main/java/com/newlecture/backend/{controller,entity,repository,repository/jdbc,dto}
```

Windows PowerShell에서는 `mkdir -p` 대신 `mkdir`를 여러 번 실행하거나, `New-Item -ItemType Directory -Force -Path`를 사용한다.

`application.properties`(`src/main/resources/application.properties`) 확인:

```
spring.datasource.url=jdbc:postgresql://host:5432/dbname
spring.datasource.username=여기에 실제 계정
spring.datasource.password=여기에 실제 비밀번호
spring.datasource.driver-class-name=org.postgresql.Driver
```

실제 데이터베이스 접속 정보에 맞게 수정한다.

**✅ 확인**

- `src/main/java/com/newlecture/backend/` 아래에 `controller`, `entity`, `repository`, `dto` 폴더가 생겼다.
- `application.properties`에 데이터베이스 접속 정보가 적혀 있다.

**🎓 newlec 쌤의 코멘트**

Spring Boot 프로젝트는 패키지 구조를 미리 정해두는 게 중요하다. `controller`는 HTTP 요청을 받고, `entity`는 데이터베이스 테이블과 1:1로 대응하는 클래스를 만든다. `repository`는 데이터 접근 로직을 구현하고, `dto`는 화면에 보여줄 데이터를 담는 클래스다. 이 구조를 지키면 나중에 서비스 계층을 추가할 때도 파일을 옮길 필요가 없다.

**📝 이 단계의 핵심**

- Spring Boot 프로젝트는 `controller`, `entity`, `repository`, `dto` 패키지로 나눈다.
- `application.properties`에 데이터베이스 접속 정보를 적어둔다.

## 2. 엔티티 만들기

데이터베이스 테이블의 열을 Java 필드로 변환하는 엔티티 클래스를 만든다. 엔티티는 데이터베이스와 1:1로 대응하는 클래스다.

### 2-1. `Category` 엔티티 만들기

파일: `src/main/java/com/newlecture/backend/entity/Category.java`

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

### 2-2. `Menu` 엔티티 만들기

기존 파일은 다음 내용으로 덮어쓴다.

파일: `src/main/java/com/newlecture/backend/entity/Menu.java`

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

**✅ 확인**

- `Category.java`와 `Menu.java` 파일이 `entity` 패키지에 생겼다.
- 각 클래스에 데이터베이스 테이블의 열과 같은 필드가 있다.

**🎓 newlec 쌤의 코멘트**

엔티티는 데이터베이스 테이블의 "Java 버전"이다. `categories` 테이블의 `id`, `name`, `sort_order` 열이 `Category` 클래스의 `id`, `name`, `sortOrder` 필드가 된다. 엔티티는 데이터베이스와 1:1로 대응해야 하므로, 화면에 보여줄 때 필요한 `categoryName` 같은 필드는 엔티티에 넣지 않는다. 그런 필드는 DTO에서 처리한다.

**📝 이 단계의 핵심**

- 엔티티는 데이터베이스 테이블과 1:1로 대응하는 클래스다.
- 엔티티에는 화면에 보여줄 때 필요한 필드(`categoryName` 등)를 넣지 않는다.

## 3. DTO 만들기

DTO(Data Transfer Object)는 화면에 보여줄 데이터를 담는 클래스다. 엔티티와 달리, 화면에 필요한 필드만 골라서 담는다.

다음 코드에서 생성자, Getter/Setter 등은 원래 Lombok을 사용할 수도 있다. 다만 환경에 따라 오류가 날 수 있어서 이번 실습은 직접 코딩한다. Lombok 사용이 편하면 그걸 사용해도 된다.

### 3-1. `CategoryDTO` 만들기

파일: `src/main/java/com/newlecture/backend/dto/CategoryDTO.java`

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

### 3-2. `MenuSummaryDTO` 만들기

파일: `src/main/java/com/newlecture/backend/dto/MenuSummaryDTO.java`

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

**✅ 확인**

- `CategoryDTO.java`와 `MenuSummaryDTO.java` 파일이 `dto` 패키지에 생겼다.
- `CategoryDTO`에는 `count` 필드가 있고, `MenuSummaryDTO`에는 `categoryName`, `favoriteCount` 필드가 있다.

**🎓 newlec 쌤의 코멘트**

DTO는 "이 화면에 이 데이터만 보여줘"라고 말하는 클래스다. `MenuSummaryDTO`의 `categoryName`은 `menus` 테이블에 없는 필드다. 이 필드는 `categories` 테이블에서 가져와서 `menus` 테이블의 데이터와 합쳐서 만들어야 한다. 엔티티에 `categoryName`을 넣으면 안 되는 이유가 바로 이것이다. 엔티티는 데이터베이스와 1:1이어야 하므로, 데이터베이스에 없는 필드는 넣을 수 없다.

**📝 이 단계의 핵심**

- DTO는 화면에 필요한 필드만 골라서 담는 클래스다.
- 데이터베이스에 없는 필드(`categoryName`, `count`)는 DTO에서 처리한다.

## 4. Repository 인터페이스 만들기

Repository 인터페이스는 "이 데이터를 이렇게 가져와줘"라고 요청하는 계약서다. 실제 구현은 다음 단계에서 `JdbcTemplate`으로 만든다.

### 4-1. `CategoryRepository` 인터페이스 만들기

파일: `src/main/java/com/newlecture/backend/repository/CategoryRepository.java`

```java
package com.newlecture.backend.repository;

import com.newlecture.backend.dto.CategoryDTO;
import java.util.List;

public interface CategoryRepository {
    List<CategoryDTO> findAllWithCount();
}
```

### 4-2. `MenuRepository` 인터페이스 만들기

기존 내용과 다른 부분이 있으면 다음 내용으로 덮어쓴다.

파일: `src/main/java/com/newlecture/backend/repository/MenuRepository.java`

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

**✅ 확인**

- `CategoryRepository.java`와 `MenuRepository.java` 파일이 `repository` 패키지에 생겼다.
- 각 인터페이스에 메서드 시그니처만 있고, 구현체는 없다.

**🎓 newlec 쌤의 코멘트**

인터페이스는 "무엇을 할 수 있는지"만 정의하고, "어떻게 하는지"는 구현체에서 결정한다. `CategoryRepository` 인터페이스는 `findAllWithCount()` 메서드가 있다고만 선언한다. 이 메서드가 실제로는 `JdbcTemplate`으로 SQL을 실행해서 데이터를 가져오는지는 구현체(`JdbcCategoryRepository`)에서 결정한다. 이렇게 하면 나중에 `JdbcTemplate` 대신 JPA를 사용해도, 인터페이스만 그대로 유지하면 된다.

**📝 이 단계의 핵심**

- Repository 인터페이스는 "무엇을 할 수 있는지"만 정의한다.
- 구현체는 다음 단계에서 `JdbcTemplate`으로 만든다.

## 5. `JdbcCategoryRepository` 구현

`JdbcTemplate`을 사용해 `CategoryRepository` 인터페이스를 구현한다. `categories` 테이블에서 데이터를 가져오고, `menus` 테이블에서 각 카테고리의 메뉴 수를 세어 `count` 필드에 넣는다.

### 5-1. `JdbcCategoryRepository` 만들기

파일: `src/main/java/com/newlecture/backend/repository/jdbc/JdbcCategoryRepository.java`

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

**✅ 확인**

- `JdbcCategoryRepository.java` 파일이 `repository/jdbc` 패키지에 생겼다.
- `@Repository` 어노테이션이 붙어 있다.
- `JdbcTemplate`을 생성자로 주입받는다.

**🎓 newlec 쌤의 코멘트**

`@Repository` 어노테이션은 "이 클래스는 Spring이 관리하는 빈(bean)입니다"라고 Spring에게 알려주는 것이다. Spring은 이 어노테이션을 보고, `JdbcCategoryRepository` 객체를 자동으로 생성하고, 필요한 의존성(`JdbcTemplate`)을 주입한다. `JdbcTemplate`은 Spring Boot가 `application.properties`의 데이터베이스 접속 정보로 자동으로 생성해준다. 우리가 직접 `new JdbcTemplate()`을 할 필요가 없다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `JdbcCategoryRepository`가 빈으로 등록되지 않음 | `@Repository` 어노테이션 누락 | 클래스 위에 `@Repository` 추가 |
| `JdbcTemplate`이 `null` | `JdbcTemplate`이 빈으로 등록되지 않음 | `application.properties`에 데이터베이스 접속 정보 확인 |

**📝 이 단계의 핵심**

- `@Repository` 어노테이션은 Spring이 빈으로 관리한다는 뜻이다.
- `JdbcTemplate`은 Spring Boot가 자동으로 생성해준다.

## 6. `JdbcMenuRepository` 구현

`JdbcTemplate`을 사용해 `MenuRepository` 인터페이스를 구현한다. `menus` 테이블에서 데이터를 가져오고, `categories` 테이블에서 `categoryName`을 가져와 합친다.

### 6-1. `JdbcMenuRepository` 만들기

파일: `src/main/java/com/newlecture/backend/repository/jdbc/JdbcMenuRepository.java`

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

**✅ 확인**

- `JdbcMenuRepository.java` 파일이 `repository/jdbc` 패키지에 생겼다.
- `@Repository` 어노테이션이 붙어 있다.
- `JdbcTemplate`을 생성자로 주입받는다.

**🎓 newlec 쌤의 코멘트**

`JdbcMenuRepository`의 SQL은 `menus` 테이블과 `categories` 테이블을 `JOIN`해서 `categoryName`을 가져온다. `favoriteCount`는 서브쿼리로 `favorites` 테이블에서 세어온다. 이렇게 하면 한 번의 SQL로 필요한 데이터를 모두 가져올 수 있다. `JdbcTemplate`의 `query` 메서드는 `RowMapper`를 받아, 각 행을 DTO로 변환한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `categoryName`이 `null` | `LEFT JOIN`이 아닌 `INNER JOIN` 사용 | `LEFT JOIN`으로 변경 |
| `favoriteCount`가 `0` | 서브쿼리 누락 | 서브쿼리 추가 |

**📝 이 단계의 핵심**

- `JdbcTemplate`의 `query` 메서드는 `RowMapper`를 받아 행을 DTO로 변환한다.
- `LEFT JOIN`으로 `categoryName`을 가져오고, 서브쿼리로 `favoriteCount`를 계산한다.

## 7. `CategoryController` 만들기

`CategoryController`를 만들어 `GET /api/categories` 엔드포인트를 구현한다. `@Autowired`로 `CategoryRepository`를 주입받는다.

### 7-1. `CategoryController` 만들기

파일: `src/main/java/com/newlecture/backend/controller/CategoryController.java`

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

**✅ 확인**

- `CategoryController.java` 파일이 `controller` 패키지에 생겼다.
- `@RestController`와 `@RequestMapping("/api")` 어노테이션이 붙어 있다.
- `@Autowired`로 `CategoryRepository`를 주입받는다.

**🎓 newlec 쌤의 코멘트**

`@Autowired`는 "이 의존성을 Spring이 자동으로 주입해줘"라고 Spring에게 요청하는 것이다. `CategoryController`의 생성자에 `CategoryRepository`를 넣으면, Spring은 `CategoryRepository`의 구현체(`JdbcCategoryRepository`)를 찾아서 주입한다. 우리가 직접 `new JdbcCategoryRepository()`를 할 필요가 없다. 이것이 DI(의존성 주입)의 핵심이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `CategoryRepository`가 `null` | `@Autowired` 누락 | 생성자 위에 `@Autowired` 추가 |
| `JdbcCategoryRepository`가 빈으로 등록되지 않음 | `@Repository` 누락 | `JdbcCategoryRepository`에 `@Repository` 추가 |

**📝 이 단계의 핵심**

- `@Autowired`는 Spring이 의존성을 자동으로 주입하게 한다.
- `@RestController`는 HTTP 요청을 처리하는 컨트롤러다.

## 8. `MenuController` 만들기

`MenuController`를 만들어 `GET /api/menus` 엔드포인트를 구현한다. `@Autowired`로 `MenuRepository`를 주입받는다.

### 8-1. `MenuController` 만들기

파일: `src/main/java/com/newlecture/backend/controller/MenuController.java`

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

**✅ 확인**

- `MenuController.java` 파일이 `controller` 패키지에 생겼다.
- `@RestController`와 `@RequestMapping("/api")` 어노테이션이 붙어 있다.
- `@Autowired`로 `MenuRepository`를 주입받는다.

**🎓 newlec 쌤의 코멘트**

`MenuController`의 `list` 메서드는 `name`, `category`, `minPrice`, `maxPrice` 파라미터를 받아, 어떤 조건으로 데이터를 가져올지 결정한다. `name`이 있으면 `findByName`, `category`가 있으면 `findByCategory`, `minPrice`와 `maxPrice`가 있으면 `findByPriceRange`를 호출한다. 아무 조건도 없으면 `findAll`을 호출한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `category` 파라미터가 `null` | `@RequestParam`의 `required`가 `true` | `required = false`로 변경 |
| `minPrice`와 `maxPrice`가 `null` | `@RequestParam`의 `required`가 `true` | `required = false`로 변경 |

**📝 이 단계의 핵심**

- `@RequestParam`의 `required = false`로 옵셔널 파라미터를 만든다.
- 조건에 따라 다른 Repository 메서드를 호출한다.

## 9. 실행과 테스트

Spring Boot 애플리케이션을 실행하고, API가 제대로 동작하는지 확인한다.

### 9-1. 애플리케이션 실행

```
mvn spring-boot:run
```

Windows에서는 `mvnw spring-boot:run`을 사용할 수도 있다.

### 9-2. API 테스트

```
curl http://localhost:8080/api/categories
curl http://localhost:8080/api/menus
curl "http://localhost:8080/api/menus?category=1"
curl "http://localhost:8080/api/menus?name=라떼"
```

**✅ 확인**

- `http://localhost:8080/api/categories`가 카테고리 목록을 JSON으로 반환한다.
- `http://localhost:8080/api/menus`가 메뉴 목록을 JSON으로 반환한다.
- `http://localhost:8080/api/menus?category=1`이 커피 카테고리만 반환한다.
- `http://localhost:8080/api/menus?name=라떼`이 "라떼"가 포함된 메뉴만 반환한다.

**🎓 newlec 쌤의 코멘트**

이제 `localhost:8080/api/categories`와 `localhost:8080/api/menus`가 프론트엔드 `MenuCard`가 요구하는 JSON을 반환한다. `CategoryDTO`의 `count` 필드는 각 카테고리의 메뉴 수를, `MenuSummaryDTO`의 `categoryName` 필드는 카테고리 이름을 담고 있다. 이 JSON을 프론트엔드가 받아서 `MenuCard`를 그릴 수 있다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| Connection refused | 애플리케이션이 실행되지 않음 | `mvn spring-boot:run` 실행 |
| 500 Internal Server Error | 데이터베이스 접속 실패 | `application.properties`의 데이터베이스 접속 정보 확인 |
| 404 Not Found | URL이 잘못됨 | URL 확인 |

**📝 이 단계의 핵심**

- `mvn spring-boot:run`으로 애플리케이션을 실행한다.
- `curl`로 API를 테스트한다.

## 정리

1단계: Spring Boot 프로젝트의 기본 골격을 만들고, 패키지 구조를 정한다.
2단계: 데이터베이스 테이블과 1:1로 대응하는 엔티티 클래스를 만든다.
3단계: 화면에 필요한 필드만 골라서 담는 DTO 클래스를 만든다.
4단계: "무엇을 할 수 있는지"만 정의하는 Repository 인터페이스를 만든다.
5단계: `JdbcTemplate`으로 `CategoryRepository`를 구현한다.
6단계: `JdbcTemplate`으로 `MenuRepository`를 구현한다.
7단계: `@Autowired`로 `CategoryRepository`를 주입받는 `CategoryController`를 만든다.
8단계: `@Autowired`로 `MenuRepository`를 주입받는 `MenuController`를 만든다.
9단계: 애플리케이션을 실행하고, API를 테스트한다.
