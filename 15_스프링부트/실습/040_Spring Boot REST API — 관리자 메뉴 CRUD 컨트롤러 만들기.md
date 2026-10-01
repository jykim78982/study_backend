---
tags: [스프링부트, REST, 컨트롤러, DTO, Postman, 실습]
---

> 🔗 관련 노트: [[075_3계층 컨벤션 — 컨트롤러·서비스·리포지토리 명명과 CRUD 설계]] · [[068_스프링 프레임워크 개요와 3계층 아키텍처 — Controller·Service·Repository, Entity와 DTO]]

# Spring Boot REST API — 관리자 메뉴 CRUD 컨트롤러 만들기

**대상**: `@RestController`와 기본 어노테이션을 알고, Java 17+와 Spring Boot 3.x, Gradle, Postman을 설치해 둔 사람

**목표**: `MenuController`에 5개 엔드포인트(POST, GET 목록, GET 상세, PUT, DELETE)를 목업 데이터로 구현하고 Postman으로 테스트한다

**완성물**: `MenuController` 클래스와 관련 DTO 클래스들이 포함된 프로젝트. Postman으로 각 엔드포인트를 호출할 때 올바른 상태 코드와 JSON 응답이 반환되는 상태

## 1. HTTP 메서드와 REST API의 대응 관계

REST API를 만들 때 가장 먼저 알아야 할 것은 "어떤 동작에 어떤 HTTP 메서드를 쓰는가"입니다. 이 단계에서는 코드를 쓰지 않고, 개념만 정리해 볼게요.

**1-1. HTTP 메서드 4가지의 역할 확인**

| HTTP 메서드 | 의미 | REST API에서의 역할 |
|---|---|---|
| GET | 가져오기 | 리소스를 조회한다. 데이터를 변경하지 않는다. |
| POST | 만들기 | 새로운 리소스를 생성한다. |
| PUT | 전체 교체 | 기존 리소스를 전체적으로 수정한다. |
| DELETE | 삭제하기 | 리소스를 삭제한다. |

**1-2. 메뉴 CRUD와 메서드 매핑**

관리자 메뉴 관리 기능을 이 메서드에 매핑해 보세요.

- 메뉴 생성: `POST /api/v1/admin/menus`
- 메뉴 목록 조회: `GET /api/v1/admin/menus`
- 메뉴 상세 조회: `GET /api/v1/admin/menus/{id}`
- 메뉴 수정: `PUT /api/v1/admin/menus`
- 메뉴 삭제: `DELETE /api/v1/admin/menus/{id}`

✅ **확인**
- 위 표를 보고 "생성=POST, 조회=GET, 수정=PUT, 삭제=DELETE"가 자연스럽게 떠오릅니다.
- URL 구조에서 `/menus/{id}`가 특정 리소스를 가리킨다는 것을 이해합니다.

🎓 **newlec 쌤의 코멘트**

REST API는 "리소스"를 중심으로 설계합니다. `/menus`는 메뉴 목록이라는 리소스이고, `/menus/1`은 id가 1인 메뉴라는 특정 리소스입니다. HTTP 메서드는 이 리소스에 대한 "동작"을 나타냅니다. GET은 읽기만 하고, POST는 만들고, PUT은 덮어쓰고, DELETE는 지웁니다. 이 규칙을 지키면 프론트엔드 개발자나 다른 백엔드 개발자가 코드를 보지 않고도 API를 어떻게 써야 하는지 알 수 있습니다.

📝 **이 단계의 핵심**
- GET은 조회, POST는 생성, PUT은 수정, DELETE는 삭제.
- URL의 `{id}`는 특정 리소스를 가리키는 경로 변수입니다.

## 2. Postman 콜렉션 만들기

Postman은 API를 테스트하는 도구입니다. 이 단계에서는 메뉴 관리 API를 위한 콜렉션을 만들어 볼게요.

**2-1. Postman 실행 및 콜렉션 생성**

