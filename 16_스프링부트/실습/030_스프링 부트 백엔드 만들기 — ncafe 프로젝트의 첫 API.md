---
tags: [웹, 스프링부트, Java, 실습]
---

> 🔗 관련 노트: [[033_어노테이션 기반 매핑과 RTTI(리플렉션)]] · [[031_스프링 부트 백엔드 만들기 — PostgreSQL 연결과 JDBC Repository]]

# 스프링 부트 백엔드 만들기 — ncafe 프로젝트의 첫 API

**대상**: 서블릿의 `doGet`/`doPost` 구조를 알고 있고, Next.js 프론트엔드(`ncafe/frontend`)를 이미 만든 학생

**목표**: `ncafe/backend` 폴더에 스프링 부트 프로젝트를 생성하고, `/api/menus` API를 만들어 Postman으로 확인한다

**완성물**: `ncafe/backend` 폴더의 스프링 부트 앱과, Postman에서 `GET /api/menus` 요청 시 JSON 배열이 반환되는 상태

**필수 준비물**

- Java 17 이상(JDK 설치 확인: `java -version`)
- Maven 3.8 이상(또는 IntelliJ IDEA 내장 Maven)
- Postman(무료 버전)
- VSCode 또는 IntelliJ IDEA

**전제**: `ncafe/frontend` 폴더는 이미 존재한다고 가정한다. 이 폴더 옆에 나란히 `ncafe/backend` 폴더를 만든다.

## 1. Spring Initializr로 프로젝트 생성하기

Spring JDBC가 아니라 Spring Initializr로, 스프링 프로젝트 자체를 생성해주는 도구부터 준비한다.

### 1-1. VSCode에서 Spring Initializr 실행

VSCode 확장 모듈 창을 열고 "spring"이라고 검색하면 Spring Boot Dashboard, Spring Initializr Java Support, Spring Boot Tools, Spring Boot Extension Pack을 볼 수 있다. 이 도구들은 서로 종속 관계가 있어서 일반적으로 Spring Boot Extension Pack만 설치해도 모두 설치되지만, Spring Initializr가 같이 설치되지 않는다면 직접 설치한다.

VSCode 상단 메뉴에서 File > New File... 또는 Command Palette(`Ctrl+Shift+P`/`Cmd+Shift+P`)를 열고 `Spring: Create a new Spring Initializr Project`를 선택한다.

### 1-2. 프로젝트 설정 입력

화면에 표시되는 항목에 아래 값을 입력한다. 프로젝트를 식별하는 도메인으로는 `com.newlecture`를 입력한다.

| 항목 | 입력값 |
|---|---|
| Project Name | backend |
| Project Location | ncafe 폴더(현재 열려 있는 루트) |
| Language | Java |
| Build Tool | Maven |
| Java Version | 21 |
| Dependencies | Spring Web(필수), Lombok(선택, 추천) |

Windows/Mac 공통: Location을 `ncafe` 폴더로 지정해야 `ncafe/backend`가 만들어진다. `ncafe` 폴더가 아닌 다른 곳에 만들면 폴더 구조가 깨진다.

### 1-3. 생성 완료 확인

VSCode 사이드바에서 `ncafe` 폴더를 보면 `frontend` 옆에 `backend` 폴더가 생겼는지 확인한다.

**✅ 확인**

- VSCode 사이드바에서 `ncafe/backend` 폴더가 보인다.
- `backend` 폴더 안에 `src`, `pom.xml`, `.mvn`이 보인다.

**🎓 newlec 쌤의 코멘트**

Spring Initializr는 스프링 부트 공식에서 제공하는 프로젝트 생성기다. `pom.xml`에 필요한 의존성을 자동으로 넣고, 기본 폴더 구조를 만들어준다. 서블릿 프로젝트에서 `web.xml`을 직접 작성하고 Servlet 클래스를 등록하던 과정을 스프링 부트가 자동으로 처리해준다. 이 "자동 설정"이 스프링 부트의 핵심이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `backend`가 `ncafe` 밖에 생성됨 | Location을 `ncafe` 폴더가 아닌 상위 폴더로 선택 | `backend` 폴더를 `ncafe` 안으로 이동 |
| Spring Web이 선택되지 않음 | Dependencies에서 체크를 누르기 전에 다음으로 넘어감 | 다시 Initializr 실행하거나 `pom.xml`에 `spring-boot-starter-web` 추가 |

