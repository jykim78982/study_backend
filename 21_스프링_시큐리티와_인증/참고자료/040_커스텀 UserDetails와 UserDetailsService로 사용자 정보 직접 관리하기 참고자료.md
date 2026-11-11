---
tags: [스프링시큐리티, UserDetails, UserDetailsService, 커스텀인증, AuthenticationPrincipal, SecurityContextHolder, BCrypt, 참고자료]
---

> 🔗 관련 노트: [[039_JDBC를 활용한 사용자 관리와 데이터베이스 기반 인증 참고자료]] · [[098_스프링 시큐리티 인가 설정 — URL별 허용 규칙, 역할, 커스텀 로그인 페이지]] · [[093_서블릿 필터와 스프링 시큐리티 입문 — 필터 체인, @Bean, UserDetailsService]]

# 커스텀 UserDetails와 UserDetailsService로 사용자 정보 직접 관리하기

지난 노트에서는 `InMemoryUserDetailsManager`를 사용해 메모리에 임시 계정을 올리고 URL 권한을 설정했다. 하지만 실제 서비스를 만들 때는 메모리가 아니라 데이터베이스(DB)에 회원 정보를 저장하고 불러와야 한다.

또한 스프링 시큐리티가 기본으로 제공하는 계정 정보에는 아이디와 비밀번호, 권한 목록만 들어있다. 실제 서비스에서는 화면에 사용자의 진짜 이름이나 닉네임, 이메일 같은 추가 정보를 보여주어야 하는 경우가 많다.

이번 노트에서는 DB와 연동하고 원하는 추가 정보까지 함께 다룰 수 있도록 커스텀 `UserDetails`와 `UserDetailsService`를 만드는 방법을 다룬다.

## 1. 왜 커스텀 클래스가 필요한가?

스프링 시큐리티 내부에서 인증된 사용자 정보는 `UserDetails`라는 기본 규격(인터페이스)에 담겨 관리된다.

기본으로 제공되는 `User` 클래스는 단순하다. 아이디(Username), 비밀번호(Password), 권한(Authorities) 딱 세 가지만 들어있다.

```
 1. 기본 User 객체 (사용 불가)              2. 커스텀 UserDetails 필요성

 User {                                     CustomUserDetails
   username                                 ┌──────────────┬──────────────┐
   password                                 │ Username     │ name     ✚   │
   authorities                              │ Password     │ nickname ✚   │
   nickname ?   ✗  ← 없는 필드              │ Authorities  │              │
 }                                          └──────────────┴──────────────┘
        │ 컨트롤러에서 접근                              │ 컨트롤러에서 접근
        ▼                                               ▼
 username·password·authorities뿐            원하는 추가 정보(nickname)를 바로 꺼냄 ✓
 nickname → 꺼낼 수 없음 ✗ (DB 재조회 필요)
```

> 원문 바로잡기 — 기본 `User` 클래스에는 아이디·비밀번호·권한 외에도 **계정 상태 값 네 가지**(`enabled`, `accountNonExpired`, `accountNonLocked`, `credentialsNonExpired`)가 들어 있다. 2절의 `isEnabled()` 등이 바로 이것이다. "세 가지만"은 **사용자를 설명하는 정보**가 그것뿐이라는 뜻으로 읽으면 된다. 이름·닉네임·이메일 같은 서비스 고유 정보를 넣을 자리가 없다는 것이 핵심이다.

만약 로그인한 사용자의 '이름(Name)'이나 '닉네임(Nickname)'을 화면에 띄우고 싶다면 어떻게 해야 할까? 기본 `User` 객체만 사용하면 로그인 후에 DB를 다시 조회해야 하는 번거로움이 생긴다.

스프링 시큐리티의 세션 공간에 내 서비스에 필요한 회원 정보(이름, 닉네임 등)를 한 번에 담아두고 꺼내 쓰기 위해 `UserDetails`를 직접 구현한 커스텀 클래스가 필요하다.

