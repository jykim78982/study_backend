---
tags: [스프링부트, 스프링시큐리티, JWT, JJWT, ConfigurationProperties, JwtProvider, OncePerRequestFilter, SecurityContextHolder, Bearer, SecurityConfig, SessionCreationPolicy, CSRF, 실습]
---

> 🔗 관련 노트: [[099_인증 방식의 변화와 JWT — 세션에서 토큰으로, SAML·OAuth 2.0·BFF]] · [[098_스프링 시큐리티 인가 설정 — URL별 허용 규칙, 역할, 커스텀 로그인 페이지]] · [[093_서블릿 필터와 스프링 시큐리티 입문 — 필터 체인, @Bean, UserDetailsService]]

# 스프링 부트 JWT 인증 구현 — JJWT 설정, JwtProvider, JwtAuthenticationFilter, SecurityConfig

풀스택 환경에서 토큰 기반 인증을 쓰기로 했다면, 백엔드 서버가 토큰을 **발급**하고 **검증**할 수 있어야 한다. 이 실습은 네 단계로 진행한다.

| 단계 | 만드는 것 | 비유 |
|---|---|---|
| 1부 | JJWT 라이브러리 + `JwtProperties` (비밀키, 만료 시간) | 토큰의 **재료와 규격서** |
| 2부 | `JwtProvider` (토큰 발급, 검증, 정보 추출) | 토큰을 찍어내고 검사하는 **기계** |
| 3부 | `JwtAuthenticationFilter` (요청마다 토큰 검사 → 로그인 상태로 등록) | 출입구의 **보안 요원** |
| 4부 | `SecurityConfig` (필터 등록, 세션·CSRF 끄기, 경로별 권한) | 보안 요원을 출입구에 세우는 **제어실** |

> **추가 설명 — 수업 프로젝트(ncafe)와 다른 점**: ncafe 스타터 백엔드는 JJWT 대신 스프링 시큐리티의 **OAuth2 Resource Server** 모듈(`spring-boot-starter-oauth2-resource-server`)을 쓴다. 그 모듈이 `JwtEncoder`/`JwtDecoder`와 토큰 검사 필터를 이미 갖고 있어서, `SecurityConfig`에 `.oauth2ResourceServer(o -> o.jwt(...))` 한 줄로 3부의 필터를 대신한다. 이 실습은 그 안에서 일어나는 일을 **JJWT로 직접 만들어 보는** 과정이다. 두 방식 모두 많이 쓰인다.

---

## 1부. 스프링 부트에서 JWT 사용을 위한 개발 환경 구축

### 0. 부트 프로젝트 생성하기

VS Code에서 Spring Initializr 확장 프로그램이나 명령어 팔레트로 프로젝트를 만든다.

1. **명령어 팔레트 열기**: `Ctrl + Shift + P`(macOS는 `Cmd + Shift + P`) → `Spring Initializr: Create a Gradle Project`
2. **스프링 부트 버전**: 안정 버전인 `4.1.2`를 고른다. `SNAPSHOT`, `RC1`이 붙은 것은 개발 중인 버전이므로 고르지 않는다.

   ```
   Specify Spring Boot version.
   ▶ 4.1.2
     4.2.0 (SNAPSHOT)
     4.2.0 (RC1)
     4.1.3 (SNAPSHOT)
     4.0.10 (SNAPSHOT)
     4.0.9
   ```

3. **언어와 자바 버전**: `Java`(그 밖에 Kotlin, Groovy)를 고르고, 사용 중인 자바 버전(예: 17, 21)을 지정한다.
4. **Group과 Artifact**: 패키지 경로와 이름을 입력한다. 이 실습에서는 패키지가 `com.ncafe.backend`다.
5. **의존성**: `Spring Web`, `Spring Boot DevTools`, `Lombok` 정도만 고른다.

스프링 시큐리티는 **일부러 넣지 않았다**. 1~2부는 JWT 라이브러리만으로 진행하고, 시큐리티는 3부에서 필터를 만들 때 추가한다.

> 원문 바로잡기 — 원문은 DevTools를 "설정 자동 완성을 위한" 의존성이라고 했다. DevTools는 코드를 고치면 **서버를 자동으로 재시작**하고 브라우저를 새로고침해 주는 개발 도구다. `application.yml`에서 내가 만든 설정(`jwt.secret` 등)을 자동 완성해 주는 것은 `spring-boot-configuration-processor`다(4절 추가 설명 참고).

> **추가 설명 — 스프링 부트 4의 자바 버전**: 스프링 부트 4는 **자바 17 이상**이 필요하다. ncafe 스타터는 자바 25를 쓴다.

### 1. JWT 라이브러리 선택 및 의존성 추가

자바에서 JWT를 다룰 때 가장 많이 쓰는 라이브러리는 **JJWT**(Java JWT)다. `build.gradle`의 `dependencies`에 0.12.x 버전 라이브러리 3개를 추가한다.

```groovy
dependencies {
    // JWT 관련 라이브러리 (JJWT)
    implementation 'io.jsonwebtoken:jjwt-api:0.12.6'
    runtimeOnly 'io.jsonwebtoken:jjwt-impl:0.12.6'
    runtimeOnly 'io.jsonwebtoken:jjwt-jackson:0.12.6'
}
```

| 라이브러리 | 역할 | 범위 |
|---|---|---|
| `jjwt-api` | 토큰 생성과 검증에 필요한 핵심 **인터페이스** | `implementation` — 내 코드가 직접 씀 |
| `jjwt-impl` | 그 인터페이스의 실제 **구현체** | `runtimeOnly` — 실행할 때만 필요 |
| `jjwt-jackson` | 토큰 안의 JSON을 Jackson으로 처리하도록 연결 | `runtimeOnly` |

> **추가 설명 — 왜 `runtimeOnly`인가**: 내 코드는 `jjwt-api`의 인터페이스(`Jwts`, `Claims` 등)만 보고 작성한다. 구현체는 실행할 때 JJWT가 알아서 찾아 쓴다. `runtimeOnly`로 두면 실수로 구현체 내부 클래스를 직접 쓰는 일을 컴파일 단계에서 막을 수 있고, 나중에 구현이 바뀌어도 내 코드는 영향을 받지 않는다.

Gradle 파일을 저장한 뒤 VS Code에서 프로젝트를 다시 불러오면(Gradle 새로고침) 라이브러리가 내려받아진다.

### 2. 설정을 중앙 관리해야 하는 이유

토큰을 만들고 검증할 때 반드시 필요한 값이 두 가지 있다.

