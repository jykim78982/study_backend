---
tags: [스프링부트, JPA, SpringDataJPA, Optional, Postman, 실습]
---

> 🔗 관련 노트: [[044_JPA 추가하기 — MenuRepository로 첫 API 만들기]] · [[078_ORM과 JPA — 개념부터 API 설계 관점까지]] · [[043_Docker로 팀 공용 PostgreSQL 개발 DB 만들기]]

# JPA 기본 메서드 실습 — Postman으로 CRUD 완성하기

> **주의**: 이 실습은 조별 프로젝트 과제가 아니라 개인 공부용이다. 조별 프로젝트는 공부가 아니라 적용!

**대상**: `Menu` 엔티티와 `MenuRepository`를 만든 뒤, `JpaRepository`가 제공하는 기본 메서드를 직접 호출해보고 싶은 사람

**목표**: `data.sql`로 시드 데이터를 넣고, Postman으로 `save`, `findAll`, `findById`, `existsById`, `deleteById`, `count`를 호출해서 CRUD를 완료한다

**완성물**: 시드 데이터가 로드된 PostgreSQL과, Postman Collection으로 전체 CRUD 흐름을 실행할 수 있는 `MenuAdminController`

**준비물**

- 앞 편(JPA 추가하기)을 마친 상태. `Menu` 엔티티, `MenuRepository`, `MenuAdminController`(POST, GET)가 이미 있다.
- Postman 설치
- `application.yml`에 `spring.sql.init.mode` 설정이 아직 없거나 `never`인 상태
- `data.sql` 파일은 아직 없다.

> **추가 설명 — 반드시 개인 DB에서 할 것**: 이 실습은 `data.sql`로 데이터를 지우고(`DELETE`/`TRUNCATE`) 다시 넣는 작업을 한다. 조 전체가 함께 쓰는 공용 DB(`cloud.newlecture.com:544x`)에 연결한 채로 실행하면 **팀원들이 넣은 데이터가 전부 지워질 수 있다.** 개인 공부용이므로 로컬 Docker로 띄운 PostgreSQL(`localhost:5432`)에 연결해서 진행한다.

> 앞 편과 마찬가지로 원문의 패키지명 `com.new-cafe.backend`는 하이픈 때문에 컴파일되지 않으므로 `com.newcafe.backend`로, 컨트롤러 클래스명은 앞 편에서 만든 `MenuAdminController`로 통일했다.

## 1. data.sql로 시드 데이터 넣기

애플리케이션이 시작될 때 미리 데이터를 넣어두기 위해 `data.sql` 파일을 사용한다. Spring Boot는 `src/main/resources`에 있는 `data.sql`을 자동으로 실행한다.

문제는 실행 순서다. Spring Boot 2.5부터 `data.sql` 같은 SQL 스크립트는 기본적으로 **Hibernate가 테이블을 만들기 전에** 실행된다. 그래서 그대로 두면 테이블이 아직 없는 상태에서 `INSERT`가 실행되어 `relation "menus" does not exist` 오류가 난다. 이를 막으려면 `spring.jpa.defer-datasource-initialization: true`를 추가해서, **JPA의 DDL(테이블 생성·갱신)이 끝난 뒤에 `data.sql`이 실행되도록** 순서를 미뤄야 한다(1-2에서 설정).

**1-1. data.sql 만들기**

파일: `src/main/resources/data.sql`

```sql
-- 시드 데이터: 애플리케이션 시작 시마다 실행된다.
-- 재시작 시 중복 삽입을 막으려면 아래 줄의 주석을 해제한다.
-- TRUNCATE TABLE menus RESTART IDENTITY;

INSERT INTO menus (kor_name, eng_name, price) VALUES ('아메리카노', 'Americano', 4500);
INSERT INTO menus (kor_name, eng_name, price) VALUES ('라떼', 'Latte', 5000);
INSERT INTO menus (kor_name, eng_name, price) VALUES ('카푸치노', 'Cappuccino', 5200);
```

