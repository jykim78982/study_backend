---
tags: [Next.js, 쿠키인증, JWT, BFF, ServerAction, proxy, HttpOnly, 미들웨어, 권한제어, 실습]
---

> 🔗 관련 노트: [[051_로그인 API 작업 코드 — AuthController, AuthService, DTO, In-Memory User, MenuController]] · [[050_스프링 부트 JWT 인증 구현 — JJWT 설정, JwtProvider, JwtAuthenticationFilter, SecurityConfig, 로그인 API]]

# Next.js와 스프링 백엔드로 구현하는 쿠키 기반 인증과 미들웨어 권한 제어

> **첨부 파일 안내**
> - `ncafe-prep-06-nextjs-cookie-auth.zip`: 현재 노트의 내용이 적용되기 **전** 상태의 프로젝트 파일이다. 이 노트를 보면서 실습해보고 싶은 사람은 그 파일을 다운로드 한 후 압축을 해제해서 사용하길 바란다.
> - `ncafe-lesson-06-nextjs-cookie-auth.zip`: 이 노트 전체가 **적용된** 파일이다. 전체가 적용된 결과를 확인하고 싶을 때 사용할 수 있다.

---

## 1. JWT 토큰을 생성하는 위치

웹 서비스를 만들 때 사용자가 누구인지 확인하는 과정인 인증과, 그 사용자가 특정 페이지에 들어갈 수 있는지 확인하는 권한 관리는 필수이다.

권한을 위해서 인증정보를 관리하는 방법은 서버에 저장하는 방법과 JWT 토큰으로 만들어서 클라이언트가 가지고 다니는 방법이 있다. 그 중에서 이번에는 JWT 토큰을 이용하는 인증/허가 방법을 알아보도록 하자.

JWT 토큰은 언제 사용하는 것일까? 이는 로그인 처리를 담당하는 서버와 실제 서비스나 데이터를 제공하는 서버가 따로 나누어져 있을 때 주로 사용한다. 로그인 성공 시 발급받은 토큰만 제시하면, 매번 서버의 회원 DB를 직접 조회하지 않고도 토큰 자체로 사용자의 신원을 증명하고 서비스를 이용할 수 있기 때문이다.

다시 말해서 자원을 제공하는 리소스 서버가 여러 개가 있을 때 유효한 방법이다. 그렇다면 인증 서버가 따로 없고 프론트엔드 서버와 백엔드 서버를 운영하는 환경에서 토큰을 발급하는 주체는 어디가 되면 좋을까? 그 주체는 단연코 백엔드에서 하는 것이 유리하다. 다만 편리성을 우선에 둔다면 프론트 서버에서 해도 무방하다.

가게를 하나 운영한다고 가정해 보자. 건물의 모든 열쇠를 만들고 손님의 신분을 확인하여 열쇠를 내어주는 본점 역할은 스프링 백엔드가 담당한다. 반면 손님이 눈으로 보는 안내 데스크와 방 입구 역할은 Next.js 프론트엔드가 담당한다.

이런 상황에서 Next.js가 직접 열쇠(토큰)를 새로 만들어 손님에게 내어주면 본점의 장부와 맞지 않는 문제가 생긴다. 따라서 열쇠는 스프링 백엔드에서 발급받고, Next.js는 그 열쇠를 안전한 주머니(쿠키)에 담아 두었다가 방문자가 방에 들어갈 때 입장표를 검사하는 문지기(미들웨어) 역할만 담당하는 구조가 가장 안전하고 명확하다.

이전 노트에서는 스프링 백엔드에 로그인 API(`POST /api/auth/login`)를 만들고, Postman으로 토큰을 발급받아 보호된 API를 호출하는 것까지 확인했다. 이제 열쇠를 찍어내는 본점은 완성된 셈이다.

이번 노트에서는 Next.js 프론트엔드를 이 본점에 연결한다. 사용자가 로그인 화면에서 아이디와 비밀번호를 입력하면, Next.js가 스프링에서 토큰을 받아 안전한 곳에 보관하고, 이후 보호된 페이지(`/my`, `/admin`)에 들어갈 때마다 그 토큰을 확인하도록 만든다.

이 노트에서는 다음 순서로 진행한다.

1. 토큰을 어디에 두고 누가 검사할지 구조를 먼저 정한다.
2. 그 구조에 맞게 백엔드 두 줄을 손본다 (토큰 속 역할 이름).
3. 프론트엔드에 토큰·세션·백엔드 호출 공통 모듈을 만든다.
4. 로그인 Server Action과 로그인 폼을 만든다.
5. 헤더가 로그인 상태를 보여주고, 로그아웃이 되게 한다.
6. 문지기(`proxy.ts`)로 `/my`, `/admin`을 보호한다.
7. 관리자 화면에서 쿠키의 토큰이 실제로 스프링까지 통하는지 확인한다.

---

## 1. 토큰은 어디에 두고, 누가 검사하는가

코드를 쓰기 전에 구조부터 정해야 한다. 이 구조가 이후 모든 파일의 위치와 모양을 결정하기 때문이다.

### 1) 세 명의 참여자

로그인 이후의 세계에는 참여자가 셋이다.

| 참여자 | 역할 | 비유 |
|---|---|---|
| 스프링 백엔드 | 아이디·비밀번호를 확인하고 토큰을 발급한다. 토큰이 진짜인지(서명) 검사하는 비밀키를 유일하게 가진다. | 열쇠를 만들고 진품 여부를 판별하는 본점 |
| Next.js 서버 | 브라우저 대신 스프링을 호출하고, 받은 토큰을 쿠키에 넣어 준다. 보호된 페이지에 들어가기 전 쿠키를 확인한다. | 안내 데스크와 각 방 입구의 문지기 |
| 브라우저 | 화면을 보여주고, 쿠키를 자동으로 들고 다닌다. 토큰 내용을 볼 수 없다. | 열쇠가 든 주머니를 찬 손님 |

### 2) 세 가지 원칙

이 노트의 모든 코드는 다음 세 원칙에서 나온다.

**원칙 1. 토큰은 브라우저 자바스크립트가 만질 수 없는 곳에 둔다.**  
localStorage나 리액트 상태에 토큰을 두면, 페이지에 악성 스크립트가 하나라도 끼어드는 순간(XSS) 토큰이 그대로 빠져나간다. 반면 HttpOnly 쿠키는 `document.cookie`로 읽을 수 없고, 브라우저가 같은 사이트 요청에 자동으로 실어 보낼 뿐이다. 그래서 토큰은 반드시 HttpOnly 쿠키에 둔다.

**원칙 2. 비밀키는 스프링만 가진다.**  
토큰의 서명을 검증하려면 비밀키가 필요하다. 이 키를 프론트엔드에도 복사하면 유출될 수 있는 장소가 두 배가 된다. 그래서 Next.js는 토큰을 읽기만 한다. 토큰 안의 "누구인지(sub)", "역할(role)", "언제 만료되는지(exp)"를 꺼내 화면 이동을 결정할 뿐이고, 진짜 판정(이 토큰이 위조되지 않았는가)은 스프링이 요청마다 401/403으로 내린다.

**원칙 3. 스프링을 부르는 것은 Next.js 서버뿐이다.**  
브라우저가 스프링(`localhost:8080`)을 직접 `fetch`하지 않는다. 로그인은 Server Action이, 데이터 조회는 서버 컴포넌트가 쿠키에서 토큰을 꺼내 `Authorization: Bearer` 헤더로 스프링에 전달한다. 이렇게 하면 두 가지가 공짜로 따라온다.