- **비밀키**(Secret Key): 서버만 아는 비밀 문자열이다. 토큰이 위조되지 않았음을 증명하는 **서명 도장** 역할을 한다.
- **유효기간**(Expiration Time): 토큰이 살아 있는 시간이다. 액세스 토큰과 리프레시 토큰의 수명을 각각 정한다.

이 값을 자바 코드에 직접 적으면 문제가 생긴다.

- 소스 코드가 공개되면 비밀키도 함께 유출된다.
- 만료 시간을 바꿀 때마다 자바 코드를 고치고 다시 빌드해야 한다.

그래서 이 값들은 **외부 설정 파일**(`application.yml`)로 빼고, 실제 비밀값은 환경 변수로 넣는다.

### 3. application.yml에 JWT 설정 추가하기

파일: `src/main/resources/application.yml`

```yaml
jwt:
  # HS256 알고리즘을 사용하려면 최소 256비트(32바이트/32자) 이상의 길이를 가져야 한다.
  secret: ${JWT_SECRET:v9y$B&E)H@McQfTjWnZr4u7x!A%C*F-JaNdR}
  access-token-expiration: 1800000      # 30분 (밀리초: 30 * 60 * 1000)
  refresh-token-expiration: 1209600000  # 14일 (밀리초: 14 * 24 * 60 * 60 * 1000)
```

**보안 설정 시 주의점**

- **비밀키의 최소 길이**: JJWT 0.12.x부터는 HS256을 쓸 때 **최소 32바이트(256비트)** 비밀키를 강제한다. 키가 짧으면 서버를 실행할 때 `WeakKeyException`이 나며 뜨지 않는다.
- **환경 변수 활용**: `${JWT_SECRET:기본값}` 형태로 쓴다. 운영 환경에서는 Docker Compose나 서버의 환경 변수(`JWT_SECRET`)로 진짜 비밀키를 넣고, 개발 환경에서는 `:` 뒤의 기본값을 쓴다.

> **추가 설명 — 32"자"가 아니라 32"바이트"**: 영문, 숫자, 기호는 1글자가 1바이트지만 한글은 UTF-8에서 1글자가 **3바이트**다. 기준은 바이트 수다. 위 기본값은 36자(36바이트)라 조건을 만족한다. 운영용 키는 사람이 만든 문장보다 무작위 값이 안전하다.
>
> ```bash
> openssl rand -base64 48     # 64글자짜리 무작위 문자열 생성
> ```

> **추가 설명 — 기본값의 함정**: 기본값이 있으면 운영 서버에 `JWT_SECRET`을 **깜빡 안 넣어도** 서버가 그대로 뜬다. 그러면 깃허브에 공개된 기본 키로 운영 토큰이 서명되고, 그 키를 아는 사람은 누구든 관리자 토큰을 만들 수 있다. 운영에서는 반드시 환경 변수로 덮어쓰고, 더 안전하게 하려면 운영 프로필에서는 `${JWT_SECRET}`처럼 기본값을 빼서 값이 없으면 서버가 뜨지 않게 한다.

### 4. 자바 클래스로 설정값 가져오기

`@ConfigurationProperties`를 붙이면, 지정한 접두사(`jwt`) 아래의 설정값이 자바 객체 필드에 **자동으로 들어간다**.

파일: `src/main/java/com/ncafe/backend/config/JwtProperties.java`

```java
package com.ncafe.backend.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "jwt")
public class JwtProperties {

    private String secret;
    private long accessTokenExpiration;
    private long refreshTokenExpiration;

    // Getter, Setter
    public String getSecret() {
        return secret;
    }

    public void setSecret(String secret) {
        this.secret = secret;
    }

    public long getAccessTokenExpiration() {
        return accessTokenExpiration;
    }

    public void setAccessTokenExpiration(long accessTokenExpiration) {
        this.accessTokenExpiration = accessTokenExpiration;
    }

    public long getRefreshTokenExpiration() {
        return refreshTokenExpiration;
    }

    public void setRefreshTokenExpiration(long refreshTokenExpiration) {
        this.refreshTokenExpiration = refreshTokenExpiration;
    }
}
```

이제 토큰을 만드는 클래스나 서비스에서 `JwtProperties`를 주입받아 비밀키와 만료 시간을 꺼내 쓰면 된다.

> **추가 설명 — 이름이 달라도 연결되는 이유**: yml의 `access-token-expiration`(케밥 표기)이 자바의 `accessTokenExpiration`(카멜 표기)에 들어가는 것은 스프링 부트의 **느슨한 바인딩** 덕분이다. 환경 변수 `JWT_ACCESS_TOKEN_EXPIRATION`으로도 같은 값을 덮어쓸 수 있다.

> **추가 설명 — 더 짧게 쓰는 방법**: Getter/Setter 대신 **record**로 써도 된다. 값이 생성자로 한 번만 들어가고 바뀌지 않아서 설정 클래스에 잘 맞는다. ncafe 스타터도 이 방식이다. record에는 `@Component`를 붙일 수 없으므로, 대신 설정 클래스나 메인 클래스에 `@EnableConfigurationProperties(JwtProperties.class)` 또는 `@ConfigurationPropertiesScan`을 붙여 등록한다.
>
> ```java
> @ConfigurationProperties(prefix = "jwt")
> public record JwtProperties(String secret, long accessTokenExpiration, long refreshTokenExpiration) {}
> ```
>
> 이 경우 꺼낼 때는 `getSecret()`이 아니라 `secret()`이다.

> **추가 설명 — yml 자동 완성 켜기**: 아래 의존성을 추가하면 `application.yml`에서 `jwt.`을 칠 때 내가 만든 속성이 자동 완성되고, IDE의 "알 수 없는 속성" 경고도 사라진다.
>
> ```groovy
> annotationProcessor 'org.springframework.boot:spring-boot-configuration-processor'
> ```

### 5. 1부 정리

스프링 부트 프로젝트에 JJWT 라이브러리를 등록하고, 토큰을 만들 때 필요한 비밀키와 만료 시간을 **외부 설정 파일**로 관리하도록 기반을 갖췄다.

---

## 2부. JWT 생성과 검증을 위한 JwtProvider 구현

### 1. JWT 유틸리티 클래스가 필요한 이유와 기본 구조

