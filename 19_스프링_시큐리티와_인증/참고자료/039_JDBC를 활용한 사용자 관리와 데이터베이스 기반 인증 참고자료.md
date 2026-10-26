---
tags: [스프링시큐리티, JdbcUserDetailsManager, UserDetailsService, DataSource, PostgreSQL, BCrypt, 인증, ROLE_, 참고자료]
---

> 🔗 관련 노트: [[098_스프링 시큐리티 인가 설정 — URL별 허용 규칙, 역할, 커스텀 로그인 페이지]] · [[093_서블릿 필터와 스프링 시큐리티 입문 — 필터 체인, @Bean, UserDetailsService]]

# JDBC를 활용한 사용자 관리와 데이터베이스 기반 인증

지난 노트에서는 메모리에 임시로 사용자 정보를 생성하는 `InMemoryUserDetailsManager`를 이용해 스프링 시큐리티의 기본 인가 설정을 알아보았다. 하지만 실제 서비스에서는 서버를 재시작해도 사용자 정보가 유지되어야 하므로 데이터베이스에 회원 데이터를 저장하고 조회해야 한다.

이번 노트에서는 `JdbcUserDetailsManager`를 사용해 데이터베이스의 사용자 테이블과 스프링 시큐리티를 연결하고, 데이터베이스 기반의 인증을 구현하는 방법을 다루어보자.

> 🎓 **쌤의 코멘트**
>
> 이 노트는 읽기만 하세요. 절대로 작성하거나 주의 깊게 볼 필요 없습니다. 이 방법을 사용하는 경우는 없으니까, 그냥 이런 옵션도 있구나~ 생각하면서 읽으시면 됩니다.
>
> 만약에 시간이 없다~? 그럼 … 이것만 기억하세요.
>
> **아~ 인증을 제공하는 서비스가 SQL을 이용해서 제공하는 방법도 있구나~**

> **추가 설명 — 실무에서 쓰는 방식은 따로 있다**: 실제 프로젝트에서는 대부분 JPA로 회원 엔티티와 Repository를 만들고, `UserDetailsService`를 직접 구현해 그 Repository를 호출한다. 이 노트의 방식은 "스프링 시큐리티가 결국 **아이디로 사용자를 찾아 주는 `UserDetailsService`만 있으면 된다**"는 구조를 보여 주는 중간 단계로 읽으면 된다.
>
> | 방식 | 사용자 조회 방법 | 쓰는 곳 |
> |---|---|---|
> | `InMemoryUserDetailsManager` | 코드에 적은 사용자를 메모리에서 찾음 | 학습, 테스트 |
> | `JdbcUserDetailsManager` (이 노트) | 지정한 SQL로 DB에서 찾음 | 거의 안 씀 |
> | 직접 구현한 `UserDetailsService` + JPA | Repository로 엔티티를 찾아 `UserDetails`로 변환 | **실무 표준** |

## 1. 메모리 저장소의 한계와 JDBC 기반 인증

`InMemoryUserDetailsManager`는 코드로 직접 사용자 정보를 작성해 메모리에 올려두는 방식이다. 테스트나 학습용으로는 편리하지만, 서버가 꺼지면 회원 정보가 사라지거나 회원가입 기능을 만들 수 없는 치명적인 한계가 있다.

스프링 시큐리티는 데이터베이스와 연동하여 사용자를 조회할 수 있도록 `JdbcUserDetailsManager`를 제공한다. 데이터베이스 연결 도구인 `DataSource`를 주입받고, 테이블 구조에 맞게 회원 정보 조회 쿼리와 권한 조회 쿼리를 지정해주면 로그인 시 데이터베이스에서 사용자를 검색해 인증을 처리한다.

스프링 시큐리티의 `JdbcUserDetailsManager`를 사용할 때에는 JPA Entity 대신 SQL DDL 문과 직접적인 쿼리 매핑을 사용한다.

JPA Entity(JPA/Hibernate) 기반으로 처리하려면 `JdbcUserDetailsManager`가 아닌 `UserDetailsService` 인터페이스를 직접 구현하여 Spring Data JPA의 Repository를 호출하는 커스텀 `UserDetailsService`를 작성해야 한다.

