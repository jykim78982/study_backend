---
tags: [MVC, 모델2, 서블릿, JSP, 포워딩]
---

> 🔗 관련 노트: [[034_웹 애플리케이션과 JSP]] · [[033_어노테이션 기반 매핑과 RTTI(리플렉션)]] · [[009_JSP 스크립틀릿과 CSV 데이터 조회]] · [[038_JDBC API와 리포지토리 분리]] · [[006_서블릿·HTTP API 메서드 체이닝 뜯어보기]] · [[007_컬렉션·제네릭 API 메서드 체이닝 뜯어보기]] · [[012_servlet 실습 — 서블릿·JSP·리포지토리·JDBC 연동]]

# MVC 패턴과 모델2(서블릿·JSP 분리)

> ⚠️ 여기서 다루는 MVC는 **서버 단(JSP/서블릿, 스프링)에서 쓰는 MVC**다. 프론트엔드(Angular, Vue, React 등)에서도 MVC라는 이름을 쓰지만, 그건 또 다른 맥락이다 — 이름만 같을 뿐 완전히 같은 개념은 아니다.

## 1. MVC는 원래 어디서 나온 개념인가

MVC는 원래 **윈도우(데스크탑) 프로그램**을 만들기 위해 나온 개념이다. 윈도우 형태의 GUI 프로그램은 MS가 OS로 만들기 훨씬 전부터 이미 있었고, MVC는 그 세계에서 나온 방법론이다.

지금 서버 개발에서 말하는 MVC는 **그 개념을 웹에 맞게 변형해서 이름만 따온 것**이다. 웹은 윈도우 프로그램 형태가 아니기 때문에, 원조 MVC와 완전히 똑같지는 않다. 다만 **철학은 같다** — 바로 **"모델(Model)"의 필요성**이다.

서버 쪽에서 쓰이는 이 MVC는 **단방향 MVC**라고도 부른다.

## 2. 왜 MVC가 필요한가 — 스파게티 코드 문제

이전에 만든 `detail.jsp`를 보면, 자바 코드(`<% %>`)와 HTML 코드가 한 파일 안에 섞여 있다. 이질적인 두 종류의 코드가 뒤섞인 상태를 **스파게티 코드**라고 부른다 — 한 번 꼬이면 손대기 어려운 코드라는 뜻이다.

- 꼬이는 이유: 코드가 뒤섞여 있어서 **찾기도, 해석하기도** 어렵다
- 지금은 코드 블록이 몇 개 안 되지만, 실제 업무용 화면을 만들면 코드 블록이 수백 개까지 늘어날 수 있다
- 그렇다면 **두 종류의 코드를 각각 따로 나누어둘 수는 없을까?** — 그러면 훨씬 깔끔해질 것이다

### 예시1 vs 예시2

**예시1 — 제어(로직)와 출력이 뒤섞인 코드**

```jsp
<div>
    <p>한글명: <%= menu.getKorName().trim() %></p>
    <p>가격: <%= (menu.getPrice() >= 5000 ? "프리미엄" : "일반") %>
        - <%= menu.getPrice() %>원</p>
    <p>상태: <%= menu.getPrice() > 0 ? "판매중" : "품절" %></p>
</div>
```

각 출력 라인마다 `.trim()`, 가격 비교 같은 **판단·가공 로직이 그 자리에서 바로 실행**된다. 코드 줄 수는 적지만, 화면을 읽는 사람이 HTML 구조와 자바 로직을 동시에 해석해야 한다.

**예시2 — 제어를 위로 끌어올리고, 출력은 변수만 꽂아 넣는 코드**

```jsp
<%
    // 제어부: 출력 전에 필요한 값을 전부 미리 계산해둔다
    String korName = menu.getKorName().trim();
    String priceLabel = (menu.getPrice() >= 5000) ? "프리미엄" : "일반";
    String statusLabel = (menu.getPrice() > 0) ? "판매중" : "품절";
    int price = menu.getPrice();
%>
<div>
    <p>한글명: <%= korName %></p>
    <p>가격: <%= priceLabel %> - <%= price %>원</p>
    <p>상태: <%= statusLabel %></p>
</div>
```

변수(`korName`, `priceLabel`, `statusLabel`)가 늘어나서 코드 줄 수는 더 많아졌다. 하지만 아래쪽 출력부에는 더 이상 판단 로직이 없다 — **그냥 이미 계산된 값을 꽂아 넣기만** 한다. HTML 구조를 읽는 사람은 로직을 몰라도 되고, 로직을 고치는 사람은 위쪽 블록만 보면 된다.

### "코드량이 적으니 예시1이 낫지 않나요?"라는 질문

