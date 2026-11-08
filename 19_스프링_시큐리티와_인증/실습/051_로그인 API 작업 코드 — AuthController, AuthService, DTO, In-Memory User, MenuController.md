---
tags: [스프링시큐리티, JWT, 로그인API, AuthController, AuthService, AuthenticationManager, LoginRequest, LoginResponse, InMemoryUserDetailsManager, MenuController, Postman, 실습]
---

> 🔗 관련 노트: [[050_스프링 부트 JWT 인증 구현 — JJWT 설정, JwtProvider, JwtAuthenticationFilter, SecurityConfig, 로그인 API]] · [[100_JWT 로그인 API — AuthController, AuthService, AuthenticationManager와 토큰을 받는 쪽]] · [[099_인증 방식의 변화와 JWT — 세션에서 토큰으로, SAML·OAuth 2.0·BFF]]

# 로그인 API 작업 코드 — AuthController, AuthService, DTO, In-Memory User, MenuController

로그인 요청을 처리하고 JWT 토큰을 발급하는 `AuthController`와 `AuthService`를 구현한다.

> **첨부 파일 안내**
> - `ncafe-prep-05-login-api.zip`: 이 노트의 내용이 적용되기 **전** 상태의 프로젝트다. 노트를 보면서 직접 실습해 보고 싶을 때 내려받아 압축을 풀어 사용한다.
> - `ncafe-lesson-05-login-api`: 이 노트 전체가 **적용된** 결과다. 완성된 모습을 확인하고 싶을 때 사용한다.

---

## 1. 로그인 요청을 처리하는 컨트롤러와 서비스의 역할

이전까지는 건물의 출입구를 지키는 보안 요원(`JwtAuthenticationFilter`)과 제어실(`SecurityConfig`) 설정을 마쳤다. 보안 요원은 손님이 들고 온 출입증(JWT)을 **검사**만 한다. 그래서 아직 출입증 자체를 **발급**해 주는 창구가 없는 상태다.

손님이 처음 방문했을 때 아이디와 비밀번호를 제출하면, 진짜 회원인지 확인하고 새 출입증을 나눠 주는 전담 창구가 필요하다. 백엔드에서 이 창구 역할을 하는 것이 **로그인 API**다.

```
① 손님의 요청        사용자가 화면에서 아이디/비밀번호를 입력하고 로그인 버튼을 누른다
        │
        ▼
② 창구의 접수        AuthController가 LoginRequest를 받아 AuthService로 전달
        │
        ▼
③ 신원 확인·발행     AuthService가 AuthenticationManager로 아이디/비밀번호를 검증하고,
        │            통과하면 JwtProvider로 새 JWT를 만든다
        ▼
④ 응답 전달          LoginResponse(accessToken, tokenType)에 담아 사용자에게 돌려준다
```

---

## 2. 로그인 DTO와 토큰 응답 객체 만들기

사용자가 서버로 보내는 로그인 정보와, 서버가 사용자에게 돌려줄 토큰 정보를 담을 데이터 상자(DTO) 두 개를 만든다.

### 2-1. LoginRequest — 로그인 요청 데이터 상자

사용자가 보낸 아이디와 비밀번호를 담는다.

경로: `src/main/java/com/ncafe/backend/dto/auth/LoginRequest.java`

```java
package com.ncafe.backend.dto.auth;

import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
public class LoginRequest {
    private String username;
    private String password;
}
```

- JSON → 객체 바인딩에 **기본 생성자**가 필요하므로 `@NoArgsConstructor`를 붙인다.
- `@Data`가 getter/setter를 만들어 준다.

### 2-2. LoginResponse — 토큰 응답 데이터 상자

로그인에 성공했을 때 서버가 사용자에게 돌려줄 토큰을 담는다.

경로: `src/main/java/com/ncafe/backend/dto/auth/LoginResponse.java`

```java
package com.ncafe.backend.dto.auth;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class LoginResponse {
    private String accessToken;
    private String tokenType;
}
```

```java
// AuthService에서 이렇게 만든다
return LoginResponse.builder()
        .accessToken(token)
        .tokenType("Bearer")
        .build();
```

