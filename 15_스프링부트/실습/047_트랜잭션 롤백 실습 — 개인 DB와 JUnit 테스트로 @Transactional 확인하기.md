---
tags: [스프링부트, 트랜잭션, Transactional, JUnit, SpringBootTest, PostgreSQL, 실습]
---

> 🔗 관련 노트: [[088_트랜잭션 — 논리적 작업 단위와 @Transactional 롤백 원리]] · [[084_트랜잭션 — 작업 단위, ACID, 그리고 스프링 @Transactional이 필요한 이유]] · [[046_PostgreSQL 제약조건 실습 — NOT NULL, DEFAULT, CHECK, PK, FK]]

# 트랜잭션 롤백 실습 — 개인 DB와 JUnit 테스트로 @Transactional 확인하기

**대상**: 트랜잭션 개념과 JPA 엔티티·리포지토리를 배웠고, `@Transactional`이 실제로 롤백하는지 직접 보고 싶은 사람

**목표**: 개인 DB와 별도 연습 프로젝트를 만들고, JUnit 테스트로 서비스를 실행하면서 제약조건 위반으로 실패를 일으켜 `@Transactional` 유무에 따라 DB에 남는 데이터를 비교한다

**완성물**: 개인 DB에 연결된 `demo` 프로젝트, `CategoryService`와 이를 실행하는 `CategoryServiceTest`

> **왜 따로 만드나**: 공용 프로젝트와 공용 DB로 테스트하면 테이블과 데이터가 서로 엉킨다. 이 실습은 데이터를 넣고 지우며 실패도 일부러 일으키므로, **각자의 DB**와 **별도의 프로젝트**에서 진행한다.

## 1. 개인 데이터베이스 만들기

서버(PostgreSQL)에 접속해서 다음 두 명령을 실행한다. `계정명` 부분은 반드시 자기 계정으로 바꾼다.

**1-1. 데이터베이스 생성**

```bash
sudo -u postgres psql -c "CREATE DATABASE 계정명db;"
# → CREATE DATABASE
```

- `sudo -u postgres`: 리눅스의 `postgres` 사용자로 명령을 실행한다. 이 사용자는 PostgreSQL 관리자 권한을 가진다.
- `psql -c "..."`: psql 셸에 들어가지 않고 명령 하나만 실행하고 나온다. 셸에 직접 들어가서(`sudo -u postgres psql`) `CREATE DATABASE`를 입력해도 결과는 같다.

**1-2. 앱 계정에 권한 주기**

접속용 사용자를 따로 만들지 않고, 이미 있는 `ncafe` 계정이 새 DB의 `public` 스키마를 모두 쓸 수 있게 한다.

```bash
sudo -u postgres psql -d 계정명db -c "GRANT ALL ON SCHEMA public TO ncafe;"
# → GRANT
```

> **추가 설명 — 왜 GRANT가 필요한가**: PostgreSQL 15부터는 `public` 스키마에 **아무나 테이블을 만들 수 없게** 기본 권한이 바뀌었다. DB를 만든 것은 `postgres` 관리자이므로, `ncafe` 계정으로 접속해 테이블을 만들려면 `public` 스키마 권한을 따로 줘야 한다. 단, `GRANT`는 **권한을 빌려주는 것**이지 소유권을 넘기는 것이 아니다. DB의 소유자는 여전히 `postgres`다. 소유자 자체를 바꾸려면 `ALTER DATABASE 계정명db OWNER TO ncafe;`를 쓴다.

**✅ 확인**

- VS Code의 데이터베이스 확장에서 새로고침하면, `ncafe` 계정으로 볼 수 있는 계정별 DB 목록에 내 DB가 보인다.

## 2. 연습 프로젝트 만들기

1. VS Code에서 `Ctrl+Shift+P` → **Spring Initializr: Create a Gradle Project**
2. 언어 Java, 패키지 `com.example`, 프로젝트 이름 `demo`, 패키징 Jar, Java 21
3. 의존성 다섯 개 선택

| 의존성 | 용도 |
|---|---|
| Spring Web | 웹 애플리케이션 기본 |
| Spring Data JPA | 엔티티·리포지토리 |
| Lombok | `@Getter`, `@ToString` 등 반복 코드 생략 |
| **PostgreSQL Driver** | PostgreSQL 연결 — **반드시 넣어야 한다** |
| Spring Boot DevTools | 코드 변경 시 자동 재시작 (필수는 아님) |

