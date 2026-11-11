---
tags: [ErrorResponse, AuthenticationEntryPoint, AccessDeniedHandler, RestControllerAdvice, 401, 403, JWT, SpringSecurity, 실습]
---

> 🔗 관련 노트: [[053_Refresh Token으로 조용히 갱신하기 — 재발급 API, RefreshTokenStore, proxy 문지기]] · [[052_Next.js 쿠키 기반 인증과 미들웨어 권한 제어 코드]] · [[050_스프링 부트 JWT 인증 구현 — JJWT 설정, JwtProvider, JwtAuthenticationFilter, SecurityConfig, 로그인 API]] · [[098_스프링 시큐리티 인가 설정 — URL별 허용 규칙, 역할, 커스텀 로그인 페이지]]

# 스프링 시큐리티의 401·403 응답을 JSON으로 통일하기 — ErrorResponse, EntryPoint, AccessDeniedHandler

> **첨부 파일 안내**
> - `ncafe-prep-08-auth-error-response.zip`: 현재 노트의 내용이 적용되기 **전** 상태의 프로젝트 파일이다. 이 노트를 보면서 실습해보고 싶은 사람은 그 파일을 다운로드 한 후 압축을 해제해서 사용하길 바란다.
> - `ncafe-lesson-08-auth-error-response.zip`: 이 노트 전체가 **적용된** 파일이다. 전체가 적용된 결과를 확인하고 싶을 때 사용할 수 있다.
>
> 참고 프로젝트 경로(적용 완료본): `ncafe-lesson-08-auth-error-response`

---

이전 노트([[053_Refresh Token으로 조용히 갱신하기 — 재발급 API, RefreshTokenStore, proxy 문지기]])에서는 Refresh Token으로 Access Token을 조용히 갱신하는 구조를 완성했다. 로그인, 재발급, 로그아웃, 문지기까지 인증의 큰 흐름은 다 만들어졌다.

이번 노트는 그 흐름에서 실패했을 때 스프링이 뭐라고 대답하는지를 다룬다. 지금까지는 성공 경로에 집중하느라 실패 응답을 스프링 시큐리티의 기본값에 맡겨 두었다. 그 기본값이 어떤 모양인지 보면 왜 손봐야 하는지가 바로 드러난다.

```bash
# 토큰 없이 보호된 API 호출
curl -i http://localhost:8080/api/menus

HTTP/1.1 403
{"timestamp":"2026-10-29T08:25:50.224Z","status":403,"error":"Forbidden","message":"Forbidden","path":"/api/menus"}

# 비밀번호를 틀리게 로그인
curl -i -X POST http://localhost:8080/api/auth/login \
  -H 'Content-Type: application/json' -d '{"username":"newlec","password":"x"}'

HTTP/1.1 403
```

두 가지가 눈에 띈다. 토큰이 없는 것도 403, 비밀번호가 틀린 것도 403이다. HTTP에서 403은 "누군지는 알겠는데 권한이 없다"는 뜻이고, "누군지 모르겠다"는 401이다. 지금은 이 둘이 섞여 있어서 프론트엔드가 "다시 로그인하세요"와 "권한이 없습니다"를 구분할 수 없다. 그리고 본문은 스프링 부트의 `/error` 기본 형식이라 메시지가 "Forbidden"뿐이다. 사용자에게 보여줄 말이 없다.

이번 노트에서는 다음 순서로 진행한다.

1. 스프링 시큐리티가 실패를 처리하는 두 지점이 어디인지 본다.
2. 모든 에러가 공유할 응답 형식(`ErrorResponse`)을 만든다.
3. 인증 실패를 401 JSON으로 바꾸는 엔트리포인트를 만든다.
4. 권한 부족을 403 JSON으로 바꾸는 `AccessDeniedHandler`를 만든다.
5. 컨트롤러에서 던진 예외도 같은 형식이 되도록 `@RestControllerAdvice`로 모은다.
6. `SecurityConfig`에 등록한다.
7. Postman으로 아홉 가지 경우를 확인한다.
8. 프론트엔드가 그 메시지를 그대로 보여주게 한다.

---

## 1. 스프링 시큐리티는 실패를 어디서 처리하는가

### 1) 401과 403

| 상태 | 이름 | 뜻 | 우리 서비스에서 |
|---|---|---|---|
| 401 | Unauthorized | 인증 실패 — 누군지 모른다 | 토큰이 없다, 만료됐다, 위조됐다, 비밀번호가 틀렸다 |
| 403 | Forbidden | 인가 실패 — 누군지는 알지만 권한이 없다 | USER 토큰으로 `/api/admin/**`을 불렀다 |

이름이 헷갈리기로 유명하다. "Unauthorized"라고 쓰여 있지만 실제 뜻은 "Unauthenticated(인증 안 됨)"에 가깝다. 역사적인 이름이라 어쩔 수 없다. 401은 로그인 문제, 403은 권한 문제로 외우면 된다.

프론트엔드 입장에서 이 구분은 행동을 결정한다.

