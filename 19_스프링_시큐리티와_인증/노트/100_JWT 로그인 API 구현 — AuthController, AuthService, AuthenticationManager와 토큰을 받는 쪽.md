---
tags: [스프링시큐리티, JWT, 로그인, AuthenticationManager, UserDetailsService, PasswordEncoder, SecurityContextHolder, DTO, Lombok, Builder, ResponseEntity, 엔드포인트, BFF]
---

> 🔗 관련 노트: [[050_스프링 부트 JWT 인증 구현 — JJWT 설정, JwtProvider, JwtAuthenticationFilter, SecurityConfig, 로그인 API]] · [[099_인증 방식의 변화와 JWT — 세션에서 토큰으로, SAML·OAuth 2.0·BFF]] · [[093_서블릿 필터와 스프링 시큐리티 입문 — 필터 체인, @Bean, UserDetailsService]]

# JWT 로그인 API 구현 — AuthController, AuthService, AuthenticationManager와 토큰을 받는 쪽

지난 시간까지 `JwtProperties`, `JwtProvider`, `JwtAuthenticationFilter`를 만들고 `SecurityConfig`에 필터를 등록했다. 토큰을 **검사하는** 입구는 생겼지만, 토큰을 **발급하는** 곳이 아직 없다. 이번에는 로그인 요청을 받는 컨트롤러와 서비스를 만들어, 아이디/비밀번호를 확인하고 JWT를 돌려주는 API를 완성한다.

---

## 1. 세션·쿠키 방식과 토큰 방식, 언제 무엇을 쓰나

스프링 보안을 다룬다는 것은 두 가지 애플리케이션 형태 중 하나를 고른다는 뜻이다.

| | 세션·쿠키 방식 | 토큰 방식 |
|---|---|---|
| 맞는 구조 | 서버 **한 대**가 인증, 페이지 생성, 리소스 제공을 모두 맡음 | 페이지를 만드는 서버, 리소스(API) 서버, 인증 서버가 **나뉘어** 있음 |
| 인증 상태 | 서버의 세션 저장소에 저장 (Stateful) | 어디에도 저장하지 않고 **사용자가 들고 다님** (Stateless) |
| 이유 | 한 서버 안이라 세션 관리가 쉽고 가장 안전하다 | 서버가 여럿이면 "누가 세션을 관리하나"가 어려워진다 |

"서버가 한 대면 세션, 여러 대면 토큰"이라는 답도 맞지만, 정확히는 **그 서버가 무슨 역할을 하는지**를 봐야 한다. 한 서버가 인증도 하고 페이지도 만들고 리소스도 준다면 세션을 써도 된다. 그런데 페이지를 만드는 쪽(Next.js)과 리소스를 주는 쪽(스프링 부트)이 갈라지면, 둘 사이에서 세션을 공유하기 어렵다. 그래서 "어딘가에 저장하지 말고 그냥 가지고 다니게 하자"는 것이 **무상태(Stateless)** 이고, 그것을 구현하는 수단이 토큰이다.

정확한 코드는 기억이 안 나더라도, **내가 어떤 구조로 무엇을 선택할지**는 머릿속에 분명히 있어야 한다.

---

## 2. 지금까지 만든 것 다시 보기 — 요청이 컨트롤러까지 가는 길

클라이언트가 서버로 요청할 때, 로그인한 적이 있다면 **토큰**을 가져간다. 토큰은 쿠키로도 보낼 수 있고 헤더로도 보낼 수 있지만, 우리 서버는 **헤더로 보내 달라**고 약속했다. 필터의 `resolveToken()`이 `Authorization` 헤더에서 `Bearer ` 뒤의 토큰만 꺼내므로, 이 서버는 쿠키를 아예 보지 않는다.

```
클라이언트 ──Authorization: Bearer <토큰>──▶ [JwtAuthenticationFilter] ─▶ [스프링 시큐리티 필터들] ─▶ 컨트롤러 ─▶ 서비스
                                              ① 토큰을 꺼내 검증              ② 인가(권한) 판단
                                                 SecurityContext에 등록         permitAll / authenticated / hasRole
```

컨트롤러에 닿기 전에 **두 개의 문**을 지난다. 앞의 문은 우리가 만든 JWT 필터(문지기)이고, 뒤의 문은 **인가**를 담당하는 스프링 시큐리티의 필터다.

**왜 JWT 필터가 필요한가**

스프링 시큐리티는 인가를 판단할 때 `SecurityContextHolder`에 들어 있는 `Authentication` 객체를 본다.

