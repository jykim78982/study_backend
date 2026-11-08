---
tags: [서블릿, Maven, 빌드도구, pom.xml, 실습]
---

> 🔗 관련 노트: [[032_톰캣과 서블릿, 생명주기와 빌드 도구]] · [[006_서블릿 프로그램 만들기]]

# [실습 7] 빌드 도구를 이용한 자바 프로젝트

## 왜 지금 다시 프로젝트를 새로 만드는가

지금까지는 자바 프로젝트를 만들 때 특정 IDE(VS Code)를 기반으로 프로젝트를 생성해왔다. 이전 실습에서도 `lib` 폴더에 jar를 직접 넣고, VS Code의 클래스패스 설정으로 프로젝트를 구성했다.

문제는 이렇게 만든 프로젝트는 **다른 IDE에서는 열어볼 수도, 호환도 안 된다**는 점이다. 특정 IDE용으로 만든 프로젝트는 그 IDE로만 계속 써야 하는 종속 관계가 생긴다. 이건 이전 노트 3~4장에서 다룬 "IDE 간 프로젝트 비호환" 문제 그 자체다.

그래서 앞으로는 **IDE에 종속되지 않는 도구(빌드 도구) 기반으로 프로젝트를 만들고, 그 위에 IDE를 연결해서 쓰는 방식**을 기본으로 한다. Maven은 이 목적에 맞는 좋은 선택지다 — 안정적이고 사용률이 높을 뿐 아니라, Maven으로 만든 프로젝트는 어떤 IDE로 열든 똑같이 동작한다.

이번 실습은 Maven으로 VS Code에서 외부 라이브러리(`tomcat-embed`)를 설정하고, 서블릿 환경을 직접 구축해서 실행해보는 과정이다. Maven은 프로젝트 루트의 **`pom.xml`에 의존성(dependency)을 선언**하는 방식이고, VS Code의 Extension Pack for Java가 이 방식을 안정적으로 지원한다.

## 1. VS Code에서 Maven 프로젝트 생성

1. `Ctrl+Shift+P`(macOS는 `Cmd+Shift+P`)로 명령 팔레트를 연다
2. `Java: Create Java Project...`를 입력해서 자바 프로젝트 생성을 선택한다
3. 빌드 도구 목록에서 **Maven**을 선택한다
4. 아키타입(템플릿) 선택 창에서 **`maven-archetype-quickstart`**(또는 `No Archetype`)를 선택한다
5. 버전과 그룹 정보를 입력한다
   - Version: `1.4`(또는 최신 버전)
   - GroupId: `com.example`
   - ArtifactId: `maven_servlet_project`
6. 저장할 폴더를 선택한다(예: `workspace2`)

프로젝트를 생성하면 터미널에 groupId, artifactId, version이 맞는지 확인하는 질문이 순서대로 뜬다. 이미 앞 단계에서 값을 다 지정했으므로, 그냥 엔터를 계속 치면 설정한 기본값 그대로 프로젝트가 만들어진다.

```
[INFO] <<< maven-archetype-plugin:3.1.2:generate (default-cli) < generate-sources @ standalone-pom <<<
[INFO]
[INFO] --- maven-archetype-plugin:3.1.2:generate (default-cli) @ standalone-pom ---
[INFO] Generating project in Interactive mode
[INFO] Using property: groupId = com.example
[INFO] Using property: artifactId = maven_servlet_project
Define value for property 'version' 1.0-SNAPSHOT: :
```

프로젝트가 성공적으로 만들어지면 "아무 키나 누르라"는 안내가 뜬다. 엔터를 눌러 마무리한다.

실제 지정한 폴더로 가서 프로젝트가 잘 만들어졌는지 확인하고, VS Code로 그 폴더를 연다. Maven 프로젝트 특유의 구조(`src/main/java`, `pom.xml` 등, 이전 노트 8장 참고)가 보이면 정상적으로 만들어진 것이다.

처음 열었을 때 파일 몇 개가 빨간색 오류로 표시될 수 있는데, VS Code가 아직 Maven 프로젝트를 인식하고 필요한 걸 내려받는 중이라 그렇다 — 조금 기다리면 오류가 사라진다.

## 2. 의존성 추가 — `pom.xml`

생성된 프로젝트 루트의 `pom.xml`을 열고 `<dependencies>` 블록에 임베디드 톰캣과 서블릿 라이브러리를 추가한다.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>maven_servlet_project</artifactId>
    <version>1.0-SNAPSHOT</version>

    <properties>
        <maven.compiler.source>21</maven.compiler.source>
        <maven.compiler.target>21</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <dependencies>
        <!-- 1. Jakarta Servlet API -->
        <dependency>
            <groupId>jakarta.servlet</groupId>
            <artifactId>jakarta.servlet-api</artifactId>
            <version>6.0.0</version>
            <scope>provided</scope>
        </dependency>

        <!-- 2. Embedded Tomcat Core -->
        <dependency>
            <groupId>org.apache.tomcat.embed</groupId>
            <artifactId>tomcat-embed-core</artifactId>
            <version>10.1.19</version>
        </dependency>

        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.11</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

