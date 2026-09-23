---
tags: [스프링부트, Java, DI, IoC]
---

> 🔗 관련 노트: [[065_스프링의 정체성 — DI 컨테이너, IoC, 인터페이스와 병렬 개발]] · [[068_스프링 프레임워크 개요와 3계층 아키텍처 — Controller·Service·Repository, Entity와 DTO]] · [[036_WSL2 기반 VSCode 개발 환경 구축 및 자바 프로젝트 실습]]

# 스프링 DI/IoC 기초 — 빌드 도구 없이 JAR 직접 설치로 배우기

이번 실습은 DI를 위한 스프링의 역할을 이해하기 위한 실습입니다. DI는 스프링이 없어도 할 수 있는 일입니다.

하지만 그것을 스프링 없이 하려면 코드를 수정하는 방식으로 해야하고 그렇게 되면 수정이 도미노 현상을 발생시키게 됩니다. 그래서 이번 실습에서는 그 도미노 문제를 확인해보고 스프링의 DI 서비스가 어떤 도움을 주는지를 경험하는 실습이 될 것입니다.

그리고 이번 실습에서는 빌드 도구 없이, 스프링 부트가 제공하는 라이브러리도 없이, 스프링의 DI을 사용하기 위한 최소한의 라이브러리만 사용해볼 예정입니다. 최소한의 라이브러리임에도 얼마나 많은 라이브러리를 다운받아야 하는지 빌드 도구가 얼마나 고마운 도구인지도 함께 경험해보는 실습이 될 예정입니다.

단순히 따라만 하지 말고, 지금 언급한 부분을 잘 확인해보시기 바랍니다.

**대상**: Java 기초(클래스, 인터페이스, 생성자)는 알지만 스프링과 DI/IoC 개념을 처음 접하는 분

**목표**: Maven·Gradle 없이 JAR 파일을 직접 내려받아 classpath에 연결하고, XML과 Annotation 두 가지 방식으로 스프링 컨테이너를 실행하며 의존성 주입의 원리를 체득한다

**완성물**: `lib/` 폴더에 JAR이 담긴 `spring-di-prj/` 프로젝트. `App.java`를 실행하면 `OrderService`가 `OrderRepository`를 주입받아 목업 데이터를 출력한다

**준비물**: JDK 21(또는 최신 LTS)가 설치되어 있어야 합니다. `java -version` 명령으로 확인하세요.

## 1. 프로젝트 뼈대 만들기

스프링을 빌드 도구 없이 쓰려면 JAR 파일을 직접 관리해야 합니다. 먼저 프로젝트의 뼈대를 만들며, 나중에 JAR을 넣을 `lib/` 폴더와 소스 코드가 들어갈 `src/` 폴더를 준비해 볼게요.

앞으로 모든 실습환경은 실제 리눅스 환경에서 다루는 것을 기본으로 하겠습니다. 현재 리눅스 환경이 아니라면 WSL 환경에서 작업하는 것을 기본으로 하겠습니다.

이 작업을 수행하기 전에 VSCode를 통해서 WSL에 접속한 후에 작업을 수행하기 바랍니다.

### 1-1. 프로젝트 폴더 생성

터미널에서 작업할 루트 폴더(예: `~/projects`)로 이동하고 다음 명령을 실행하세요.

```bash
mkdir -p spring-di-prj/src
mkdir -p spring-di-prj/lib
cd spring-di-prj
```

Windows PowerShell에서도 동일한 명령이 동작합니다.

### 1-2. 폴더 구조 확인

```bash
ls
```

**✅ 확인**

- `src`와 `lib` 폴더가 `spring-di-prj` 안에 생겼습니다.
- 현재 경로가 `spring-di-prj`입니다.

### 1-3. VSCode 실행

현재 폴더를 VSCode로 열기 위해 터미널에서 다음 명령을 실행하세요.

```bash
code .
```

**🎓 newlec 쌤의 코멘트**

보통 스프링 프로젝트를 만들면 빌드도구를 이용해서 `pom.xml`이나 `build.gradle` 파일이 먼저 생성합니다. 하지만 이 따라하기에서는 의도적으로 그걸 쓰지 않고 있습니다. 왜냐하면 스프링의 핵심은 '빌드 도구가 마법처럼 의존성을 찾아주는 것'이 아니라, '내가 만든 객체들이 어떻게 연결되는지'를 도와주는 것이기 때문입니다. JAR 파일을 직접 내려받고 classpath를 설정하는 과정을 거치면, 스프링 컨테이너가 실제로 어떤 파일들을 읽어서 객체를 만들어내는지 눈으로 확인할 수 있게 됩니다.

