---
tags: [스프링부트, 설정, YAML, Gradle, Kotlin]
---

> 🔗 관련 노트: [[080_Spring Data JPA 리포지토리와 엔티티 매핑 — 쿼리 메서드, 연관관계, 복합키]]

# 스프링 부트 설정 파일 — application.yml과 Gradle Kotlin DSL

프로젝트의 애플리케이션 설정 파일을 `application.properties`에서 `application.yml`로, 빌드 설정 파일을 `build.gradle`에서 `build.gradle.kts`로 바꾼 이유와 차이를 정리한다. 엔티티마다 `@Column`을 붙이지 않고 설정으로 이름 규칙을 맞추는 방법도 함께 본다.

## 1. application.properties → application.yml

두 파일은 **같은 설정을 다른 표기법으로** 쓴 것이다. 스프링 부트는 둘 다 읽는다.

```properties
# application.properties — 매번 앞부분을 다 써야 한다
spring.application.name=backend
spring.datasource.url=jdbc:postgresql://localhost:5432/newcafe
spring.datasource.username=newcafe
spring.datasource.password=1234
```

```yaml
# application.yml — 들여쓰기가 앞부분을 대신한다
spring:
  application:
    name: backend
  datasource:
    url: jdbc:postgresql://localhost:5432/newcafe
    username: newcafe
    password: 1234
```

`properties`는 `spring.datasource.url`, `spring.datasource.username`처럼 **공통 앞부분을 줄마다 반복**해야 한다. `yml`은 들여쓰기 자체가 "앞의 이름에 이어진다"는 뜻이라 반복을 생략할 수 있고, 설정이 계층 구조로 보여 읽기 쉽다.

> **YAML 주의점**
> - 들여쓰기에는 **탭이 아니라 공백(스페이스)**만 쓸 수 있다. 탭을 쓰면 파싱 에러가 난다. 공백 개수(보통 2칸)도 같은 계층끼리 맞아야 한다.
> - `키: 값`에서 콜론 뒤에 **공백 한 칸**이 반드시 있어야 한다.
> - 한 프로젝트에 두 파일이 다 있으면 둘 다 읽히고, 같은 키는 `properties` 쪽이 우선한다. 헷갈리지 않게 하나만 두는 것이 좋다.

## 2. build.gradle → build.gradle.kts

Gradle 빌드 설정은 두 가지 언어로 쓸 수 있다.

| 파일 | 언어 | 특징 |
|---|---|---|
| `build.gradle` | **Groovy** DSL | 예전부터 쓰던 방식. 문법이 느슨하다. |
| `build.gradle.kts` | **Kotlin** DSL (`kts` = Kotlin Script) | 코틀린 문법이라 타입 검사가 된다. |

DSL(Domain Specific Language)은 특정 목적(여기서는 빌드 설정)을 위해 만든 작은 언어라는 뜻이다.

```groovy
// build.gradle (Groovy)
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    runtimeOnly 'org.postgresql:postgresql'
}
```

```kotlin
// build.gradle.kts (Kotlin)
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    runtimeOnly("org.postgresql:postgresql")
}
```

**Kotlin DSL의 장점**: 코틀린 문법 체계라서 설정 파일도 **구문·타입 검사**를 받는다. 설정에 오타나 잘못된 값이 있으면 빌드가 시작되기 전에 에러로 잡히고, 에디터의 자동 완성도 정확하게 동작한다. Groovy는 문법이 느슨해서 잘못 쓴 설정이 그대로 통과했다가 나중에 문제가 되는 경우가 있다.

AI에게 "이 Gradle 설정을 Kotlin DSL로 바꿔줘"라고 하면 대부분 그대로 변환해준다. 바꾼 뒤에는 빌드가 정상인지 꼭 확인한다.

### 코틀린 이야기 — 안드로이드와 스프링

코틀린은 JetBrains가 만든 언어로, 자바처럼 JVM(자바 플랫폼) 위에서 동작한다.