따라서 `JdbcUserDetailsManager`를 다루는 본 단원에서는 데이터베이스 테이블 및 SQL 쿼리를 직접 활용하는 구조를 그대로 유지한다.

일단 이전 수업에서 다루었던 다음 내용은 주석처리하거나 지우도록 하자.

```java
// @Bean
// public UserDetailsService userDetailsService(PasswordEncoder passwordEncoder) {
//     UserDetails user = User.builder().username("user")
//             .password(passwordEncoder.encode("user")).roles("USER").build();
//     UserDetails admin = User.builder().username("admin")
//             .password(passwordEncoder.encode("admin")).roles("USER", "ADMIN").build();
//     return new InMemoryUserDetailsManager(user, admin);
// }
```

> **추가 설명 — 왜 지워야 하나**: `UserDetailsService` 타입의 빈이 두 개(메모리용, JDBC용) 있으면 스프링 시큐리티가 어느 쪽으로 로그인을 처리할지 정하지 못한다. 그래서 기존 메모리용 빈을 없애고 JDBC용 하나만 남긴다. `PasswordEncoder` 빈은 DB에 저장된 BCrypt 비밀번호를 비교할 때 그대로 쓰이므로 **지우지 않는다.**

> **추가 설명 — DB 연결 준비**: `DataSource`는 스프링 부트가 `application.yml`의 `spring.datasource.*` 값과 의존성을 보고 자동으로 만들어 주는 빈이다. `build.gradle`에 아래 두 가지가 있어야 주입받을 수 있다.
>
> ```groovy
> implementation 'org.springframework.boot:spring-boot-starter-jdbc'   // 또는 data-jpa (jdbc 포함)
> runtimeOnly 'org.postgresql:postgresql'
> ```

## 2. 데이터베이스 테이블 구조 설계

스프링 시큐리티 인증을 데이터베이스와 연동하려면 회원 정보와 권한 정보를 담을 테이블이 필요하다. 일반적으로 사용자와 권한을 N:M 관계(다대다 관계)로 처리하기 위해 매핑 테이블을 둔다.

제시된 DDL 문은 MySQL/MariaDB 문법에 가깝다. PostgreSQL을 사용하려면 데이터 타입과 제약 조건 문법을 PostgreSQL 전용으로 변경해야 한다.

PostgreSQL에서는 `AUTO_INCREMENT` 대신 `BIGSERIAL`이나 `GENERATED ALWAYS AS IDENTITY`를 사용하며, `TINYINT(1)` 대신 `BOOLEAN` 또는 `SMALLINT` 타입을 사용하는 것이 권장된다.

> **추가 설명 — 두 문법 비교**: 원문에는 MySQL 버전 DDL이 빠져 있어서, 차이가 나는 부분만 표로 정리한다.
>
> | 항목 | MySQL/MariaDB | PostgreSQL |
> |---|---|---|
> | 자동 증가 키 | `id BIGINT AUTO_INCREMENT PRIMARY KEY` | `id BIGSERIAL PRIMARY KEY` 또는 `id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY` |
> | 참/거짓 | `TINYINT(1)` (0/1로 저장) | `BOOLEAN` (`TRUE`/`FALSE`) |
> | 테이블 옵션 | `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4` | 없음 |

PostgreSQL 기준 DDL 문은 다음과 같다.

여기서는 사용자 정보를 담는 `users`, 권한 종류를 정의하는 `roles`, 사용자가 어떤 권한을 가지는지 연결하는 `user_roles` 테이블을 사용한다.

```sql
-- 사용자 정보 테이블
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE
);

-- 권한 종류 테이블
CREATE TABLE roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- 사용자-권한 매핑 테이블
CREATE TABLE user_roles (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);
```

```
users                       user_roles                  roles
┌────┬──────────┬───┐       ┌─────────┬─────────┐       ┌────┬────────────┐
│ id │ username │...│ 1───N │ user_id │ role_id │ N───1 │ id │ name       │
├────┼──────────┼───┤       ├─────────┼─────────┤       ├────┼────────────┤
│ 1  │ user     │   │       │ 1       │ 1       │       │ 1  │ ROLE_USER  │
│ 2  │ admin    │   │       │ 2       │ 1       │       │ 2  │ ROLE_ADMIN │
└────┴──────────┴───┘       │ 2       │ 2       │       └────┴────────────┘
                            └─────────┴─────────┘
```