```
SecurityContextHolder
 └─ SecurityContext
     └─ Authentication          ← 사용자 아이디(principal), 비밀번호(credentials)
         └─ GrantedAuthority들  ← 역할(ROLE_USER, ROLE_ADMIN ...)
```

세션 방식이었다면 이 객체를 채우는 일을 스프링 시큐리티가 **알아서** 했다. 그런데 JWT는 약간 특수한 모양으로 들어오므로, 토큰을 꺼내서 스프링 시큐리티가 이해할 수 있는 `Authentication` 객체로 만들어 홀더에 담아 주는 일을 **우리가 직접** 해야 한다. 그것이 `JwtAuthenticationFilter`의 역할이다. 그래서 필터 순서가 중요하다. 우리 필터가 먼저 사용자 정보를 담아야 뒤의 보안 필터가 그것을 보고 판단한다.

**Postman으로 헤더에 토큰 넣기**

어떤 요청이든 헤더에 값을 심을 수 있다. 직접 `Headers` 탭에 `Authorization: Bearer <토큰>`을 써도 되고, Postman의 **Authorization 탭**에서 타입을 **Bearer Token**으로 고르고 토큰만 붙여 넣어도 같은 헤더가 만들어진다. 로컬 서버를 호출하려면 웹 버전이 아니라 설치형 Postman(또는 데스크톱 에이전트)이 필요하다.

> 원문 바로잡기 — 수업 중 헤더 이름을 "authentication"이라고 했지만, 표준 헤더 이름은 **`Authorization`** 이다. 필터 코드도 `request.getHeader("Authorization")`으로 꺼낸다. 값은 `Bearer` 한 칸 띄고 토큰이다.

---

## 3. 엔드포인트와 AuthController

**엔드포인트란**

엔드포인트(endpoint)는 클라이언트가 **맞닿는 지점**, 서비스의 접점이다. 일반적으로 URL을 말하고, 지금 만드는 엔드포인트는 **컨트롤러의 URL**이다. 사용자가 로그인할 URL이 필요하므로 컨트롤러를 만든다.

**이름은 `LoginController`가 아니라 `AuthController`**

예전에는 `LoginController`라고 많이 했다. 그런데 "로그인"은 행위 이름이라, 그 컨트롤러에는 로그인만 들어가야 할 것 같다. 로그인과 로그아웃(나중에는 토큰 재발급까지)을 함께 담을 울타리는 **인증(auth)** 이 맞으므로 `AuthController`로 짓는다. URL도 `/api/auth`로 둔다.

**POST만 만든다**

로그인은 아이디/비밀번호를 받아서 처리하는 것이므로 `@PostMapping("/login")`만 있으면 된다. 페이지를 만들던 시절과 달리 API 서버에는 "로그인 화면을 달라"는 GET이 필요 없다. 줄 것이 없기 때문이다.

```java
package com.ncafe.backend.controller;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.ncafe.backend.dto.auth.LoginRequest;
import com.ncafe.backend.dto.auth.LoginResponse;
import com.ncafe.backend.service.AuthService;

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
}
```

| 부분 | 설명 |
|---|---|
| 매개변수 `LoginRequest` | 예전처럼 `username`, `password`를 낱개로 받을 수도 있지만, 최종 버전은 **DTO**로 받는다 |
| `@RequestBody` | 클라이언트가 JSON을 **본문에 통째로** 보내므로, 그 본문을 통째로 받아 객체에 채워 넣으라는 뜻이다. 이것이 없으면 값이 비어 있다 |
| `AuthService service` | 서비스는 **필드 주입 대신 생성자 주입**으로 받는다 |
| 반환 `LoginResponse` | 토큰을 담은 응답이므로 변수 이름은 `tokenResponse`로 둔다 |

**DTO 이름에 `Dto`를 붙일까 뺄까**

`LoginRequestDto`로 할지 `LoginRequest`로 할지가 갈린다. "리포지토리는 `OOORepository`, 서비스는 `OOOService`, 컨트롤러는 `OOOController`처럼 붙이는데 DTO만 빼면 일관성이 없다"는 반론이 나올 수 있다.