- CORS 설정이 필요 없다. 브라우저에서 다른 출처(8080)로 요청이 나가지 않기 때문이다.
- 토큰이 브라우저로 내려가는 자바스크립트 번들에 절대 섞이지 않는다.

이 구조를 흔히 BFF(Backend For Frontend) 라고 부른다. 브라우저 입장에서는 Next.js 서버가 유일한 백엔드다.

### 3) 전체 흐름

```
① 로그인 폼 제출
        │
        ▼
② Next.js Server Action
   POST http://localhost:8080/api/auth/login
        │
        ▼
③ 스프링 AuthService → JWT 발급 (role: "USER" | "ADMIN")
        │
        ▼
④ Next.js가 accessToken을 HttpOnly 쿠키(accessToken)에 저장
        │
        ▼
⑤ /my, /admin 접근 시 proxy.ts가 쿠키를 읽어 라우팅 판단
        │  (서명 검증 없음 — 화면 이동용 1차 관문)
        ▼
⑥ 서버 컴포넌트 / backendFetch
   Authorization: Bearer <token> 으로 스프링 보호 API 호출
        │
        ▼
⑦ JwtAuthenticationFilter가 서명 검증 + ROLE_ 복원 → 최종 401/403/200
```

---

## 2. 백엔드 손보기 — 토큰에 담는 역할 이름

이전 노트의 AuthService는 인증 객체에서 꺼낸 권한 문자열을 그대로 토큰에 넣었다. 그런데 `User.builder().roles("ADMIN")`으로 만든 사용자의 권한 문자열은 스프링 보안 내부적으로 사용하는 권한이름은 `"ADMIN"`이 아니라 `"ROLE_ADMIN"` 이다. 스프링 시큐리티가 `roles()`에 넘긴 값 앞에 자동으로 `ROLE_` 접두어를 붙이기 때문이다.

지금까지는 백엔드 혼자 토큰을 주고받았기 때문에 문제가 없었다. 백엔드가 토큰을 만들 때 `ROLE_ADMIN`을 넣고, 검사할 때도 `ROLE_ADMIN`을 찾으니 아무런 탈이 나지 않았다.

하지만 이제는 토큰을 Next.js 프론트엔드도 함께 읽는다. Next.js 문지기가 `/admin` 페이지 접근을 막으려면 토큰에 담긴 역할(role)을 확인해야 한다. 이때 토큰에 `ROLE_ADMIN`이라는 값이 들어 있으면, Next.js 프론트엔드 코드도 스프링 시큐리티가 앞에 `ROLE_`을 붙인다는 사정을 알고 있어야 한다.

```ts
// 이렇게 쓰고 싶지 않다 — Next.js가 스프링 사정을 알아야 한다
if (payload.role !== "ROLE_ADMIN") ...
```

토큰은 두 시스템이 공유하는 공용 데이터다. 공용 데이터에는 한쪽의 내부 규약을 넣지 않는 것이 경계를 깔끔하게 유지하는 길이다. 그래서 이렇게 정리한다.

- 토큰에는 `"USER"`, `"ADMIN"`처럼 순수한 역할 이름만 담는다.
- `ROLE_` 접두어는 스프링이 토큰을 다시 읽는 지점(`JwtAuthenticationFilter`)에서 붙인다.

### 1) AuthService — 접두어를 떼고 담기

한 가지 더 고려할 점이 있다. 이전 노트에서 admin 계정을 `.roles("USER", "ADMIN")`으로 만들었기 때문에 권한이 두 개다. `findFirst()`는 정렬 순서에 따라 운 좋게 `ROLE_ADMIN`을 돌려주지만, 그런 우연에 기대지 말고 "ADMIN이 있으면 ADMIN"이라고 명시적으로 고른다.

> 원문 바로잡기 — 위 문단은 `admin` 계정이 `.roles("USER", "ADMIN")`이라고 전제하는데, 이 코드는 **050(수업 적용본)** 에만 있다. 051의 `SecurityConfig`는 `admin`을 `.roles("ADMIN")` 하나로 만든다. 어느 쪽이든 아래 코드는 동작한다. 권한이 `ROLE_ADMIN` 하나여도 `roles.contains("ADMIN")`이 `true`가 되기 때문이다.

경로: `backend/src/main/java/com/ncafe/backend/service/AuthService.java`

```java
package com.ncafe.backend.service;

import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.stereotype.Service;

import java.util.List;

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
        // -> 권한 정보 Grant..
        // -> 인증 Authentication
        // -> 보안객체 홀더 SercurityContextHolder

        String username = authenticate.getName();

        // 토큰은 프론트엔드도 읽는 "공용 데이터"이므로 스프링 내부 규약인 "ROLE_" 접두어는 떼어 낸다.
        // (접두어는 JwtAuthenticationFilter가 토큰을 다시 읽을 때 붙인다)
        List<String> roles = authenticate.getAuthorities().stream()
                        .map(GrantedAuthority::getAuthority)
                        .map(authority -> authority.replaceFirst("^ROLE_", ""))
                        .toList();

        // admin 계정은 USER와 ADMIN을 모두 가지므로, 더 높은 권한인 ADMIN을 대표 역할로 담는다.
        String role = roles.contains("ADMIN") ? "ADMIN" : roles.stream().findFirst().orElse("USER");

        // authentication 정보를 JWT 페이로드에 담아서 리턴
        String token = jwtProvider.createAccessToken(username, role);
               
        return LoginResponse.builder()
                .accessToken(token)
                .tokenType("Bearer")
                .build();
    } 
}
```

> 원문 바로잡기 — 코드 안의 `// -> 보안객체 홀더 SercurityContextHolder` 주석은 `authenticate()`가 홀더에 인증 정보를 담는 것처럼 읽히지만 그렇지 않다(`Sercurity`는 `Security`의 오타다). `authenticate()`는 인증된 `Authentication`을 **돌려줄 뿐**이고, `SecurityContextHolder`에 담는 것은 요청마다 `JwtAuthenticationFilter`가 한다. 그래서 로그인 API에서는 그 객체에서 아이디와 역할만 꺼내 토큰을 만든다.

### 2) JwtAuthenticationFilter — 읽을 때 접두어 복원

필터에서 권한 객체를 만드는 한 줄만 바뀐다.

경로: `backend/src/main/java/com/ncafe/backend/security/jwt/JwtAuthenticationFilter.java`

```java
            // 토큰에서 사용자 아이디와 권한 추출
            String username = jwtProvider.getUsername(token);
            String role = jwtProvider.getRole(token);

            // 스프링 시큐리티 권한 객체 생성
            // 토큰에는 "ADMIN"처럼 순수한 역할 이름만 들어 있다.
            // hasRole("ADMIN")은 "ROLE_ADMIN"을 찾으므로 여기서 접두어를 다시 붙인다.
            SimpleGrantedAuthority authority = new SimpleGrantedAuthority("ROLE_" + role);
```

이제 토큰의 `role` 클레임은 `"ADMIN"`이고, 스프링 안에서는 `ROLE_ADMIN` 권한으로 복원되어 `hasRole("ADMIN")`과 그대로 맞는다. 백엔드를 다시 실행한 뒤 Postman으로 `admin` / `123` 로그인 → 토큰을 jwt.io에 붙여 넣어 `"role": "ADMIN"`으로 바뀌었는지 확인하고 넘어가자.

---

## 3. 프론트엔드 공통 모듈 — app/_lib/auth/