스프링 시큐리티가 사용자를 정상적으로 인증하려면 아이디(`username`), 암호화된 비밀번호(`password`), 계정 활성화 여부(`enabled`) 정보가 필수적이다.

> **추가 설명 — `password` 길이를 넉넉히 잡는 이유**: BCrypt 결과는 `$2a$10$...` 형태의 **60자** 문자열이다. `{bcrypt}` 같은 접두사가 붙거나 나중에 다른 알고리즘으로 바꿀 수도 있으므로 `VARCHAR(255)`처럼 여유 있게 둔다.

> **추가 설명 — 스프링 시큐리티의 기본 테이블 구조**: 쿼리를 따로 지정하지 않으면 `JdbcUserDetailsManager`는 아래 두 테이블을 찾는다. 이 구조를 그대로 쓰면 3절의 커스텀 쿼리가 필요 없지만, 아이디를 기본 키로 쓰는 단순한 구조라 실제 회원 테이블과는 잘 맞지 않는다. 그래서 이 노트처럼 내 테이블에 맞는 쿼리를 지정하는 경우가 많다.
>
> ```sql
> CREATE TABLE users (
>     username VARCHAR(50) NOT NULL PRIMARY KEY,
>     password VARCHAR(500) NOT NULL,
>     enabled BOOLEAN NOT NULL
> );
> CREATE TABLE authorities (
>     username VARCHAR(50) NOT NULL REFERENCES users(username),
>     authority VARCHAR(50) NOT NULL
> );
> ```

### 샘플 데이터 삽입 예시

테이블 생성이 완료되면 아래와 같이 기본 권한과 사용자 데이터, 그리고 매핑 데이터를 추가하여 인증 테스트를 진행할 수 있다. 비밀번호는 BCrypt 알고리즘으로 암호화된 문자열을 저장해야 한다.

```sql
-- 권한 샘플 데이터 삽입
INSERT INTO roles (id, name) VALUES (1, 'ROLE_USER');
INSERT INTO roles (id, name) VALUES (2, 'ROLE_ADMIN');

-- 사용자 샘플 데이터 삽입 (비밀번호: password123)
INSERT INTO users (id, username, password, enabled)
VALUES (1, 'user', '$2a$10$8.UnVuG9HHgffUDAlk8qfOUvgkqRzgVym5luV621m13sge2W13S2m', 1);

INSERT INTO users (id, username, password, enabled)
VALUES (2, 'admin', '$2a$10$8.UnVuG9HHgffUDAlk8qfOUvgkqRzgVym5luV621m13sge2W13S2m', 1);

-- 사용자-권한 매핑 데이터 삽입
INSERT INTO user_roles (user_id, role_id) VALUES (1, 1); -- user에게 ROLE_USER 부여
INSERT INTO user_roles (user_id, role_id) VALUES (2, 1); -- admin에게 ROLE_USER 부여
INSERT INTO user_roles (user_id, role_id) VALUES (2, 2); -- admin에게 ROLE_ADMIN 부여
```

> 원문 바로잡기 — `enabled`를 `BOOLEAN`으로 만들었는데 값에 숫자 `1`을 넣으면 PostgreSQL에서는 `column "enabled" is of type boolean but expression is of type integer` 오류가 난다. MySQL처럼 0/1이 자동으로 바뀌지 않는다. `TRUE`를 쓰거나, 기본값이 `TRUE`이므로 `enabled` 컬럼을 빼고 넣는다.
>
> ```sql
> INSERT INTO users (id, username, password, enabled)
> VALUES (1, 'user', '$2a$10$...', TRUE);
> ```

> **추가 설명 — `id`를 직접 넣으면 시퀀스가 따라오지 않는다**: `BIGSERIAL`은 내부의 **시퀀스**가 다음 번호를 정한다. 위처럼 `id`를 1, 2로 직접 넣으면 시퀀스는 여전히 1에서 출발하므로, 나중에 회원가입으로 `id` 없이 넣을 때 `duplicate key value violates unique constraint "users_pkey"` 오류가 난다. 샘플 데이터를 넣은 뒤 시퀀스를 맞춰 두거나, 처음부터 `id`를 빼고 넣는다.
>
> ```sql
> SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
> SELECT setval('roles_id_seq', (SELECT MAX(id) FROM roles));
> ```

