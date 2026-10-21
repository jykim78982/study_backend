---
tags: [스프링부트, 필터, Filter, FilterChain, 스프링시큐리티, SpringSecurity, Bean, UserDetailsService, 인증, 로그인]
---

> 🔗 관련 노트: [[089_엔터프라이즈 애플리케이션 구조와 스프링의 역할 — 큰 그림 정리]] · [[088_AOP와 프록시 — 곁다리 코드를 호출 흐름 밖으로 빼는 방법]] · [[035_MVC 패턴과 모델2(서블릿·JSP 분리)]] · [[073_스프링 DI]]

# 서블릿 필터와 스프링 시큐리티 입문 — 필터 체인, @Bean, UserDetailsService

스프링은 DI에서 시작해 트랜잭션, 데이터 접근까지 도와주는 **라이브러리**다. 이번에는 스프링이 제공하는 **보안(Spring Security)**을 다룬다. 스프링 시큐리티의 기술적 바탕은 **필터**이므로, 필터를 직접 만들어 보는 것부터 시작한다.

| 스프링 기능 | 이해하려면 알아야 할 기반 |
|---|---|
| DI | IoC 컨테이너 |
| 트랜잭션 | AOP |
| **시큐리티** | **필터** |

## 1. 필터 — 모든 요청이 거쳐 가는 성문

### 서블릿은 하나, 컨트롤러는 여러 개

스프링 부트를 쓰면 서블릿은 **하나**다. 모든 요청을 먼저 받아 알맞은 컨트롤러로 넘겨주는 이 서블릿을 **프론트 컨트롤러**라고 하고, 스프링의 구현체 이름이 `DispatcherServlet`이다. 덕분에 우리가 만드는 컨트롤러는 서블릿을 상속하지 않는 POJO가 된다.

### 고약한 요청은 어디서 걸러야 하나

요청 중에는 고약한 녀석들이 섞여 들어올 수 있다. 로그인하지 않은 사람, 고객이지만 엉뚱한 것을 숨겨 온 사람 등이다. 이걸 **모든 서블릿이나 모든 컨트롤러마다** 검사한다면 같은 코드가 곳곳에 반복된다.

그래서 이런 검사 코드는 **모든 요청이 반드시 거쳐 가는 앞단**에 둔다. 서블릿 환경은 이를 위한 별도의 클래스를 제공한다.

| 만들고 싶은 것 | 만드는 것 |
|---|---|
| 요청을 처리하는 응용 프로그램 | **서블릿** |
| 그 전에 앞단에서 먼저 실행할 내용 | **필터** |

필터는 들어올 때만 거치는 게 아니라 **나갈 때도** 거친다. 성에 들어오려면 꼭 성문을 지나야 하고, 문지기가 "어디 가십니까? 무슨 목적으로 오셨어요?"를 묻는다. 나갈 때도 "잠깐, 뭘 갖고 나가는지 봅시다"를 한다. 필터는 이런 **입출구**다.

```
          ┌─────── 필터 ───────┐
요청 ━━▶ │  전처리             │ ━━▶ [DispatcherServlet] ━━▶ [Controller]
응답 ◀━━ │  후처리             │ ◀━━
          └────────────────────┘
```

### 필터는 보안 전용이 아니다

필터는 여러 목적으로 쓰고, 목적별로 **여러 개**를 둘 수 있다.

- **보안**: 인증·인가(권한) 검사
- **인코딩**: 요청·응답의 문자 인코딩 설정
- **압축·해제**: 들어올 때 압축을 풀고, 나갈 때 다시 압축
- **로그**: 들어올 때 "이름 적고 가세요", 나갈 때 "이름 확인하고 가세요"
- 그 밖에 **전처리·후처리**가 필요한 모든 작업