토큰을 다루는 코드는 로그인, 헤더, 문지기, 백엔드 호출 등 여러 곳에서 쓰인다. 흩어 놓지 않고 `app/_lib/auth/` 한 곳에 모은다. 파일은 셋이고, 각자 하는 일이 다르다.

| 파일 | 하는 일 | 실행되는 곳 |
|---|---|---|
| `token.ts` | 토큰 문자열을 읽는다 (해독, 만료 확인). 검증은 하지 않는다. | 서버 컴포넌트, `proxy.ts` 모두 |
| `session.ts` | 쿠키에서 토큰을 꺼내 "지금 누가 로그인했나"를 알려준다. | 서버 전용 (`cookies()` 사용) |
| `backend.ts` | 토큰을 Authorization 헤더에 실어 스프링을 호출한다. | 서버 전용 |

### 1) token.ts — 토큰을 읽는 도구

경로: `frontend/app/_lib/auth/token.ts`

```ts
/**
 * JWT 토큰을 "읽기만" 하는 유틸리티.
 *
 * 서명 검증은 하지 않는다. 비밀키는 스프링 백엔드만 가지고 있고,
 * 프론트엔드는 토큰 안의 정보(누구인지, 언제 만료되는지)를 라우팅 판단에만 쓴다.
 * 진짜 검증은 백엔드의 JwtAuthenticationFilter가 요청마다 수행한다.
 *
 * proxy.ts와 서버 컴포넌트 양쪽에서 쓰므로 Node 전용 API(Buffer)는 피한다.
 */

/** 브라우저 쿠키에 저장할 때 쓰는 이름 */
export const ACCESS_TOKEN_COOKIE = "accessToken";

/** 백엔드 JwtProvider.createAccessToken()이 토큰에 담는 내용 */
export type TokenPayload = {
  sub: string; // 사용자 아이디
  role: string; // "USER" | "ADMIN" (ROLE_ 접두어 없음)
  iat: number; // 발급 시각 (초)
  exp: number; // 만료 시각 (초)
};

/** JWT의 두 번째 조각(payload)을 base64url → JSON 으로 해독한다. 형식이 이상하면 null */
export function decodeToken(token: string): TokenPayload | null {
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;
    const base64 = payload
      .replace(/-/g, "+")
      .replace(/_/g, "/")
      .padEnd(Math.ceil(payload.length / 4) * 4, "=");
    const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
    const json = JSON.parse(new TextDecoder().decode(bytes)) as Partial<TokenPayload>;
    if (typeof json.sub !== "string" || typeof json.exp !== "number") return null;
    return { sub: json.sub, role: json.role ?? "USER", iat: json.iat ?? 0, exp: json.exp };
  } catch {
    return null;
  }
}

/** 만료 여부. exp는 초 단위, Date.now()는 밀리초 단위라는 점에 주의 */
export function isExpired(payload: TokenPayload): boolean {
  return payload.exp * 1000 <= Date.now();
}
```

왜 서명을 검증하지 않는가? 1절의 원칙 2 때문이다. 검증하려면 비밀키가 필요하고, 프론트엔드에 비밀키를 두고 싶지 않다. 여기서 하는 일은 "쿠키에 든 토큰이 겉보기에 멀쩡하고 아직 만료 전인가"를 확인해 화면 이동을 결정하는 것뿐이다. 누군가 토큰을 위조해 `role: "ADMIN"`을 넣더라도, 관리자 화면 껍데기까지는 볼 수 있을지언정 데이터는 스프링이 403으로 거절한다.

왜 Buffer가 아니라 `atob`을 쓰는가? 이 파일은 `proxy.ts`에서도 쓰인다. `atob`과 `TextDecoder`는 Node와 Edge 런타임 어디서나 동작하는 웹 표준 API라 환경을 가리지 않는다.

`exp`는 초, `Date.now()`는 밀리초다. `isExpired()`에서 `* 1000`을 빠뜨리면 모든 토큰이 만료된 것으로 판정된다.

### 2) session.ts — 지금 누가 로그인했나

경로: `frontend/app/_lib/auth/session.ts`

```ts
import { cookies } from "next/headers";
import { ACCESS_TOKEN_COOKIE, decodeToken, isExpired } from "./token";

/**
 * 서버 컴포넌트·Server Action에서 "지금 로그인한 사람"을 알아내는 함수.
 *
 * cookies()는 서버에서만 호출할 수 있다. HttpOnly 쿠키는 브라우저 자바스크립트가
 * 읽을 수 없으므로, 세션 판단은 항상 서버에서 끝내고 결과(이름, 역할)만 화면에 내려보낸다.
 */
export type Session = {
  username: string;
  role: string;
  isAdmin: boolean;
  /** 백엔드 호출 시 Authorization 헤더에 실어 보낼 원본 토큰 */
  token: string;
};

export async function getSession(): Promise<Session | null> {
  const token = (await cookies()).get(ACCESS_TOKEN_COOKIE)?.value;
  if (!token) return null;

  const payload = decodeToken(token);
  if (!payload || isExpired(payload)) return null;

  return {
    username: payload.sub,
    role: payload.role,
    isAdmin: payload.role === "ADMIN",
    token,
  };
}
```

`cookies()`는 `next/headers`에서 가져오는 서버 전용 함수다. HttpOnly 쿠키는 브라우저 자바스크립트가 읽을 수 없으므로, "로그인했는가"라는 판단 자체를 서버에서 끝내고 결과(이름, 역할)만 화면에 내려보낸다. 원본 `token`을 함께 돌려주는 이유는 3)에서 스프링을 호출할 때 헤더에 실어야 하기 때문인데, 이 값은 서버 컴포넌트 안에서만 쓰고 클라이언트 컴포넌트에 prop으로 넘기지 않는다.

### 3) backend.ts — 스프링 호출 창구

경로: `frontend/app/_lib/auth/backend.ts`

```ts
import { getSession } from "./session";

/**
 * 스프링 백엔드 주소. 브라우저에 노출될 필요가 없으므로 NEXT_PUBLIC_ 접두어를 붙이지 않는다.
 * .env.local 에 BACKEND_URL=http://localhost:8080 처럼 설정한다. 없으면 로컬 기본값을 쓴다.
 */
export const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8080";

/**
 * 쿠키의 토큰을 Authorization: Bearer 헤더로 바꿔 백엔드를 호출한다.
 *
 * 브라우저 → Next.js 서버 → 스프링 순서로만 통신한다(BFF 구조).
 * 브라우저가 스프링을 직접 부르지 않으므로 CORS 설정이 필요 없고,
 * 토큰이 클라이언트 자바스크립트에 노출되지 않는다.
 */
export async function backendFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const session = await getSession();
  const headers = new Headers(init.headers);
  if (session) headers.set("Authorization", `Bearer ${session.token}`);
  return fetch(`${BACKEND_URL}${path}`, { ...init, headers, cache: "no-store" });
}
```

왜 `NEXT_PUBLIC_` 접두어를 붙이지 않는가? Next.js는 `NEXT_PUBLIC_`으로 시작하는 환경 변수만 브라우저 번들에 넣는다. 스프링 주소는 Next.js 서버만 알면 되므로 접두어 없이 두어 브라우저에 노출되지 않게 한다.

`frontend/.env.example` 파일을 만들어 설정 항목을 문서화한다. 실제 값은 `.env.local`에 두고, `.env.local`은 git에 올리지 않는다.

경로: `frontend/.env.example`

```env
# 스프링 백엔드 주소 (서버에서만 사용, 브라우저에 노출되지 않음)
BACKEND_URL=http://localhost:8080
```