**📝 이 단계의 핵심**

- `lib/` 폴더는 외부 JAR 파일이 들어가는 곳입니다.
- `src/` 폴더는 우리가 작성할 Java 소스 파일이 들어가는 곳입니다.

## 2. 스프링 없이 코드 작성하기

스프링을 적용하기 전에, 먼저 '스프링 없이' 어떻게 코드를 작성하는지부터 만들어 볼게요. `OrderRepository` 인터페이스와 두 가지 구현체, 그리고 이들을 사용하는 `OrderService`와 `App` 클래스를 작성합니다. 데이터는 실제 DB에 연결하지 않고 목업 문자열을 반환하도록 합니다.

### 2-1. OrderRepository 인터페이스 작성

**파일**: `src/OrderRepository.java`

```java
public interface OrderRepository {
    String findOrderById(String id);
}
```

### 2-2. JdbcOrderRepository 구현체 작성

**파일**: `src/JdbcOrderRepository.java`

```java
public class JdbcOrderRepository implements OrderRepository {
    @Override
    public String findOrderById(String id) {
        // 목업: 실제 JDBC 로 DB 를 조회하는 대신 문자열 반환
        return "[JDBC] Order ID: " + id + " - Status: PAID";
    }
}
```

### 2-3. FileOrderRepository 구현체 작성

**파일**: `src/FileOrderRepository.java`

```java
public class FileOrderRepository implements OrderRepository {
    @Override
    public String findOrderById(String id) {
        // 목업: 실제 파일에서 읽는 대신 문자열 반환
        return "[FILE] Order ID: " + id + " - Status: SHIPPED";
    }
}
```

### 2-4. OrderService 클래스 작성

**파일**: `src/OrderService.java`

```java
public class OrderService {
    private final OrderRepository orderRepository;

    // 생성자: OrderRepository 를 주입받음
    public OrderService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    public String getOrderInfo(String id) {
        return "Service Result: " + orderRepository.findOrderById(id);
    }
}
```

### 2-5. App 클래스 작성 (직접 생성 방식)

**파일**: `src/App.java`

```java
public class App {
    public static void main(String[] args) {
        // 문제 상황: 구현체를 직접 new 로 생성
        OrderRepository repository = new JdbcOrderRepository();
        OrderService service = new OrderService(repository);

        String result = service.getOrderInfo("ORD-1001");
        System.out.println(result);
    }
}
```

**✅ 확인**

- `src/` 폴더 안에 `OrderRepository.java`, `JdbcOrderRepository.java`, `FileOrderRepository.java`, `OrderService.java`, `App.java` 총 5개 파일이 있습니다.
- 아직 컴파일은 하지 않았습니다.

**🎓 newlec 쌤의 코멘트**

여기서 `OrderService`는 `OrderRepository`의 구체적인 타입(`JdbcOrderRepository`)을 몰라야만 합니다. 인터페이스만 알면 됩니다. 하지만 `App` 클래스를 보면 `new JdbcOrderRepository()`라고 직접 생성하고 있기 때문에 이 부분이 바로 '제어 역전(IoC)'으로 해결해야 할 문제입니다.

제어의 역전이란 `App`이 `OrderService`를 만드는 것도, `OrderService`가 `OrderRepository`를 만드는 것도 모두 '내가 객체를 직접 만들어 연결하던 과정을, 그 책임을 외부에 맡기겠다.'는 의미입니다. 이 '만드는 책임'을 내가 아닌 스프링 컨테이너에게 넘기는 것이 DI의 핵심입니다.

그렇게 객체를 생성하고 조립을 내가 직접 안할 때의 장/단점을 체크해보시기 바랍니다.

**📝 이 단계의 핵심**

- `OrderService`는 `OrderRepository` 인터페이스를 의존성으로 가집니다.
- 현재 `App`은 `JdbcOrderRepository`를 하드코딩으로 생성하고 있습니다.

## 3. 컴파일·실행과 경직된 코드 확인

이제 지금 만든 코드를 컴파일하고 실행해서, 현재 상태가 얼마나 '경직된' 코드인지 확인해 볼 차례입니다. 특히 `JdbcOrderRepository`를 `FileOrderRepository`로 바꾸려면 어떤 일이 일어나는지 관심있게 봐주시기 바랍니다.