> **추가 설명 — DELETE 대신 TRUNCATE ... RESTART IDENTITY를 쓴 이유**: 원문은 `DELETE FROM menus;`를 쓰지만, `DELETE`는 행만 지우고 **id 자동 증가 번호는 초기화하지 않는다.** 그래서 재시작할 때마다 시드 데이터의 id가 1, 2, 3 → 4, 5, 6 → 7, 8, 9로 계속 밀려서, 6단계의 예상 응답(id 1~4)과 맞지 않게 된다. PostgreSQL의 `TRUNCATE TABLE menus RESTART IDENTITY;`는 데이터를 비우면서 id 번호도 1부터 다시 시작하게 해준다. 또 앞 편에서 POST로 넣은 아메리카노가 이미 1건 있으므로, 처음 한 번은 이 줄의 주석을 풀고 실행해 깨끗한 상태에서 시작하는 것이 좋다.

**1-2. application.yml 수정**

파일: `src/main/resources/application.yml`

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/ncafedb
    username: ncafe
    password: your_password_here
    driver-class-name: org.postgresql.Driver
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: true
    properties:
      hibernate:
        format_sql: true
    # Hibernate가 테이블을 만든 뒤에 data.sql을 실행하도록 순서를 미룬다
    defer-datasource-initialization: true
  sql:
    init:
      # data.sql을 애플리케이션 시작 시마다 실행한다
      mode: always
```

> 원문 예시에는 `defer-datasource-initialization` 설정이 빠져 있고, `mode: always` 줄에 "테이블을 만든 뒤 실행하도록 설정"이라는 주석이 붙어 있다. 하지만 **실행 여부**를 정하는 것이 `mode`이고, **실행 순서**를 정하는 것은 `defer-datasource-initialization`이다. 두 설정이 모두 있어야 한다. `defer-datasource-initialization`은 `spring.jpa` 아래에 들어간다는 점도 주의한다.

**`spring.sql.init.mode` 값의 의미**

| 값 | 동작 |
|---|---|
| `always` | 애플리케이션이 시작될 때마다 `data.sql`을 실행한다 |
| `embedded` | 내장 DB(H2, HSQLDB 등)일 때만 실행한다 (기본값) |
| `never` | 실행하지 않는다 |

기본값이 `embedded`이기 때문에, PostgreSQL처럼 외부 DB를 쓸 때는 `always`로 바꾸지 않으면 `data.sql`이 있어도 실행되지 않는다.

**1-3. 애플리케이션 재시작 및 확인**

```bash
./gradlew bootRun
```

Windows는 `gradlew.bat bootRun`

**✅ 확인**

- 터미널 로그에 `Hibernate: create table menus (...)` 또는 `alter table` 문장이 보인다(테이블이 이미 있으면 생략될 수 있다).
- 이후 DB에 3건의 시드 데이터가 들어간다. psql에서 `SELECT * FROM menus;`로 확인한다.

> `show-sql: true`는 **Hibernate가 만든 SQL**만 출력한다. `data.sql`의 INSERT는 Hibernate가 아니라 Spring Boot의 SQL 초기화 기능이 실행하므로 `Hibernate: insert ...` 형태로는 찍히지 않는다. 시드 데이터가 들어갔는지는 DB를 직접 조회하거나 6-2의 GET 요청으로 확인한다.

**🎓 코멘트**: `spring.sql.init.mode: always`는 개발 환경에서 매우 유용하지만, `data.sql`에 INSERT만 있으면 재시작할 때마다 데이터가 중복으로 쌓인다. 이 실습에서는 간단하게 상단의 초기화 문장을 주석으로 두고, 데이터를 초기화하고 싶을 때만 주석을 푸는 방식으로 진행한다. 더 나은 방법은 테이블 구조는 `schema.sql`, 데이터는 `data.sql`로 분리하거나, **Flyway·Liquibase** 같은 DB 마이그레이션 도구로 "어떤 스크립트를 이미 실행했는지"를 기록하며 관리하는 것이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `relation "menus" does not exist` | `data.sql`이 테이블 생성 전에 실행됨 | `spring.jpa.defer-datasource-initialization: true` 추가 |
| 재시작할 때마다 데이터가 3건씩 늘어남 | 초기화 없이 INSERT만 반복 실행됨 | `data.sql` 상단의 `TRUNCATE ... RESTART IDENTITY` 주석 해제 후 재실행 |
| `data.sql`이 있는데 실행되지 않음 | `spring.sql.init.mode`가 기본값(`embedded`) | `mode: always`로 변경 |
| SQL 구문 오류 | `data.sql`에 BOM 문자 포함 | 파일 인코딩을 UTF-8(BOM 없음)으로 변경 |

> 원문 표의 `Duplicate key value violates unique constraint`는 이 구조에서는 잘 나지 않는다. id를 직접 넣지 않고 자동 생성에 맡기기 때문에, 중복 INSERT는 에러 없이 **같은 메뉴가 새 id로 하나 더 생기는** 형태로 나타난다.

**📝 핵심**: `spring.sql.init.mode: always`로 `data.sql`을 항상 실행하고, `spring.jpa.defer-datasource-initialization: true`로 JPA 테이블 생성 후에 실행되도록 순서를 보장한다.

## 2. findById — 단건 조회와 Optional

`JpaRepository`의 `findById`는 `Optional<T>`를 반환한다. `Optional`은 "값이 있을 수도, 없을 수도 있는 상자"다. 존재하지 않는 id로 조회하면 `null` 대신 **빈 Optional**을 돌려줘서 `NullPointerException`을 막는다.

**2-1. MenuAdminController 수정**

파일: `src/main/java/com/newcafe/backend/api/v1/admin/MenuAdminController.java`

```java
package com.newcafe.backend.api.v1.admin;

