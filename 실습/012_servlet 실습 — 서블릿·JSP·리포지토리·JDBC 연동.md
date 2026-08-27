---
tags: [서블릿, JSP, JDBC, 리포지토리, 실습, MVC]
---

> 🔗 관련 노트: [[032_톰캣과 서블릿, 생명주기와 빌드 도구]] · [[034_웹 애플리케이션과 JSP]] · [[035_MVC 패턴과 모델2(서블릿·JSP 분리)]] · [[036_EL과 4가지 저장소]] · [[038_JDBC API와 리포지토리 분리]] · [[013_servlet 실습 — 메뉴 등록(Create) 기능과 퍼블리싱 연동]]

# servlet 실습 — 서블릿·JSP·리포지토리·JDBC 연동

`ncafe-servlet`(Maven 프로젝트, groupId `com.ncafe`)은 서블릿·JSP·리포지토리(JDBC)를 프레임워크 없이 클래스 단위로 직접 엮어본 실습 프로젝트다. Jakarta Servlet API 6.0, JSTL 3.0, PostgreSQL JDBC 드라이버, 내장 Tomcat 10.1.20을 쓴다.

## 1. 프로젝트 구조

```
ncafe-servlet/
├── pom.xml
└── src/main/
    ├── java/com/newlecture/
    │   ├── App.java                              # main() — 내장 톰캣 구동
    │   ├── controller/admin/menus/
    │   │   └── ListController.java                # @WebServlet("/admin/menus/list")
    │   ├── entity/
    │   │   └── Menu.java                           # 도메인 모델
    │   └── repository/
    │       └── MenuRepository.java                 # JDBC DAO
    └── webapp/WEB-INF/views/admin/menus/
        └── list.jsp                                # 뷰
```

- **`web.xml`이 존재하지 않는다.** 서블릿 등록은 `@WebServlet("/admin/menus/list")` 애노테이션만으로 이뤄진다. 리스너·필터도 없다.
- **별도의 `DBUtil`/커넥션 풀이 없다.** `MenuRepository`가 메서드마다 직접 `DriverManager.getConnection(...)`을 호출한다.
- 계층 구조는 `Servlet(Controller) → Repository(DAO, JDBC) → PostgreSQL → Entity → JSP` 로 단순하다. 서비스(비즈니스 로직) 계층은 따로 없다.

## 2. 부트스트랩 — `App.java` (내장 톰캣)

일반적인 WAR 배포 대신, `main()`에서 직접 톰캣을 띄우는 방식이다.

```java
public class App {
    public static void main(String[] args) throws Exception {
        int port = 8080;
        Tomcat tomcat = new Tomcat();
        tomcat.setPort(port);
        tomcat.getConnector();

        String docBase = new File("src/main/webapp").getAbsolutePath();
        Context context = tomcat.addWebapp("", docBase);

        // Maven/IDE 클래스로더를 Tomcat의 부모 클래스로더로 전달
        context.setParentClassLoader(App.class.getClassLoader());

        // target/classes 를 WEB-INF/classes로 바인딩
        File classesDir = new File("target/classes");
        StandardRoot resources = new StandardRoot(context);
        resources.addPreResources(new DirResourceSet(
                resources, "/WEB-INF/classes", classesDir.getAbsolutePath(), "/"));
        context.setResources(resources);

        tomcat.start();
        tomcat.getServer().await();
    }
}
```

- `tomcat.addWebapp("", docBase)`로 `src/main/webapp`을 컨텍스트 루트(`""`)에 마운트한다.
- 컴파일된 클래스는 `target/classes`에 있는데, 이 디렉터리를 `WEB-INF/classes`로 인식시켜야 톰캣이 `@WebServlet` 애노테이션이 붙은 클래스를 스캔할 수 있다 — `DirResourceSet`으로 바인딩하는 이유다.
- `web.xml` 없이도 서블릿이 동작하는 이유가 바로 이 애노테이션 스캔이다.

## 3. 전체 요청 흐름 — 메뉴 목록 조회 한 번을 끝까지 추적