### 3-1. 컴파일

```bash
javac -d out src/*.java
```

`-d out`은 클래스 파일(`.class`)이 생성될 폴더를 `out`으로 지정하는 것입니다.

위의 명령어를 실행 디렉토리는 프로젝트 루트입니다.

### 3-2. 실행

```bash
java -cp out App
```

**✅ 확인**

- 터미널에 `Service Result: [JDBC] Order ID: ORD-1001 - Status: PAID`가 출력됩니다.

### 3-3. 구현체 변경 시나리오 시연

이제 Order 정보를 데이터베이스에 기록하지 말고 빅데이터로도 분석할 수 있도록 파일로 저장하자는 요구사항이 들어왔다고 가정해보겠습니다. 그러면 기존 코드를 수정해야 할까요? 아니면 새로운 클래스를 만들어서 교체를 해야할까요?

네 맞습니다. 이미 사용중인 코드를 수정하는 것보다는 확장하는 것이 더 바람직한 방법입니다. 그래서 `FileOrderRepository`로 바꾸고 싶다고 가정해 봅시다. 그러려면 우리는 `App.java` 코드를 수정해야 합니다.

**파일**: `src/App.java` (수정 전)

```java
OrderRepository repository = new JdbcOrderRepository();
```

**파일**: `src/App.java` (수정 후)

```java
OrderRepository repository = new FileOrderRepository();
```

수정 후 다시 컴파일하고 실행합니다.

```bash
javac -d out src/*.java
java -cp out App
```

**✅ 확인**

- 터미널에 `Service Result: [FILE] Order ID: ORD-1001 - Status: SHIPPED`가 출력됩니다.

**🎓 newlec 쌤의 코멘트**

보셨나요? 단순히 구현체만 바꾸기 위해 `App.java`라는 '최상위 실행 파일'을 수정해야 했습니다. 만약 `OrderService`를 사용하는 클래스가 100개 있었다면, 그 100개 파일을 모두 열어 `new` 문장을 수정해야 했을까요? 스프링의 DI는 이 '수정'을 코드에서 분리시켜 줍니다. 구현체를 바꾸는 행위를 코드(Java 파일)가 아닌 설정 파일이나 어노테이션으로 옮기는 것입니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `error: cannot find symbol` | `javac` 실행 시 `src/` 안의 모든 파일을 지정하지 않음 | `javac -d out src/*.java`로 전체 컴파일 |
| `Exception in thread "main" java.lang.NoClassDefFoundError` | `java` 실행 시 classpath에 `out` 폴더가 없음 | `java -cp out App`로 `-cp` 옵션 확인 |

**📝 이 단계의 핵심**

- 직접 `new`로 객체를 생성하면, 구현체 변경 시 해당 코드를 수정해야 합니다.
- 이 '수정의 번거로움'을 없애는 것이 DI의 목적입니다.

## 4. 스프링 JAR 직접 내려받기

이제 스프링 컨테이너를 이용해서 객체를 교체해야 할 경우에도 코드를 수정할 필요가 없다는 것을 경험하게 될 것입니다.

그리기 위해서 우선 스프링 컨테이너를 사용하기 위해서 스프링 JAR 파일을 구해오도록 하겠습니다. Maven Central에서 필요한 JAR 5개를 직접 내려받아 `lib/` 폴더에 배치하고, 컴파일 및 실행 시 `-cp` 옵션으로 연결하는 방법을 사용하도록 합니다.

### 4-1. 필요한 JAR 목록 확인

스프링 컨테이너의 기본 동작에 필요한 최소 JAR들은 다음과 같습니다. (Spring Framework 6.x 기준), 현재 최신 버전은 7.x입니다. 필요하면 그것도 상관없습니다.

- spring-core
- spring-beans
- spring-context
- spring-expression
- commons-logging (스프링이 로깅을 위해 사용하는 유틸리티)
- spring-aop

참고: Spring 6.x는 Java 17 이상을 요구합니다. JDK 21이므로 문제없습니다.

### 4-2. JAR 다운로드

브라우저로 Maven Central에 접속합니다.