> **추가 설명 — "세션 공간"은 어디인가**: 로그인에 성공하면 `UserDetails` 객체는 인증 객체(`Authentication`)의 **principal**(주체)로 들어가고, 이 인증 객체가 `SecurityContext`에 담겨 세션에 저장된다. 요청이 올 때마다 스프링 시큐리티가 세션에서 이것을 꺼내 `SecurityContextHolder`에 올려 두므로, 코드 어디서든 꺼내 쓸 수 있다.
>
> ```
> HttpSession
>  └─ SPRING_SECURITY_CONTEXT
>       └─ SecurityContext
>            └─ Authentication
>                 ├─ principal    = CustomUserDetails(username, name, nickname, ...)
>                 ├─ credentials  = (비밀번호, 인증 후 지워짐)
>                 └─ authorities  = [ROLE_USER]
> ```

## 2. 추가 정보를 담는 커스텀 UserDetails 구현

우선 `UserDetails` 인터페이스를 구현하는 나만의 사용자 클래스를 만든다. 여기서는 기본 필드 외에 사용자의 실제 이름(`name`)과 닉네임(`nickname`)을 추가한다.

**CustomUserDetails.java**

```java
package com.example.security.user;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;

public class CustomUserDetails implements UserDetails {

    private final String username; // 로그인 아이디
    private final String password; // 암호화된 비밀번호
    private final String name;     // 사용자 이름 (추가 정보)
    private final String nickname; // 닉네임 (추가 정보)
    private final Collection<? extends GrantedAuthority> authorities; // 권한 목록

    public CustomUserDetails(String username, String password, String name, String nickname, Collection<? extends GrantedAuthority> authorities) {
        this.username = username;
        this.password = password;
        this.name = name;
        this.nickname = nickname;
        this.authorities = authorities;
    }

    // 커스텀으로 추가한 Getter 메서드
    public String getName() {
        return name;
    }

    public String getNickname() {
        return nickname;
    }

    // UserDetails 인터페이스 필수 구현 메서드들
    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return authorities;
    }

    @Override
    public String getPassword() {
        return password;
    }

    @Override
    public String getUsername() {
        return username;
    }

    // 계정 만료 여부 (true: 만료 안 됨)
    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    // 계정 잠금 여부 (true: 잠기지 않음)
    @Override
    public boolean isAccountNonLocked() {
        return true;
    }

    // 비밀번호 만료 여부 (true: 만료 안 됨)
    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    // 계정 활성화 여부 (true: 활성화)
    @Override
    public boolean isEnabled() {
        return true;
    }
}
```

이제 로그인 성공 시 화면이나 컨트롤러에서 사용자의 닉네임이나 이름을 바로 꺼내서 쓸 수 있게 된다.

> **추가 설명 — 상태 메서드 네 개는 생략할 수 있다**: 스프링 시큐리티 6.x부터 `isAccountNonExpired()` 등 네 메서드는 인터페이스에 `default`로 `true`를 돌려주도록 들어 있다. 그래서 위처럼 전부 `true`라면 적지 않아도 된다. 반대로 DB에 `enabled`, 잠금 여부 같은 컬럼이 있다면 하드코딩한 `true` 대신 **그 값을 돌려줘야** 정지된 회원의 로그인이 막힌다.
>
> | 메서드가 `false`를 돌려주면 | 로그인 결과 |
> |---|---|
> | `isEnabled()` | `DisabledException` — 비활성 계정 |
> | `isAccountNonLocked()` | `LockedException` — 잠긴 계정(비밀번호 여러 번 틀림 등) |
> | `isAccountNonExpired()` | `AccountExpiredException` — 기간이 끝난 계정 |
> | `isCredentialsNonExpired()` | `CredentialsExpiredException` — 비밀번호 변경 기한 지남 |

