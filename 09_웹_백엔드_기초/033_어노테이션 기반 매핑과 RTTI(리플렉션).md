---
tags: [서블릿, 톰캣, 어노테이션, 리플렉션, RTTI, HTTP]
날짜: 2026-08-12
---

> 🔗 관련 노트: [[032_톰캣과 서블릿, 생명주기와 빌드 도구]] · [[029_오버라이드와 super, 생성자 체이닝]]

# 어노테이션 기반 매핑과 RTTI(리플렉션)

앞으로 프로젝트는 계속 **빌드 도구**(대표적으로 **Maven**)를 이용해서 만든다. 지금 서블릿을 들여다보는 이유는, 최종 목적지인 **스프링**을 이해하기 위한 사전 지식이 필요하기 때문이다. 서블릿 자체에 통달할 필요는 없고, "어떻게 매핑이 이루어지는가"와 "그걸 가능하게 하는 자바 기능이 무엇인가"만 잠깐 들여다본다는 감각으로 보면 된다.

## 1. 지금까지 한 것 — 수동 매핑, 그리고 그 한계

이전에 만든 톰캣은 **임베디드 톰캣**(우리가 직접 자바 코드 안에서 도구로 갖다 쓰는 톰캣)이었다. 그래서 `main()` 함수 안에서 이렇게 URL과 서블릿 클래스를 직접 짝지어줄 수 있었다.

```java
Tomcat.addServlet(context, servletName, new HelloServlet());
context.addServletMappingDecoded("/hello", servletName);
```

**서버로 쓰는 톰캣**(우리가 직접 `main()`을 짜지 않고, 완성된 톰캣 프로그램을 설치해서 띄우는 경우)이라면 이렇게 코드로 매핑을 넘겨줄 방법이 없다 — 그래서 `WEB-INF/web.xml` 같은 설정 파일로 "이 URL이 오면 이 클래스를 써라"를 알려줘야 한다. 즉 **매핑을 코드로 주느냐, 설정 파일로 주느냐**의 차이일 뿐, **어떤 식으로든 매핑은 반드시 있어야 한다**는 게 핵심이다.

### 왜 매핑이 반드시 필요한가 — 웹서버와 WAS의 차이

톰캣의 원래 역할(웹서버)은 단순하다. 홈 디렉토리에서 요청받은 경로의 문서를 찾아보고, 있으면 돌려주고 **없으면 404**를 낸다.

그런데 우리는 "이 URL이 오면 이 서블릿 객체를 실행해서 그 결과를 돌려달라"는 걸 원한다. 이건 단순 파일 조회가 아니라 **프로그램을 실행**하는 일이다. 이렇게 요청에 맞는 객체를 찾아 실행까지 해주는 역할을 하는 걸 **WAS**(Web Application Server)라고 한다. 톰캣이 순수 웹서버 역할만 한다면 매핑 자체가 필요 없지만, **WAS 역할을 하려면 "이 URL 요청이 오면 이 객체를 실행해라"는 매핑 정보가 반드시 있어야 한다.**

### 수동 매핑의 문제 — 서블릿이 늘어날수록

애플리케이션 하나를 제대로 만들려면 서블릿이 최소 몇 개나 필요할까? CRUD(생성/조회/수정/삭제)만 생각해도 최소 4~5개의 서블릿이 필요하다.

문제는 서블릿을 하나 추가할 때마다:

- 서블릿 클래스 파일을 새로 만들어야 하고
- **`App.java`에도 매핑 코드를 한 줄 더 추가**해야 한다

```java
tomcat.addServlet("", servletName1, new Servlet1());
context.addServletMappingDecoded("/path1", servletName1);
tomcat.addServlet("", servletName2, new Servlet2());
context.addServletMappingDecoded("/path2", servletName2);
// 서블릿이 늘어날수록 이 반복이 계속 늘어난다...
```

이렇게 되면:

- 반복되는 코드가 계속 늘어나서 나중에 고칠 게 많아지고
- 매핑 정보가 서블릿 클래스가 아니라 **다른 파일(`App.java`)에 있어서** 코드를 볼 때마다 파일을 왔다갔다 해야 하고
- 다른 사람이 만든 서블릿을 갖다 쓸 때 매핑 코드 추가를 깜빡하면 버그가 된다

## 2. 그래서 등장한 것 — 어노테이션 기반 매핑