> **추가 설명 — 해시 값은 직접 만들어 쓴다**: 자료에 적힌 해시가 정말 `password123`인지는 눈으로 확인할 수 없다. 로그인이 계속 실패한다면 해시가 맞지 않을 가능성이 크므로, 같은 `BCryptPasswordEncoder`로 직접 만들어 넣는 것이 확실하다. BCrypt는 같은 비밀번호라도 매번 다른 해시가 나오지만(솔트가 섞이므로) 어느 것이든 `matches()`로 검증된다.
>
> ```java
> System.out.println(new BCryptPasswordEncoder().encode("password123"));
> // $2a$10$xxxxxxxx...  ← 이 값을 INSERT에 넣는다
> ```

> **추가 설명 — 테이블과 샘플 데이터를 자동으로 넣으려면**: `src/main/resources`에 `schema.sql`(CREATE문)과 `data.sql`(INSERT문)을 두고 아래 설정을 켜면 앱이 시작할 때 실행된다. H2 같은 내장 DB는 기본으로 실행되지만 PostgreSQL은 `always`로 켜야 한다. 재시작할 때마다 다시 실행되므로 `CREATE TABLE IF NOT EXISTS`, `INSERT ... ON CONFLICT DO NOTHING`처럼 중복에 안전하게 써 둔다.
>
> ```yaml
> spring:
>   sql:
>     init:
>       mode: always
> ```

## 3. JdbcUserDetailsManager와 커스텀 SQL 설정

스프링 시큐리티의 기본 테이블 구조와 우리가 작성한 테이블 구조가 다를 수 있다. 이때 `JdbcUserDetailsManager`에 커스텀 쿼리를 직접 작성해 알려주면 원하는 테이블 구조로 손쉽게 인증을 진행할 수 있다.

- **`usersByUsernameQuery`**: 입력받은 아이디로 사용자의 아이디, 비밀번호, 활성화 여부를 조회한다.
- **`authoritiesByUsernameQuery`**: 입력받은 아이디로 해당 사용자가 가진 모든 권한 이름을 조회한다.

**SecurityConfig.java (JDBC 사용자 서비스 설정)**

```java
package com.example.security.config;

import javax.sql.DataSource;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.provisioning.JdbcUserDetailsManager;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public UserDetailsService userDetailsService(DataSource dataSource) {
        JdbcUserDetailsManager manager = new JdbcUserDetailsManager(dataSource);

        // 1. 사용자 정보를 조회하는 SQL 쿼리 설정
        manager.setUsersByUsernameQuery(
            "SELECT username, password, enabled " +
            "FROM users " +
            "WHERE username = ?"
        );

        // 2. 사용자의 권한 목록을 조회하는 SQL 쿼리 설정
        manager.setAuthoritiesByUsernameQuery(
            "SELECT u.username, r.name AS authority " +
            "FROM users u " +
            "JOIN user_roles ur ON u.id = ur.user_id " +
            "JOIN roles r ON r.id = ur.role_id " +
            "WHERE u.username = ?"
        );

        return manager;
    }
}
```

> **추가 설명 — 문자열 끝의 공백**: 쿼리를 `+`로 이어 붙일 때 각 줄 끝에 공백(`"... enabled "`)이 없으면 `enabledFROM users`처럼 붙어서 SQL 문법 오류가 난다. 자바 15 이상이면 텍스트 블록(`"""`)으로 쓰는 편이 안전하다.
>
> ```java
> manager.setUsersByUsernameQuery("""
>         SELECT username, password, enabled
>         FROM users
>         WHERE username = ?
>         """);
> ```