Postman을 실행하고, 왼쪽 패널의 Collections 탭에서 **+ Create collection** 버튼을 클릭합니다.

- Name: `Admin Menu API`
- Description: (비워둬도 됩니다)

**2-2. 콜렉션에 요청 폴더 만들기**

만든 `Admin Menu API` 콜렉션에 마우스를 올리면 **+ Add folder** 버튼이 보입니다. 클릭하고 폴더 이름을 `Menu CRUD`로 입력합니다.

✅ **확인**
- Postman 왼쪽 패널에 `Admin Menu API` 콜렉션이 보입니다.
- 그 안에 `Menu CRUD` 폴더가 있습니다.

🎓 **newlec 쌤의 코멘트**

Postman에서 콜렉션은 "API 그룹"을 묶어두는 폴더 같은 것입니다. 프로젝트마다, 기능별로 콜렉션을 나누면 나중에 API가 많아져도 혼란이 없습니다. 요청을 폴더에 넣어두면 요청 순서나 그룹 단위로 실행할 수도 있습니다. 이 따라하기에서는 `Menu CRUD` 폴더 안에 5개 요청을 하나씩 추가할 것입니다.

📝 **이 단계의 핵심**
- Postman에서 콜렉션은 API를 그룹화하는 단위입니다.
- 폴더를 만들어 요청을 정리하면 관리가 쉬워집니다.

## 3. 컨트롤러 클래스 세팅

이제 실제 코드를 시작합니다. `MenuController` 클래스를 만들고, 클래스 레벨의 어노테이션을 설정해 볼게요.

**3-1. 컨트롤러 패키지 만들기**

Gradle 프로젝트의 `src/main/java` 폴더에서 `com.newlecture.ncafe.backend.controller.admin` 패키지가 있는지 확인합니다.

패키지가 없다면 VSCode 또는 IntelliJ IDEA에서 `src/main/java` 폴더를 우클릭 → New → Package → `com.newlecture.ncafe.backend.controller.admin` 입력해서 생성

**3-2. MenuController.java 파일 만들기**

파일: `src/main/java/com/newlecture/ncafe/backend/controller/admin/MenuController.java`

```java
package com.newlecture.ncafe.backend.controller.admin;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController("adminMenuController")
@RequestMapping("/api/v1/admin/menus")
public class MenuController {
}
```

**3-3. 프로젝트 실행**

터미널에서 다음 명령을 실행합니다.

```bash
./gradlew bootRun
```

> Windows에서는 `gradlew.bat bootRun`

✅ **확인**
- 터미널에 `Started BackendApplication in X.XXX seconds` 같은 메시지가 출력됩니다.
- 에러가 없으면 성공입니다.

🎓 **newlec 쌤의 코멘트**

`@RestController`는 `@Controller`와 `@ResponseBody`를 합친 것입니다. `@Controller`는 뷰를 반환하는 컨트롤러이고, `@ResponseBody`는 메서드 반환 값을 JSON으로 직렬화해서 응답 바디에 넣는 어노테이션입니다. REST API는 항상 JSON을 주고받으므로 `@RestController`를 사용합니다. `@RequestMapping("/api/v1/admin/menus")`는 이 클래스의 모든 메서드에 공통으로 붙는 URL prefix입니다. 각 메서드에서 `@PostMapping`만 쓰면 `/api/v1/admin/menus`가 자동으로 붙습니다.

❌ **자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Port 8080 was already in use` | 다른 앱이 8080 포트를 사용 중 | 다른 포트로 실행: `./gradlew bootRun --args='--server.port=8081'` |
| `Could not find package com.example.demo.controller` | 패키지 경로가 잘못됨 | `src/main/java` 아래에 해당 패키지 폴더가 있는지 확인 |

📝 **이 단계의 핵심**
- `@RestController`는 JSON 응답을 위한 컨트롤러입니다.
- `@RequestMapping`은 클래스 레벨에서 공통 URL prefix를 설정합니다.

## 4. POST — 메뉴 생성

이제 첫 번째 엔드포인트, 메뉴 생성을 구현해 볼게요. 이 단계에서 요청 DTO와 응답 DTO를 정의합니다.

**4-1. MenuCreateRequestDto 정의**

파일: `src/main/java/com/newlecture/ncafe/backend/dto/admin/menu/MenuCreateRequestDto.java`

```java
package com.newlecture.ncafe.backend.dto.admin.menu;