import com.newcafe.backend.entity.Menu;
import com.newcafe.backend.repository.MenuRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/api/v1/admin/menus")
@RequiredArgsConstructor
public class MenuAdminController {

    private final MenuRepository menuRepository;

    // 기존: POST /api/v1/admin/menus
    @PostMapping
    public Menu createMenu(@RequestBody Menu menu) {
        return menuRepository.save(menu);
    }

    // 기존: GET /api/v1/admin/menus
    @GetMapping
    public List<Menu> findAllMenus() {
        return menuRepository.findAll();
    }

    // 신규: GET /api/v1/admin/menus/{id}
    @GetMapping("/{id}")
    public ResponseEntity<Menu> getMenuById(@PathVariable Long id) {
        Optional<Menu> menu = menuRepository.findById(id);

        if (menu.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        return ResponseEntity.ok(menu.get());
    }
}
```

빈 Optional이면(존재하지 않는 id) 404 Not Found를, 값이 있으면 `get()`으로 꺼내서 200 OK와 함께 돌려준다.

> **추가 설명 — Optional답게 한 줄로 쓰기**: `isEmpty()` → `get()` 패턴은 이해하기 쉽지만, 결국 "null 체크"를 모양만 바꿔 쓴 것과 같다. Optional이 제공하는 메서드를 쓰면 같은 로직을 분기 없이 쓸 수 있다.
>
> ```java
> @GetMapping("/{id}")
> public ResponseEntity<Menu> getMenuById(@PathVariable Long id) {
>     return menuRepository.findById(id)
>             .map(ResponseEntity::ok)                      // 값이 있으면 200 OK로 감싼다
>             .orElse(ResponseEntity.notFound().build());   // 비어 있으면 404
> }
> ```
>
> 실무에서는 `orElseThrow(() -> new MenuNotFoundException(id))`로 예외를 던지고, 그 예외를 `@RestControllerAdvice` 전역 예외 처리기에서 404 응답으로 바꾸는 방식을 가장 많이 쓴다. 그러면 컨트롤러마다 404 처리 코드를 반복하지 않아도 된다.

**✅ 확인**

- `MenuAdminController`에 `getMenuById` 메서드가 추가된다.
- `java.util.Optional`이 import 되어 있다.
- IDE에서 `menu.isEmpty()`와 `menu.get()`에 빨간 에러가 없다.

**🎓 코멘트**: `Optional`은 Java 8에서 도입된 클래스로, null을 명시적으로 처리하도록 돕는다. `findById`가 Optional을 반환하는 이유는, 없는 id로 조회했을 때 null을 돌려주면 호출하는 쪽이 null 체크를 잊고 `menu.getPrice()`를 호출하다 `NullPointerException`이 나기 때문이다. `Optional.empty()`는 빈 상자, `Optional.of(value)`는 값이 든 상자다. `orElseThrow()`는 빈 상자일 때 예외를 던지고, `orElse(value)`는 빈 상자일 때 기본값을 돌려준다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Cannot resolve method 'isEmpty'` | Java 11 미만 사용 | Java 11 이상 사용, 또는 `!menu.isPresent()`로 변경 |
| `NoSuchElementException` | 빈 Optional에 `get()` 호출 | 반드시 `isEmpty()`/`isPresent()` 확인 후 `get()`, 또는 `orElse`·`orElseThrow` 사용 |

> 원문 표에는 `NullPointerException`으로 되어 있지만, 빈 Optional에서 `get()`을 호출하면 실제로는 `NoSuchElementException: No value present`가 발생한다.

**📝 핵심**: `findById`는 `Optional<T>`를 반환한다. Optional은 null 대신 "값이 없을 수 있다"는 사실을 타입으로 드러낸다.

## 3. existsById — 존재 여부 확인

`existsById`는 특정 id가 존재하는지 `boolean`으로 반환한다. 엔티티 전체를 가져오지 않고 존재 여부만 확인한다.

**3-1. MenuAdminController 수정**

```java
// 신규: GET /api/v1/admin/menus/{id}/exists
@GetMapping("/{id}/exists")
public ResponseEntity<Boolean> existsMenuById(@PathVariable Long id) {
    boolean exists = menuRepository.existsById(id);
    return ResponseEntity.ok(exists);
}
```

**✅ 확인**

- `MenuAdminController`에 `existsMenuById` 메서드가 추가된다.
- 응답 본문이 `true` 또는 `false`다.

**🎓 코멘트**: `existsById`는 존재 여부 확인에 특화된 메서드다. `findById`로 조회해서 `isEmpty()`를 확인하는 것보다 의도가 명확하고, 엔티티의 모든 컬럼을 읽어 객체로 만드는 과정이 없어서 가볍다.

> **추가 설명 — 실제로 실행되는 SQL**: 원문은 `existsById`가 `SELECT 1 ... LIMIT 1`을 실행한다고 설명하지만, Spring Data JPA의 기본 구현은 **id 조건의 count 쿼리**(`select count(m1_0.id) from menus m1_0 where m1_0.id=?`)를 실행한다. `show-sql` 로그로 직접 확인해볼 수 있다. 이것이 느리지 않은 이유는 `WHERE id = ?`가 **기본키 인덱스**를 타서 최대 한 행만 확인하기 때문이다. 참고로 "COUNT(*)는 전체를 스캔한다"는 말은 `WHERE` 조건 없이 테이블 전체 개수를 셀 때(5단계의 `count()`) 해당하는 이야기다.

> **추가 설명 — REST 관점에서 /exists는?**: `/{id}/exists`처럼 동사적인 경로는 학습용으로 메서드를 하나씩 호출해보기 위한 것이다. 실제 API에서는 별도 경로 없이 `GET /{id}`의 200/404로 존재 여부를 판단하거나, 본문 없이 상태 코드만 받는 `HEAD /{id}` 요청을 쓰는 경우가 많다. `existsById`는 주로 서비스 계층 안에서 "중복 확인", "삭제 전 존재 확인" 같은 로직에 쓰인다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `404 Not Found` | URL 경로 오류 | `/api/v1/admin/menus/{id}/exists`인지 확인 |

**📝 핵심**: `existsById`는 `boolean`을 반환하며, 엔티티를 읽지 않고 기본키 조건으로 존재 여부만 확인한다.

## 4. deleteById — 삭제

`deleteById`는 특정 id의 엔티티를 삭제한다. 내부적으로 먼저 `findById`로 조회한 뒤, 존재하면 삭제하고, 존재하지 않으면 아무 일도 하지 않는다.

**4-1. MenuAdminController 수정**

```java
// 신규: DELETE /api/v1/admin/menus/{id}
@DeleteMapping("/{id}")
public ResponseEntity<Void> deleteMenuById(@PathVariable Long id) {
    menuRepository.deleteById(id);
    return ResponseEntity.noContent().build();
}
```

**✅ 확인**

- `MenuAdminController`에 `deleteMenuById` 메서드가 추가된다.
- `ResponseEntity.noContent()`(204 No Content)를 반환한다.

**🎓 코멘트**: `deleteById`는 `void`를 반환한다. 삭제 결과를 확인하려면 삭제 후 `existsById`나 `findById`를 호출해야 한다. 내부적으로는 `findById`로 엔티티를 불러온 뒤 `EntityManager.remove()`를 호출한다. 그래서 콘솔에는 `select`가 먼저 찍히고 그다음 `delete`가 찍힌다. `delete(entity)` 메서드는 id가 아니라 엔티티 객체 자체를 넘겨야 한다는 점이 다르다.

> **추가 설명 — 버전에 따라 동작이 다르다**: 존재하지 않는 id를 넘겼을 때 "아무 일도 하지 않는" 동작은 **Spring Data JPA 3.0(Spring Boot 3) 이후**의 동작이다. 그 이전 버전에서는 `EmptyResultDataAccessException`이 발생했다. 오래된 블로그 예제에서 "deleteById 전에 existsById로 확인하라"는 코드가 많이 보이는 이유다.

> **추가 설명 — 없는 id를 삭제해도 204를 돌려줘도 될까?**: DELETE는 **멱등성**(같은 요청을 여러 번 보내도 결과 상태가 같음)을 가진 메서드다. "삭제 요청 후 그 리소스가 없는 상태"라는 결과는 이미 없던 경우에도 똑같으므로 204를 돌려주는 설계도 흔하다. 반대로 "없는 걸 지우려 했다"는 사실을 클라이언트에 알려야 한다면, 서비스에서 `existsById`로 먼저 확인하고 404를 돌려주는 방식을 쓴다. 둘 중 무엇을 고를지는 팀에서 정하는 API 규칙의 문제다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `405 Method Not Allowed` | HTTP 메서드가 DELETE가 아님 | Postman에서 Method를 DELETE로 변경 |
| `500 Internal Server Error` | 외래키 제약 위반 | 다른 테이블에서 이 id를 참조하고 있는지 확인 |

**📝 핵심**: `deleteById`는 `void`를 반환하며, 존재하지 않는 id로 삭제해도 에러가 나지 않는다(Spring Data JPA 3 이상).

## 5. count — 전체 개수

`count`는 테이블의 전체 행 수를 반환한다. 내부적으로 `SELECT COUNT(*)`를 실행한다.

**5-1. MenuAdminController 수정**

```java
// 신규: GET /api/v1/admin/menus/count
@GetMapping("/count")
public ResponseEntity<Long> countMenus() {
    long count = menuRepository.count();
    return ResponseEntity.ok(count);
}
```

**✅ 확인**

- `MenuAdminController`에 `countMenus` 메서드가 추가된다.
- 응답 본문이 숫자다.

**🎓 코멘트**: `count`는 테이블 전체 행 수를 반환한다. 조건 없는 `COUNT(*)`는 행을 하나하나 세야 하므로 큰 테이블에서는 느려질 수 있다. `menus`처럼 작은 테이블에서는 문제가 없다.

> **추가 설명 — /count와 /{id}가 충돌하지 않는 이유**: `/count`와 `/{id}`는 둘 다 `/api/v1/admin/menus/○○` 모양이라 겹쳐 보인다. 스프링은 요청 경로를 매핑할 때 **변수가 없는 고정 경로(`/count`)를 변수 경로(`/{id}`)보다 우선**하기 때문에, `GET /count`는 `countMenus()`로 정확히 들어간다. 만약 `/count` 매핑이 없다면 `count`라는 글자를 `Long id`로 바꾸려다 실패해 400 Bad Request가 난다.

> **추가 설명 — 목록 화면의 "총 N개"**: 이 `count()`는 필터와 상관없는 **전체 개수**다. 검색 조건이 걸린 목록 화면의 "총 12개" 같은 숫자는 조건이 반영된 개수여야 하므로, 실무에서는 `Pageable`을 받는 `findAll(Pageable)`이 돌려주는 `Page` 객체의 `getTotalElements()`를 쓰는 경우가 많다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `404 Not Found` | URL 경로 오류 | `/api/v1/admin/menus/count`인지 확인 |

**📝 핵심**: `count`는 `long`을 반환하고 `SELECT COUNT(*)`를 실행한다.

## 6. Postman으로 전체 CRUD 흐름 실행

Postman에서 Collection을 만들고, 각 엔드포인트를 순서대로 호출해서 CRUD를 완료한다.

**6-1. Postman Collection 만들기**

Postman에서 New → Collection을 클릭하고 `JPA CRUD`라는 이름의 Collection을 만든다.

> **추가 설명 — 주소를 변수로 빼두기**: Collection 설정의 Variables 탭에 `baseUrl = http://localhost:8080/api/v1/admin/menus`를 등록하면, 각 요청 URL을 `{{baseUrl}}/4`처럼 쓸 수 있다. 나중에 포트나 서버 주소가 바뀌어도 변수 하나만 고치면 된다.

**6-2. 시드 데이터 조회**

- Method: `GET`
- URL: `http://localhost:8080/api/v1/admin/menus`
- Body: 없음

예상 응답(200 OK):

```json
[
  {"id": 1, "korName": "아메리카노", "engName": "Americano", "price": 4500},
  {"id": 2, "korName": "라떼", "engName": "Latte", "price": 5000},
  {"id": 3, "korName": "카푸치노", "engName": "Cappuccino", "price": 5200}
]
```

**6-3. 새 데이터 추가**

- Method: `POST`
- URL: `http://localhost:8080/api/v1/admin/menus`
- Body: raw → JSON

```json
{
  "korName": "에스프레소",
  "engName": "Espresso",
  "price": 4000
}
```

예상 응답(200 OK):

```json
{"id": 4, "korName": "에스프레소", "engName": "Espresso", "price": 4000}
```

> 새 리소스를 만드는 요청은 원래 `201 Created`가 더 적절하지만, 지금 `createMenu`는 엔티티를 그대로 반환하므로 200이 나온다. `ResponseEntity.created(...)`로 바꾸는 방법은 앞선 REST API 실습에서 다뤘다.

**6-4. 단건 조회**

- Method: `GET`
- URL: `http://localhost:8080/api/v1/admin/menus/4`

예상 응답(200 OK):

```json
{"id": 4, "korName": "에스프레소", "engName": "Espresso", "price": 4000}
```

**6-5. 존재 확인**

- Method: `GET`
- URL: `http://localhost:8080/api/v1/admin/menus/4/exists`

예상 응답(200 OK): `true`

**6-6. 삭제**

- Method: `DELETE`
- URL: `http://localhost:8080/api/v1/admin/menus/4`

예상 응답: `204 No Content`

**6-7. 삭제 확인**

- Method: `GET`
- URL: `http://localhost:8080/api/v1/admin/menus/4`

예상 응답: `404 Not Found`

**6-8. 개수 확인**

- Method: `GET`
- URL: `http://localhost:8080/api/v1/admin/menus/count`

예상 응답(200 OK): `3`

> 예상 응답의 id(1~4)는 시드 데이터를 넣기 전에 테이블이 비어 있고 id 번호도 초기화된 상태를 가정한 것이다. id가 다르게 나온다면 1-1의 `TRUNCATE ... RESTART IDENTITY` 주석을 풀고 재시작한 뒤 다시 해본다.

**✅ 확인**

- Postman의 모든 요청이 200, 204, 404 중 예상한 상태 코드를 반환한다.
- `GET /api/v1/admin/menus`로 3개의 시드 데이터가 보인다.
- POST로 추가한 데이터가 `GET /{id}`로 조회된다.
- DELETE 후 `GET /{id}`는 404를 반환한다.
- `GET /count`는 3을 반환한다.

**🎓 코멘트**: Postman Collection은 API 테스트를 체계적으로 관리하는 좋은 방법이다. 각 요청의 URL, Method, Body, 예상 응답을 정리해두면 나중에 다른 개발자가 이 API를 쓸 때도 도움이 된다. `JpaRepository`의 기본 메서드 `save`, `findAll`, `findById`, `existsById`, `deleteById`, `count`만으로도 대부분의 간단한 CRUD가 가능하다. 더 복잡한 조회가 필요하면 메서드 이름 규칙(쿼리 메서드)이나 `@Query` 어노테이션을 쓰는데, `@Query`는 다음 실습에서 다룬다.

> **추가 설명 — 이번 실습에서 쓴 메서드 정리**
>
> | 메서드 | 반환 타입 | 실행되는 SQL(개념) | HTTP 매핑 |
> |---|---|---|---|
> | `save(entity)` | 저장된 엔티티 | id가 null이면 `INSERT`, 있으면 `SELECT` 후 `UPDATE` | `POST /` |
> | `findAll()` | `List<T>` | `SELECT * FROM menus` | `GET /` |
> | `findById(id)` | `Optional<T>` | `SELECT ... WHERE id = ?` | `GET /{id}` |
> | `existsById(id)` | `boolean` | `SELECT COUNT(id) ... WHERE id = ?` | `GET /{id}/exists` |
> | `deleteById(id)` | `void` | `SELECT ... WHERE id = ?` 후 `DELETE` | `DELETE /{id}` |
> | `count()` | `long` | `SELECT COUNT(*) FROM menus` | `GET /count` |

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `404 Not Found` | URL 경로 오류 | Postman의 URL이 `/api/v1/admin/menus`로 시작하는지 확인 |
| `405 Method Not Allowed` | HTTP 메서드 오류 | Postman의 Method가 GET/POST/DELETE 중 맞는 것인지 확인 |
| `415 Unsupported Media Type` | POST Body 형식 오류 | Body를 raw → **JSON**으로 선택했는지 확인(Text로 두면 발생) |
| `500 Internal Server Error` | 애플리케이션 에러 | 터미널 로그의 스택 트레이스 확인 |

**📝 핵심**: Postman Collection으로 API 테스트를 체계적으로 관리하고, `JpaRepository`의 기본 메서드로 CRUD를 완료한다.

## 마무리

1. `data.sql`로 시드 데이터 로드. `spring.sql.init.mode: always` + `spring.jpa.defer-datasource-initialization: true`
2. `findById` 엔드포인트 추가. `Optional` 개념 이해
3. `existsById` 엔드포인트 추가. `boolean` 반환
4. `deleteById` 엔드포인트 추가. `void` 반환
5. `count` 엔드포인트 추가. `long` 반환
6. Postman으로 전체 CRUD 흐름 실행
