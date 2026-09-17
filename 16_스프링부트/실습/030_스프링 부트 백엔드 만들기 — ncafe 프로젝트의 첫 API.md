---
tags: [웹, 스프링부트, Java, 실습]
---

> 🔗 관련 노트: [[033_어노테이션 기반 매핑과 RTTI(리플렉션)]] · [[031_스프링 부트 백엔드 만들기 — PostgreSQL 연결과 JDBC Repository]]

# 스프링 부트 백엔드 만들기 — ncafe 프로젝트의 첫 API

`ncafe/frontend` 옆에 `ncafe/backend`라는 스프링 부트 프로젝트를 새로 만들고, `/api/menus` GET API를 구현해 Postman으로 확인하는 과정을 정리한 실습이다.

## 1. Spring Initializr로 프로젝트 생성하기

VSCode 확장 모듈 창에서 "spring"을 검색하면 Spring Boot Dashboard, Spring Initializr Java Support, Spring Boot Tools, Spring Boot Extension Pack이 나온다. 이들은 서로 종속 관계라 Spring Boot Extension Pack 하나만 설치해도 대부분 같이 설치되지만, Spring Initializr가 빠져 있다면 따로 설치한다.

Command Palette(`Ctrl+Shift+P`)에서 `Spring: Create a new Spring Initializr Project`를 실행하고 아래 값을 입력한다.

| 항목 | 입력값 |
|---|---|
| Project Name | backend |
| Project Location | ncafe 폴더(현재 열려 있는 루트) |
| Language | Java |
| Build Tool | Maven |
| Java Version | 21 |
| Dependencies | Spring Web(필수), Lombok(선택, 추천) |

Location을 반드시 `ncafe` 폴더로 지정해야 `ncafe/backend`가 만들어진다. 다른 위치를 고르면 프론트엔드(`ncafe/frontend`)와 나란한 폴더 구조가 깨진다.

생성이 끝나면 VSCode 사이드바에서 `frontend` 옆에 `backend` 폴더가 생기고, 그 안에 `src`, `pom.xml`, `.mvn`이 보이는지 확인한다.

Spring Initializr는 스프링 부트 공식 프로젝트 생성기로, `pom.xml`에 필요한 의존성을 자동으로 넣고 기본 폴더 구조를 만들어준다. 서블릿 프로젝트에서 `web.xml`을 직접 작성하고 서블릿 클래스를 등록하던 과정을, 스프링 부트는 이 "자동 설정"으로 대신한다.

## 2. 생성된 폴더 구조 훑어보기

### 2-1. `BackendApplication.java` — 진입점

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

- `@SpringBootApplication`: 이 클래스가 스프링 부트 애플리케이션의 진입점임을 알린다. 자동 설정, 컴포넌트 스캔, 자동 구성을 함께 활성화한다.
- `SpringApplication.run(...)`: 내장 톰캣을 시작하고 스프링 컨텍스트를 로드한다. 서블릿 프로젝트에서 `web.xml`을 읽어 서블릿을 등록하던 과정을 이 한 줄이 대신한다.

### 2-2. `src/main/resources` — 설정과 정적 파일

| 파일/폴더 | 역할 |
|---|---|
| `application.properties` | 서버 포트, DB 연결 등 설정 값. 서블릿의 `web.xml`에 해당 |
| `static/` | 정적 파일(CSS, JS, 이미지) 서빙 폴더 |
| `templates/` | 서버 사이드 렌더링 템플릿(Thymeleaf 등) 폴더 |

Next.js 프론트엔드와 통신할 때는 `static/`을 거의 쓰지 않는다 — 프론트엔드가 이미 그 역할을 하기 때문이다.

### 2-3. `src/test/java` — 기본 테스트

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

`@SpringBootTest`는 스프링 컨텍스트를 로드해 테스트한다. `contextLoads()`는 컨텍스트가 정상적으로 시작되는지만 확인하는 기본 테스트다.

서블릿 프로젝트에서는 `web.xml`에 서블릿을 등록하고 `doGet`/`doPost`에서 직접 `HttpServletRequest`/`HttpServletResponse`를 처리했다. 스프링 부트에서는 `@SpringBootApplication`이 자동으로 내장 톰캣을 띄우고, `@RestController`로 만든 클래스를 자동으로 감지해 URL 매핑을 등록한다.

## 3. `/api/menus` API 만들기

### 3-1. `Menu` 엔티티

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