public record MenuCreateRequestDto(
    String name,
    String description,
    String category
) {}
```

> DTO 이름 설명: `MenuCreateRequestDto`는 "메뉴를 생성할 때 사용자가 보내는 요청 데이터"를 의미합니다. `Create`는 동작(생성), `Request`는 방향(클라이언트 → 서버), `Dto`는 데이터 전송 객체라는 뜻입니다. `id`, `createdAt`, `updatedAt` 같은 서버가 관리하는 필드는 요청에 포함하지 않습니다.

**4-2. MenuCreatedResponseDto 정의**

파일: `src/main/java/com/newlecture/ncafe/backend/dto/admin/menu/MenuCreatedResponseDto.java`

```java
package com.newlecture.ncafe.backend.dto.admin.menu;

public record MenuCreatedResponseDto(
    Long id,
    String name,
    String description,
    String category
) {}
```

> DTO 이름 설명: `MenuCreatedResponseDto`는 "메뉴 생성 후 서버가 클라이언트에게 반환하는 응답 데이터"입니다. `Created`는 과거형으로 "생성된" 상태를 나타내고, `Response`는 방향(서버 → 클라이언트)입니다. 생성 후 서버가 할당하는 `id`가 포함됩니다.

**4-3. MenuController에 POST 메서드 추가**

파일: `src/main/java/com/newlecture/ncafe/backend/controller/admin/MenuController.java`

```java
package com.newlecture.ncafe.backend.controller.admin;

import com.newlecture.ncafe.backend.dto.admin.menu.MenuCreateRequestDto;
import com.newlecture.ncafe.backend.dto.admin.menu.MenuCreatedResponseDto;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController("adminMenuController")
@RequestMapping("/api/v1/admin/menus")
public class MenuController {

