---
tags: [RefreshToken, AccessToken, JWT, Next.js, proxy, HttpOnly, BFF, AuthService, RefreshTokenStore, 실습]
---

> 🔗 관련 노트: [[052_Next.js 쿠키 기반 인증과 미들웨어 권한 제어 코드]] · [[050_스프링 부트 JWT 인증 구현 — JJWT 설정, JwtProvider, JwtAuthenticationFilter, SecurityConfig, 로그인 API]] · [[051_로그인 API 작업 코드 — AuthController, AuthService, DTO, In-Memory User, MenuController]] · [[100_JWT 로그인 API — AuthController, AuthService, AuthenticationManager와 토큰을 받는 쪽]]

# Refresh Token으로 조용히 갱신하기 — 재발급 API, RefreshTokenStore, proxy 문지기

> **첨부 파일 안내**
> - `ncafe-prep-07-refresh-token.zip`: 현재 노트의 내용이 적용되기 **전** 상태의 프로젝트 파일이다. 이 노트를 보면서 실습해보고 싶은 사람은 그 파일을 다운로드 한 후 압축을 해제해서 사용하길 바란다.
> - `ncafe-lesson-07-refresh-token.zip`: 이 노트 전체가 **적용된** 파일이다. 전체가 적용된 결과를 확인하고 싶을 때 사용할 수 있다.
>
> 참고 프로젝트 경로(적용 완료본): `ncafe-lesson-07-refresh-token`

---

이전 노트([[052_Next.js 쿠키 기반 인증과 미들웨어 권한 제어 코드]])에서는 Next.js 프론트엔드를 스프링 본점에 연결했다. 사용자가 로그인하면 Next.js가 토큰을 HttpOnly 쿠키에 보관하고, 문지기(`proxy.ts`)가 보호된 페이지의 출입을 결정하며, 서버 컴포넌트가 쿠키의 토큰을 `Authorization` 헤더로 바꿔 스프링을 호출하는 구조였다.

그런데 그 노트의 마지막에 한 가지 불편을 남겨 두었다. Access Token의 수명이 30분이라서, 30분이 지나면 문지기가 `/login`으로 보내 버리고 사용자는 다시 로그인해야 한다. 수명을 늘리면 되지 않을까? 토큰이 새어 나갔을 때 그만큼 오래 악용된다. 짧게 두면 안전하지만 사용자가 괴롭다.

이번 노트에서는 이 딜레마를 Refresh Token으로 푼다. 짧은 열쇠(Access Token)와 긴 열쇠(Refresh Token)를 함께 발급하고, 짧은 열쇠가 만료되면 긴 열쇠로 조용히 새 짧은 열쇠를 받아 온다. 사용자는 로그인 화면을 다시 보지 않는다.

이 노트에서는 다음 순서로 진행한다.

1. 토큰이 왜 두 개여야 하는지, 누가 재발급을 맡을지 구조를 정한다.
2. 백엔드가 로그인 시 Refresh Token을 함께 발급하고 기억하게 한다.
3. 백엔드에 재발급(`/api/auth/refresh`)과 폐기(`/api/auth/logout`) API를 만든다.
4. 필터에 작은 구멍 하나를 막는다.
5. Postman으로 백엔드만 먼저 확인한다.
6. 프론트엔드 공통 모듈에 쿠키 옵션과 재발급 호출을 추가한다.
7. 로그인·로그아웃 Server Action이 두 번째 쿠키를 다루게 한다.
8. 문지기(`proxy.ts`)가 만료된 토큰을 스스로 갱신하게 한다.
9. 실행하고, 30분을 기다리지 않고 재발급을 눈으로 확인한다.

---

## 1. 토큰은 왜 두 개인가, 재발급은 누가 하는가

### 1) 짧은 열쇠와 긴 열쇠

호텔을 떠올려 보자. 객실 카드키는 분실해도 피해가 작도록 하루만 유효하다. 대신 프런트에 신분증을 보여주면 새 카드키를 받을 수 있다. 신분증은 카드키보다 훨씬 오래 유효하지만, 객실 문을 직접 열지는 못한다. 프런트에서 카드키로 바꿔야만 쓸 수 있다.

| | Access Token (카드키) | Refresh Token (신분증) |
|---|---|---|
| 수명 | 짧다 — 30분 | 길다 — 14일 |
| 용도 | 보호된 API 호출 (`Authorization: Bearer`) | 새 Access Token 발급 요청 **에만** 쓴다 |
| 담는 정보 | `sub`(아이디), `role`(역할), `exp` | `sub`, `exp` — **역할이 없다** |
| 스프링이 기억하나 | 아니오 — 서명만 맞으면 통과 (STATELESS) | 예 — 발급한 것만 인정하고, 로그아웃하면 지운다 |
| 쿠키 이름 | `accessToken` | `refreshToken` |

핵심은 세 번째와 네 번째 줄이다. Refresh Token에는 역할을 넣지 않아서 그 자체로는 아무 문도 열지 못하게 만들고, 서버가 발급 내역을 기억해서 로그아웃하면 즉시 쓸모없게 만든다. 수명이 긴 토큰에는 이 두 가지 안전장치가 필요하다.

`JwtProvider.createRefreshToken()`과 `application.yml`의 `refresh-token-expiration`(14일)은 [[050_스프링 부트 JWT 인증 구현 — JJWT 설정, JwtProvider, JwtAuthenticationFilter, SecurityConfig, 로그인 API]]에서 이미 만들어 두었다. 이제 쓸 차례다.

```yaml
# backend/src/main/resources/application.yml
jwt:
  secret: ${JWT_SECRET:v9y$B&E)H@McQfTjWnZr4u7x!A%C*F-JaNdR}
  access-token-expiration: 1800000      # 30분
  refresh-token-expiration: 1209600000  # 14일
```

### 2) 이번 노트의 세 가지 원칙

**원칙 1. Refresh Token은 재발급 창구(`/api/auth/refresh`)에서만 받는다.**  
`Authorization` 헤더에 Refresh Token을 실어 보내도 필터가 출입증을 주지 않아야 한다. 그러지 않으면 14일짜리 만능 열쇠가 되어 버린다. 4절에서 이 구멍을 막는다.

**원칙 2. 서버는 자기가 발급한 Refresh Token을 기억한다.**  
Access Token은 서명만 보고 통과시키지만(이전 노트의 STATELESS), Refresh Token은 "서버가 아직 인정하는 토큰인가"를 따로 확인한다. 로그아웃은 이 기억을 지우는 일이다. 이번 노트에서는 메모리 Map에 두고, 나중에 DB 테이블로 옮긴다.

**원칙 3. 재발급은 문지기(`proxy.ts`)가 한다.**  
어디서 재발급해야 할까? 후보는 둘이다.