- 401을 받으면 → 토큰을 버리고 로그인 페이지로 보낸다.
- 403을 받으면 → 로그인은 유지하고 "권한이 없습니다"를 보여준다.

### 2) ExceptionTranslationFilter — 두 갈래 길

스프링 시큐리티의 필터 체인 안에는 `ExceptionTranslationFilter`라는 필터가 있다. 이름 그대로 예외를 HTTP 응답으로 번역하는 필터다. 뒤쪽 필터나 컨트롤러에서 예외가 올라오면 이 필터가 잡아서 두 갈래로 보낸다.

```
                        ┌─ AuthenticationException ─▶ AuthenticationEntryPoint ─▶ (401)
ExceptionTranslationFilter ─┤
                        └─ AccessDeniedException ───▶ AccessDeniedHandler ──────▶ (403)
```

- `AuthenticationException`: "인증이 안 됐다." 토큰 없이 보호된 경로에 왔을 때 인가 필터가 던지고, 로그인에서 비밀번호가 틀렸을 때 `AuthenticationManager`가 던진다(`BadCredentialsException`이 이것의 자식이다).
- `AccessDeniedException`: "인증은 됐는데 권한이 모자란다." `hasRole("ADMIN")`에 USER가 걸렸을 때 인가 필터가 던진다.

여기서 기본값의 함정이 드러난다. `AuthenticationEntryPoint`를 지정하지 않으면 스프링 시큐리티는 `Http403ForbiddenEntryPoint`를 쓴다. 이름 그대로 401 상황에서 403을 돌려준다. 폼 로그인이나 HTTP Basic을 켜면 각자의 엔트리포인트(로그인 페이지로 리다이렉트, `WWW-Authenticate` 헤더)가 자동으로 붙지만, 우리는 둘 다 끄고 JWT 필터만 쓰기 때문에 엔트리포인트가 비어 있다. 그래서 전부 403이었다.

### 3) 번역이 일어나는 두 층

실패는 두 층에서 생긴다.

| 층 | 예 | 누가 번역하나 |
|---|---|---|
| 필터 층 (컨트롤러에 닿기 전) | 토큰 없음, 토큰 무효, 권한 부족 | `ExceptionTranslationFilter` → 엔트리포인트 / `AccessDeniedHandler` |
| 컨트롤러 층 (컨트롤러·서비스 안) | 비밀번호 불일치, 리프레시 토큰 무효 | 스프링 MVC의 `@ExceptionHandler` / `@RestControllerAdvice` |

컨트롤러 층의 예외는 MVC가 먼저 잡을 기회를 가진다. MVC가 처리하지 않고 흘려보내면 필터 층까지 올라가서 `ExceptionTranslationFilter`가 잡는다. 지금까지 비밀번호 불일치가 403이었던 것은 `BadCredentialsException`이 MVC에서 처리되지 않고 필터까지 올라가 `Http403ForbiddenEntryPoint`를 만났기 때문이다.

이번 노트의 설계는 이렇다. 필터 층은 시큐리티 핸들러가, 컨트롤러 층은 `@RestControllerAdvice`가 맡되, 두 층이 같은 응답 형식을 쓴다.

---

## 2. 공통 응답 형식 — ErrorResponse

프론트엔드가 "실패 응답은 어떤 모양인가"를 한 가지만 알면 되도록, 모든 에러가 같은 DTO를 쓴다. `dto/common` 패키지를 새로 만든다.

```java
package com.ncafe.backend.dto.common;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;

/**
 * 모든 에러 응답의 공통 형식.
 *
 * 스프링 시큐리티의 401/403, 컨트롤러의 예외, 나중에 추가될 검증 오류까지
 * 전부 이 모양으로 내려보내면 프론트엔드는 "status 와 message 를 읽는다" 한 가지만 알면 된다.
 */
@Data
@Builder
public class ErrorResponse {
    private int status;        // HTTP 상태 코드 (401, 403, ...)
    private String error;      // 상태 코드의 이름 (UNAUTHORIZED, FORBIDDEN, ...)
    private String message;    // 사람이 읽을 설명. 프론트가 그대로 화면에 보여줄 수 있다
    private String path;       // 요청 경로. 디버깅용
    private Instant timestamp;

    public static ErrorResponse of(int status, String error, String message, String path) {
        return ErrorResponse.builder()
                .status(status)
                .error(error)
                .message(message)
                .path(path)
                .timestamp(Instant.now())
                .build();
    }
}
```

- 필드 구성은 스프링 부트의 `/error` 형식을 따랐다. `status`, `error`, `message`, `path`, `timestamp`. 익숙한 모양이라 Postman에서 봤을 때 낯설지 않고, 기본 형식을 쓰는 다른 에러(404 등)와도 비슷하다.
- `message`는 사용자에게 보여줄 문장이다. 스프링 내부 사정("Full authentication is required to access this resource")이 아니라 "로그인이 필요합니다."처럼 쓴다. 프론트가 번역 없이 화면에 올릴 수 있게 하는 것이 목표다.
- `of()` 정적 메서드: 네 군데에서 만들게 되므로 `timestamp`를 매번 채우지 않도록 묶었다.

