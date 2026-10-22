---
tags: [스프링부트, 트랜잭션, Transactional, 전파, Propagation, 격리수준, Isolation, MVCC, 참고자료]
---

> 🔗 관련 노트: [[090_트랜잭션 전파 — 서비스가 서비스를 호출할 때]] · [[091_전파 옵션 다시 보기 — 도메인 부모와 트랜잭션 부모, 테스트로 확인하기]] · [[092_트랜잭션 격리 수준 — 읽는 동안 남이 건드리지 못하게]] · [[087_트랜잭션이 필요한 경우와 @Transactional의 커넥션 공유 원리]]

# Spring Boot @Transactional 전파 속성과 격리 수준

Spring Boot에서 AOP 기반으로 작동하는 `@Transactional` 어노테이션은 다양한 옵션을 제공한다. 여러 트랜잭션이 묶여서 실행될 때의 동작을 정의하는 **전파(Propagation) 속성**과, 여러 트랜잭션이 동시에 실행될 때 데이터 일관성을 유지하기 위한 **격리 수준(Isolation Level)** 옵션을 다룬다.

## 1. 트랜잭션 전파(Propagation) 속성

트랜잭션 전파는 이미 진행 중인 트랜잭션이 있는 상태에서 다른 트랜잭션 메서드가 호출될 때, 그 메서드를 **기존 트랜잭션에 참여**시킬지 아니면 **별도의 독립된 트랜잭션**으로 실행할지를 결정하는 설정이다.

### 1-1. 도메인 설계 및 엔티티 구성

자식 도메인 서비스(`MenuService`)가 부모 도메인 서비스(`CategoryService`)를 참조하도록 **단방향** 의존 관계를 설정한다.

예제를 위해 롬복을 쓰지 않는 `Category` 엔티티와 `Menu` 엔티티를 작성한다. `Category` 엔티티의 `slug` 필드에는 DB 유니크 제약 조건을 설정한다. `application.yml`의 `spring.jpa.hibernate.ddl-auto` 옵션을 `update`로 설정하면 PostgreSQL에 유니크 제약 조건이 자동으로 생성된다.

```java
package com.example.demo.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "categories")
public class Category {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;

    @Column(unique = true)
    private String slug;

    public Category() {
    }

    public Category(String name, String slug) {
        this.name = name;
        this.slug = slug;
    }

    public Long getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public String getSlug() {
        return slug;
    }

    @Override
    public String toString() {
        return "Category{" +
                "id=" + id +
                ", name='" + name + '\'' +
                ", slug='" + slug + '\'' +
                '}';
    }
}
```

```java
package com.example.demo.entity;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "menus")
public class Menu {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;
    private int price;

    public Menu() {
    }

    public Menu(String name, int price) {
        this.name = name;
        this.price = price;
    }

    public Long getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public int getPrice() {
        return price;
    }

    @Override
    public String toString() {
        return "Menu{" +
                "id=" + id +
                ", name='" + name + '\'' +
                ", price=" + price +
                '}';
    }
}
```

> **추가 설명 — 이 예제의 Menu에는 카테고리 FK가 없다**: 전파 동작만 보기 위해 두 엔티티를 연관관계 없이 단순하게 만들었다. 그래서 `@BeforeEach`에서 메뉴와 카테고리를 어떤 순서로 지워도 FK 오류가 나지 않는다. 실제 프로젝트처럼 `Menu`가 `Category`를 참조한다면 **메뉴(자식)를 먼저** 지워야 한다.

리포지토리 인터페이스는 다음과 같이 구성한다.

```java
package com.example.demo.repository;

import com.example.demo.entity.Category;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CategoryRepository extends JpaRepository<Category, Long> {
}
```

```java
package com.example.demo.repository;

import com.example.demo.entity.Menu;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MenuRepository extends JpaRepository<Menu, Long> {
}
```

### 1-2. REQUIRED vs REQUIRES_NEW 동작 비교