> 원문 바로잡기 — 원문의 `@Data @NoArgsConstructor` + `new LoginResponse(token)`은 단일 인자 생성자가 없어 **컴파일 오류**가 난다. `tokenType`도 비게 된다. 수업 적용본처럼 `@Builder`로 `accessToken`과 `tokenType("Bearer")`를 함께 채운다.

---

## 3. AuthenticationManager를 활용한 AuthService 로그인 로직 작성

아이디와 비밀번호 검증은 직접 DB를 조회해서 일일이 비교해도 되지만, 스프링 시큐리티가 제공하는 `AuthenticationManager`를 쓰면 안전하고 편리하게 검증할 수 있다.

`AuthenticationManager`는 스프링 시큐리티가 인증을 하기 위해 내부적으로 쓰는 인증 관리 객체다. 이 안에는 이미 `UserDetailsService`를 호출해 저장된 사용자의 암호화된 비밀번호와 권한 정보를 조회하는 흐름이 들어 있다. 주입된 `PasswordEncoder`(예: `BCryptPasswordEncoder`)로 사용자가 입력한 평문 비밀번호와 저장된 암호화 비밀번호를 비교하는 것도 이 흐름의 일부다.

비밀번호가 일치해서 인증에 성공하면, 인증된 사용자 정보와 권한 목록을 담은 `Authentication` 객체를 만들어 **돌려준다**. 이 객체를 받아 `JwtProvider`로 토큰을 발급하는 것은 `AuthService`의 일이다.

> 원문 바로잡기 — 원문에는 인증이 완료되면 `AuthenticationManager`가 `JwtProvider`를 호출해 토큰 발급까지 처리한다고 되어 있지만, `AuthenticationManager`는 JWT를 모른다. 인증 객체를 돌려주는 데서 끝이고, 토큰 발급은 `AuthService`가 한다.

### 3-1. AuthenticationManager 빈 등록

이 객체를 쓰려면 `SecurityConfig`에 빈으로 등록하는 코드를 추가하면 된다. (`AuthService`에서 호출하는 부분은 따로 있다.)

경로: `src/main/java/com/ncafe/backend/config/SecurityConfig.java`

```java
@Bean
public AuthenticationManager authenticationManager(
        AuthenticationConfiguration authenticationConfiguration) throws Exception {
    return authenticationConfiguration.getAuthenticationManager();
}
```

> **주의**: 스프링 부트는 `AuthenticationManager`를 자동으로 빈 등록하지 않는다. 이 `@Bean`이 없으면 `AuthService` 생성자 주입 시 `NoSuchBeanDefinitionException`이 난다.

### 3-2. AuthService — 신원 확인 + JWT 발급

이제 로그인 핵심 로직을 담당하는 `AuthService`를 작성한다.

경로: `src/main/java/com/ncafe/backend/service/AuthService.java`

```java
package com.ncafe.backend.service;

import com.ncafe.backend.dto.auth.LoginRequest;
import com.ncafe.backend.dto.auth.LoginResponse;
import com.ncafe.backend.security.jwt.JwtProvider;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

    private final AuthenticationManager authenticationManager;
    private final JwtProvider jwtProvider;

    public AuthService(AuthenticationManager authenticationManager, JwtProvider jwtProvider) {
        this.authenticationManager = authenticationManager;
        this.jwtProvider = jwtProvider;
    }

    public LoginResponse login(LoginRequest request) {
        // 1. 아직 인증되지 않은 토큰 객체
        UsernamePasswordAuthenticationToken authenticationToken =
                new UsernamePasswordAuthenticationToken(request.getUsername(), request.getPassword());

        // 2. AuthenticationManager에게 검증 위임 (UserDetailsService + PasswordEncoder)
        Authentication authentication = authenticationManager.authenticate(authenticationToken);

        // 3. 검증된 인증 객체에서 아이디·권한 추출
        String username = authentication.getName();
        String role = authentication.getAuthorities().stream()
                .findFirst()
                .map(GrantedAuthority::getAuthority)
                .orElse("ROLE_USER");

        // 4. JwtProvider로 Access Token 생성
        String token = jwtProvider.createAccessToken(username, role);

        // 5. 응답 DTO로 반환
        return LoginResponse.builder()
                .accessToken(token)
                .tokenType("Bearer")
                .build();
    }
}
```