> **추가 설명 — 인증과 인가**: 보안 필터가 하는 검사는 두 단계로 나뉜다. 문지기 비유로 보면 이렇다.
>
> | | 묻는 것 | 문지기 비유 | 실패하면 |
> |---|---|---|---|
> | **인증** (Authentication) | **누구냐?** | 신분증을 보고 이 성의 주민인지 확인 | 로그인 페이지로 보낸다 (401) |
> | **인가** (Authorization) | **그걸 해도 되냐?** | 주민이라도 왕궁 안까지 들어갈 자격이 있는지 확인 | 접근을 거부한다 (403) |
>
> 로그인은 인증이고, "관리자만 메뉴 관리 페이지에 들어갈 수 있다"는 인가다. 인증이 먼저 되어야 인가를 할 수 있다. 스프링 시큐리티의 `SecurityFilterChain`에서 "어떤 URL을 누구에게 열어 줄지" 설정하는 부분이 인가에 해당한다.

필터를 만들기만 하면 따로 호출하지 않아도 앞단에서 **저절로** 실행된다. 등록은 설정 한 줄이면 된다.

| 환경 | 필터 등록 방법 |
|---|---|
| 서블릿 직접 사용 | `@WebFilter` 어노테이션 또는 `web.xml`에 필터 선언 |
| 스프링 부트 | 필터 클래스에 `@Component` (IoC에 담기) |

> **추가 설명 — 스프링 부트에서 @WebFilter를 쓰려면**: 스프링 부트는 `@WebFilter`가 붙은 클래스를 기본으로 찾지 않는다. 메인 클래스에 `@ServletComponentScan`을 붙여야 인식한다. 그래서 스프링 부트에서는 `@Component`로 IoC에 담는 방식이 가장 간단하다.

## 2. 필터 직접 만들어 보기

`filter` 폴더를 만들고 `FirstFilter` 클래스를 추가한다. 강사가 준 코드의 패키지명은 프로젝트에 맞게 고친다.

```java
package com.newlecture.springsecurity.filter;   // 내 프로젝트 패키지에 맞게

import jakarta.servlet.*;
import org.springframework.stereotype.Component;
import java.io.IOException;

@Component                                  // IoC에 담아야 스프링이 실행해 준다
public class FirstFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        System.out.println("요청: 필터 전처리");      // 들어올 때

        chain.doFilter(request, response);           // 다음으로 가세요

        System.out.println("완료: 필터 후처리");      // 나갈 때
    }
}
```

### 실험 1 — @Component 없이 실행

`@Component`를 빼고 서버를 실행한 뒤 페이지를 요청하면 콘솔에 아무것도 찍히지 않는다. 필터가 **스프링이 실행할 수 있는 공간**, 즉 IoC 컨테이너에 없기 때문이다. 어떤 객체든 스프링이 인식하려면 IoC에 담겨 있어야 한다. 담을 때 쓰는 어노테이션 중 컨트롤러·서비스·리포지토리는 역할이 맞지 않으므로 **`@Component`**를 쓴다.

### 실험 2 — chain.doFilter()를 주석 처리

`@Component`를 붙이고 `chain.doFilter(...)` 줄을 주석 처리한 뒤 페이지를 요청한다.

- 콘솔에 "요청: 필터 전처리"만 찍힌다.
- 브라우저 화면은 **하얗게** 비어 있다.

이것이 정상이다. 화면이 하얗지 않다면 필터가 동작하지 않은 것이다. "다음으로 가세요"라는 말을 하지 못했으니 요청이 필터에서 멈춰 버린 것이다.

### 실험 3 — chain.doFilter()를 살림

주석을 풀고 다시 실행하면 페이지가 정상으로 열리고, 콘솔에 전처리와 후처리가 **모두** 찍힌다.

```
요청: 필터 전처리
  → (컨트롤러 실행, 페이지 생성)
완료: 필터 후처리
```

마치 **함수 호출**처럼, `chain.doFilter()`에서 다음으로 갔다가 그 일이 끝나면 다시 돌아와서 그 다음 줄을 실행한다.

또 하나 눈여겨볼 점은 콘솔에 이 출력이 **여러 번** 찍힌다는 것이다. 페이지 하나를 요청해도 브라우저는 CSS, 이미지 등을 각각 따로 요청하고, **모든 요청은 개별적으로 필터를 거친다.**

### 필터 체인

필터는 여러 개를 쌓을 수 있다. 이렇게 이어진 필터들을 **필터 체인(Filter Chain)**이라고 한다.

```
요청 ━▶ [필터 A] ━▶ [필터 B] ━▶ [필터 C] ━▶ [서블릿]
응답 ◀━ [필터 A] ◀━ [필터 B] ◀━ [필터 C] ◀━
```