> **추가 설명 — 로그인만 할 거라면 `JdbcDaoImpl`로도 충분하다**: `JdbcUserDetailsManager`는 `JdbcDaoImpl`(조회 전용)을 상속해서 `createUser`, `updateUser`, `deleteUser`, `changePassword` 같은 **관리 기능**을 더한 클래스다. 그런데 이 관리 기능들은 2절의 **기본 테이블 구조**(`users`, `authorities`)를 기준으로 SQL이 짜여 있다. 이 노트처럼 테이블을 직접 설계했다면 `createUser`를 쓰려고 해도 `setCreateUserSql`, `setCreateAuthoritySql` 등을 모두 다시 지정해야 한다. 결국 지정한 두 쿼리로 **조회(로그인)만** 하게 된다.

## 4. 데이터베이스 연동 동작 순서

로그인 요청이 들어오면 스프링 시큐리티 내부에서는 데이터베이스를 조회해 인증을 진행한다.

1. 사용자가 로그인 화면에서 아이디와 비밀번호를 입력하고 제출한다.
2. 스프링 시큐리티가 `UserDetailsService`로 등록된 `JdbcUserDetailsManager`를 호출한다.
3. `setUsersByUsernameQuery`로 등록한 SQL이 실행되어 데이터베이스에 해당 아이디를 가진 사용자가 있는지 확인하고, 암호화된 비밀번호와 활성화 상태를 가져온다.
4. `setAuthoritiesByUsernameQuery`로 등록한 SQL이 실행되어 해당 사용자가 가진 권한 목록(예: `ROLE_USER`, `ROLE_ADMIN`)을 조인 쿼리로 가져온다.
5. 비밀번호 검증기(`PasswordEncoder`)가 사용자가 입력한 비밀번호와 DB에서 가져온 암호화된 비밀번호를 비교한다.
6. 검증에 성공하면 사용자 정보와 권한 목록을 담은 인증 객체를 세션에 저장한다.

```
POST /login (username=admin, password=...)
   │
   ▼
UsernamePasswordAuthenticationFilter
   │
   ▼
DaoAuthenticationProvider ──loadUserByUsername("admin")──▶ JdbcUserDetailsManager
   │                                                         ├─ ③ users 조회 SQL
   │                                                         └─ ④ 권한 조회 SQL
   │◀───────────── UserDetails(admin, $2a$10$..., enabled, [ROLE_USER, ROLE_ADMIN])
   │
   ├─ ⑤ passwordEncoder.matches(입력값, DB 해시)
   │      └ 계정 상태(enabled 등) 확인
   ▼
⑥ 인증 객체 → SecurityContext → 세션(JSESSIONID)
```

> **추가 설명 — 실패하는 경우별 결과**: 아래 경우는 모두 로그인 실패로 처리되어 기본 설정에서는 `/login?error`로 돌아간다.
>
> | 상황 | 어디서 걸리나 |
> |---|---|
> | 아이디가 DB에 없다 | ③ 조회 결과가 0행 → `UsernameNotFoundException` |
> | 사용자는 있는데 권한이 하나도 없다 | ④ 조회 결과가 0행 → "권한이 없는 사용자"로 보고 **사용자를 못 찾은 것과 똑같이** 실패 |
> | 비밀번호가 틀렸다 | ⑤ `matches()`가 `false` → `BadCredentialsException` |
> | `enabled`가 `FALSE`다 | 계정 상태 확인 → `DisabledException` |
>
> 두 번째 경우가 놓치기 쉽다. 회원가입을 만들 때 `users`에만 넣고 `user_roles`에 `ROLE_USER`를 같이 넣지 않으면, 비밀번호가 맞아도 로그인이 되지 않는다.

## 5. 주의할 사항: 권한 이름 형식과 컬럼 이름

`JdbcUserDetailsManager`에 커스텀 SQL을 적용할 때 자칫 놓치기 쉬운 두 가지 점이 있다.

### 1) 권한 조회 쿼리의 별칭(Alias) 지정

스프링 시큐리티 내부에서는 권한 조회 쿼리의 결과 컬럼 이름으로 `username`과 `authority`를 기본적으로 요구한다. 따라서 조인 쿼리를 작성할 때 권한명이 들어가는 컬럼에는 반드시 `AS authority`와 같이 별칭을 붙여주어야 에러 없이 권한을 가져온다.