```
 1부: 재료와 규격서 (JwtProperties)          2부: 토큰 생성·검증 기계 (JwtProvider)
 ┌──────────────────────────┐            ┌─────────────────────────────────────────┐
 │ 비밀키 (string)            │  설정값    │ ① 토큰 발급                                │
 │ Access Token 만료 시간      │ ───────▶  │   사용자 ID + 권한 → Access Token (username, role) │
 │ Refresh Token 만료 시간     │  전달     │                  → Refresh Token (username)       │
 └──────────────────────────┘            │ ② 토큰 검증                                │
                                         │   손님 토큰 → 서명 검증, 만료 확인 → 유효 ✔ / 무효 ✘ │
                                         └─────────────────────────────────────────┘
```

서버는 로그인에 성공한 사용자에게 토큰을 만들어 줘야 하고, 이후 요청이 올 때마다 그 토큰이 유효한지 확인해야 한다. 이 기능을 컨트롤러나 서비스 곳곳에 흩어 두면 관리가 어려우므로, `JwtProvider`라는 전담 클래스에 모은다.

먼저 뼈대와 **비밀키 초기화**부터 작성한다.

파일: `src/main/java/com/ncafe/backend/security/jwt/JwtProvider.java`

```java
package com.ncafe.backend.security.jwt;

import com.ncafe.backend.config.JwtProperties;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;

@Component
public class JwtProvider {

    private final JwtProperties jwtProperties;
    private SecretKey secretKey;

    public JwtProvider(JwtProperties jwtProperties) {
        this.jwtProperties = jwtProperties;
    }

    @PostConstruct
    public void init() {
        // 문자열 상태인 비밀키를 JJWT 규격에 맞는 SecretKey 객체로 변환한다.
        byte[] keyBytes = jwtProperties.getSecret().getBytes(StandardCharsets.UTF_8);
        this.secretKey = Keys.hmacShaKeyFor(keyBytes);
    }
}
```

- JJWT 0.12.x부터는 문자열을 서명에 바로 쓸 수 없다. `Keys.hmacShaKeyFor()`로 **암호화 전용 키 객체**(`SecretKey`)로 바꿔야 한다. 키가 32바이트보다 짧으면 여기서 `WeakKeyException`이 난다.
- `@PostConstruct`를 붙인 메서드는 스프링 빈이 생성되고 **의존성 주입(`JwtProperties`)이 끝난 직후** 자동으로 한 번 실행된다. 따로 호출하지 않아도 클래스를 쓸 준비가 될 때 비밀키가 변환되어 있다.

> **추가 설명 — 생성자에서 해도 된다**: 생성자 주입을 쓰면 생성자가 실행될 때 이미 `jwtProperties`가 들어와 있으므로, `init()`의 내용을 생성자 안에 써도 같다. 그러면 `secretKey`를 `final`로 둘 수 있다. `@PostConstruct`가 꼭 필요한 것은 **필드 주입**(`@Autowired private JwtProperties ...`)처럼 생성자 실행 시점에 아직 값이 없을 때다.

### 2. Access Token과 Refresh Token 생성하기

`Jwts.builder()`에 토큰에 넣을 정보(사용자 아이디, 권한, 발급 시각, 만료 시각)를 쌓은 뒤 비밀키로 서명하면 최종 문자열이 된다.

| 토큰 | 발급 시점 | 쓰임 | 수명 |
|---|---|---|---|
| **Access Token** | 로그인 성공 직후 | API를 요청할 때마다 헤더에 담아 보내는 **인증용** 토큰. 서버는 이것으로 로그인 여부와 권한을 판단 | 짧게 (30분) |
| **Refresh Token** | Access Token과 함께 로그인 성공 시 | Access Token이 만료됐을 때, 다시 로그인하지 않고 **새 Access Token을 재발급**받는 요청에만 사용 | 길게 (14일) |

`JwtProvider` 안에 아래 메서드를 추가한다.

```java
import io.jsonwebtoken.Jwts;

public class JwtProvider {

    // ... 기존 코드 (필드, 생성자, init 메서드) 생략 ...

    // Access Token 생성
    public String createAccessToken(String username, String role) {
        long now = System.currentTimeMillis();
        long expiration = now + jwtProperties.getAccessTokenExpiration();

        return Jwts.builder()
                .subject(username)                          // 토큰 주인 (사용자 아이디)
                .claim("role", role)                        // 사용자 권한 정보 추가
                .issuedAt(new java.util.Date(now))          // 토큰 발급 시각
                .expiration(new java.util.Date(expiration)) // 토큰 만료 시각
                .signWith(secretKey)                        // 비밀키로 서명
                .compact();
    }

    // Refresh Token 생성
    public String createRefreshToken(String username) {
        long now = System.currentTimeMillis();
        long expiration = now + jwtProperties.getRefreshTokenExpiration();

        return Jwts.builder()
                .subject(username)
                .issuedAt(new java.util.Date(now))
                .expiration(new java.util.Date(expiration))
                .signWith(secretKey)
                .compact();
    }
}
```

- Access Token에는 **권한**(`role`)을 함께 담는다. 서버가 요청마다 DB를 조회하지 않고 토큰만 보고 권한을 바로 알 수 있게 하기 위해서다.
- Refresh Token은 재발급용으로만 쓰므로 권한 없이 만료 시간만 길게 잡는다.

> **추가 설명 — 알고리즘은 키 길이로 정해진다**: `signWith(secretKey)`처럼 알고리즘을 안 적으면 JJWT가 **키 길이에 맞는 가장 강한 HMAC 알고리즘**을 고른다. 32~47바이트면 HS256, 48~63바이트면 HS384, 64바이트 이상이면 HS512다. 위 기본 키(36바이트)는 HS256이 된다.

> **추가 설명 — 만든 토큰을 눈으로 확인하기**: 발급한 Access Token을 https://jwt.io 에 붙여 넣으면 페이로드가 `{"sub": "user@ncafe.local", "role": "ROLE_USER", "iat": ..., "exp": ...}`처럼 그대로 보인다. 서명이 있을 뿐 암호화가 아니므로 비밀번호 같은 값은 절대 클레임에 넣지 않는다.

### 3. 토큰 유효성 검증과 정보 추출하기

토큰이 서버로 돌아오면 세 가지를 검사해야 한다.

1. 우리 서버가 발급한 것이 맞는가 (서명)
2. 중간에 누가 내용을 바꾸지 않았는가 (서명)
3. 유효기간이 지나지 않았는가 (만료 시간)

JJWT는 `Jwts.parser()`로 이 검사를 **한 번에 자동으로** 해 준다. `JwtProvider` 안에 이어서 작성한다.