    @PostMapping
    public ResponseEntity<MenuCreatedResponseDto> createMenu(@RequestBody MenuCreateRequestDto request) {
        // 목업: id를 1로 고정
        MenuCreatedResponseDto response = new MenuCreatedResponseDto(
            1L,
            request.name(),
            request.description(),
            request.category()
        );
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}
```

**4-4. Postman에서 POST 요청 테스트**

Postman에서 `Admin Menu API > Menu CRUD` 폴더에 요청을 추가합니다.

- Method: `POST`
- URL: `http://localhost:8080/api/v1/admin/menus`
- Body 탭 → raw → JSON 선택
- Body 내용:

```json
{
  "name": "김치찌개",
  "description": "매콤한 김치찌개",
  "category": "국물"
}
```

Send 버튼을 클릭합니다.

✅ **확인**
- Postman 응답 영역에 상태 코드 `201 Created`가 보입니다.
- 응답 JSON에 `"id": 1`이 포함됩니다.
- 응답 JSON에 요청한 `name`, `description`, `category`가 그대로 반환됩니다.

🎓 **newlec 쌤의 코멘트**

`@RequestBody`는 요청 바디의 JSON을 Java 객체로 변환해 줍니다. `MenuCreateRequestDto`가 record이므로 Jackson이 자동으로 JSON 필드를 매핑합니다. `ResponseEntity.status(HttpStatus.CREATED)`는 상태 코드를 201로 설정합니다. 201은 "새 리소스가 생성되었습니다"라는 의미입니다. id를 1로 고정해 둔 것은 목업이므로 실제 DB가 없기 때문입니다. 나중에 DB를 연결하면 id는 시퀀스로 자동 생성될 것입니다.

❌ **자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `400 Bad Request` | JSON 형식이 잘못되거나 필드명이 다름 | Postman Body에서 JSON이 유효한지, 필드명이 `name`, `description`, `category`인지 확인 |
| `404 Not Found` | URL이 잘못됨 | URL이 `http://localhost:8080/api/v1/admin/menus`인지 확인. `/menus` 뒤에 슬래시 없어야 함 |

📝 **이 단계의 핵심**
- 요청 DTO는 사용자가 보내는 필드만 포함하고, `id` 같은 서버 관리 필드는 제외합니다.
- 생성 응답에는 서버가 할당하는 `id`를 포함합니다.
- 생성 성공 시 상태 코드는 `201 Created`입니다.

## 5. GET — 메뉴 목록 조회

이제 메뉴 목록을 조회하는 엔드포인트를 구현해 볼게요.

**5-1. MenuListRequestDto 정의**

파일: `src/main/java/com/newlecture/ncafe/backend/dto/admin/menu/MenuListRequestDto.java`

```java
package com.newlecture.ncafe.backend.dto.admin.menu;

public record MenuListRequestDto(
    Integer page,
    String category
) {}
```

> DTO 이름 설명: `MenuListRequestDto`는 "메뉴 목록을 조회할 때 사용자가 보내는 요청 데이터"입니다. `List`는 "목록"을 의미하고, `page`와 `category`는 필터 조건입니다. `page`는 페이지 번호, `category`는 카테고리 필터입니다.

**5-2. MenuListResponseDto 정의**

파일: `src/main/java/com/newlecture/ncafe/backend/dto/admin/menu/MenuListResponseDto.java`

```java
package com.newlecture.ncafe.backend.dto.admin.menu;

public record MenuListResponseDto(
    Long id,
    String name,
    String category
) {}
```

> DTO 이름 설명: `MenuListResponseDto`는 "메뉴 목록에 들어갈 요약 정보"입니다. 목록에서는 상세 정보가 필요 없으므로 `name`과 `category`만 포함합니다. `description` 같은 긴 텍스트는 목록에 포함하지 않는 것이 일반적입니다.

**5-3. MenuController에 GET 목록 메서드 추가**

```java
@GetMapping
public ResponseEntity<List<MenuListResponseDto>> getMenus(@RequestBody MenuListRequestDto request) {
    // 목업: 2개의 메뉴 반환
    List<MenuListResponseDto> menus = List.of(
        new MenuListResponseDto(1L, "김치찌개", "국물"),
        new MenuListResponseDto(2L, "비빔밥", "밥")
    );
    return ResponseEntity.ok(menus);
}
```

**5-4. Postman에서 GET 요청 테스트**

- Method: `GET`
- URL: `http://localhost:8080/api/v1/admin/menus`
- Body 탭 → raw → JSON 선택
- Body 내용:

```json
{
  "page": 1,
  "category": null
}
```

Send 버튼을 클릭합니다.

✅ **확인**
- Postman 응답 영역에 상태 코드 `200 OK`가 보입니다.
- 응답 JSON이 배열(`[ ... ]`) 형태입니다.
- 배열에 2개 항목이 있고, 각 항목에 `id`, `name`, `category`가 있습니다.

🎓 **newlec 쌤의 코멘트**

GET 요청에 `@RequestBody`를 사용하는 것은 비표준적입니다. 일반적으로 GET은 쿼리 파라미터(`?page=1&category=국물`)를 사용합니다. 하지만 이 따라하기에서는 프론트엔드에서 JavaScript로 JSON 바디를 보내는 방식을 시뮬레이션하기 위해 `@RequestBody`를 사용합니다. 실무에서는 GET에 `@RequestParam`을 사용하는 것이 더 일반적입니다. `ResponseEntity.ok()`는 상태 코드 200을 반환합니다.

❌ **자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `405 Method Not Allowed` | Postman에서 Method를 POST로 잘못 선택 | Method를 GET으로 변경 |
| `400 Bad Request` | Body가 비어 있거나 JSON이 아님 | Body에 유효한 JSON을 입력 |

📝 **이 단계의 핵심**
- 목록 응답에는 요약 정보만 포함합니다.
- GET에 `@RequestBody`를 사용할 수 있지만, 실무에서는 `@RequestParam`이 더 일반적입니다.

## 6. GET — 메뉴 상세 조회

이제 특정 메뉴의 상세 정보를 조회하는 엔드포인트를 구현해 볼게요.

**6-1. MenuDetailResponseDto 정의**

파일: `src/main/java/com/newlecture/ncafe/backend/dto/admin/menu/MenuDetailResponseDto.java`

```java
package com.newlecture.ncafe.backend.dto.admin.menu;

public record MenuDetailResponseDto(
    Long id,
    String name,
    String description,
    String category,
    String createdAt,
    String updatedAt
) {}
```

> DTO 이름 설명: `MenuDetailResponseDto`는 "특정 메뉴의 전체 필드를 포함하는 상세 정보"입니다. `Detail`은 "상세"를 의미하고, 목록과 달리 `description`, `createdAt`, `updatedAt` 같은 모든 필드를 포함합니다.

**6-2. MenuController에 GET 상세 메서드 추가**

```java
@GetMapping("/{id}")
public ResponseEntity<MenuDetailResponseDto> getMenu(@PathVariable Long id) {
    // 목업: id가 1이면 김치찌개, 그 외는 404
    if (id == 1L) {
        MenuDetailResponseDto menu = new MenuDetailResponseDto(
            1L,
            "김치찌개",
            "매콤한 김치찌개",
            "국물",
            "2024-01-01T00:00:00",
            "2024-01-01T00:00:00"
        );
        return ResponseEntity.ok(menu);
    }
    return ResponseEntity.notFound().build();
}
```

**6-3. Postman에서 GET 상세 요청 테스트**

- Method: `GET`
- URL: `http://localhost:8080/api/v1/admin/menus/1`
- Body: (비워둠)

Send 버튼을 클릭합니다.

✅ **확인**
- Postman 응답 영역에 상태 코드 `200 OK`가 보입니다.
- 응답 JSON에 `id`, `name`, `description`, `category`, `createdAt`, `updatedAt`이 모두 있습니다.
- `id`가 1인 경우에만 200이 반환되고, 다른 id(예: 999)는 404가 반환됩니다.

🎓 **newlec 쌤의 코멘트**

`@PathVariable`는 URL의 `{id}` 부분을 Java 변수로 바인딩합니다. `@GetMapping("/{id}")`에서 `/{id}`의 중괄호는 URL 템플릿 변수입니다. `@PathVariable Long id`는 URL의 `/1`을 `Long` 타입의 `id` 변수로 변환해 줍니다. `ResponseEntity.notFound().build()`는 404 상태 코드를 반환합니다. 목업에서는 id가 1일 때만 데이터를 반환하고, 그 외에는 404를 반환합니다.

❌ **자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `404 Not Found` (id=1일 때) | URL에 `/1`이 누락됨 | URL이 `http://localhost:8080/api/v1/admin/menus/1`인지 확인 |
| `400 Bad Request` | URL에 숫자가 아닌 값이 들어감 | URL의 `{id}` 부분에 숫자만 입력 |

📝 **이 단계의 핵심**
- `@PathVariable`는 URL의 경로 변수를 Java 변수로 바인딩합니다.
- 상세 조회에는 모든 필드를 포함합니다.
- 존재하지 않는 리소스는 404를 반환합니다.

## 7. PUT — 메뉴 수정

이제 메뉴를 수정하는 엔드포인트를 구현해 볼게요.

**7-1. MenuUpdateRequestDto 정의**

파일: `src/main/java/com/newlecture/ncafe/backend/dto/admin/menu/MenuUpdateRequestDto.java`

```java
package com.newlecture.ncafe.backend.dto.admin.menu;

public record MenuUpdateRequestDto(
    String name,
    String description,
    String category
) {}
```

> DTO 이름 설명: `MenuUpdateRequestDto`는 "메뉴를 수정할 때 사용자가 보내는 요청 데이터"입니다. `Update`는 "수정"을 의미합니다. `id`는 URL에 포함되므로 요청 바디에 포함하지 않습니다.

**7-2. MenuUpdatedResponseDto 정의**

파일: `src/main/java/com/newlecture/ncafe/backend/dto/admin/menu/MenuUpdatedResponseDto.java`

```java
package com.newlecture.ncafe.backend.dto.admin.menu;

public record MenuUpdatedResponseDto(
    Long id,
    String name,
    String description,
    String category,
    String updatedAt
) {}
```

> DTO 이름 설명: `MenuUpdatedResponseDto`는 "메뉴 수정 후 서버가 반환하는 응답 데이터"입니다. `Updated`는 "수정된" 상태를 나타내고, `updatedAt`이 포함됩니다.

**7-3. MenuController에 PUT 메서드 추가**

```java
@PutMapping
public ResponseEntity<MenuUpdatedResponseDto> updateMenu(@RequestBody MenuUpdateRequestDto request) {
    // 목업: id를 1로 고정
    MenuUpdatedResponseDto response = new MenuUpdatedResponseDto(
        1L,
        request.name(),
        request.description(),
        request.category(),
        "2024-01-02T00:00:00"
    );
    return ResponseEntity.ok(response);
}
```

**7-4. Postman에서 PUT 요청 테스트**

- Method: `PUT`
- URL: `http://localhost:8080/api/v1/admin/menus`
- Body 탭 → raw → JSON 선택
- Body 내용:

```json
{
  "name": "김치찌개(수정)",
  "description": "매운 김치찌개",
  "category": "국물"
}
```

Send 버튼을 클릭합니다.

✅ **확인**
- Postman 응답 영역에 상태 코드 `200 OK`가 보입니다.
- 응답 JSON에 `id`, `name`, `description`, `category`, `updatedAt`이 있습니다.
- `name`이 "김치찌개(수정)"으로 변경되어 있습니다.

🎓 **newlec 쌤의 코멘트**

PUT은 리소스를 전체적으로 교체하는 의미입니다. id는 URL에 포함되지 않고, 요청 바디에 포함되지 않습니다. 왜냐하면 `PUT /api/v1/admin/menus`는 "메뉴 목록 리소스를 교체"하는 것이 아니라, "특정 메뉴를 수정"하는 것이기 때문입니다. 실제로는 `PUT /api/v1/admin/menus/{id}`가 더 정확하지만, 이 따라하기에서는 id를 목업으로 1로 고정해 두었습니다. `ResponseEntity.ok()`는 200을 반환합니다.

❌ **자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `405 Method Not Allowed` | Postman에서 Method를 POST로 잘못 선택 | Method를 PUT으로 변경 |
| `400 Bad Request` | JSON 형식이 잘못됨 | Body에서 JSON이 유효한지 확인 |

📝 **이 단계의 핵심**
- PUT은 전체 교체, id는 URL에 포함하지 않습니다.
- 수정 응답에는 `updatedAt`이 포함됩니다.

## 8. DELETE — 메뉴 삭제

이제 메뉴를 삭제하는 엔드포인트를 구현해 볼게요.

**8-1. MenuController에 DELETE 메서드 추가**

```java
@DeleteMapping("/{id}")
public ResponseEntity<Void> deleteMenu(@PathVariable Long id) {
    // 목업: 항상 204 반환
    return ResponseEntity.noContent().build();
}
```

**8-2. Postman에서 DELETE 요청 테스트**

- Method: `DELETE`
- URL: `http://localhost:8080/api/v1/admin/menus/1`
- Body: (비워둠)

Send 버튼을 클릭합니다.

✅ **확인**
- Postman 응답 영역에 상태 코드 `204 No Content`가 보입니다.
- 응답 바디가 비어 있습니다.

🎓 **newlec 쌤의 코멘트**

DELETE는 리소스를 삭제하는 요청입니다. 성공 시 204 No Content를 반환합니다. 204는 "요청이 성공했지만 응답 바디가 없다"는 의미입니다. `ResponseEntity.noContent().build()`는 204를 반환합니다. `@PathVariable Long id`는 URL의 `{id}`를 바인딩합니다.

❌ **자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `405 Method Not Allowed` | Postman에서 Method를 GET으로 잘못 선택 | Method를 DELETE로 변경 |
| `404 Not Found` | URL에 `/1`이 누락됨 | URL이 `http://localhost:8080/api/v1/admin/menus/1`인지 확인 |

📝 **이 단계의 핵심**
- DELETE 성공 시 204 No Content를 반환합니다.
- `@PathVariable`는 URL의 경로 변수를 바인딩합니다.

## 9. 전체 테스트

이제 Postman에서 5개 엔드포인트를 모두 호출해서 응답을 확인해 볼게요.

**9-1. POST 요청 재실행**

Postman에서 `Admin Menu API > Menu CRUD` 폴더의 POST 요청을 선택하고 Send를 클릭합니다.

> 기대 응답: `201 Created`, `id: 1`

**9-2. GET 목록 요청 재실행**

GET 목록 요청을 선택하고 Send를 클릭합니다.

> 기대 응답: `200 OK`, 배열에 2개 항목

**9-3. GET 상세 요청 재실행**

GET 상세 요청(URL: `/api/v1/admin/menus/1`)을 선택하고 Send를 클릭합니다.

> 기대 응답: `200 OK`, `id: 1`, 모든 필드 포함

**9-4. PUT 요청 재실행**

PUT 요청을 선택하고 Send를 클릭합니다.

> 기대 응답: `200 OK`, `id: 1`, `updatedAt` 포함

**9-5. DELETE 요청 재실행**

DELETE 요청(URL: `/api/v1/admin/menus/1`)을 선택하고 Send를 클릭합니다.

> 기대 응답: `204 No Content`, 바디 없음

✅ **확인**
- 5개 요청 모두 예상한 상태 코드와 응답을 반환합니다.
- Postman 응답 영역에서 각 요청의 상태 코드와 JSON을 확인합니다.

🎓 **newlec 쌤의 코멘트**

이제 5개 엔드포인트가 모두 동작합니다. Postman에서 각 요청을 실행할 때 상태 코드와 응답 JSON을 확인하는 것이 중요합니다. 201은 생성, 200은 조회/수정, 204는 삭제입니다. 이 목업은 실제 DB가 없으므로 항상 같은 데이터를 반환합니다. 나중에 DB를 연결하면 각 요청이 실제 데이터를 조작할 것입니다.

📝 **이 단계의 핵심**
- 5개 엔드포인트 모두 Postman으로 테스트할 수 있습니다.
- 상태 코드: 201(생성), 200(조회/수정), 204(삭제).

## 정리

1. 1단계: HTTP 메서드와 REST API의 대응 관계를 이해합니다.
2. 2단계: Postman에서 콜렉션과 폴더를 만듭니다.
3. 3단계: `@RestController`와 `@RequestMapping`으로 컨트롤러 클래스를 세팅합니다.
4. 4단계: POST로 메뉴를 생성하고, 요청/응답 DTO를 정의합니다.
5. 5단계: GET으로 메뉴 목록을 조회하고, 목록 DTO를 정의합니다.
6. 6단계: GET으로 메뉴 상세를 조회하고, `@PathVariable`를 사용합니다.
7. 7단계: PUT으로 메뉴를 수정하고, 수정 DTO를 정의합니다.
8. 8단계: DELETE로 메뉴를 삭제하고, 204 No Content를 반환합니다.
9. 9단계: Postman으로 5개 엔드포인트를 모두 테스트합니다.