> 원문 바로잡기 — 스프링 시큐리티(`JdbcDaoImpl`)는 조회 결과를 컬럼 **이름이 아니라 순서(번호)**로 읽는다. 그래서 `AS authority`가 없어도 동작하고, 반대로 별칭을 붙여도 **순서가 틀리면** 엉뚱한 값을 읽는다. 지켜야 하는 것은 이름이 아니라 아래 **컬럼 순서**다. `AS authority`는 기본 쿼리와 모양을 맞춰 읽기 쉽게 하는 습관으로 보면 된다.
>
> | 쿼리 | 1번째 컬럼 | 2번째 컬럼 | 3번째 컬럼 |
> |---|---|---|---|
> | `usersByUsernameQuery` | 아이디 | 비밀번호 | 활성화 여부(boolean) |
> | `authoritiesByUsernameQuery` | 아이디 | **권한 이름** | — |
>
> 예를 들어 권한 쿼리를 `SELECT r.name AS authority, u.username ...`처럼 순서를 바꾸면, 별칭은 맞아도 2번째 컬럼인 `username`("admin")이 권한으로 들어가 `hasRole("ADMIN")`이 통과하지 못한다.

### 2) ROLE_ 접두사 규칙

스프링 시큐리티의 `hasRole("ADMIN")` 인가 메서드를 사용할 경우 데이터베이스 `roles` 테이블의 `name` 컬럼에 `ROLE_ADMIN` 형태로 저장되어 있거나, 조회 시 `ROLE_` 접두사가 붙어있어야 한다. DB에 `ADMIN` 형태로 저장해 두었다면 `hasAuthority("ADMIN")`를 사용하거나 SQL 조회 시 `CONCAT('ROLE_', r.name)`과 같이 접두사를 붙여 가공해야 한다.

> **추가 설명 — 접두사를 붙이는 세 가지 방법**: DB에 `ADMIN`, `USER`처럼 접두사 없이 저장했을 때 쓸 수 있는 방법이다.
>
> | 방법 | 코드 |
> |---|---|
> | SQL에서 붙이기 | `SELECT u.username, CONCAT('ROLE_', r.name) ...` (PostgreSQL은 `'ROLE_' \|\| r.name`도 된다) |
> | 매니저 설정으로 붙이기 | `manager.setRolePrefix("ROLE_");` — 조회한 권한 이름 앞에 자동으로 붙인다 |
> | 인가 규칙을 바꾸기 | `hasRole("ADMIN")` 대신 `hasAuthority("ADMIN")` |
>
> 정리하면 `hasRole("ADMIN")`은 내부적으로 `hasAuthority("ROLE_ADMIN")`과 같다. 결국 **사용자가 가진 권한 문자열**과 **규칙이 요구하는 문자열**이 정확히 같아야 통과한다.

## 6. 마무리

`JdbcUserDetailsManager`를 사용하면 기존 사용자 테이블 구조를 유지하면서도 커스텀 SQL 쿼리를 통해 스프링 시큐리티 인증을 손쉽게 연결할 수 있다.

메모리 방식에서 벗어나 데이터베이스 기반으로 전환됨에 따라 회원가입, 정보 수정, 권한 변경 등의 실제 서비스 로직을 완성할 수 있는 기반이 마련된다.

> **추가 설명 — 다음 단계: JPA로 직접 구현하기**: 앞의 쌤 코멘트처럼 실무에서는 `UserDetailsService`를 직접 구현한다. 구조만 미리 보면 다음과 같다. `JdbcUserDetailsManager`가 SQL 두 개로 하던 일을, Repository 조회 한 번과 `UserDetails` 변환으로 대신한다.
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
>         Member member = memberRepository.findByUsername(username)
>                 .orElseThrow(() -> new UsernameNotFoundException(username));
>
>         return User.builder()
>                 .username(member.getUsername())
>                 .password(member.getPassword())          // DB의 BCrypt 해시
>                 .roles(member.getRoleNames())            // "USER", "ADMIN" → ROLE_ 자동 부착
>                 .disabled(!member.isEnabled())
>                 .build();
>     }
> }
> ```
>
> 이 클래스가 `@Service`로 빈 등록되면 스프링 시큐리티가 자동으로 이것을 `UserDetailsService`로 사용하므로, `SecurityConfig`의 `userDetailsService` 빈은 지운다.
