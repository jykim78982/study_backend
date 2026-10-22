---
tags: [스프링부트, JdbcTemplate, PostgreSQL, DTO, 실습]
---

> 🔗 관련 노트: [[073_스프링 DI]] · [[072_API URL 설계 — 페이지 단위 스케치와 주인공·곁다리 규칙]] · [[037_스프링 DI·IoC 기초 — 빌드 도구 없이 JAR 직접 설치로 배우기]]

# Spring Boot 3계층 실습 — JdbcTemplate로 Menu API 만들기

**대상**: 오전 수업에 참여해서 Spring Boot 프로젝트 구조와 3계층(Controller → Service → Repository)을 이해하고 있는 사람, 이전 수업에서 JdbcTemplate으로 데이터를 가져온 경험이 있는 사람

**목표**: menus와 categories 테이블의 데이터를 JdbcTemplate으로 가져와서, Service에서 DTO로 조립하고 Controller에서 서빙하는 과정을 직접 코딩하며 3계층의 역할을 체감한다

**완성물**: `/api/v1/menus`와 `/api/v1/menus/categories` 두 API가 Postman이나 브라우저에서 JSON 응답을 반환하는 상태. 내부 구조는 엔티티가 테이블과 1:1로 대응하고, 조립 로직이 Service에 있는 상태

## 1. build.gradle에 JDBC 의존성 추가

Spring Boot가 데이터베이스와 대화하려면 두 가지 도구가 필요합니다. 하나는 SQL을 실행하는 도구(JdbcTemplate)이고, 다른 하나는 PostgreSQL과 통신하는 드라이버입니다. 이 두 가지를 프로젝트에 추가해 볼게요.

### 1-1. build.gradle 파일 열기

프로젝트 루트 폴더의 `build.gradle` 파일을 엽니다.

파일: `build.gradle`

### 1-2. dependencies 블록에 의존성 추가

`dependencies { ... }` 블록 안에 아래 두 줄을 추가합니다.

```gradle
dependencies {
    // ... 기존 의존성들 ...

    // JdbcTemplate와 DataSource 자동 설정을 위한 스타터
    implementation 'org.springframework.boot:spring-boot-starter-jdbc'

    // PostgreSQL JDBC 드라이버 (런타임에만 필요)
    runtimeOnly 'org.postgresql:postgresql'
}
```

**왜 `runtimeOnly`인가?** PostgreSQL 드라이버는 우리가 코드를 작성할 때 직접 import해서 사용하지 않습니다. 프로그램이 실행될 때(run할 때) Spring이 자동으로 드라이버를 찾아서 연결하기 때문에, 컴파일 시점에는 필요 없고 실행 시점에만 필요하므로 `runtimeOnly`로 설정합니다.

**✅ 확인**

터미널에서 아래 명령을 실행하여 컴파일이 정상적으로 되는지 확인합니다.

```bash
cd backend
./gradlew compileJava
```

- `BUILD SUCCESSFUL`이 표시됩니다.
- 에러가 없다면 성공입니다.

**🎓 newlec 쌤의 코멘트**

식당 비유로 설명하면, `spring-boot-starter-jdbc`는 주방에 있는 '전자레인지' 같은 도구입니다. 우리가 직접 불을 다루지 않고, 버튼만 누르면(코드를 적으면) 내부적으로 복잡한 과정(연결, 쿼리 실행)을 처리해 줍니다. `postgresql` 드라이버는 그 전자레인지가 우리 가게의 특수한 재료(PostgreSQL)를 처리할 수 있도록 해주는 '어댑터'입니다. 이 두 가지가 없으면 Spring은 데이터베이스와 어떻게 대화해야 할지 모릅니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Could not resolve org.springframework.boot:spring-boot-starter-jdbc` | Gradle 캐시 문제 또는 네트워크 문제 | `./gradlew clean` 후 다시 `compileJava` 실행 |
| `Unresolved reference: postgresql` | `runtimeOnly` 대신 `implementation`으로 잘못 적었거나 오타 | `runtimeOnly 'org.postgresql:postgresql'` 문법을 정확히 확인 |

**📝 이 단계의 핵심**

- `spring-boot-starter-jdbc`: JdbcTemplate 사용 가능하게 해주는 스타터
- `org.postgresql:postgresql`: PostgreSQL 연결용 드라이버 (`runtimeOnly`)

## 2. application.properties에 DB 연결 정보 설정

Spring Boot가 데이터베이스에 연결하려면 '주소', '아이디', '비밀번호'가 필요합니다. 이 정보를 설정 파일에 적어주면 Spring이 자동으로 DataSource를 만들어 줍니다.

### 2-1. application.properties 파일 열기

`src/main/resources/application.properties` 파일을 엽니다.

파일: `src/main/resources/application.properties`

### 2-2. 데이터베이스 연결 정보 추가

파일 아래에 아래 4줄을 추가합니다. (값은 실제 DB 환경에 맞게 수정하세요)

```properties
# 데이터베이스 연결 정보
spring.datasource.url=jdbc:postgresql://cloud.newlecture.com:5432/ncafedb
spring.datasource.username=ncafe
spring.datasource.password=newlec1210+
spring.datasource.driver-class-name=org.postgresql.Driver
```

**속성 설명**

- `url`: `jdbc:postgresql://서버주소:포트/데이터베이스이름` 형식
- `username`: DB 접속 계정
- `password`: DB 접속 비밀번호
- `driver-class-name`: 사용할 JDBC 드라이버 클래스 이름 (보통 자동 감지되지만 명시하는 것이 안전합니다)

**✅ 확인**

이 단계에서는 컴파일 확인만 합니다. 실제 연결은 나중에 테스트할 때 확인합니다.

```bash
./gradlew compileJava
```

`BUILD SUCCESSFUL`이 표시됩니다.

**🎓 newlec 쌤의 코멘트**