1. 검색창에 `spring-core` 검색 → 최신 버전(예: 6.1.x) 클릭 → jar 파일 링크를 우클릭하여 `lib/` 폴더로 저장.
2. `spring-beans` 검색 → 같은 버전의 jar 파일을 `lib/`에 저장.
3. `spring-context` 검색 → 같은 버전의 jar 파일을 `lib/`에 저장.
4. `spring-expression` 검색 → 같은 버전의 jar 파일을 `lib/`에 저장.
5. `commons-logging` 검색 → 최신 버전(예: 1.2.x)의 jar 파일을 `lib/`에 저장.
6. `spring-aop` 검색 → 같은 버전의 jar 파일을 `lib/`에 저장.

팁: 파일 이름이 `spring-core-6.1.0.jar`처럼 버전이 붙어 있으면, `lib/` 안에서는 `spring-core.jar`로 이름을 바꾸는 것이 classpath 설정 시 편합니다. (선택 사항이지만 권장)

### 4-3. lib 폴더 내용 확인

```bash
ls lib/
```

**✅ 확인**

- `lib/` 폴더 안에 `spring-core.jar`, `spring-beans.jar`, `spring-context.jar`, `spring-expression.jar`, `commons-logging.jar` (또는 버전이 붙은 이름) 총 5개 파일이 있습니다.

**🎓 newlec 쌤의 코멘트**

Maven이나 Gradle을 쓰면 이 과정을 자동으로 해줍니다. 하지만 직접 해보면 알 수 있습니다. 스프링 컨테이너는 `spring-context` JAR 안에 있는 클래스들이 `spring-beans`, `spring-core`의 클래스들을 참조하면서 동작합니다. classpath에 이 JAR들이 없으면 `ClassNotFoundException`이나 `NoClassDefFoundError`가 발생합니다. `-cp` 옵션은 Java가 클래스를 찾을 때 어디를 봐야 하는지 알려주는 '지도'입니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| JAR 파일이 깨졌거나 0바이트 | 브라우저 다운로드 오류 | 다시 다운로드 |
| commons-logging 버전 불일치 | Spring 6.x는 Java 17+를 요구하므로 최신 commons-logging 사용 권장 | 1.2.x 이상 버전 사용 |

**📝 이 단계의 핵심**

- 스프링 컨테이너 실행에 최소 5개의 JAR이 필요합니다.
- `lib/` 폴더에 JAR을 모아두고, 컴파일/실행 시 `-cp`로 지정합니다.

## 5. XML 설정으로 스프링 컨테이너 사용하기

이제 스프링 컨테이너를 사용해서 `OrderService`와 `OrderRepository`를 연결해 볼게요. 먼저 가장 전통적인 방식인 XML 설정을 사용해 봅니다. `applicationContext.xml` 파일을 만들어 컨테이너에 "이 인터페이스는 이 구현체로 만들어줘"라고 지시합니다.

### 5-1. applicationContext.xml 작성

**파일**: `src/applicationContext.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.springframework.org/schema/beans
           http://www.springframework.org/schema/beans/spring-beans.xsd">

    <!-- OrderRepository 구현체 Bean 정의 -->
    <!-- id="jdbcOrderRepository" 는 이 Bean 의 이름 -->
    <bean id="jdbcOrderRepository" class="JdbcOrderRepository"/>

    <!-- OrderService Bean 정의 -->
    <!-- constructor-arg 의 ref 속성으로 jdbcOrderRepository 를 주입 -->
    <bean id="orderService" class="OrderService">
        <constructor-arg ref="jdbcOrderRepository"/>
    </bean>

</beans>
```

중요: `class` 속성에는 패키지 경로가 없으므로, 클래스가 기본 패키지(없음)에 있다고 가정합니다. 만약 `com.example` 패키지에 있다면 `class="com.example.JdbcOrderRepository"`로 작성해야 합니다. 이 예제에서는 편의상 기본 패키지로 작성했습니다.

### 5-2. App.java 수정 (XML 컨테이너 사용)

**파일**: `src/App.java`

```java
import org.springframework.context.support.ClassPathXmlApplicationContext;

public class App {
    public static void main(String[] args) {
        // XML 설정 파일을 읽어 컨테이너 생성
        // "classpath:applicationContext.xml" 은 classpath 루트에서 파일 탐색
        ClassPathXmlApplicationContext context = 
            new ClassPathXmlApplicationContext("applicationContext.xml");

        // 컨테이너에서 Bean 을 꺼냄
        OrderService service = context.getBean(OrderService.class);

        String result = service.getOrderInfo("ORD-1001");
        System.out.println(result);
        
        context.close();
    }
}
```