| 후보 | 문제 |
|---|---|
| `backendFetch` 안에서 | 스프링이 401을 주면 재발급하고 다시 시도한다. 자연스러워 보이지만 **서버 컴포넌트는 쿠키를 새로 쓸 수 없다**(`cookies().set()`은 Server Action과 Route Handler에서만 허용). 새 토큰을 받아도 브라우저에 저장하지 못하니 다음 요청에서 또 재발급해야 한다. |
| `proxy.ts` 안에서 | 요청이 페이지에 닿기 전에 실행되고, 응답 쿠키를 쓸 수 있으며, 같은 요청의 쿠키를 바꿔치기해서 뒤따르는 서버 컴포넌트에 넘길 수도 있다. Next.js 16의 `proxy.ts`는 Node.js 런타임으로 실행되므로 스프링을 `fetch`하는 데 제약도 없다. |

그래서 문지기가 맡는다. 문지기가 재발급을 끝내 두면, `backendFetch`에 도착하는 토큰은 항상 유효하다는 전제가 생기고 서버 컴포넌트 코드는 하나도 바뀌지 않는다.

### 3) 전체 흐름

```
① 페이지 요청 (accessToken / refreshToken 쿠키)
        │
        ▼
② proxy.ts
   Access 유효? ──예──▶ 보호 경로 출입 판정 → next
        │아니오
        ▼
   Refresh 있음? ──아니오──▶ 비로그인 (보호 경로면 /login)
        │예
        ▼
③ POST /api/auth/refresh { refreshToken }
        │
   ┌────┴────┐
 성공        실패(폐기·만료·위조)
   │           │
   ▼           ▼
④ 요청 쿠키 교체    두 쿠키 삭제
   + Set-Cookie     + 보호 경로면 /login
   (새 accessToken)
        │
        ▼
⑤ 서버 컴포넌트 / backendFetch
   Authorization: Bearer <새 Access> → 스프링
```

재발급에 실패하면(폐기됐거나 14일이 지났거나 위조) 문지기는 두 쿠키를 모두 지우고 보호 경로라면 `/login`으로 보낸다. 완전한 비로그인 상태로 되돌리는 것이다.

---

## 2. 백엔드 — 로그인 시 Refresh Token 발급하고 기억하기

### 1) LoginResponse — 필드 하나 추가

경로: `backend/src/main/java/com/ncafe/backend/dto/auth/LoginResponse.java`

```java
package com.ncafe.backend.dto.auth;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class LoginResponse {
    private String accessToken;
    /** 액세스 토큰이 만료됐을 때 새 액세스 토큰을 받기 위한 토큰. 수명이 길다(14일). */
    private String refreshToken;
    private String tokenType;
}
```

### 2) RefreshTokenStore — 서버의 기억

원칙 2의 "기억"을 담당하는 클래스다. `security/jwt` 패키지에 둔다.

경로: `backend/src/main/java/com/ncafe/backend/security/jwt/RefreshTokenStore.java`

```java
package com.ncafe.backend.security.jwt;

import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 발급한 리프레시 토큰을 기억해 두는 저장소.
 *
 * 액세스 토큰은 서명만 맞으면 통과시키지만(STATELESS),
 * 리프레시 토큰은 수명이 길어서 "서버가 아직 인정하는 토큰인지"를 따로 확인해야 한다.
 * 로그아웃하면 여기서 지우고, 그 뒤로는 같은 토큰으로 재발급받을 수 없다.
 *
 * 지금은 메모리(Map)에 두므로 서버를 재시작하면 모두 사라진다. DB 수업에서 테이블로 옮긴다.
 */
@Component
public class RefreshTokenStore {

    // key: 사용자 아이디, value: 그 사용자에게 마지막으로 발급한 리프레시 토큰
    private final Map<String, String> tokens = new ConcurrentHashMap<>();

    public void save(String username, String refreshToken) {
        tokens.put(username, refreshToken);
    }

    /** 저장된 토큰과 같은지 확인한다. 로그아웃했거나 다른 기기에서 다시 로그인했으면 false */
    public boolean matches(String username, String refreshToken) {
        return refreshToken.equals(tokens.get(username));
    }

    public void remove(String username) {
        tokens.remove(username);
    }
}
```

- **`ConcurrentHashMap`**: 여러 요청이 동시에 들어와도 안전한 Map이다. 톰캣은 요청마다 다른 스레드를 쓴다.
- **사용자당 하나**: 키가 아이디이므로 같은 사용자가 다시 로그인하면 이전 Refresh Token은 덮어써져 무효가 된다. "한 계정은 한 곳에서만 로그인"이라는 단순한 정책이다. 기기별로 여러 개를 허용하려면 키를 토큰 자체로 바꾸면 되는데, 그건 DB로 옮길 때 다룬다.
- **메모리의 한계**: 스프링을 재시작하면 Map이 비므로 기존 Refresh Token은 전부 "모르는 토큰"이 되어 재발급이 거절된다. 개발 중에 백엔드를 재시작한 뒤 로그인 페이지로 튕기는 것은 정상 동작이다.

### 3) AuthService.login — 두 토큰 발급

이전 노트의 `login()`에 Refresh Token 발급과 저장을 추가한다. 역할을 고르는 코드는 재발급에서도 쓰므로 `toRole()` 메서드로 뽑아 둔다. 전체 파일은 3절에서 한 번에 보고, 여기서는 `login()`만 본다.

```java
    public LoginResponse login(LoginRequest loginRequest){

        UsernamePasswordAuthenticationToken authenticationToken
            = new UsernamePasswordAuthenticationToken(loginRequest.getUsername(), loginRequest.getPassword());

        Authentication authenticate = authenticationManager.authenticate(authenticationToken);

        String username = authenticate.getName();
        String role = toRole(authenticate.getAuthorities());

        // 1. 액세스 토큰: 짧게(30분). 요청마다 Authorization 헤더에 실린다.
        String accessToken = jwtProvider.createAccessToken(username, role);

        // 2. 리프레시 토큰: 길게(14일). 액세스 토큰이 만료됐을 때 재발급용으로만 쓴다.
        //    서버가 기억해 두어야 로그아웃 시 무효화할 수 있다.
        String refreshToken = jwtProvider.createRefreshToken(username);
        refreshTokenStore.save(username, refreshToken);

        return LoginResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .tokenType("Bearer")
                .build();
    }
```

---

## 3. 백엔드 — 재발급과 폐기 API

### 1) RefreshRequest — 요청 본문

재발급과 로그아웃 모두 "Refresh Token 하나"를 받는다. DTO 하나로 둘 다 처리한다.

경로: `backend/src/main/java/com/ncafe/backend/dto/auth/RefreshRequest.java`

```java
package com.ncafe.backend.dto.auth;

import lombok.Data;
import lombok.NoArgsConstructor;

/** POST /api/auth/refresh, POST /api/auth/logout 의 요청 본문 */
@Data
@NoArgsConstructor
public class RefreshRequest {
    private String refreshToken;
}
```

### 2) InvalidTokenException — 거절 사유

재발급이 거절되는 경우는 둘이다. 서명이나 만료가 틀렸거나(위조·14일 경과), 서명은 맞지만 서버가 더 이상 인정하지 않거나(로그아웃·재로그인). 둘 다 같은 예외로 던지고, 컨트롤러가 401로 바꾼다.

경로: `backend/src/main/java/com/ncafe/backend/security/jwt/InvalidTokenException.java`