**📝 이 단계의 핵심**

- Spring Initializr는 `pom.xml`과 기본 폴더 구조를 자동으로 만들어준다.
- 프로젝트는 항상 `ncafe/backend`에 있어야 프론트엔드(`ncafe/frontend`)와 같은 루트에서 관리된다.

## 2. 생성된 폴더 구조 훑어보기

스프링 부트 프로젝트의 폴더 구조를 하나씩 열어보며, 각 폴더가 서블릿 프로젝트의 어떤 역할을 대체하는지 확인한다.

### 2-1. `src/main/java` 폴더 열기

VSCode에서 `ncafe/backend/src/main/java` 폴더를 확장한다. 그 안에 `com.newlecture.backend`(설정한 패키지명) 폴더가 있고, 그 안에 `BackendApplication.java`가 있다.

### 2-2. `BackendApplication.java` 코드 확인

파일: `src/main/java/com/newlecture/backend/BackendApplication.java`

```java
package com.newlecture.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class BackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(BackendApplication.class, args);
    }
}
```

주석 설명:

- `@SpringBootApplication`: 이 클래스가 스프링 부트 애플리케이션의 진입점임을 알린다. 자동 설정, 컴포넌트 스캔, 자동 구성을 활성화한다.
- `SpringApplication.run(...)`: 서블릿 컨테이너(Tomcat)를 시작하고, Spring 컨텍스트를 로드한다. 서블릿 프로젝트에서 `web.xml`을 읽어 Servlet을 등록하던 과정을 이 한 줄이 대신한다.

### 2-3. `src/main/resources` 폴더 확인

`src/main/resources` 폴더를 확장한다.

| 파일/폴더 | 역할 |
|---|---|
| `application.properties` | 서버 포트, 데이터베이스 연결 등 설정 값. 서블릿의 `web.xml`에 해당하는 설정 파일이다. |
| `static/` | 정적 파일(CSS, JS, 이미지)을 서빙하는 폴더. 서블릿에서 `sendFile()`로 직접 내보내던 파일을 여기서 자동으로 서빙한다. |
| `templates/` | 서버 사이드 렌더링 템플릿(Thymeleaf 등)을 두는 폴더. |

중요: Next.js 프론트엔드와 통신할 때는 `static/` 폴더를 거의 사용하지 않는다. 프론트엔드가 빌드된 정적 파일을 서빙하는 용도로만 사용하거나, 아예 프론트엔드 서버가 그 역할을 하면 된다.

### 2-4. `src/test/java` 폴더 확인

`src/test/java` 폴더를 확장한다. `BackendApplicationTests.java`가 있다.

```java
package com.newlecture.backend;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class BackendApplicationTests {

    @Test
    void contextLoads() {
    }
}
```

주석 설명: `@SpringBootTest`는 스프링 컨텍스트를 로드하여 테스트한다. `contextLoads()`는 "컨텍스트가 정상적으로 시작되는지"만 확인하는 기본 테스트다.

**✅ 확인**

- `BackendApplication.java`에 `@SpringBootApplication`과 `main` 함수가 있다.
- `src/main/resources/application.properties` 파일이 있다.
- `src/test/java`에 `BackendApplicationTests.java`가 있다.

**🎓 newlec 쌤의 코멘트**

서블릿 프로젝트에서는 `web.xml`에서 Servlet을 등록하고, `doGet`/`doPost`에서 직접 `HttpServletRequest`/`HttpServletResponse`를 처리했다. 스프링 부트에서는 `@SpringBootApplication`이 자동으로 내장 Tomcat을 시작하고, `@RestController`로 만든 클래스를 자동으로 감지하여 URL 매핑을 등록한다. `main` 함수는 "서버를 시작한다"는 한 줄의 의미다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `main` 함수를 실행해도 서버가 안 뜸 | `@SpringBootApplication` 애노테이션 누락 | 클래스 위에 `@SpringBootApplication` 추가 |
| `application.properties`가 안 보임 | `src/main/resources` 폴더가 비어 있음 | 폴더를 새로 만들거나, Initializr 설정에서 `application.properties` 생성 확인 |

