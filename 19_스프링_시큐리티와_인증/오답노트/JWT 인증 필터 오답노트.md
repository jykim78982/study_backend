# JWT 인증 필터 오답노트

### 1. JWT 인증 필터가 하는 일과 하지 않는 일

**문제**: JWT 인증 필터가 요청 처리 과정에서 반드시 수행해야 하는 작업으로 옳지 않은 것은?

1. 토큰의 유효성(서명·만료·형식 등)을 검증한다
2. 토큰에서 사용자 식별 정보와 권한을 추출해 `Authentication` 객체로 변환한다
3. `Authorization` 헤더에서 Bearer 토큰을 추출한다
4. 세션 저장소에서 인증 정보를 조회하여 보안 컨텍스트를 구성한다

**정답: 4번**

JWT 환경에서는 세션을 쓰지 않는다. 그래서 세션 저장소에서 인증 정보를 찾지 않고, **토큰을 해석해서** 보안 컨텍스트를 직접 채운다.

**왜 4번이 틀렸나 — 무상태(Stateless)**

| | 세션 방식 | JWT 방식 |
|---|---|---|
| 로그인 정보가 있는 곳 | 서버(또는 Redis 같은 세션 저장소) | **토큰 안**(클레임: 아이디, 권한, 만료 시각) |
| 요청마다 하는 일 | 쿠키의 세션 ID로 저장소를 **조회** | 헤더의 토큰을 **검증하고 해석** |
| 보안 컨텍스트를 채우는 쪽 | 스프링 시큐리티가 세션에서 **자동으로** | 우리가 만든 JWT 필터가 **직접** |

4번은 **세션 방식**에서 스프링 시큐리티가 하는 일이다(세션에 저장해 둔 `SecurityContext`를 요청마다 꺼내 온다). JWT 필터는 저장소를 뒤질 필요가 없다. 토큰을 열어 서명만 확인하면 필요한 정보가 그 안에 다 들어 있기 때문이다. 그래서 `SecurityConfig`에서도 세션 정책을 `STATELESS`로 둔다.

**JWT 인증 필터가 하는 일 (1, 2, 3번) — 실행 순서**

`OncePerRequestFilter`를 상속한 필터가 **모든 요청마다** 아래 순서로 처리한다. 보기 번호 순서와 실제 순서가 다르니 주의한다.

```
① 토큰 추출 (3번)       Authorization: Bearer eyJhbGci...  →  "Bearer " 뒤의 토큰만 꺼낸다
        │
        ▼
② 토큰 검증 (1번)       서명이 맞는가(위조), 만료되지 않았는가, 형식이 올바른가
        │
        ▼
③ 인증 객체 등록 (2번)  토큰에서 아이디와 권한을 꺼내 Authentication 객체로 만들고
        │               SecurityContextHolder에 담는다
        ▼
④ 다음 필터로 넘김      filterChain.doFilter(request, response)
```

```java
String token = resolveToken(request);                         // ① 추출
if (token != null && jwtProvider.validateToken(token)) {      // ② 검증
    String username = jwtProvider.getUsername(token);         // ③ 정보 꺼내기
    String role = jwtProvider.getRole(token);
    Authentication authentication = new UsernamePasswordAuthenticationToken(
            username, null, List.of(new SimpleGrantedAuthority(role)));
    SecurityContextHolder.getContext().setAuthentication(authentication);
}
filterChain.doFilter(request, response);                      // ④ 무조건 다음으로
```

③을 거쳐야 컨트롤러에서 `Authentication` 매개변수나 `@AuthenticationPrincipal`로 현재 로그인한 사용자를 꺼내 쓸 수 있고, 뒤쪽 인가 필터가 `hasRole("ADMIN")` 같은 규칙을 판단할 수 있다.

> 해설 바로잡기 — 해설에 "토큰 자체에 사용자 정보와 권한이 서명과 함께 **암호화**되어 들어 있다"고 했지만, 일반적인 JWT(JWS)는 **암호화가 아니라 서명**만 되어 있다. 페이로드는 Base64URL로 인코딩만 되어 있어서 누구나 풀어 볼 수 있다(jwt.io에 붙여 넣으면 그대로 보인다). 서명은 내용을 **숨기는** 것이 아니라 **위조를 막는** 장치다. 그래서 비밀번호 같은 민감한 값은 클레임에 넣지 않는다. 내용까지 숨기려면 JWE라는 암호화 형식을 따로 쓴다.

> **추가 설명 — 토큰이 없거나 잘못돼도 필터는 막지 않는다**: ②에서 검증에 실패하면 예외를 던지는 것이 아니라 `SecurityContext`를 **비워 둔 채** ④로 넘긴다. 로그인 같은 공개 경로도 이 필터를 지나가기 때문이다. 인증이 필요한 경로는 뒤쪽 인가 단계에서 스프링 시큐리티가 막는다.

> **추가 설명 — "저장소를 아예 안 본다"는 기본 구현의 이야기다**: 토큰의 아이디로 DB에서 사용자를 다시 조회하는 구현도 있다(탈퇴, 정지된 사용자를 바로 막고 싶을 때). 그래도 그것은 **사용자 정보 DB** 조회이지, 4번처럼 로그인 상태를 담은 **세션 저장소**를 조회하는 것은 아니다. 어느 쪽이든 서버는 "누가 로그인해 있는지"를 기억하지 않는다.

**정리**: JWT 인증 필터의 일은 **추출(헤더에서 Bearer 토큰) → 검증(서명·만료·형식) → 등록(`Authentication`을 만들어 `SecurityContextHolder`에)** 세 단계다. 세션 저장소 조회는 세션 방식의 일이고, 무상태인 JWT 방식에서는 하지 않는다.