자바 코드를 HTML 여기저기 흩어 쓰는 방식(예시1)과, 자바 코드를 한곳에 몰아넣고 출력 부분만 최소화하는 방식(예시2)을 비교하면, "예시1이 메모리도 적게 들고 코드량도 적지 않나?"라는 생각이 들 수 있다.

**이건 근시안적인 판단이다.** 가장 중요한 기준은 성능이 아니라 **코드 해석의 용이함·편리함**이다. 코드는 짧다고 좋은 게 아니라, **읽었을 때 이해하기 쉽고 난도가 낮아야** 좋은 코드다. 코드량이 조금 늘고 변수가 더 생기더라도, 그 대가로 **자바 코드를 한곳에 몰아둘 수 있다면** 그게 더 나은 구조다.

## 3. Model이라는 발상 — 제어는 위로, 출력은 아래로

방향을 이렇게 잡는다.

- **출력을 위한 제어(로직)는 위쪽으로 끌어올린다**
- 위쪽에서는 **출력할 데이터를 준비**하기만 한다
- 아래쪽(문서, 화면)에서는 그 **데이터를 꽂아 넣어서 출력만** 한다

이렇게 하면 코드가 물과 기름처럼 자연스럽게 나뉜다. 출력하는 쪽에서는 **model이라 불리는, 화면에 출력될 최소한의 데이터**만 있으면 된다.

이전에는 "문서를 제어"했다면, 이제는 **"출력할 데이터를 준비하고, 그 데이터를 제어"**하는 쪽으로 무게중심이 옮겨간다. 위에서는 로직을 제어해서 모델(데이터)을 만들고, 아래에서는 그 모델을 꽂아 넣기만 하는 방법론 — 이게 MVC의 골자다.

### Q. MVC는 객체지향인가?

**아니다.** MVC는 **UI(사용자 화면)를 만들 때 쓰는 방법론**이다. 사용자 화면을 만들지 않는 상황이라면 MVC를 쓸 이유가 없다. 사용자 화면을 직접 제어하지 않고, 제어(Controller)는 화면(View)에 데이터(Model)만 넘겨주도록 하는 것 — **"모델을 사용하는 방법"**이라고도 할 수 있다.

MVC와 그 변형들이 여러 이름으로 존재하지만 골자는 다 똑같다 — **"문서를 출력하는 부분에서 로직(제어)을 쓰지 말자."**

- **Model**: 중심에 있는 데이터
- **View**: 그 모델을 이용(출력)하는 쪽
- **Controller**: 모델을 만드는 쪽으로 로직을 몰아둔 것

> MVC란? **화면을 구현할 때, 화면 제어(로직)를 화면 자체로부터 분리**함으로써 데이터(Model)를 중심으로 View와 Controller의 역할을 나누는 설계 방법론이다.

## 4. 지금 우리 코드는 MVC일까?

예시2처럼 제어부와 출력부를 나누어봤자, 지금은 **그 둘이 여전히 하나의 JSP 파일 안에 함께 들어있는 상황**이다. 지금의 `detail.jsp`를 다시 보면, 파일 위쪽에는 제어(로직) 블록이, 아래쪽에는 그 값을 꽂아 넣는 출력 블록이 나뉘어 있지만, 둘 다 **같은 파일 하나를 열어야만** 확인할 수 있다. 반복문·조건문처럼 **동적으로 달라져야 하는 부분에 코드가 남는 건 어쩔 수 없다** — 이런 부분은 예외로 남겨둔다. 그걸 제외한 코드는 전부 위쪽 한곳에 몰아둔다.

그래도 화면(view) 안에 자바 코드가 남아 있다는 게 찜찜하다. 이 껍데기(HTML)에 자바 코드가 **최대한 안 들어가게** 만드는 방법이 바로 아래에서 다룰 **모델2** 구조다.

## 5. 모델1 vs 모델2

- **모델1**: JSP 하나 안에 View와 Controller가 한 몸으로 섞여 있는 구조. 지금까지 만든 `detail.jsp`, `list.jsp`가 여기 해당한다.
- **모델2**: **서블릿(Controller)과 JSP(View)의 역할을 완전히 분리**하는 구조. JSP 안의 업무 로직(제어 코드)을 서블릿으로 옮기고, JSP는 순수하게 태그(HTML)만 남은 View로 만든다.

### 모델1에서 뭐가 문제였나

`detail.jsp`를 자세히 보면, 스크립틀릿 안에 있는 코드가 단순한 "출력 제어"만이 아니라 **업무 로직(CSV를 읽고 파싱하는 것)과 사용자 입력 처리(`id` 파라미터 처리)까지 전부** 들어 있다.