> **추가 설명 — `getName()`과 `authentication.getName()`은 다르다**: 여기서 만든 `getName()`은 "뉴렉처" 같은 **실제 이름**을 돌려준다. 반면 스프링 시큐리티의 `Authentication.getName()`은 **로그인 아이디**(`getUsername()` 값)를 돌려준다. 이름이 같아서 헷갈리기 쉬우므로, 실무에서는 커스텀 필드를 `realName`, `displayName`처럼 겹치지 않게 짓기도 한다.

> **추가 설명 — 엔티티를 통째로 넣지 않는다**: 이 객체는 세션에 저장되므로 화면에 자주 쓰는 **작은 값**(id, 이름, 닉네임)만 담는다. JPA 엔티티(`Member`)를 필드로 통째로 넣으면, 지연 로딩 연관관계가 세션 밖에서 터지거나(`LazyInitializationException`) 세션이 무거워진다. 또 세션에 담긴 값은 **로그인한 순간의 복사본**이라, 회원이 닉네임을 바꿔도 다시 로그인하기 전까지는 예전 닉네임이 보인다. 정보 수정 기능을 만들 때 기억해 둔다.

> **추가 설명 — 비밀번호가 세션에 남는 문제**: 스프링의 기본 `User` 클래스는 `CredentialsContainer`를 구현해서, 인증이 끝나면 스프링 시큐리티가 `eraseCredentials()`를 불러 비밀번호를 `null`로 지운다. 위 `CustomUserDetails`는 이것을 구현하지 않아 **BCrypt 해시가 세션에 계속 남는다.** 해시라서 바로 위험하진 않지만, 지우고 싶다면 `password` 필드에서 `final`을 빼고 아래처럼 추가한다.
>
> ```java
> public class CustomUserDetails implements UserDetails, CredentialsContainer {
>     private String password;   // final 제거
>     ...
>     @Override
>     public void eraseCredentials() {
>         this.password = null;
>     }
> }
> ```

## 3. DB 연동을 위한 커스텀 UserDetailsService 구현

스프링 시큐리티는 사용자가 로그인 폼에 아이디를 입력하고 제출하면, 등록된 `UserDetailsService` 객체의 `loadUserByUsername()` 메서드를 호출한다.

이 메서드 안에서 DB나 저장소를 조회해 회원 데이터를 가져온 뒤, 방금 만든 `CustomUserDetails` 객체로 포장해 반환해주기만 하면 된다.

**CustomUserDetailsService.java**

```java
package com.example.security.user;

import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class CustomUserDetailsService implements UserDetailsService {

    // 실제 프로젝트에서는 JPA Repository나 MyBatis Mapper 등을 주입받아 사용한다.
    // private final UserRepository userRepository;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {

        // 1. DB에서 username으로 회원 정보를 조회하는 과정을 시뮬레이션한다.
        // 예: Member member = userRepository.findByEmail(username)
        //         .orElseThrow(() -> new UsernameNotFoundException("사용자를 찾을 수 없습니다: " + username));

        // 예시를 위한 임시 가상 DB 조회 처리
        if (!"newlec@newlecture.com".equals(username)) {
            // 사용자가 없으면 반드시 UsernameNotFoundException 예외를 던져야 한다.
            throw new UsernameNotFoundException("존재하지 않는 사용자입니다: " + username);
        }

        // DB에서 가져온 회원의 권한 정보 생성 (ROLE_ 접두사 사용)
        List<SimpleGrantedAuthority> authorities = List.of(new SimpleGrantedAuthority("ROLE_USER"));

        // 2. 조회한 DB 회원 정보를 커스텀 UserDetails 객체에 담아서 반환한다.
        // (주의: 비밀번호는 반드시 BCrypt 등으로 암호화된 상태로 DB에 들어있어야 한다)
        return new CustomUserDetails(
                "newlec@newlecture.com",
                "$2a$10$8.UnVuG9HHgffUDAlk8qfOUVGkqRzgVymGe07xd00DMxs.AQp.o.O", // "1111"의 BCrypt 암호화 값
                "뉴렉처",
                "newlec_nick",
                authorities
        );
    }
}
```