`chain.doFilter()`의 "다음"은 **다음 필터**일 수도 있고, 마지막 필터라면 **서블릿**일 수도 있다. 어느 필터든 `doFilter()`를 부르지 않으면 그 뒤로는 아무도 실행되지 않는다. 보안 필터가 "넌 못 들어가"라고 할 수 있는 원리가 이것이다.

## 3. 스프링 시큐리티 — 보안 필터를 만들어 둔 라이브러리

지금까지는 보안을 위한 필터를 직접 만들어 써 왔다. 이제 그럴 필요가 없다. 그 필터를 만들어 둔 라이브러리가 **Spring Security**다.

### 라이브러리 추가

현재 프로젝트의 라이브러리는 Web, JPA, Lombok, PostgreSQL, DevTools, **Thymeleaf**다.

> Thymeleaf는 서버에서 페이지를 만드는 템플릿 엔진으로, JSP를 대체한다. JSP보다 HTML에 가깝고 직관적이다. 요즘은 화면을 프론트엔드가 따로 만드는 경우가 많아 수업에서 따로 배우지는 않고, 보안 실습에서만 잠깐 본다.

`build.gradle`의 `dependencies`에 보안 스타터와 보안 테스트용 스타터를 추가한다(위치는 크게 상관없다).

```groovy
implementation 'org.springframework.boot:spring-boot-starter-security'
testImplementation 'org.springframework.security:spring-security-test'
```

앞에서 만든 `FirstFilter`는 방해가 되므로 `@Component`를 주석 처리해 둔다.

### 추가만 했는데 모든 페이지가 막힌다

서버를 다시 시작하고 메인 페이지에 가 보면 **로그인 화면**이 나온다. 아무것도 하지 않았는데 "너 누구야?"부터 묻는다.

**스타터(starter)**는 라이브러리만 추가하는 게 아니라 **기본 설정까지 풀세트로** 들어 있다. 그래서 포함하자마자 바로 동작한다. 스프링 시큐리티의 기본 설정은 다음과 같다.

- **일단 다 막는다.** 보안에는 수동적 방식과 능동적 방식이 있는데, 스프링 시큐리티는 능동적이다. 처음엔 모두 막아 두고, 개발자가 "이건 열어 줘", "저건 열어 줘"를 하나씩 설정한다.
- 인증되지 않은 사용자가 허락받지 않은 페이지를 요청하면, 입구(필터)에서 **로그인 페이지로 리디렉트**한다.
- 그 **로그인 페이지도 스프링 시큐리티가 만들어 준 것**이다. 원하면 직접 만든 페이지로 바꿀 수 있다.
- 로그인 처리 로직도 이미 구현되어 있다. 로그인 페이지도, 로그인 로직도 만들 필요가 없다.

> **추가 설명 — 필터 "하나"가 아니라 필터 "묶음"이다**: 스프링 시큐리티를 추가하면 서블릿 필터 체인에 보안용 필터 하나(`DelegatingFilterProxy`)가 끼어들고, 그 안에서 다시 **보안 전용 필터 체인**(`SecurityFilterChain`)이 돈다. 인증 확인, 로그인 처리, 로그아웃, 예외 처리 등을 맡은 필터가 10개 넘게 줄지어 있다. 우리가 2절에서 만든 필터 체인과 같은 구조가 보안 안에 한 번 더 들어 있는 셈이다.

> 화면이 바로 바뀌지 않으면 서버를 중지했다가 다시 실행하거나, 빌드가 꼬였을 수 있으니 Java 클린(Clean Java Language Server Workspace) 후 다시 실행한다.

### 기본 계정으로 로그인

기본 설정에서는 계정이 하나 있다.

- 아이디: `user`
- 비밀번호: 서버가 시작될 때 터미널에 찍히는 값 (`Using generated security password: ...`)

비밀번호는 **실행할 때마다 바뀐다.** 서버를 다시 시작했다면 새로 찍힌 값을 복사해서 쓴다. 이 값을 입력하면 로그인이 된다.

> 터미널에서 `Ctrl+C`를 누르면 복사가 아니라 실행 중인 서버가 멈출 수 있다. 터미널의 복사는 텍스트를 선택한 상태에서 해야 한다.