```java
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;

// ... 기존 import 생략 ...

public class JwtProvider {

    // ... 기존 코드 (필드, 생성자, init, createAccessToken, createRefreshToken) 생략 ...

    // 토큰에서 사용자 아이디(Subject) 추출
    public String getUsername(String token) {
        return parseClaims(token).getSubject();
    }

    // 토큰에서 권한(Role) 정보 추출
    public String getRole(String token) {
        return parseClaims(token).get("role", String.class);
    }

    // 토큰 유효성 검증
    public boolean validateToken(String token) {
        try {
            parseClaims(token);
            return true;
        } catch (ExpiredJwtException e) {
            // 토큰이 만료된 경우
            return false;
        } catch (JwtException | IllegalArgumentException e) {
            // 서명이 올바르지 않거나 토큰 형식이 잘못된 경우
            return false;
        }
    }

    // 토큰 내부 데이터(Claims) 파싱 메서드
    private Claims parseClaims(String token) {
        return Jwts.parser()
                .verifyWith(secretKey)    // 검증에 사용할 비밀키 설정
                .build()
                .parseSignedClaims(token) // 토큰 해석 및 서명 검증
                .getPayload();
    }
}
```

| 메서드 | 하는 일 |
|---|---|
| `parseClaims(token)` | 토큰을 해석하는 공통 메서드. 비밀키로 **서명과 만료 시간을 자동 검사**하고, 통과하면 페이로드(`Claims`)를 돌려준다 |
| `getUsername(token)` | `Claims`에서 `.getSubject()`로 토큰 주인의 아이디를 꺼낸다 |
| `getRole(token)` | `Claims`에서 `.get("role", String.class)`로 발급 때 넣은 권한을 꺼낸다 |
| `validateToken(token)` | `parseClaims()`를 실행해 보고 예외가 없으면 `true`, 있으면 `false` |

검증에 실패하면 JJWT가 예외를 던지고, `validateToken()`이 받아서 `false`로 바꾼다.

| 예외 | 언제 | 대응 |
|---|---|---|
| `ExpiredJwtException` | 토큰 수명이 끝났을 때 | 클라이언트에게 **재발급**을 요청하게 한다 |
| `JwtException` | 누군가 토큰 글자를 바꿨거나, 다른 키로 서명했거나, 형식이 깨졌을 때 | 위조이거나 잘못된 요청이므로 **즉시 거절** |
| `IllegalArgumentException` | 토큰 값이 `null`이거나 비어 있을 때 | 즉시 거절 |

> **추가 설명 — 지금 코드는 두 경우를 구분하지 못한다**: 만료와 위조 모두 `false`만 돌려주므로, 바깥에서는 "재발급하면 되는 토큰"인지 "버려야 할 토큰"인지 알 수 없다. 만료 시 프론트가 Refresh Token으로 자동 재발급하게 하려면, 결과를 `VALID` / `EXPIRED` / `INVALID` 같은 값으로 돌려주거나 401 응답에 "만료" 표시를 담아 구분해야 한다. `catch` 순서는 지금처럼 **하위 예외(`ExpiredJwtException`)를 먼저** 써야 한다. 상위 예외인 `JwtException`을 먼저 쓰면 만료도 거기에 잡혀 버린다(순서가 바뀌면 컴파일 오류가 난다).

### 4. 2부 정리

- 비밀키를 안전한 객체(`SecretKey`)로 들고 있는다.
- 사용자 정보로 Access Token과 Refresh Token을 만든다.
- 들어온 토큰의 서명과 만료 여부를 검사하고, 아이디와 권한을 꺼낸다.

---

## 3부. JWT를 검사하여 로그인 상태로 만들어 주는 JwtAuthenticationFilter 구현

### 1. build.gradle에 스프링 시큐리티 의존성 추가하기

로그인 정보를 보관하는 `SecurityContextHolder` 같은 도구를 쓰려면 스프링 시큐리티가 필요하다.

```groovy
dependencies {
    // 스프링 시큐리티 스타터 추가
    implementation 'org.springframework.boot:spring-boot-starter-security'

    // 스프링 시큐리티 테스트 도구 추가
    testImplementation 'org.springframework.security:spring-security-test'
}
```

- 이 라이브러리를 넣으면 프로젝트 전체에 스프링 시큐리티의 **기본 필터 체인**이 켜지고, 인증과 인가를 처리하는 핵심 클래스를 쓸 수 있다.
- `spring-security-test`는 컨트롤러 테스트에서 `@WithMockUser`처럼 "로그인한 사용자인 척"하는 도구를 제공한다.

> **추가 설명 — 추가하자마자 모든 API가 막힌다**: 시큐리티를 넣고 `SecurityConfig`를 아직 안 만들었다면, 스프링 시큐리티의 **기본 설정**이 적용된다. 모든 요청에 로그인이 필요해지고, 브라우저로 접속하면 기본 로그인 페이지가 뜨며, 콘솔에 `Using generated security password: ...`가 찍힌다. 고장이 아니라 정상이다. 4부에서 `SecurityConfig`를 만들어 이 기본 설정을 바꾼다.

### 2. JWT 인증 필터의 개념과 OncePerRequestFilter

```
 방문객 도착                    보안 요원 필터                          건물 내부 입장
 ───────────                  ───────────────                        ───────────────
 요청: Authorization 헤더  ─▶  명찰 확인 (토큰 추출 및 검증)
 "Bearer eyJhbGciOi..."         │ 올바른 명찰이면
                                ▼
                          건물 내부 출입증 발급
                          (UsernamePasswordAuthenticationToken)
                                │
                                ▼
                          SecurityContextHolder (인증 정보 보관함)  ─▶  다음 필터로 요청 전달
                                                                     → 서비스, 컨트롤러
```

건물 입구의 보안 요원처럼, 필터는 요청이 올 때마다 **명찰(JWT)** 을 확인하고, 올바르면 **건물 내부 출입증**을 걸어 준 뒤 안으로 보낸다.

이 필터는 `OncePerRequestFilter`를 상속받아 만든다. 이름 그대로 **한 번의 HTTP 요청당 딱 한 번만 실행되는 필터**다.

> 원문 바로잡기 — 원문은 `OncePerRequestFilter`를 "스프링 시큐리티가 제공하는 클래스"라고 했지만, 패키지(`org.springframework.web.filter`)에서 보이듯 **스프링 웹(spring-web)** 이 제공하는 클래스다. 스프링 시큐리티의 여러 필터도 이것을 상속받아 만들어져 있어서 함께 자주 등장할 뿐이다.

**🎓 newlec 쌤의 코멘트 — 요청당 딱 한 번만 실행되는 필터?**