`frontend/.gitignore`에는 `.env*`가 이미 있어 `.env.example`까지 무시되므로, 예외 한 줄을 추가한다.

경로: `frontend/.gitignore`

```gitignore
# env files (can opt-in for committing if needed)
.env*
!.env.example
```

---

## 4. 로그인 — Server Action과 폼

### 1) Server Action이 로그인을 맡는 이유

로그인은 "스프링에 POST → 토큰 받기 → HttpOnly 쿠키 설정"이다. 마지막 단계가 핵심이다. HttpOnly 쿠키는 서버가 `Set-Cookie` 응답 헤더로만 만들 수 있고, 브라우저 자바스크립트로는 만들 수 없다. 따라서 로그인 처리는 반드시 Next.js 서버에서 실행되어야 한다.

Next.js App Router에서 서버에서 실행되는 함수를 폼에 직접 연결하는 방법이 Server Action이다. 파일 맨 위에 `"use server"`를 선언하면, 그 파일의 함수는 서버에서만 실행되고 클라이언트 컴포넌트는 그 함수를 import해 `<form action={...}>`에 넘길 수 있다. 별도의 `route.ts`(API 라우트)를 만들 필요가 없다.

### 2) loginAction.ts

콜로케이션 규칙대로 로그인 폼 컴포넌트 폴더(`app/login/_components/LoginForm/`) 안에 둔다. 이전에 있던 목업 파일 `loginApi.ts`와 `useLoginForm.ts`는 삭제한다.

경로: `frontend/app/login/_components/LoginForm/loginAction.ts`

```ts
"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { BACKEND_URL } from "@/app/_lib/auth/backend";
import { ACCESS_TOKEN_COOKIE, decodeToken } from "@/app/_lib/auth/token";

/** useActionState가 주고받는 상태. 성공하면 redirect 되므로 실패 메시지만 담는다 */
export type LoginState = { error: string | null };

/**
 * 로그인 Server Action.
 * 1. 폼 값을 꺼내 스프링의 POST /api/auth/login 으로 보낸다.
 * 2. 돌려받은 accessToken을 HttpOnly 쿠키에 저장한다.
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

  const { accessToken } = (await res.json()) as { accessToken: string; tokenType: string };

  // 2. HttpOnly 쿠키에 저장 — 쿠키 수명은 토큰 만료 시각에 맞춘다
  const payload = decodeToken(accessToken);
  const maxAge = payload ? Math.max(0, payload.exp - Math.floor(Date.now() / 1000)) : 60 * 30;

  (await cookies()).set(ACCESS_TOKEN_COOKIE, accessToken, {
    httpOnly: true, // 자바스크립트로 접근 불가 → XSS로 탈취되지 않음
    secure: process.env.NODE_ENV === "production", // 운영에서는 HTTPS에서만 전송
    sameSite: "lax", // 다른 사이트에서 시작된 POST에는 실리지 않음
    path: "/",
    maxAge,
  });

  // 3. 원래 가려던 곳으로. 외부 주소로 보내지 않도록 "/"로 시작하는 경로만 허용
  const safeNext = next.startsWith("/") && !next.startsWith("//") ? next : "/";
  redirect(safeNext);
}
```

코드의 주요 부분을 살펴본다.

- **함수 시그니처 (`prevState`, `formData`)**: 뒤에서 쓸 `useActionState` 훅이 요구하는 모양이다. 첫 인자는 직전 상태, 둘째는 폼 데이터다. 성공하면 `redirect()`로 떠나 버리므로 돌려주는 상태에는 실패 메시지만 있으면 된다.
- **`BACKEND_URL/api/auth/login`**: 이전 노트에서 만든 스프링 엔드포인트다. 응답 JSON의 필드 이름도 스프링 `LoginResponse`의 `accessToken`과 맞춰야 한다.
- **401·403을 "아이디 또는 비밀번호 오류"로 해석**: 스프링은 `BadCredentialsException`을 `ExceptionTranslationFilter`가 받아 403으로 돌려준다(아직 `AuthenticationEntryPoint`를 따로 두지 않았으므로). 두 코드를 모두 잡아 둔다.
- **쿠키 옵션**
  - `httpOnly: true` — 원칙 1. 자바스크립트에서 읽을 수 없다.
  - `secure: production`에서만 — 운영에서는 HTTPS로만 전송한다. 개발 중(`next dev`)에는 `http://localhost`에서도 쿠키가 붙어야 하므로 끈다.
  - `sameSite: "lax"` — 다른 사이트에서 시작된 POST 요청에는 쿠키가 실리지 않는다. CSRF를 막는 1차 방어선이다.
  - `maxAge` — 토큰의 `exp`에서 계산해 쿠키와 토큰의 수명을 같게 맞춘다. 토큰은 만료됐는데 쿠키만 남아 있는 상황을 줄인다.
- **`safeNext`**: 문지기가 `?next=/my`처럼 "원래 가려던 곳"을 붙여 준다. 그런데 이 값이 `https://evil.com`이면 로그인 직후 외부 사이트로 튕기는 오픈 리다이렉트 취약점이 된다. `/`로 시작하는 내부 경로만 허용한다.

### 3) LoginForm.tsx — useActionState로 연결

경로: `frontend/app/login/_components/LoginForm/LoginForm.tsx`

```tsx
"use client";

import Link from "next/link";
import { useActionState } from "react";
import { useSearchParams } from "next/navigation";
import { login, type LoginState } from "./loginAction";
import styles from "./LoginForm.module.css";

const initialState: LoginState = { error: null };

export function LoginForm() {
  // [현재 상태, 폼에 연결할 액션, 진행 중 여부]
  const [state, formAction, pending] = useActionState(login, initialState);

  // proxy가 붙여 준 ?next=/my 같은 값. 로그인 후 돌아갈 곳
  const next = useSearchParams().get("next") ?? "/";

  return (
    <div className={styles.wrap}>
      <form className={styles.form} action={formAction} noValidate>
        <input type="hidden" name="next" value={next} />

        <label className={styles.field}>
          <span>아이디</span>
          <input className="input" name="username" autoComplete="username" placeholder="newlec" required autoFocus />
        </label>

        <label className={styles.field}>
          <span>비밀번호</span>
          <input className="input" type="password" name="password" autoComplete="current-password" placeholder="••••••••" required />
        </label>

        {state.error && (
          <p className={styles.error} role="alert">⚠ {state.error}</p>
        )}

        <button type="submit" className="btn btnPrimary btnLg" disabled={pending}>
          {pending ? "로그인 중…" : "로그인"}
        </button>
      </form>

      <p className={styles.foot}>
        아직 멤버가 아니세요? <Link href="/signup">회원가입</Link>
      </p>
      <p className={`mono ${styles.hint}`}>테스트 계정: newlec / 123 · admin / 123</p>
    </div>
  );
}
```

- `useActionState(login, initialState)`: 리액트 19 훅이다. `[현재 상태, 폼에 넘길 액션, 진행 중 여부]`를 돌려준다. 폼을 제출하면 `login(이전상태, FormData)`가 서버에서 실행되고, 그 반환값이 `state`가 된다.
- `<form action={formAction}>`: 자바스크립트가 켜져 있으면 페이지 이동 없이 서버 액션을 호출한다. 꺼져 있어도 일반 POST로 동작한다(점진적 향상).
- `pending`: 서버와 통신 중이면 `true`다. 버튼을 비활성화해 중복 제출을 막는다.
- `useSearchParams()`로 `next` 읽기: 문지기가 붙인 `?next=...`를 숨은 필드로 폼에 넣어 Server Action까지 전달한다.