```java
package com.ncafe.backend.security.jwt;

/** 리프레시 토큰이 위조·만료됐거나 서버가 더 이상 인정하지 않을 때 던진다. 컨트롤러가 401로 바꾼다. */
public class InvalidTokenException extends RuntimeException {
    public InvalidTokenException(String message) {
        super(message);
    }
}
```

왜 `RuntimeException`인가? 서비스 메서드 시그니처에 `throws`를 붙이지 않아도 되고, 트랜잭션 안에서 던져도 롤백 대상이 된다. 스프링 서비스 계층의 관례다.

### 3) AuthService — 전체

경로: `backend/src/main/java/com/ncafe/backend/service/AuthService.java`

```java
package com.ncafe.backend.service;

import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.stereotype.Service;

import java.util.Collection;
import java.util.List;

import com.ncafe.backend.dto.auth.LoginRequest;
import com.ncafe.backend.dto.auth.LoginResponse;
import com.ncafe.backend.security.jwt.InvalidTokenException;
import com.ncafe.backend.security.jwt.JwtProvider;
import com.ncafe.backend.security.jwt.RefreshTokenStore;

@Service
public class AuthService {

    private AuthenticationManager authenticationManager;
    private JwtProvider jwtProvider;
    private UserDetailsService userDetailsService;
    private RefreshTokenStore refreshTokenStore;

    public AuthService(AuthenticationManager authenticationManager,
                       JwtProvider jwtProvider,
                       UserDetailsService userDetailsService,
                       RefreshTokenStore refreshTokenStore){
        this.authenticationManager = authenticationManager;
        this.jwtProvider = jwtProvider;
        this.userDetailsService = userDetailsService;
        this.refreshTokenStore = refreshTokenStore;
    }

    public LoginResponse login(LoginRequest loginRequest){

        UsernamePasswordAuthenticationToken authenticationToken
            = new UsernamePasswordAuthenticationToken(loginRequest.getUsername(), loginRequest.getPassword());

        Authentication authenticate = authenticationManager.authenticate(authenticationToken);
        // -> 권한 정보 Grant..
        // -> 인증 Authentication
        // -> 보안객체 홀더 SercurityContextHolder

        String username = authenticate.getName();
        String role = toRole(authenticate.getAuthorities());

        // 1. 액세스 토큰: 짧게(30분). 요청마다 Authorization 헤더에 실린다.
        String accessToken = jwtProvider.createAccessToken(username, role);

        // 2. 리프레시 토큰: 길게(14일). 액세스 토큰이 만료됐을 때 재발급용으로만 쓴다.
        //    서버가 기억해 두어야 로그아웃 시 무효화할 수 있다.
        String refreshToken = jwtProvider.createRefreshToken(username);
        refreshTokenStore.save(username, refreshToken);

        return LoginResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .tokenType("Bearer")
                .build();
    }

    /** 리프레시 토큰을 받아 새 액세스 토큰을 발급한다. 리프레시 토큰은 그대로 유지한다. */
    public LoginResponse refresh(String refreshToken){

        // 1. 서명과 만료 확인 (위조됐거나 14일이 지났으면 거절)
        if (refreshToken == null || !jwtProvider.validateToken(refreshToken)) {
            throw new InvalidTokenException("리프레시 토큰이 유효하지 않습니다.");
        }

        // 2. 서버가 아직 인정하는 토큰인지 확인 (로그아웃했으면 저장소에 없다)
        String username = jwtProvider.getUsername(refreshToken);
        if (!refreshTokenStore.matches(username, refreshToken)) {
            throw new InvalidTokenException("이미 만료 처리된 리프레시 토큰입니다.");
        }

        // 3. 리프레시 토큰에는 역할이 없으므로 사용자 정보를 다시 읽어 역할을 알아낸다.
        //    (그 사이 권한이 바뀌었어도 새 액세스 토큰에는 최신 역할이 담긴다)
        UserDetails user = userDetailsService.loadUserByUsername(username);
        String role = toRole(user.getAuthorities());

        String accessToken = jwtProvider.createAccessToken(username, role);

        return LoginResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .tokenType("Bearer")
                .build();
    }

    /** 로그아웃: 저장소에서 지워 같은 리프레시 토큰으로는 더 이상 재발급받지 못하게 한다. */
    public void logout(String refreshToken){
        if (refreshToken == null || !jwtProvider.validateToken(refreshToken)) {
            return; // 이미 쓸 수 없는 토큰이면 할 일이 없다
        }
        refreshTokenStore.remove(jwtProvider.getUsername(refreshToken));
    }

    /**
     * 스프링의 권한 목록을 토큰에 담을 대표 역할 하나로 바꾼다.
     * 토큰은 프론트엔드도 읽는 "공용 데이터"이므로 스프링 내부 규약인 "ROLE_" 접두어는 떼어 낸다.
     * (접두어는 JwtAuthenticationFilter가 토큰을 다시 읽을 때 붙인다)
     * admin 계정은 USER와 ADMIN을 모두 가지므로, 더 높은 권한인 ADMIN을 대표 역할로 담는다.
     */
    private String toRole(Collection<? extends GrantedAuthority> authorities){
        List<String> roles = authorities.stream()
                        .map(GrantedAuthority::getAuthority)
                        .map(authority -> authority.replaceFirst("^ROLE_", ""))
                        .toList();
        return roles.contains("ADMIN") ? "ADMIN" : roles.stream().findFirst().orElse("USER");
    }
}
```

`refresh()`의 세 단계를 따로 짚어 보자.

1. **서명과 만료**: `validateToken()`은 050 노트에서 만든 메서드다. 비밀키로 서명을 확인하고 `exp`를 본다. 위조됐거나 14일이 지났으면 여기서 끝난다.
2. **서버의 기억**: 서명이 맞아도 저장소에 없으면 거절한다. 로그아웃한 토큰, 다른 곳에서 다시 로그인해 덮어써진 토큰이 여기서 걸린다. 이 단계가 없으면 로그아웃이 의미가 없다.
3. **역할 다시 읽기**: Refresh Token에는 `role`이 없다(1절 원칙 1). 새 Access Token에 역할을 담으려면 사용자 정보를 다시 읽어야 한다. `UserDetailsService`는 SecurityConfig에 빈으로 등록해 둔 것이다. 지금은 메모리 사용자지만, DB로 바뀌어도 이 코드는 그대로다. 부수 효과로, 그 사이 관리자가 사용자의 권한을 바꿨다면 새 Access Token에는 바뀐 권한이 담긴다.

`logout()`은 짧다. 토큰이 유효하면 저장소에서 지우고, 유효하지 않으면 조용히 끝낸다. 로그아웃은 "실패"가 있어서는 안 되는 작업이다. 이미 깨진 토큰을 들고 로그아웃하러 온 사용자에게 에러를 보여줄 이유가 없다.

### 4) AuthController — 두 엔드포인트와 401 변환

경로: `backend/src/main/java/com/ncafe/backend/controller/AuthController.java`