**📝 이 단계의 핵심**

- `main` 함수는 내장 Tomcat을 시작하고 Spring 컨텍스트를 로드한다.
- `src/main/resources`는 설정과 정적 파일을, `src/test/java`는 테스트를 담당한다.

## 3. `/api/menus` API 만들기

이제 `/api/menus` API를 만든다. 먼저 데이터 구조를 정의하는 `Menu` 엔티티를 만들고, 그 데이터를 반환하는 컨트롤러를 만든다.

### 3-1. `Menu.java` 엔티티 만들기

파일: `src/main/java/com/newlecture/backend/entity/Menu.java`

```java
package com.newlecture.backend.entity;

import lombok.Data;
import java.time.LocalDate;

@Data
public class Menu {
    private Integer id;
    private String korName;
    private String engName;
    private Integer price;
    private String description;
    private String imgSrc;
    private Integer categoryId;
    private LocalDate createTime;
}
```

주석 설명:

- `@Data`(Lombok): getter/setter/toString/equals/hashCode를 자동으로 생성한다. Lombok이 없다면 수동으로 작성해야 한다.
- 필드명은 Java 컨벤션(카멜케이스)으로 작성한다. JSON 응답에서는 `kor_name` 같은 스네이크케이스가 필요하면 `@JsonProperty` 또는 Jackson 설정으로 변환할 수 있다.

### 3-2. `MenuController.java` 만들기

파일: `src/main/java/com/newlecture/backend/controller/MenuController.java`

```java
package com.newlecture.backend.controller;

import com.newlecture.backend.entity.Menu;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/api")
public class MenuController {

    @GetMapping("/menus")
    public List<Menu> getMenus() {
        List<Menu> menus = new ArrayList<>();

        Menu menu1 = new Menu();
        menu1.setId(1);
        menu1.setKorName("아메리카노");
        menu1.setEngName("Americano");
        menu1.setPrice(4500);
        menu1.setDescription("진한 에스프레소와 물의 조화");
        menu1.setImgSrc("/images/americano.png");
        menu1.setCategoryId(1);
        menu1.setCreateTime(LocalDate.now());

        Menu menu2 = new Menu();
        menu2.setId(2);
        menu2.setKorName("카페라떼");
        menu2.setEngName("Cafe Latte");
        menu2.setPrice(5000);
        menu2.setDescription("에스프레소와 스티밍 밀크");
        menu2.setImgSrc("/images/latte.png");
        menu2.setCategoryId(1);
        menu2.setCreateTime(LocalDate.now());

        menus.add(menu1);
        menus.add(menu2);

        return menus;
    }
}
```

주석 설명:

- `@RestController`: `@Controller` + `@ResponseBody`의 합성어. 반환 값을 자동으로 JSON으로 변환한다.
- `@RequestMapping("/api")`: 이 컨트롤러의 모든 메서드에 `/api`를 기본 경로로 붙인다.
- `@GetMapping("/menus")`: `GET /api/menus` 요청을 이 메서드가 처리한다.
- 목업 데이터: 실제 데이터베이스가 없으므로 `ArrayList`에 직접 값을 넣어 반환한다.

### 3-3. 서버 실행

터미널에서 `ncafe/backend` 폴더로 이동하고 실행한다.

```
cd ncafe/backend
mvn spring-boot:run
```

Windows/Mac 공통: Maven이 설치되어 있지 않으면 IntelliJ IDEA에서 `BackendApplication.java`의 `main` 함수를 실행해도 된다.

**✅ 확인**

- 터미널에 `Tomcat started on port(s): 8080`이 출력된다.
- `http://localhost:8080/api/menus`를 브라우저에서 직접 열면 JSON 배열이 보인다.

**🎓 newlec 쌤의 코멘트**