계정이 `user` 하나뿐이고, 비밀번호를 매번 콘솔에서 복사해야 하는 건 기본값일 뿐이다. 사용자를 추가하고, 어떤 URL을 열고 막을지 **설정**할 수 있다.

## 4. 보안 설정 파일 — SecurityConfig

### 설정 파일은 어디에 두나

| 방식 | 설명 |
|---|---|
| `auth`(authentication) 폴더 | 인증 관련 파일을 모두 여기에 둔다 |
| **`config` 폴더** | 보안을 포함해 여러 설정을 두루 모아 둔다 |

지금은 설정이 많지 않으니 `config` 폴더에 `SecurityConfig.java`를 만든다. 다음 프로젝트에서는 도메인 단위로 묶고 어댑터 계층을 추가하는 방식으로 바꾼다.

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
            .formLogin(Customizer.withDefaults());
        return http.build();
    }

    @Bean
    public UserDetailsService userDetailsService() {
        UserDetails user1 = User.withUsername("newlec")
                .password("{noop}1234")
                .roles("USER")
                .build();

        UserDetails user2 = User.withUsername("admin")
                .password("{noop}1234")
                .roles("ADMIN")
                .build();

        return new InMemoryUserDetailsManager(user1, user2);
    }
}
```

중요한 블록은 두 개다.

| 블록 | 역할 |
|---|---|
| `SecurityFilterChain` | 어떤 URL을 열고 막을지, 로그인 방식 등 **보안 필터 체인 설정** |
| `UserDetailsService` | 스프링 시큐리티에게 **사용자 정보를 제공** |

### @Configuration — @Component로 바꿔도 될까?

IoC에 담을 때 쓰는 어노테이션은 `@Component`, `@Service`, `@Controller`, `@Repository`가 있고, 여기에 `@Configuration`도 있다. 설정 파일에 `@Configuration` 대신 `@Component`를 붙여도 IoC에 잘 담긴다. 설정 파일에는 "이건 설정이다"라고 **의미에 맞게** `@Configuration`을 붙이는 것이 맞다.

> **추가 설명 — 의미만 다른 것은 아니다**: `@Configuration`은 스프링이 이 클래스를 CGLIB **프록시**로 감싼다. 그래서 설정 클래스 안에서 `@Bean` 메서드를 다른 `@Bean` 메서드가 직접 호출해도, 매번 새 객체를 만들지 않고 **IoC에 이미 있는 같은 객체**를 돌려준다. `@Component`로 바꾸면 이 처리가 빠져서, 그런 호출이 있을 경우 객체가 여러 개 생길 수 있다. 위 예제처럼 `@Bean` 메서드끼리 서로 부르지 않는다면 차이가 드러나지 않는다.

## 5. @Bean — 내가 만들지 않은 객체를 IoC에 담기

### 소스 코드가 없는 클래스는 어떻게 담나

`@Component` 같은 어노테이션을 붙이려면 그 클래스의 **소스 코드**가 있어야 한다. 내가 만든 클래스는 소스가 있으니 붙이면 된다. 그런데 **내가 만들지 않은 클래스**(라이브러리 클래스 등)는 소스에 어노테이션을 붙일 수 없다. `new`로 객체를 만들 수는 있는데, IoC에 담을 방법이 없다.

이럴 때 쓰는 것이 **`@Bean`**이다.

```java
@Configuration
public class TestConfig {