```java
package com.ncafe.backend.controller;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.ncafe.backend.dto.auth.LoginRequest;
import com.ncafe.backend.dto.auth.LoginResponse;
import com.ncafe.backend.dto.auth.RefreshRequest;
import com.ncafe.backend.security.jwt.InvalidTokenException;
import com.ncafe.backend.service.AuthService;

import java.util.Map;

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

    /** 리프레시 토큰 문제는 401로 알려 준다. 프론트는 이 응답을 받으면 로그인 페이지로 보낸다. */
    @ExceptionHandler(InvalidTokenException.class)
    @ResponseStatus(HttpStatus.UNAUTHORIZED)
    public Map<String, String> handleInvalidToken(InvalidTokenException e){
        return Map.of("message", e.getMessage());
    }
}
```

`/refresh`와 `/logout`은 토큰 없이 호출된다. `SecurityConfig`에서 `/api/auth/**`를 `permitAll()`로 열어 두었으므로 따로 손댈 것이 없다. Access Token이 만료된 상태에서 재발급을 요청하는 것이니 당연히 인증 없이 들어와야 한다.

- **`@ResponseStatus(NO_CONTENT)`**: 로그아웃은 돌려줄 본문이 없다. 204가 "성공했고 내용 없음"의 표준 표현이다.
- **`@ExceptionHandler`**: 이 컨트롤러 안에서 `InvalidTokenException`이 던져지면 500 대신 401과 메시지 JSON으로 바꾼다. 프론트의 `refresh.ts`(6절)는 `res.ok`가 아니면 모두 실패로 보므로 상태 코드만 중요하지만, Postman으로 볼 때 사유가 보이면 디버깅이 편하다.

---

## 4. 백엔드 — 필터의 구멍 막기

`JwtAuthenticationFilter`(이전 노트)는 `Authorization: Bearer <토큰>`이 오면 서명을 확인하고 `role` 클레임으로 권한 객체를 만든다. 그런데 Refresh Token도 같은 비밀키로 서명된 JWT다. 누군가 Refresh Token을 Authorization 헤더에 실어 보내면 어떻게 될까?

서명은 통과한다. `getRole()`은 클레임이 없으니 `null`을 돌려준다. 그러면 `"ROLE_" + null = "ROLE_null"`이라는 권한으로 인증 객체가 만들어진다. `hasRole("ADMIN")`은 막히지만 `authenticated()`는 통과한다. 즉 `GET /api/menus` 같은 "로그인만 하면 되는" API를 14일짜리 토큰으로 호출할 수 있게 된다. **1절 원칙 1 위반**이다.

고치는 방법은 간단하다. 역할이 없는 토큰에는 출입증을 주지 않는다.

경로: `backend/src/main/java/com/ncafe/backend/security/jwt/JwtAuthenticationFilter.java` (해당 부분)

```java
        // 2. 토큰이 존재하고 유효한지 검증
        if (token != null && jwtProvider.validateToken(token)) {
            // 토큰에서 사용자 아이디와 권한 추출
            String username = jwtProvider.getUsername(token);
            String role = jwtProvider.getRole(token);

            // 리프레시 토큰에는 role 클레임이 없다. 수명이 긴 리프레시 토큰을
            // 액세스 토큰처럼 Authorization 헤더에 실어 보내도 출입증을 주지 않는다.
            if (role == null) {
                filterChain.doFilter(request, response);
                return;
            }

            // 스프링 시큐리티 권한 객체 생성
            // 토큰에는 "ADMIN"처럼 순수한 역할 이름만 들어 있다.
            // hasRole("ADMIN")은 "ROLE_ADMIN"을 찾으므로 여기서 접두어를 다시 붙인다.
            SimpleGrantedAuthority authority = new SimpleGrantedAuthority("ROLE_" + role);
            // ... (이하 동일)
```

`return` 앞에 `filterChain.doFilter()`를 부르는 것을 잊지 말자. 출입증을 안 줄 뿐이지 요청 자체를 끊는 것은 아니다. 인증 객체 없이 다음 필터로 넘어가면, 보호된 경로에서는 스프링 시큐리티가 알아서 403을 준다.

> **왜 type 클레임을 넣지 않았나?** Access Token에 `"type": "access"`, Refresh Token에 `"type": "refresh"`를 넣고 필터에서 구분하는 방법도 흔하다. 더 명시적이지만 JwtProvider를 고쳐야 한다. 이번 노트에서는 "역할이 없으면 Access Token이 아니다"라는 이미 있는 사실을 이용해 기존 코드를 최소한으로 건드렸다.

---

## 5. Postman으로 백엔드만 먼저 확인하기

프론트엔드로 넘어가기 전에 백엔드가 혼자서 제대로 동작하는지 확인한다. 스프링을 재시작하고(`./gradlew bootRun`) 다음 순서로 요청한다. `{{...}}`는 앞 응답에서 복사한 값이다.

| # | 요청 | 기대 결과 | 확인하는 것 |
|---|---|---|---|
| 1 | `POST /api/auth/login` `{"username":"admin","password":"123"}` | 200, `accessToken`과 `refreshToken`이 서로 다른 문자열 | 2절 — 두 토큰 발급 |
| 2 | `refreshToken`을 jwt.io에 붙여 넣기 | payload에 `sub`, `iat`, `exp`만 있고 **role 없음** | 1절 — 역할 없는 긴 열쇠 |
| 3 | `GET /api/menus` + `Authorization: Bearer {{refreshToken}}` | **403** | 4절 — 필터의 구멍 막힘 |
| 4 | `GET /api/menus` + `Authorization: Bearer {{accessToken}}` | 200 | 기존 동작 유지 |
| 5 | `POST /api/auth/refresh` `{"refreshToken":"{{refreshToken}}"}` | 200, 새 `accessToken` (1번과 다름), role은 ADMIN | 3절 — 재발급, 역할 다시 읽기 |
| 6 | `GET /api/admin/menus` + 5번의 새 accessToken | 200 | 재발급된 토큰이 진짜 통한다 |
| 7 | `POST /api/auth/refresh` `{"refreshToken":"abc.def.ghi"}` | 401 `{"message":"리프레시 토큰이 유효하지 않습니다."}` | 3절 1단계 — 서명 |
| 8 | `POST /api/auth/logout` `{"refreshToken":"{{refreshToken}}"}` | **204** | 3절 — 폐기 |
| 9 | 5번을 다시 보내기 | 401 `{"message":"이미 만료 처리된 리프레시 토큰입니다."}` | 3절 2단계 — 서버의 기억 |
| 10 | `GET /api/menus` + 1번의 accessToken | **200 (!)** | 아래 설명 |

10번이 의외일 수 있다. 로그아웃했는데 Access Token이 아직 통한다. 이것이 STATELESS의 대가다. 스프링은 Access Token을 기억하지 않으므로 "이미 로그아웃한 토큰"인지 알 길이 없고, 서명과 만료만 본다. 로그아웃이 막는 것은 **재발급**이다. 그래서 Access Token의 수명을 30분처럼 짧게 두는 것이고, 로그아웃 후 최대 30분의 틈은 이 구조에서 받아들이는 위험이다. 이 틈까지 막으려면 "로그아웃된 Access Token 블랙리스트"를 두어야 하는데, 그러면 STATELESS를 포기하는 셈이 된다.

---

## 6. 프론트엔드 공통 모듈 — 쿠키 옵션과 재발급 호출