기본값(디폴트)은 **"안 써도 되면 안 쓰는 것이 좋다"** 다. `this`도 세터처럼 매개변수와 필드 이름이 겹칠 때만 쓰고 나머지는 빼는 것과 같다. 서비스, 컨트롤러, 리포지토리에 접미사를 붙이는 이유는 **빼면 엔티티 이름과 겹쳐서** 뺄 수 없기 때문이다(`Menu`와 `MenuService`). 그래서 엔티티 패키지에서는 `MenuEntity`가 아니라 그냥 `Menu`라고 쓴다. `LoginRequest`는 `Dto`를 빼도 이상하지 않으므로 **뺀다**. 일관성의 기준은 "빼는 것"이고, 붙이는 쪽이 예외다.

이런 논쟁에서는 **내 머릿속에 보편적인 기본값이 있어야** 휘둘리지 않는다. 논쟁하다 지면 오히려 좋다. 내 논리의 빈틈과 더 좋은 방법을 찾은 것이기 때문이다.

**`ResponseEntity`로 감쌀까**

API는 POST든 GET이든 결과가 있으면 돌려줘야 하므로 응답도 DTO(`LoginResponse`)다. 상태 코드를 함께 담으려고 `ResponseEntity.ok(결과)`로 감쌀 수도 있다. 하지만 `ok`는 200이고, **감싸지 않아도 기본으로 200**이 나간다. 실패하는 경우를 걱정할 수 있지만, 로그인 중 예외가 나면 이 `return`은 실행되지 않고 **예외 처리 흐름이 따로 응답**을 만든다. 데이터베이스의 기본값이 있는 컬럼을 INSERT 때 굳이 채우지 않는 것처럼, 기본값으로 충분하면 쓰지 않는다. 결론은 **감싸지 않고 `LoginResponse`를 그대로 반환**한다.

> **추가 설명 — `ResponseEntity`가 필요한 경우**: 200이 아닌 성공 코드(생성 `201 Created`, 내용 없음 `204 No Content`)를 주거나, 응답 헤더(`Location`, `Set-Cookie` 등)를 직접 붙여야 할 때는 `ResponseEntity`를 쓴다. 그런 예외적인 메서드에만 쓰면 된다.

> **추가 설명 — 비밀번호가 틀리면 어떤 응답이 나가나**: `authenticate()`가 실패하면 `BadCredentialsException`이 던져지고, 이 예외는 스프링 시큐리티의 예외 처리 필터가 받아서 **인증 실패 응답**을 만든다. 지금처럼 `AuthenticationEntryPoint`를 따로 정하지 않았다면 이 응답은 **403**이다. "아이디/비밀번호가 틀림(401)"을 프론트에 분명히 알리려면, 엔트리 포인트를 등록하거나 `@RestControllerAdvice`에서 `AuthenticationException`을 잡아 401 JSON을 돌려준다.

---

## 4. LoginRequest, LoginResponse — 롬복과 빌더

DTO는 많아질 것이므로 `dto/auth` 폴더를 만들어 그 안에 둔다.

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

롬복 라이브러리가 프로젝트에 없으면 추가한다(`compileOnly`와 `annotationProcessor` 두 줄).

**tokenType은 왜 있나**

헤더에 `Authorization: Bearer <토큰>`처럼 쓸 때 앞의 `Bearer`가 **토큰의 종류(타입)** 다. 우리가 쓰는 것은 Bearer뿐이라 사실 토큰만 줘도 되지만, 나중에 다른 타입을 쓸 수도 있으니 **옵션을 열어 두는** 의미로 응답에 함께 준다. 클라이언트는 `tokenType + " " + accessToken`을 그대로 헤더에 넣으면 된다.

**빌더 패턴**

`@Builder`를 붙이면 `new`와 세터 대신 **속성을 점(.)으로 이어 붙여** 객체를 만들 수 있다. 원하는 속성만 골라 채울 수 있어서, 매개변수 조합마다 생성자를 오버로드하지 않아도 된다. 설정 코드(`Jwts.builder()`, `User.builder()`)에서도 같은 방식을 이미 봤다.

```java
LoginResponse response = LoginResponse.builder()
        .accessToken(token)
        .tokenType("Bearer")
        .build();        // 여기서 객체가 만들어진다
```

만든 객체를 변수에 담아 써도 되고, 변수 없이 바로 `return`해도 된다.

> 원문 바로잡기 — 수업 중 "롬복이 하는 일은 자바 파일을 다시 만드는 것"이라고 했지만, 롬복은 `.java` 소스 파일을 새로 만들지 않는다. **컴파일하는 도중에** 코드 구조(AST)에 빌더, 게터, 세터를 끼워 넣어서, 결과물인 **`.class` 파일**에 그 코드가 들어간다. `build/classes/java/main/.../LoginResponse.class`를 IDE에서 열면(디컴파일) `LoginResponseBuilder`라는 안쪽 클래스가 생긴 것을 볼 수 있다.

