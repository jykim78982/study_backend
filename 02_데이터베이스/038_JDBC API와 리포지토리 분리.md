---
tags: [데이터베이스, JDBC, PostgreSQL, 리포지토리, 서블릿]
날짜: 2026-08-20
---

> 🔗 관련 노트: [[037_RDBMS와 SQL 기초]] · [[035_MVC 패턴과 모델2(서블릿·JSP 분리)]] · [[005_JDBC API 메서드 체이닝 뜯어보기]] · [[006_서블릿·HTTP API 메서드 체이닝 뜯어보기]] · [[039_예외 처리와 try-with-resources]]

# JDBC API와 리포지토리 분리

## 1. 우리는 DB를 "만드는 입장"이다

DB를 이용하는 두 가지 입장이 있다.

- **일반 사용자 입장**: 남이 만든 애플리케이션(SQL 클라이언트 도구 등)을 써서 SQL을 날린다. SQL을 몰라도 되고, 그냥 버튼을 누른다.
- **애플리케이션을 만드는 입장**: 우리가 실제로 해야 할 일은, SQL을 직접 만들어서 **DB를 이용한 UI(업무용 화면)를 만드는 것**이다. 사용자는 SQL을 모르니, 그걸 한 단계 더 가려서 업무적인 버튼과 화면으로 감싸줘야 한다.

## 2. JDBC API — DBMS가 달라져도 코드가 호환되게 하기위한 표준

오라클, MS SQL Server 같은 DBMS를 쓰려면 SQL을 실행할 편집기(API)가 필요하다. 각 DBMS는 자기만의 API(드라이버)를 제공하는데, 문제는 여기서 생긴다.

- 오라클을 쓰다가 가격이나 호환 문제로 MS SQL로 이주하려 하면, **기능은 같은데 사용 방법이 달라서 API를 전부 다시 고쳐야** 한다.
- SI 업체 입장에서는 A회사·B회사 프로젝트마다 DBMS가 다르면 코드가 제각각이라 불편하다 — "기능이 같은데 왜 이름을 안 맞추냐"는 불만이 나온다.

이 문제를 해결하기 위해 **JDBC(Java DataBase Connectivity)**라는 표준 인터페이스가 등장했다. 비유하면 **"돼지코" 콘센트**와 같다 — 콘센트 뒤에 어떤 방식이 있는지 몰라도, 돼지코 모양 하나만 맞으면 꽂아 쓸 수 있다.

- 우리는 **앞의 돼지코(JDBC 인터페이스)**만 쓰면 되고, 뒤에서 실제로 구동하는 코드(각 DBMS 드라이버)가 어떤 함수를 갖고 어떻게 동작하는지는 몰라도 된다. 오히려 알아봤자 좋을 게 없다.
- DB를 바꿔야 하면 **드라이버만 교체**하면 된다 — JDBC 자체(중간 인터페이스)는 실제 구동 코드가 아니라, 연결을 위한 **중간 거점**일 뿐이다.
- JDBC가 모방한 선례가 윈도우 제어판의 **ODBC**다 — DBMS를 통일된 방식으로 다루는 중간 인터페이스라는 개념 자체가 먼저 있었다.

**JDBC 자체는 별도 라이브러리 설치가 필요 없다.** 다만 JDBC 인터페이스만으로는 DB에 연결할 수 없다 — 실제로 쓰려는 DB의 **구동 코드(드라이버)**를 함께 가지고 있어야 한다. Maven을 쓰면 `pom.xml`에 드라이버 의존성만 추가하면 끝난다.

```xml
<!-- PostgreSQL JDBC Driver -->
<dependency>
  <groupId>org.postgresql</groupId>
  <artifactId>postgresql</artifactId>
  <version>42.7.4</version>
</dependency>
```

## 3. JDBC의 4단계 흐름

JDBC로 DB를 다룰 때 머릿속에 그려야 할 건 이 네 가지뿐이다.

| 단계 | 담당 | 역할 |
|---|---|---|
| 1. 드라이버 로드 | `DriverManager` | 문자열로 알려준 드라이버를 로드(사실상 `new`와 비슷)한다 |
| 2. 연결 생성 | `Connection` | 드라이버를 통해 실제 DB와 연결한다 |
| 3. 문장 실행 | `Statement` | 연결 객체로 SQL을 실행할 도구를 얻는다 |
| 4. 결과집합 사용 | `ResultSet` | 서버에 만들어진 결과를 한 줄씩 가져온다(fetch) |