이전 노트의 `app/_lib/auth/`에 파일 세 개를 더하고 두 개를 손본다.

```
frontend/app/_lib/auth/
├── token.ts      (수정) REFRESH_TOKEN_COOKIE 추가
├── env.ts        (신규) BACKEND_URL — backend.ts에서 분리
├── backend.ts    (수정) BACKEND_URL을 env.ts에서 가져와 다시 내보냄
├── cookies.ts    (신규) 두 토큰 쿠키의 옵션
├── refresh.ts    (신규) POST /api/auth/refresh 호출
└── session.ts    (그대로)
```

### 1) token.ts — 쿠키 이름 추가

경로: `frontend/app/_lib/auth/token.ts`

```ts
/** 브라우저 쿠키에 저장할 때 쓰는 이름 */
export const ACCESS_TOKEN_COOKIE = "accessToken";
/** 재발급용 리프레시 토큰 쿠키 이름. 액세스 토큰보다 수명이 길다(14일) */
export const REFRESH_TOKEN_COOKIE = "refreshToken";
```

나머지(`decodeToken`, `isExpired`)는 그대로다. Refresh Token도 같은 JWT 형식이라 `decodeToken()`으로 `exp`를 읽을 수 있다. 쿠키 수명을 맞출 때 쓴다.

### 2) env.ts — BACKEND_URL 분리

경로: `frontend/app/_lib/auth/env.ts`

```ts
/**
 * 스프링 백엔드 주소. 브라우저에 노출될 필요가 없으므로 NEXT_PUBLIC_ 접두어를 붙이지 않는다.
 * .env.local 에 BACKEND_URL=http://localhost:8080 처럼 설정한다. 없으면 로컬 기본값을 쓴다.
 *
 * backend.ts(서버 컴포넌트용)와 proxy.ts(문지기) 양쪽에서 쓰므로 next/headers 를 import 하지 않는 파일에 둔다.
 */
export const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8080";
```

왜 옮기는가? 이전 노트의 `backend.ts`는 `session.ts`를 import하고, `session.ts`는 `next/headers`의 `cookies()`를 import한다. 이제 `proxy.ts`가 `BACKEND_URL`을 써야 하는데, 문지기에서 `next/headers`를 끌어들이는 것은 피하고 싶다(`cookies()`는 문지기에서 쓸 수 없는 API다). 그래서 아무것도 import하지 않는 파일에 상수를 두고, 양쪽이 거기서 가져간다.

경로: `frontend/app/_lib/auth/backend.ts`

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
```

`export { BACKEND_URL }`로 다시 내보내기 때문에, 이전 노트에서 `backend.ts`로부터 `BACKEND_URL`을 가져다 쓰던 `backendCheckApi.ts`는 고치지 않아도 된다. 함수 본문은 한 줄도 바뀌지 않았다. **1절 원칙 3의 결과**다.

### 3) cookies.ts — 쿠키 옵션을 한 곳에

이전 노트에서는 `loginAction.ts`가 쿠키 옵션을 직접 들고 있었다. 이제 쿠키를 쓰는 곳이 둘(로그인 액션, 문지기)이 되므로 옵션을 한 곳으로 모은다. 두 곳의 옵션이 조금이라도 다르면 브라우저는 다른 쿠키로 취급할 수 있다.

경로: `frontend/app/_lib/auth/cookies.ts`

```ts
import { ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE, decodeToken } from "./token";

/**
 * 토큰 쿠키 옵션. loginAction(처음 저장)과 proxy.ts(재발급 후 갱신)가 같은 옵션을 쓰도록 한 곳에 둔다.
 *
 * - httpOnly: 자바스크립트로 접근 불가 → XSS로 탈취되지 않음
 * - secure: 운영에서는 HTTPS에서만 전송
 * - sameSite lax: 다른 사이트에서 시작된 POST에는 실리지 않음
 * - maxAge: 토큰 자체의 만료 시각에 맞춘다. 쿠키가 토큰보다 오래 살 이유가 없다.
 */
export type TokenCookie = {
  name: string;
  value: string;
  options: { httpOnly: true; secure: boolean; sameSite: "lax"; path: "/"; maxAge: number };
};

function tokenCookie(name: string, token: string, fallbackSeconds: number): TokenCookie {
  const payload = decodeToken(token);
  const maxAge = payload ? Math.max(0, payload.exp - Math.floor(Date.now() / 1000)) : fallbackSeconds;
  return {
    name,
    value: token,
    options: {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge,
    },
  };
}

/** 액세스 토큰 쿠키 (기본 30분) */
export const accessTokenCookie = (token: string) => tokenCookie(ACCESS_TOKEN_COOKIE, token, 60 * 30);

/** 리프레시 토큰 쿠키 (기본 14일) */
export const refreshTokenCookie = (token: string) => tokenCookie(REFRESH_TOKEN_COOKIE, token, 60 * 60 * 24 * 14);
```

- **`maxAge`를 토큰의 `exp`에서 계산**: Access Token 쿠키는 30분 뒤, Refresh Token 쿠키는 14일 뒤 브라우저가 알아서 지운다. 쿠키가 토큰보다 오래 남아 "있는데 못 쓰는" 상태를 만들지 않는다.
- **반환값이 `{ name, value, options }` 객체**: `cookies().set(name, value, options)`(Server Action)과 `response.cookies.set(name, value, options)`(문지기)의 인자 모양이 같아서, 양쪽에서 `c.name`, `c.value`, `c.options`로 펼쳐 쓰면 된다.

### 4) refresh.ts — 재발급 호출

경로: `frontend/app/_lib/auth/refresh.ts`

```ts
import { BACKEND_URL } from "./env";

/**
 * 리프레시 토큰으로 새 액세스 토큰을 받아 온다.
 * POST /api/auth/refresh → { accessToken, refreshToken, tokenType }
 *
 * 실패(401: 폐기·만료·위조, 또는 백엔드 다운)하면 null. 호출한 쪽에서 로그아웃 처리한다.
 */