서비스 계층에서는 `CategoryService`가 카테고리를 저장하고, `MenuService`가 메뉴를 저장하면서 `CategoryService`를 호출한다. DB의 slug 중복 예외(`DataIntegrityViolationException`)가 발생할 때 전파 설정에 따라 **롤백 범위**가 어떻게 달라지는지 확인한다.

```java
package com.example.demo.service;

import com.example.demo.entity.Category;
import com.example.demo.repository.CategoryRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class CategoryService {

    private final CategoryRepository categoryRepository;

    public CategoryService(CategoryRepository categoryRepository) {
        this.categoryRepository = categoryRepository;
    }

    @Transactional(propagation = Propagation.REQUIRED)
    public void createCategoryRequired(String name, String slug) {
        categoryRepository.save(new Category(name, slug));
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void createCategoryRequiresNew(String name, String slug) {
        categoryRepository.save(new Category(name, slug));
    }
}
```

```java
package com.example.demo.service;

import com.example.demo.entity.Menu;
import com.example.demo.repository.MenuRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class MenuService {

    private final MenuRepository menuRepository;
    private final CategoryService categoryService;

    public MenuService(MenuRepository menuRepository, CategoryService categoryService) {
        this.menuRepository = menuRepository;
        this.categoryService = categoryService;
    }

    @Transactional(propagation = Propagation.REQUIRED)
    public void createMenuAndCategoryRequired(String menuName, int price, String categoryName, String slug) {
        menuRepository.save(new Menu(menuName, price));
        categoryService.createCategoryRequired(categoryName, slug);
    }

    @Transactional(propagation = Propagation.REQUIRED)
    public void createMenuAndCategoryRequiresNew(String menuName, int price, String categoryName, String slug) {
        menuRepository.save(new Menu(menuName, price));
        try {
            categoryService.createCategoryRequiresNew(categoryName, slug);
        } catch (Exception e) {
            System.out.println("하위 트랜잭션 예외 포착 및 처리: " + e.getClass().getSimpleName());
        }
    }
}
```

전파 옵션이 붙은 쪽은 **호출당하는 `CategoryService`**(도메인 부모)다. 호출하는 `MenuService`는 둘 다 기본값인 `REQUIRED`로 트랜잭션을 시작할 뿐이다. 두 메서드의 차이는 `REQUIRES_NEW` 쪽만 하위 호출을 `try-catch`로 감쌌다는 점이다.

테스트 클래스로 두 방식을 비교한다. 이미 DB에 slug가 `"beverage"`인 카테고리가 있는 상태에서 같은 slug로 저장을 시도한다.

```java
package com.example.demo;

import com.example.demo.entity.Category;
import com.example.demo.repository.CategoryRepository;
import com.example.demo.repository.MenuRepository;
import com.example.demo.service.CategoryService;
import com.example.demo.service.MenuService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
public class PropagationTest {

    @Autowired
    private MenuService menuService;

    @Autowired
    private CategoryRepository categoryRepository;

    @Autowired
    private MenuRepository menuRepository;

    @BeforeEach
    void setUp() {
        menuRepository.deleteAll();
        categoryRepository.deleteAll();
        categoryRepository.save(new Category("음료", "beverage"));
    }

    @Test
    void testRequiredPropagation() {
        System.out.println("=== REQUIRED 전파 테스트 시작 ===");
        try {
            // 중복된 slug 'beverage' 사용으로 DataIntegrityViolationException 발생
            menuService.createMenuAndCategoryRequired("아메리카노", 4000, "신규음료", "beverage");
        } catch (Exception e) {
            System.out.println("최상위 예외 포착: " + e.getClass().getSimpleName());
        }

        System.out.println("메뉴 테이블 건수: " + menuRepository.count());
        System.out.println("카테고리 테이블 건수: " + categoryRepository.count());
    }

    @Test
    void testRequiresNewPropagation() {
        System.out.println("=== REQUIRES_NEW 전파 테스트 시작 ===");
        // 중복된 slug 'beverage' 사용 시도
        menuService.createMenuAndCategoryRequiresNew("라떼", 4500, "신규음료", "beverage");

        System.out.println("메뉴 테이블 건수: " + menuRepository.count());
        System.out.println("카테고리 테이블 건수: " + categoryRepository.count());
    }
}
```

