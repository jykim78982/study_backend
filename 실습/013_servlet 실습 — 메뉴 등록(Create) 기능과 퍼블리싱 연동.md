---
tags: [서블릿, JSP, JDBC, 리포지토리, 실습, HTML, 폼, PRG패턴]
---

> 🔗 관련 노트: [[012_servlet 실습 — 서블릿·JSP·리포지토리·JDBC 연동]] · [[042_웹 퍼블리싱과 시맨틱 마크업(HTML)]] · [[044_HTML 폼 요소 다루기]]

# servlet 실습 — 메뉴 등록(Create) 기능과 퍼블리싱 연동

`publishing` 프로젝트(정적 HTML 퍼블리싱 실습)에서 만든 관리자 화면들이 `ncafe-servlet` 프로젝트로 옮겨가면서 실제 서블릿·JDBC와 어떻게 연동되는지, 목록(List)에 이어 등록(Create) 기능을 통해 확인한다.

## 1. 두 프로젝트의 관계

- `C:\Workspace\Workspace2\publishing\`: 서버 로직 없이 순수 HTML/CSS로 화면을 먼저 만들어보는 퍼블리싱 실습 프로젝트다. `admin/menus/` 아래 `list.html`·`create.html`·`detail.html`·`edit.html`이 있다.
- `C:\Workspace\Workspace2\ncafe-servlet\`: 이 중 일부 화면을 실제 서블릿·JSP·JDBC로 연동한 프로젝트다. 현재는 **목록(list)**과 **등록(create)** 두 기능만 서버까지 완전히 연동돼 있고, 상세(detail)·수정(edit)은 퍼블리싱 쪽에만 존재하며 서블릿 프로젝트로는 아직 옮겨지지 않았다.
- 퍼블리싱 HTML을 JSP로 옮길 때 공통으로 벌어지는 일: 정적 페이지에는 없던 `action` 속성이 실제 서블릿 경로로 채워지고, 순수 UI였던 버튼이 진짜 폼 전송 버튼이 된다.

## 2. 퍼블리싱 원본 — `admin/menus/create.html`

서버 연동 전 정적 폼의 모습이다.

```html
<form id="form-for-menu" method="post">
  <input type="file">
  <input type="text" placeholder="예:카페라떼" autofocus
    name="kor-name" autocomplete="off" required>
  <!-- datalist 실습 예시는 주석 처리되어 있음 -->
  <input type="text" placeholder="예:Cafe Latte"
    name="eng-name" required>
  <input type="text" name="price" required>
  <select name="category-id">
    <option value="">카테고리 선택</option>
    <option value="1">커피</option>
    ...
  </select>
  <textarea rows="10" cols="50" name="description"
    placeholder="특징이나 재료등 설명을 적어 주세요">
  </textarea>
  <button>전송</button>