> **추가 설명 — 해시 값은 직접 만들어 넣는다**: 자료의 해시가 정말 `"1111"`인지는 눈으로 확인할 수 없다. 로그인이 계속 실패하면 해시가 틀렸을 가능성이 크므로, 같은 인코더로 만든 값을 넣는다. BCrypt는 실행할 때마다 다른 값이 나오지만 어느 것이든 `matches()`로 검증된다.
>
> ```java
> System.out.println(new BCryptPasswordEncoder().encode("1111"));
> ```

> **추가 설명 — 아이디가 이메일이어도 폼 필드 이름은 `username`이다**: 이 예시는 이메일을 아이디로 쓰지만, 메서드 이름은 여전히 `loadUserByUsername`이고 매개변수에는 로그인 폼의 `username` 필드 값이 들어온다. 직접 만든 로그인 폼의 입력칸을 `name="email"`로 했다면 스프링 시큐리티가 값을 찾지 못하므로, 입력칸 이름을 `username`으로 두거나 설정에서 바꿔 준다.
>
> ```java
> .formLogin(form -> form
>         .loginPage("/login")
>         .usernameParameter("email"))   // 폼의 name="email" 값을 아이디로 사용
> ```

> **추가 설명 — 실제 DB 연동 형태**: 주석으로 된 부분을 실제로 채우면 아래와 같은 모양이 된다. `Member` 엔티티에 이름·닉네임·권한이 있다고 가정한다.
>
> ```java
> @Service
> @RequiredArgsConstructor
> public class CustomUserDetailsService implements UserDetailsService {
>
>     private final MemberRepository memberRepository;
>
>     @Override
>     public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
>         Member member = memberRepository.findByEmail(username)
>                 .orElseThrow(() -> new UsernameNotFoundException("존재하지 않는 사용자입니다: " + username));
>
>         List<SimpleGrantedAuthority> authorities = member.getRoles().stream()
>                 .map(role -> new SimpleGrantedAuthority("ROLE_" + role.getName()))   // "USER" → "ROLE_USER"
>                 .toList();
>
>         return new CustomUserDetails(
>                 member.getEmail(),
>                 member.getPassword(),   // DB에 저장된 BCrypt 해시
>                 member.getName(),
>                 member.getNickname(),
>                 authorities);
>     }
> }
> ```

## 4. 시큐리티 설정 연결 및 결과 확인

커스텀 `UserDetailsService` 클래스에 `@Service` 어노테이션을 붙여두면, 스프링 시큐리티가 이를 자동으로 감지하여 로그인 인증 서비스로 사용한다.

따라서 기존 `SecurityConfig.java`에 작성했던 메모리 기반 사용자 설정(`InMemoryUserDetailsManager`) 빈은 삭제하면 된다.

> **추가 설명 — 왜 반드시 삭제해야 하나**: 스프링 시큐리티는 `UserDetailsService` 타입 빈이 **딱 하나**일 때만 그것을 자동으로 로그인에 연결한다. `@Service`로 만든 커스텀 서비스와 메모리용 빈이 둘 다 남아 있으면 어느 쪽도 자동으로 고르지 않고, 로그인이 엉뚱하게 실패한다. 같은 이유로 `PasswordEncoder` 빈도 하나만 두며, 이 빈이 함께 자동 연결되어 `matches()` 비교에 쓰인다.

**SecurityConfig.java (정리된 설정)**

```java
package com.example.security.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(authorize -> authorize
                .requestMatchers("/", "/menus", "/menus/*").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .requestMatchers("/my").hasRole("USER")
                .anyRequest().authenticated()
            )
            .formLogin(Customizer.withDefaults());

        return http.build();
    }
}
```

이제 로그인 폼에 아이디(`newlec@newlecture.com`)와 비밀번호(`1111`)를 입력하면 `CustomUserDetailsService`가 실행되어 인증이 처리된다.