- 최신 JDBC 드라이버부터는 `Class.forName(...)`으로 드라이버를 직접 로드할 필요가 없어졌다 — `DriverManager.getConnection(...)`을 호출하면 라이브러리가 알아서 등록된 드라이버를 찾아 로드한다.
- 연결 문자열 형식: `jdbc:postgresql://호스트:5432/DB이름` — 원격 연결이면 호스트가 달라지고, 필요하면 SSL 옵션이 붙는다.
- 결과집합(`ResultSet`)은 예전에는 "파일"이라고 불렀다 — 화면에 보일 모양 그대로, 중복도 허용해서 담아두는 구조이기 때문이다. 그 흔적으로 제일 앞을 **BOF**, 더 읽을 데이터가 없는 지점을 **EOF**라고 부른다.
- 클라이언트는 레코드(행)를 한 번에 하나씩만 가져올 수 있다. 서버는 클라이언트가 몇 번째까지 가져갔는지 **커서**로 기억한다. 커서의 기본 위치는 맨 앞이다.
- `rs.next()`를 호출하면 커서가 한 칸 내려가면서 그 행을 가져온다(fetch). 컬럼을 꺼낼 때는 `rs.getString("kor_name")`처럼 **DB의 컬럼명을 그대로** 써서 지정한다.

## 4. 실전 코드 — `JdbcMenuRepository`

`maven_servlet_project`의 `com.example.repository.JdbcMenuRepository`가 실제로 이 4단계를 그대로 구현한다.

```java
package com.example.repository;

import java.sql.Statement;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

import com.example.entity.Menu;

public class JdbcMenuRepository {
    public List<Menu> findAll() {
        List<Menu> menus = new ArrayList<>();

        String URL = "jdbc:postgresql://<host>:5432/<dbname>";
        try {
            Connection conn = DriverManager.getConnection(URL, "<user>", "<password>");
            System.out.println(conn.isClosed());

            String sql = "SELECT id, kor_name, eng_name, price FROM menus";

            Statement st = conn.createStatement();
            ResultSet rs = st.executeQuery(sql);

            rs.next();
            String korName = rs.getString("kor_name");
            System.out.println(korName);

            conn.close();
            System.out.println(conn.isClosed());
        } catch (SQLException e) {
            e.printStackTrace();
        }

        return menus;
    }
}
```

- 연결 문자열(호스트/DB명/계정/비밀번호)은 코드에 그대로 박아두지 않는 게 정석이다 — 여기서는 자리표시자로 대체했다.
- **아직 미완성 지점**: 지금 이 코드는 `rs.next()`로 한 행만 꺼내 `System.out.println`으로 출력만 하고, `menus` 리스트에는 아무것도 담지 않는다. 실제로 완성하려면 `while (rs.next())`로 반복하면서 매 행마다 `Menu` 객체를 만들어 `menus.add(menu)`로 채워 넣어야 한다 — CSV를 파싱하던 옛 로직과 흐름은 같고, 데이터를 어디서 읽어오는지만 다르다.

## 5. 통짜 코드의 문제 — 입출력과 데이터 소스가 뒤섞여 있으면 안 된다

서블릿의 `doGet(request, response)`는 원래 **사용자와의 입출력을 위한 자리**다. 그런데 예전 코드는 그 자리에 CSV를 읽는 코드까지 같이 들어 있었다 — 기능적으로 같이 있을 필요가 없는 것들이 한곳에 뭉쳐 있는 **통짜 코드**다.

여기서 데이터 소스가 "CSV 파일"에서 "DB"로 바뀌는 상황을 생각해보자. **이때 달라지는 건 입출력이 아니라 데이터 소스다.** 입출력을 담당하는 서블릿 입장에서는, 데이터를 어디서 가져오는지에 대해 관심을 끊는 것이 바람직하다 — **데이터 소스를 관리하는 역할자를 따로 두어야 한다.**

## 6. 리포지토리로 역할 분리하기

목록을 가져오는 코드가 서블릿 파일에 같이 있을 필요가 없다. 데이터 접근만 전담하는 클래스, 즉 **리포지토리(Repository)**를 따로 둔다. 예전에는 이 역할을 **DAO**라고 불렀다.

`maven_servlet_project`에는 같은 `Menu`를 다루는 리포지토리가 데이터 소스별로 나뉘어 있다.

- **`FileMenuRepository`**: CSV 파일에서 `Menu` 목록을 읽어오는 역할.
- **`JdbcMenuRepository`**: DB(JDBC)에서 `Menu` 목록을 읽어오는 역할.

둘 다 `findAll()`이라는 같은 이름의 메서드로 `List<Menu>`를 반환한다 — **엔티티마다 그 데이터를 관리하는 리포지토리를 따로 둔다**는 원칙이다(엔티티·테이블·구조체·레코드는 결국 같은 단위를 가리킨다).

컨트롤러(`ListServlet`)는 이제 데이터를 직접 읽는 대신, 리포지토리에게 요청만 한다.

```java
@Override
protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
    JdbcMenuRepository repository = new JdbcMenuRepository();

    List<Menu> menus = repository.findAll();

    req.setAttribute("menus", menus);
    req.getRequestDispatcher("/WEB-INF/views/admin/menus/list.jsp").forward(req, resp);
}
```

사용자와 상호작용하는 쪽(서블릿)은 "뭘로 찾아줘, 찾아서 다 줘, 저장해줘, 수정해줘"처럼 **요청을 리포지토리에 넘기고, 받은 결과로 화면을 그리는 일**만 한다. 이렇게 역할을 나누는 눈이 있어야 코드의 구조(아키텍처)가 만들어지고, 그래야 큰 프로젝트도 감당할 수 있다.