```
브라우저 GET /admin/menus/list?price=5000  (파라미터 있음)
      또는 GET /admin/menus/list           (파라미터 없음)
    │
    ▼
ListController.doGet()             ← @WebServlet("/admin/menus/list")
    │  price 파라미터 파싱
    │  new MenuRepository()
    ▼
MenuRepository.findAll() / findAllByPrice(price)
    │  DriverManager.getConnection(...)
    │  PreparedStatement/Statement 실행
    ▼
PostgreSQL (테이블 menus)
    │  ResultSet
    ▼
mapRow(rs) → Menu 객체 리스트로 변환
    │
    ▼
req.setAttribute("list", list)
req.getRequestDispatcher(".../list.jsp").forward(req, resp)
    │
    ▼
list.jsp — <c:forEach var="menu" items="${list}"> 로 렌더링
    │
    ▼
브라우저에 HTML 응답 (주소창은 여전히 /admin/menus/list)
```

`forward()`는 서버 내부 이동이라 브라우저 주소창이 바뀌지 않고, 클라이언트는 `WEB-INF` 아래의 실제 JSP 경로를 알 수 없다 — `WEB-INF`에 뷰를 둔 이유(직접 접근 차단)와 정확히 맞물린다.

## 4. 서블릿 계층 — `ListController`

```java
@WebServlet("/admin/menus/list")
public class ListController extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        String _price = req.getParameter("price");

        Integer price = null;
        if (!_price.equals(""))
            price = Integer.parseInt(_price);

        MenuRepository repository = new MenuRepository();

        List<Menu> list;
        if (price != null) {
            list = repository.findAll();
        } else {
            list = repository.findAllByPrice(price);
        }
        req.setAttribute("list", list);
        RequestDispatcher dispatcher = req.getRequestDispatcher("/WEB-INF/views/admin/menus/list.jsp");
        dispatcher.forward(req, resp);
    }
}
```

**서블릿이 하는 일**: 요청 파라미터 파싱 → 리포지토리 호출 → 결과를 request 속성으로 저장 → JSP로 forward. 이 네 단계가 서블릿(컨트롤러) 계층의 전형적인 책임이다.

### 이 코드에 있는 버그 (실습이라 미완성 상태로 남아있음)

- **분기가 뒤바뀌어 있다.** `price != null`일 때 오히려 필터링 없는 `findAll()`을 부르고, `price == null`일 때 `findAllByPrice(price)`에 `null`을 넘긴다. `findAllByPrice`는 내부에서 `pst.setInt(1, price)`를 호출하므로, `Integer` `null`을 `int`로 오토언박싱하다 `NullPointerException`이 난다.
- **`price` 파라미터 자체가 없을 때도 터진다.** 쿼리스트링에 `price`가 아예 없으면 `req.getParameter("price")`는 `null`을 반환하는데, 곧바로 `_price.equals("")`를 호출해서 NPE가 난다. 빈 문자열(`""`)만 방어하고 `null`은 방어하지 못한 코드다.

이 두 버그는 실제 소스에 남아있는 "여러분이 마무리하세요"라는 주석과 함께 있는, 의도적으로 남겨둔 미완성 지점이다 — 리포지토리·컨트롤러 연동 원리를 이해했는지 확인하는 실습 포인트로 보면 된다.

## 5. 리포지토리(DAO) 계층 — `MenuRepository`

```java
public class MenuRepository {
    private static final String URL = "jdbc:postgresql://<host>:5432/<dbname>";
    private static final String UID = "<사용자명>";
    private static final String PWD = "<비밀번호>";
    private static final String DRIVER = "org.postgresql.Driver";

    static {
        try {
            Class.forName(DRIVER);
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }
    }
```

**정적 필드 + 정적 초기화 블록**: 접속 정보(URL/UID/PWD)를 클래스 상수로 고정해두고, `static { ... }` 블록에서 `Class.forName(DRIVER)`로 PostgreSQL 드라이버 클래스를 딱 한 번만 로딩·등록한다. 이 블록은 이 클래스가 처음 메모리에 올라갈 때(클래스 로딩 시점) 자동으로 실행되므로, `findAll()` 같은 메서드를 호출하기 전에 드라이버 등록이 이미 끝나 있음을 보장한다.