---

## 3. 인증 실패 → 401 — JsonAuthenticationEntryPoint

```java
package com.ncafe.backend.security.handler;

import tools.jackson.databind.ObjectMapper;
import com.ncafe.backend.dto.common.ErrorResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.stereotype.Component;

import java.io.IOException;

/**
 * "인증되지 않은" 요청이 보호된 경로에 왔을 때 호출된다 → 401.
 *
 * 스프링 시큐리티는 엔트리포인트를 지정하지 않으면 403 Forbidden 을 돌려준다(Http403ForbiddenEntryPoint).
 * 그러면 "토큰이 없다"(401)와 "권한이 없다"(403)를 구분할 수 없어 프론트엔드가 올바르게 대응하지 못한다.
 *
 * 토큰이 없는 경우와 있지만 쓸 수 없는 경우(만료·위조)를 메시지로 구분한다.
 */
@Component
public class JsonAuthenticationEntryPoint implements AuthenticationEntryPoint {

    private final ObjectMapper objectMapper;

    public JsonAuthenticationEntryPoint(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    @Override
    public void commence(HttpServletRequest request,
                         HttpServletResponse response,
                         AuthenticationException authException) throws IOException {

        String message = request.getHeader("Authorization") == null
                ? "로그인이 필요합니다."
                : "토큰이 유효하지 않거나 만료되었습니다.";

        ErrorResponse body = ErrorResponse.of(
                HttpStatus.UNAUTHORIZED.value(),
                HttpStatus.UNAUTHORIZED.name(),
                message,
                request.getRequestURI()
        );

        response.setStatus(HttpStatus.UNAUTHORIZED.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");
        objectMapper.writeValue(response.getWriter(), body);
    }
}
```

### 1) 왜 직접 JSON을 쓰는가

컨트롤러에서는 객체를 `return`하면 스프링 MVC가 알아서 JSON으로 바꿔 준다. 하지만 엔트리포인트는 필터 층이라 MVC가 아직 개입하기 전이다. 그래서 `HttpServletResponse`에 상태 코드, Content-Type, 본문을 손으로 써야 한다. `ObjectMapper`는 스프링 부트가 빈으로 등록해 두므로 생성자로 주입받는다.

### 2) import `tools.jackson.databind.ObjectMapper`

이 프로젝트는 Spring Boot 4를 쓰고, Spring Boot 4는 Jackson 3를 쓴다. Jackson 3에서 패키지가 `com.fasterxml.jackson.databind`에서 `tools.jackson.databind` 로 바뀌었다. 인터넷의 예제 대부분은 옛 패키지를 쓰므로 그대로 복사하면 `cannot find symbol: class ObjectMapper`가 난다. 클래스 이름은 같고 패키지만 다르다.

### 3) 메시지 두 가지

`Authorization` 헤더가 아예 없으면 "로그인이 필요합니다", 있는데도 여기까지 왔으면 필터가 토큰을 거절한 것이므로 "토큰이 유효하지 않거나 만료되었습니다"다. 지난 노트의 "역할 없는 리프레시 토큰을 Bearer로 보낸 경우"도 후자에 해당한다. 필터가 출입증을 주지 않고 넘겼기 때문에 인증 없음으로 여기 도착한다.

만료와 위조를 더 세분하고 싶다면 `JwtAuthenticationFilter`에서 거절 사유를 `request.setAttribute()`로 남기고 여기서 읽으면 된다. 이번 노트에서는 프론트엔드가 둘을 구분할 필요가 없어서(어느 쪽이든 재로그인) 합쳤다.

---

## 4. 권한 부족 → 403 — JsonAccessDeniedHandler

```java
package com.ncafe.backend.security.handler;

import tools.jackson.databind.ObjectMapper;
import com.ncafe.backend.dto.common.ErrorResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.stereotype.Component;

import java.io.IOException;

/**
 * 인증은 됐지만 권한이 모자란 요청 → 403.
 * 예: USER 토큰으로 /api/admin/** 호출.
 *
 * 기본 동작도 403 이지만 본문이 스프링 부트의 /error 형식이라 ErrorResponse 로 통일한다.
 */
@Component
public class JsonAccessDeniedHandler implements AccessDeniedHandler {

    private final ObjectMapper objectMapper;

    public JsonAccessDeniedHandler(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    @Override
    public void handle(HttpServletRequest request,
                       HttpServletResponse response,
                       AccessDeniedException accessDeniedException) throws IOException {

        ErrorResponse body = ErrorResponse.of(
                HttpStatus.FORBIDDEN.value(),
                HttpStatus.FORBIDDEN.name(),
                "이 기능을 사용할 권한이 없습니다.",
                request.getRequestURI()
        );

        response.setStatus(HttpStatus.FORBIDDEN.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");
        objectMapper.writeValue(response.getWriter(), body);
    }
}
```

엔트리포인트와 구조가 같다. 상태 코드가 403이고 메시지가 하나뿐이라는 점만 다르다. 이쪽은 기본 동작도 403이었으므로 상태 코드는 그대로고 본문만 바뀐다.