- JSP는 **재스퍼가 일해야만** 비로소 진짜 자바 코드가 되는 형태다 — 즉 **사용자가 요청한 시점에야** `.java` 파일이 만들어진다.
- 만약 JSP가 300개 있다면, 누군가 그 300개에 대해 각각 요청을 보내야만 그 300개의 `.java` 파일이 만들어진다.
- **업무 로직(주문 로직, 메뉴 조회 로직)은 자주 바뀌지 않는다.** CSV를 읽어서 파싱하는 방식, 메뉴를 조회하는 조건 같은 건 요구사항이 근본적으로 바뀌지 않는 한 손댈 일이 거의 없다.
- 반면 **화면의 껍데기(스타일, 레이아웃, 문구)는 필요에 따라 수시로 바뀐다.** 버튼 색을 바꾸거나, 문구를 수정하거나, 레이아웃을 조정하는 일은 디자인/마케팅 요청 하나로도 자주 일어난다.
- 문제는 **변경 주기가 전혀 다른 두 종류의 코드가 같은 파일에 뒤섞여 있다**는 점이다.
    - HTML/디자인만 고치러 온 사람(퍼블리셔, 프론트엔드 담당)이 파일을 열면 **원치 않아도 자바 로직을 같이 마주치게** 된다. 잘 모르는 코드 옆에서 작업하다 보면 실수로 로직을 건드려 업무 오류를 낼 위험도 생긴다.
    - 반대로 업무 로직을 고치는 개발자도, 화면 껍데기 변경 때문에 수시로 커밋되는 이 파일을 **같이 리뷰하고 충돌(merge conflict)을 처리**해야 한다 — 실제로는 전혀 다른 두 작업인데 버전 관리 이력(git history)에서는 하나로 뒤섞인다.
    - 결과적으로 **"이 파일이 왜 바뀌었는가"를 파악하기 어려워진다.** 화면 문구 하나 바꾼 커밋인지, 조회 로직이 바뀐 커밋인지 diff만 봐서는 한눈에 구분되지 않는다.
- 그래서 HTML을 만드는 사람이 자바 코드를 함께 봐야 한다는 것 자체가, 그리고 서로 다른 책임을 가진 두 작업이 한 문서를 같이 건드려야 한다는 것 자체가 구조적인 문제다.

## 6. 실제 모델2 구현 — `admin/menus` 예시

`maven_servlet_project`에서 실제로 컨트롤러와 뷰를 분리한 구조를 확인할 수 있다.

```
src/main/java/com/example/controller/admin/menu/
├── ListServlet.java     ("/admin/menus" 매핑)
└── DetailServlet.java   ("/admin/menus/12" 매핑)

src/main/webapp/WEB-INF/views/admin/menus/
├── list.jsp     ← 순수 View
└── detail.jsp   ← 순수 View
```

### 컨트롤러 — `DetailServlet.java`

```java
package com.example.controller.admin.menu;

import com.example.entity.Menu;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
// ... (생략)

@WebServlet("/admin/menus/12")
public class DetailServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        Menu menu = null;

        // 1. ClassLoader를 이용해 CSV 파일 읽기 (업무 로직)
        InputStream is = req.getServletContext().getClassLoader().getResourceAsStream("data/menus.csv");
        if (is != null) {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
                // ... CSV 파싱, menu 객체 생성 (009 노트의 detail.jsp와 동일한 로직)
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        req.setAttribute("menu", menu);
        req.getRequestDispatcher("/WEB-INF/views/admin/menus/detail.jsp").forward(req, resp);
    }
}
```

CSV를 읽고 파싱하는 **업무 로직이 전부 서블릿(컨트롤러) 쪽으로 옮겨졌다.** 마지막 두 줄이 핵심이다.

1. `req.setAttribute("menu", menu)` — 만든 데이터(모델)를 `request`에 실어둔다.
2. `req.getRequestDispatcher(...).forward(req, resp)` — View(JSP)로 흐름을 **넘긴다(포워딩)**.

### 뷰 — `WEB-INF/views/admin/menus/detail.jsp`

```jsp
<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ page import="com.example.entity.Menu" %>

<%
    // 서블릿이 forward하면서 request에 담아 보낸 menu 객체를 꺼내서 menu 변수에 저장
    Menu menu = (Menu) request.getAttribute("menu");
%>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>메뉴 상세 정보</title>
</head>
<body>
    <h1>메뉴 상세 페이지 (기본)</h1>
    <hr>

    <% if (menu != null) { %>
        <div>
            <img src="<%= menu.getImgSrc() %>" alt="<%= menu.getKorName() %>" width="200"><br>
            <p><strong>한글명:</strong> <%= menu.getKorName() %></p>
            <p><strong>가격:</strong> <%= menu.getPrice() %>원</p>
        </div>
    <% } else { %>
        <p>메뉴 데이터를 불러올 수 없습니다.</p>
    <% } %>
</body>
</html>
```