Spring Boot의 '자동 설정(Auto-Configuration)'은 마법처럼 느껴질 수 있지만, 실제로는 아주 단순한 규칙을 따릅니다. "classpath에 JDBC 드라이버가 있고, `spring.datasource.*` 속성이 있으면 DataSource 빈을 만들어주겠다"는 약속입니다. 우리는 이 약속만 지켜주면, `@Configuration` 클래스를 직접 작성할 필요가 없습니다. 이것이 Spring Boot가 'Convention over Configuration'(규칙이 설정보다 우선)을 강조하는 이유입니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Access denied for user` | username 또는 password 오류 | DB 관리 도구에서 계정 정보 재확인 |
| `Connection refused` | url의 host/port 오류 또는 DB 서버 미실행 | url 값이 정확한지, DB 서버가 켜져 있는지 확인 |

**📝 이 단계의 핵심**

- `spring.datasource.*` 4가지만 있으면 Spring이 DataSource를 자동 생성
- `driver-class-name`은 명시하는 것이 안전

## 3. Category 엔티티 생성 (1차 구현)

이제 categories 테이블의 데이터를 Java 객체로 표현할 엔티티를 만들겠습니다. **주의**: 이 단계에서는 '1차 구현'으로, 나중에 코드 리뷰에서 수정할 부분을 의도적으로 포함합니다.

### 3-1. Category.java 파일 생성

`src/main/java/com/newlecture/ncafe/backend/entity/` 폴더에 `Category.java`를 만듭니다.

파일: `src/main/java/com/newlecture/ncafe/backend/entity/Category.java`

```java
package com.newlecture.ncafe.backend.entity;

public class Category {

    private Long id;
    private String name;
    // 1차 구현: 메뉴 개수를 함께 가져오기 위해 추가 (나중에 수정될 부분)
    private Integer menuCount;

    public Category() {
    }

    // getter/setter
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public Integer getMenuCount() { return menuCount; }
    public void setMenuCount(Integer menuCount) { this.menuCount = menuCount; }
}
```

**왜 menuCount를 넣었나?** API 응답에 카테고리 이름과 함께 메뉴 개수가 필요하기 때문입니다. 하지만 엄밀히 말하면 categories 테이블에는 `menu_count` 컬럼이 없습니다. 이는 menus 테이블과 JOIN해서 계산해야 하는 값입니다. 이 '불순물'이 나중에 코드 리뷰에서 문제점으로 지적될 것입니다.

**✅ 확인**

```bash
./gradlew compileJava
```

`BUILD SUCCESSFUL`이 표시됩니다.

**🎓 newlec 쌤의 코멘트**

엔티티(Entity)는 보통 '데이터베이스 테이블의 한 행'을 1:1로 표현하는 객체입니다. Menu 엔티티는 menus 테이블의 컬럼만 가지고 있어야 합니다. 그런데 Category 엔티티에 menuCount를 넣으면, 이 엔티티는 더 이상 categories 테이블의 순수한 대변자가 아닙니다. '카테고리 정보 + 계산된 메뉴 개수'라는 혼합체가 됩니다. 실무에서는 이런 경우를 피하기 위해, 순수한 엔티티는 유지하고 계산된 값은 Service나 View 객체에서 처리하는 것이 원칙입니다. 하지만 지금은 '편리함'을 위해 이렇게 해놓고, 나중에 왜 안 좋은지 스스로 발견해 보도록 하겠습니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Cannot find symbol: class Category` | 패키지 경로 오류 | `package com.newlecture.ncafe.backend.entity;`가 정확한지 확인 |

**📝 이 단계의 핵심**

- Category 엔티티 생성
- 1차 구현에서는 menuCount를 포함 (나중에 수정 예정)

## 4. CategoryRepository 인터페이스 작성 (1차)

Service가 Category 데이터를 가져오려면, Repository 인터페이스가 필요합니다. 이 인터페이스는 '무엇을 가져올지'만 정의하고, '어떻게 가져올지'는 구현체에 맡깁니다.

### 4-1. CategoryRepository.java 파일 생성

`src/main/java/com/newlecture/ncafe/backend/repository/` 폴더에 `CategoryRepository.java`를 만듭니다.

파일: `src/main/java/com/newlecture/ncafe/backend/repository/CategoryRepository.java`

```java
package com.newlecture.ncafe.backend.repository;

import java.util.List;
import com.newlecture.ncafe.backend.entity.Category;

public interface CategoryRepository {
    // 1차 구현: 메뉴 개수를 함께 가져오는 메서드
    List<Category> findAllWithMenuCount();
}
```

**왜 인터페이스인가?** Service는 `CategoryRepository` 인터페이스만 참조합니다. 실제 구현체는 `DfCategoryRepository`(Df = Default/Implementation)입니다. 이렇게 하면 Service는 '구현 방식'을 알지 않아도 되고, 나중에 구현 방식을 바꿀 때(예: JdbcTemplate → JPA) Service 코드를 건드릴 필요가 없습니다. 이것이 '의존성 역전 원리(DIP)'입니다. 073 노트에서 다룬 것처럼, 컨트롤러와 서비스가 항상 구체 클래스가 아니라 인터페이스를 참조하도록 만드는 원칙이 Repository 계층에도 그대로 적용되는 것입니다.

**✅ 확인**

```bash
./gradlew compileJava
```

`BUILD SUCCESSFUL`이 표시됩니다.

**🎓 newlec 쌤의 코멘트**

식당 비유로 보면, `CategoryRepository` 인터페이스는 '재료 주문서'의 형식입니다. "카테고리 목록을 가져와"라고 적혀 있는 주문서입니다. 실제 재료를 가져오는 사람은 `DfCategoryRepository`(재료 판매상)입니다. 주방장(Service)은 주문서(인터페이스)만 보고 주문을 하고, 재료를 실제로 누가 가져오는지(구현체)는 알 필요가 없습니다. 만약 재료 판매상이 바뀌어도, 주문서 형식만 유지되면 주방장은 아무것도 바꾸지 않아도 됩니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `CategoryRepository is not abstract and does not implement abstract method` | 구현체가 없거나 메서드 시그니처 불일치 | 아직 구현체를 만들지 않았으므로 정상. 다음 단계에서 구현 |

**📝 이 단계의 핵심**

- CategoryRepository 인터페이스 생성
- `findAllWithMenuCount()` 메서드 선언 (1차)

## 5. DfMenuRepository 구현 — JdbcTemplate로 menus 테이블 조회

이제 핵심입니다. menus 테이블의 데이터를 JdbcTemplate으로 가져와서 Menu 엔티티 리스트로 변환하는 코드를 작성합니다.

### 5-1. DfMenuRepository.java 파일 수정

`src/main/java/com/newlecture/ncafe/backend/repository/DfMenuRepository.java` 파일을 엽니다.

파일: `src/main/java/com/newlecture/ncafe/backend/repository/DfMenuRepository.java`