이 불편함을 해결하기 위해 등장한 방법이 **애노테이션(annotation)**이다. 서블릿 클래스 위에 애노테이션을 붙이면 "이 URL이 오면, 이 클래스를 객체화해서 여기 있는 걸 실행해달라"는 뜻이 된다.

```java
@WebServlet("/test")
public class TestServlet extends HttpServlet {
    // ...
}
```

이렇게 하면 **매핑 정보가 서블릿 클래스 자기 자신 안에** 담긴다. 서블릿을 추가할 때 `App.java`를 고칠 필요가 없다 — 클래스 파일 하나만 새로 만들고, 그 위에 `@WebServlet("/새경로")`만 붙이면 끝이다.

### 톰캣이 애노테이션을 읽으려면

애노테이션은 그냥 클래스에 붙여놓은 표시일 뿐이다. 톰캣이 그 표시를 실제로 읽어서 매핑에 반영하려면, "어디를 뒤져서 애노테이션을 찾을지"를 톰캣에게 알려주는 별도 설정이 필요하다. `maven_servlet_project`의 `App.java`에는 이 설정 과정이 그대로 남아 있다.

```java
File docBase = new File("src/main/webapp");
if (!docBase.exists() && !docBase.mkdirs()) {
    throw new IllegalStateException("docBase 디렉터리를 만들 수 없습니다: " + docBase.getAbsolutePath());
}
Context context = tomcat.addWebapp("", docBase.getAbsolutePath());

WebResourceRoot resources = new StandardRoot(context);
resources.addPreResources(new DirResourceSet(resources, "/WEB-INF/classes",
        new File("target/classes").getAbsolutePath(), "/"));
context.setResources(resources);
```

코드가 하는 일을 한 줄씩 뜯어보면 이렇다.

1. **`tomcat.addWebapp(...)`** — `tomcat.addContext(...)`는 빈 Context 하나만 만들 뿐, 애노테이션 스캔 기능은 켜주지 않는다. `addContext(...)` 대신 **`addWebapp(...)`**을 써야 비로소 다음 두 가지가 함께 켜진다.
   - `@WebServlet` 같은 애노테이션을 스캔하는 기능
   - `web.xml` 기반의 기본 서블릿(정적 파일 서비스) 등록
2. **`WebResourceRoot` / `DirResourceSet`** — 톰캣은 애노테이션 스캔 대상을 아무 데서나 찾지 않고, **`WEB-INF/classes`라는 정해진 경로 아래만** 뒤진다. 그런데 우리가 만든 `.class` 파일은 Maven이 컴파일해서 만들어놓은 `target/classes`에 있지, `WEB-INF/classes`라는 폴더가 실제로 있는 건 아니다. `DirResourceSet`은 "톰캣이 `WEB-INF/classes`를 들여다볼 때, 실제로는 `target/classes` 폴더를 보고 있는 것처럼" 두 경로를 연결해주는 역할을 한다.

정리하면, 이 코드는 "이 클래스들은 이러이러한 경로(`target/classes`)에 번역되어 있으니, 그걸 `WEB-INF/classes`인 것처럼 보고 애노테이션을 확인해서 URL을 적용해라"는 지시를 톰캣에게 대신 해주는 코드다.

### 어노테이션이란 정확히 무엇인가

**애노테이션은 실행 환경(프로그램)이 실행 중에 읽을 수 있게 코드에 달아놓는 주석**이다. 사람이 보는 일반 주석(`//`, `/* */`)과 정반대다.

- 사람이 보는 주석은 컴파일하면 **사라진다** — 클래스 파일(바이트코드)에는 남지 않는다
- 애노테이션은 남길 수도, 사라지게 할 수도 있지만 **일반적으로는 실행 환경이 볼 수 있게 컴파일 후에도 그대로 남는다** — 그래서 톰캣이 실행 중에 `@WebServlet("/test")`라는 정보를 클래스 파일에서 다시 읽어낼 수 있는 것이다

## 3. 톰캣은 어노테이션을 어떻게 "읽어서 실행"까지 하는가 — RTTI

애노테이션을 읽는 방법과 사용법 자체는 이미 여러 자료에 잘 나와 있다. 여기서 다룰 건 조금 더 깊은 내용이다 — **어노테이션을 어떻게 읽고, 그 정보로 어떻게 객체를 만들어서 실행까지 시키는가**다. 이건 자바의 **RTTI**(Runtime Type Information, 런타임 타입 정보)를 알아야 이해할 수 있다.

### 타입 정보를 얻는 세 가지 방법