</form>
```

- **`action` 속성이 없다.** [[044_HTML 폼 요소 다루기]] 11절에서 정리했듯, `action`을 생략하면 현재 페이지 URL로 그대로 제출된다 — 아직 받아줄 서블릿이 없는 퍼블리싱 단계이므로 당연한 상태다.
- 이미지 입력은 `type="file"`로, 실제 파일 업로드를 염두에 둔 형태였다.
- `<button>`에 `type`이 없다(기본값은 `submit`이라 동작은 하지만 명시적이지 않다).

## 3. 서블릿 연동 후 — `create.jsp`에서 달라진 점

| 항목 | 퍼블리싱 원본(`create.html`) | 서블릿 연동(`create.jsp`) |
|---|---|---|
| `action` | 없음 | `/admin/menus/create` |
| 이미지 입력 | `<input type="file">` | `<input type="text" name="img-src">` (파일 업로드 미구현, 경로 문자열만 받음) |
| 가격 입력 | `required` 있음 | `required` 없음 |
| datalist 예시 | 주석으로 존재 | 제거됨 |
| 시맨틱 구조(`header`/`aside`/`nav`×3/`main`/`section`/`footer`) | 동일 | 동일 |

- `action="/admin/menus/create"`가 `CreateController`의 `@WebServlet` 경로와 정확히 일치한다.
- 가격 필드에서 `required`가 빠진 점은 실무에서 흔히 생기는 "화면(HTML)과 서버(Controller) 검증 규칙이 미묘하게 어긋나는" 사례다 — 브라우저 단에서는 빈 값이 통과될 수 있는데, `CreateController`는 `price`가 비어 있으면 `0`으로 채워서 저장해버린다(4절 참고).

## 4. `CreateController` — GET(폼 표시)·POST(저장) 전체 흐름

```java
@WebServlet("/admin/menus/create")
public class CreateController extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest req,
            HttpServletResponse resp) throws ServletException, IOException {
        RequestDispatcher dispatcher = req.getRequestDispatcher(
                "/WEB-INF/views/admin/menus/create.jsp");
        dispatcher.forward(req, resp);
    }

    @Override
    protected void doPost(HttpServletRequest req,
            HttpServletResponse resp) throws ServletException, IOException {
        req.setCharacterEncoding("UTF-8");

        String korName = req.getParameter("kor-name");
        String engName = req.getParameter("eng-name");
        String imgSrc = req.getParameter("img-src");
        String description = req.getParameter("description");

        String priceStr = req.getParameter("price");
        Integer price = (priceStr != null && !priceStr.isBlank())
                ? Integer.parseInt(priceStr) : 0;

        String categoryIdStr = req.getParameter("category-id");
        Integer categoryId = (categoryIdStr != null && !categoryIdStr.isBlank())
                ? Integer.parseInt(categoryIdStr) : null;

        Menu menu = new Menu(korName, engName, imgSrc, description, price, categoryId);

        JdbcMenuRepository repository = new JdbcMenuRepository();
        repository.save(menu);

        resp.sendRedirect("/admin/menus/list");
    }
}
```

- **`doGet`은 단순 forward만 한다.** [[012_servlet 실습 — 서블릿·JSP·리포지토리·JDBC 연동]]의 `ListController`와 달리 파라미터 처리나 조회 없이, 등록 폼(JSP)을 그대로 보여주기만 하면 되기 때문이다.
- **`doPost`가 실제 처리를 담당한다.** 이 한 서블릿이 "폼을 보여준다(GET)"와 "폼을 처리한다(POST)"를 모두 맡고 있어서 [[044_HTML 폼 요소 다루기]] 11절에서 설명한 "폼을 보여주는 페이지와 처리하는 서버 로직이 같은 경로를 공유하는 구조"의 실제 예시가 된다 — GET과 POST가 같은 URL(`/admin/menus/create`)을 메서드로만 구분해 나눠 쓴다.
- `price`가 빈 문자열이거나 없으면 `0`으로, `category-id`가 비어 있으면 `null`로 처리한다 — 두 필드의 "빈 값" 처리 방식이 서로 다르다(하나는 기본값 대체, 하나는 `null` 허용).

## 5. `JdbcMenuRepository.save()` — INSERT

```java
public int save(Menu menu) {
    String sql = "INSERT INTO menus (kor_name, eng_name, img_src, "
               + "description, price, category_id) VALUES (?, ?, ?, ?, ?, ?)";
    int result = 0;

    try (Connection conn = DriverManager.getConnection(URL, UID, PWD);
         PreparedStatement pst = conn.prepareStatement(sql)) {

        pst.setString(1, menu.getKorName());
        pst.setString(2, menu.getEngName());
        pst.setString(3, menu.getImgSrc());
        pst.setString(4, menu.getDescription());
        pst.setInt(5, menu.getPrice());

        if (menu.getCategoryId() != null) {
            pst.setInt(6, menu.getCategoryId());
        } else {
            pst.setNull(6, java.sql.Types.INTEGER);
        }

        result = pst.executeUpdate();
    } catch (SQLException e) {
        e.printStackTrace();
    }

    return result;
}
```

> ⚠️ 실제 소스에는 `URL`/`UID`/`PWD`에 실제 접속 정보가 하드코딩되어 있다. 여기서는 값을 적지 않는다 — [[012_servlet 실습 — 서블릿·JSP·리포지토리·JDBC 연동]]과 같은 이유로 실제 DB 접속 정보를 노트에 남기지 않는다.

- `findAll()`·`findAllByPrice()`는 `SELECT`라 `executeQuery()`를 쓰지만, `save()`는 `INSERT`라 **영향받은 행 수(int)**를 돌려주는 `executeUpdate()`를 쓴다.
- `menu.getCategoryId()`가 `null`이면 `pst.setInt(6, ...)` 대신 `pst.setNull(6, java.sql.Types.INTEGER)`를 호출한다 — `int`(기본형)는 애초에 `null`을 담을 수 없으므로, `Integer`(래퍼 타입)로 값을 받아 `null` 여부를 먼저 검사한 뒤 SQL에 반영하는 패턴이다.
- `CreateController`는 `save()`가 반환하는 `int`(영향받은 행 수)를 받아서 버리고 있다 — 저장이 실제로 성공했는지 확인하지 않은 채 바로 리다이렉트한다.

## 6. 저장 후 리다이렉트 — PRG 패턴

```java
resp.sendRedirect("/admin/menus/list");
```

- `save()` 호출이 끝나자마자 `sendRedirect()`로 목록 페이지 URL을 응답한다 — 브라우저는 이 응답을 받고 `/admin/menus/list`로 **다시 GET 요청**을 보낸다.
- 이게 바로 **POST-Redirect-GET(PRG) 패턴**이다: 등록 처리(POST)를 곧바로 화면으로 forward하지 않고, 일단 목록 페이지로 리다이렉트(302)시킨 뒤 그 목록 페이지를 GET으로 새로 받아오게 만든다.
- 이렇게 하는 이유는 사용자가 등록 완료 화면에서 새로고침(F5)을 눌러도 POST 요청이 중복 전송되지 않게 하기 위해서다 — forward로 처리했다면 주소창은 여전히 `/admin/menus/create`인 채로 결과만 보여주게 되어, 새로고침 시 등록이 한 번 더 일어날 위험이 있다.
- 이 흐름이 바로 "http 302는 리다이렉션이 정상 작동했다는 뜻"이라는 앞선 질문의 실제 코드 사례다 — `sendRedirect()`가 호출되면 서버는 302 응답과 `Location: /admin/menus/list` 헤더를 내려보내고, 브라우저가 그 헤더를 보고 알아서 다시 요청한다.

## 7. `MenuRepository` → `JdbcMenuRepository`, 필드 타입 변경

[[012_servlet 실습 — 서블릿·JSP·리포지토리·JDBC 연동]]을 작성한 시점 이후 프로젝트가 바뀌었다.

- 리포지토리 클래스 이름이 `MenuRepository`에서 **`JdbcMenuRepository`**로 바뀌었다. JDBC로 구현된 리포지토리임을 클래스 이름에 명시한 것으로 보인다.
- `Menu` 엔티티의 모든 필드가 기본형(`int`)에서 **래퍼 타입(`Integer`)**으로 바뀌었다(`id`, `price`, `categoryId` 등). `save()`에서 `categoryId`가 `null`일 수 있는 상황을 다뤄야 하다 보니, `null`을 표현할 수 없는 기본형 대신 래퍼 타입으로 전체를 통일한 것으로 보인다.
- 생성자도 3개(전체 필드 / `id` 없이 / `createTime` 없이)에서 **기본 생성자 포함 4개**로 늘었다.
- `findById(int id)` 메서드도 새로 추가되어 있다(상세 페이지용으로 준비된 것으로 보이나, 이를 호출하는 `DetailController`는 아직 없다).

## 8. HTML5 폼 검증 실습 — `publishing/form/step1.html` ~ `step6.html`

`ncafe-servlet`과 별개로, `publishing` 프로젝트에는 브라우저 자체 검증(자바스크립트 없이)을 실습하는 폼 6종이 있다. [[044_HTML 폼 요소 다루기]] 8절(`required`)의 연장선에 있는 내용이다.

| 단계 | 다루는 속성 | 예시 |
|---|---|---|
| step1 | 텍스트 `required`, select `required`(첫 옵션 `value=""` 필수), 단일 checkbox `required` | `<input type="checkbox" value="yes" required>` |
| step2 | `minlength`/`maxlength` | `<input minlength="4" maxlength="12">`, `<textarea minlength="10" maxlength="200">` |
| step3 | `type="number"` + `min`/`max`/`step`, `type="date"` + `min`/`max` | `<input type="number" min="0" max="100" step="5">` |
| step4 | `type="email"`(단일/`multiple`), `type="url"` | `<input type="email" multiple>`, `<input type="url" placeholder="https://...">` |
| step5 | `type="tel"` + `pattern`, `type="password"` + `pattern` (+ `title`로 안내문구) | `<input type="tel" pattern="010-\d{4}-\d{4}" title="...">` |
| step6 | `novalidate` — 브라우저 검증을 끄고 백엔드 검증만 테스트 | `<form novalidate>` |

- **select의 `required` 우회 함정**: step1 주석에 있는 설명처럼, 첫 번째 `<option>`의 `value`를 생략하면(`<option>-- 스택을 선택하세요 --</option>`) 그 텍스트 자체가 `value`로 채워져 버려서, 아무것도 고르지 않은 상태로도 "값이 있는 것"처럼 통과된다. 반드시 `value=""`를 명시해야 `required`가 의도대로 동작한다.
- **`type="number"`에 소수점을 쓰려면 `step`을 명시해야 한다** — `step`을 생략하면 기본값 `1`(정수 단위)이 적용되어, `step="0.01"`처럼 소수 단위를 명시하지 않으면 소수 입력 자체가 막힌다.
- **`pattern`은 반드시 `title`과 짝지어 쓰는 게 좋다** — `pattern`만 있으면 형식이 안 맞을 때 브라우저 기본 오류 문구만 뜨지만, `title`을 넣으면 그 문구가 안내 메시지로 그대로 노출된다.
- **`novalidate`는 폼 전체의 브라우저 검증을 끈다** — 서버 쪽 검증 로직을 테스트하고 싶을 때, 일부러 유효하지 않은 값을 보내보는 용도로 쓴다. `required`가 걸려 있어도 `novalidate`가 있으면 브라우저가 막지 않는다.

## 9. 요청 흐름 정리 — 등록 한 번을 끝까지 추적

```
브라우저 GET /admin/menus/create
    │
    ▼
CreateController.doGet() → forward → create.jsp (등록 폼 렌더링)
    │
    │  사용자가 폼 작성 후 전송
    ▼
브라우저 POST /admin/menus/create  (body에 kor-name, eng-name, ...)
    │
    ▼
CreateController.doPost()
    │  파라미터 파싱 → Menu 객체 생성
    ▼
JdbcMenuRepository.save(menu)  → INSERT INTO menus (...)
    │
    ▼
resp.sendRedirect("/admin/menus/list")   ← 302 Found, Location 헤더
    │
    ▼
브라우저 GET /admin/menus/list  (자동 재요청)
    │
    ▼
ListController.doGet() → forward → list.jsp (갱신된 목록 렌더링)
```

목록(List)은 조회 후 바로 forward, 등록(Create)은 저장 후 리다이렉트(PRG) — 같은 계층 구조(Controller → Repository → DB)를 쓰면서도 "결과를 어떻게 화면에 반영하는가"가 GET성 요청이냐 POST(생성) 요청이냐에 따라 다르게 설계된 걸 확인할 수 있다.