스타일 파일은 사용하는 클래스만 남긴다.

경로: `frontend/app/login/_components/LoginForm/LoginForm.module.css`

```css
.wrap { display: flex; flex-direction: column; gap: 18px; }
.form { display: flex; flex-direction: column; gap: 14px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field span { font-size: 13px; font-weight: 700; color: var(--ink-2); }
.error { padding: 10px 14px; background: var(--danger-soft); color: var(--danger); border-radius: var(--radius-sm); font-size: 13px; font-weight: 600; }
.foot { font-size: 14px; color: var(--muted); text-align: center; }
.foot a { color: var(--brand); font-weight: 700; }
.hint { font-size: 11px; color: var(--muted); text-align: center; opacity: 0.8; }
```

### 4) page.tsx — Suspense로 감싸기

경로: `frontend/app/login/page.tsx`

```tsx
import type { Metadata } from "next";
import { Suspense } from "react";
import { AuthShell } from "@/app/_components/AuthShell";
import { LoginForm } from "./_components/LoginForm";

export const metadata: Metadata = { title: "로그인" };

export default function LoginPage() {
  return (
    <AuthShell
      eyebrow="login"
      title={<>다시 오셨군요,<br />자리는 그대로예요</>}
      lead="로그인하면 좋아요한 메뉴와 장바구니, 스탬프가 이어집니다."
      asideTitle="멤버가 되면"
      asideItems={[
        { icon: "☕", text: "방문마다 스탬프, 10잔마다 무료 음료" },
        { icon: "🪑", text: "포커스 존·팀 룸 사전 예약" },
        { icon: "🧑‍💻", text: "모각코 · 피칭 나이트 우선 신청" },
        { icon: "🎟", text: "뉴렉처 수강생 10% 할인" },
      ]}
      asideQuote={{ quote: "로그인 버튼 누르는 순간부터 커피가 내려지기 시작합니다. 농담 아니에요.", by: "new cafe 바리스타" }}
    >
      {/* LoginForm은 useSearchParams()를 쓰므로 Suspense로 감싼다 (정적 셸 + 요청 시 스트리밍) */}
      <Suspense fallback={<div className="skeleton" style={{ height: 260, borderRadius: 14 }} />}>
        <LoginForm />
      </Suspense>
    </AuthShell>
  );
}
```

왜 Suspense가 필요한가? 이 프로젝트는 `next.config.ts`에서 `cacheComponents: true`를 켜 두었다. 이 모드에서 Next.js는 페이지를 빌드 시점에 최대한 미리 렌더링(정적 셸)하고, 요청이 와야만 알 수 있는 부분(쿠키, 쿼리스트링 등)은 Suspense 경계 안에서 요청 시점에 스트리밍한다. `useSearchParams()`는 요청 시점 데이터이므로 Suspense 없이 쓰면 빌드가 실패한다. `fallback`은 정적 셸에 들어가는 자리 표시자다.

---

## 5. 헤더에 로그인 상태 반영하고 로그아웃하기

### 1) 왜 헤더를 둘로 나누는가

기존 SiteHeader는 클라이언트 컴포넌트(`"use client"`)였고, 목업 함수로 "항상 로그인됨"이라고 가정했다. 이제 진짜 세션을 읽어야 하는데, 세션은 쿠키에 있고 쿠키는 서버에서만 읽을 수 있다(`cookies()`). 그런데 헤더에는 스크롤 감지, 드롭다운 열기 같은 브라우저 상호작용도 있어서 클라이언트 컴포넌트여야 한다.

해법은 역할을 둘로 나누는 것이다.

| 컴포넌트 | 종류 | 하는 일 |
|---|---|---|
| `SiteHeader` | 서버 | `getSession()`으로 쿠키를 읽고, 화면에 필요한 값(`username`, `role`, `isAdmin`)만 골라 뷰에 넘긴다. 토큰 원본은 여기서 끊긴다. |
| `SiteHeaderView` | 클라이언트 | 넘겨받은 값으로 그린다. 상호작용을 담당한다. |

서버 컴포넌트가 클라이언트 컴포넌트에 prop을 넘기는 것은 자유롭지만, 그 prop은 브라우저로 직렬화되어 내려간다. 그래서 `token`은 넘기지 않고 이름과 역할만 넘긴다.

### 2) siteHeaderApi.ts — 목업 세션 제거

경로: `frontend/app/_components/SiteHeader/siteHeaderApi.ts`

```ts
import { cartItems } from "@/app/_mocks/session";

/** 장바구니 수량 (목업). 로그인 상태는 app/_lib/auth/session.ts 의 getSession()이 담당 */
export function getCartCount(): number {
  return cartItems.reduce((sum, item) => sum + item.quantity, 0);
}
```

### 3) SiteHeader.tsx — 서버 컴포넌트

경로: `frontend/app/_components/SiteHeader/SiteHeader.tsx`

```tsx
import { getSession } from "@/app/_lib/auth/session";
import { getCartCount } from "./siteHeaderApi";
import { SiteHeaderView } from "./SiteHeaderView";

/**
 * 서버 컴포넌트. 쿠키에서 세션을 읽어 화면용 데이터만 클라이언트 뷰에 넘긴다.
 * 토큰 원본은 여기서 끊기고 브라우저로 내려가지 않는다.
 */
export async function SiteHeader() {
  const session = await getSession();
  return (
    <SiteHeaderView
      user={session ? { username: session.username, role: session.role, isAdmin: session.isAdmin } : null}
      cartCount={getCartCount()}
    />
  );
}

/** Suspense fallback — 세션을 아직 모르는 상태의 헤더 (로고·내비만) */
export function SiteHeaderSkeleton() {
  return <SiteHeaderView user={null} cartCount={0} loading />;
}
```

### 4) SiteHeaderView.tsx — 클라이언트 컴포넌트

기존 `SiteHeader.tsx`의 화면 코드를 이 파일로 옮기고, 세션 대신 `user` prop을 받도록 바꾼 것이다.

경로: `frontend/app/_components/SiteHeader/SiteHeaderView.tsx`

