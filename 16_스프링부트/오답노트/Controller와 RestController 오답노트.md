# Controller와 RestController 오답노트

### 1. @Controller와 @RestController의 차이에 관한 설명으로 옳은 것은?

**문제**: @Controller와 @RestController의 차이에 관한 설명으로 옳은 것은?

1. @RestController는 리포지토리 빈을 자동 등록하는 특수 컨트롤러이다.
2. 둘은 기능적으로 동일하며 단지 표기법의 차이일 뿐이다.
3. @Controller는 JSP/Thymeleaf 같은 뷰 이름을 반환하는 서버 렌더링에 주로 사용되고 @RestController는 JSON 등의 응답 본문을 직접 반환하는 API에 사용된다.
4. @Controller는 데이터 응답을 위해 사용하고 @RestController는 뷰 이름을 반환하기 위해 사용한다.

**정답: 3번**

두 어노테이션의 차이는 핵심적으로 다음 한 가지로 정리된다.

```
@RestController = @Controller + @ResponseBody
```

`@RestController`는 실제로 스프링 내부에서 `@Controller`에 `@ResponseBody`가 합성된 형태로 정의되어 있다.

```java
// @RestController의 실제 Spring 내부 정의 코드
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Controller      // 1. 컨트롤러임을 선언
@ResponseBody    // 2. 메서드의 반환값을 HTTP 응답 본문(Body)으로 직렬화
public @interface RestController { ... }
```

| 구분 | @Controller (기존 MVC) | @RestController (RESTful API) |
|---|---|---|
| 주요 반환값 | 뷰 이름(View Name) — 예: `"index"`, `"user/profile"` | 데이터/객체 — 예: `User` 객체, `List<DTO>`, `ResponseEntity` |
| 내부 처리 과정 | 반환된 문자열을 받아 **ViewResolver**가 해당하는 HTML/JSP/Thymeleaf 템플릿 파일을 찾아 렌더링함 | 반환된 자바 객체를 `HttpMessageConverter`(예: Jackson)가 JSON/XML 형태로 변환하여 HTTP Body에 출력함 |
| 주 목적 | 서버 사이드 렌더링(SSR) — HTML 화면을 만들어 브라우저에 전달 | REST API 서버 — React, Next.js, Vue, 모바일 앱 등에 순수 JSON 데이터 전달 |

**코드로 비교**

```java
// 1. @Controller — 화면을 돌려줄 때
@Controller
public class WebController {

    @GetMapping("/home")
    public String homePage() {
        // "home"이라는 이름의 뷰 파일(home.html 또는 home.jsp)을 찾아서 HTML을 렌더링
        return "home";
    }
}
```

```java
// 2. @RestController — React, Next.js 등 프론트엔드로 JSON을 던져줄 때
@RestController
public class ApiController {

    @GetMapping("/api/user")
    public User getUser() {
        // User 객체가 JSON 형태({"id": 1, "name": "김철수"})로 변환되어 HTTP Body에 담김
        return new User(1, "김철수");
    }
}
```

> 참고: `@Controller`를 쓰면서 특정 메서드에서만 JSON 데이터를 반환하고 싶다면, 메서드 위에 `@ResponseBody`를 직접 명시해주면 `@RestController`와 동일하게 작동한다.

**1번이 오답인 이유**: 리포지토리 빈(Repository Bean)을 등록하는 어노테이션은 `@Repository`다. `@RestController`는 HTTP 요청을 받아 처리하는 웹 계층(Presentation Layer) 컴포넌트이지, 데이터 접근 계층과는 무관하다.

**2번이 오답인 이유**: 반환값을 '뷰(View)'로 해석할지 'HTTP 응답 데이터(Body)'로 해석할지 처리 과정(ViewResolver vs HttpMessageConverter) 자체가 완전히 다르다. 단순한 표기법 차이가 아니라 동작 방식이 다른 별개의 조합이다.

**4번이 오답인 이유**: 역할이 서로 반대로 설명되어 있다. `@Controller`가 뷰 이름을, `@RestController`가 데이터를 반환한다.

**한 줄 요약**: `@RestController`는 `@Controller` + `@ResponseBody`이며, `@Controller`는 뷰 이름을(서버 렌더링), `@RestController`는 데이터를 그대로(REST API) 반환한다.

tags: #스프링부트 #Java #어노테이션 #Controller

> 🔗 관련 노트: [[073_스프링 DI]]