```java
package com.newlecture.ncafe.backend.repository;

import java.util.List;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import com.newlecture.ncafe.backend.entity.Menu;

@Repository
public class DfMenuRepository implements MenuRepository {

    private final JdbcTemplate jdbcTemplate;

    // 생성자 주입: Spring이 JdbcTemplate 빈을 자동으로 주입
    public DfMenuRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public List<Menu> findAll() {
        String sql = "SELECT id, slug, category_id, kor_name, eng_name, price, "
                   + "description, detail, status, is_new, img_src, created_at, updated_at "
                   + "FROM menus ORDER BY id";

        return jdbcTemplate.query(sql, new RowMapper<Menu>() {
            @Override
            public Menu mapRow(java.sql.ResultSet rs, int rowNum) throws java.sql.SQLException {
                Menu menu = new Menu();
                menu.setId(rs.getLong("id"));
                menu.setSlug(rs.getString("slug"));
                menu.setCategoryId(rs.getLong("category_id"));
                menu.setKorName(rs.getString("kor_name"));
                menu.setEngName(rs.getString("eng_name"));
                menu.setPrice(rs.getInt("price"));
                menu.setDescription(rs.getString("description"));
                menu.setDetail(rs.getString("detail"));
                menu.setStatus(rs.getString("status"));
                menu.setIsNew(rs.getBoolean("is_new"));
                menu.setImgSrc(rs.getString("img_src"));
                menu.setCreatedAt(rs.getTimestamp("created_at").toLocalDateTime());
                menu.setUpdatedAt(rs.getTimestamp("updated_at").toLocalDateTime());
                return menu;
            }
        });
    }
}
```

**코드 흐름 설명**

1. `jdbcTemplate.query(sql, rowMapper)` 호출
2. Spring이 Connection을 획득하고 SQL을 실행
3. ResultSet의 각 행마다 `mapRow` 메서드가 호출됨
4. `rs.getXxx("컬럼명")`으로 값을 읽어 Menu 객체에 세팅
5. 모든 행 변환 후 `List<Menu>` 반환

**RowMapper 주의점**

- `int8`(bigint) → `rs.getLong()`
- `int4`(integer) → `rs.getInt()`
- `varchar`/`text` → `rs.getString()`
- `bool` → `rs.getBoolean()`
- `timestamptz` → `rs.getTimestamp().toLocalDateTime()`

**✅ 확인**

```bash
./gradlew compileJava
```

`BUILD SUCCESSFUL`이 표시됩니다.

**🎓 newlec 쌤의 코멘트**

JdbcTemplate은 JDBC의 번거로움을 숨겨주는 도구입니다. 직접 Connection, PreparedStatement, ResultSet을 열고 닫고 예외를 처리하지 않아도 됩니다. 우리가 할 일은 'SQL 문장'과 '한 행을 어떻게 객체로 바꿀지(RowMapper)'만 정의하면 됩니다. `@Repository` 어노테이션은 이 클래스를 Spring 빈으로 등록하고, JDBC 예외를 Spring 예외로 변환하는 역할도 합니다. 이 단계에서 Menu 엔티티는 menus 테이블의 컬럼만 가지고 있습니다. `categoryName`은 없습니다. 이것이 '엔티티 = 테이블 1:1' 원칙입니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `SQLSyntaxErrorException: column "xxx" does not exist` | SQL의 컬럼명 오타 또는 DB 스키마 불일치 | DB 스키마와 SQL의 컬럼명을 대조 |
| `NullPointerException in mapRow` | `rs.getXxx()`가 null을 반환하고, primitive 타입에 대입 | `rs.getObject()` 또는 null 체크 로직 추가 |
| `Cannot find symbol: class JdbcTemplate` | 1단계에서 의존성 추가 누락 | `build.gradle`에 `spring-boot-starter-jdbc`가 있는지 확인 |

**📝 이 단계의 핵심**

- JdbcTemplate 생성자 주입
- `jdbcTemplate.query(sql, rowMapper)` 사용
- RowMapper로 ResultSet 행 → Entity 변환
- Menu 엔티티는 menus 테이블 컬럼만 포함

## 6. DfCategoryRepository 구현 (1차: LEFT JOIN + COUNT)

이제 categories 테이블과 menus 테이블을 JOIN해서 카테고리별 메뉴 개수를 함께 가져오는 코드를 작성합니다. **주의**: 이 단계도 '1차 구현'으로, 나중에 코드 리뷰에서 수정될 것입니다.

### 6-1. DfCategoryRepository.java 파일 생성

`src/main/java/com/newlecture/ncafe/backend/repository/` 폴더에 `DfCategoryRepository.java`를 만듭니다.

파일: `src/main/java/com/newlecture/ncafe/backend/repository/DfCategoryRepository.java`

```java
package com.newlecture.ncafe.backend.repository;

import java.util.List;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import com.newlecture.ncafe.backend.entity.Category;

@Repository
public class DfCategoryRepository implements CategoryRepository {

    private final JdbcTemplate jdbcTemplate;

    public DfCategoryRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public List<Category> findAllWithMenuCount() {
        String sql = "SELECT c.id, c.name, COUNT(m.id) AS menu_count "
                   + "FROM categories c "
                   + "LEFT JOIN menus m ON c.id = m.category_id "
                   + "GROUP BY c.id, c.name "
                   + "ORDER BY c.sort_order";

        return jdbcTemplate.query(sql, new RowMapper<Category>() {
            @Override
            public Category mapRow(java.sql.ResultSet rs, int rowNum) throws java.sql.SQLException {
                Category category = new Category();
                category.setId(rs.getLong("id"));
                category.setName(rs.getString("name"));
                category.setMenuCount(rs.getInt("menu_count"));
                return category;
            }
        });
    }
}
```

**SQL 설명**

- `LEFT JOIN`: 메뉴가 0개인 카테고리도 포함
- `COUNT(m.id)`: 카테고리별 메뉴 개수 계산
- `GROUP BY`: 카테고리별로 그룹화
- `ORDER BY c.sort_order`: 화면 표시 순서

**✅ 확인**

```bash
./gradlew compileJava
```

`BUILD SUCCESSFUL`이 표시됩니다.

**🎓 newlec 쌤의 코멘트**

이 쿼리는 '카테고리 목록과 각 카테고리의 메뉴 개수'를 한 번에 가져옵니다. 효율적이지만, Category 엔티티에 `menuCount`라는 '계산된 값'이 들어오게 됩니다. 이는 3단계에서 만든 Category 엔티티의 `menuCount` 필드와 일치합니다. 하지만 이 '일치'가 나중에 문제의 씨앗이 될 것입니다. Repository가 '단순한 데이터 조회'를 넘어 '비즈니스 로직(카운트)'을 수행하고 있기 때문입니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `SQLSyntaxErrorException: column "c.sort_order" does not exist` | DB 스키마에 sort_order 컬럼이 없음 | DB 스키마 확인, 없으면 추가 또는 SQL 수정 |
| `menu_count` 값이 0으로만 나옴 | JOIN 조건 오류 또는 데이터 없음 | menus 테이블에 category_id 값이 있는지 확인 |