---

## 5. AuthService — 인증은 AuthenticationManager에게 맡긴다

로그인 요청을 받은 컨트롤러는 직접 처리하지 않고 서비스에 넘긴다. 서비스 이름은 그냥 `AuthService`다. 인증이 **주인공**인 서비스라 특별한 수식어가 필요 없다.

> **추가 설명 — 인터페이스는 생략했다**: 정석은 `AuthService` 인터페이스와 구현체를 나누는 것이지만, 수업에서는 번거로워 생략했다. `@Service`를 빠뜨리면 IoC 컨테이너에 등록되지 않아 컨트롤러 주입이 실패하니 주의한다.

```java
package com.ncafe.backend.service;

import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.stereotype.Service;

import com.ncafe.backend.dto.auth.LoginRequest;
import com.ncafe.backend.dto.auth.LoginResponse;
import com.ncafe.backend.security.jwt.JwtProvider;

@Service
public class AuthService {

    private AuthenticationManager authenticationManager;
    private JwtProvider jwtProvider;

    public AuthService(AuthenticationManager authenticationManager, JwtProvider jwtProvider){
        this.authenticationManager = authenticationManager;
        this.jwtProvider = jwtProvider;
    }

    public LoginResponse login(LoginRequest loginRequest){

        UsernamePasswordAuthenticationToken authenticationToken
            = new UsernamePasswordAuthenticationToken(loginRequest.getUsername(), loginRequest.getPassword());

        Authentication authenticate = authenticationManager.authenticate(authenticationToken);

        String username = authenticate.getName();
        String role = authenticate.getAuthorities().stream()
                        .findFirst()
                        .map(GrantedAuthority::getAuthority)
                        .orElse("ROLE_USER");

        // authentication 정보를 JWT 페이로드에 담아서 리턴
        String token = jwtProvider.createAccessToken(username, role);

        return LoginResponse.builder()
                .accessToken(token)
                .tokenType("Bearer")
                .build();
    }
}
```

**왜 직접 비교하지 않고 매니저에게 맡기나**

아이디/비밀번호가 맞는지 확인하는 과정은 스프링 시큐리티 안에 **이미 구현되어 있다**. 그 일을 하는 것이 `AuthenticationManager`다. 우리는 `UsernamePasswordAuthenticationToken`(아이디, 비밀번호를 담는 그릇)을 채워서 넘기기만 하면 된다. 인증을 전부 우리가 할 거라면 스프링 보안을 쓸 이유가 없다. 스프링 보안이 만든 인증 흐름을 쓰려고 쓰는 것이다.

| 줄 | 하는 일 |
|---|---|
| `new UsernamePasswordAuthenticationToken(아이디, 비밀번호)` | 2인자 생성자 → **아직 인증 전** 상태의 그릇 |
| `authenticationManager.authenticate(...)` | 검증에 성공하면 **인증 완료된** `Authentication`을 돌려준다. 실패하면 예외 |
| `authenticate.getName()` | 인증된 사용자 아이디. 넘긴 아이디와 같지만, 검증을 거친 쪽에서 꺼낸다 |
| `getAuthorities().stream().findFirst()...` | 권한 목록(컬렉션)에서 첫 번째 권한 이름(`ROLE_USER` 등)을 꺼내고, 없으면 기본값 `ROLE_USER` |
| `jwtProvider.createAccessToken(username, role)` | 이미 만든 도구로 JWT 발급 |
| `LoginResponse.builder()...build()` | 토큰과 타입 `"Bearer"`를 담아 반환 |

스트림이 익숙하지 않으면 `getAuthorities().iterator().next().getAuthority()`처럼 첫 번째를 꺼내도 된다. 다만 비어 있을 때의 처리를 따로 써야 해서 스트림 쪽이 더 간단하다.

**AuthenticationManager 안에서 일어나는 일**

```
AuthService
   │ UsernamePasswordAuthenticationToken(아이디, 비밀번호)
   ▼
AuthenticationManager ──"이 방식(아이디/비밀번호)을 처리할 담당자는?"──▶ AuthenticationProvider (DaoAuthenticationProvider)
                                                                         │
                                         ┌───────────────────────────────┤
                                         ▼                               ▼
                               UserDetailsService                 PasswordEncoder
                          (DB, 메모리, JDBC에서 사용자 조회)    (입력 비밀번호 vs 저장된 해시 비교)
                                         │
                                         ▼
                      인증 완료된 Authentication + GrantedAuthority(역할) 반환
```