자바에서 클래스의 타입 정보를 담은 구조체 `Class<?>`를 얻는 대표적인 방법은 세 가지다.

**1. 객체 인스턴스에서 획득 — `obj.getClass()`**

이미 생성된 객체가 있을 때, `Object` 클래스가 제공하는 `getClass()` 메소드로 얻는다.

```java
Exam exam = new Exam();
Class<?> cls = exam.getClass();
```

**2. 클래스 리터럴 사용 — `ClassName.class`**

소스 코드 작성 시점에 클래스 타입을 직접 알고 있을 때 쓴다. 컴파일 타임에 체크되므로 셋 중 가장 간단하고 안전하다.

```java
Class<?> cls = Exam.class;
```

**3. 문자열로 동적 로딩 — `Class.forName("패키지명.클래스명")`**

클래스의 풀 패키지 경로를 문자열로 전달해서, **런타임에 동적으로** 클래스를 불러온다.

```java
Class<?> cls = Class.forName("com.example.Exam");
```

`Class<?>`는 그 타입에 대한 정보(필드, 메소드, 애노테이션, 생성자 등)를 들여다볼 수 있는 **돋보기** 같은 구조체다. 1번과 2번은 소스 코드에 클래스 이름이 그대로 드러나 있는 상황에서 쓴다. 반면 **3번(`Class.forName`)은 소스 코드 작성 시점에 클래스 이름을 몰라도, 문자열만 있으면** 타입 정보를 얻어낼 수 있다는 점이 다르다 — 톰캣이 디렉토리를 뒤져서 클래스 이름 문자열만 알아낸 상태로 그 클래스를 다뤄야 하는 지금 상황이 정확히 이 경우다.

### 클래스 이름만으로 객체 만들기 — `new` 없이

`Class.forName(...)`을 쓰면 **문자열로 된 클래스 이름만으로** 타입 정보를 얻을 수 있다. `workspace2/my-java-app/src/annotation/App.java`의 예시가 정확히 이 과정을 보여준다.

```java
package annotation;

import com.newlecture.examlib.entity.Exam;

import java.lang.reflect.Constructor;
import java.lang.reflect.Field;

public class App {
    public static void main(String[] args) throws Exception {
        // RTTI(런타임 타입 정보) : 런타임에 클래스의 정보를 얻을 수 있는 기능
        // Runtime Type Information

        // 1. 동적으로 불러올 클래스의 전체 경로(패키지명 + 클래스명)를 문자열로 준비합니다.
        String className = "com.newlecture.examlib.entity.Exam";

        // 2. Class.forName(): 문자열로 된 클래스 이름을 이용해 해당 클래스의 정보(Class 객체)를 메모리에 로드합니다.
        Class<?> cls = Class.forName(className);
        // Class<?> cls = Exam.class; // (참고: 코드 작성 시점에 클래스를 직접 지칭하는 일반적인 방식)

        // 3. getDeclaredConstructor(): 해당 클래스에 선언된 기본 생성자(매개변수가 없는 생성자)를 가져옵니다.
        Constructor<?> constructor = cls.getDeclaredConstructor();

        // 4. newInstance(): 가져온 생성자를 실행하여 실제 객체(인스턴스)를 동적으로 생성하고, Exam 타입으로 형변환합니다.
        Exam exam = (Exam) constructor.newInstance();
        // Exam exam = new Exam(); // (참고: new 키워드로 직접 객체를 생성하는 일반적인 방식)

        // 5. getClass(): 이미 생성된 객체(exam)로부터 역으로 해당 객체의 클래스 정보(Class)를 얻어옵니다.
        Class<?> clsExam = exam.getClass();

        // 6. getDeclaredFields() / getDeclaredMethods(): 클래스 안에 선언된 모든 변수(필드)와 메서드 목록을 가져오는 기능입니다.
        cls.getDeclaredFields();
        cls.getDeclaredMethods();

        // 7. 생성한 객체를 saveCSV 메서드로 전달하여 내부 필드 이름을 출력합니다.
        saveCSV(exam);
    }

    // Object 타입으로 전달받아, 어떤 객체든 들어올 수 있도록 만듭니다.
    private static void saveCSV(Object data) {
        // 8. 전달받은 객체의 실제 클래스 정보를 조회합니다.
        Class<?> cls = data.getClass();
        
        // 9. 클래스의 전체 이름(패키지 포함)을 출력합니다.
        System.out.println(cls.getName());
        
        // 10. 해당 클래스에 선언된 모든 변수(필드)들의 정보 배열을 가져옵니다.
        Field[] fields = cls.getDeclaredFields();

        // 11. 반복문을 돌며 클래스 내부에 정의된 변수(필드)들의 이름을 하나씩 출력합니다.
        for (int i = 0; i < fields.length; i++) {
            String fieldNama = fields[i].getName();
            System.out.println(fieldNama);
        }
    }
}
```