```tsx
"use client";

import Link from "next/link";
import styles from "./SiteHeader.module.css";
import { useSiteHeader } from "./useSiteHeader";
import { ProfileMenu } from "@/app/_components/ProfileMenu";

export type HeaderUser = { username: string; role: string; isAdmin: boolean };

type Props = {
  user: HeaderUser | null;
  cartCount: number;
  /** 세션을 아직 읽는 중이면 로그인/프로필 영역을 비워 둔다 */
  loading?: boolean;
};

const navItems = [
  { href: "/menus", label: "메뉴" },
  { href: "/space", label: "공간" },
  { href: "/community", label: "커뮤니티" },
];

export function SiteHeaderView({ user, cartCount, loading = false }: Props) {
  const { menuOpen, setMenuOpen, scrolled, isActive } = useSiteHeader();

  return (
    <header className={`${styles.header} ${scrolled ? styles.scrolled : ""}`}>
      <div className={`container ${styles.inner}`}>
        <Link href="/" className={styles.logo} aria-label="new cafe 홈">
          <span className={styles.logoMark}>
            <span className={styles.steam} />
            <span className={styles.steam} />
            <span className={styles.cup} />
          </span>
          <span className={styles.logoText}>
            new<span className={styles.logoDot}>.</span>cafe
          </span>
        </Link>

        <nav className={styles.nav} aria-label="주요 메뉴">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`${styles.navLink} ${isActive(item.href) ? styles.active : ""}`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className={styles.actions}>
          {loading ? null : user ? (
            <ProfileMenu username={user.username} role={user.role} isAdmin={user.isAdmin} cartCount={cartCount} />
          ) : (
            <>
              <Link href="/login" className="btn btnGhost btnSm">로그인</Link>
              <Link href="/signup" className="btn btnPrimary btnSm">회원가입</Link>
            </>
          )}
          <button
            type="button"
            className={styles.burger}
            aria-label="메뉴 열기"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            <span /><span /><span />
          </button>
        </div>
      </div>

      {menuOpen && (
        <div className={styles.mobileMenu}>
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} className={styles.mobileLink}>{item.label}</Link>
          ))}
          {user ? (
            <>
              <Link href="/my" className={styles.mobileLink}>마이 대시보드</Link>
              <Link href="/my/likes" className={styles.mobileLink}>좋아요</Link>
              <Link href="/my/cart" className={styles.mobileLink}>장바구니</Link>
              {user.isAdmin && <Link href="/admin" className={styles.mobileLink}>관리자 대시보드</Link>}
            </>
          ) : (
            <>
              <Link href="/login" className={styles.mobileLink}>로그인</Link>
              <Link href="/signup" className={styles.mobileLink}>회원가입</Link>
            </>
          )}
        </div>
      )}
    </header>
  );
}

export { SiteHeader, SiteHeaderSkeleton } from "./SiteHeader";
```

### 5) layout.tsx — 헤더를 Suspense로 감싸기

경로: `frontend/app/layout.tsx`

```tsx
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";
import { SiteHeader, SiteHeaderSkeleton } from "./_components/SiteHeader";
import { SiteFooter } from "./_components/SiteFooter";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://new-cafe.com"),
  title: {
    default: "new cafe — 아이디어가 내려지는 곳",
    template: "%s | new cafe",
  },
  description:
    "뉴렉처와 함께하는 코워킹 카페. 커피 한 잔 옆에서 코딩을 배우고, 의견을 나누고, 프로젝트를 만들어 가는 곳.",
  openGraph: {
    title: "new cafe",
    description: "아이디어를 구현하고 싶은 사람들이 모이는 코워킹 카페",
    url: "https://new-cafe.com",
    siteName: "new cafe",
    locale: "ko_KR",
    type: "website",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ko" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        {/* 헤더는 쿠키(세션)를 읽으므로 Suspense로 감싼다.
            정적인 나머지 페이지는 먼저 내려가고, 로그인 상태가 결정된 헤더가 뒤따라 스트리밍된다. */}
        <Suspense fallback={<SiteHeaderSkeleton />}>
          <SiteHeader />
        </Suspense>
        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>{children}</div>
        <SiteFooter />
      </body>
    </html>
  );
}
```

4절과 같은 이유다. `SiteHeader`가 `cookies()`를 읽으므로 Suspense 경계가 필요하다. 덕분에 랜딩이나 메뉴 목록처럼 정적인 페이지는 빌드된 HTML이 먼저 내려가고, 로그인 여부가 결정된 헤더가 그 뒤를 따라 채워진다. `SiteHeaderSkeleton`은 그 짧은 순간에 보이는 "로그인 버튼이 아직 없는 헤더"다.

### 6) ProfileMenu.tsx — prop 이름 변경

목업 시절의 `nickname`, `email` 대신 토큰에서 얻을 수 있는 `username`, `role`을 받는다. 바뀌는 부분만 적는다.

경로: `frontend/app/_components/ProfileMenu/ProfileMenu.tsx`

```tsx
type Props = {
  username: string;
  role: string;
  isAdmin: boolean;
  cartCount?: number;
};

export function ProfileMenu({ username, role, isAdmin, cartCount = 0 }: Props) {
  const m = useProfileMenu();
  const sections = getProfileMenuSections(isAdmin, cartCount);
  const initial = username.slice(0, 1).toUpperCase();
  // ...

            <div className={styles.who}>
              <strong>{username}</strong>
              <span>{isAdmin ? "관리자" : "멤버"} · {role}</span>
            </div>
```

### 7) 로그아웃 — logoutAction.ts와 useProfileMenu.ts

로그아웃은 "쿠키를 지우는 것"이다. HttpOnly 쿠키는 서버만 지울 수 있으므로 이것도 Server Action이다.

경로: `frontend/app/_components/ProfileMenu/logoutAction.ts`

```ts
"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ACCESS_TOKEN_COOKIE } from "@/app/_lib/auth/token";

/** 로그아웃: 쿠키를 지우면 토큰이 사라지고, 다음 요청부터 비로그인 상태가 된다 */
export async function logout() {
  (await cookies()).delete(ACCESS_TOKEN_COOKIE);
  redirect("/login");
}
```

프로필 메뉴의 훅에서 목업 `logout()` 대신 이 Server Action을 호출한다. 폼이 아닌 버튼 클릭에서 호출하므로 `useTransition`으로 감싸 진행 중 상태를 얻는다.

경로: `frontend/app/_components/ProfileMenu/useProfileMenu.ts`

```ts
"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import { usePathname } from "next/navigation";
import { logout } from "./logoutAction";

export function useProfileMenu() {
  const [open, setOpen] = useState(false);
  const [loggingOut, startLogout] = useTransition();
  const ref = useRef<HTMLDivElement>(null);
  const pathname = usePathname();

  // 바깥 클릭 / ESC 로 닫기
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  // 라우트 이동 시 닫기
  useEffect(() => { setOpen(false); }, [pathname]);

  // Server Action 호출 — 쿠키 삭제 후 /login 으로 redirect 된다
  const handleLogout = () => startLogout(() => logout());

  return { open, setOpen, toggle: () => setOpen((v) => !v), ref, loggingOut, handleLogout, pathname };
}
```

Server Action 안의 `redirect("/login")`은 클라이언트에서 호출했을 때도 Next.js가 알아서 페이지를 이동시킨다.

---

## 6. 문지기 — proxy.ts

### 1) middleware.ts에서 proxy.ts로

Next.js 16부터 미들웨어 파일 규약의 이름이 `middleware.ts`에서 `proxy.ts`로 바뀌었다(함수 이름도 `proxy`). 기능은 같다. 기존 `frontend/middleware.ts`는 삭제하고 같은 위치에 `proxy.ts`를 만든다. `middleware.ts`를 남겨 두면 빌드 때 deprecated 경고가 뜬다.

### 2) 코드

경로: `frontend/proxy.ts`

```ts
import { NextResponse, type NextRequest } from "next/server";
import { ACCESS_TOKEN_COOKIE, decodeToken, isExpired } from "@/app/_lib/auth/token";

/**
 * 문지기. 보호된 페이지에 들어가기 직전에 쿠키의 토큰을 확인한다.
 *
 * - 토큰이 없거나 만료 → /login?next=원래경로 로 보낸다.
 * - /admin 은 role 이 ADMIN 일 때만 통과시킨다.
 *
 * 여기서는 서명을 검증하지 않는다(비밀키는 백엔드만 가진다).
 * 화면 껍데기에 들어가지 못하게 막는 1차 관문일 뿐이고,
 * 데이터 접근의 최종 판정은 백엔드가 401/403 으로 내린다.
 */
export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const token = request.cookies.get(ACCESS_TOKEN_COOKIE)?.value;
  const payload = token ? decodeToken(token) : null;
  const loggedIn = payload !== null && !isExpired(payload);

  if (!loggedIn) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname + search);
    const response = NextResponse.redirect(loginUrl);
    if (token) response.cookies.delete(ACCESS_TOKEN_COOKIE); // 만료·손상된 쿠키는 정리
    return response;
  }

  if (pathname.startsWith("/admin") && payload.role !== "ADMIN") {
    return NextResponse.redirect(new URL("/my", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/my/:path*", "/admin/:path*"],
};
```