CSV를 읽고 파싱하는 코드는 완전히 사라졌다. 남은 건 **`request`에서 모델을 꺼내는 한 줄**과, 반복문·조건문처럼 동적 출력에 어쩔 수 없이 필요한 최소한의 코드뿐이다. `ListServlet.java`/`list.jsp`도 같은 패턴이다 — 컨트롤러가 `menus` 배열과 `count`를 만들어 `setAttribute`로 실어 보내고, JSP는 그걸 꺼내 `<% for %>`로 출력만 한다.

## 7. 왜 View를 사용자가 직접 요청하면 안 되는가

`/admin/menus/12`(서블릿, 컨트롤러)와 `admin/menus/detail.jsp`(뷰)를 각각 직접 요청해보면 알 수 있는 게 있다.

- **서블릿(`/12`)만 직접 실행**: 컨트롤러만 실행된 결과라, 화면을 만들 View가 없으니 **빈 화면**이 보인다.
- **JSP(`detail.jsp`)만 직접 실행**: View만 실행된 결과라, `request.getAttribute("menu")`로 꺼낼 데이터가 애초에 없으니(컨트롤러를 거치지 않았으니) **오류**가 난다.

둘 다 반쪽짜리이기 때문에, **어느 한쪽만 단독으로 실행되는 상황이 발생하면 안 된다.** 사용자의 요청은 반드시 **컨트롤러(`/admin/menus/12`)로 먼저 가야 하고**, 컨트롤러가 필요한 데이터(모델)를 만든 다음 **View(JSP)를 호출하는 방식**으로 흘러가야 한다. 즉:

- 사용자는 **컨트롤러만** 직접 요청할 수 있어야 한다
- **View(JSP)는 사용자가 직접 호출할 수 없어야** 한다 — 반드시 컨트롤러를 거쳐서만 실행되어야 한다

### 이유를 일반화하면 — MVC 역할 분리(Separation of Concerns) 관점

위 예시에서 본 "빈 화면"과 "오류"는 사실 더 큰 문제의 두 가지 증상일 뿐이다. MVC 패턴의 핵심은 **역할 분리**이고, 사용자가 Controller나 Model을 거치지 않고 View를 직접 요청하면 구조·보안·유지보수 측면에서 아래 네 가지 문제가 함께 발생한다.

**1. 비즈니스 로직 및 데이터 검증 우회**

컨트롤러는 요청을 처리하기 전에 권한 확인, 입력값 검증, 세션 상태 확인 같은 필수 로직을 수행한다. View를 직접 요청하면 이 검증 절차 자체가 통과되어, 비인가 사용자가 화면에 접근하거나 잘못된 상태로 페이지가 그려질 수 있다.

**2. 데이터 미전달로 인한 화면 오류 (앞서 본 "오류"의 정체)**

JSP 같은 동적 View는 Model에서 넘겨받은 데이터(DB 조회 결과, 사용자 정보 등)를 바탕으로 화면을 그린다. 컨트롤러를 거치지 않고 View에 바로 접근하면 그 데이터 자체가 준비되지 않은 상태라, 화면이 비정상 출력되거나 `request.getAttribute(...)`가 `null`을 반환하며 오류로 이어진다.

**3. 보안 취약점 노출**

렌더링 전용 파일(뷰 파일, 템플릿)의 경로가 외부에 그대로 노출되면 공격자가 시스템 내부 구조를 파악하기 쉬워진다. 프론트엔드/백엔드의 경계가 모호해지면서, 원래 감춰져 있어야 할 로직이나 주석까지 그대로 드러날 위험도 있다 — `WEB-INF`로 뷰 파일을 옮겨 막는 이유가 바로 이것.

**4. 유지보수성·재사용성 저하 (강한 결합)**

사용자가 `/views/user/profile.jsp` 같은 View 파일 경로를 직접 호출하게 되면, 나중에 그 파일의 위치나 이름이 바뀔 때마다 사용자가 쓰던 URL까지 전부 함께 바꿔야 한다. **컨트롤러라는 중계자를 두어 "요청 URL"과 "실제 View 파일 경로"를 매핑**해둬야, View 쪽 구조가 바뀌어도 바깥에 노출된 URL은 그대로 유지할 수 있다.

**요청 흐름 정리**

| 흐름 | 경로 |
|---|---|
| ❌ 잘못된 흐름 | 사용자 → View(직접 접근) → 데이터 부족/보안 문제 |
| ✅ 올바른 흐름 | 사용자 → Controller → Model(데이터 처리/조회) → View(데이터 바인딩·렌더링) → 응답 |