핵심은 두 가지다.

- **모든 객체가 `new`로만 만들어지는 건 아니다.** `cls.getDeclaredConstructor()`로 생성자 정보를 얻고, 그 `Constructor`의 `newInstance()`를 호출하면 `new Exam()`과 완전히 똑같은 결과가 나온다. 다른 점은, 이 방식은 **`Exam`이라는 이름을 소스 코드에 직접 쓰지 않고도**(문자열 `className`만 가지고) 객체를 만들어낼 수 있다는 것이다
- **어떤 객체든 `.getClass()`로 자신의 타입 정보를 스스로 알려줄 수 있다.** `saveCSV(Object data)`처럼 매개변수 타입을 `Object`로 열어두면, 어떤 객체가 넘어오든 `data.getClass()`로 실제 타입을 알아내고, `getDeclaredFields()`로 그 타입이 가진 필드 이름들을 뽑아낼 수 있다 — `Exam`이든 다른 무엇이든, 코드를 미리 알지 못해도 속성 이름을 알아낼 수 있는 것이다

이게 왜 필요한지는 라이브러리를 만드는 입장에서 생각하면 명확해진다. `save(exam)`처럼 특정 타입 하나만 저장하는 함수라면 `exam.getKor()`, `exam.getEng()`처럼 속성을 미리 다 알고 저장하면 된다. 하지만 **"어떤 객체든 저장할 수 있는" 범용 라이브러리**를 만들려면, 넘겨받는 객체가 `Exam`으로 고정되어 있지 않으니 그 객체가 무슨 속성을 가졌는지 미리 알 방법이 없다 — 이걸 실행 중에 알아내게 해주는 것이 RTTI(리플렉션)다. (RTTI는 입문 수준의 지식이 아니라, 나중에 라이브러리나 프레임워크를 직접 만드는 입장이 될 때 필요한 지식이다. 지금은 "이런 게 있다"는 정도로만 알아둬도 충분하다.)

### 톰캣 입장에서 정리하면

톰캣(또는 앞으로 배울 스프링)이 어노테이션 기반 매핑을 처리하는 전체 그림은 이렇다.

1. 서버가 시작될 때, 지정된 디렉토리(`WEB-INF/classes`)의 `.class` 파일들을 파일 API로 전부 탐색한다
2. 각 클래스 이름(문자열)에 대해 `Class.forName(...)`으로 타입 정보를 얻고, `@WebServlet` 같은 애노테이션이 붙어있는지 확인한다
3. 이렇게 얻은 "URL ↔ 클래스" 매핑 정보를 **메모리에 배열/맵으로 미리 캐싱**해둔다 — 매 요청마다 디렉토리를 다시 탐색하면 느리기 때문이다
4. 요청이 들어오면 그 URL에 해당하는 클래스를 캐시에서 찾아, `Constructor.newInstance()`로 객체를 만들고, 해당 메소드(`service` 등)를 찾아 **`invoke(...)`로 호출**해서 응답을 만든다

우리가 앞으로 쓰게 될 톰캣이나 스프링 같은 라이브러리는 내부적으로 이런 방식(디렉토리 스캔 → RTTI로 클래스/애노테이션 확인 → `newInstance` → `invoke`)으로 동작한다는 걸 알아두면, "이게 어떻게 동작하는 거지?"라는 의문에 답을 갖고 있는 셈이 된다.

## 4. HTTP 요청 메소드와 에러 코드

클라이언트가 서버에 요청하는 방법에는 여러 종류가 있다. HTTP로는 **GET, POST, PUT, PATCH, DELETE** 등을 쓸 수 있다.

- **GET**: 원격에 있는 리소스를 "달라"고 요청하는 것 — 문서 조회가 대표적이다
- **POST**: 무언가를 "제출"하는 요청. 예를 들어 로그인 폼에서 id/pw를 입력하고 버튼을 누르는 건, 서버에게 뭘 달라는 게 아니라 **입력한 값을 서버로 제출(submit)**하는 것이므로 POST다