매니저는 먼저 인증 방식(폼 로그인, 아이디/비밀번호, 구글 같은 OAuth 등)에 맞는 **담당자(프로바이더)** 를 찾는다. 아이디/비밀번호 방식이면, 실제 사용자 정보를 `UserDetailsService`에게 받아 오고 `PasswordEncoder`로 비밀번호를 비교한다. 맞으면 역할 정보를 담은 인증 객체를 돌려준다.

> 원문 바로잡기 — 수업에서는 "사용자 정보와 입력값을 비교하는 역할을 Authentication 객체가 한다"고 했다. 비교를 하는 것은 **`AuthenticationProvider`**(아이디/비밀번호 방식에서는 `DaoAuthenticationProvider`)이고, `Authentication`은 아이디, 비밀번호, 권한을 담는 **그릇**이다.

> 원문 바로잡기 — 수업 중 코드 주석과 설명에 "인증되면 `SecurityContextHolder`에 담긴다"는 내용이 있었다. **`authenticate()`는 인증 객체를 돌려줄 뿐, 홀더에 담지 않는다.** 홀더에 담는 것은 그것을 호출한 쪽의 일이다. 세션 방식에서는 로그인 필터가 담고 세션에 저장한다. 우리 로그인 API는 **홀더에 담을 필요가 없다**. 결과를 JWT로 만들어 돌려주면 끝이고, 다음 요청부터는 `JwtAuthenticationFilter`가 토큰을 보고 매번 홀더를 채운다.

**꼭 매니저를 써야 하나**

아니다. 귀찮으면 리포지토리로 사용자를 꺼내 `passwordEncoder.matches()`로 직접 비교하고, 맞으면 역할을 꺼내 JWT를 만들어 반환해도 된다. 매니저를 쓰면 계정 잠김, 비활성 계정 확인 같은 스프링 시큐리티의 인증 규칙을 그대로 따라가고, 나중에 인증 방식을 늘리기 쉽다는 장점이 있다.

> **추가 설명 — 역할이 여러 개면 첫 번째만 들어간다**: 아래 `admin`처럼 `USER`, `ADMIN` 두 역할을 가진 사용자도 `findFirst()`로 **하나만** 토큰에 넣는다. `User`는 권한을 이름순으로 정렬해 보관하므로 `ROLE_ADMIN`이 먼저 나와서 지금 테스트에서는 문제가 없지만, 순서에 기대는 코드다. 이 토큰으로는 `hasRole("USER")` 경로를 통과하지 못한다. 역할이 여럿일 수 있다면 `roles: ["ROLE_USER", "ROLE_ADMIN"]`처럼 **목록**으로 클레임에 넣고, 필터에서도 목록으로 권한을 만드는 것이 안전하다.

> **추가 설명 — 필드에 `final`을 붙인다**: `AuthService`의 두 필드는 생성자에서 한 번만 들어오므로 `private final`로 두는 것이 좋다. 실수로 바꾸는 것을 막고, 생성자 주입이라는 의도도 분명해진다.

---

## 6. UserDetailsService와 PasswordEncoder 등록

매니저가 인증하려면 **실제 사용자 정보**를 줄 `UserDetailsService`가 있어야 한다. 아이디/비밀번호만 받아서는 비교할 대상이 없기 때문이다. 데이터베이스 연동은 지난번에 다뤘으므로, 이번에는 **메모리**에 사용자를 만들어 둔다. `SecurityConfig`에 빈 두 개를 추가한다.

```java
@Bean
public PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
}

@Bean
public UserDetailsService userDetailsService(PasswordEncoder passwordEncoder){

    UserDetails user = User.builder()
                        .username("jykim")
                        .password(passwordEncoder.encode("123"))
                        .roles("USER")
                        .build();

    UserDetails admin = User.builder()
                        .username("admin")
                        .password(passwordEncoder.encode("123"))
                        .roles("USER", "ADMIN")
                        .build();

    return new InMemoryUserDetailsManager(user, admin);
}
```