서버 내부에서 포워드(forward)나 에러 처리(include/error) 등으로 요청이 다시 호출되면, 일반 필터는 **매번 다시 실행**된다. 그러면 토큰 검사나 DB 조회가 중복으로 수행되어 비효율적이고 예기치 못한 에러가 날 수 있다. `OncePerRequestFilter`는 이 필터가 **이미 실행됐는지 감지**해서, 클라이언트 요청 한 번의 범위 안에서는 필터 로직이 단 한 번만 실행되도록 보장한다.

기본 구조는 다음과 같다(자세한 코드는 4절).

```java
package com.ncafe.backend.security.jwt;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtProvider jwtProvider;

    public JwtAuthenticationFilter(JwtProvider jwtProvider) {
        this.jwtProvider = jwtProvider;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {

        // TODO: 토큰 추출 및 검증 로직 구현

        filterChain.doFilter(request, response);
    }
}
```

### 3. 요청 헤더에서 토큰 추출 및 검증 구현하기

클라이언트는 보통 `Authorization` 헤더에 토큰을 담아 보낸다. 값에는 토큰만 있는 게 아니라 `Bearer eyJhbGciOi...`처럼 앞에 **`Bearer `(공백 포함 7글자)** 접두사가 붙는다. 그래서 먼저 이 접두사를 잘라 **순수한 토큰**만 꺼내야 한다.

```
 HTTP 요청 헤더
   Authorization: Bearer eyJhbGciOi...
                  └──┬──┘└────┬────┘
                  잘라냄 ✂    순수한 JWT 토큰 → 검증 ✔
```

```java
private String resolveToken(HttpServletRequest request) {
    String bearerToken = request.getHeader("Authorization");

    // 헤더에 값이 있고 "Bearer "로 시작하는지 확인한다.
    if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
        // "Bearer " 7글자를 제외한 나머지 순수 토큰 문자열만 잘라서 반환한다.
        return bearerToken.substring(7);
    }

    return null;
}
```

`Bearer `로 시작하는 정상적인 값이면 토큰만 잘라 주고, 헤더가 없거나 형식이 맞지 않으면 `null`을 돌려준다.

### 4. SecurityContext에 인증 정보 저장하고 요청 넘기기

순수한 토큰을 얻었으면 `JwtProvider`로 진짜인지 확인한다. 유효하면 아이디와 권한을 꺼내 **스프링 시큐리티 전용 출입증**(`UsernamePasswordAuthenticationToken`)을 만들고, 보관함인 `SecurityContextHolder`에 넣는다. 그래야 뒤의 컨트롤러와 서비스가 "로그인한 사용자구나" 하고 알 수 있다.

파일: `src/main/java/com/ncafe/backend/security/jwt/JwtAuthenticationFilter.java`

```java
package com.ncafe.backend.security.jwt;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Collections;

public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtProvider jwtProvider;

    public JwtAuthenticationFilter(JwtProvider jwtProvider) {
        this.jwtProvider = jwtProvider;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {

        // 1. 요청 헤더에서 순수 토큰 추출
        String token = resolveToken(request);

        // 2. 토큰이 존재하고 유효한지 검증
        if (token != null && jwtProvider.validateToken(token)) {
            // 토큰에서 사용자 아이디와 권한 추출
            String username = jwtProvider.getUsername(token);
            String role = jwtProvider.getRole(token);

            // 스프링 시큐리티 권한 객체 생성
            SimpleGrantedAuthority authority = new SimpleGrantedAuthority(role);

            // 스프링 시큐리티 전용 인증 객체(출입증) 생성
            Authentication authentication = new UsernamePasswordAuthenticationToken(
                    username,
                    null,
                    Collections.singletonList(authority)
            );

            // 보관함(SecurityContext)에 인증 정보 저장
            SecurityContextHolder.getContext().setAuthentication(authentication);
        }

        // 3. 다음 필터로 요청 전달
        filterChain.doFilter(request, response);
    }

    private String resolveToken(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}
```

| 단계 | 하는 일 |
|---|---|
| `resolveToken` | 요청 헤더에서 토큰 글자만 꺼낸다 |
| `validateToken` | `JwtProvider`로 토큰이 맞는지 검사한다 |
| `SecurityContextHolder` 저장 | 유효하면 권한을 붙인 출입증을 보관함에 넣어 **로그인 상태**로 등록한다 |
| `filterChain.doFilter` | 검사가 끝나면 다음 필터로 요청을 넘긴다 |

> **추가 설명 — 출입증의 세 칸**: `UsernamePasswordAuthenticationToken(principal, credentials, authorities)`에서 첫 칸은 **누구인지**(아이디), 둘째 칸은 **비밀번호**, 셋째 칸은 **권한 목록**이다. 이미 토큰으로 검증이 끝났으므로 비밀번호는 필요 없어서 `null`을 넣는다. 권한 목록을 받는 이 3인자 생성자는 "**인증 완료**" 상태(`isAuthenticated() == true`)의 객체를 만든다. 반대로 2인자 생성자는 "아직 인증 전"(로그인 폼에서 막 받은 아이디/비밀번호) 상태다.

> **추가 설명 — `role` 값에는 `ROLE_` 접두사가 있어야 한다**: `SimpleGrantedAuthority(role)`은 받은 문자열을 **그대로** 권한 이름으로 쓴다. 나중에 `SecurityConfig`에서 `.hasRole("ADMIN")`으로 막으면 스프링 시큐리티는 `ROLE_ADMIN`이라는 권한을 찾는다. 그래서 토큰을 만들 때 `createAccessToken(email, "ROLE_ADMIN")`처럼 접두사를 붙여 넣거나, 필터에서 `new SimpleGrantedAuthority("ROLE_" + role)`처럼 붙여야 한다. 토큰에 `"ADMIN"`만 넣고 `hasRole("ADMIN")`을 쓰면 로그인은 되는데 **계속 403**이 난다. ncafe 스타터도 같은 이유로 `setAuthorityPrefix("ROLE_")`를 쓴다.

> **추가 설명 — Refresh Token을 넣으면 500 에러가 난다**: 두 토큰은 같은 비밀키로 서명되므로, 누군가 Refresh Token을 `Authorization` 헤더에 넣어 보내도 `validateToken()`은 `true`를 돌려준다. 그런데 Refresh Token에는 `role`이 없어서 `getRole()`이 `null`을 돌려주고, `new SimpleGrantedAuthority(null)`에서 `IllegalArgumentException`이 나서 요청이 **500 에러**로 끝난다. 또 수명이 14일인 Refresh Token이 API 인증에 쓰일 수 있다는 것 자체가 문제다. 토큰에 **종류를 구분하는 클레임**을 넣고 필터에서 확인한다.
>
> ```java
> // 발급할 때
> .claim("type", "access")    // createAccessToken
> .claim("type", "refresh")   // createRefreshToken
>
> // 필터에서: Access Token일 때만 인증 처리
> if ("access".equals(claims.get("type", String.class))) { ... }
> ```