**📝 이 단계의 핵심**

- DfCategoryRepository 구현
- LEFT JOIN + COUNT로 카테고리별 메뉴 개수 조회
- Category 엔티티에 menuCount 설정 (1차)

## 7. DfMenuService — 두 Repository의 데이터를 DTO로 조립 (1차)

이제 Service 계층입니다. Service는 Repository에서 가져온 '날것(엔티티)'을 받아서, API에 맞게 'DTO'로 변환하는 역할을 합니다.

### 7-1. DfMenuService.java 파일 수정

`src/main/java/com/newlecture/ncafe/backend/service/DfMenuService.java` 파일을 엽니다.

파일: `src/main/java/com/newlecture/ncafe/backend/service/DfMenuService.java`

```java
package com.newlecture.ncafe.backend.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;

import com.newlecture.ncafe.backend.dto.menu.MenuListRequestDto;
import com.newlecture.ncafe.backend.dto.menu.MenuListResponseDto;
import com.newlecture.ncafe.backend.entity.Category;
import com.newlecture.ncafe.backend.entity.Menu;
import com.newlecture.ncafe.backend.repository.CategoryRepository;
import com.newlecture.ncafe.backend.repository.MenuRepository;

@Service
public class DfMenuService implements MenuService {

    private final MenuRepository menuRepository;
    private final CategoryRepository categoryRepository;

    public DfMenuService(MenuRepository menuRepository, CategoryRepository categoryRepository) {
        this.menuRepository = menuRepository;
        this.categoryRepository = categoryRepository;
    }

    @Override
    public List<MenuListResponseDto> getList(MenuListRequestDto requestDto) {
        // 1. 메뉴 목록 조회 (날것)
        List<Menu> menus = menuRepository.findAll();

        // 2. 카테고리 목록 조회 (날것 + menuCount)
        List<Category> categories = categoryRepository.findAllWithMenuCount();

        // 3. categoryId → categoryName 매핑 Map 생성
        Map<Long, String> categoryNameMap = categories.stream()
                .collect(Collectors.toMap(Category::getId, Category::getName));

        // 4. Menu 엔티티를 DTO로 변환
        List<MenuListResponseDto> list = new ArrayList<>();
        for (Menu menu : menus) {
            MenuListResponseDto dto = new MenuListResponseDto();
            dto.setId(menu.getId());
            // categoryId로 categoryName을 Map에서 찾아서 설정
            dto.setCategoryName(categoryNameMap.get(menu.getCategoryId()));
            dto.setKorName(menu.getKorName());
            dto.setEngName(menu.getEngName());
            dto.setPrice(menu.getPrice());
            dto.setImgSrc(menu.getImgSrc());
            dto.setIsLike(false); // 예시용
            list.add(dto);
        }
        return list;
    }
}
```

**데이터 흐름**

1. `menuRepository.findAll()` → `List<Menu>`(categoryName 없음)
2. `categoryRepository.findAllWithMenuCount()` → `List<Category>`(menuCount 포함)
3. Category 리스트를 `Map<categoryId, categoryName>`으로 변환
4. 각 Menu의 categoryId로 Map에서 categoryName을 찾아 DTO에 설정

**왜 Service에서 조립하는가?**

- Repository는 각자 자기 테이블만 알면 됨 (단일 책임 원칙)
- Menu 엔티티에 categoryName을 넣지 않음 (엔티티 = 테이블 1:1)
- Service에서 여러 Repository의 데이터를 합쳐서 DTO를 만듦

**✅ 확인**

```bash
./gradlew compileJava
```

`BUILD SUCCESSFUL`이 표시됩니다.

**🎓 newlec 쌤의 코멘트**

이 단계에서 '조립'이 일어납니다. Menu 엔티티에는 categoryName이 없습니다. 하지만 API 응답에는 categoryName이 필요합니다. 그래서 Service에서 CategoryRepository를 추가로 호출해서 categoryName을 가져오고, Menu의 categoryId와 매칭시켜서 DTO에 채워 넣습니다. 이 과정이 'Service의 역할'입니다. Repository는 '날것'만 가져오고, Service는 '조리(조립)'를 해서 '완성된 요리(DTO)'를 Controller에 전달합니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `NullPointerException in categoryNameMap.get()` | categoryId가 null이거나 Map에 없는 key | menus 테이블의 category_id가 categories 테이블의 id와 일치하는지 확인 |
| `IllegalStateException: Duplicate key` | categories에 중복된 id가 있음 | DB 데이터 무결성 확인 |

**📝 이 단계의 핵심**

- DfMenuService 구현
- 두 Repository의 데이터를 Service에서 조립
- Map을 이용한 categoryId → categoryName 매핑
- Menu 엔티티에 categoryName을 넣지 않음

## 8. DfCategoryService (1차: 엔티티를 그대로 DTO로 변환)

이제 카테고리 목록 API를 위한 Service를 작성합니다.

### 8-1. CategoryService 인터페이스 확인

`src/main/java/com/newlecture/ncafe/backend/service/CategoryService.java`가 있는지 확인합니다. 없으면 생성합니다.

파일: `src/main/java/com/newlecture/ncafe/backend/service/CategoryService.java`

```java
package com.newlecture.ncafe.backend.service;

import java.util.List;
import com.newlecture.ncafe.backend.dto.menu.CategoryListResponseDto;

public interface CategoryService {
    List<CategoryListResponseDto> findAll();
}
```

### 8-2. DfCategoryService.java 파일 생성

`src/main/java/com/newlecture/ncafe/backend/service/` 폴더에 `DfCategoryService.java`를 만듭니다.

파일: `src/main/java/com/newlecture/ncafe/backend/service/DfCategoryService.java`

```java
package com.newlecture.ncafe.backend.service;

import java.util.ArrayList;
import java.util.List;

import org.springframework.stereotype.Service;

import com.newlecture.ncafe.backend.dto.menu.CategoryListResponseDto;
import com.newlecture.ncafe.backend.entity.Category;
import com.newlecture.ncafe.backend.repository.CategoryRepository;

@Service
public class DfCategoryService implements CategoryService {

    private final CategoryRepository repository;

    public DfCategoryService(CategoryRepository repository) {
        this.repository = repository;
    }

    @Override
    public List<CategoryListResponseDto> findAll() {
        // 1. 카테고리 목록 조회 (날것 + menuCount)
        List<Category> categories = repository.findAllWithMenuCount();

        // 2. Category 엔티티를 DTO로 변환
        List<CategoryListResponseDto> list = new ArrayList<>();
        for (Category category : categories) {
            CategoryListResponseDto dto = new CategoryListResponseDto();
            dto.setId(category.getId());
            dto.setName(category.getName());
            dto.setMenuCount(category.getMenuCount());
            list.add(dto);
        }
        return list;
    }
}
```