### 5-3. 컴파일 및 실행

```bash
javac -cp "lib/*" -d out src/*.java
java -cp "out:src:lib/*" App
```

Windows 메모: Windows에서 classpath 구분자는 세미콜론(`;`)입니다. `java -cp "out;lib/*" App`로 실행하세요. Mac/Linux는 콜론(`:`)입니다.

**✅ 확인**

- 터미널에 `Service Result: [JDBC] Order ID: ORD-1001 - Status: PAID`가 출력됩니다.
- `App.java`에 `new JdbcOrderRepository()`가 없습니다.

**🎓 newlec 쌤의 코멘트**

이제 `App`은 `OrderService`를 직접 만들지 않습니다. 대신 `ClassPathXmlApplicationContext`를 만들어 XML 파일을 읽게 하고, 그 컨테이너에서 `getBean(OrderService.class)`로 객체를 꺼냅니다. 컨테이너는 XML을 읽고 `OrderService`를 만들 때, `constructor-arg`에 지정된 `jdbcOrderRepository`를 찾아서 자동으로 주입해 줍니다. 이것이 '제어 역전'입니다. 객체를 '만드는' 주체가 `App`에서 Spring Container로 넘어간 것입니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `FileNotFoundException: class path resource [applicationContext.xml]` | XML 파일이 classpath 루트에 없음 | `applicationContext.xml`이 `out/` 폴더에 있는지 확인. `javac` 시 `-d out`으로 컴파일하면 `src/` 안의 리소스 파일도 `out/`에 복사되지 않습니다. 해결: `cp src/applicationContext.xml out/` 명령을 실행하거나, `java` 실행 시 `-cp "out:src:lib/*"`로 `src`도 classpath에 포함 |
| `BeanCreationException` | XML 문법 오류 또는 클래스 이름 오타 | XML의 `class` 속성 값과 실제 클래스 이름이 일치하는지 확인 |

**📝 이 단계의 핵심**

- XML 설정은 Bean의 `id`, `class`, 그리고 `constructor-arg`로 의존성을 정의합니다.
- `ClassPathXmlApplicationContext`는 XML 파일을 읽어 컨테이너를 초기화합니다.

## 6. XML 설정만으로 구현체 교체하기

XML 방식의 가장 큰 장점은 '구현체 변경 시 코드 수정 없이 설정만 바꾸면 된다'는 것입니다. `JdbcOrderRepository`를 `FileOrderRepository`로 바꾸는 과정을 시연해 볼게요.

### 6-1. applicationContext.xml 수정

**파일**: `src/applicationContext.xml`

`jdbcOrderRepository` Bean을 `fileOrderRepository`로 변경하고, `OrderService`의 `constructor-arg ref`도 함께 변경합니다.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.springframework.org/schema/beans
           http://www.springframework.org/schema/beans/spring-beans.xsd">

    <!-- 변경: JdbcOrderRepository -> FileOrderRepository -->
    <bean id="fileOrderRepository" class="FileOrderRepository"/>

    <bean id="orderService" class="OrderService">
        <!-- 변경: ref="jdbcOrderRepository" -> ref="fileOrderRepository" -->
        <constructor-arg ref="fileOrderRepository"/>
    </bean>