> **추가 설명 — 토큰을 세 번 해석하고 있다**: 위 필터는 `validateToken()`, `getUsername()`, `getRole()`을 차례로 부르는데, 셋 다 안에서 `parseClaims()`를 실행한다. 요청 하나마다 **서명 검증을 세 번** 하는 셈이다. `JwtProvider`에 `Claims`를 한 번에 돌려주는 메서드를 두고, 필터에서는 한 번만 해석해서 꺼내 쓰는 것이 좋다.
>
> ```java
> // JwtProvider: 유효하면 Claims, 아니면 null
> public Claims getClaimsIfValid(String token) {
>     try {
>         return parseClaims(token);
>     } catch (JwtException | IllegalArgumentException e) {
>         return null;
>     }
> }
>
> // 필터
> Claims claims = (token != null) ? jwtProvider.getClaimsIfValid(token) : null;
> if (claims != null && "access".equals(claims.get("type", String.class))) {
>     String username = claims.getSubject();
>     String role = claims.get("role", String.class);
>     ...
> }
> ```

> **추가 설명 — 필터에 `@Component`를 붙이지 않는 이유**: 이 필터는 일부러 `@Component` 없이 만들고, 4부의 `SecurityConfig`에서 `new JwtAuthenticationFilter(jwtProvider)`로 직접 만들어 등록한다. `Filter`를 `@Component`로 빈 등록하면 스프링 부트가 **서블릿 필터로도 자동 등록**해서, 시큐리티 필터 체인 밖에서도 한 번 더 걸리게 된다. 시큐리티 체인에만 넣고 싶은 필터는 빈으로 만들지 않는 것이 깔끔하다.

### 5. 주의할 사항 및 정리

**1) `filterChain.doFilter()` 호출을 빠뜨리지 않는다**

맨 마지막의 `filterChain.doFilter(request, response);`는 "검사가 끝났으니 다음 필터나 컨트롤러로 보내라"는 뜻이다. 이 줄을 빠뜨리면 요청이 중간에 끊겨서 응답이 오지 않는다. 토큰이 있든 없든, 검증에 성공하든 실패하든 **무조건 마지막에 호출**해야 한다.

**2) 토큰이 없거나 잘못되어도 필터에서 에러를 던지지 않는다**

로그인이나 회원가입처럼 **토큰 없이 들어와야 하는 공개 요청**도 이 필터를 지나간다. 필터에서 예외를 던져 막아 버리면 아무도 로그인할 수 없다. 토큰이 없거나 잘못됐으면 `SecurityContext`에 아무것도 넣지 않고 그냥 넘긴다. 그러면 공개 경로는 통과하고, 인증이 필요한 경로는 뒤쪽 **인가 단계**에서 스프링 시큐리티가 막는다.

```
 토큰 없음 / 잘못된 토큰 ─▶ 필터: SecurityContext 비워 둔 채 통과
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
   /api/member/auth/login (permitAll)   /api/admin/menus (hasRole ADMIN)
            통과 ✔                          인가 단계에서 거절 ✘
```

> **추가 설명 — 거절될 때 401이 아니라 403이 나올 수 있다**: 폼 로그인과 HTTP Basic을 끈 상태에서 `AuthenticationEntryPoint`를 따로 정하지 않으면, 스프링 시큐리티는 로그인하지 않은 사용자도 **403 Forbidden**으로 돌려보낸다. "로그인이 필요함(401)"과 "권한이 없음(403)"을 프론트가 구분하려면, 마무리의 남은 작업처럼 401을 돌려주는 `AuthenticationEntryPoint`를 등록해야 한다.

### 6. 3부 마무리

지금까지 만든 `JwtProvider`와 `JwtAuthenticationFilter`로 다음 일이 가능해졌다.

- **자동화된 토큰 검증**: 요청 헤더에서 JWT를 읽어 유효성을 검사한다.
- **보안 컨텍스트 반영**: 정상 토큰이면 `SecurityContextHolder`에 인증 객체를 등록해서, 이후 로직에서 현재 로그인한 사용자 정보를 꺼내 쓸 수 있다.

하지만 아직 필터를 `SecurityConfig`에 **등록하지 않았으므로 지금 상태로는 동작하지 않는다**. 4부에서 등록한다.

---

## 4부. SecurityConfig에 JwtAuthenticationFilter 등록 및 접근 권한 설정하기

3부에서는 출입구에서 방문객의 토큰을 검사하는 보안 요원인 `JwtAuthenticationFilter`를 만들었다. 하지만 보안 요원을 만들어 두기만 하고 건물 출입구에 배치하지 않으면 아무 소용이 없다. 4부에서는 스프링 시큐리티의 제어실인 `SecurityConfig` 클래스를 만들어 필터를 출입구에 세우고, 토큰 기반 인증에 맞는 보안 규칙을 설정한다.

### 1. SecurityConfig와 JWT 보안 설정의 필요성

스프링 시큐리티는 기본적으로 매우 엄격한 보안 규칙으로 동작한다. 기본 설정에서는 모든 요청에 전통적인 로그인 폼과 세션 방식을 쓰려고 한다.

하지만 우리는 JWT 토큰 방식을 쓰기로 했다. 그래서 스프링 시큐리티 제어실에 "세션 대신 토큰을 쓸 것이고, 우리가 만든 보안 요원이 먼저 출입증을 확인하게 하겠다"라고 규칙을 다시 정해 주어야 한다.

이 설정을 담는 곳이 `@Configuration`과 `@EnableWebSecurity`를 붙인 `SecurityConfig` 클래스다. 기본 골격은 다음과 같다.

```java
package com.ncafe.backend.config;

...
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
            // 이 부분에 설정을 추가할 예정이다.

        return http.build();
    }
}
```