## 3. application.yml 설정

`src/main/resources/application.properties`를 복사해서 이름을 `application.yml`로 바꾸고 연결 정보를 넣는다.

```yaml
spring:
  datasource:
    url: jdbc:postgresql://서버주소:포트/계정명db
    username: ncafe
    password: ********
  jpa:
    show-sql: true                 # Hibernate가 만든 SQL을 콘솔에 출력
    hibernate:
      ddl-auto: create-drop        # 시작 시 테이블 생성, 종료 시 삭제
```

> **`application.properties`는 지워야 하나?** 지우지 않아도 된다. 두 파일이 모두 있으면 **둘 다 적용**된다. 다만 같은 설정 키가 양쪽에 있으면 **`.properties` 쪽 값이 우선**한다. 실수로 서로 다른 값을 넣어 헷갈릴 염려가 있다면 지우는 것이 깔끔하다.

`ddl-auto` 각 값의 의미는 [[088_트랜잭션 — 논리적 작업 단위와 @Transactional 롤백 원리]]에 정리했다. 이 실습에서는 6단계에서 값을 바꿔 가며 직접 결과를 확인한다.

## 4. 엔티티 · 리포지토리 · 서비스 만들기

`entity`, `repository`, `service` 폴더를 만들고 카테고리 기능을 구성한다. (강의에서 받은 코드를 바탕으로 핵심만 정리했다.)

**4-1. 엔티티**

파일: `entity/Category.java`

```java
@Entity
@Table(name = "categories")
@Getter @Setter
@NoArgsConstructor
@ToString
public class Category {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)               // NOT NULL
    private String name;

    @Column(nullable = false, unique = true) // NOT NULL + UNIQUE
    private String slug;

    public Category(String name, String slug) {
        this.name = name;
        this.slug = slug;
    }
}
```

> **추가 설명 — slug란**: **URL에 사용되는 식별자**다. `id`와 다른 점은 **그 페이지를 설명하는 내용이 URL에 들어간다**는 것이다.
>
> ```
> /categories/3        ← id: 무엇인지 알 수 없다
> /categories/coffee   ← slug: 주소만 봐도 커피 카테고리인 걸 안다
> ```
>
> - 사용자에게 노출되는 URL에는 slug를 쓰고, 노출할 필요가 없으면 굳이 쓰지 않는다.
> - 한글, 특수문자, 빈칸은 쓰지 않는다. 영문 소문자, 숫자, 하이픈(`-`)을 쓴다.
> - 이름과 별개로 **URL용 버전을 한 번 더 만드는 것**이다. 영어는 이름에서 특수문자만 처리하면 자동으로 만들 수 있지만, 한글은 자동 변환이 어려워 사람이 직접 입력하는 경우가 많다.
> - 주소로 쓰이므로 겹치면 안 된다. 그래서 `unique = true`를 건다.

**4-2. 리포지토리**

파일: `repository/CategoryRepository.java`

```java
public interface CategoryRepository extends JpaRepository<Category, Long> {
    Optional<Category> findBySlug(String slug);   // slug로 카테고리 찾기
}
```

**4-3. 서비스**

파일: `service/CategoryService.java`

```java
@Service
public class CategoryService {

    private final CategoryRepository categoryRepository;

    public CategoryService(CategoryRepository categoryRepository) {  // 생성자 주입
        this.categoryRepository = categoryRepository;
    }

    public Category create(String name, String slug) {
        Category category = new Category(name, slug);
        return categoryRepository.save(category);    // 저장된 엔티티를 그대로 반환
    }
}
```