    @Bean
    public String[] names() {                   // 함수명이 아니라 "이름"
        return new String[] {"홍길동", "김길동", "이길동"};
    }
}
```

### 메서드 이름 = IoC에 담길 이름

보통 함수 이름은 `remove`, `add`, `print`처럼 **행위(동사)**다. 그런데 `names()`는 누가 봐도 행위가 아니라 **명사**다. 이 메서드 이름은 동작을 뜻하는 게 아니라, 반환한 객체가 **IoC에 담길 때 쓸 이름**이기 때문이다.

IoC에 객체를 담으려면 두 가지가 필요하다.

1. **이름**: 그 객체를 찾을 때 쓸 이름 → 메서드 이름(`names`)
2. **담아 달라는 요청** → `@Bean`

정리하면 "내가 만들지 않았지만 IoC에 담아서 쓰고 싶은 게 있다면, `new`로 만들어 반환하는 메서드에 이름을 정하고 `@Bean`을 붙이면 된다." 이 메서드는 별도 파일일 필요 없이 **IoC에 담기는 클래스 안이면 어디든** 둘 수 있다.

### 어노테이션으로 담을 때의 이름

`@Component` 등으로 담을 때도 이름은 반드시 있다. 지정하지 않으면 **클래스 이름의 앞글자를 소문자로** 바꾼 것이 이름이 된다(`MenuController` → `menuController`).

그래서 다른 패키지에 같은 이름의 클래스가 있으면 이름이 충돌한다. 예전에 `admin` 패키지의 `MenuController`와 루트의 `MenuController`가 충돌했던 것이 이 경우다. 이때는 한쪽에 이름을 직접 지정한다.

```java
@Controller("adminMenuController")      // 이름을 직접 지정해 충돌을 피한다
public class MenuController { ... }
```

### @Bean으로 담은 객체 쓰기

```java
@Controller
public class HomeController {

    private final String[] names;

    public HomeController(String[] names) {     // 생성자로 주입받는다
        this.names = names;
    }
    ...
}
```

> **추가 설명 — 주입은 이름보다 타입이 먼저다**: 강의에서는 "`names`라는 이름으로 가져온다"고 설명했다. 스프링은 주입할 때 **타입**(`String[]`)으로 먼저 찾고, 같은 타입의 빈이 하나뿐이면 이름과 상관없이 그것을 넣는다. 같은 타입의 빈이 **여러 개**일 때 비로소 매개변수 이름이나 `@Qualifier("names")`로 어느 것인지 고른다. 또 `final` 필드는 선언만 해서는 값이 들어가지 않으므로, 위처럼 **생성자**를 만들어 주입받아야 한다(소스 작업 → 생성자 추가로 만들면 편하다).

이제 `SecurityConfig`를 다시 보면, `SecurityFilterChain`과 `UserDetailsService`는 모두 **스프링 시큐리티의 클래스**라 소스가 없다. 그래서 `@Bean`으로 만들어 IoC에 담는 것이다.

## 6. UserDetailsService — 사용자 정보를 서비스하는 녀석

스프링 시큐리티는 사용자 정보를 **`UserDetails`**라고 부른다. 사용자 정보를 제공하는 서비스는 그래서 **`UserDetailsService`**다.

| 우리가 쓰던 말 | 스프링 시큐리티의 말 |
|---|---|
| 사용자 정보 | `UserDetails` |
| 사용자 정보를 제공하는 서비스 | `UserDetailsService` |

스프링 시큐리티는 로그인을 처리할 때 **무조건** 이 `UserDetailsService`에게 사용자를 달라고 한다. 그래서 이 타입의 객체가 IoC에 반드시 있어야 한다. 만드는 방법은 세 가지다.

| 방법 | 사용자 정보가 있는 곳 |
|---|---|
| **인메모리** (`InMemoryUserDetailsManager`) | 코드에서 메모리에 직접 만든 사용자 (이번 예제) |
| **데이터베이스** (`JdbcUserDetailsManager` 등) | DB 테이블 |
| **커스텀** (`UserDetailsService`를 직접 구현) | 내가 원하는 방식 (예: 우리 회원 엔티티) |

이번 예제는 인메모리 방식이다. `User.withUsername(...)...build()`로 사용자를 만들어 `InMemoryUserDetailsManager`에 담아 반환한다. 사용자는 원하는 만큼 계속 추가할 수 있고, 이 관리자가 사용자 목록을 한꺼번에 들고 있다가 스프링 시큐리티에 제공한다.

> **추가 설명 — 비밀번호 앞의 {noop}**: 스프링 시큐리티는 비밀번호를 **암호화된 형태**로 비교하는 것이 기본이다. 비밀번호를 그냥 `"1234"`로 넣으면 로그인할 때 `There is no PasswordEncoder mapped for the id "null"` 오류가 난다. `{noop}`은 "암호화하지 않은(no operation) 비밀번호"라는 표시로, 학습용으로만 쓴다. 실무에서는 `BCryptPasswordEncoder` 같은 인코더로 암호화한 값을 저장한다.

### 확인

서버를 다시 시작한다(VS Code 상단 바의 새로 고침 버튼으로 재가동해도 된다). 이제 터미널에 기본 비밀번호가 **찍히지 않는다.** 기본 계정은 `UserDetailsService`를 직접 등록하지 않았을 때만 만들어지기 때문이다. 설정한 계정(`newlec` / `1234`)으로 로그인되면 성공이다.

## 7. 우리는 아무것도 안 했다 — 로그인 직접 구현해 보기

돌아보면 우리가 한 일은 "이런 사용자가 있고, 비밀번호는 이것이다"라고 **설정한 것뿐**이다. 로그인 페이지도, 로그인 처리 로직도 만들지 않았다. 원래 로그인은 이렇게 흘러간다.

```
1. 사용자에게 아이디·비밀번호 입력 페이지를 준다
2. 사용자가 입력해서 POST로 보낸다
3. 받은 아이디로 DB에서 사용자 정보(UserDetails)를 가져온다
4. 그 안의 비밀번호와 사용자가 보낸 비밀번호를 비교한다
5. 맞으면 통과, 틀리면 거부
```

스프링 시큐리티는 3~5를 `UserDetailsService`를 이용해 대신 해 준 것이다. 이 과정은 어렵지 않다. 게시글 목록에서 **검색어로 데이터를 찾는 것**과 같고, 찾은 뒤 비밀번호를 비교하는 것만 다르다. 이걸 스프링 시큐리티 없이 직접 구현해 본다.

### 준비 — 시큐리티 끄기

라이브러리를 추가하면 설정이 자동으로 들어가므로 충돌하지 않게 끈다.

1. `SecurityConfig` 클래스 상단의 어노테이션(`@Configuration` 등)을 주석 처리한다. 이게 없으면 그 안의 `@Bean`도 읽히지 않는다.
2. `build.gradle`의 시큐리티 라이브러리를 주석 처리한다.
3. 라이브러리가 사라지면 `SecurityConfig`의 import와 코드가 모두 오류가 나므로, 파일 내용 전체를 주석 처리한다.
4. 서버를 껐다가 다시 시작한다(또는 Java 클린 후 실행).

### 로그인 폼이 보내는 것 확인

로그인 페이지(`/login`)의 폼을 보면 다음과 같다.

```html
<form action="/login" method="post">
    <input name="username">
    <input name="password" type="password">