두 클래스의 JSON 쓰는 코드 네 줄이 똑같다. 공통 메서드로 뽑고 싶어질 텐데, 두 개뿐이라 그대로 두었다. 세 번째 핸들러가 생기면 그때 뽑는다.

---

## 5. 컨트롤러 층의 예외 — GlobalExceptionHandler

지난 노트에서 `AuthController` 안에 `@ExceptionHandler(InvalidTokenException.class)`를 두어 재발급 실패를 401로 바꿨다. 그때는 `Map.of("message", ...)`를 돌려줬는데, 이제 `ErrorResponse` 형식이 생겼으니 거기에 맞추고, 비밀번호 불일치도 같은 곳에서 처리한다.

컨트롤러 하나에 붙은 `@ExceptionHandler`는 그 컨트롤러에서만 동작한다. 앞으로 컨트롤러가 늘어날 것이므로 `@RestControllerAdvice`로 뽑아 모든 컨트롤러에 적용한다.

```java
package com.ncafe.backend.controller;

import com.ncafe.backend.dto.common.ErrorResponse;
import com.ncafe.backend.security.jwt.InvalidTokenException;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 컨트롤러 안에서 던져진 예외를 ErrorResponse 로 바꾼다.
 *
 * 필터 단계의 401/403 은 시큐리티 핸들러(JsonAuthenticationEntryPoint, JsonAccessDeniedHandler)가 맡고,
 * 컨트롤러·서비스 단계의 예외는 여기서 맡는다. 두 곳 모두 같은 ErrorResponse 형식을 쓴다.
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    /** 로그인: 아이디·비밀번호 불일치. AuthenticationManager 가 던진다 */
    @ExceptionHandler(BadCredentialsException.class)
    @ResponseStatus(HttpStatus.UNAUTHORIZED)
    public ErrorResponse handleBadCredentials(BadCredentialsException e, HttpServletRequest request) {
        return ErrorResponse.of(
                HttpStatus.UNAUTHORIZED.value(),
                HttpStatus.UNAUTHORIZED.name(),
                "아이디 또는 비밀번호가 올바르지 않습니다.",
                request.getRequestURI()
        );
    }

    /** 재발급: 리프레시 토큰이 위조·만료·폐기됨. AuthService.refresh() 가 던진다 */
    @ExceptionHandler(InvalidTokenException.class)
    @ResponseStatus(HttpStatus.UNAUTHORIZED)
    public ErrorResponse handleInvalidToken(InvalidTokenException e, HttpServletRequest request) {
        return ErrorResponse.of(
                HttpStatus.UNAUTHORIZED.value(),
                HttpStatus.UNAUTHORIZED.name(),
                e.getMessage(),
                request.getRequestURI()
        );
    }
}
```

- `@RestControllerAdvice`: `@ControllerAdvice` + `@ResponseBody`. 모든 `@RestController`에 공통으로 적용되는 `@ExceptionHandler` 모음이다. 여기서는 객체를 `return`하면 MVC가 JSON으로 바꿔 주므로, 3절과 달리 `ObjectMapper`를 직접 다룰 필요가 없다.
- `BadCredentialsException`을 여기서 잡는 이유: 1절 3)에서 봤듯이 이 예외는 MVC가 처리하지 않으면 필터까지 올라가 엔트리포인트를 만난다. 엔트리포인트에 맡겨도 401은 나오지만, 메시지가 "토큰이 유효하지 않거나 만료되었습니다"가 되어 버린다(로그인 요청에는 `Authorization` 헤더가 있을 수도 없을 수도 있다). 로그인 실패는 로그인 실패답게 "아이디 또는 비밀번호가 올바르지 않습니다"로 답하려면 컨트롤러 층에서 잡아야 한다.
- `e.getMessage()`를 그대로 쓰는 것: `InvalidTokenException`은 지난 노트에서 우리가 만든 예외라 메시지가 이미 사용자용 문장이다("리프레시 토큰이 유효하지 않습니다.", "이미 만료 처리된 리프레시 토큰입니다."). 반면 `BadCredentialsException`의 메시지는 스프링 것("Bad credentials")이라 우리 문장으로 바꿔 쓴다.
- 아이디가 없는 경우도 같은 메시지다. `AuthenticationManager`는 "아이디 없음"(`UsernameNotFoundException`)을 보안상 `BadCredentialsException`으로 숨겨서 던진다. 공격자가 "이 아이디는 존재한다"는 사실을 알아낼 수 없게 하기 위해서다.

### AuthController에서 지역 핸들러 제거

지난 노트에서 넣었던 `@ExceptionHandler` 메서드와 그 import(`ExceptionHandler`, `InvalidTokenException`, `Map`)를 지운다. 남는 것은 세 엔드포인트뿐이다.