> **추가 설명 — `SecurityFilterChain` 빈을 만드는 순간 기본 설정이 빠진다**: 3부 1절에서 본 "모든 API가 막히고 기본 로그인 페이지가 뜨는" 동작은, 내가 만든 `SecurityFilterChain` 빈이 **없을 때만** 스프링 부트가 대신 넣어 주는 설정이다. 이 빈을 직접 등록하면 그 기본 설정은 통째로 빠지고, 여기에 적은 규칙만 적용된다. 그래서 폼 로그인과 HTTP Basic도 `http.formLogin(...)`, `http.httpBasic(...)`을 부르지 않는 한 켜지지 않는다.

### 2. 세션 관리와 CSRF 비활성화하기

JWT 토큰 인증을 쓸 때는 기존의 서버 중심 보안 설정 두 가지를 바꿔야 한다.

**1) CSRF(사이트 간 요청 위조) 비활성화**

세션 기반 로그인에서는 웹 브라우저가 쿠키를 **자동으로** 서버에 보내는 특성을 이용한 공격(CSRF)을 막으려고 CSRF 토큰 검사가 꼭 필요했다. JWT 방식에서는 쿠키 대신 **HTTP 요청 헤더에 직접 토큰을 실어** 보내므로 쿠키 자동 전송 공격에서 상대적으로 자유롭다. 그래서 CSRF 보호 기능을 꺼도 된다.

| 구분 | 세션(쿠키) 방식 | JWT(헤더) 방식 |
|---|---|---|
| 신원 정보를 보내는 방법 | 브라우저가 쿠키(세션 ID)를 **자동 전송** | 프론트 코드가 `Authorization` 헤더에 **직접** 넣음 |
| 공격자 사이트가 우리 서버로 요청을 보내면 | 사용자 쿠키가 자동으로 따라감 → 사용자인 척 요청 성공 | 헤더는 자동으로 붙지 않음 → 토큰 없는 요청이 되어 거절 |
| 서버 상태 | 세션을 서버 메모리에 저장 (Stateful) | 저장하지 않음 (Stateless) |
| CSRF 방어 | CSRF 토큰 검사 필요 | 꺼도 됨 (공격 위험 낮음) |

```
[세션 방식]
 사용자 브라우저 ──요청 + 쿠키(세션 ID) 자동 전송──▶ 서버 (세션: 사용자)
 공격자 사이트   ──위조 요청 (쿠키가 자동으로 따라감)─▶ 서버 ─▶ CSRF 토큰 검사로 막아야 함

[JWT 방식]
 사용자 브라우저 ──요청 + Authorization: Bearer 토큰──▶ 서버 (무상태)
 공격자 사이트   ──위조 요청 (토큰 없음)──────────────▶ 서버 ─▶ 인증 실패, CSRF 방어 불필요
```

> **추가 설명 — 토큰을 쿠키에 담으면 CSRF 방어가 다시 필요하다**: "CSRF를 꺼도 된다"는 것은 토큰을 **헤더로 보낼 때만** 맞는 말이다. XSS를 피하려고 토큰을 `HttpOnly` 쿠키에 넣는 방식(BFF 구조 등)이라면, 브라우저가 그 쿠키를 다시 자동으로 보내므로 CSRF 위험이 되살아난다. 그때는 쿠키에 `SameSite=Lax` 또는 `Strict`를 주거나 CSRF 보호를 다시 켜야 한다.

**2) 세션 정책을 STATELESS(무상태)로 설정**

스프링 시큐리티의 기본 동작은 사용자가 로그인하면 서버 메모리에 세션을 만들어 기억하는 것이다. 하지만 JWT를 쓰는 이유는 서버에 상태를 저장하지 않고(Stateless) 들어오는 토큰만 보고 신원을 확인하기 위해서다. 그래서 서버가 세션을 만들거나 기억하지 않도록 세션 정책을 `STATELESS`로 설정한다.

두 설정은 다음 절 코드에서 확인한다.

### 3. JwtAuthenticationFilter 등록 및 경로별 권한 설정

이제 제어실 설정 코드에서 보안 요원(`JwtAuthenticationFilter`)을 배치하고, 손님이 들어올 수 있는 길을 나눈다.

```java
package com.ncafe.backend.config;

import com.ncafe.backend.security.jwt.JwtAuthenticationFilter;
import com.ncafe.backend.security.jwt.JwtProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
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
            // 1. CSRF 비활성화
            .csrf(AbstractHttpConfigurer::disable)

            // 2. 세션을 사용하지 않으므로 STATELESS로 설정
            .sessionManagement(session -> 
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )

            // 3. 경로별 접근 권한 설정
            .authorizeHttpRequests(auth -> auth
                // 로그인, 회원가입 등 공개 API는 토큰 없이도 접근 허용
                .requestMatchers("/api/auth/**").permitAll()
                // 그 외의 모든 요청은 인증된 사용자만 접근 가능
                .anyRequest().authenticated()
            )

            // 4. 커스텀 JWT 필터를 UsernamePasswordAuthenticationFilter 앞에 배치
            .addFilterBefore(
                new JwtAuthenticationFilter(jwtProvider), 
                UsernamePasswordAuthenticationFilter.class
            );

        return http.build();
    }
}
```

**코드 주요 부분 살펴보기**

- `csrf(AbstractHttpConfigurer::disable)`: 토큰 방식을 쓰므로 CSRF 방어 기능을 끈다.
- `sessionCreationPolicy(SessionCreationPolicy.STATELESS)`: 서버가 세션을 만들거나 저장하지 않도록 단단히 일러 둔다.
- `requestMatchers("/api/auth/**").permitAll()`: 로그인, 회원가입은 처음 오는 손님이 지나는 길이므로 토큰이 없어도 들어오게 문을 열어 둔다.
- `anyRequest().authenticated()`: 공개한 문 말고 다른 모든 길은 반드시 출입증(토큰)을 보여 줘야 들어가게 막는다.
- `addFilterBefore(..., UsernamePasswordAuthenticationFilter.class)`: 우리가 만든 `JwtAuthenticationFilter`를 스프링 시큐리티의 기본 아이디/비밀번호 검사 필터보다 **앞에** 세운다. 그래야 요청이 들어오자마자 토큰을 먼저 검사해서 로그인 상태로 만들어 줄 수 있다.

> **추가 설명 — `AbstractHttpConfigurer::disable`과 `csrf -> csrf.disable()`은 같다**: 메서드 참조로 줄여 쓴 것일 뿐 동작은 같다. ncafe 스타터는 `csrf -> csrf.disable()` 모양을 쓴다.