</project>
```

`pom.xml`을 저장하면 VS Code 우측 하단에 라이브러리를 동기화할지 묻는 알림이 뜬다. **Always Allow** 또는 **Sync**를 클릭한다. 동기화되는 동안 한참 코드에 오류가 있는 것처럼 보일 수 있는데, 정상이다 — 이전 실습 [실습 1]에서 jar를 직접 찾아 `lib`에 넣던 걸, 이번엔 이 클릭 한 번으로 대신하는 셈이다.

## 3. 서블릿 및 서버 실행 클래스 작성

Maven의 표준 소스 경로인 `src/main/java/com/example/` 폴더 안에 자바 파일을 작성한다. 앞서 4장에서 다룬 "경로를 명시하지 않아도 관례로 정해진 구조"(이전 노트 8장)가 바로 이 위치다.

### `HelloServlet.java`

```java
package com.example;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;

public class HelloServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        resp.setContentType("text/html; charset=UTF-8");
        PrintWriter out = resp.getWriter();
        out.println("<html>");
        out.println("<body>");
        out.println("<h1>Hello, Maven & Servlet!</h1>");
        out.println("<p>메이븐(Maven)을 통한 서블릿 실행 성공!</p>");
        out.println("</body>");
        out.println("</html>");
    }
}
```

이전 실습의 `HelloServlet`과 내용은 거의 같지만, 이번엔 `package com.example;`이 붙는다 — Maven 프로젝트는 관례상 소스 코드가 도메인 기반 패키지 안에 있어야 하기 때문이다.

### `App.java` — 임베디드 톰캣 실행 클래스

Maven 프로젝트의 컴파일 결과물은 `target/classes` 폴더에 만들어진다. 아래 코드는 톰캣의 Context 경로(`docBase`)를 현재 디렉토리로 지정해서, 이 결과물을 바라보게 한다.

```java
package com.example;

import org.apache.catalina.Context;
import org.apache.catalina.startup.Tomcat;

import java.io.File;

public class App {

    public static void main(String[] args) throws Exception {
        // 1. 임베디드 톰캣 객체 생성
        Tomcat tomcat = new Tomcat();
        tomcat.setPort(8080);
        tomcat.getConnector();

        // 2. Context 설정
        String docBase = new File(".").getAbsolutePath();
        Context context = tomcat.addContext("", docBase);

        // 3. 순수 자바 코드로 서블릿 등록 및 URL 매핑 (애노테이션/스캔 필요 없음)
        String servletName = "helloServlet";

        // 서블릿 객체 생성 및 등록
        Tomcat.addServlet(context, servletName, new HelloServlet());

        // URL 경로 매핑 (/hello)
        context.addServletMappingDecoded("/hello", servletName);

        // 4. 서버 시작 및 대기
        tomcat.start();
        System.out.println("Server started on http://localhost:8080/hello");
        tomcat.getServer().await();
    }
}
```

`Tomcat.addServlet(...)`으로 서블릿 객체를 등록하고 `addServletMappingDecoded("/hello", ...)`로 URL을 매핑하는 흐름은 이전 실습 [실습 1]의 `ServerApp.java`와 완전히 같은 패턴이다 — 다만 이번엔 그 서블릿과 실행 클래스가 Maven이 관리하는 표준 구조 안에 놓여 있다는 점이 다르다.

## 4. 실행 및 결과 확인

1. VS Code에서 `App.java` 파일을 연다
2. `main` 메소드 위에 뜨는 Run 버튼을 클릭하거나 `Ctrl+F5`로 실행한다
3. 콘솔에 `Server started on http://localhost:8080/hello`가 출력되는지 확인한다
4. 브라우저에서 `http://localhost:8080/hello`로 접속해 결과를 확인한다

## 요약 포인트

- **`pom.xml`(Project Object Model)**: 수동으로 라이브러리를 관리하던 번거로운 작업을, 몇 줄의 선언만으로 자동화해주는 핵심 설정 파일이다
- **Maven 중앙 저장소(Maven Central Repository)**: 필요한 라이브러리를 이름과 버전만 명시하면, Maven이 전 세계 저장소에서 그 라이브러리와 딸린 의존성까지 자동으로 가져와 연결해준다(이전 노트 6~7장에서 다룬 `.m2` 로컬 저장소·전이 의존성이 바로 이 과정을 통해 채워진다)

이전 실습 [실습 1]과 이 실습을 나란히 놓고 보면, **같은 결과(임베디드 톰캣 + 서블릿 실행)를 얻는 데 필요한 수고가 완전히 다르다**는 게 이 실습의 핵심이다. jar를 하나하나 찾아 받고 클래스패스에 등록하던 과정이, Maven에서는 `pom.xml`에 몇 줄 선언하고 저장하는 것으로 끝난다.