```java
package com.ncafe.backend.controller;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.ncafe.backend.dto.auth.LoginRequest;
import com.ncafe.backend.dto.auth.LoginResponse;
import com.ncafe.backend.dto.auth.RefreshRequest;
import com.ncafe.backend.service.AuthService;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;


@RestController 
@RequestMapping("/api/auth")
public class AuthController {
    private final AuthService service;

    public AuthController(AuthService service){
        this.service = service;
    }

    
    @PostMapping("/login")    
    public LoginResponse login(@RequestBody LoginRequest loginRequest){

        LoginResponse tokenResponse = service.login(loginRequest);

        return tokenResponse;
    }

    /** 액세스 토큰이 만료됐을 때 리프레시 토큰으로 새 액세스 토큰을 받는다. */
    @PostMapping("/refresh")
    public LoginResponse refresh(@RequestBody RefreshRequest refreshRequest){

        return service.refresh(refreshRequest.getRefreshToken());
    }

    /** 리프레시 토큰을 폐기한다. 액세스 토큰은 남은 수명(최대 30분)까지만 유효하다. */
    @PostMapping("/logout")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void logout(@RequestBody RefreshRequest refreshRequest){

        service.logout(refreshRequest.getRefreshToken());
    }
}
```

---

## 6. SecurityConfig에 등록하기

두 핸들러를 생성자로 주입받고, `exceptionHandling()`으로 필터 체인에 꽂는다.

```java
package com.ncafe.backend.config;

import com.ncafe.backend.security.handler.JsonAccessDeniedHandler;
import com.ncafe.backend.security.handler.JsonAuthenticationEntryPoint;
import com.ncafe.backend.security.jwt.JwtAuthenticationFilter;
import com.ncafe.backend.security.jwt.JwtProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    private final JwtProvider jwtProvider;
    private final JsonAuthenticationEntryPoint authenticationEntryPoint;
    private final JsonAccessDeniedHandler accessDeniedHandler;

    public SecurityConfig(JwtProvider jwtProvider,
                          JsonAuthenticationEntryPoint authenticationEntryPoint,
                          JsonAccessDeniedHandler accessDeniedHandler) {
        this.jwtProvider = jwtProvider;
        this.authenticationEntryPoint = authenticationEntryPoint;
        this.accessDeniedHandler = accessDeniedHandler;
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            // 1. CSRF 비활성화
            .csrf(AbstractHttpConfigurer::disable)

            // 2. 세션을 사용하지 않으므로 STATELESS로 설정
            .sessionManagement(session -> 
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )

            // 3. 경로별 접근 권한 설정
            .authorizeHttpRequests(auth -> auth
                // 로그인, 회원가입 등 공개 API는 토큰 없이도 접근 허용
                .requestMatchers("/api/auth/**", "/error").permitAll()
                // 관리자만 접근 가능
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                // 그 외의 모든 요청은 인증된 사용자만 접근 가능
                .anyRequest().authenticated()
            )

            // 4. 커스텀 JWT 필터를 UsernamePasswordAuthenticationFilter 앞에 배치
            .addFilterBefore(
                new JwtAuthenticationFilter(jwtProvider), 
                UsernamePasswordAuthenticationFilter.class
            )

            // 5. 인증·인가 실패를 JSON 으로 응답
            //    - 인증 안 됨(토큰 없음·만료·위조) → 401 (JsonAuthenticationEntryPoint)
            //    - 인증은 됐지만 권한 부족      → 403 (JsonAccessDeniedHandler)
            //    지정하지 않으면 둘 다 403 에 스프링 부트 기본 /error 본문이 내려간다.
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint(authenticationEntryPoint)
                .accessDeniedHandler(accessDeniedHandler)
            );

        return http.build();
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration authenticationConfiguration) throws Exception {
        return authenticationConfiguration.getAuthenticationManager();
    }

    @Bean 
    public PasswordEncoder passwordEncoder(){
        return new BCryptPasswordEncoder();
    }

    @Bean 
    public UserDetailsService userDetailsService(PasswordEncoder passWordEncoder){

        UserDetails user = User.builder()
                            .username("newlec")
                            .password(passWordEncoder.encode("123"))
                            .roles("USER")
                            .build();

        UserDetails admin = User.builder()
                            .username("admin")
                            .password(passWordEncoder.encode("123"))
                            .roles("USER", "ADMIN")
                            .build();

        return new InMemoryUserDetailsManager(user, admin);
    }    
}
```

- 생성자 주입: 두 핸들러는 `@Component`라 스프링이 빈으로 만들어 둔다. `SecurityConfig`가 생성자로 받는다. `JwtProvider`를 받던 방식과 같다.
- `exceptionHandling()`: `ExceptionTranslationFilter`의 두 갈래(1절 2)에 우리 핸들러를 꽂는 설정이다. 4번 뒤에 체이닝으로 이어 붙였으므로 4번 끝의 `;`가 `)`로 바뀐 것에 주의한다.
- `/error`의 `permitAll()`은 그대로 둔다. 이제 401/403은 `/error`를 거치지 않지만, 404 같은 다른 에러는 여전히 스프링 부트의 `/error`로 포워딩된다. 그 경로가 인증을 요구하면 404가 401로 둔갑하는 혼란이 생긴다.

---

## 7. Postman으로 확인하기