- **생성자 주입**: 생성자의 매개변수로 리포지토리를 받기만 하면 스프링이 IoC 컨테이너에서 찾아 자동으로 넣어준다(생성자가 하나면 `@Autowired` 생략 가능).
- **`final`**: 한 번 주입되면 다른 객체로 바꿀 수 없게 잠근다.
- 자동 주입이 되려면 서비스 자신도 컨테이너에 있어야 하므로 `@Service`를 붙인다.
- **`save()`는 왜 반환값이 있나**: `save()`는 저장한 엔티티를 돌려준다. `IDENTITY` 전략이면 DB가 만든 `id`가 채워진 상태다. 이 값을 그대로 반환하면 호출한 쪽에서 방금 만든 데이터를 바로 확인할 수 있다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| 서비스에서 엉뚱한 타입을 `private final`로 선언해 빨간 줄 | 서비스 안에 서비스 자신을 필드로 씀 | 필드 타입을 `CategoryRepository`로 고친다 |
| 필드에 빨간 줄 (초기화되지 않음) | `final` 필드를 초기화하는 생성자가 없음 | 리포지토리를 받는 생성자를 추가한다 |

## 5. JUnit 테스트로 서비스 실행하기

### 왜 main 함수로는 안 되나

예전에는 `App.java`에 `main()`을 만들어 코드를 실행해 봤다. 하지만 `main()`에서 `new CategoryService(...)`를 해서는 이 서비스를 테스트할 수 없다. 리포지토리는 스프링이 만든 구현 객체가 필요하고, DB 연결과 JPA 기능도 스프링이 준비해줘야 하는데, 그냥 `main()`으로는 **IoC 컨테이너가 만들어지지 않기 때문**이다.

그렇다고 매번 컨트롤러를 만들고 부트를 실행해서 URL을 호출하는 것(통합 테스트)은 번거롭다. **IoC 컨테이너를 띄우면서도 main 함수처럼 간단히 실행**할 수 있는 것이 테스트 클래스다.

**5-1. 테스트 파일 생성**

1. `CategoryService.java`에서 마우스 오른쪽 → **Source Action** → **Generate Tests**
2. 패키지와 클래스 이름(`com.example.demo.service.CategoryServiceTest`)을 확인하고 Enter
3. 테스트할 메서드 선택 화면은 그냥 Enter

생성된 파일은 `src/main`과 같은 높이에 있는 **`src/test`** 폴더 안, 같은 패키지 경로에 만들어진다.

```
src/
├── main/java/com/example/demo/service/CategoryService.java
└── test/java/com/example/demo/service/CategoryServiceTest.java
```

다시 오른쪽 클릭 → Generate Tests에서 메서드(`create`)를 선택하면, 이미 만든 테스트 파일에 그 메서드를 위한 테스트 함수가 추가된다. 서비스 메서드마다 테스트 함수를 따로 만들 수 있다는 뜻이다.

**5-2. 테스트 함수 감 잡기**

```java
@Test
void hello() {
    System.out.println("Hello");
}
```

`@Test`를 붙인 메서드는 **실행할 수 있는 단위**가 된다. 이름은 마음대로 지어도 되고 여러 개 만들어도 된다. 왼쪽의 실행 화살표를 누르면 그 메서드만 실행되고, 출력은 **디버그 콘솔**에 나온다. "테스트용 main 함수를 원하는 만큼 만든다"고 생각하면 된다. 도구로 만들지 않고 직접 작성해도 `@Test`만 붙이면 된다.

**5-3. 서비스 주입받아 실행하기**

파일: `src/test/java/com/example/demo/service/CategoryServiceTest.java`

```java
@SpringBootTest
class CategoryServiceTest {

    @Autowired
    private CategoryService categoryService;

    @Test
    void create() {
        Category category = categoryService.create("Coffee", "coffee");
        System.out.println(category);
    }
}
```

- **`@SpringBootTest`**: 테스트를 실행할 때 스프링 부트 애플리케이션 컨텍스트(IoC 컨테이너)를 띄운다. 그래야 `@Autowired`로 서비스를 꺼내 쓸 수 있다.
- **필드 주입 `@Autowired`**: 서비스 코드에서는 생성자 주입이 권장되지만, 테스트 클래스는 스프링이 아니라 JUnit이 객체를 만들기 때문에 필드에 `@Autowired`를 붙이는 방식을 흔히 쓴다. 테스트에서는 이것이 좋다 나쁘다를 따지지 않는다.