export async function refreshAccessToken(refreshToken: string): Promise<string | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refreshToken }),
      cache: "no-store",
    });
    if (!res.ok) return null;
    const { accessToken } = (await res.json()) as { accessToken?: string };
    return accessToken ?? null;
  } catch {
    return null;
  }
}
```

실패 이유를 구분하지 않고 전부 `null`로 돌려준다. 문지기 입장에서는 이유가 무엇이든 할 일이 같다 — 쿠키를 지우고 비로그인으로 취급한다. 성공과 실패 두 갈래만 있는 함수가 호출하는 쪽을 단순하게 만든다.

---

## 7. 로그인·로그아웃 Server Action — 두 번째 쿠키

### 1) loginAction.ts — 두 쿠키 저장

이전 노트의 코드에서 바뀐 곳은 응답 해석과 쿠키 저장 부분이다.

경로: `frontend/app/login/_components/LoginForm/loginAction.ts`

```ts
"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { BACKEND_URL } from "@/app/_lib/auth/env";
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

  if (res.status === 401 || res.status === 403) {
    return { error: "아이디 또는 비밀번호가 올바르지 않아요." };
  }
  if (!res.ok) {
    return { error: `로그인에 실패했어요. (HTTP ${res.status})` };
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

로그인 폼(`LoginForm.tsx`)은 바뀌지 않는다. 폼은 아이디와 비밀번호를 보낼 뿐이고, 토큰이 하나든 둘이든 알 바가 아니다.

### 2) logoutAction.ts — 백엔드에 폐기 요청 후 쿠키 삭제

경로: `frontend/app/_components/ProfileMenu/logoutAction.ts`

```ts
"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { BACKEND_URL } from "@/app/_lib/auth/env";
import { ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE } from "@/app/_lib/auth/token";

/**
 * 로그아웃.
 * 1. 백엔드에 리프레시 토큰 폐기를 요청한다 (POST /api/auth/logout).
 *    이걸 빼먹으면 쿠키를 지워도 어딘가에 남은 리프레시 토큰으로 14일 동안 재발급이 가능하다.
 * 2. 두 쿠키를 지운다. 다음 요청부터 비로그인 상태가 된다.
 */
export async function logout() {
  const cookieStore = await cookies();
  const refreshToken = cookieStore.get(REFRESH_TOKEN_COOKIE)?.value;

  if (refreshToken) {
    try {
      await fetch(`${BACKEND_URL}/api/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refreshToken }),
        cache: "no-store",
      });
    } catch {
      // 백엔드가 꺼져 있어도 로그아웃은 진행한다. 쿠키만 지워도 이 브라우저에서는 끝난다.
    }
  }

  cookieStore.delete(ACCESS_TOKEN_COOKIE);
  cookieStore.delete(REFRESH_TOKEN_COOKIE);
  redirect("/login");
}
```

이전 노트의 로그아웃은 쿠키 삭제뿐이었다. 그때는 Access Token 하나였고 30분이면 어차피 죽으니 그걸로 충분했다. 이제는 14일짜리 토큰이 서버에 기억되어 있다. 쿠키만 지우면 브라우저에서는 사라지지만, 서버 저장소에는 남아서 그 값을 아는 누군가는 14일 동안 재발급받을 수 있다. 그래서 로그아웃은 반드시 서버에 알리는 것이 먼저다. 백엔드가 꺼져 있어 알리지 못하더라도 사용자를 로그아웃 상태로는 만들어야 하므로, `catch`에서 삼키고 쿠키 삭제로 넘어간다.

---

## 8. 문지기 — 만료된 토큰을 스스로 갱신하기

이 노트의 핵심이다. 이전 노트의 `proxy.ts`는 "토큰이 없거나 만료 → 로그인으로"가 전부였다. 이제 그 사이에 "만료됐지만 Refresh Token이 있으면 재발급" 단계가 들어간다.

### 1) 코드

경로: `frontend/proxy.ts`

```ts
import { NextResponse, type NextRequest } from "next/server";
import { ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE, decodeToken, isExpired } from "@/app/_lib/auth/token";
import { accessTokenCookie } from "@/app/_lib/auth/cookies";
import { refreshAccessToken } from "@/app/_lib/auth/refresh";

/**
 * 문지기. 모든 페이지 요청에 앞서 토큰 상태를 정리하고, 보호된 페이지는 출입을 막는다.
 *
 * 1) 액세스 토큰이 없거나 만료됐는데 리프레시 토큰이 있으면 → 백엔드에서 새 액세스 토큰을 받아
 *    - 응답 쿠키에 담아 브라우저의 쿠키를 갱신하고
 *    - 이번 요청의 쿠키도 바꿔치기해서 뒤따르는 서버 컴포넌트(getSession)가 새 토큰을 읽게 한다.
 *    재발급에 실패하면(폐기·만료·백엔드 다운) 두 쿠키를 지워 완전한 비로그인 상태로 만든다.
 * 2) /my, /admin 은 로그인 상태여야 통과. 아니면 /login?next=원래경로 로 보낸다.
 * 3) /admin 은 role 이 ADMIN 일 때만 통과.
 *
 * 여기서는 서명을 검증하지 않는다(비밀키는 백엔드만 가진다).
 * 화면 껍데기에 들어가지 못하게 막는 1차 관문일 뿐이고,
 * 데이터 접근의 최종 판정은 백엔드가 401/403 으로 내린다.
 */
export async function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  const accessToken = request.cookies.get(ACCESS_TOKEN_COOKIE)?.value;
  const refreshToken = request.cookies.get(REFRESH_TOKEN_COOKIE)?.value;

  let payload = accessToken ? decodeToken(accessToken) : null;
  let loggedIn = payload !== null && !isExpired(payload);

  // 1) 액세스 토큰이 못 쓰게 됐고 리프레시 토큰이 있으면 재발급을 시도한다
  let renewedToken: string | null = null;
  let refreshFailed = false;

  if (!loggedIn && refreshToken) {
    renewedToken = await refreshAccessToken(refreshToken);
    if (renewedToken) {
      payload = decodeToken(renewedToken);
      loggedIn = payload !== null && !isExpired(payload);
      // 이번 요청의 쿠키를 새 토큰으로 바꿔치기 (아래 NextResponse.next 의 request.headers 로 전달된다)
      request.cookies.set(ACCESS_TOKEN_COOKIE, renewedToken);
    } else {
      refreshFailed = true;
    }
  }

  // 2) 보호 경로 판정
  const isProtected = pathname.startsWith("/my") || pathname.startsWith("/admin");

  let response: NextResponse;
  if (isProtected && !loggedIn) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname + search);
    response = NextResponse.redirect(loginUrl);
  } else if (pathname.startsWith("/admin") && payload?.role !== "ADMIN") {
    // 3) 로그인은 했지만 관리자가 아니다
    response = NextResponse.redirect(new URL("/my", request.url));
  } else {
    // 바꿔치기한 쿠키가 서버 컴포넌트까지 전달되도록 요청 헤더를 넘긴다
    response = NextResponse.next({ request: { headers: new Headers(request.headers) } });
  }

  // 쿠키 정리: 재발급 성공이면 갱신, 실패면 삭제
  if (renewedToken) {
    const c = accessTokenCookie(renewedToken);
    response.cookies.set(c.name, c.value, c.options);
  } else if (!loggedIn) {
    if (accessToken) response.cookies.delete(ACCESS_TOKEN_COOKIE); // 만료·손상된 액세스 토큰 정리
    if (refreshFailed) response.cookies.delete(REFRESH_TOKEN_COOKIE); // 더 이상 못 쓰는 리프레시 토큰 정리
  }

  return response;
}