| 단계 | 하는 일 |
|---|---|
| 1 | `UsernamePasswordAuthenticationToken(아이디, 비밀번호)` — **미인증** 상태의 그릇 |
| 2 | `authenticate()` — 성공 시 인증 완료 `Authentication`, 실패 시 `BadCredentialsException` |
| 3 | `getName()`, 권한 목록 첫 번째(`ROLE_USER` / `ROLE_ADMIN`) |
| 4 | `jwtProvider.createAccessToken(username, role)` |
| 5 | `LoginResponse` 빌더로 반환 |

```
AuthService
   │ UsernamePasswordAuthenticationToken(아이디, 비밀번호)
   ▼
AuthenticationManager ──▶ DaoAuthenticationProvider
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
     UserDetailsService                PasswordEncoder
     (InMemory / DB 조회)              (BCrypt 비교)
              │
              ▼
     인증 완료 Authentication + GrantedAuthority
              │
              ▼
     JwtProvider.createAccessToken(...) → LoginResponse
```

> 원문 바로잡기 — DTO import는 `com.ncafe.backend.dto.LoginRequest`가 아니라 **`com.ncafe.backend.dto.auth.LoginRequest`** 이다.

> **추가 설명**: 로그인 시점에 `SecurityContextHolder`에 담을 필요는 없다. 다음 요청부터는 `JwtAuthenticationFilter`가 토큰을 보고 매번 홀더를 채운다.

---

## 4. AuthController 구현과 로그인 API 엔드포인트 개방

외부에서 HTTP 요청을 받아 서비스 로직을 호출해 주는 컨트롤러를 작성한다. 요청 경로는 이전 `SecurityConfig`에서 `permitAll()`로 열어 둔 `/api/auth/login`으로 한다.

경로: `src/main/java/com/ncafe/backend/controller/AuthController.java`

```java
package com.ncafe.backend.controller;

import com.ncafe.backend.dto.auth.LoginRequest;
import com.ncafe.backend.dto.auth.LoginResponse;
import com.ncafe.backend.service.AuthService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@RequestBody LoginRequest loginRequest) {
        LoginResponse tokenResponse = authService.login(loginRequest);
        return ResponseEntity.ok(tokenResponse);
    }
}
```

| 부분 | 설명 |
|---|---|
| `@RequestMapping("/api/auth")` | 인증 관련 URL 울타리 |
| `@PostMapping("/login")` | 최종 경로 `POST /api/auth/login` |
| `@RequestBody` | JSON 본문을 `LoginRequest`로 바인딩 |
| 생성자 주입 | 필드 주입 대신 `AuthService`를 생성자로 받음 |

이제 `/api/auth/login`으로 아이디와 비밀번호를 담아 POST 요청을 보내면, 서비스가 신원을 확인한 뒤 JWT를 담은 JSON 응답을 돌려준다.

> **추가 설명**: `ResponseEntity.ok(...)` 없이 `LoginResponse`를 그대로 반환해도 기본 상태 코드는 200이다. 둘 다 결과는 같다.

---

## 5. 임시 사용자(In-Memory User) 설정을 통한 로그인 로직 테스트

사용자 정보를 관리하는 전담 서비스(`UserDetailsService`)나 DB 회원 데이터가 없어도, 테스트용 임시 사용자(In-Memory User)를 스프링 시큐리티 설정에 등록하면 지금까지 작성한 로그인 로직을 그대로 테스트할 수 있다.

권한에 따른 동작을 확인하려면 일반 사용자(`USER`)와 관리자(`ADMIN`)처럼 역할이 다른 사용자를 함께 등록해 두는 것이 유용하다. `SecurityConfig`에 `UserDetailsService` 빈을 임시로 추가하면 `AuthenticationManager`가 이 회원 정보를 참조해 로그인 검증을 수행한다.

### 5-1. PasswordEncoder + 임시 사용자

```java
@Bean
public PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
}

@Bean
public UserDetailsService userDetailsService(PasswordEncoder passwordEncoder) {
    UserDetails user = User.builder()
            .username("newlec")
            .password(passwordEncoder.encode("123"))
            .roles("USER")
            .build();

    UserDetails admin = User.builder()
            .username("admin")
            .password(passwordEncoder.encode("123"))
            .roles("ADMIN")
            .build();

    return new InMemoryUserDetailsManager(user, admin);
}
```