> 강의에서는 테스트용 어노테이션이 "부트 전체를 로드하지 않고 테스트 목적으로만 간단하게 연다"고 설명했지만, `@SpringBootTest`는 **애플리케이션 전체 빈을 모두 로드**한다. 일부만 로드하는 것은 `@DataJpaTest`(JPA 관련 빈만), `@WebMvcTest`(웹 계층만) 같은 **슬라이스 테스트** 어노테이션이다. 또 `@SpringBootTest`의 기본값은 가짜 웹 환경(MOCK)이라 실제 톰캣 서버는 띄우지 않는다. 실제 서버까지 띄우려면 `webEnvironment = WebEnvironment.RANDOM_PORT` 등을 지정한다.

**5-4. toString — 출력 결과 보기 좋게 만들기**

`toString()`을 따로 만들지 않은 객체를 출력하면 이런 값이 나온다.

```
com.example.demo.entity.Category@1a2b3c4d
```

모든 클래스의 부모인 `Object`가 `toString()`을 **`클래스 이름 + "@" + 해시코드(16진수)`**로 기본 구현해 두었기 때문이다. 안에 든 값을 보고 싶다면 `toString()`을 오버라이드한다.

```java
@Override
public String toString() {
    return String.format("Category[id=%d, name=%s, slug=%s]", id, name, slug);
}
```

매번 쓰기 귀찮으므로 보통 Lombok의 `@ToString`을 붙인다(4-1의 엔티티에 이미 붙어 있다).

> **추가 설명 — 연관관계가 있으면 @ToString 주의**: `Category`가 `List<Menu>`를 갖고 `Menu`도 `Category`를 가지는 양방향 관계라면, 서로의 `toString()`을 계속 호출해 `StackOverflowError`가 난다. 또 지연 로딩 필드까지 출력하느라 의도치 않은 쿼리가 나간다. 이런 필드는 `@ToString.Exclude`로 뺀다.

**5-5. 테스트 전용 설정 파일**

`src/test` 아래에 `resources` 폴더를 만들고 설정 파일을 복사해 둔다. 테스트 설정은 운영 설정과 분리해야 마음대로 망가뜨릴 수 있고, 다른 DB를 써도 된다.

```
src/test/resources/application.yml   ← 테스트용 설정
```

> 강의에서는 테스트 폴더를 "별도의 부트 프로젝트"라고 설명했지만 정확히는 그렇지 않다. 테스트를 실행하면 `src/main`의 클래스와 리소스도 **함께 클래스패스에 올라간다**(그래서 서비스 코드를 그대로 가져다 테스트할 수 있다). 다만 **같은 이름의 파일이 있으면 `src/test/resources` 쪽이 우선**한다. 그래서 테스트 폴더에 설정 파일이 없으면 main의 설정을 그대로 쓰게 된다.
>
> 테스트용 설정을 따로 두는 방법은 두 가지다.
>
> | 방법 | 파일 | 적용 조건 |
> |---|---|---|
> | 같은 이름으로 덮어쓰기 | `src/test/resources/application.yml` | 테스트 실행 시 자동으로 main의 파일 대신 쓰인다 |
> | 프로필로 분리 | `application-test.yml` | 테스트 클래스에 `@ActiveProfiles("test")`를 붙여야 적용된다. 이때 기본 `application.yml`도 함께 읽고, 같은 키는 `-test` 쪽 값으로 덮어쓴다 |
>
> 강의 중에 파일 이름을 `application-test.yml`로 바꾸라는 안내가 있었는데, 이렇게 바꿨다면 `@ActiveProfiles("test")`를 함께 붙여야 테스트 설정이 실제로 적용된다.

**✅ 확인**