| 부분 | 설명 |
|---|---|
| `PasswordEncoder` 빈 | 저장된 비밀번호는 반드시 **인코딩(해시)** 되어 있어야 한다. 단방향 해시는 예전엔 MD5 등을 썼지만 지금은 **BCrypt**가 대세다. 여기서만 쓸 거면 직접 `new` 해도 되지만, 스프링 시큐리티의 다른 로직도 쓰도록 **IoC에 담는다** |
| 메서드 매개변수 `PasswordEncoder` | `@Bean` 메서드는 매개변수만 선언하면 IoC에서 **주입**받는다 |
| `.roles("USER")` | 자동으로 `ROLE_` 접두사가 붙어 `ROLE_USER` 권한이 된다. 그래서 토큰에도 `ROLE_USER`가 들어가고, 필터가 그대로 권한으로 만들면 `hasRole("ADMIN")`과 맞물린다 |
| `admin`의 역할 두 개 | 관리자는 관리자 역할도 하지만 일반 사용자 역할도 하므로 둘 다 준다 |
| `InMemoryUserDetailsManager` | 메모리에 사용자를 들고 있는 `UserDetailsService` 구현체. 수업용이다 |

`UserDetails`가 기본으로 가진 정보는 아이디, 비밀번호, 역할 정도다. 컨트롤러에서 이메일, 닉네임처럼 더 많은 사용자 정보를 쓰고 싶다면 **커스텀 `UserDetails`** 를 만든다. 현장에서는 이 메모리 방식을 빼고, 데이터베이스를 조회하는 **커스텀 `UserDetailsService`를 별도 서비스 클래스**로 만들어 쓰는 경우가 많다.

컨트롤러에서 현재 로그인한 사용자가 필요하면, 매개변수에 `Authentication authentication`을 선언하고 `authentication.getName()`으로 아이디를 꺼낸다(`@AuthenticationPrincipal`로 받는 방법도 있다).

> **추가 설명 — `AuthenticationManager`는 빈으로 직접 꺼내 줘야 한다**: 스프링 부트는 `AuthenticationManager`를 **빈으로 등록해 주지 않는다**. 그래서 `AuthService`가 생성자로 받으려 하면 서버 시작 시 `NoSuchBeanDefinitionException`이 난다. 스프링 시큐리티가 내부에 만들어 둔 매니저를 꺼내 빈으로 등록한다. 이 매니저는 위에서 등록한 `UserDetailsService`와 `PasswordEncoder` 빈을 자동으로 연결해 쓴다.
>
> ```java
> @Bean
> public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
>     return config.getAuthenticationManager();
> }
> ```

> **추가 설명 — 공개 경로에 `/error`를 함께 연다**: 코드 정리본의 `SecurityConfig`는 `.requestMatchers("/api/auth/**", "/error").permitAll()`로 `/error`도 열어 두었다. 이것이 막혀 있으면 서버 안에서 난 에러가 원래의 400, 500 대신 403으로 가려진다.

---

## 7. 세션 방식이었다면 — JWT 필터를 끼운 이유 다시 보기

같은 내용을 세션 방식의 흐름과 비교하면 더 분명해진다.

```
[세션 방식]
요청 + 쿠키(JSESSIONID) ─▶ 스프링 시큐리티 필터
                           │ 세션 저장소에서 SID로 사용자 조회
                           ├─ 있음 → SecurityContextHolder에 자동으로 담김
                           └─ 없음 → 인증 정보 없음
                           ▼
                         매처 확인 (permitAll? 권한 필요?)
                           ├─ permitAll → 통과
                           ├─ 권한 있음 → 통과
                           └─ 권한 없음 → 403 (페이지 시절엔 로그인 페이지로 리다이렉트)

[JWT 방식]
요청 + Authorization 헤더 ─▶ JwtAuthenticationFilter ─▶ 스프링 시큐리티 필터 (매처 확인은 같다)
                             토큰 검증 후 SecurityContextHolder에 "직접" 담음
```

세션에 담는 방식을 쓰면 홀더를 채우는 일이 **저절로** 일어난다. 그런데 우리는 세션을 쓰지 않는다. 세션을 쓰지 않으면 세션 ID 쿠키(`JSESSIONID`)도 아예 만들어지지 않는다. 이 쿠키가 있다는 것 자체가 "세션을 쓰고 있다"는 뜻이다. 다만 세션을 완전히 금지한 것은 아니고, 인증이 아닌 다른 용도로는 쓸 수 있다.

그래서 기존 필터 **앞에** JWT 필터를 둬서, 토큰에서 정보를 꺼내 홀더에 담아 주는 **수작업**을 한다. 그래야 뒤의 매니저와 보안 필터가 정상 흐름을 탄다.