스프링을 재시작하고 아홉 가지를 확인한다. 이번 노트의 요점은 상태 코드와 본문 모양이므로, 각 응답에서 `status`와 `message`를 본다.

| # | 요청 | 기대 상태 | 기대 message | 번역한 곳 |
|---|---|---|---|---|
| 1 | `GET /api/menus` (헤더 없음) | 401 | 로그인이 필요합니다. | 엔트리포인트 |
| 2 | `GET /api/menus` + `Bearer abc.def.ghi` | 401 | 토큰이 유효하지 않거나 만료되었습니다. | 엔트리포인트 |
| 3 | `POST /api/auth/login {"username":"newlec","password":"x"}` | 401 | 아이디 또는 비밀번호가 올바르지 않습니다. | `GlobalExceptionHandler` |
| 4 | newlec / 123으로 로그인 후, 그 `accessToken`으로 `GET /api/admin/menus` | 403 | 이 기능을 사용할 권한이 없습니다. | `AccessDeniedHandler` |
| 5 | 같은 토큰으로 `GET /api/menus` | 200 | (메뉴 배열) | — |
| 6 | 4번 로그인의 `refreshToken`을 Bearer로 `GET /api/menus` | 401 | 토큰이 유효하지 않거나 만료되었습니다. | 엔트리포인트 (필터가 역할 없는 토큰을 거절) |
| 7 | `POST /api/auth/refresh {"refreshToken":"abc.def.ghi"}` | 401 | 리프레시 토큰이 유효하지 않습니다. | `GlobalExceptionHandler` |
| 8 | `POST /api/auth/refresh` (4번의 진짜 `refreshToken`) | 200 | (새 `accessToken`) | — |
| 9 | `GET /api/nothing` (헤더 없음) | 401 | 로그인이 필요합니다. | 엔트리포인트 |

실제 응답 하나를 보면 이렇다.

```json
{
  "error": "UNAUTHORIZED",
  "message": "로그인이 필요합니다.",
  "path": "/api/menus",
  "status": 401,
  "timestamp": "2026-10-29T08:27:56.843676060Z"
}
```

1번과 3번을 비교해 보자. 이번 노트 전에는 둘 다 403에 본문이 "Forbidden" 또는 비어 있었다. 이제 둘 다 401이지만 메시지로 사정을 알 수 있고, 4번(진짜 403)과는 상태 코드로 구분된다.

9번은 "없는 경로인데 404가 아니라 401인가?" 싶을 수 있다. 인가 필터는 컨트롤러 매핑을 보기 전에 동작한다. `anyRequest().authenticated()`에 걸려 404 여부를 따지기도 전에 401로 끝난다. 보호된 서버는 로그인하지 않은 사람에게 "그 경로가 존재하는지"조차 알려주지 않는 셈이라 의도된 동작이다. 토큰을 붙여서 보내면 404가 난다.

---

## 8. 프론트엔드 — 메시지를 그대로 보여주기

백엔드가 사람이 읽을 메시지를 내려주므로 프론트엔드는 그 문장을 꺼내 보여주기만 하면 된다. 지금까지 프론트가 자체적으로 만들던 문구("아이디 또는 비밀번호가 올바르지 않아요", "백엔드가 403로 거절했어요")를 백엔드 메시지로 바꾼다.

### 1) `backend.ts` — `readErrorMessage()`

`backendFetch`가 있는 파일에 에러 본문을 읽는 도우미를 더한다.

```ts
import { getSession } from "./session";
import { BACKEND_URL } from "./env";

export { BACKEND_URL };

/**
 * 쿠키의 토큰을 Authorization: Bearer 헤더로 바꿔 백엔드를 호출한다.
 *
 * 브라우저 → Next.js 서버 → 스프링 순서로만 통신한다(BFF 구조).
 * 브라우저가 스프링을 직접 부르지 않으므로 CORS 설정이 필요 없고,
 * 토큰이 클라이언트 자바스크립트에 노출되지 않는다.
 *
 * 액세스 토큰이 만료됐을 때의 재발급은 여기서 하지 않는다. 서버 컴포넌트는 쿠키를 새로 쓸 수 없기 때문이다.
 * 재발급은 요청이 페이지에 닿기 전에 proxy.ts 가 끝내 두므로, 여기에 오는 토큰은 늘 유효하다.
 */
export async function backendFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const session = await getSession();
  const headers = new Headers(init.headers);
  if (session) headers.set("Authorization", `Bearer ${session.token}`);
  return fetch(`${BACKEND_URL}${path}`, { ...init, headers, cache: "no-store" });
}

/** 백엔드 ErrorResponse 의 모양. status 와 message 만 있으면 프론트는 충분하다 */
export type BackendError = { status: number; error: string; message: string; path: string };

/**
 * 실패 응답(4xx/5xx)에서 사람이 읽을 메시지를 꺼낸다.
 * 백엔드가 ErrorResponse 형식으로 내려주면 그 message 를, 아니면 상태 코드로 만든 기본 문구를 돌려준다.
 */
export async function readErrorMessage(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as Partial<BackendError>;
    if (typeof body.message === "string" && body.message) return body.message;
  } catch {
    // JSON 이 아니면 아래 기본 문구
  }
  return `요청이 실패했어요. (HTTP ${res.status})`;
}
```