### `WEB-INF` — 사용자가 절대 직접 요청할 수 없는 영역

지금까지 `.jsp` 파일이 `webapp/admin/menus/` 아래에 있었다면, 사용자가 URL로 `admin/menus/detail.jsp`를 직접 쳐서 접근할 수 있는 영역에 있는 것이다. 이걸 막으려면 **`WEB-INF` 디렉토리 안으로 옮기면 된다.**

**`WEB-INF` 안에 있는 파일은 사용자가 브라우저로 직접 요청할 수 없다.** 그래서 위 예시처럼 뷰 파일들이 `src/main/webapp/WEB-INF/views/admin/menus/` 아래로 옮겨져 있는 것이다 — 이렇게 하면 오직 서블릿(컨트롤러)만이 서버 내부에서 `RequestDispatcher`로 이 파일에 접근할 수 있고, 사용자는 URL로 직접 도달할 방법이 없다.

## 8. 포워딩(forwarding)

컨트롤러가 뷰로 흐름을 넘기는 것을 **포워딩(forwarding)**이라고 부른다. 우편물을 다른 수신자에게 넘기듯, **받은 요청을 다른 자원(JSP)에 넘겨서 이어받게 하는 것**이다.

- 포워딩은 **값과 상관없이 흐름(요청 처리)을 이어주는 것** 자체를 가리킨다.
- 실제로 **값을 공유하는 방법**(모델을 전달하는 방법)은 포워딩과는 별개의 개념이다 — 값 공유는 아래에서 다루는 **저장소 객체(`setAttribute`/`getAttribute`)**로 이루어진다.

```java
req.getRequestDispatcher("/WEB-INF/views/admin/menus/detail.jsp").forward(req, resp);
```

`RequestDispatcher.forward(req, resp)`가 바로 그 포워딩을 실행하는 코드다.

## 9. 값을 공유하는 저장소 — `page` / `request` / `session` / `application`

모든 웹 개발 기술에는 **값을 세팅하고 얻을 수 있는(`setAttribute`/`getAttribute`) 저장소 객체**가 공통으로 존재한다. 기술마다 객체 이름이나 형식은 달라도 **용도는 같다.** 중요한 건 각 저장소가 **언제부터 언제까지 유지되는지**, 그 생명주기를 아는 것이다.

이런 저장소 객체들은 재스퍼가 만든 `.java` 파일을 보면 **이미 지역 변수로 마련되어 있는 내장 객체**라는 걸 확인할 수 있다 — 그래서 JSP에서 별도 선언 없이 바로 쓸 수 있다.

| 저장소 | 유지 범위 |
|---|---|
| `page` | 한 페이지의 요청·응답이 끝나면 바로 사라진다 |
| `request` | 하나의 요청-응답 사이(**포워딩되는 두 자원 사이**)에서만 공유되고 그 후 버려진다 |
| `session` | 한 사용자가 사이트를 떠나기 전까지 그 사용자 전용 데이터를 저장한다 |
| `application` | 애플리케이션이 시작되고 나서 완전히 종료될 때까지 저장된다 (이전에 다룬 `ServletContext`와 같은 범위) |

**포워딩할 때 데이터를 담아두고 넘겨줄 저장소로는 이 중 무엇이 적절할까?** 컨트롤러와 뷰는 **하나의 요청-응답 사이클 안에서 포워딩으로 연결**되므로, 둘이 `request`와 `response`를 공유하게 된다. 그래서 `req.setAttribute("menu", menu)`처럼 **`request` 저장소**에 값을 담아두면, 포워딩된 JSP 쪽에서 `request.getAttribute("menu")`로 그 값을 그대로 꺼낼 수 있다. `session`이나 `application`을 쓰면 필요 이상으로 오래 남거나 다른 사용자·다른 요청과 뒤섞일 수 있으므로, 포워딩 시점의 값 전달에는 `request`가 맞는 범위다.

## 10. 왜 배열과 `size`를 따로 들고 다니면 불편한가 — 박싱/언박싱

`Menu[] menus`와 `int size`를 세트로 관리하다 보면, "함수 안에서 `size`를 바꾼 걸 함수 밖(`main`)에서도 반영되게 할 수 없을까?"라는 생각이 든다. `int`는 값 형식이라 함수에 넘기면 복사본이 넘어가므로(Call by Value), 함수 안에서 아무리 `size`를 바꿔도 밖의 값은 그대로다.

그럼 "참조로 넘기면 되지 않나?"라는 생각이 이어진다 — 배열처럼 `Object`(참조형)로 감싸서 넘기면 함수 밖에서도 그 변경이 보이지 않을까? 여기서 확인해야 할 게 **박싱(boxing)/언박싱(unboxing)**이다.