</beans>
```

### 6-2. 리소스 복사 및 실행

XML 파일만 수정했으므로, Java 파일은 다시 컴파일할 필요가 없습니다. 하지만 `out/` 폴더에 있는 `applicationContext.xml`은 여전히 구버전입니다.

```bash
cp src/applicationContext.xml out/
java -cp "out:lib/*" App
```

Windows: `copy src\applicationContext.xml out\`

**✅ 확인**

- 터미널에 `Service Result: [FILE] Order ID: ORD-1001 - Status: SHIPPED`가 출력됩니다.
- `App.java`는 변경하지 않았습니다.

**🎓 newlec 쌤의 코멘트**

이것이 DI의 힘입니다. `App.java`는 `OrderService`가 어떤 `OrderRepository`를 가지는지 모릅니다. 그저 `OrderService`를 주입받아서 `getOrderInfo`를 호출할 뿐입니다. 구현체가 바뀌는 것은 컨테이너의 '설정' 문제이지, '코드' 문제가 아닙니다. 운영 환경에서 DB 접속이 불안정해서 파일 기반 저장소로 임시 전환해야 할 때, 개발자가 코드를 고치지 않고 설정 파일만 수정하면 됩니다.

**📝 이 단계의 핵심**

- XML 방식에서는 구현체 변경 시 `applicationContext.xml`만 수정하면 됩니다.
- Java 소스 코드(`App.java`, `OrderService.java`)는 변경할 필요가 없습니다.

## 7. Annotation 방식으로 전환하기

XML 파일이 번거롭다고 느끼셨나요? 스프링은 Annotation을 통해 설정을 코드 안에 직접 쓸 수 있게 해줍니다. `@Component`, `@Service`, `@Configuration`, `@ComponentScan`을 사용해 XML 없이 컨테이너를 구성해 볼게요.

주의: Annotation을 사용하는 이번 예제에서는 모든 소스코드 파일에 패키지 명이 반드시 있어야 합니다. 왜냐하면 이제 코드에서 `@ComponentScan`을 `AppConfig` 자바 파일로 설정을 할 예정인데, 그 파일의 패키지명 이하의 모든 클래스 파일을 검색해서 Annotation 설정을 읽기 때문입니다. 클래스에 패키지 명이 없으면 스캔에서 제외됩니다.

### 7-1. JdbcOrderRepository에 @Component 추가

**파일**: `src/JdbcOrderRepository.java`

```java
package com.newlecture.app;
import org.springframework.stereotype.Component;

@Component
public class JdbcOrderRepository implements OrderRepository {
    @Override
    public String findOrderById(String id) {
        return "[JDBC] Order ID: " + id + " - Status: PAID";
    }
}
```

### 7-2. FileOrderRepository에 @Component 추가

**파일**: `src/FileOrderRepository.java`

```java
package com.newlecture.app;
import org.springframework.stereotype.Component;

@Component
public class FileOrderRepository implements OrderRepository {
    @Override
    public String findOrderById(String id) {
        return "[FILE] Order ID: " + id + " - Status: SHIPPED";
    }
}
```

### 7-3. OrderService에 @Service 추가

**파일**: `src/OrderService.java`

```java
package com.newlecture.app;
import org.springframework.stereotype.Service;

@Service
public class OrderService {
    private final OrderRepository orderRepository;

    public OrderService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    public String getOrderInfo(String id) {
        return "Service Result: " + orderRepository.findOrderById(id);
    }
}
```

### 7-4. AppConfig 클래스 작성 (Java Config)

**파일**: `src/AppConfig.java`

```java
package com.newlecture.app;

import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;

@Configuration
@ComponentScan
public class AppConfig {
    // 빈 메서드도 가능하지만, @ComponentScan 으로 클래스를 스캔하므로
    // 명시적인 @Bean 메서드는 필요 없습니다.
    // 만약 여러 OrderRepository 구현체가 @Component 로 붙어 있으면
    // @Primary 또는 @Qualifier 로 구분해야 합니다.
    // 이 예제에서는 JdbcOrderRepository 만 @Component 로 활성화해 두겠습니다.
    // (FileOrderRepository 는 주석 처리하거나 @Component 를 제거할 수 있음)
}
```

주의: `JdbcOrderRepository`와 `FileOrderRepository` 둘 다 `@Component`가 붙어 있으면, `OrderRepository` 타입의 Bean이 두 개가 되어 `NoUniqueBeanDefinitionException`이 발생합니다. 이 단계에서는 `JdbcOrderRepository`만 사용하므로, `FileOrderRepository`의 `@Component`를 주석 처리하거나 제거합니다.

**파일**: `src/FileOrderRepository.java` (수정)

```java
package com.newlecture.app;
// @Component  // 주석 처리: 현재는 JdbcOrderRepository 만 사용
public class FileOrderRepository implements OrderRepository {
    @Override
    public String findOrderById(String id) {
        return "[FILE] Order ID: " + id + " - Status: SHIPPED";
    }
}
```

### 7-5. App.java 수정 (Annotation 컨테이너 사용)

**파일**: `src/App.java`

```java
package com.newlecture.app;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;