`try/catch`와 `Partial<>`로 감싼 이유는 백엔드를 완전히 믿지 않기 위해서다. 스프링이 아예 죽어서 프록시나 게이트웨이가 HTML을 돌려줄 수도 있고, 아직 `ErrorResponse`로 바꾸지 않은 에러(404 등)는 본문 모양이 다르다. 어떤 경우든 함수는 문자열 하나를 돌려주고, 호출하는 쪽은 분기 없이 화면에 올린다.

### 2) `loginAction.ts` — 상태 코드 분기 제거

지난 노트까지는 401과 403을 묶어 "아이디 또는 비밀번호가 올바르지 않아요"를 프론트가 만들어 냈다. 이제 백엔드가 알려주므로 분기가 사라진다.

```ts
"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { BACKEND_URL } from "@/app/_lib/auth/env";
import { readErrorMessage } from "@/app/_lib/auth/backend";
import { accessTokenCookie, refreshTokenCookie } from "@/app/_lib/auth/cookies";

/** useActionState가 주고받는 상태. 성공하면 redirect 되므로 실패 메시지만 담는다 */
export type LoginState = { error: string | null };

/**
 * 로그인 Server Action.
 * 1. 폼 값을 꺼내 스프링의 POST /api/auth/login 으로 보낸다.
 * 2. 돌려받은 accessToken(30분)과 refreshToken(14일)을 각각 HttpOnly 쿠키에 저장한다.
 * 3. 원래 가려던 페이지(next)로 이동시킨다.
 */
export async function login(_prev: LoginState, formData: FormData): Promise<LoginState> {
  const username = String(formData.get("username") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const next = String(formData.get("next") ?? "/");

  if (!username || !password) {
    return { error: "아이디와 비밀번호를 입력해 주세요." };
  }

  // 1. 백엔드에 인증 요청
  let res: Response;
  try {
    res = await fetch(`${BACKEND_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
      cache: "no-store",
    });
  } catch {
    return { error: `백엔드 서버에 연결할 수 없어요. (${BACKEND_URL})` };
  }

  // 백엔드가 ErrorResponse 로 사유를 내려준다 (401: 아이디·비밀번호 불일치)
  if (!res.ok) {
    return { error: await readErrorMessage(res) };
  }

  const { accessToken, refreshToken } = (await res.json()) as {
    accessToken: string;
    refreshToken: string;
    tokenType: string;
  };

  // 2. 두 토큰을 각각의 HttpOnly 쿠키에 저장 — 쿠키 수명은 토큰 만료 시각에 맞춘다
  const cookieStore = await cookies();
  for (const c of [accessTokenCookie(accessToken), refreshTokenCookie(refreshToken)]) {
    cookieStore.set(c.name, c.value, c.options);
  }

  // 3. 원래 가려던 곳으로. 외부 주소로 보내지 않도록 "/"로 시작하는 경로만 허용
  const safeNext = next.startsWith("/") && !next.startsWith("//") ? next : "/";
  redirect(safeNext);
}
```

"연결할 수 없어요"만 프론트에 남았다. 백엔드가 응답조차 못 하는 상황은 백엔드가 메시지를 줄 수 없으니 당연하다.

### 3) `backendCheckApi.ts` — 거절 사유 표시

관리자 대시보드의 연결 확인 위젯도 같은 도우미를 쓴다.

```ts
import { backendFetch, BACKEND_URL, readErrorMessage } from "@/app/_lib/auth/backend";

export type BackendCheckResult =
  | { ok: true; status: number; menus: string[] }
  | { ok: false; status: number | null; message: string };

/** GET /api/admin/menus — ADMIN 토큰이 있어야 200. 토큰이 실제로 백엔드까지 통하는지 확인한다 */
export async function checkAdminMenus(): Promise<BackendCheckResult> {
  try {
    const res = await backendFetch("/api/admin/menus");
    if (!res.ok) return { ok: false, status: res.status, message: await readErrorMessage(res) };
    return { ok: true, status: res.status, menus: (await res.json()) as string[] };
  } catch {
    return { ok: false, status: null, message: `백엔드(${BACKEND_URL})에 연결할 수 없어요.` };
  }
}
```

`BackendCheck.tsx`는 이미 `result.message`를 화면에 올리고 있어서 손댈 것이 없다.

### 4) 브라우저에서 확인

| # | 할 일 | 기대 결과 | 어디서 오나 |
|---|---|---|---|
| 1 | newlec / wrong으로 로그인 | 폼 아래 "⚠ 아이디 또는 비밀번호가 올바르지 않습니다." | 백엔드 `GlobalExceptionHandler` → `readErrorMessage` |
| 2 | 스프링을 끄고 로그인 | "⚠ 백엔드 서버에 연결할 수 없어요. (`http://localhost:8080`)" | 프론트 `catch` |
| 3 | admin / 123으로 로그인 후 `/admin` | "스프링 백엔드 연결됨 · 200" | 변화 없음 |