- **`matcher`**: 이 두 경로 패턴에서만 문지기가 실행된다. `matcher`를 비우면 정적 파일 요청까지 전부 가로채므로 반드시 지정한다.
- **토큰이 없거나 만료 → `/login?next=원래경로`**: 로그인 후 돌아올 수 있게 원래 경로를 붙여 보낸다. 이 값이 4절의 `safeNext`로 이어진다.
- **깨진 쿠키 정리**: 만료되었거나 해독되지 않는 쿠키는 응답에서 지워 준다. 그러지 않으면 매 요청마다 같은 판정을 반복한다.
- **`/admin`은 `role === "ADMIN"`만**: 2절에서 토큰의 역할을 `"ADMIN"`으로 정리했기 때문에 이렇게 단순하게 비교할 수 있다. 관리자가 아니면 자기 대시보드(`/my`)로 보낸다.

### 3) 문지기가 하지 않는 일

문지기는 서명을 검증하지 않는다. 1절의 원칙 2다. 누군가 쿠키를 조작해 `role: "ADMIN"`을 넣으면 `/admin` 화면 껍데기까지는 들어올 수 있다. 하지만 그 화면이 보여주는 데이터는 전부 스프링에서 오고, 스프링은 서명이 맞지 않는 토큰을 403으로 거절한다. 문지기는 "빈손으로 가지 않게 하는" 1차 관문이고, 최종 판정은 항상 백엔드가 한다.

한 가지 더. Next.js 문서에 따르면 Server Action은 `proxy.ts`의 보호 범위 밖이다. Server Action은 별도 라우트가 아니라 "그 함수를 쓴 페이지로 가는 POST"로 처리되기 때문에, `matcher`에 없는 `/login` 페이지의 액션은 문지기를 거치지 않는다. 따라서 데이터를 바꾸는 Server Action을 만들 때는 액션 안에서 직접 `getSession()`으로 권한을 확인해야 한다. 이번 노트의 로그인·로그아웃 액션은 로그인 전 상태에서 호출되는 것이 정상이므로 해당하지 않는다.

> **추가 설명 — "문지기 밖"의 정확한 범위**: 문지기가 막아 주는지는 그 액션이 실행되는 **경로가 `matcher`에 있느냐**로 갈린다. `/admin/...` 페이지에서 호출한 액션은 그 경로로 가는 요청이라 문지기를 지나지만, `matcher`에 없는 경로에서 쓰인 액션은 지나지 않는다. 또 액션은 사실상 공개된 POST 엔드포인트라서 직접 호출될 수도 있다. 그래서 어느 쪽이든 **액션 안에서 `getSession()`으로 직접 확인**하는 것이 안전하다.

---

## 7. 끝까지 통하는지 확인 — 관리자 대시보드의 백엔드 호출

지금까지는 쿠키를 만들고 확인하는 코드였다. 마지막으로 쿠키의 토큰이 실제로 스프링의 보호된 API를 통과하는지 화면에서 보여주는 작은 위젯을 관리자 대시보드에 붙인다. 이전 노트에서 만든 `GET /api/admin/menus`(ADMIN 전용)를 호출한다.

### 1) backendCheckApi.ts

경로: `frontend/app/admin/_components/BackendCheck/backendCheckApi.ts`

```ts
import { backendFetch, BACKEND_URL } from "@/app/_lib/auth/backend";

export type BackendCheckResult =
  | { ok: true; status: number; menus: string[] }
  | { ok: false; status: number | null; message: string };

/** GET /api/admin/menus — ADMIN 토큰이 있어야 200. 토큰이 실제로 백엔드까지 통하는지 확인한다 */
export async function checkAdminMenus(): Promise<BackendCheckResult> {
  try {
    const res = await backendFetch("/api/admin/menus");
    if (!res.ok) return { ok: false, status: res.status, message: `백엔드가 ${res.status}로 거절했어요.` };
    return { ok: true, status: res.status, menus: (await res.json()) as string[] };
  } catch {
    return { ok: false, status: null, message: `백엔드(${BACKEND_URL})에 연결할 수 없어요.` };
  }
}
```

`backendFetch()`가 쿠키에서 토큰을 꺼내 `Authorization` 헤더를 붙여 준다. 이 파일 어디에도 토큰을 직접 다루는 코드가 없다는 점에 주목하자. 3절의 공통 모듈이 그 일을 한다.

### 2) BackendCheck.tsx

경로: `frontend/app/admin/_components/BackendCheck/BackendCheck.tsx`

```tsx
import { checkAdminMenus } from "./backendCheckApi";
import styles from "./BackendCheck.module.css";

/** 서버 컴포넌트. 쿠키의 토큰으로 백엔드 보호 API를 호출해 결과를 보여준다 */
export async function BackendCheck() {
  const result = await checkAdminMenus();
  return (
    <section className={`${styles.panel} ${result.ok ? styles.ok : styles.fail}`} aria-live="polite">
      <div className={styles.head}>
        <span className="eyebrow">backend</span>
        <strong>{result.ok ? "스프링 백엔드 연결됨" : "스프링 백엔드 연결 실패"}</strong>
        <code className="mono">GET /api/admin/menus → {result.status ?? "ERR"}</code>
      </div>
      {result.ok ? (
        <ul className={styles.list}>
          {result.menus.map((m) => <li key={m}>{m}</li>)}
        </ul>
      ) : (
        <p>{result.message}</p>
      )}
    </section>
  );
}
```

경로: `frontend/app/admin/_components/BackendCheck/BackendCheck.module.css`

```css
.panel { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 18px; border-radius: var(--radius); border: 1px solid var(--line); background: var(--surface); }
.ok { border-color: var(--accent); background: color-mix(in srgb, var(--accent-soft) 50%, var(--surface)); }
.fail { border-color: var(--danger); background: color-mix(in srgb, var(--danger-soft) 50%, var(--surface)); }
.head { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.head strong { font-size: 14px; }
.head code { font-size: 12px; color: var(--muted); }
.list { list-style: none; display: flex; gap: 6px; flex-wrap: wrap; }
.list li { padding: 4px 10px; border-radius: 999px; background: var(--surface); border: 1px solid var(--line); font-size: 12px; font-weight: 600; }
.panel p { font-size: 13px; color: var(--danger); }
```

경로: `frontend/app/admin/_components/BackendCheck/index.ts`

```ts
export { BackendCheck } from "./BackendCheck";
```

### 3) admin/page.tsx에 끼워 넣기

경로: `frontend/app/admin/page.tsx`

```tsx
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { BackendCheck } from "./_components/BackendCheck";
import { AdminStats } from "./_components/AdminStats";
import { SalesChart } from "./_components/SalesChart";
import { TopMenus } from "./_components/TopMenus";
import { RecentOrders } from "./_components/RecentOrders";
import styles from "./page.module.css";

export const metadata: Metadata = { title: "대시보드" };

export default function AdminDashboardPage() {
  return (
    <main className={styles.main}>
      <header className="pageHead" style={{ paddingTop: 8, paddingBottom: 8 }}>
        <div>
          <span className="eyebrow">admin / dashboard</span>
          <h1>오늘의 운영 현황</h1>
          <p>주문·매출·인기 메뉴를 한눈에. 숫자는 모두 목업입니다.</p>
        </div>
        <div className={styles.actions}>
          <Link href="/admin/menus" className="btn btnPrimary">메뉴 관리</Link>
          <Link href="/admin/categories" className="btn">카테고리 관리</Link>
        </div>
      </header>

      {/* 쿠키의 토큰으로 백엔드를 호출하므로 Suspense 아래에서 요청 시점에 렌더링 */}
      <Suspense fallback={<div className="skeleton" style={{ height: 52, borderRadius: 14 }} />}>
        <BackendCheck />
      </Suspense>

      <AdminStats />
```