> **추가 설명 — 테스트 메서드에 @Transactional을 붙이지 않은 이유**: 테스트 메서드에 `@Transactional`을 붙이면 테스트가 끝날 때 자동으로 롤백된다. 또 서비스의 트랜잭션이 **테스트의 트랜잭션에 참여**해 버려서, `REQUIRED`와 `REQUIRES_NEW`의 커밋 차이를 볼 수 없다. 그래서 여기서는 붙이지 않고, `@BeforeEach`에서 매번 데이터를 지우고 다시 넣는다.

테스트 실행 전 DB에는 `@BeforeEach`에 의해 `Category("음료", "beverage")` 1건이 저장되어 있다. 각 테스트 메서드의 단계별 동작과 콘솔 출력은 다음과 같다.

**testRequiredPropagation() 실행 과정**

- 기존 데이터: `Category("음료", "beverage")` (총 1건)
- 실행 단계:
  1. `MenuService.createMenuAndCategoryRequired()`가 시작되며 최상위 트랜잭션이 생성된다.
  2. `Menu("아메리카노", 4000)`를 저장한다.
  3. `CategoryService.createCategoryRequired()`가 호출되며 기존 트랜잭션에 참여(REQUIRED)한다.
  4. 이미 있는 slug `"beverage"`로 `Category("신규음료", "beverage")` 저장을 시도하다가 DB 유니크 제약 조건 위반으로 `DataIntegrityViolationException`이 발생한다.
  5. 예외가 `CategoryService`를 빠져나오며 트랜잭션 전체가 rollback-only로 표시되고, 예외는 그대로 `MenuService` 밖으로 던져진다.
  6. `MenuService`의 프록시가 예외를 보고 전체 트랜잭션을 롤백한다. 저장했던 메뉴도 함께 롤백된다.
- 결과: 메뉴 0건, 카테고리 1건(기존 데이터 유지)

> 원문 바로잡기 — 원문은 5단계에서 "최상위 영역에서 `UnexpectedRollbackException`으로 변환되어 포착된다"고 했고, 콘솔 출력도 `최상위 예외 포착: UnexpectedRollbackException`으로 적었다. 하지만 이 코드에서는 `MenuService`가 예외를 잡지 않으므로, `DataIntegrityViolationException`이 **그대로** 테스트까지 올라온다. 따라서 실제 출력은 `최상위 예외 포착: DataIntegrityViolationException`이다. 수업에서 실행했을 때도 이 예외 이름이 찍혔다.
>
> `UnexpectedRollbackException`은 **바깥 메서드가 안쪽 예외를 `try-catch`로 잡아 버리고 정상 종료하려 할 때** 나온다. 트랜잭션은 이미 rollback-only로 표시되어 있는데 커밋을 시도하니, 스프링이 "커밋하려 했지만 롤백했다"고 알려 주는 예외다. `createMenuAndCategoryRequired()` 안에 `REQUIRES_NEW` 쪽처럼 `try-catch`를 넣으면 이 경우를 직접 확인할 수 있다. 어느 쪽이든 메뉴 0건, 카테고리 1건이라는 결과는 같다.

**testRequiresNewPropagation() 실행 과정**