**이 단계의 특징**

- `DfMenuService`와 달리, Category 엔티티에 이미 menuCount가 있으므로 추가로 MenuRepository를 호출할 필요가 없습니다.
- 하지만 이는 '1차 구현'의 편의성입니다. 나중에 코드 리뷰에서 이 부분이 문제점으로 지적될 것입니다.

**✅ 확인**

```bash
./gradlew compileJava
```

`BUILD SUCCESSFUL`이 표시됩니다.

**🎓 newlec 쌤의 코멘트**

이 Service는 매우 단순합니다. Repository에서 가져온 Category 엔티티를 그대로 DTO로 복사하는 것뿐입니다. 왜냐하면 Category 엔티티에 이미 menuCount가 들어있기 때문입니다. 하지만 이 '단순함'이 '불순함'을 숨기고 있습니다. Category 엔티티가 categories 테이블의 순수한 대변자가 아니기 때문입니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Cannot find symbol: class CategoryListResponseDto` | DTO 클래스가 없거나 패키지 오류 | `dto/menu/CategoryListResponseDto.java`가 있는지 확인 |

**📝 이 단계의 핵심**

- DfCategoryService 구현
- Category 엔티티를 DTO로 변환
- menuCount를 엔티티에서 직접 가져옴 (1차)

## 9. MenuController에 categories 엔드포인트 추가

이제 Controller 계층입니다. Controller는 Service에서 받은 DTO를 그대로 JSON으로 변환해서 반환하는 역할만 합니다.

### 9-1. MenuController.java 파일 수정

`src/main/java/com/newlecture/ncafe/backend/controller/MenuController.java` 파일을 엽니다.

파일: `src/main/java/com/newlecture/ncafe/backend/controller/MenuController.java`

```java
package com.newlecture.ncafe.backend.controller;

import java.util.List;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.newlecture.ncafe.backend.dto.menu.CategoryListResponseDto;
import com.newlecture.ncafe.backend.dto.menu.MenuListRequestDto;
import com.newlecture.ncafe.backend.dto.menu.MenuListResponseDto;
import com.newlecture.ncafe.backend.service.CategoryService;
import com.newlecture.ncafe.backend.service.MenuService;

@RestController
@RequestMapping("/api/v1/menus")
public class MenuController {

    private final MenuService service;
    private final CategoryService categoryService;

    public MenuController(MenuService service, CategoryService categoryService) {
        this.service = service;
        this.categoryService = categoryService;
    }

    // 기존 메뉴 목록 API
    @GetMapping
    public List<MenuListResponseDto> list(MenuListRequestDto requestDto) {
        return service.getList(requestDto);
    }

    // 새로운 카테고리 목록 API
    @GetMapping("categories")
    public List<CategoryListResponseDto> categoryList() {
        return categoryService.findAll();
    }
}
```

**Controller의 역할**

- `@RestController`: `@Controller` + `@ResponseBody`의 합성어. JSON으로 반환
- `@RequestMapping("/api/v1/menus")`: 이 컨트롤러의 기본 경로
- `@GetMapping("categories")`: `/api/v1/menus/categories` 경로에 매핑 — 072 노트에서 다룬 "곁다리는 주인공 뒤에 하위 경로로 붙인다"는 규칙 그대로다. 메뉴(주인공)가 최상위 경로를 갖고, 카테고리(곁다리)는 그 뒤에 붙는다.
- `categoryService.findAll()` 호출 후 반환
- Controller는 '변환'을 하지 않습니다. Service에서 이미 DTO로 변환된 것을 그대로 반환

**✅ 확인**

```bash
./gradlew compileJava
```

`BUILD SUCCESSFUL`이 표시됩니다.

**🎓 newlec 쌤의 코멘트**

Controller는 '홀담당'입니다. 주방장(Service)이 완성한 요리(DTO)를 손님(API 호출자)에게 그대로 전달하는 역할입니다. 홀담당은 요리를 다시 조리하지 않습니다. 만약 Controller에서 DTO를 다시 변환하거나, 비즈니스 로직을 넣는다면, 그것은 '홀담당이 주방에서 요리하는' 것과 같습니다. 역할이 혼재되면 유지보수가 어려워집니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `404 Not Found` | 경로 오타 또는 `@RequestMapping` 누락 | `@RequestMapping("/api/v1/menus")`와 `@GetMapping("categories")`를 확인 |
| `500 Internal Server Error` | Service 또는 Repository에서 예외 발생 | 콘솔 로그를 확인하여 원인을 파악 |

**📝 이 단계의 핵심**

- MenuController에 CategoryService 주입
- categories 엔드포인트 추가
- Controller는 변환 없이 DTO를 그대로 반환

## 10. 1차 구현 테스트

이제 서버를 실행해서 두 API가 정상적으로 동작하는지 확인합니다.

### 10-1. 서버 실행

터미널에서 아래 명령을 실행합니다.

```bash
./gradlew bootRun
```

`Started Application in X.XXX seconds` 메시지가 나오면 서버가 실행된 것입니다.

### 10-2. Postman 또는 브라우저로 API 호출

- **API 1: 메뉴 목록**
  - URL: `http://localhost:8080/api/v1/menus`
  - Method: GET
- **API 2: 카테고리 목록**
  - URL: `http://localhost:8080/api/v1/menus/categories`
  - Method: GET

**✅ 확인**

API 1 응답 예시:

```json
[
  {
    "id": 20,
    "categoryName": "커피",
    "korName": "아이스 아메리카노",
    "engName": "Iced Americano",
    "price": 3800,
    "imgSrc": "/images/menus/iced-americano.svg",
    "isLike": false
  }
]
```

API 2 응답 예시:

```json
[
  { "id": 1, "name": "커피", "menuCount": 5 },
  { "id": 2, "name": "티", "menuCount": 2 },
  { "id": 3, "name": "에이드 · 스무디", "menuCount": 2 },
  { "id": 4, "name": "디저트", "menuCount": 2 }
]
```

두 API 모두 200 OK 상태 코드를 반환하고, JSON 데이터가 정상적으로 표시됩니다.

**🎓 newlec 쌤의 코멘트**