서블릿에서 `doGet`이 `request.getParameter()`로 값을 읽고 `response.getWriter()`로 JSON을 직접 작성했다면, 스프링에서는 `@GetMapping`이 요청을 메서드에 바인딩하고, 반환 값을 Jackson이 자동으로 JSON으로 변환한다. `Menu` 엔티티는 데이터베이스 테이블과 1:1로 대응하지만, 지금은 목업 데이터이므로 데이터베이스 없이도 동작한다. 나중에 JPA를 추가하면 이 `Menu` 클래스가 엔티티로 그대로 사용된다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| 404 Not Found | `@RequestMapping("/api")` 또는 `@GetMapping("/menus")` 경로 오타 | 경로가 `/api/menus`인지 확인 |
| Lombok 에러: `cannot find symbol: method setId` | Lombok 플러그인 미설치 또는 `@Data` 누락 | IntelliJ에서 Lombok 플러그인 활성화, 또는 `@Data` 제거 후 수동 getter/setter 작성 |
| `mvn: command not found` | Maven 미설치 또는 PATH 미설정 | Maven 설치 후 PATH 설정, 또는 IDE에서 실행 |

**📝 이 단계의 핵심**

- `@RestController` + `@GetMapping`으로 URL과 Java 메서드를 연결한다.
- 엔티티 클래스는 데이터 구조를 정의하고, 컨트롤러는 요청을 받아 응답을 반환한다.

## 4. Postman으로 확인하기

이제 Postman에서 `GET /api/menus` 요청을 보내고, JSON 응답이 정상적으로 오는지 확인한다.

### 4-1. Postman에서 새 요청 만들기

Postman을 열고, New Tab > GET을 선택한다.

노트: 지금은 단순 GET 요청이라서 Postman이 없거나 설치가 안 되어 있다면 그냥 브라우저를 열고 주소창에 다음 내용을 입력해도 된다.

### 4-2. URL 입력

URL 입력창에 다음을 입력한다.

```
http://localhost:8080/api/menus
```

### 4-3. 요청 보내기

Send 버튼을 누른다.

### 4-4. 응답 확인

Postman 하단의 Body 탭에서 JSON 배열이 보인다.

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
  {
    "id": 2,
    "korName": "카페라떼",
    "engName": "Cafe Latte",
    "price": 5000,
    "description": "에스프레소와 스티밍 밀크",
    "imgSrc": "/images/latte.png",
    "categoryId": 1,
    "createTime": "2026-09-15"
  }
]
```

**✅ 확인**

- Postman에서 200 OK 상태 코드가 보인다.
- Body에 두 개의 메뉴 객체가 포함된 JSON 배열이 보인다.
- `price`가 숫자, `createTime`이 `"2026-09-15"` 형식의 문자열로 보인다.

**🎓 newlec 쌤의 코멘트**

Postman은 API를 테스트하는 가장 기본적인 도구다. Next.js 프론트엔드에서 `fetch('http://localhost:8080/api/menus')`로 이 API를 호출하면, Postman에서 본 것과 동일한 JSON을 받을 수 있다. CORS 설정이 필요하면 `@CrossOrigin` 또는 `WebMvcConfigurer`로 허용 원본을 설정해야 한다. 지금은 로컬에서 테스트하므로 CORS 문제가 없지만, 프론트엔드(3000포트)와 백엔드(8080포트)가 다른 포트를 사용할 때 CORS가 발생한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| Connection refused | 서버가 안 떠 있음 | `mvn spring-boot:run`이 실행 중인지 확인 |
| 404 Not Found | URL 오타 또는 서버가 다른 포트 | `http://localhost:8080/api/menus` 정확히 입력, 서버 포트 확인 |
| JSON이 아니라 HTML 에러 페이지 | 서버가 에러를 반환 | 터미널에서 스프링 부트 로그를 확인, 스택 트레이스 확인 |

**📝 이 단계의 핵심**

- Postman은 API를 독립적으로 테스트하는 도구다.
- 200 OK와 올바른 JSON 구조가 보이면 API가 정상 동작한다.

## 정리

1단계: Spring Initializr로 `ncafe/backend` 프로젝트를 생성한다.
2단계: `main` 함수는 내장 Tomcat을 시작하고, `src/main/resources`는 설정과 정적 파일을 담당한다.
3단계: `@RestController` + `@GetMapping`으로 `/api/menus` API를 만들고, 목업 데이터를 반환한다.
4단계: Postman으로 `GET /api/menus` 요청을 보내 JSON 응답을 확인한다.

다음에 볼 따라하기: JPA로 데이터베이스에 연결하고, 실제 메뉴 데이터를 조회하는 API 만들기([[031_스프링 부트 백엔드 만들기 — PostgreSQL 연결과 JDBC Repository]]).