- 기존 데이터: `Category("음료", "beverage")` (총 1건)
- 실행 단계:
  1. `MenuService.createMenuAndCategoryRequiresNew()`가 시작되며 상위 트랜잭션이 생성된다.
  2. `Menu("라떼", 4500)`를 저장한다.
  3. `CategoryService.createCategoryRequiresNew()`가 호출되며 상위 트랜잭션이 보류(suspend)되고, **새 커넥션으로** 하위 트랜잭션(REQUIRES_NEW)이 생성된다.
  4. 중복 slug `"beverage"`로 `Category("신규음료", "beverage")` 저장을 시도하다가 `DataIntegrityViolationException`이 발생한다.
  5. 독립된 하위 트랜잭션만 롤백되고, 상위 메서드의 `try-catch`가 이 예외를 잡아 처리한다.
  6. 상위 트랜잭션은 예외의 영향을 받지 않고 정상적으로 커밋된다.
- 결과: 메뉴 1건(`"라떼"` 추가), 카테고리 1건(기존 데이터 유지)

실행 콘솔 출력은 다음과 같다(REQUIRED 쪽은 바로잡은 결과).

```
=== REQUIRED 전파 테스트 시작 ===
최상위 예외 포착: DataIntegrityViolationException
메뉴 테이블 건수: 0
카테고리 테이블 건수: 1

=== REQUIRES_NEW 전파 테스트 시작 ===
하위 트랜잭션 예외 포착 및 처리: DataIntegrityViolationException
메뉴 테이블 건수: 1
카테고리 테이블 건수: 1
```

**REQUIRED**의 경우, 하위 `CategoryService`에서 발생한 예외가 하나뿐인 물리 트랜잭션 전체를 rollback-only 상태로 만든다. 따라서 상위 `MenuService`가 저장한 메뉴까지 모두 롤백되어 메뉴 테이블이 0건이 된다.

반면 **REQUIRES_NEW**의 경우, `CategoryService`가 새 물리 트랜잭션을 만들어 실행된다. 카테고리 저장이 실패하면 하위 트랜잭션만 롤백되고, 상위 `MenuService`는 예외를 `try-catch`로 잡은 뒤 자기 트랜잭션을 정상적으로 커밋한다. 그 결과 메뉴 테이블에 1건이 저장된다.

> **추가 설명 — REQUIRES_NEW라도 try-catch가 없으면**: 하위 트랜잭션의 예외를 잡지 않으면 예외가 `MenuService` 밖으로 던져지고, 상위 트랜잭션도 그 예외를 보고 롤백한다. 그러면 메뉴도 0건이 된다. "하위만 롤백, 상위는 커밋"은 **새 트랜잭션 + 예외 처리**가 함께 있어야 성립한다.

DB를 직접 조회(`SELECT * FROM menus;`, `SELECT * FROM categories;`)해도 같은 결과를 확인할 수 있다.

### 1-3. 기타 전파 옵션

- **REQUIRED** (기본값): 기존 트랜잭션이 있으면 참여하고, 없으면 생성한다.
- **REQUIRES_NEW**: 항상 새 트랜잭션을 생성한다. 기존 트랜잭션이 있으면 그 트랜잭션은 보류된다.
- **MANDATORY**: 반드시 기존 트랜잭션 안에서 실행되어야 한다. 기존 트랜잭션이 없으면 `IllegalTransactionStateException`이 발생한다.
- **SUPPORTS**: 기존 트랜잭션이 있으면 참여하고, 없으면 트랜잭션 없이(non-transactional) 실행한다.
- **NOT_SUPPORTED**: 트랜잭션 없이 실행한다. 기존 트랜잭션이 있으면 보류시킨다.
- **NEVER**: 트랜잭션 없이 실행한다. 기존 트랜잭션이 있으면 예외가 발생한다.
- **NESTED**: 기존 트랜잭션이 있으면 중첩(Nested) 트랜잭션을 만들어 실행한다. DB의 세이브포인트(Savepoint) 기능을 쓰며, 중첩 트랜잭션의 롤백은 부모 트랜잭션에 영향을 주지 않는다. (JPA 사용 시 제한이 있다.)

```java
@Transactional(propagation = Propagation.MANDATORY)
public void mandatoryMethod() {
    // 트랜잭션 필수
}
```