- `Object`는 **참조형**이다. 참조형에는 값 그 자체를 대입할 수 없다 — 값을 담으려면 그 값을 감싸는 **박스(래퍼 클래스)**가 필요하다.
- `int` 같은 값 형식을 `Integer` 같은 **래퍼 클래스**로 감싸는 것이 **박싱**이고, 그 박스를 까서 다시 값을 꺼내는 것이 **언박싱**이다.
- `Integer`를 비롯한 래퍼 클래스들은 전부 `Number`라는 추상 클래스에서 파생된다. 그런데 **`Number` 계열 래퍼 클래스는 함수의 인자로 전달되는 순간 자동으로 언박싱된다** — 즉 참조형으로 감싸서 넘겨봤자, 함수 안으로 들어가는 순간 다시 값 형식(`int`)처럼 취급된다.
- 그래서 함수 쪽에서 매개변수를 `Integer size`로 받아도, 함수 안에서 그 값을 바꾸면 그 순간 다시 **박싱**되어 새로운 `Integer` 객체가 만들어질 뿐이다. 원래 넘어온 참조가 가리키던 값이 바뀌는 게 아니므로, 함수 밖의 `size`는 여전히 그대로다.

**결론: `size` 하나만 참조로 넘겨서 함수 안에서 바꾸려는 시도 자체를 포기해야 한다.** 애초에 이 방향으로 문제를 풀 수 없다.

## 11. 배열과 `size`를 하나의 캡슐로 묶기

`size`를 참조로 넘기려는 시도가 막다른 길이라면, 접근 자체를 바꿔야 한다. **배열과 `size`는 원래부터 쌍으로 붙어다녀야 하는 데이터**다 — 그렇다면 이 둘을 아예 **하나의 객체**로 묶어버리면 된다.

실습으로 만든 `MenuList.java`가 실제로 이 방식을 구현한다.

```java
package collection;

import collection.entity.Menu;

// 데이터를 수집하고 관리해주는 서비스 클래스
// => 콜렉션
public class MenuList {
    private Menu[] menus = new Menu[10];
    private int size = 0;

    public int getSize() {
        return size;
    }

    public void add(Menu menu) {
        menus[size] = menu;
        size++;
    }

    public Menu get(int i) {
        return menus[i];
    }
}
```

`Menu[] menus`와 `int size`를 `MenuList` 하나로 캡슐화했다. 이제 배열과 `size`를 따로 주고받을 필요가 없다 — `MenuList` 객체 하나만 넘기면, 그 안에 `size`까지 함께 참조된다.

```java
// Ex2MenuCollection.java
private static void input(MenuList menus) {
    // ...
    int size = menus.getSize();
    Menu menu = new Menu(size + 1, korName, engName, price);
    menus.add(menu);
    // ...
}

private static void print(MenuList menus) {
    int size = menus.getSize();
    for (int i = 0; i < size; i++) {
        Menu m = menus.get(i);
        // ...
    }
}
```

`input`, `print` 두 함수 모두 `MenuList menus` **하나만** 매개변수로 받는다. 그 안에서 `menus.add(menu)`로 메뉴를 추가하는 서비스, `menus.get(i)`로 메뉴 하나를 꺼내는 서비스를 각각 호출할 뿐, 배열과 `size`를 별도로 주고받지 않는다.

이렇게 **"데이터를 수집하고 관리하는 일"을 전담하는 역할자**를 만든 것이 바로 **컬렉션(Collection)**이다. `MenuList`는 `Menu`를 관리하는 전용 컬렉션인 셈이다.

### 그런데 이 컬렉션은 `Menu`밖에 못 다룬다

`MenuList`는 딱 `Menu`만 관리할 수 있다. 성적 데이터(`Exam`)를 관리하고 싶으면 `ExamList`를 또 만들어야 한다. 그런데 `add`, `get`, `getSize`처럼 **서비스 로직 자체는 거의 똑같고, 달라지는 건 오직 다루는 타입(`Menu[]` → `Exam[]`)뿐**이다. 그렇다면 이 컬렉션을 **형식에 구애받지 않고 두루 쓸 수 있게** 만들 수는 없을까?

## 12. 컬렉션과 제네릭 — 배열에서 `ArrayList`로

배열(`Menu[] menus = new Menu[100]`)은 **크기가 고정**되어 있고, 값을 채우고 관리하는 걸 전부 손으로 해야 한다(`count` 변수로 현재 채워진 개수를 따로 세는 등). 목록의 크기가 늘어나거나 줄어들 수 있고, 추가·삭제·조회가 잦다면 배열 대신 **컬렉션**을 쓰는 게 훨씬 편하다.