> **수업 문답 — "그럼 세션 쓰면 되잖아요?"**: 세션이 가장 좋고 가장 안전하다. 하지만 지금은 서버가 둘(Next.js, 스프링 부트)이라 "어느 서버의 세션에 저장할 건가, 두 서버가 인증 정보를 어떻게 공유할 건가"가 문제가 된다. 방법은 있지만 그것이 올바른 방법인지 따져 봐야 하고, 그래서 토큰을 쓴다.

**로그인 요청은 어떻게 통과하나**

로그인하러 오는 순간에는 당연히 인증 정보가 **없다**. 홀더도 비어 있다. 그래서 `/api/auth/**`는 반드시 `permitAll()`로 열어야 한다. 인증 없이 통과한 요청이 `AuthService`에서 아이디/비밀번호를 검증받고, **인증 상태(토큰)를 받아 가는** 것이다. 받아 간 토큰은 다음 요청부터 통과 쿠폰처럼 쓰인다.

---

## 8. 토큰은 누가 받나 — 브라우저 vs Next.js 서버

로그인 API가 토큰을 돌려줄 때, 그것을 받는 클라이언트는 둘 중 누구일까?

1. 브라우저
2. Next.js 서버

다시 말해 **토큰을 브라우저에 저장할지, 프론트엔드 서버에 저장할지**를 묻는 것이다. 받는 쪽이 저장하기 때문이다. 전통적으로 프론트엔드를 해 온 사람들은 브라우저에 저장하는 쪽을 선호하지만, 토큰이 외부로 노출되는 것은 바람직하지 않다. 쌤의 선택은 **2번**이다.

```
 브라우저                       Next.js 서버 (프론트엔드 서버)              스프링 부트 (백엔드 서버)
    │ ① GET /login  ───────────▶ 로그인 페이지 반환
    │ ② POST 아이디/비밀번호 ───▶  ③ POST /api/auth/login ──────────────────▶ 검증, JWT 발급
    │                              ④ 응답 본문으로 토큰 받음 ◀──────────────────┘
    │                              ⑤ 토큰 보관: 서버 세션에 저장 (또는 쿠키로 브라우저에)
    │ ⑥ 세션 ID(또는 쿠키) ◀───────┘
    │ ⑦ 이후 요청 ─────────────▶  ⑧ 보관한 토큰을 Authorization 헤더에 붙여 ─▶ API 호출
```

브라우저가 스프링 부트에 **직접** 로그인하게 하지 않고, Next.js 서버를 거치게 한다. 스프링 부트는 토큰을 응답 **본문**으로 돌려주므로 Next.js 서버가 받는다. Next.js는 받은 토큰을 다음 두 방식 중 하나로 다룬다.

| 방식 | 내용 |
|---|---|
| 서버 세션에 저장 | 토큰은 Next.js 서버에 두고, 브라우저에는 세션 아이디만 준다. 브라우저는 토큰을 들고 다니지 않는다 |
| 쿠키로 공유 | 보안상 조금 양보해서, Next.js가 토큰을 쿠키에 담아 브라우저로 보낸다. 그러면 브라우저와 Next.js 서버가 같은 토큰을 안다 |

**쿠키는 브라우저만 관리한다**

스프링 부트가 Next.js 서버에 토큰을 돌려줄 때는 `Set-Cookie`가 아니라 **응답 본문**으로 줬다. 서버끼리의 요청에서 "이 값을 쿠키로 저장해라"라고 하는 것은 의미가 없다. 쿠키를 저장하고 자동으로 보내는 것은 **브라우저만** 할 수 있는 일이다. 그래서 쿠키 설정은 Next.js가 **브라우저에게** 응답할 때만 할 수 있다.

어떤 식으로 할지는 여러 방법이 있지만, 중간에 프론트엔드 서버가 개입하면 클라이언트를 더 안전하게 만들 여지가 생긴다. 이 구조가 BFF(Backend For Frontend)다.

> **추가 설명 — 쿠키로 공유한다면 속성을 꼭 단다**: 토큰을 쿠키에 담아 브라우저로 보낸다면 `HttpOnly`(자바스크립트로 못 읽게 해서 XSS로 토큰을 훔치지 못하게), `Secure`(HTTPS에서만 전송), `SameSite=Lax` 또는 `Strict`(다른 사이트에서 보낸 요청에는 쿠키가 따라가지 않게 해서 CSRF 방어)를 붙인다. 토큰이 다시 쿠키로 자동 전송되므로 CSRF 대비가 다시 필요해진다는 점도 기억한다.