> **추가 설명 — NESTED와 REQUIRES_NEW의 차이, JPA에서의 제한**:
>
> | | REQUIRES_NEW | NESTED |
> |---|---|---|
> | 커넥션 | 새 커넥션, 별개의 물리 트랜잭션 | 같은 커넥션, 같은 물리 트랜잭션 안의 세이브포인트 |
> | 안쪽만 롤백 | 가능 | 가능 (세이브포인트까지만 되돌림) |
> | 바깥이 롤백되면 | 안쪽은 이미 커밋되어 **남는다** | 안쪽도 **함께 롤백**된다 |
>
> "중첩 트랜잭션의 롤백은 부모에 영향을 주지 않는다"는 말은 맞지만, 반대로 **부모가 롤백되면 중첩 트랜잭션도 같이 롤백**된다. 또 Spring Boot가 JPA에서 기본으로 쓰는 `JpaTransactionManager`는 세이브포인트를 지원하지 않아서, NESTED를 쓰면 `NestedTransactionNotSupportedException`이 발생한다. JDBC 기반 `DataSourceTransactionManager`에서는 동작한다.

## 2. 트랜잭션 격리 수준(Isolation Level)

트랜잭션 격리 수준은 여러 트랜잭션이 동시에 처리될 때, 한 트랜잭션이 다른 트랜잭션에서 변경하거나 조회하는 데이터를 **어느 정도까지 볼 수 있게 허용할지** 결정하는 설정이다.

```java
@Transactional(isolation = Isolation.READ_COMMITTED)
public List<Menu> getMenus() { ... }
```

### 2-1. 트랜잭션 격리 수준이 필요한 이유와 동시성 문제

트랜잭션은 보통 데이터를 수정하거나 생성할 때 제약 조건 위반 등 오류가 나면 이전 상태로 롤백하려고 적용한다. 그렇다면 데이터를 수정하지 않고 **읽기만** 할 때는 트랜잭션 처리가 필요 없을까?

단순 조회는 제약 조건을 위반할 일이 없으므로 트랜잭션이 필요 없다고 생각하기 쉽다. 하지만 읽기 작업만 하더라도 트랜잭션 처리는 필요하다. **여러 트랜잭션이 동시에 진행되기 때문**이다.

```
[트랜잭션 A]  -- (1) READ -- --------------> -- (2) READ -- --------------> -- (3) READ --
                  |                            |                            ^
[트랜잭션 B]         +------ (다른 작업 개입) -------+                            |
                       [수정/삭제/삽입 후 COMMIT] --------------------------+
```

위 흐름처럼 데이터를 바꾸지 않고 여러 번 읽기만(READ) 해서 전체 결과나 목록을 돌려주는 트랜잭션 A가 있다고 하자. 읽기 전용 작업인데도, 작업이 진행되는 동안 동시에 실행 중인 트랜잭션 B가 끼어들어 데이터를 수정·삭제·삽입하고 커밋할 수 있다.

이처럼 수정이 없는 단순 조회 트랜잭션이라도, 처리하는 데이터가 다른 트랜잭션의 영향을 받지 않으려면 트랜잭션이 끝날 때까지 데이터 상태가 **일관되게** 유지되도록 보호해야 한다. 한 트랜잭션이 진행되는 동안 다른 트랜잭션의 간섭(interference)을 받지 않도록 제어하는 설정이 **격리 수준**(고립화 옵션)이다.

격리 수준을 제대로 설정하지 않아 고립을 보장하지 못하면 다음 3가지 동시성 문제가 생긴다.