### 경로(path)는 누구의 책임인가

`FileMenuRepository`가 CSV를 읽으려면 파일 경로가 필요하다. 이 경로를 **서블릿에서 얻어서 리포지토리에 전달할지**, **리포지토리가 직접 얻을지**를 정해야 한다.

- 책임을 나눌 때는 극도로 "개인주의적"으로 봐야 한다 — **서블릿(HTTP 요청·응답)을 다루는 것은 리포지토리의 역할이 아니다.**
- 그래서 경로는 서블릿 쪽에서 얻어 리포지토리에 넘겨주는 방식(생성자 또는 setter)을 쓴다. 경로가 특정 리포지토리 하나에만 필요한 것인지, 다른 곳에서도 필요한 것인지도 함께 고려해야 한다.

## 7. 리소스의 실제 경로를 구하는 법

`data/menus.csv`를 읽으려면 **절대경로**가 필요하다. 하지만 `menus.csv`의 위치는 프로젝트를 옮겨 다니면 달라질 수 있어서, 코드에 고정된 절대경로를 박아둘 수 없다 — 그래서 **실행 중에 동적으로 경로를 알아내야** 한다.

이때 필요한 것이 `ClassLoader`다. 스트림을 바로 얻는 대신, **리소스가 있는 위치의 절대경로 자체**를 얻어서 리포지토리에 넘겨줄 수도 있다.

```java
String path = req.getServletContext().getClassLoader()
        .getResource("data/menus.csv").getPath();

FileMenuRepository repository = new FileMenuRepository(path);
```

이 한 줄은 왼쪽에서 오른쪽으로 이어지는 **메서드 체이닝**이다. 각 단계가 반환하는 객체를 따라가며 순서대로 읽으면 된다.

- **`req`**: 서블릿의 `doGet(req, resp)`로 들어온 `HttpServletRequest` 객체. 지금 처리 중인 HTTP 요청 그 자체다.
- **`.getServletContext()`**: `req`에서 **이 웹 애플리케이션 전체를 대표하는 객체(`ServletContext`)**를 꺼낸다. 서블릿 하나가 아니라 애플리케이션 전체에 걸쳐 공유되는 정보(설정, 리소스 등)에 접근할 때 쓴다.
- **`.getClassLoader()`**: `ServletContext`에서 **이 애플리케이션의 클래스를 로드한 `ClassLoader` 객체**를 꺼낸다. 지금 실행 중인 클래스·리소스가 실제로 어디에 배치되어 있는지 알고 있는 객체다.
- **`.getResource("data/menus.csv")`**: `ClassLoader`에게 "`data/menus.csv`라는 리소스가 실제로 어디 있는지 알려줘"라고 요청한다. 반환값은 그 위치를 가리키는 **`URL` 객체**다.
- **`.getPath()`**: 그 `URL` 객체에서 **파일시스템 경로 문자열**만 뽑아낸다. 이 문자열이 곧 `FileMenuRepository`에 넘겨줄 절대경로다.

이렇게 얻은 `path` 문자열은 그다음 줄 `new FileMenuRepository(path)`로 넘어간다.

- `FileMenuRepository`는 문자열 하나를 받는 생성자를 갖고 있다 — `public FileMenuRepository(String path) { this.path = path; }`.
- 이 생성자는 넘겨받은 `path` 값을 그대로 **인스턴스 필드(`this.path`)에 저장**만 할 뿐, 이 시점에는 파일을 열거나 읽지 않는다.
- 실제로 이 경로가 쓰이는 건 나중에 `findAll()`이 호출될 때다 — 그 안에서 `this.path`를 이용해 `new FileInputStream(path)`처럼 파일을 열어 CSV를 읽는다.
- 즉 이 줄이 하는 일은 "**나중에 파일을 열 때 쓸 경로를, 객체를 만드는 시점에 미리 넣어둔다**"는 것이다 — 실제 파일 접근은 생성자가 아니라 `findAll()` 호출 시점으로 미뤄져 있다.

경로를 다룰 때 기억해둘 배포 구조가 있다. Maven 프로젝트는 `src/main/java`와 `src/main/resources` 두 위치를 구분해서 쓰는데, 배포되면 **둘 다 톰캣의 `WEB-INF/classes` 디렉토리 안에 같이 들어간다.**

- `src/main/java`의 소스는 컴파일되어 `target/classes`를 거쳐 `WEB-INF/classes`로 배포된다.
- `src/main/resources`(CSV 같은 리소스 파일)도 컴파일 없이 그대로 `WEB-INF/classes`로 함께 복사된다.
- 톰캣은 실행 시 이 `classes` 디렉토리 안의 내용을 읽는다 — 그래서 `ClassLoader`로 "지금 실행 중인 클래스가 있는 위치"를 기준으로 리소스의 실제 경로를 알아낼 수 있는 것이다.