> ⚠️ 위 코드의 URL/사용자명/비밀번호는 실제 값을 `<host>`, `<사용자명>`, `<비밀번호>`로 치환했다. 실제 프로젝트에는 클라우드 PostgreSQL 접속 정보가 하드코딩되어 있다.

```java
    public List<Menu> findAll() {
        List<Menu> menus = new ArrayList<>();
        String sql = "SELECT id, kor_name, eng_name, img_src, description, price, category_id, create_time FROM menus ORDER BY id ASC";

        try (Connection conn = DriverManager.getConnection(URL, UID, PWD);
                Statement st = conn.createStatement();
                ResultSet rs = st.executeQuery(sql)) {

            while (rs.next()) {
                menus.add(mapRow(rs));
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return menus;
    }
```

**`findAll()`**: 전체 메뉴를 `id` 오름차순으로 가져온다. 값을 끼워 넣을 필요가 없는 고정된 SQL이라 가장 단순한 `Statement`를 쓴다. `try-with-resources` 괄호 안에 `Connection`·`Statement`·`ResultSet` 세 개를 한꺼번에 선언해서, 메서드가 끝나면(정상 종료든 예외든) 셋 다 역순으로 자동 close된다. `rs.next()`로 한 행씩 커서를 옮기며 `mapRow(rs)`로 변환한 `Menu`를 리스트에 담아 반환한다. 조회에 실패해도 예외를 던지지 않고 `catch`에서 스택트레이스만 찍은 뒤, 지금까지 담은(비어 있을 수도 있는) `menus`를 그대로 반환한다.

```java
    public List<Menu> findAllByPrice(Integer price) {
        List<Menu> menus = new ArrayList<>();
        String sql = "SELECT id, kor_name, eng_name, img_src, description, price, category_id, create_time FROM menus WHERE price = ?";

        try (Connection conn = DriverManager.getConnection(URL, UID, PWD);
                PreparedStatement pst = conn.prepareStatement(sql)) {

            pst.setInt(1, price);

            try (ResultSet rs = pst.executeQuery()) {
                while (rs.next()) {
                    menus.add(mapRow(rs));
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return menus;
    }
```

**`findAllByPrice(Integer price)`**: 특정 가격의 메뉴만 걸러서 가져온다. SQL에 `?` 자리표시자를 두고 `pst.setInt(1, price)`로 값을 바인딩하는 `PreparedStatement`를 쓴다는 점이 `findAll()`과 다르다 — 사용자 입력값(price)이 SQL 문자열에 직접 섞이지 않으므로 SQL 인젝션을 막을 수 있고, `int`로 캐스팅하지 않고 `?`에 값만 채워 넣으면 되니 문자열 이스케이프도 신경 쓸 필요가 없다. `ResultSet`은 `PreparedStatement`와 분리해서 안쪽에 별도의 `try-with-resources`로 열었는데, 실행할 때마다 새로 만들어지는 `ResultSet`을 `PreparedStatement`보다 좁은 범위에서 확실히 닫기 위한 구조다. 단, 이 메서드는 `price`가 `null`로 들어오면 `pst.setInt(1, price)`에서 오토언박싱하다가 `NullPointerException`이 난다(4절의 버그와 연결되는 지점).

```java
    private Menu mapRow(ResultSet rs) throws SQLException {
        return new Menu(
                rs.getInt("id"),
                rs.getString("kor_name"),
                rs.getString("eng_name"),
                rs.getString("img_src"),
                rs.getString("description"),
                rs.getInt("price"),
                rs.getInt("category_id"),
                rs.getTimestamp("create_time"));
    }
}
```

**`mapRow(ResultSet rs)`**: `ResultSet`의 커서가 가리키는 현재 행 한 줄을 `Menu` 객체 하나로 변환하는, 이 클래스 전용의 `private` 헬퍼 메서드다. 컬럼명을 문자열로 지정해 `rs.getInt("id")`, `rs.getString("kor_name")`처럼 타입에 맞는 getter로 값을 꺼내고, 이를 그대로 `Menu` 생성자에 순서대로 넘긴다. `findAll()`과 `findAllByPrice()` 모두 행을 순회하면서 이 메서드 하나를 공통으로 호출하므로, "DB 행 → 객체" 매핑 로직이 한 곳에만 존재하게 된다(컬럼이 추가·변경되면 이 메서드만 고치면 된다).