이제 1차 구현이 완료되었습니다. 두 API가 정상적으로 동작합니다. 하지만 이 코드는 '일관성' 문제가 있습니다. Menu 엔티티는 menus 테이블과 1:1로 대응하지만, Category 엔티티는 categories 테이블과 1:1로 대응하지 않습니다. Category 엔티티에 menuCount라는 '계산된 값'이 포함되어 있기 때문입니다. 이 문제를 해결하는 것이 다음 단계의 '코드 리뷰'입니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Connection refused` | 서버가 실행되지 않음 | `./gradlew bootRun`이 정상적으로 실행 중인지 확인 |
| `500 Internal Server Error` | DB 연결 실패 또는 SQL 오류 | 콘솔 로그를 확인하여 원인을 파악 |

**📝 이 단계의 핵심**

- 서버 실행
- 두 API가 정상적으로 동작하는지 확인
- 1차 구현 완료

## 11. 코드 리뷰 — 일관성 문제 발견

이제 코드를 다시 살펴보고, '일관성' 문제를 발견합니다.

### 11-1. Menu 엔티티와 Category 엔티티 비교

**Menu 엔티티**:

- menus 테이블의 컬럼만 포함
- categoryName이 없음
- '엔티티 = 테이블 1:1' 원칙을 따름

**Category 엔티티 (1차)**:

- categories 테이블의 컬럼 + menuCount 포함
- menuCount는 categories 테이블에 없는 컬럼
- '엔티티 = 테이블 1:1' 원칙을 위반

### 11-2. 문제점 발견

| 문제 | 설명 |
|---|---|
| 엔티티 불순 | Category 엔티티에 menuCount라는 계산된 값이 포함되어 있음 |
| Repository 책임 혼재 | DfCategoryRepository가 '단순 조회'가 아닌 '비즈니스 로직(카운트)'을 수행 |
| Service의 불필요한 의존성 | DfMenuService는 CategoryRepository를 호출해서 categoryName을 가져옴. 하지만 DfCategoryService는 MenuRepository를 호출하지 않음. 일관성이 없음 |

**핵심 질문**:

- Category 엔티티는 categories 테이블의 순수한 대변자여야 하는가?
- menuCount는 어디에서 계산되어야 하는가?
- DfCategoryService는 MenuRepository를 추가로 호출해서 menuCount를 계산해야 하는가?

**✅ 확인**

- Category 엔티티에 menuCount가 포함되어 있음을 확인
- DfCategoryRepository의 SQL에 COUNT가 포함되어 있음을 확인
- DfMenuService와 DfCategoryService의 '조립 방식'이 다름을 확인

**🎓 newlec 쌤의 코멘트**

이제 '일관성' 문제를 발견했습니다. Menu 엔티티는 '순수'하지만, Category 엔티티는 '불순'합니다. 이 '불순'은 menuCount라는 계산된 값이 엔티티에 들어있기 때문입니다. 실무에서는 이런 '불순'을 피하기 위해, 엔티티는 항상 테이블과 1:1로 대응하게 하고, 계산된 값은 Service나 View 객체에서 처리하는 것이 원칙입니다. 이제 이 문제를 해결하기 위해 코드를 수정합니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| 문제점을 발견하지 못함 | '동작하는 코드'에 안주함 | '왜 이렇게 작성했는가?'를 스스로 질문 |

**📝 이 단계의 핵심**

- Category 엔티티의 '불순' 문제 발견
- menuCount는 엔티티에 들어서는 안 됨
- DfCategoryService는 MenuRepository를 추가로 호출해야 함

## 12. Category 엔티티 수정 — menuCount 제거, sortOrder 추가

이제 Category 엔티티를 '순수'하게 수정합니다.

### 12-1. Category.java 파일 수정

`src/main/java/com/newlecture/ncafe/backend/entity/Category.java` 파일을 엽니다.

파일: `src/main/java/com/newlecture/ncafe/backend/entity/Category.java`

```java
package com.newlecture.ncafe.backend.entity;

public class Category {

    private Long id;
    private String name;
    private Integer sortOrder; // categories 테이블의 컬럼 추가
    // menuCount 제거

    public Category() {
    }

    // getter/setter
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public Integer getSortOrder() { return sortOrder; }
    public void setSortOrder(Integer sortOrder) { this.sortOrder = sortOrder; }
}
```

**변경 사항**

- menuCount 필드 제거
- sortOrder 필드 추가 (categories 테이블의 컬럼)
- 이제 Category 엔티티는 categories 테이블과 1:1로 대응

**✅ 확인**

```bash
./gradlew compileJava
```

`BUILD SUCCESSFUL`이 표시됩니다.

**🎓 newlec 쌤의 코멘트**

이제 Category 엔티티는 '순수'해졌습니다. categories 테이블의 컬럼만 가지고 있습니다. menuCount는 더 이상 엔티티에 들어있지 않습니다. 이제 menuCount는 Service에서 계산해야 합니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Cannot find symbol: method getMenuCount()` | 다른 곳에서 `getMenuCount()`를 호출 | 다음 단계에서 DfCategoryRepository와 DfCategoryService를 수정 |

**📝 이 단계의 핵심**

- Category 엔티티 수정
- menuCount 제거, sortOrder 추가
- 엔티티 = 테이블 1:1 원칙 준수

## 13. CategoryRepository 인터페이스 수정

이제 CategoryRepository 인터페이스를 수정합니다.

### 13-1. CategoryRepository.java 파일 수정

`src/main/java/com/newlecture/ncafe/backend/repository/CategoryRepository.java` 파일을 엽니다.

파일: `src/main/java/com/newlecture/ncafe/backend/repository/CategoryRepository.java`

```java
package com.newlecture.ncafe.backend.repository;

import java.util.List;
import com.newlecture.ncafe.backend.entity.Category;

public interface CategoryRepository {
    // findAllWithMenuCount() → findAll()로 변경
    List<Category> findAll();
}
```

**변경 사항**

- `findAllWithMenuCount()` → `findAll()`로 변경
- 이제 '단순 조회'만 수행

**✅ 확인**

```bash
./gradlew compileJava
```

`BUILD SUCCESSFUL`이 표시됩니다.

**🎓 newlec 쌤의 코멘트**

이제 CategoryRepository는 '단순 조회'만 수행합니다. menuCount를 계산하지 않습니다. menuCount는 Service에서 계산합니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `CategoryRepository is not abstract and does not implement abstract method` | 구현체(DfCategoryRepository)가 아직 수정되지 않음 | 다음 단계에서 DfCategoryRepository를 수정 |

**📝 이 단계의 핵심**

- CategoryRepository 인터페이스 수정
- `findAllWithMenuCount()` → `findAll()`