</form>
```

로그인 버튼을 누르면 `username=newlec&password=1234`가 `/login`으로 **POST**된다. POST이므로 주소창(쿼리 스트링)이 아니라 **요청 본문(payload, body)**에 담겨 간다.

> **HTTP와 HTTPS**: 요청 본문에 담긴다고 안전한 것은 아니다. HTTP로 보내면 네트워크를 엿보는(스니핑) 도구로 `password=1234`가 **그대로 보이고**, 마음먹으면 전부 저장할 수도 있다. HTTPS를 쓰면 본문까지 **암호화**되어 전달되므로 그냥 보이지 않는다. 구글이 비용을 들여서라도 HTTPS를 쓰라고 하는 이유다.

### 데이터가 오는 세 가지 모양

| 모양 | 예 | 보내는 쪽 | 스프링에서 받는 법 |
|---|---|---|---|
| **URL 인코딩** (`application/x-www-form-urlencoded`) | `username=newlec&password=1234` | **HTML 폼** (기본값) | `@RequestParam` |
| JSON | `{"username":"newlec","password":"1234"}` | 자바스크립트 (`fetch` 등) | `@RequestBody` |
| XML | `<username>newlec</username>...` | 과거에 많이 쓰던 방식 | `@RequestBody` |

셋 다 키와 값이 들어 있다. 하지만 서버는 **아무 말이 없으면 URL 인코딩 방식으로 해석**한다. 그게 기본이기 때문이다. JSON이나 XML로 보낼 때는 "본문 전체를 이 형식으로 읽어라"라고 알려야 하고, 그것이 `@RequestBody`다.

지금은 **순수 HTML 폼**으로 보내므로 URL 인코딩으로 온다. 그래서 `@RequestBody`가 아니라 키 이름으로 하나씩 받는다.

> **추가 설명 — HTML 폼이 보낼 수 있는 방식**: 강의에서는 "순수 HTML은 URL 인코딩밖에 못 보낸다"고 했는데, 폼에 `enctype="multipart/form-data"`를 지정하면 **파일 업로드용** 형식으로도 보낼 수 있다. 다만 JSON은 HTML 폼만으로는 보낼 수 없고 자바스크립트가 필요하다는 점은 맞다.

### 컨트롤러 — POST /login

로그인 페이지를 주는 `GET /login`은 이미 있다. 같은 주소로 **POST**를 처리하는 메서드를 하나 더 만든다.

```java
@Controller
public class AuthController {