`maven_servlet_project`의 `ListServlet.java`가 실제로 배열 방식에서 `ArrayList` 방식으로 바뀐 걸 코드에 남아있는 주석으로 확인할 수 있다.

```java
@Override
protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
    // Menu[] menus = new Menu[100];
    // int count = 0;

    List<Menu> menus = new ArrayList<>();

    InputStream is = req.getServletContext().getClassLoader().getResourceAsStream("data/menus.csv");
    if (is != null) {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
            String line;
            boolean isFirstLine = true;
            while ((line = reader.readLine()) != null) {
                if (isFirstLine) { isFirstLine = false; continue; }
                String[] tokens = line.split(",");
                if (tokens.length >= 7) {
                    // ... 필드 파싱

                    // menus[count++] = new Menu(...);
                    Menu menu = new Menu(id, korName, engName, imgSrc, description, categoryName, price);
                    menus.add(menu);
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    req.setAttribute("menus", menus);
    req.getRequestDispatcher("/WEB-INF/views/admin/menus/list.jsp").forward(req, resp);
}
```

주석 처리된 두 줄(`Menu[] menus = new Menu[100];`, `menus[count++] = ...`)이 예전 배열 방식이고, 그 대신 `List<Menu> menus = new ArrayList<>()`로 선언해서 `menus.add(menu)`로 값을 추가한다. **크기를 미리 정해둘 필요가 없고, 채워진 개수(`count`)도 따로 관리할 필요 없이 `menus.size()`로 바로 알 수 있다.**

`List<Menu>`의 `<Menu>` 부분이 **제네릭**이다 — 이 리스트에는 `Menu` 타입만 담을 수 있다고 미리 선언해두는 문법이다. 그 덕에 요소를 꺼낼 때(`menus.get(i)`) 별도의 형변환 없이 바로 `Menu`로 쓸 수 있다.

| 선언 방식 | 특징 | 주의점 |
|---|---|---|
| `List<Menu>` | `Menu`만 저장, 타입 안정성 확보 | 다른 타입은 추가 불가 |
| `List<Object>` | 여러 타입을 섞어 저장 가능 | 꺼낸 값을 쓰려면 형변환 필요 |
| Raw Type(`List`) | 제네릭 타입 생략 | 컴파일 단계 타입 검사가 약해짐 |

**선언은 상위 타입(`List`)으로, 생성은 구현 클래스(`ArrayList`)로** 하는 게 관례다.

```java
List<Menu> menus = new ArrayList<>();
```

`ListServlet`이 필요로 하는 기능이 "목록에 추가하고, 꺼내고, 개수를 센다"는 **목록 공통 기능**뿐이라면, 실제 구현체(`ArrayList`)가 무엇인지에 직접 의존할 필요가 없다 — 그래서 변수 타입은 인터페이스인 `List`로 선언한다.

### JSP 쪽도 배열 접근에서 리스트 접근으로

`WEB-INF/views/admin/menus/list.jsp`도 서블릿이 바뀐 방식에 맞춰 함께 바뀐다.

```jsp
<%
    // 서블릿이 forward하면서 request에 담아 보낸 menus 값을 꺼내서 변수에 저장
    List<Menu> menus = (List<Menu>) request.getAttribute("menus");
    int count = menus.size();
%>
...
<% for (int i = 0; i < count; i++) { %>
  <tr>
    <td><a href="detail.jsp?id=<%= menus.get(i).getId() %>"><%= menus.get(i).getKorName() %></a></td>
    <td><%= menus.get(i).getCategoryName() %></td>
    <td><%= menus.get(i).getPrice() %>원</td>
  </tr>
<% } %>
```

- 배열의 `menus[i]` → 리스트의 `menus.get(i)`
- 배열의 `menus.length` → 리스트의 `menus.size()`
- `request.getAttribute("menus")`의 반환 타입은 `Object`이므로, 실제로 `List<Menu>`의 기능(`.get()`, `.size()`)을 쓰려면 `(List<Menu>)`로 **형변환**이 필요하다 — 컨트롤러가 애초에 `menus`와 `count`를 각각 보냈던 이전 방식과 달리, 지금은 컬렉션 자체가 개수 정보(`.size()`)를 갖고 있으므로 **`count`를 별도로 `setAttribute`할 필요조차 없다.** 모델이 이미 갖고 있는 정보는 모델에서 직접 얻는 쪽이 전달 데이터를 더 단순하게 만든다.

## 13. `Object`로 뭐든 담으면 안 되나 — 제네릭이 필요한 이유