## 6. 엔티티(모델) — `Menu`

```java
public class Menu {
    private int id;
    private String korName;
    private String engName;
    private String imgSrc;
    private String description;
    private int price;
    private int categoryId;
    private Date createTime;

    // 3개의 생성자 오버로드(전체 필드 / id 없이 / createTime 없이)
    // 필드별 getter/setter
}
```

- 순수 POJO(getter/setter만 있는 데이터 객체)다. `MenuRepository.mapRow()`가 이 클래스의 생성자를 호출해 `ResultSet` 행 하나를 객체 하나로 만든다.
- 필드명이 카멜케이스(`korName`)인데 DB 컬럼명은 스네이크케이스(`kor_name`)다 — `mapRow()`에서 이 매핑을 수동으로 맞춰준다(ORM이 없으니 매핑도 사람이 직접 짠다).
- JSP에서 `${menu.korName}`처럼 EL로 접근하려면 `getKorName()` getter가 있어야 하는데, 정확히 그 규칙을 따르고 있다.

## 7. 뷰 계층 — `list.jsp`

```jsp
<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>

...
<section>
  <h3>메뉴목록</h3>
  <table>
    <tr>
      <td>ID</td><td>이미지</td><td>메뉴명</td>
      <td>카테고리</td><td>가격</td><td>등록일</td><td>수정</td>
    </tr>
    <c:forEach var="menu" items="${list}">
      <tr>
        <td><a href="/admin/menus/detail?id=${menu.id}">${menu.id}</a></td>
        <td>${menu.imgSrc}</td>
        <td>${menu.korName} ${menu.engName}</td>
        <td>${menu.categoryId}</td>
        <td>${menu.price}원</td>
        <td>${menu.createTime}</td>
        <td><button>수정</button><button>삭제</button></td>
      </tr>
    </c:forEach>
  </table>
</section>
```

- `<c:forEach var="menu" items="${list}">` — 서블릿이 `req.setAttribute("list", list)`로 넣어둔 request 스코프 속성을 JSTL이 그대로 읽어 반복한다.
- `${menu.id}`, `${menu.korName}` 같은 EL 표현식은 내부적으로 `menu.getId()`, `menu.getKorName()`을 호출한다 — [[036_EL과 4가지 저장소]]에서 정리한 "EL은 getter 규칙을 따라 자동 호출한다"는 원칙이 실제 코드에서 그대로 확인된다.
- `수정`/`삭제`/`상세` 링크(`/admin/menus/detail?id=...`)는 화면상 껍데기만 있고, 이를 받아줄 `DetailController`나 상세 페이지는 프로젝트에 아직 없다 — 목록 조회 한 기능만 끝까지 연동돼 있고, 나머지는 다음 실습에서 이어서 만들어야 할 자리로 남아있다.

## 8. 계층별 책임 정리

| 계층 | 클래스 | 책임 |
|---|---|---|
| 부트스트랩 | `App` | 내장 톰캣 구동, `webapp`/`target/classes` 마운트 |
| 컨트롤러(서블릿) | `ListController` | 요청 파라미터 처리, 리포지토리 호출, request 속성 세팅, JSP로 forward |
| 리포지토리(DAO) | `MenuRepository` | JDBC 연결, SQL 실행, `ResultSet` → 엔티티 매핑 |
| 엔티티 | `Menu` | DB 행 하나에 대응하는 데이터 객체 |
| 뷰 | `list.jsp` | request 속성을 JSTL/EL로 꺼내 HTML로 렌더링 |

프레임워크(Spring 등) 없이도 서블릿·JSP·JDBC만으로 요청 하나가 컨트롤러 → DAO → DB → 엔티티 → 뷰까지 어떻게 흘러가는지 그대로 손으로 확인할 수 있는 실습이다. 다만 예외 처리(`printStackTrace`로 삼켜버림), 커넥션 풀 부재, 컨트롤러의 분기 버그처럼 실무에서는 보완해야 할 지점들도 함께 남아있다.