| 계정 | 비밀번호 | 역할 |
|---|---|---|
| `newlec` | `123` | `ROLE_USER` |
| `admin` | `123` | `ROLE_ADMIN` |

- 비밀번호는 반드시 `passwordEncoder.encode(...)`로 넣는다. 평문 `"123"`을 그대로 넣으면 BCrypt 비교가 실패한다.
- `.roles("USER")`는 내부적으로 `ROLE_USER` 권한을 만든다. `hasRole("ADMIN")`은 `ROLE_` 접두사를 자동으로 붙인다.
- `newlec / 123` 또는 `admin / 123`으로 `/api/auth/login`에 POST 요청을 보내면, DB 연결 없이도 권한별로 JWT가 발급되는지 확인할 수 있다.

> 원문 바로잡기 — 원문의 `SecurityConfig` 코드에는 `BCryptPasswordEncoder`의 import가 빠져 있다. `org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder`를 추가해야 컴파일된다(아래 전체 코드에 포함).

### 5-2. 경로별 인가 (관리자 규칙 포함)

```java
.authorizeHttpRequests(auth -> auth
    // 로그인 등 공개 API는 토큰 없이 허용
    .requestMatchers("/api/auth/**", "/error").permitAll()
    // 관리자만 접근
    .requestMatchers("/api/admin/**").hasRole("ADMIN")
    // 그 외는 인증 필요
    .anyRequest().authenticated()
)
```

- `/api/auth/**`를 `permitAll()`로 열지 않으면 로그인 요청 자체가 403이 난다.
- 규칙은 **위에서 처음 맞는 것**만 적용되므로 `anyRequest()`보다 앞에 쓴다.

### 5-3. SecurityConfig 전체 (적용본 기준)

```java
package com.ncafe.backend.config;

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

    public SecurityConfig(JwtProvider jwtProvider) {
        this.jwtProvider = jwtProvider;
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(AbstractHttpConfigurer::disable)
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**", "/error").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .addFilterBefore(
                new JwtAuthenticationFilter(jwtProvider),
                UsernamePasswordAuthenticationFilter.class
            );

        return http.build();
    }

    @Bean
    public AuthenticationManager authenticationManager(
            AuthenticationConfiguration authenticationConfiguration) throws Exception {
        return authenticationConfiguration.getAuthenticationManager();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public UserDetailsService userDetailsService(PasswordEncoder passwordEncoder) {
        UserDetails user = User.builder()
                .username("newlec")
                .password(passwordEncoder.encode("123"))
                .roles("USER")
                .build();

        UserDetails admin = User.builder()
                .username("admin")
                .password(passwordEncoder.encode("123"))
                .roles("ADMIN")
                .build();

        return new InMemoryUserDetailsManager(user, admin);
    }
}
```

---

## 6. 권한을 테스트하기 위한 엔드포인트 컨트롤러 추가하기

발급된 JWT의 권한(Role)에 따라 특정 API의 접근이 제대로 제어되는지 확인하려고 테스트용 엔드포인트를 추가한다. 메뉴 정보를 조회하는 간단한 `MenuController`를 만들어 일반 사용자(`USER`)와 관리자(`ADMIN`)의 접근 권한을 테스트한다.

경로: `src/main/java/com/ncafe/backend/controller/MenuController.java`

```java
package com.ncafe.backend.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api")
public class MenuController {

    // 인증된 사용자면 누구나
    @GetMapping("/menus")
    public ResponseEntity<List<String>> getMenuList() {
        List<String> menus = List.of("아메리카노", "카페라떼", "바닐라라떼");
        return ResponseEntity.ok(menus);
    }

    // ADMIN만 (SecurityConfig의 /api/admin/** → hasRole("ADMIN"))
    @GetMapping("/admin/menus")
    public ResponseEntity<List<String>> getAdminMenuList() {
        List<String> adminMenus = List.of("메뉴 등록", "메뉴 수정", "메뉴 삭제");
        return ResponseEntity.ok(adminMenus);
    }
}
```