public class App {
    public static void main(String[] args) {
        // Annotation 기반 컨테이너 생성
        // AppConfig 클래스를 파라미터로 전달
        AnnotationConfigApplicationContext context = 
            new AnnotationConfigApplicationContext(AppConfig.class);

        OrderService service = context.getBean(OrderService.class);

        String result = service.getOrderInfo("ORD-1001");
        System.out.println(result);
        
        context.close();
    }
}
```

**✅ 확인**

- `src/` 폴더에 `AppConfig.java`가 추가되었습니다.
- `JdbcOrderRepository.java`에 `@Component`가 있습니다.
- `FileOrderRepository.java`의 `@Component`는 주석 처리되어 있습니다.
- `App.java`는 `AnnotationConfigApplicationContext`를 사용합니다.

**🎓 newlec 쌤의 코멘트**

`@Configuration`은 이 클래스가 스프링 컨테이너의 설정 클래스임을 나타냅니다. `@ComponentScan`은 현재 패키지(기본 패키지) 안의 클래스들을 스캔하여 `@Component`, `@Service`, `@Repository` 등이 붙은 클래스들을 자동으로 Bean으로 등록합니다. `AnnotationConfigApplicationContext`는 XML 파일 대신 Java 클래스(`AppConfig`)를 읽어 컨테이너를 초기화합니다. 이 방식이 현재 스프링 프로젝트에서 가장 많이 사용됩니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `NoUniqueBeanDefinitionException` | `OrderRepository` 구현체가 두 개 이상 `@Component`로 등록됨 | 사용하지 않는 구현체의 `@Component`를 주석 처리하거나, `@Primary`를 한 곳에만 붙임 |
| `NoSuchBeanDefinitionException` | `@ComponentScan`이 클래스를 찾지 못함 | `AppConfig`가 있는 패키지에서 `@ComponentScan`이 동작하는지 확인. 기본 패키지는 빈 문자열("")이므로 문제없음 |

**📝 이 단계의 핵심**

- `@Component`, `@Service`는 클래스를 Bean으로 등록합니다.
- `@Configuration` + `@ComponentScan`은 Java로 설정을 정의하는 방법입니다.
- `AnnotationConfigApplicationContext`는 Java 설정 클래스를 읽어 컨테이너를 만듭니다.

## 8. Annotation 설정만으로 구현체 교체하기

XML 방식과 마찬가지로, Annotation 방식에서도 구현체를 바꾸는 과정을 시연해 볼게요. 이번에는 `FileOrderRepository`를 사용하도록 변경합니다.

### 8-1. JdbcOrderRepository의 @Component 주석 처리

**파일**: `src/JdbcOrderRepository.java`

```java
package com.newlecture.app;

// @Component  // 주석 처리: 현재는 FileOrderRepository 만 사용
public class JdbcOrderRepository implements OrderRepository {
    @Override
    public String findOrderById(String id) {
        return "[JDBC] Order ID: " + id + " - Status: PAID";
    }
}
```

### 8-2. FileOrderRepository의 @Component 활성화

**파일**: `src/FileOrderRepository.java`

```java
package com.newlecture.app;
import org.springframework.stereotype.Component;