export const config = {
  // 정적 파일(_next, 확장자 있는 경로)을 제외한 모든 페이지에서 실행한다.
  // 보호 경로만 걸면 홈 같은 공개 페이지의 헤더가 만료된 토큰 때문에 "로그아웃 상태"로 보이기 때문이다.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};
```

### 2) 함수가 async가 되었다

이전 노트의 `proxy`는 동기 함수였다. 쿠키를 읽고 해독하는 일만 했기 때문이다. 이제 스프링을 `fetch`하므로 `async`가 되고, 재발급이 필요한 요청은 그만큼 느려진다. 하지만 재발급은 30분에 한 번이다. 나머지 요청은 `loggedIn`이 true라서 if 블록을 건너뛰고, 이전과 똑같이 쿠키 해독만 한다.

### 3) 쿠키 바꿔치기 — 두 군데에 써야 한다

재발급에 성공하면 새 토큰을 두 곳에 넣는다.

| 어디에 | 코드 | 누가 읽나 |
|---|---|---|
| 이번 요청의 쿠키 | `request.cookies.set(ACCESS_TOKEN_COOKIE, renewedToken)` + `NextResponse.next({ request: { headers } })` | 이 요청을 처리할 서버 컴포넌트 — `getSession()`, `backendFetch()` |
| 응답의 Set-Cookie | `response.cookies.set(c.name, c.value, c.options)` | 브라우저 — 다음 요청부터 새 쿠키를 들고 온다 |

둘 중 하나만 하면 어떻게 될까?

- **응답에만 넣으면**: 브라우저는 새 쿠키를 받지만, 이번 화면은 만료된 토큰으로 렌더링된다. `getSession()`이 `null`을 돌려주고 헤더에 "로그인" 버튼이 뜬다. 새로고침하면 그제야 정상이다.
- **요청에만 넣으면**: 이번 화면은 정상이지만 브라우저 쿠키는 그대로 만료 상태다. 다음 요청마다 또 재발급한다.

`request.cookies.set()`은 `NextRequest`가 들고 있는 cookie 헤더 문자열을 고쳐 쓴다. 그 다음 `NextResponse.next({ request: { headers: new Headers(request.headers) } })`가 고쳐진 헤더를 상류(서버 컴포넌트)로 전달한다. Next.js 문서가 강조하듯 `NextResponse.next({ headers })`(응답 헤더)가 아니라 `NextResponse.next({ request: { headers } })`(요청 헤더)여야 한다.

### 4) 쿠키 정리의 네 가지 경우

마지막 블록이 하는 일을 경우별로 정리하면 이렇다.

| 상황 | `renewedToken` | `refreshFailed` | 응답 쿠키 |
|---|---|---|---|
| 토큰이 멀쩡하다 | null | false | 손대지 않음 |
| 만료됐지만 재발급 성공 | 새 토큰 | false | `accessToken` 갱신 |
| 만료됐고 재발급 실패 | null | true | `accessToken`, `refreshToken` 모두 삭제 |
| 애초에 쿠키가 없다 | null | false | 손대지 않음 (지울 것이 없다) |

세 번째 줄이 중요하다. 재발급이 거절됐다는 것은 Refresh Token이 폐기됐거나(다른 곳에서 로그아웃·재로그인) 14일이 지났다는 뜻이다. 그 쿠키를 남겨 두면 모든 요청마다 스프링에 재발급을 요청하고 401을 받는 낭비가 생긴다. 깨끗이 지워서 다음 요청부터는 "쿠키 없음"의 빠른 경로를 타게 한다.

### 5) matcher가 넓어졌다

이전 노트에서는 `/my`, `/admin`에서만 문지기를 돌렸다. 이제는 정적 파일을 뺀 모든 경로다. 왜일까?

홈(`/`)은 보호 경로가 아니지만 헤더에 로그인 상태를 보여준다. 문지기가 홈에서 돌지 않으면, Access Token이 만료된 사용자가 홈에 왔을 때 `getSession()`이 `null`을 돌려주고 헤더는 "로그인" 버튼을 보여준다. 사용자는 "로그아웃됐나?" 하고 `/my`를 눌렀다가 거기서야 재발급이 되어 다시 로그인 상태가 된다. 이상한 경험이다.

그래서 **재발급은 모든 페이지에서**, **출입 통제는 `/my`와 `/admin`에서만** 한다. 코드에서 `isProtected`가 두 역할을 가르는 경계다.

`matcher`의 정규식은 Next.js 문서의 권장 패턴이다. `_next/static`, `_next/image`, `favicon.ico`, 그리고 `.`이 들어간 경로(이미지, 폰트 등 확장자 있는 파일)를 제외한다. 이것을 빼먹으면 이미지 하나 로드할 때마다 문지기가 돈다.

---

## 9. 실행과 테스트

### 1) 실행

스프링을 재시작한다(`RefreshTokenStore`가 새 빈이다). Next.js는 `npm run dev` 상태면 자동으로 다시 읽는다.

```bash
# 터미널 1 — 스프링 백엔드 (8080)
cd backend
./gradlew bootRun

# 터미널 2 — Next.js 프론트엔드 (3000)
cd frontend
npm run dev
```

### 2) 30분을 기다리지 않고 재발급 보기

재발급은 Access Token이 만료돼야 일어난다. 30분을 기다리는 대신 두 가지 방법이 있다.

- **방법 A — 쿠키를 직접 지운다.** 개발자 도구 → Application → Cookies에서 `accessToken`만 지우고(`refreshToken`은 남긴다) 새로고침한다. 문지기 입장에서 "Access Token 없음 + Refresh Token 있음"은 만료와 같은 상황이다.
- **방법 B — 만료 시간을 줄인다.** `application.yml`의 `access-token-expiration`을 `60000`(1분)으로 바꾸고 스프링을 재시작한다. 로그인하고 1분 뒤 아무 페이지나 새로고침하면 재발급이 일어난다. 확인이 끝나면 원래 값(`1800000`)으로 되돌린다.

### 3) 시나리오

| # | 할 일 | 기대 결과 | 어디서 결정되나 |
|---|---|---|---|
| 1 | `admin` / `123`으로 로그인 | `/`로 이동, 헤더에 아바타 A | `loginAction.ts` |
| 2 | 개발자 도구 → Cookies | `accessToken`(Max-Age 1800)과 `refreshToken`(Max-Age 1209600) 두 개, 둘 다 HttpOnly ✓ | `cookies.ts` |
| 3 | `accessToken` 쿠키만 삭제 후 `/admin` 새로고침 | 화면이 그대로 뜨고, Cookies에 `accessToken`이 다시 생겨 있음. "스프링 백엔드 연결됨 → 200" | `proxy.ts` 재발급 → 요청·응답 쿠키 교체 |
| 4 | 3번 직후 Network 탭에서 `/admin` 응답 헤더 | `Set-Cookie: accessToken=...; HttpOnly; Max-Age=1800` | `response.cookies.set` |
| 5 | `accessToken`만 삭제 후 홈(`/`) 새로고침 | 헤더가 로그인 상태 그대로 (아바타 A) | 넓어진 matcher |
| 6 | `refreshToken` 쿠키 값을 아무 글자로 바꾸고 `accessToken` 삭제 후 `/my` | `/login?next=/my`로 이동, Cookies에서 두 쿠키 모두 사라짐 | `proxy.ts` 재발급 실패 → 삭제 |
| 7 | 다시 로그인 → 프로필 메뉴 → 로그아웃 | `/login`으로 이동, 두 쿠키 삭제 | `logoutAction.ts` |
| 8 | 7번 직전에 복사해 둔 `refreshToken`으로 Postman `POST /api/auth/refresh` | 401 "이미 만료 처리된 리프레시 토큰입니다." | 백엔드 저장소에서 제거됨 |
| 9 | `newlec` / `123`으로 로그인 → `accessToken` 삭제 → `/admin` | `/my`로 되돌아감, `accessToken`은 재발급되어 있음 | 재발급 성공 후 `role = USER` 판정 |
| 10 | 스프링 종료 → `accessToken` 삭제 → `/my` | `/login`으로 이동, 두 쿠키 삭제 | `refresh.ts`의 `catch` → null |

3번이 이 노트의 종착점이다. 사용자는 아무것도 하지 않았는데 만료된 열쇠가 새 열쇠로 바뀌어 있고, 그 열쇠로 스프링의 관리자 API까지 통과했다.

10번은 생각해 볼 거리다. 스프링이 잠시 내려간 사이에 들어온 사용자는 Refresh Token까지 잃고 로그인 페이지로 보내진다. "백엔드 장애 = 전원 로그아웃"이 지나치다고 느껴진다면, `refresh.ts`에서 네트워크 오류와 401을 구분해서 돌려주고 문지기가 네트워크 오류일 때는 쿠키를 지우지 않도록 바꿀 수 있다. 이번 노트에서는 단순함을 택했다.

### 4) 터미널에서 확인하기 (선택)

문지기의 재발급은 curl로도 볼 수 있다. 브라우저 없이 "Refresh Token 쿠키만" 들고 보호 경로에 들어가 본다.

```bash
# 스프링에서 리프레시 토큰만 받아 둔다
RT=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H 'Content-Type: application/json' -d '{"username":"admin","password":"123"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["refreshToken"])')