## 14. DfCategoryRepository 수정 — JOIN + COUNT 제거

이제 DfCategoryRepository 구현체를 수정합니다.

### 14-1. DfCategoryRepository.java 파일 수정

`src/main/java/com/newlecture/ncafe/backend/repository/DfCategoryRepository.java` 파일을 엽니다.

파일: `src/main/java/com/newlecture/ncafe/backend/repository/DfCategoryRepository.java`

```java
package com.newlecture.ncafe.backend.repository;

import java.util.List;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import com.newlecture.ncafe.backend.entity.Category;

@Repository
public class DfCategoryRepository implements CategoryRepository {

    private final JdbcTemplate jdbcTemplate;

    public DfCategoryRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public List<Category> findAll() {
        // JOIN + COUNT 제거, 단순 SELECT
        String sql = "SELECT id, name, sort_order FROM categories ORDER BY sort_order";

        return jdbcTemplate.query(sql, new RowMapper<Category>() {
            @Override
            public Category mapRow(java.sql.ResultSet rs, int rowNum) throws java.sql.SQLException {
                Category category = new Category();
                category.setId(rs.getLong("id"));
                category.setName(rs.getString("name"));
                category.setSortOrder(rs.getInt("sort_order"));
                // menuCount 제거
                return category;
            }
        });
    }
}
```

**변경 사항**

- SQL: LEFT JOIN + COUNT 제거, 단순 SELECT
- RowMapper: menuCount 설정 제거, sortOrder 설정 추가
- 이제 DfCategoryRepository는 '단순 조회'만 수행

**✅ 확인**

```bash
./gradlew compileJava
```

`BUILD SUCCESSFUL`이 표시됩니다.

**🎓 newlec 쌤의 코멘트**

이제 DfCategoryRepository는 '단순 조회'만 수행합니다. menuCount를 계산하지 않습니다. menuCount는 Service에서 계산합니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `SQLSyntaxErrorException: column "sort_order" does not exist` | DB 스키마에 sort_order 컬럼이 없음 | DB 스키마 확인, 없으면 추가 또는 SQL 수정 |

**📝 이 단계의 핵심**

- DfCategoryRepository 수정
- JOIN + COUNT 제거, 단순 SELECT
- menuCount 설정 제거, sortOrder 설정 추가

## 15. DfCategoryService 수정 — menuCount를 Service에서 계산

이제 DfCategoryService를 수정해서, menuCount를 Service에서 계산합니다.

### 15-1. DfCategoryService.java 파일 수정

`src/main/java/com/newlecture/ncafe/backend/service/DfCategoryService.java` 파일을 엽니다.

파일: `src/main/java/com/newlecture/ncafe/backend/service/DfCategoryService.java`

```java
package com.newlecture.ncafe.backend.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;

import com.newlecture.ncafe.backend.dto.menu.CategoryListResponseDto;
import com.newlecture.ncafe.backend.entity.Category;
import com.newlecture.ncafe.backend.entity.Menu;
import com.newlecture.ncafe.backend.repository.CategoryRepository;
import com.newlecture.ncafe.backend.repository.MenuRepository;

@Service
public class DfCategoryService implements CategoryService {

    private final CategoryRepository categoryRepository;
    private final MenuRepository menuRepository; // 추가

    public DfCategoryService(CategoryRepository categoryRepository, MenuRepository menuRepository) {
        this.categoryRepository = categoryRepository;
        this.menuRepository = menuRepository; // 추가
    }

    @Override
    public List<CategoryListResponseDto> findAll() {
        // 1. 카테고리 목록 조회 (날것)
        List<Category> categories = categoryRepository.findAll();

        // 2. 메뉴 목록 조회 (날것)
        List<Menu> menus = menuRepository.findAll();

        // 3. categoryId → menuCount 매핑 Map 생성
        Map<Long, Long> menuCountMap = menus.stream()
                .collect(Collectors.groupingBy(Menu::getCategoryId, Collectors.counting()));

        // 4. Category 엔티티를 DTO로 변환
        List<CategoryListResponseDto> list = new ArrayList<>();
        for (Category category : categories) {
            CategoryListResponseDto dto = new CategoryListResponseDto();
            dto.setId(category.getId());
            dto.setName(category.getName());
            // menuCount를 Map에서 가져와서 설정
            dto.setMenuCount(menuCountMap.getOrDefault(category.getId(), 0L).intValue());
            list.add(dto);
        }
        return list;
    }
}
```

**변경 사항**

- MenuRepository를 추가로 주입
- `menuRepository.findAll()` 호출
- `Map<categoryId, menuCount>` 생성
- menuCount를 Map에서 가져와서 DTO에 설정
- 이제 menuCount는 Service에서 계산

**✅ 확인**

```bash
./gradlew compileJava
```

`BUILD SUCCESSFUL`이 표시됩니다.

**🎓 newlec 쌤의 코멘트**

이제 DfCategoryService는 MenuRepository를 추가로 호출해서 menuCount를 계산합니다. Category 엔티티는 '순수'하고, menuCount는 Service에서 계산됩니다. 이제 DfMenuService와 DfCategoryService의 '조립 방식'이 일관됩니다. 둘 다 MenuRepository와 CategoryRepository를 호출해서 데이터를 조립합니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `NullPointerException in menuCountMap.get()` | categoryId가 null이거나 Map에 없는 key | `getOrDefault`를 사용 (이미 적용) |

**📝 이 단계의 핵심**

- DfCategoryService 수정
- MenuRepository 추가로 주입
- menuCount를 Service에서 계산
- DfMenuService와 일관된 조립 방식

## 16. DfMenuService 수정 — findAllWithMenuCount → findAll

이제 DfMenuService를 수정해서, CategoryRepository의 `findAll()`을 사용합니다.

### 16-1. DfMenuService.java 파일 수정

`src/main/java/com/newlecture/ncafe/backend/service/DfMenuService.java` 파일을 엽니다.

파일: `src/main/java/com/newlecture/ncafe/backend/service/DfMenuService.java`