`@Data`(Lombok)는 getter/setter/toString/equals/hashCode를 자동으로 생성한다. 필드명은 자바 컨벤션(카멜케이스)으로 쓰고, JSON에서 스네이크케이스가 필요하면 `@JsonProperty`나 Jackson 설정으로 변환한다.

### 3-2. `MenuController`

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

- `@RestController`: `@Controller` + `@ResponseBody`의 합성어. 반환 값을 자동으로 JSON으로 변환한다.
- `@RequestMapping("/api")`: 이 컨트롤러의 모든 메서드에 `/api`를 기본 경로로 붙인다.
- `@GetMapping("/menus")`: `GET /api/menus` 요청을 이 메서드가 처리한다.
- 아직 데이터베이스가 없으므로 `ArrayList`에 값을 직접 넣어 목업 데이터로 반환한다.

서블릿의 `doGet`이 `request.getParameter()`로 값을 읽고 `response.getWriter()`로 JSON을 직접 작성했다면, 스프링에서는 `@GetMapping`이 요청을 메서드에 바인딩하고 반환 값을 Jackson이 자동으로 JSON으로 변환한다. `Menu` 엔티티는 데이터베이스 테이블과 1:1로 대응하도록 설계된 것이라, 나중에 JPA를 붙이면 이 클래스를 그대로 엔티티로 쓸 수 있다.

### 3-3. 서버 실행

```
cd ncafe/backend
mvn spring-boot:run
```

Maven이 없으면 IntelliJ IDEA에서 `BackendApplication.java`의 `main` 함수를 실행해도 된다. 터미널에 `Tomcat started on port(s): 8080`이 뜨고, 브라우저로 `http://localhost:8080/api/menus`를 열면 JSON 배열이 보인다.

## 4. Postman으로 확인하기

Postman에서 새 GET 요청을 만들고 URL에 `http://localhost:8080/api/menus`를 입력한 뒤 Send를 누르면, 응답 Body에 다음과 같은 JSON 배열이 온다.

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

200 OK 상태 코드와 함께, `price`는 숫자, `createTime`은 `"2026-09-15"` 형식의 문자열로 나오는지 확인한다. 프론트엔드에서 `fetch('http://localhost:8080/api/menus')`로 이 API를 호출하면 Postman에서 본 것과 같은 JSON을 받는다. 다만 프론트엔드(3000번 포트)와 백엔드(8080번 포트)처럼 포트가 다르면 CORS 문제가 생길 수 있고, 이때는 `@CrossOrigin` 또는 `WebMvcConfigurer`로 허용 원본을 설정해야 한다.

## 5. 자주 하는 실수

| 증상 | 원인 | 해결 |
|---|---|---|
| `backend`가 `ncafe` 밖에 생성됨 | Location을 `ncafe`가 아닌 상위 폴더로 선택 | `backend` 폴더를 `ncafe` 안으로 이동 |
| Spring Web이 선택되지 않음 | Dependencies 체크 전에 다음으로 넘어감 | Initializr 재실행 또는 `pom.xml`에 `spring-boot-starter-web` 직접 추가 |
| 404 Not Found | `@RequestMapping`/`@GetMapping` 경로 오타 | 최종 경로가 `/api/menus`인지 확인 |
| Lombok 에러(`cannot find symbol: method setId`) | Lombok 플러그인 미설치 또는 `@Data` 누락 | IDE에서 Lombok 플러그인 활성화, 또는 `@Data` 제거 후 수동 getter/setter 작성 |
| `mvn: command not found` | Maven 미설치 또는 PATH 미설정 | Maven 설치 후 PATH 설정, 또는 IDE에서 직접 실행 |
| Connection refused(Postman) | 서버가 떠 있지 않음 | `mvn spring-boot:run`이 실행 중인지 확인 |

## 6. 정리

| 단계 | 내용 |
|---|---|
| 1 | Spring Initializr로 `ncafe/backend` 프로젝트 생성 |
| 2 | `main` 함수가 내장 톰캣을 시작, `src/main/resources`가 설정·정적 파일 담당 |
| 3 | `@RestController` + `@GetMapping`으로 `/api/menus` API를 만들고 목업 데이터 반환 |
| 4 | Postman으로 `GET /api/menus` 요청을 보내 JSON 응답 확인 |

다음 실습에서는 JPA로 데이터베이스에 연결해 실제 메뉴 데이터를 조회하는 API를 만든다.