# accessToken 없이 refreshToken만 → 200, 응답에 Set-Cookie: accessToken=...
curl -s -o /dev/null -D - http://localhost:3000/admin -b "refreshToken=$RT" \
  | grep -i -E "^HTTP|^set-cookie"

# 위조된 refreshToken → 307 /login, 두 쿠키 삭제(빈 값의 Set-Cookie 두 개)
curl -s -o /dev/null -D - http://localhost:3000/my -b "accessToken=x; refreshToken=bad" \
  | grep -i -E "^HTTP|^location|^set-cookie"
```

---

## 10. 주의할 사항과 정리

### 1) 로그아웃 후에도 Access Token은 최대 30분 산다

5절 10번에서 봤듯이 스프링은 Access Token을 기억하지 않는다. 로그아웃이 막는 것은 재발급이고, 이미 발급된 Access Token은 남은 수명 동안 유효하다. 이것은 STATELESS 설계의 의도된 결과이며, Access Token 수명을 짧게 두는 이유다. 이 30분의 틈이 허용되지 않는 서비스라면 블랙리스트(또는 Redis)를 두어야 한다.

### 2) 저장소가 메모리다

`RefreshTokenStore`는 스프링을 재시작하면 비워진다. 재시작 후 브라우저에 남은 `refreshToken` 쿠키는 "모르는 토큰"이라 재발급이 거절되고, 문지기가 두 쿠키를 지운 뒤 로그인 페이지로 보낸다. 개발 중에는 이것이 정상이다. 운영에서는 DB 테이블이나 Redis로 옮긴다. 옮길 때 바뀌는 것은 `RefreshTokenStore` 안쪽뿐이고 `AuthService`는 그대로다.

### 3) Refresh Token 자체는 갱신하지 않는다

이번 구현에서 `/refresh`는 Access Token만 새로 주고 Refresh Token은 그대로 돌려준다. 즉 14일이 지나면 어쨌든 다시 로그인해야 한다. 재발급 때마다 Refresh Token도 새로 발급하고 이전 것을 폐기하는 방식을 **Refresh Token Rotation**이라고 한다. 탈취된 Refresh Token이 한 번만 쓰이고 버려지므로 더 안전하지만, 프론트가 두 쿠키를 모두 갱신해야 하고 동시 요청 처리가 까다로워진다. 이번 노트의 범위 밖이다.

### 4) 한 계정은 한 곳에서만

`RefreshTokenStore`의 키가 아이디이므로, 같은 계정으로 다른 브라우저에서 로그인하면 먼저 로그인한 쪽의 Refresh Token은 덮어써진다. 먼저 로그인한 브라우저는 Access Token이 만료되는 시점에 재발급이 거절되어 로그아웃된다. 기기별 동시 로그인을 허용하려면 키를 토큰(또는 기기 식별자)으로 바꾸면 된다.

### 5) 문지기가 모든 페이지에서 돈다

`matcher`를 넓혔으므로 홈, 메뉴, 로그인 페이지에서도 문지기가 실행된다. 하지만 쿠키가 없거나 토큰이 멀쩡하면 `fetch` 없이 해독만 하고 끝나므로 비용은 거의 없다. 스프링을 부르는 것은 만료 + Refresh Token 있음일 때뿐이다.

### 6) 정리

| 원칙 | 구현한 곳 |
|---|---|
| Refresh Token은 재발급 창구에서만 받는다 | `JwtAuthenticationFilter`의 `role == null` 가드 |
| 서버는 발급한 Refresh Token을 기억한다 | `RefreshTokenStore`, `AuthService.refresh()` 2단계, `logout()` |
| 재발급은 문지기가 한다 | `proxy.ts` — 요청 쿠키 교체 + 응답 Set-Cookie |
| 쿠키 옵션은 한 곳에서 | `cookies.ts` — 로그인 액션과 문지기가 공유 |
| 서버 컴포넌트는 바뀌지 않는다 | `backendFetch`, `getSession`, `BackendCheck` 모두 그대로 |

### 7) 이번 노트에서 추가·수정된 파일

**백엔드 (추가)**

- `dto/auth/RefreshRequest.java`
- `security/jwt/RefreshTokenStore.java`
- `security/jwt/InvalidTokenException.java`

**백엔드 (수정)**

- `dto/auth/LoginResponse.java` — `refreshToken` 필드
- `service/AuthService.java` — 두 토큰 발급, `refresh()`, `logout()`, `toRole()`
- `controller/AuthController.java` — `/refresh`, `/logout`, `@ExceptionHandler`
- `security/jwt/JwtAuthenticationFilter.java` — `role == null` 가드

**프론트엔드 (추가)**

- `app/_lib/auth/env.ts`
- `app/_lib/auth/cookies.ts`
- `app/_lib/auth/refresh.ts`

**프론트엔드 (수정)**

- `app/_lib/auth/token.ts` — `REFRESH_TOKEN_COOKIE`
- `app/_lib/auth/backend.ts` — `BACKEND_URL`을 `env.ts`에서 가져옴
- `app/login/_components/LoginForm/loginAction.ts` — 두 쿠키 저장
- `app/_components/ProfileMenu/logoutAction.ts` — 백엔드 폐기 요청
- `proxy.ts` — 재발급, 넓어진 matcher

---

## 마무리

이번 노트로 사용자는 30분마다 로그인 화면을 보는 대신, 14일 동안 한 번 로그인한 상태로 서비스를 쓰게 되었다. 짧은 열쇠는 자주 바뀌고, 긴 열쇠는 재발급 창구에서만 쓰이며, 서버는 긴 열쇠를 기억하고 있다가 로그아웃하면 잊는다. 문지기는 만료된 열쇠를 발견하면 사용자 모르게 바꿔 준다.