브라우저를 기반으로 순수하게(자바스크립트 없이) 요청할 수 있는 방법은 **GET과 POST뿐**이다. PUT/PATCH/DELETE 같은 요청은 자바스크립트나 별도 도구를 써야 보낼 수 있다 — 이건 나중에 자바스크립트를 배우면 다룰 내용이다. 참고로 브라우저 주소창에 URL을 직접 입력해서 오는 요청은 **항상 GET**이다.

자주 만나는 에러 코드도 함께 정리한다.

| 코드 | 의미 |
|---|---|
| 404 | 요청한 리소스(URL)가 없음 |
| 403 | 권한이 없음 |
| 405 | 그 요청 방식(메소드)을 처리할 수 없음 |

## 5. 요청이 들어왔을 때 실제로 벌어지는 일 — `service`와 `doGet`/`doPost`의 관계

`/test`로 GET 요청이 들어왔을 때 벌어지는 일을 순서대로 보면 이렇다.

1. 시작할 때 이미 매핑 정보를 긁어와 알고 있는 톰캣이 요청을 받는다(URL로 오는 요청은 100% GET이다)
2. `newInstance()` 방식으로 톰캣이 서블릿 객체를 만들고, 그 객체의 `init()`을 호출한다 — `TestServlet`이 `init()`을 오버라이드하지 않았다면, 부모(`HttpServlet`)의 `init()`이 그대로 실행된다
3. `init()` 다음은 **`service()`**다. `TestServlet`이 `service()`를 오버라이드했다면 그게 호출되고, 오버라이드하지 않았다면 부모의 `service()`가 실행되어 `doGet`/`doPost` 등으로 **분배**해준다

`maven_servlet_project`의 `TestServlet.java`가 정확히 이 지점을 보여준다.

```java
@WebServlet("/test")
public class TestServlet extends HttpServlet {

    // 404 에러 : 리소스가 없음
    // 403 에러 : 권한 없음
    // 405 에러 : method가 없음
    @Override
    protected void service(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.getWriter().print("Hello Test Page");
        // super.service(req, resp); service에서 끝낼 거면 이 내용은 없어야된다.
    }
}
```

### 왜 `super.service(...)`를 호출하면 안 되는가

여기서 아주 중요한 함정이 있다.

- `service()`를 오버라이드하고 그 안에서 응답까지 다 끝낸다면(위 코드처럼), **절대로 `super.service(req, resp)`를 호출하면 안 된다.**
- `super.service(...)`를 호출하면, 부모 `HttpServlet`의 `service()`가 실행되면서 요청을 다시 `doGet`/`doPost`로 분배하려고 시도한다. 그런데 `TestServlet`은 `doGet`도 `doPost`도 구현한 적이 없다 — `HttpServlet`의 `doGet`/`doPost`는 기본적으로 "구현되지 않음" 상태(추상적으로 비어있는 것과 같은 처리)라서, 이 분배 과정에서 예외가 발생하고 **405 에러**로 이어진다

즉 오버라이드 방식은 두 갈래로 나뉜다.

- **`service()`를 통째로 오버라이드해서 내가 다 처리**한다 — 이 경우 `super.service(...)`를 부르면 안 된다. 이미 내가 응답을 다 만들었는데, 굳이 부모에게 다시 GET/POST 분배를 맡길 이유가 없고, 맡기는 순간 doGet/doPost가 없어서 터진다
- **`doGet`/`doPost` 같은 특화된 메소드만 오버라이드**한다 — 이 경우는 `service()`를 건드리지 않으므로, 부모의 `service()`가 정상적으로 분배 역할을 해준다. `LifecycleServlet`처럼 `super.service(req, resp)`를 호출하는 패턴이 바로 이 경우다 — 그 서블릿은 `service()` 안에서 로그만 남기고 **분배는 그대로 부모에게 맡기기 때문에** `super.service(...)` 호출이 맞다

같은 "오버라이드 후 `super` 호출"이라도, `service()` 자체를 오버라이드하는 상황과 `doGet`/`doPost`만 오버라이드하는 상황은 완전히 다른 이야기라는 걸 이 두 예제를 비교하면 명확히 알 수 있다. 예를 들어 `doPost`만 구현하고 GET 요청을 보내면, `service()`가 정상적으로 분배를 시도하지만 `doGet`이 없어서 똑같이 405가 난다 — "요청은 왔는데 그 요청 방식을 처리할 메소드가 없다"는 게 405의 정확한 의미다.