---

## 9. 테스트용 MenuController

로그인과 권한이 제대로 동작하는지 확인하려면 호출해 볼 엔드포인트가 필요하다. 테스트용 메뉴 컨트롤러를 만든다. `@RequestMapping`은 `/api`까지만 두고, 메서드마다 나머지 경로를 붙인다.

```java
package com.ncafe.backend.controller;

import java.util.List;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class MenuController {

    @GetMapping("/menus")
    public List<String> getMenuList(){
        return List.of("아메리카노", "카페라떼", "바닐라라떼");
    }

    @GetMapping("/admin/menus")
    public List<String> getAdminMenuList(){
        return null;
    }
}
```

`SecurityConfig`의 규칙과 맞춰 보면 다음과 같다.

| 경로 | 규칙 | 누가 들어가나 |
|---|---|---|
| `/api/auth/**` | `permitAll()` | 아무나 (로그인) |
| `/api/admin/**` | `hasRole("ADMIN")` | 관리자만 |
| 그 외 (`/api/menus` 등) | `anyRequest().authenticated()` | 로그인한 사용자 (유효한 토큰) |

URL 규칙끼리 경로가 **겹치지 않게** 잘 관리하는 것이 중요하다.

> 원문 바로잡기 — 수업 중 `List.of`를 "스트림 API에 추가된 것"이라고 했지만, `List.of(...)`는 **자바 9**에 추가된 컬렉션 팩토리 메서드이고 스트림이 아니라 **불변 리스트**(`List`)를 만든다. 만든 뒤에는 `add`, `remove`를 할 수 없다.

> **추가 설명 — Postman으로 확인하는 순서**:
>
> | 요청 | 기대 결과 |
> |---|---|
> | `POST /api/auth/login`, 본문(raw, JSON) `{"username":"jykim","password":"123"}` | 200, `{"accessToken":"eyJ...","tokenType":"Bearer"}` |
> | 비밀번호를 틀리게 해서 로그인 | 거절 (엔트리 포인트가 없으면 403) |
> | `GET /api/menus`, 토큰 없이 | 거절 (403) |
> | `GET /api/menus`, Authorization 탭에 jykim 토큰 | 200, `["아메리카노","카페라떼","바닐라라떼"]` |
> | `GET /api/admin/menus`, jykim 토큰 | 403 (ADMIN 아님) |
> | `GET /api/admin/menus`, admin 토큰 | 200 (지금은 `null`을 반환하므로 본문이 비어 있음) |
>
> 발급받은 토큰을 jwt.io에 붙여 넣으면 페이로드에 `"sub": "jykim"`, `"role": "ROLE_USER"`가 보인다.

---

## 정리

| 구분 | 내용 |
|---|---|
| 세션 vs 토큰 | 서버 한 대가 인증, 페이지, 리소스를 다 맡으면 세션. 역할이 나뉘면 무상태 토큰 |
| 요청 흐름 | 헤더의 토큰 → `JwtAuthenticationFilter`(홀더에 직접 담기) → 시큐리티 인가 필터 → 컨트롤러 |
| `AuthController` | `POST /api/auth/login`, `@RequestBody LoginRequest`, `LoginResponse` 그대로 반환 (200은 기본값) |
| 이름 짓기 기본값 | 안 써도 되면 안 쓴다. `Dto` 접미사, `ResponseEntity` 모두 생략 |
| DTO | `LoginRequest`(username, password), `LoginResponse`(accessToken, tokenType="Bearer"), 롬복 `@Builder` |
| `AuthService` | `AuthenticationManager.authenticate()`로 검증 → 첫 권한을 role로 → `createAccessToken()` |
| 매니저 내부 | 프로바이더가 `UserDetailsService`로 사용자 조회, `PasswordEncoder`(BCrypt)로 비교 |
| 필요한 빈 | `PasswordEncoder`, `UserDetailsService`(수업은 메모리), `AuthenticationManager`(직접 꺼내 등록) |
| 토큰을 받는 쪽 | 브라우저가 아니라 **Next.js 서버**. 세션에 보관하거나 보안 속성을 단 쿠키로 공유 (BFF) |
| 테스트 | `/api/menus`(로그인 사용자), `/api/admin/menus`(ADMIN) |

남은 일은 프론트엔드(Next.js)와 연결하는 것으로, 실습 노트로 이어진다.