| 경로 | 조건 |
|---|---|
| `GET /api/menus` | 로그인해서 유효한 토큰을 받은 사용자라면 권한과 상관없이 접근 가능 (`anyRequest().authenticated()`) |
| `GET /api/admin/menus` | `SecurityConfig` 설정에 의해 `ROLE_ADMIN`만 접근 가능. `USER` 토큰으로 접근하면 권한 부족으로 차단된다 |

> 원문 바로잡기 — 원문 `MenuController`에는 쓰지 않는 `PreAuthorize` import가 있다. 권한 제어는 어노테이션이 아니라 `SecurityConfig`의 `hasRole("ADMIN")`이 하므로 필요 없다.

---

## 7. 인증과 권한 테스트

Postman으로 설정이 잘 적용됐는지 두 가지 시나리오를 확인한다. 먼저 백엔드 프로젝트를 실행한다. VS Code 터미널에서 다음 명령어를 입력하거나, VS Code 확장 모듈 Spring Boot Dashboard로 실행해도 된다.

```bash
./gradlew bootRun
```

Postman 데스크톱 앱을 실행해 로그인한 뒤, 기존 수업에서 쓰던 워크스페이스가 있으면 그것을 선택하고 없으면 다음 순서로 진행한다.

1. **워크스페이스 이동**: 상단 메뉴의 Workspaces에서 사용할 워크스페이스(예: My Workspace)를 선택한다.
2. **새 요청 탭 생성**: 작업 영역 상단의 `+` 버튼으로 새 요청 탭을 연다.
3. **요청 정보 입력**: HTTP 메서드(GET, POST 등)를 고르고 URL 입력창에 API 주소를 입력한다.
4. **요청 헤더 설정**: 하단의 Headers 탭에서 Key에 `Authorization`, Value에 `Bearer <JWT_토큰>`을 추가한다.
5. **요청 전송 및 결과 확인**: Send 버튼을 눌러 하단 응답 창에서 상태 코드와 결과를 확인한다.

### 7-1. 토큰 없이 보호된 API 호출 테스트

- `GET http://localhost:8080/api/admin/menus`
- Headers: `Authorization` 헤더 없이 전송
- 결과: 요청이 거부된다. `anyRequest().authenticated()` 때문에 인증되지 않은 요청이 정상적으로 차단됨을 확인할 수 있다.

> 원문 바로잡기 — 원문은 "401 또는 403"이라고 했지만, 이 프로젝트에는 `AuthenticationEntryPoint`를 따로 설정하지 않았으므로 토큰 없는 요청은 **403 Forbidden**으로 내려온다. 401로 내려주려면 `AuthenticationEntryPoint`를 등록해야 한다.

### 7-2. 유효한 JWT 토큰을 포함하여 요청 테스트

먼저 `POST /api/auth/login`으로 로그인해 Access Token을 발급받는다.

1. **로그인 요청 설정**: HTTP 메서드를 `POST`로 바꾸고 URL에 `http://localhost:8080/api/auth/login`을 입력한다.
2. **요청 본문 작성**: Body 탭 → raw → 오른쪽 드롭다운에서 JSON을 선택한다.
3. **로그인 정보 입력**:

```json
{
    "username": "admin",
    "password": "123"
}
```

4. **토큰 발급 확인**: Send 후 응답 본문에서 `accessToken` 문자열을 복사한다.

```json
{
    "accessToken": "eyJhbGciOiJIUzI1NiJ9...",
    "tokenType": "Bearer"
}
```

`newlec` / `123`으로도 같은 방법으로 발급할 수 있다(권한만 다르다).

발급받은 토큰으로 보호된 API를 호출한다.

1. **테스트할 API 요청 설정**: 메서드를 `GET`으로 바꾸고 URL에 `http://localhost:8080/api/admin/menus`를 입력한다.
2. **요청 헤더 설정**: URL 입력창 아래 Headers 탭을 연다.
3. **인증 토큰 입력**:
   - Key: `Authorization`
   - Value: `Bearer <발급받은_JWT_토큰>` (`Bearer` 뒤에 한 칸을 띄우고 토큰을 붙여 넣는다)
4. **요청 전송 및 결과 확인**: Send를 누른다.

결과는 `admin` 토큰이면 200 OK와 함께 데이터가 정상 반환된다. `JwtAuthenticationFilter`가 헤더에서 토큰을 꺼내 검증하고, `SecurityContext`에 인증 객체를 등록해 접근을 허용한 것이다.