1번의 문장이 백엔드에서 왔다는 것이 이번 노트의 결과다. 문구를 바꾸고 싶으면 이제 `GlobalExceptionHandler` 한 곳만 고치면 되고, 프론트는 재배포하지 않아도 된다.

USER로 `/admin`에 들어가 403 메시지를 보려면? 지금은 문지기(`proxy.ts`)가 토큰의 `role`을 보고 `/my`로 돌려보내기 때문에 USER는 `/admin` 화면 자체에 닿지 못한다. 403 메시지가 화면에 뜨는 것은 쿠키를 조작해 `role`을 ADMIN으로 바꾼 경우뿐이고, 그때 스프링이 서명 불일치로 401을 준다. 즉 정상 경로에서는 문지기가 먼저 막고, 비정상 경로에서는 스프링이 막는다. 이것이 지난 노트들에서 말한 "1차 관문과 최종 판정"의 분업이다.

---

## 9. 주의할 사항과 정리

### 1) 401과 403의 기준은 "인증 여부"다

토큰이 있지만 무효(만료·위조)인 경우는 403이 아니라 401이다. 무효한 토큰은 인증이 안 된 것과 같기 때문이다. 403은 오직 "유효한 토큰으로 인증됐지만 그 역할로는 안 되는" 경우에만 쓴다. 프론트엔드가 401에 "재로그인", 403에 "권한 없음 안내"로 반응하려면 이 기준이 흔들리면 안 된다.

### 2) 핸들러 두 층을 섞지 않는다

필터 층의 핸들러(엔트리포인트, `AccessDeniedHandler`)는 MVC 바깥이라 `ObjectMapper`로 직접 쓰고, 컨트롤러 층(`@RestControllerAdvice`)은 객체를 `return`한다. 둘의 코드 모양이 다른 것은 실수가 아니라 동작하는 층이 다르기 때문이다. `@RestControllerAdvice`에서 `AuthenticationException` 전체를 잡으려 하면 필터 층에서 생긴 예외는 어차피 거기 닿지 않는다. 각 층의 예외는 각 층에서 잡는다.

### 3) 메시지는 사용자용으로, 세부 사정은 로그로

`ErrorResponse.message`는 화면에 그대로 올라간다. "토큰 서명 검증 실패: SignatureException"처럼 내부 사정을 적으면 공격자에게 힌트가 되고 사용자에게는 의미가 없다. 디버깅에 필요한 내용은 핸들러 안에서 로그로 남기고, 응답에는 사용자가 할 수 있는 행동("로그인하세요")이 담긴 문장만 넣는다.

### 4) Jackson 3 패키지

Spring Boot 4 프로젝트에서 `ObjectMapper`는 `tools.jackson.databind.ObjectMapper`다. `com.fasterxml.jackson.databind`로 import하면 컴파일 오류가 난다. 인터넷 예제를 복사할 때 가장 먼저 걸리는 지점이다.

### 5) 정리

| 상황 | 상태 | 번역하는 곳 | 메시지 |
|---|---|---|---|
| 토큰 없음 | 401 | `JsonAuthenticationEntryPoint` | 로그인이 필요합니다. |
| 토큰 무효(만료·위조·리프레시 토큰) | 401 | `JsonAuthenticationEntryPoint` | 토큰이 유효하지 않거나 만료되었습니다. |
| 비밀번호 불일치 | 401 | `GlobalExceptionHandler` | 아이디 또는 비밀번호가 올바르지 않습니다. |
| 리프레시 토큰 무효 | 401 | `GlobalExceptionHandler` | (예외 메시지 그대로) |
| 권한 부족 | 403 | `JsonAccessDeniedHandler` | 이 기능을 사용할 권한이 없습니다. |

네 경우 모두 같은 `ErrorResponse` 형식이고, 프론트는 `readErrorMessage()` 하나로 읽는다.

### 6) 이번 노트에서 추가·수정된 파일

**백엔드 (추가)**

- `dto/common/ErrorResponse.java`
- `security/handler/JsonAuthenticationEntryPoint.java`
- `security/handler/JsonAccessDeniedHandler.java`
- `controller/GlobalExceptionHandler.java`

**백엔드 (수정)**

- `config/SecurityConfig.java` — 핸들러 주입, `exceptionHandling()`
- `controller/AuthController.java` — 지역 `@ExceptionHandler` 제거

**프론트엔드 (수정)**

- `app/_lib/auth/backend.ts` — `BackendError`, `readErrorMessage()`
- `app/login/_components/LoginForm/loginAction.ts` — 백엔드 메시지 표시
- `app/admin/_components/BackendCheck/backendCheckApi.ts` — 백엔드 메시지 표시

---

## 마무리

이번 노트로 스프링은 실패를 401(로그인 문제)과 403(권한 문제)으로 정확히 구분하고, 어느 층에서 실패했든 같은 모양의 JSON으로 사유를 알려주게 되었다. 프론트엔드는 더 이상 상태 코드를 보고 문장을 지어내지 않고, 백엔드가 준 문장을 그대로 보여준다.