    private final AuthenticationService authenticationService;

    public AuthController(AuthenticationService authenticationService) {
        this.authenticationService = authenticationService;
    }

    @GetMapping("/login")
    public String loginForm() {
        return "login";
    }

    @PostMapping("/login")
    public String login(@RequestParam("username") String username,
                        @RequestParam("password") String password) {
        boolean ok = authenticationService.authenticate(username, password);
        // 성공·실패에 따라 사용자와 상호작용하는 부분은 다음 시간에
        ...
    }
}
```

- 폼의 `name`과 매개변수 이름이 같으면 `@RequestParam`의 괄호는 생략할 수 있다. 이름을 다르게 쓰고 싶으면 괄호 안에 폼의 키를 적어 연결한다.
- 생성자는 직접 치기보다 **소스 작업(Source Action) → 생성자 생성**으로 만드는 것이 편하고 정확하다. 주입받는 필드는 `final`로 두는 것이 안전하다.

### 서비스 — 인증을 담당하는 AuthenticationService

사용자가 `/login`으로 POST했다는 것은 "**인증해 줘**"라고 요청한 것이다. 그래서 인증을 처리하는 서비스가 필요하다. 스프링 시큐리티에서는 이 역할을 `AuthenticationProvider`라고 부르지만, 여기서는 `AuthenticationService`라고 이름 짓는다(원래는 인터페이스를 먼저 만들어야 하지만 지금은 클래스로 바로 만든다).

```java
@Service
public class AuthenticationService {

    public boolean authenticate(String username, String password) {
        boolean result = false;     // 기본은 실패
        // 아이디로 사용자를 찾고, 비밀번호를 비교해 맞으면 true
        return result;
    }
}
```

메서드 이름은 이 서비스에게 시킬 일, 즉 "아이디와 비밀번호를 줄 테니 **인증해 봐**"이므로 `authenticate`다. 반환값은 성공했는지만 알려 주면 되므로 `boolean`이다. 컨트롤러는 이 결과를 받아 사용자에게 전달하는 **홀 서빙**만 한다.

여기까지가 이번 시간의 진도다. 실제 비교 로직과 성공·실패 처리는 다음 시간에 이어서 구현한다.

## 8. 한 줄 정리

- **필터**는 모든 요청이 서블릿에 가기 전과 응답이 나가기 전에 반드시 거치는 **입출구**다. 보안, 인코딩, 압축, 로그 등 목적별로 여러 개를 쌓을 수 있다(**필터 체인**).
- 스프링 부트에서는 필터에 **`@Component`**만 붙이면 등록된다. **`chain.doFilter()`**를 부르지 않으면 요청이 그 자리에서 멈춘다.
- **Spring Security**는 보안 필터를 만들어 둔 라이브러리다. 스타터를 추가하는 순간 **모든 요청을 막고**, 로그인 페이지와 로그인 로직까지 제공한다.
- **`@Bean`**은 소스가 없어 어노테이션을 붙일 수 없는 클래스의 객체를 IoC에 담는 방법이다. **메서드 이름이 빈의 이름**이 된다.
- 스프링 시큐리티는 사용자 정보를 **`UserDetails`**, 그걸 제공하는 서비스를 **`UserDetailsService`**라고 부른다. 인메모리·DB·커스텀 세 가지로 만들 수 있다.
- HTML 폼은 **URL 인코딩**으로 보내므로 `@RequestParam`으로 받고, JSON은 `@RequestBody`로 받는다.