> **추가 설명 — `UsernamePasswordAuthenticationFilter`는 "위치 표시"로만 쓰인다**: 폼 로그인을 켜지 않았으므로 이 필터는 실제로는 체인에 **없다**. 그래도 스프링 시큐리티는 필터마다 정해진 순서 번호를 갖고 있어서, 이 클래스를 기준점으로 "그 번호 바로 앞"에 우리 필터를 끼워 넣는다. 정말 중요한 조건은 체인 맨 끝에서 접근 권한을 판단하는 **`AuthorizationFilter`보다 먼저** 실행되는 것이다. 그 전에 `SecurityContext`가 채워져 있어야 `authenticated()`를 통과한다.

> **추가 설명 — 공개 경로는 실제 컨트롤러 주소와 맞춰야 한다**: 원문은 `/api/auth/**`를 열었지만, 3부 5절 그림처럼 ncafe는 `/api/member/auth/**`가 로그인/가입 경로다. 경로 이름은 프로젝트마다 다르므로 컨트롤러의 `@RequestMapping`과 똑같이 맞춘다. 참고로 ncafe 스타터의 규칙은 아래와 같다. 마지막을 `authenticated()`가 아니라 **`denyAll()`** 로 두어서, 목록에 없는 경로는 로그인했어도 막는다(허용할 경로만 골라 여는 방식).
>
> ```java
> .authorizeHttpRequests(auth -> auth
>         .requestMatchers("/api/user/**").permitAll()          // 누구나
>         .requestMatchers("/api/member/auth/**").permitAll()   // 누구나 (가입, 로그인)
>         .requestMatchers("/api/member/**").authenticated()    // 로그인한 회원
>         .requestMatchers("/api/admin/**").hasRole("ADMIN")    // 관리자
>         .requestMatchers(HttpMethod.GET, "/actuator/health").permitAll()
>         .anyRequest().denyAll())
> ```
>
> 규칙은 **위에서부터 처음 맞는 것 하나만** 적용되므로, 좁은 경로(`/api/member/auth/**`)를 넓은 경로(`/api/member/**`)보다 먼저 쓴다.

### 4. 주의할 사항 및 정리

`SecurityConfig`를 설정할 때 실수하기 쉬운 지점들이다.

**1) 필터 순서(addFilterBefore)의 중요성**

커스텀 필터 위치를 잘못 지정하면 토큰을 가지고 들어와도 인증 처리가 되지 않는다. 반드시 `UsernamePasswordAuthenticationFilter`보다 먼저 실행되게 해야, 뒤따르는 보안 필터들이 "이미 인증이 끝난 손님이구나" 하고 통과시킨다.

**2) 세션 정책 설정 누락 금지**

`SessionCreationPolicy.STATELESS` 설정을 빠뜨리면, 토큰 인증에 성공했을 때 스프링 시큐리티가 슬그머니 세션을 만들어 버린다. 그러면 처음 한 번만 토큰이 유효하면 그 뒤에는 토큰이 만료되어도 세션 때문에 로그인 상태가 유지되는 이상한 현상이 생길 수 있다.

> 원문 바로잡기 — 이 현상은 주로 **스프링 시큐리티 5 이전**의 이야기다. 그때는 요청이 끝날 때 `SecurityContext`를 세션에 **자동 저장**했다. 스프링 시큐리티 6부터(부트 3, 4)는 필터에서 `SecurityContextHolder`에 넣기만 한 인증 정보를 세션에 자동으로 저장하지 않으므로, 우리 필터 구조에서는 이 현상이 보통 생기지 않는다. 그래도 `STATELESS`는 꼭 켠다. 켜 두지 않으면 접근이 거절될 때 원래 요청을 세션에 보관하는 기능(`RequestCache`) 같은 곳에서 세션과 `JSESSIONID` 쿠키가 생길 수 있고, "서버는 상태를 갖지 않는다"는 설계 의도를 코드에 분명히 적어 두는 역할도 한다.

**3) 공개 경로 설정 확인**

로그인 API(`/api/auth/login`)나 회원가입 API 같은 경로를 `permitAll()`에 등록하지 않으면, 토큰을 발급받으러 온 손님조차 "토큰이 없다"는 이유로 입구에서 막힌다. 토큰 없이 호출되어야 하는 경로는 반드시 적어 둔다.

> **추가 설명 — `/error`도 막히면 진짜 에러가 403으로 가려진다**: 컨트롤러에서 예외가 나면 스프링 부트는 내부적으로 `/error` 경로로 요청을 다시 보내 에러 응답을 만든다. 그런데 `/error`가 `anyRequest().authenticated()`에 걸리면, 로그인 안 한 사용자의 요청은 원래의 400이나 500 대신 **403만** 받게 되어 원인을 찾기 어렵다. 개발 중 "분명 공개 경로인데 403이 난다"면 `.requestMatchers("/error").permitAll()`을 추가해 본다.

이제 스프링 시큐리티는 서버로 들어오는 모든 요청에 대해 `JwtAuthenticationFilter`를 먼저 거치게 동작한다. 토큰이 유효하면 로그인 처리까지 자동으로 끝난다.

---

## 마무리

이 실습에서는 JWT 인증 환경을 만들기 위해 `JwtAuthenticationFilter`를 작성하고, `SecurityConfig`로 스프링 시큐리티 체인에 이 커스텀 필터를 등록, 배치했다. 이로써 HTTP 요청이 컨트롤러에 닿기 전에 요청 헤더의 JWT 유효성을 가장 먼저 검증하고, 스프링 시큐리티의 `SecurityContext`에 인증 객체를 저장하는 기초 보안 구조가 완성되었다.

```
요청 ─▶ JwtAuthenticationFilter ─▶ (UsernamePasswordAuthenticationFilter 자리) ─▶ AuthorizationFilter ─▶ 컨트롤러
          토큰 검증 → SecurityContext 등록                                         permitAll / authenticated 판단
```

토큰을 검증하고 통과시키는 입구는 마련되었으므로, 다음 작업이 남는다.

| 남은 작업 | 내용 |
|---|---|
| 인증 Controller 및 Service 구현 | 로그인 요청이 오면 사용자 정보를 확인하고, 검증된 사용자에게 Access Token과 Refresh Token을 만들어 발급하는 API |
| Refresh Token을 활용한 재발급 및 만료 처리 | Access Token이 만료되면 안전하게 토큰을 갱신하는 로직, 로그아웃과 토큰 무효화 처리 |
| 예외 처리 (Exception Handling) | 잘못되었거나 만료된 토큰으로 접근하면 스프링 시큐리티 단에서 `401 Unauthorized` 같은 커스텀 JSON 응답을 주도록 `AuthenticationEntryPoint`와 `AccessDeniedHandler` 설정 |