- 디버그 콘솔에 부트가 실행되는 로그와 `insert into categories ...` SQL이 보인다.
- `Category(id=1, name=Coffee, slug=coffee)` 형태로 출력된다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Failed to load ApplicationContext` | IoC 컨테이너 생성 실패. 실습에서는 `DataSource`(DB 커넥션 객체)를 만들지 못한 것이 원인이었다 | **테스트 결과 창이 아니라 디버그 콘솔**에서 원인 메시지를 찾는다. 설정 파일 위치·이름, DB 이름, 접속 정보를 확인한다 |
| 테스트가 엉뚱한 DB/설정으로 실행됨 | 테스트 설정 파일이 적용되지 않고 main의 설정을 씀 | 5-5의 두 방법 중 하나로 테스트 설정을 확실히 적용한다 |
| 콘솔에 한글이 깨짐 | 터미널 인코딩 문제 | 디버그 콘솔에서 확인하거나 터미널 인코딩을 UTF-8로 맞춘다 |

## 6. ddl-auto 값을 바꿔 가며 확인하기

**6-1. create-drop**: 5-3의 테스트를 실행한 뒤 DB의 `public` 스키마를 보면 방금 카테고리를 넣었는데도 **테이블 자체가 없다.** 시작할 때 만들었다가 종료하면서 지웠기 때문이다.

**6-2. create**: 값을 `create`로 바꿔 다시 실행하면 `categories` 테이블과 `coffee` 데이터가 **남아 있다.**

**6-3. update**: DB에서 테이블을 직접 `DROP`한 뒤 `update`로 실행하면, 없는 테이블도 새로 만들어 주고 데이터가 들어간다.

**✅ 확인**

- 이후 단계는 앞에서 넣은 데이터를 보면서 진행해야 하므로 **`update`로 두고** 한 번 더 실행해 둔다.

## 7. 실패를 일으켜 롤백 확인하기

서비스에 카테고리 두 개를 연달아 만드는 메서드를 추가하고, 두 번째에서 제약조건 위반으로 실패하게 한다.

**7-1. 트랜잭션 없이 실행**

파일: `service/CategoryService.java`에 추가

```java
public void createTwo() {
    categoryRepository.save(new Category("Copy", "copy"));  // ① 성공
    categoryRepository.save(new Category(null, "copy-x"));  // ② name이 NULL → NOT NULL 위반
}
```

```java
// CategoryServiceTest
@Test
void createTwo() {
    categoryService.createTwo();
}
```

**✅ 확인**

- ②에서 `null value in column "name" ... violates not-null constraint` 오류가 난다.
- 그런데 DB를 보면 **①의 `copy`가 들어가 있다.**
- 같은 테스트를 다시 실행하면 이번에는 ①에서 `duplicate key value violates unique constraint` 오류가 난다. 이미 들어간 `copy` slug와 겹쳐 UNIQUE 제약에 걸린 것이다.

업무 하나(카테고리 두 개 만들기)가 **절반만 반영된** 상태다. 결함이 이미 DB에 들어갔다.

**7-2. @Transactional 붙여 실행**

```java
@Transactional
public void createTwo() {
    categoryRepository.save(new Category("Copy2", "copy2"));  // ① (UNIQUE 중복을 피하려고 이름을 바꿈)
    categoryRepository.save(new Category(null, "copy2-x"));   // ②
}
```

**✅ 확인**

- ②에서 같은 NOT NULL 오류가 난다.
- DB에 **`copy2`가 없다.** ①까지 함께 롤백되었다.

> **추가 설명 — @Transactional을 테스트 메서드에 붙이면?** `@SpringBootTest` 테스트 메서드에 `@Transactional`을 붙이면, 테스트가 **성공해도 끝나면 무조건 롤백**한다. 테스트 데이터가 DB에 남지 않게 하려는 기능이다. 이 실습처럼 "서비스의 트랜잭션이 실패 시 롤백되는지"를 보려면 `@Transactional`을 **서비스 메서드**에 붙이고, 테스트 메서드에는 붙이지 않아야 결과를 정확히 볼 수 있다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `@Transactional`을 붙였는데도 `copy2`가 남음 | `org.springframework.transaction.annotation.Transactional`이 아닌 다른 패키지의 어노테이션을 import 했거나, 같은 클래스 안의 다른 메서드에서 `createTwo()`를 호출함 | 스프링의 `@Transactional`을 쓰고, 테스트에서 서비스 메서드를 **직접** 호출한다 |
| 7-2에서 ①부터 UNIQUE 오류가 남 | 7-1에서 쓴 slug(`copy`)를 그대로 씀 | slug를 `copy2`처럼 새 값으로 바꾼다 |

**📝 핵심**: `@Transactional`이 없으면 `save()`마다 바로 커밋되어 실패 전의 작업이 DB에 남는다. 붙이면 메서드 전체가 하나의 커넥션·트랜잭션으로 묶여 실패 시 **전부 롤백**된다.