- **안드로이드**: 원래 자바 언어로 개발하는 플랫폼이었다. 2010년 오라클이 자바 API 저작권 문제로 구글에 소송을 걸었고(청구액 약 88억 달러), 구글은 2017년 코틀린을 공식 지원 언어로 추가한 뒤 2019년 "코틀린 우선(Kotlin-first)"을 선언했다. 지금도 런타임은 JVM 계열 플랫폼이지만, 새 안드로이드 앱은 대부분 코틀린으로 쓴다.
- **스프링**: 스프링도 코틀린으로 개발할 수 있다. 한때 "자바가 밀려나는 것 아니냐"는 이야기가 있었지만, 스프링 개발은 여전히 자바가 주류다.

> **강의 내용 바로잡기**
> - 소송은 2021년 미국 대법원에서 **구글의 승소**(공정 이용 인정)로 끝났다. 또 구글이 코틀린을 택한 것은 소송만이 아니라, 코틀린의 간결한 문법과 null 안전성 같은 언어 자체의 장점도 큰 이유였다. "소송 때문에 자바를 버렸다"는 건 단순화된 이야기다.
> - "스프링이 코틀린을 버렸다"는 것도 사실이 아니다. 스프링은 지금도 코틀린을 공식 지원하고, 최근 버전에서는 JetBrains와 협력해 코틀린 지원을 오히려 강화하고 있다. 다만 스프링 사용자의 대다수가 자바를 쓰는 것은 맞다.

## 3. @Column 대신 설정으로 이름 규칙 맞추기

자바 필드는 카멜 표기(`korName`), DB 컬럼은 스네이크 표기(`kor_name`)를 쓰기 때문에, 표기법 차이로 엔티티 필드와 컬럼이 연결되지 않아 오류가 나는 경우가 있다. 그래서 필드마다 `@Column(name = "kor_name")`을 붙였는데, 엔티티가 많아지면 쓰는 손가락이 아프다.

**"왜 내 손가락을 써?"** — 반복 작업을 귀찮아하는 마인드는 좋은 것이다. 필드마다 붙이는 대신 JPA 설정에서 **이름 변환 규칙(네이밍 전략)**을 한 번 지정하면 된다.

```yaml
spring:
  jpa:
    hibernate:
      naming:
        physical-strategy: org.hibernate.boot.model.naming.CamelCaseToUnderscoresNamingStrategy
```

이렇게 하면 `korName` → `kor_name`, `MenuImage` → `menu_image`처럼 카멜 표기를 자동으로 스네이크 표기로 바꿔서 SQL을 만든다.

> 사실 Spring Boot는 이 `CamelCaseToUnderscoresNamingStrategy`를 **기본값**으로 쓴다. 그래서 설정을 따로 하지 않아도 대부분 자동 변환된다. 그런데도 변환이 안 됐다면 다른 설정(예: `PhysicalNamingStrategyStandardImpl`, 이름을 그대로 쓰는 전략)이 들어가 있거나 Hibernate만 단독으로 쓰는 환경일 가능성이 크다. 이럴 때 위 설정을 명시하면 된다. 그리고 컬럼 이름이 규칙과 아예 다르거나 `nullable`, `length` 같은 제약을 줄 때는 여전히 `@Column`을 쓴다.

## 4. 설정을 외우지 못하면 실력이 없는 걸까

예전에는 이런 설정을 매번 잊어버려서, 구글에서 검색해 붙여넣거나 따로 적어두고 썼다. 그렇다면 설정 키를 외우지 못하는 것이 실력 부족일까?

**아니다.** API가 제공하는 메서드나 설정 속성값을 암기하고 있는 것은 실력이 아니다. 실력은 그것들을 **엮어내는 능력**이다. API를 전부 외우는 것은 사실상 불가능하고, 옛날에도 포스트잇에 적어두고 썼다.

대신 중요한 것은 **"이런 설정이 있고, 이런 기능이 있다"는 사실을 머릿속에 갖고 있는 것**이다. 그래야 AI에게 "이런 기능이 있었는데 뭐였지?"라고 물어보거나, "그거 이용해서 이건 이렇게, 저건 저렇게 하자"라고 방향을 잡아줄 수 있다. AI는 코드를 작성하는 능력은 있지만, **우리가 무엇을 원하는지, 어떤 방식을 원하는지는 알 수 없다.** 문장 하나를 던지면 실타래를 끌어내듯 이어서 써줄 뿐이라서, 방향은 반드시 사람이 잡아줘야 한다.