```
POST /login (username=newlec@newlecture.com, password=1111)
   │
   ▼
DaoAuthenticationProvider
   ├─ customUserDetailsService.loadUserByUsername("newlec@newlecture.com")
   │      └─ CustomUserDetails(이메일, BCrypt 해시, "뉴렉처", "newlec_nick", [ROLE_USER])
   ├─ 계정 상태 확인 (isEnabled 등)
   ├─ passwordEncoder.matches("1111", BCrypt 해시)
   ▼
Authentication(principal = CustomUserDetails) → SecurityContext → 세션
```

인증이 완료된 후 서비스 코드나 화면에서 아래와 같이 로그인한 사용자의 이름과 닉네임에 접근할 수 있다.

```java
// 컨트롤러나 서비스에서 로그인 정보 꺼내기
Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();

System.out.println("로그인한 사용자 이름: " + userDetails.getName());     // 뉴렉처
System.out.println("로그인한 사용자 닉네임: " + userDetails.getNickname()); // newlec_nick
```

> **추가 설명 — 컨트롤러에서는 `@AuthenticationPrincipal`이 더 간단하다**: 위 코드는 어디서든 쓸 수 있지만, 컨트롤러에서는 매개변수에 어노테이션을 붙이면 스프링이 principal을 꺼내 형변환까지 해서 넣어 준다.
>
> ```java
> @GetMapping("/my")
> public String my(@AuthenticationPrincipal CustomUserDetails user, Model model) {
>     model.addAttribute("nickname", user.getNickname());
>     return "my";
> }
> ```

> **추가 설명 — 로그인 안 한 요청에서는 형변환이 터진다**: `permitAll()`인 페이지에 로그인하지 않고 들어오면 인증 객체는 **익명 사용자**이고, `getPrincipal()`은 `CustomUserDetails`가 아니라 문자열 `"anonymousUser"`를 돌려준다. 이때 위처럼 `(CustomUserDetails)`로 형변환하면 `ClassCastException`이 난다. `@AuthenticationPrincipal`은 이 경우 `null`을 넣어 주므로 `null` 확인만 하면 된다.
>
> ```java
> @GetMapping("/")
> public String index(@AuthenticationPrincipal CustomUserDetails user, Model model) {
>     if (user != null) {
>         model.addAttribute("nickname", user.getNickname());
>     }
>     return "index";
> }
> ```

> **추가 설명 — 타임리프 화면에서 바로 꺼내기**: `thymeleaf-extras-springsecurity6` 의존성을 추가하면 템플릿에서 principal의 필드를 직접 읽을 수 있다.
>
> ```groovy
> implementation 'org.thymeleaf.extras:thymeleaf-extras-springsecurity6'
> ```
>
> ```html
> <html xmlns:th="http://www.thymeleaf.org"
>       xmlns:sec="http://www.thymeleaf.org/extras/spring-security">
>
> <span sec:authorize="isAuthenticated()">
>     <span sec:authentication="principal.nickname"></span>님 환영합니다
> </span>
> <a sec:authorize="isAnonymous()" href="/login">로그인</a>
> <a sec:authorize="hasRole('ADMIN')" href="/admin">관리자</a>
> ```
>
> `principal.nickname`은 `getNickname()`을 부른다.

## 5. 주의할 사항

### 1) 존재하지 않는 회원은 예외(UsernameNotFoundException)를 발생시켜야 한다

DB 조회 결과 사용자가 없다고 해서 `null`을 반환하면 안 된다. 스프링 시큐리티 내부 흐름에 문제가 발생할 수 있으므로, 사용자를 찾지 못한 경우에는 반드시 `UsernameNotFoundException` 예외를 던져야 한다.

```java
// 올바른 예시
throw new UsernameNotFoundException("사용자를 찾을 수 없습니다.");
```

> **추가 설명 — `null`을 돌려주면 실제로 생기는 일**: 스프링 시큐리티는 `null`을 받으면 "인터페이스 규칙 위반"으로 보고 `InternalAuthenticationServiceException`(`UserDetailsService returned null, which is an interface contract violation`)을 던진다. "아이디 없음"이 아니라 **서버 내부 오류**로 기록되어 원인을 찾기 어려워진다.