| 토큰 계정 | `/api/menus` | `/api/admin/menus` |
|---|---|---|
| `admin` | 200 | 200 |
| `newlec` | 200 | 403 (권한 부족) |
| 토큰 없음 | 403 | 403 |

> 원문 바로잡기 — 원문 Postman 화면 설명에는 `/admin/menus`로 되어 있는 곳이 있는데, 실제 경로는 `/api` 가 붙은 **`/api/admin/menus`** 이다.

---

## 8. 주의할 사항과 오류 처리

로그인 기능을 구현할 때는 다음 예외 상황과 보안 사항을 염두에 둔다.

### 8-1. 잘못된 로그인 정보에 대한 예외 처리

아이디가 없거나 비밀번호가 틀리면 `authenticationManager.authenticate()`가 `BadCredentialsException`을 던진다. 예외 처리를 따로 하지 않으면 사용자에게 오류 응답이 그대로 전달된다. 전역 예외 처리기(`@RestControllerAdvice`)를 만들어 401 Unauthorized와 "아이디 또는 비밀번호가 올바르지 않습니다" 같은 메시지를 내려주는 것이 바람직하다.

> 원문 바로잡기 — 원문은 처리하지 않으면 500 Internal Server Error가 전달된다고 했지만, 이 프로젝트 설정에서는 `AuthenticationEntryPoint`가 없어서 **403 Forbidden**이 내려온다. 어느 쪽이든 사용자에게 의미가 전달되지 않으므로 직접 처리해야 한다는 결론은 같다.

### 8-2. 비밀번호 평문 저장 금지

`AuthenticationManager`가 비밀번호를 정상적으로 비교하려면 저장된 비밀번호가 `PasswordEncoder`(예: `BCryptPasswordEncoder`)로 암호화되어 있어야 한다. 회원가입 로직을 만들 때도 반드시 암호화해서 저장해야 로그인이 정상 동작한다.

### 8-3. 공개 경로 설정 확인

`SecurityConfig`에 `.requestMatchers("/api/auth/**").permitAll()`이 적용되어 있는지 다시 확인한다. 빠지면 로그인 요청 자체에 토큰이 없다는 이유로 403이 나서 로그인 창구에 접근조차 할 수 없게 된다.

---

## 한눈에 보는 흐름

```
[클라이언트]
   POST /api/auth/login { username, password }
        │
        ▼
[AuthController] ──▶ [AuthService]
                          │ authenticate()
                          ▼
                   [AuthenticationManager]
                          │ UserDetailsService + PasswordEncoder
                          ▼
                   Authentication (username, ROLE_...)
                          │
                          ▼
                   [JwtProvider.createAccessToken]
                          │
                          ▼
                   LoginResponse { accessToken, tokenType: "Bearer" }

이후 요청:
  Authorization: Bearer <accessToken>
        │
        ▼
[JwtAuthenticationFilter] → SecurityContext 등록
        │
        ▼
[SecurityConfig 인가] → /api/menus, /api/admin/menus
```

---

## 마무리

Spring Boot, Spring Security, JWT로 백엔드 인증과 권한 관리의 전 과정을 마쳤다. 필터 설정부터 로그인 API 구현, `AuthenticationManager`를 통한 신원 검증, Postman으로 권한별 접근 테스트까지 이어서, JWT 기반 백엔드 보안의 기초 틀이 완성됐다.

한 걸음 더 나아가고 싶다면 다음 주제를 이어서 공부한다.

| 주제 | 내용 |
|---|---|
| 프론트엔드 서버 연동 시 토큰 관리 | Next.js 같은 SSR 환경에서 발급받은 JWT를 안전하게 보관하고 전달하는 방법. Local Storage(XSS에 취약)와 httpOnly/Secure Cookie(CSRF·CORS 대응 필요)의 장단점을 비교하고, Server Actions 환경에 맞는 운영 전략을 학습한다 |
| DB 기반 `UserDetailsService` | In-Memory User를 걷어내고 DB에서 사용자를 조회하도록 교체 |
| 동적 권한 관리(Dynamic Security) | 코드에 고정된 권한 설정을 넘어, DB와 연동해 사용자 역할이나 자원별 접근 권한을 실시간으로 제어 |