```java
package com.newlecture.ncafe.backend.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;

import com.newlecture.ncafe.backend.dto.menu.MenuListRequestDto;
import com.newlecture.ncafe.backend.dto.menu.MenuListResponseDto;
import com.newlecture.ncafe.backend.entity.Category;
import com.newlecture.ncafe.backend.entity.Menu;
import com.newlecture.ncafe.backend.repository.CategoryRepository;
import com.newlecture.ncafe.backend.repository.MenuRepository;

@Service
public class DfMenuService implements MenuService {

    private final MenuRepository menuRepository;
    private final CategoryRepository categoryRepository;

    public DfMenuService(MenuRepository menuRepository, CategoryRepository categoryRepository) {
        this.menuRepository = menuRepository;
        this.categoryRepository = categoryRepository;
    }

    @Override
    public List<MenuListResponseDto> getList(MenuListRequestDto requestDto) {
        // 1. 메뉴 목록 조회 (날것)
        List<Menu> menus = menuRepository.findAll();

        // 2. 카테고리 목록 조회 (날것)
        List<Category> categories = categoryRepository.findAll(); // findAllWithMenuCount() → findAll()

        // 3. categoryId → categoryName 매핑 Map 생성
        Map<Long, String> categoryNameMap = categories.stream()
                .collect(Collectors.toMap(Category::getId, Category::getName));

        // 4. Menu 엔티티를 DTO로 변환
        List<MenuListResponseDto> list = new ArrayList<>();
        for (Menu menu : menus) {
            MenuListResponseDto dto = new MenuListResponseDto();
            dto.setId(menu.getId());
            dto.setCategoryName(categoryNameMap.get(menu.getCategoryId()));
            dto.setKorName(menu.getKorName());
            dto.setEngName(menu.getEngName());
            dto.setPrice(menu.getPrice());
            dto.setImgSrc(menu.getImgSrc());
            dto.setIsLike(false);
            list.add(dto);
        }
        return list;
    }
}
```

**변경 사항**

- `categoryRepository.findAllWithMenuCount()` → `categoryRepository.findAll()`
- 이제 Category 엔티티는 '순수'하므로, categoryName만 Map에서 가져옴

**✅ 확인**

```bash
./gradlew compileJava
```

`BUILD SUCCESSFUL`이 표시됩니다.

**🎓 newlec 쌤의 코멘트**

이제 DfMenuService는 CategoryRepository의 `findAll()`을 사용합니다. Category 엔티티는 '순수'하므로, categoryName만 Map에서 가져옵니다. 이제 모든 코드가 '엔티티 = 테이블 1:1' 원칙을 따릅니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `IllegalStateException: Duplicate key` | categories에 중복된 id가 있음 | DB 데이터 무결성 확인 |

**📝 이 단계의 핵심**

- DfMenuService 수정
- `findAllWithMenuCount()` → `findAll()`
- 모든 코드가 '엔티티 = 테이블 1:1' 원칙 준수

## 17. 최종 테스트 & API 확인

이제 서버를 다시 실행해서 두 API가 정상적으로 동작하는지 확인합니다.

### 17-1. 서버 재실행

터미널에서 `Ctrl+C`로 기존 서버를 종료하고, 아래 명령을 실행합니다.

```bash
./gradlew bootRun
```

`Started Application in X.XXX seconds` 메시지가 나오면 서버가 실행된 것입니다.

### 17-2. Postman 또는 브라우저로 API 호출

- **API 1: 메뉴 목록**
  - URL: `http://localhost:8080/api/v1/menus`
  - Method: GET
- **API 2: 카테고리 목록**
  - URL: `http://localhost:8080/api/v1/menus/categories`
  - Method: GET

**✅ 확인**

API 1 응답 예시:

```json
[
  {
    "id": 20,
    "categoryName": "커피",
    "korName": "아이스 아메리카노",
    "engName": "Iced Americano",
    "price": 3800,
    "imgSrc": "/images/menus/iced-americano.svg",
    "isLike": false
  }
]
```

API 2 응답 예시:

```json
[
  { "id": 1, "name": "커피", "menuCount": 5 },
  { "id": 2, "name": "티", "menuCount": 2 },
  { "id": 3, "name": "에이드 · 스무디", "menuCount": 2 },
  { "id": 4, "name": "디저트", "menuCount": 2 }
]
```

- 두 API 모두 200 OK 상태 코드를 반환하고, JSON 데이터가 정상적으로 표시됩니다.
- 응답은 1차 구현과 동일합니다.
- 바뀐 것은 내부 구조입니다.
- Category 엔티티는 '순수'해졌습니다.
- menuCount는 Service에서 계산됩니다.
- 모든 코드가 '엔티티 = 테이블 1:1' 원칙을 따릅니다.

**🎓 newlec 쌤의 코멘트**

이제 최종 구현이 완료되었습니다. 두 API는 1차 구현과 동일한 응답을 반환하지만, 내부 구조는 '일관성'이 있습니다. Menu 엔티티와 Category 엔티티 모두 '순수'하고, menuCount는 Service에서 계산됩니다. 이것이 '엔티티 = 테이블 1:1' 원칙의 힘입니다. 이제 이 코드는 유지보수가 쉽고, 확장성이 높습니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `500 Internal Server Error` | DB 연결 실패 또는 SQL 오류 | 콘솔 로그를 확인하여 원인을 파악 |

**📝 이 단계의 핵심**

- 서버 재실행
- 두 API가 정상적으로 동작하는지 확인
- 응답은 1차와 동일, 내부 구조는 '일관성' 있음
- '엔티티 = 테이블 1:1' 원칙 준수

## 정리

1. 1단계: build.gradle에 JDBC 의존성 추가
2. 2단계: application.properties에 DB 연결 정보 설정
3. 3단계: Category 엔티티 생성 (1차: menuCount 포함)
4. 4단계: CategoryRepository 인터페이스 작성 (1차: findAllWithMenuCount)
5. 5단계: DfMenuRepository 구현 — JdbcTemplate로 menus 테이블 조회
6. 6단계: DfCategoryRepository 구현 (1차: LEFT JOIN + COUNT)
7. 7단계: DfMenuService (1차: 두 Repository의 날것을 DTO로 조립)
8. 8단계: DfCategoryService (1차: Category 엔티티를 DTO로 변환)
9. 9단계: MenuController에 categories 엔드포인트 추가
10. 10단계: 1차 구현 테스트 — Postman이나 브라우저로 두 API 확인
11. 11단계: 코드 리뷰 — Menu와 Category의 일관성 문제 발견
12. 12단계: Category 엔티티 수정 (menuCount 제거, sortOrder 추가)
13. 13단계: CategoryRepository 수정 (findAllWithMenuCount → findAll)
14. 14단계: DfCategoryRepository 수정 (JOIN + COUNT 제거, 단순 SELECT)
15. 15단계: DfCategoryService 수정 (MenuRepository 추가로 주입받아 menuCount를 Service에서 조립)
16. 16단계: DfMenuService 수정 (findAllWithMenuCount → findAll)
17. 17단계: 최종 테스트 & API 확인 — 응답은 1차와 동일, 바뀐 것은 내부 구조