> 원문 바로잡기 — 위 코드는 `<AdminStats />`에서 끊겨 있다. 원문이 일부만 보여 준 것이고, 그 아래의 `SalesChart`, `TopMenus`, `RecentOrders` 배치와 `</main>`, 함수의 닫는 중괄호는 **기존 파일 그대로 둔다.** 이번에 바뀐 것은 맨 위의 `Suspense`, `BackendCheck` import와 `<BackendCheck />` 블록뿐이다.

이 컴포넌트도 쿠키를 읽으므로(`backendFetch` → `getSession` → `cookies()`) Suspense 안에 둔다.

---

## 8. 실행과 테스트

### 1) 실행

터미널 두 개를 연다.

```bash
# 터미널 1 — 스프링 백엔드 (8080)
cd backend
./gradlew bootRun

# 터미널 2 — Next.js 프론트엔드 (3000)
cd frontend
npm run dev
```

### 2) 시나리오

브라우저에서 다음 순서로 확인한다. 각 단계에서 왜 그 결과가 나오는지를 코드와 연결해 보자.

| # | 할 일 | 기대 결과 | 어디서 결정되나 |
|---|---|---|---|
| 1 | 로그인 전 `http://localhost:3000/my` 접속 | `/login?next=/my`로 이동 | `proxy.ts` (쿠키 없음) |
| 2 | 헤더 확인 | "로그인 · 회원가입" 버튼 | `SiteHeader` → `getSession() = null` |
| 3 | `newlec` / `wrong`으로 로그인 | 폼 아래 "아이디 또는 비밀번호가 올바르지 않아요" | `loginAction.ts` (스프링 403) |
| 4 | `newlec` / `123`으로 로그인 | `/my`로 이동, 헤더에 아바타 N | `loginAction.ts` → 쿠키 → `redirect(next)` |
| 5 | 개발자 도구 → Application → Cookies | `accessToken` 쿠키, HttpOnly ✓, Max-Age 1800 | 쿠키 옵션 |
| 6 | 콘솔에서 `document.cookie` 입력 | `accessToken`이 보이지 않음 | HttpOnly |
| 7 | `/admin` 접속 | `/my`로 되돌아감 | `proxy.ts` (`role = USER`) |
| 8 | 프로필 메뉴 → 로그아웃 | `/login`으로 이동, 쿠키 삭제됨 | `logoutAction.ts` |
| 9 | `admin` / `123`으로 로그인 후 `/admin` 접속 | 대시보드 상단에 "스프링 백엔드 연결됨 · GET /api/admin/menus → 200"과 메뉴 4개 | `BackendCheck` → `backendFetch` → 스프링 필터 |
| 10 | 스프링을 끈 뒤 `/admin` 새로고침 | "스프링 백엔드 연결 실패" | `backendCheckApi.ts`의 `catch` |

9번이 이 노트의 종착점이다. 브라우저는 토큰을 본 적이 없지만, 쿠키 → Next.js 서버 → Authorization 헤더 → 스프링 필터 → `ROLE_ADMIN` 복원 → `hasRole("ADMIN")` 통과까지 전체 경로가 한 번에 검증된다.

### 3) 터미널에서 확인하기 (선택)

문지기의 동작은 curl로도 볼 수 있다. 리다이렉트 상태 코드와 목적지가 그대로 드러난다.

```bash
# 쿠키 없이 보호 경로 → 307, /login?next=%2Fmy
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" http://localhost:3000/my

# 스프링에서 토큰을 받아 쿠키로 넘기면 → 200
TOKEN=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H 'Content-Type: application/json' -d '{"username":"admin","password":"123"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["accessToken"])')
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/admin -b "accessToken=$TOKEN"
```

---

## 9. 주의할 사항과 정리

### 1) 토큰을 "읽는 것"과 "검증하는 것"은 다르다

`token.ts`의 `decodeToken()`은 base64를 푸는 것일 뿐 위조 여부를 알 수 없다. 프론트엔드에서 이 값을 근거로 데이터 접근 권한을 결정해서는 안 된다. 화면 이동 판단에만 쓰고, 데이터는 항상 스프링을 거친다.

### 2) secure 쿠키와 localhost

`next start`(운영 모드)로 띄우면 `NODE_ENV=production`이 되어 쿠키에 Secure가 붙는다. 최신 Chrome과 Firefox는 `http://localhost`를 안전한 출처로 취급해 Secure 쿠키도 받아 주지만, `http://127.0.0.1`이나 사설 IP로 접속하면 쿠키가 저장되지 않는다. 개발 중에는 `npm run dev`를 쓰거나 `localhost`로 접속한다.

### 3) 30분 뒤에 일어나는 일

Access Token과 쿠키의 수명이 30분이다. 30분이 지나면 문지기가 `/login`으로 보내고, 사용자는 다시 로그인해야 한다. `JwtProvider`에 Refresh Token을 만드는 코드가 있지만 아직 `AuthService`가 돌려주지 않는다. Refresh Token을 두 번째 쿠키로 저장하고 `/api/auth/refresh`로 조용히 갱신하는 것은 [[053_Refresh Token으로 조용히 갱신하기 — 재발급 API, RefreshTokenStore, proxy 문지기]]에서 다룬다.

### 4) Server Action은 문지기 밖에 있다

6절 3)에서 설명했듯 Server Action은 `proxy.ts`의 `matcher`에 걸리지 않는다. 앞으로 "메뉴 등록" 같은 관리자용 Server Action을 만들 때는 함수 첫 줄에서 `getSession()`으로 `isAdmin`을 확인하는 습관을 들인다.

### 5) 삭제한 파일

이번 노트에서 다음 파일이 삭제되었다. 남아 있으면 빌드 오류나 경고가 난다.

- `frontend/middleware.ts` → `proxy.ts`로 대체
- `frontend/app/login/_components/LoginForm/loginApi.ts` → `loginAction.ts`로 대체
- `frontend/app/login/_components/LoginForm/useLoginForm.ts` → `useActionState`로 대체

### 6) 정리

| 원칙 | 구현한 곳 |
|---|---|
| 토큰은 브라우저 JS가 못 만진다 | `loginAction.ts`의 `httpOnly: true` |
| 비밀키는 스프링만 가진다 | `token.ts`는 해독만, 검증은 `JwtAuthenticationFilter` |
| 스프링은 Next.js 서버만 부른다 | `backend.ts`의 `backendFetch`, CORS 설정 없음 |
| 공용 데이터에 내부 규약을 넣지 않는다 | `AuthService`에서 `ROLE_` 제거, 필터에서 복원 |

---

## 마무리

이번 노트로 사용자는 화면에서 로그인하고, 브라우저는 토큰을 본 적도 없이 쿠키를 들고 다니며, Next.js 문지기는 쿠키를 보고 길을 안내하고, 스프링은 요청마다 토큰을 검증하는 구조가 완성되었다.