`MenuList`를 형식에 구애받지 않게 만들려면, `Menu[]` 대신 `Object[]`를 쓰면 될 것 같다. `Object`는 모든 타입의 부모이므로, `Object` 배열이라면 `Menu`든 숫자든 문자열이든 다 담을 수 있다 — 실제로 `ArrayList`를 제네릭 없이 그냥 쓰면 이런 "뭐든 담기는 리스트"와 똑같이 동작한다(`add`를 호출하면 내부 배열 공간이 부족할 때 알아서 더 큰 배열로 바꿔가며 계속 늘어난다).

문제는 **꺼낼 때** 드러난다. `get(i)`로 값을 꺼내면 반환 타입이 `Object`다. `.` 을 찍어봐도 `Menu`의 기능(`getKorName()` 등)이 아니라 `Object`의 기능만 보인다 — **형변환을 직접 해줘야** 하고, **그 안에 실제로 어떤 타입의 객체가 들어있는지도 매번 확인**해야 한다.

더 치명적인 건 **타입이 섞이는 걸 막을 방법이 없다**는 점이다. 학생 목록엔 학생만, 메뉴 목록엔 메뉴만 들어가는 게 보통인데, `Object`로 관리하면 실수로 다른 타입의 값이 섞여 들어가도 컴파일 시점에는 아무 문제가 없다 — 실행하다가 형변환에서 터진다.

그렇다고 다시 `Menu` 전용, `Exam` 전용으로 컬렉션을 따로따로 만드는 건(11절의 `MenuList`처럼) 서비스 로직이 거의 똑같은데도 타입마다 클래스를 복제해야 해서 비효율적이다.

### 제네릭 — "형식은 비워둘게, 네가 나중에 채워줘"

여기서 **제네릭(Generic)**이 등장한다. 제네릭은 **아직 무엇이든 될 수 있는, 아직 정해지지 않은 자리**를 만드는 문법이다 — 클래스를 정의하는 시점에는 다룰 타입을 비워두고, 그 클래스를 실제로 사용하는 쪽에서 "이번엔 이 타입으로 채워줘"라고 지정한다.

실습으로 만든 `GList.java`가 이걸 직접 구현한 예시다.

```java
package collection;

public class GList<T> {
    private Object[] objs = new Object[10];
    private int size = 0;

    public int getSize() {
        return size;
    }

    public void add(T menu) {
        if (objs.length <= size) {
            // 배열을 큰걸로 바꿔주기
        }

        objs[size] = menu;
        size++;
    }

    public T get(int i) {
        return (T) objs[i];
    }
}
```

- 클래스 이름 옆의 `<T>`가 "타입을 나중에 받겠다"는 선언이다. 타입 이름 자리에는 관례적으로 `T`(Type)를 많이 쓴다.
- 내부적으로는 여전히 `Object[]`로 값을 저장한다 — 그래서 어떤 타입이든 담을 수 있다.
- 다만 `add(T menu)`, `get(int i): T`처럼 **바깥으로 드러나는 입출력 타입은 `T`로 고정**해둔다. 그래서 실제로 사용할 때 타입을 지정하고 나면, 그 타입만 들어가고 나올 수 있다.

```java
GList<Menu> list = new GList<>();
```

`<Menu>`라고 지정하는 순간, 이 `GList`는 `Menu` 전용처럼 동작한다 — `add`에는 `Menu`만 넣을 수 있고, `get`은 형변환 없이 바로 `Menu`를 돌려준다. 클래스는 **하나**만 만들어두고, 쓰는 쪽에서 타입만 바꿔 끼우면 되는 것이다.

### `ArrayList`도 결국 이런 제네릭 클래스다

`ArrayList` 역시 `GList`와 똑같은 원리로 만들어진 제네릭 컬렉션이다. 소스를 열어보면 `List`를 기반으로 구현되어 있다는 걸 확인할 수 있다. 그래서 12절에서 본 것처럼:

- 변수 선언은 구체적인 구현 클래스(`ArrayList`)가 아니라 **더 유연한 상위 타입인 `List`**로 하는 걸 기본으로 삼는다.
- `ArrayList`에만 있는 특수 기능을 쓰는 게 아니라면, `List`가 제공하는 공통 기능만으로 충분하다.

목록(리스트) 계열 말고도 `Set`, `Map` 계열의 컬렉션도 있다는 것도 참고로 알아둘 만하다 — 지금은 목록을 다루는 `List`/`ArrayList`에 집중하면 된다.

**정리**: 이제 배열을 직접 쓸 일은 거의 없다. `ArrayList`(와 제네릭)로 배열이 하던 일을 대신할 수 있고, `size`를 따로 관리하는 번거로움도, `Object`로 인한 형변환·타입 안전성 문제도 함께 해결된다.