- **Dirty Read**: 아직 커밋되지 않은 다른 트랜잭션의 변경 데이터를 읽는 현상이다. 트랜잭션 B가 데이터를 수정하고 커밋하지 않은 상태에서 트랜잭션 A가 이를 조회했는데, 이후 B가 롤백되면 A는 **존재하지 않는 잘못된 데이터**를 읽은 셈이 된다.
- **Non-repeatable Read**: 한 트랜잭션 안에서 **같은 데이터**를 두 번 이상 조회할 때 생긴다. (1) 시점에 A가 데이터를 조회한 뒤, B가 그 데이터를 수정·삭제하고 커밋한다. 이후 (2) 시점에 A가 같은 데이터를 다시 조회하면 이전과 다른 값이 나온다.
- **Phantom Read**: 한 트랜잭션 안에서 **일정 범위**의 데이터를 두 번 이상 조회할 때 생긴다. 즉 같은 조건으로 두 번 SELECT 했을 때 행 수가 다를 수 있다. (1) 시점에 A가 범위 조회를 한 뒤, B가 그 범위에 들어가는 새 데이터를 삽입(INSERT)하고 커밋한다. 이후 (3) 시점에 A가 같은 범위를 다시 조회하면 이전에 없던 데이터(유령 레코드)가 나타난다.

### 2-2. 4가지 격리 수준과 문제 해결 범위

이런 동시성 문제를 막기 위해 DBMS는 4가지 격리 수준을 제공한다. 표의 아래로 갈수록 제어가 강해지고 막을 수 있는 문제의 범위가 넓어진다.

| 격리 수준 | Dirty Read | Non-repeatable Read | Phantom Read |
|---|---|---|---|
| READ UNCOMMITTED | 발생 가능 | 발생 가능 | 발생 가능 |
| READ COMMITTED | 방지 | 발생 가능 | 발생 가능 |
| REPEATABLE READ | 방지 | 방지 | 발생 가능 |
| SERIALIZABLE | 방지 | 방지 | 방지 |

- **READ UNCOMMITTED**: 가장 낮은 격리 수준으로, 커밋되지 않은 데이터까지 읽기를 허용한다. DBMS는 별도의 shared lock(공유 락)을 걸거나 Undo 영역의 이전 버전을 찾지 않고, 메모리 버퍼(Buffer Pool)에 있는 최신 데이터를 직접 읽는 방식으로 동작한다. 데이터 일관성을 보장하지 않으므로 Dirty Read, Non-repeatable Read, Phantom Read가 모두 생길 수 있다.

  > **추가 설명 — DBMS마다 다르다**: 위 동작 방식은 MySQL(InnoDB) 기준이다. **PostgreSQL은 READ UNCOMMITTED를 지정해도 READ COMMITTED와 똑같이 동작**해서 Dirty Read가 아예 일어나지 않는다. Oracle은 READ UNCOMMITTED 자체를 지원하지 않는다(READ COMMITTED와 SERIALIZABLE만 지원).

- **READ COMMITTED**: 커밋이 끝난 데이터만 읽도록 제한한다. DBMS는 데이터를 읽을 때 shared lock을 걸거나, MVCC(Multi-Version Concurrency Control, 다중 버전 동시성 제어) 환경에서는 **SELECT 문을 실행할 때마다** 그 시점의 최신 커밋 스냅샷을 조회한다. 다른 트랜잭션이 작업 중인 커밋 전 변경은 읽지 않으므로 Dirty Read를 해결한다. 하지만 조회 도중 다른 트랜잭션이 커밋하면 다음 조회에 바뀐 값이 반영되므로 Non-repeatable Read와 Phantom Read는 여전히 생긴다.