@Component  // 활성화
public class FileOrderRepository implements OrderRepository {
    @Override
    public String findOrderById(String id) {
        return "[FILE] Order ID: " + id + " - Status: SHIPPED";
    }
}
```

### 8-3. 컴파일 및 실행

```bash
javac -cp "lib/*" -d out src/*.java
java -cp "out:lib/*" App
```

Windows: `java -cp "out;lib/*" App`

**✅ 확인**

- 터미널에 `Service Result: [FILE] Order ID: ORD-1001 - Status: SHIPPED`가 출력됩니다.
- `App.java`와 `AppConfig.java`는 변경하지 않았습니다.
- `OrderService.java`도 변경하지 않았습니다.

**🎓 newlec 쌤의 코멘트**

Annotation 방식에서는 구현체 변경 시, 해당 클래스의 `@Component`(또는 `@Service`, `@Repository`)를 주석 처리하거나 활성화하는 것만으로 충분합니다. XML 방식에서는 XML 파일을 수정해야 했지만, Annotation 방식에서는 Java 파일 하나만 수정하면 됩니다. 하지만 여전히 '설정'이라는 개념은 존재합니다. XML은 외부 파일, Annotation은 코드 내부의 메타데이터입니다.

**📝 이 단계의 핵심**

- Annotation 방식에서는 `@Component` 주석 처리/활성화로 구현체를 교체합니다.
- `App.java`와 `OrderService.java`는 변경할 필요가 없습니다.

## 9. 세 가지 방식 비교와 정리

이제 세 가지 방식을 모두 경험했습니다. 마지막으로 이 세 가지 방식을 비교하고, DI/IoC의 이점을 정리해 볼게요.

### 9-1. 세 가지 방식 비교

| 구분 | DI 미적용 (직접 생성) | XML 설정 | Annotation 설정 |
|---|---|---|---|
| 객체 생성 주체 | App (개발자 코드) | Spring Container | Spring Container |
| 구현체 변경 시 | App.java 수정 | applicationContext.xml 수정 | @Component 주석 처리/활성화 |
| 설정 위치 | Java 코드 내부 | 외부 XML 파일 | Java 코드 내부 (Annotation) |
| 가독성 | 높음 (직관적) | 중간 (XML 구조 이해 필요) | 높음 (Java 코드와 통합) |
| 유지보수 | 어려움 (코드 수정 필요) | 쉬움 (설정 분리) | 쉬움 (설정 분리) |
| 테스트 용이성 | 어려움 (Mock 주입 어려움) | 쉬움 (Bean 교체 가능) | 쉬움 (Bean 교체 가능) |

### 9-2. IoC와 DI의 이점

- **결합도(Coupling) 감소**: `OrderService`는 `OrderRepository`의 구체적 구현체를 몰라서, `JdbcOrderRepository`가 바뀌어도 `OrderService` 코드는 변경되지 않습니다.
- **테스트 용이성**: `OrderService`를 테스트할 때, 실제 `JdbcOrderRepository` 대신 `MockOrderRepository`를 주입할 수 있습니다.
- **유연성**: 구현체를 변경할 때 설정만 수정하면 되어, 코드 배포 없이도(XML 경우) 또는 최소한의 재컴파일로(Annotation 경우) 동작을 변경할 수 있습니다.
- **관심사 분리(Separation of Concerns)**: '객체를 만드는 로직'과 '객체를 사용하는 로직'이 분리됩니다.

### 9-3. 마무리

이제 스프링의 DI/IoC 개념을 빌드 도구 없이 직접 JAR을 내려받고, XML과 Annotation 두 가지 방식으로 적용해 보았습니다. 실제 프로젝트에서는 Maven/Gradle을 사용해 JAR 관리를 자동화하고, `@SpringBootApplication`이라는 통합 어노테이션을 사용해 컨테이너를 더 쉽게 생성합니다. 하지만 이 기초를 이해하고 나면, 스프링이 '마법'이 아니라 '구조화된 객체 관리'라는 것을 알게 될 것입니다.

**✅ 확인**

- 이 단계는 학습 정리입니다.
- `spring-di-prj/` 폴더가 완성되었습니다.

**🎓 newlec 쌤의 코멘트**

스프링을 처음 배울 때 가장 헷갈리는 것이 '왜 이렇게 복잡한 구조를 만들어야 하는가'입니다. 하지만 이 따라하기를 통해 보셨듯이, DI는 '복잡함'을 위해 존재하는 것이 아니라, '변경에 대한 유연성'을 위해 존재합니다. 시스템이 커질수록, 요구사항이 바뀔수록, DI의 이점은 기하급수적으로 커집니다.

**📝 이 단계의 핵심**

- DI는 객체 생성의 책임을 개발자 코드에서 컨테이너로 옮기는 것입니다.
- XML과 Annotation은 모두 DI를 구현하는 방법이며, Annotation이 현재 표준입니다.
- IoC는 테스트 용이성과 유지보수성을 높여줍니다.

## 정리

1단계: `lib/`와 `src/` 폴더를 만들어 빌드 도구 없는 프로젝트 구조를 세웠다.
2단계: `OrderRepository` 인터페이스와 두 구현체, `OrderService`, `App`을 작성했다.
3단계: 직접 `new`로 객체를 생성하는 방식의 문제점(구현체 변경 시 코드 수정)을 확인했다.
4단계: Maven Central에서 스프링 JAR 5개를 내려받아 `lib/`에 배치하고 classpath를 설정했다.
5단계: `applicationContext.xml`을 작성하고 `ClassPathXmlApplicationContext`로 컨테이너를 실행했다.
6단계: XML만 수정하여 구현체를 `JdbcOrderRepository`에서 `FileOrderRepository`로 변경했다.
7단계: `@Component`, `@Configuration`, `@ComponentScan`을 사용해 Annotation 기반 컨테이너를 구성했다.
8단계: `@Component` 주석 처리/활성화로 Annotation 방식에서도 구현체를 변경했다.
9단계: 세 가지 방식을 비교하고 DI/IoC의 이점(결합도 감소, 테스트 용이성, 유연성)을 정리했다.