> **추가 설명 — "아이디 없음"과 "비밀번호 틀림"은 화면에서 구분되지 않는다**: `UsernameNotFoundException`을 던져도 스프링 시큐리티는 기본적으로 이것을 `BadCredentialsException`(자격 증명 오류)으로 바꿔서 처리한다. 그래서 로그인 화면에는 두 경우 모두 똑같이 "아이디 또는 비밀번호가 올바르지 않습니다"가 뜬다. "이 아이디는 없습니다"라고 알려 주면 공격자가 가입된 아이디를 알아낼 수 있기 때문에 일부러 구분하지 않는 것이다. 예외 메시지에 적은 문구도 사용자에게 보이지 않고 로그용이다.

### 2) DB에 저장된 비밀번호의 암호화 상태

`UserDetailsService`가 반환하는 `UserDetails` 객체의 비밀번호는 DB에 저장되어 있던 암호화된 문자열이어야 한다.

스프링 시큐리티는 사용자가 로그인 화면에서 입력한 평문 비밀번호와 `UserDetails`가 가지고 있는 암호화된 비밀번호를 `PasswordEncoder.matches()`로 비교하여 검증한다. 따라서 회원가입 단계에서 비밀번호를 DB에 넣을 때 반드시 `BCryptPasswordEncoder`로 암호화하여 저장해 두어야 인가가 정상 동작한다.

> 원문 바로잡기 — 비밀번호 비교는 "누구인지 확인"하는 **인증(Authentication)** 단계다. 마지막 문장의 "인가가 정상 동작한다"는 "**인증**(로그인)이 정상 동작한다"로 읽어야 한다. 인가는 그 뒤에 `hasRole("ADMIN")`처럼 권한을 확인하는 단계다.

> **추가 설명 — 회원가입에서 암호화하는 코드**: 같은 `PasswordEncoder` 빈을 주입받아 `encode()`한 값을 저장한다. 평문을 그대로 저장하면 로그인할 때 `matches()`가 실패하고, 로그에 `Encoded password does not look like BCrypt` 경고가 찍힌다.
>
> ```java
> @Service
> @RequiredArgsConstructor
> public class MemberService {
>     private final MemberRepository memberRepository;
>     private final PasswordEncoder passwordEncoder;
>
>     public void join(String email, String rawPassword, String name, String nickname) {
>         String encoded = passwordEncoder.encode(rawPassword);   // $2a$10$...
>         memberRepository.save(new Member(email, encoded, name, nickname));
>     }
> }
> ```

## 6. 마무리

기본 `User` 객체 대신 커스텀 `UserDetails`와 `UserDetailsService`를 사용하면 DB와 연동하여 실제 회원의 정보를 가져올 수 있다.

또한 기본 계정 구조에 얽매이지 않고 이름, 닉네임, 이메일 등 서비스 구현에 필요한 다양한 정보를 로그인 세션 안에서 안전하고 편리하게 관리할 수 있다.

> **추가 설명 — 지금까지의 사용자 조회 방식 정리**:
>
> | 방식 | 사용자를 어디서 찾나 | 추가 정보(닉네임 등) |
> |---|---|---|
> | `InMemoryUserDetailsManager` | 코드에 적은 메모리 목록 | 불가 |
> | `JdbcUserDetailsManager` | 지정한 SQL로 DB 조회 | 불가 (기본 `User`로 반환) |
> | 커스텀 `UserDetailsService` + 커스텀 `UserDetails` (이 노트) | Repository 등 원하는 방식으로 DB 조회 | **가능** |
>
> 세 방식 모두 스프링 시큐리티 입장에서는 "아이디를 주면 `UserDetails`를 돌려주는 `UserDetailsService`"라는 점에서 같다. 바꿔 끼우는 부품이 다를 뿐, 비밀번호 비교·세션 저장·인가 흐름은 그대로다.