- **REPEATABLE READ**: 트랜잭션 동안 조회한 데이터가 바뀌어 보이지 않게 한다. DBMS는 읽은 행에 트랜잭션 종료 때까지 shared lock을 유지하거나, MVCC 환경에서 스냅샷을 한 번 만들어 이후 모든 조회가 **같은 스냅샷**을 보게 한다. 한 번 조회한 데이터는 트랜잭션이 끝날 때까지 같은 값으로 유지되므로 Non-repeatable Read를 해결한다. 그러나 행 단위 락만으로는 새 데이터가 추가되는 범위를 완전히 막지 못해 Phantom Read는 생길 수 있다(표준 기준).

  > 원문 바로잡기 — 원문은 "자신보다 **먼저 시작된 트랜잭션**이 변경한 데이터만 읽는다"고 했는데, 정확히는 "자신의 스냅샷이 만들어지기 **전에 커밋된** 데이터만 읽는다"이다. 나보다 먼저 시작했어도 내 스냅샷 이후에 커밋한 트랜잭션의 변경은 보이지 않는다. 또 원문은 스냅샷을 "트랜잭션이 처음 시작된 시점"에 만든다고 했는데, MySQL과 PostgreSQL은 `BEGIN` 순간이 아니라 트랜잭션 안의 **첫 번째 조회문**이 실행될 때 스냅샷을 만든다.

  > **추가 설명 — 스냅샷 방식에서는 Phantom Read도 거의 안 생긴다**: 스냅샷은 그 시점의 테이블 전체 상태를 보여 주므로, 나중에 다른 트랜잭션이 삽입한 행도 보이지 않는다. 그래서 PostgreSQL의 REPEATABLE READ는 표준과 달리 **Phantom Read가 일어나지 않는다**. MySQL은 아래 2-3에서 다룬다.

- **SERIALIZABLE**: 가장 엄격한 격리 수준으로, 여러 트랜잭션을 **차례대로 하나씩 실행한 것과 같은 결과**를 보장한다. DBMS는 범위 검색 때 그 범위 전체에 갭 락(Gap Lock)이나 넥스트 키 락(Next-Key Lock) 같은 인덱스 잠금을 걸거나(MySQL), SSI(Serializable Snapshot Isolation) 기법으로 동시 수정·삽입의 충돌을 감지해 한쪽 트랜잭션을 강제로 롤백시킨다(PostgreSQL). 읽고 있는 데이터 영역 전체에 대해 다른 트랜잭션의 삽입·수정·삭제를 막으므로 Phantom Read를 포함한 모든 동시성 문제를 해결한다. 다만 동시 처리 성능이 크게 떨어질 수 있다.

  > **추가 설명 — SSI에서는 재시도가 필요하다**: PostgreSQL의 SERIALIZABLE은 미리 잠그지 않고 일단 실행한 뒤, 직렬 실행과 결과가 달라질 충돌이 보이면 한쪽을 `could not serialize access` 오류로 실패시킨다. 그래서 이 수준을 쓰는 애플리케이션은 실패한 트랜잭션을 **다시 시도하는 코드**를 함께 두어야 한다.

### 2-3. 주요 DBMS별 기본 격리 수준

주요 RDBMS는 데이터 일관성과 동시 처리 성능 사이의 균형을 고려해 서로 다른 기본 격리 수준을 쓴다.

| DBMS | 기본 격리 수준 (Default Isolation Level) |
|---|---|
| Oracle | READ COMMITTED |
| PostgreSQL | READ COMMITTED |
| Microsoft SQL Server | READ COMMITTED |
| MySQL (InnoDB 엔진) | REPEATABLE READ |

대부분의 RDBMS(Oracle, PostgreSQL, SQL Server 등)는 동시성을 높이면서도 커밋 전 데이터 조회는 막는 **READ COMMITTED**를 기본으로 쓴다. 반면 MySQL의 InnoDB 엔진은 **REPEATABLE READ**를 기본으로 쓰며, MVCC와 갭 락을 활용해 표준 SQL과 달리 REPEATABLE READ에서도 Phantom Read를 대부분 막는다.

> **추가 설명 — 스프링의 Isolation.DEFAULT**: `@Transactional`의 `isolation` 기본값은 `Isolation.DEFAULT`이고, 이는 "DBMS의 기본 격리 수준을 그대로 쓴다"는 뜻이다. 그래서 같은 코드라도 PostgreSQL에서는 READ COMMITTED, MySQL에서는 REPEATABLE READ로 동작한다. DBMS를 바꿀 때 동시성 동작이 달라질 수 있다는 점을 기억해 둔다.
