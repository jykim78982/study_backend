---
tags: [자바, 서블릿, HTTP, request, 메서드체이닝]
날짜: 2026-08-20
---

> 🔗 관련 노트: [[035_MVC 패턴과 모델2(서블릿·JSP 분리)]] · [[038_JDBC API와 리포지토리 분리]]

# 서블릿·HTTP API 메서드 체이닝 뜯어보기

`035`, `038` 노트에서 다룬 서블릿 코드의 체이닝 호출들을, 한 단계씩 무엇을 반환하고 무엇을 하는지 뜯어서 정리한다.

## 1. request에서 클래스로더를 거쳐 리소스 스트림 얻기

```java
InputStream is = req.getServletContext().getClassLoader().getResourceAsStream("data/menus.csv");
```

- **`req`**: 서블릿의 `doGet(req, resp)`로 들어온 `HttpServletRequest` 객체. 지금 처리 중인 HTTP 요청 그 자체다.
- **`.getServletContext()`**: `req`에서 **이 웹 애플리케이션 전체를 대표하는 객체(`ServletContext`)**를 꺼낸다. 서블릿 하나가 아니라 애플리케이션 전체에 걸쳐 공유되는 정보에 접근할 때 쓴다.
- **`.getClassLoader()`**: `ServletContext`에서 **이 애플리케이션의 클래스를 로드한 `ClassLoader` 객체**를 꺼낸다. 클래스·리소스가 실제로 어디 배치되어 있는지 알고 있는 객체다.
- **`.getResourceAsStream("data/menus.csv")`**: `ClassLoader`에게 "그 위치를 기준으로 `data/menus.csv`를 찾아서, 바로 읽을 수 있는 스트림으로 열어줘"라고 요청한다. 반환값은 **`InputStream`** — 위치(경로)가 아니라 **읽기 시작할 수 있는 통로**를 바로 받는다는 점이 `038` 노트의 `.getResource(...).getPath()`(경로 문자열만 받기)와 다르다.

## 2. request에 데이터를 실어 View로 흐름 넘기기

```java
req.setAttribute("menu", menu);
req.getRequestDispatcher("/WEB-INF/views/admin/menus/detail.jsp").forward(req, resp);
```

- **`req.setAttribute("menu", menu)`**: 컨트롤러가 만든 데이터(`menu`)를, `"menu"`라는 이름표를 붙여 `request` 저장소에 넣어둔다. 같은 요청을 이어받을 View(JSP)가 나중에 이 이름으로 꺼내 쓸 수 있다.
- **`req.getRequestDispatcher("/WEB-INF/...jsp")`**: `req`에게 "이 경로의 자원(JSP)으로 요청을 이어줄 중계자를 하나 만들어줘"라고 요청한다. 반환값은 **`RequestDispatcher`** — 아직 이동은 일어나지 않고, 이동을 담당할 객체만 준비된 상태다.
- **`.forward(req, resp)`**: 그 중계자에게 지금 갖고 있는 `req`(방금 `setAttribute`로 데이터를 실어둔 바로 그 객체)와 `resp`를 그대로 넘기며, **실제로 흐름을 JSP 쪽으로 이동**시킨다. `req`가 같은 객체로 그대로 넘어가기 때문에, JSP 쪽에서도 방금 담아둔 `"menu"` 값을 꺼낼 수 있는 것이다.

## 3. request에서 데이터를 꺼내 원래 타입으로 되돌리기

```java
Menu menu = (Menu) request.getAttribute("menu");
```

- **`request.getAttribute("menu")`**: `request` 저장소에서 `"menu"`라는 이름으로 저장된 값을 꺼낸다. 반환 타입은 무엇이 들어있었는지 모르는 **`Object`**다 — 저장할 때 타입 정보가 사라지기 때문이다.
- **`(Menu) ...`**: 사실 그 안에 들어있는 게 `Menu`라는 걸 개발자가 알고 있으므로, **형변환(다운캐스팅)**으로 `Object`를 다시 `Menu` 타입으로 되돌린다. 이 캐스팅이 틀리면(실제로 다른 타입이 들어있었으면) 실행 시점에 `ClassCastException`이 난다.

## 4. 체이닝이 아닌 개별 선언·문장도 뜯어보기

```java
@WebServlet("/admin/menus/12")
public class DetailServlet extends HttpServlet {
```

- **`@WebServlet("/admin/menus/12")`**: 클래스 바로 위에 붙는 **애노테이션**이다. "이 클래스는 서블릿이고, `/admin/menus/12`라는 URL 요청이 들어오면 이 클래스가 처리한다"는 걸 톰캣에게 알려주는 표식이다. 이 표식이 있어야 톰캣이 이 클래스를 스캔해서 등록한다(`033` 노트의 RTTI/리플렉션이 실제로 이 표식을 읽어내는 방식이다).
- **`extends HttpServlet`**: 이 클래스가 자바가 이미 만들어둔 `HttpServlet`의 기능(요청·응답을 다루는 기본 골격)을 그대로 물려받는다는 뜻이다. 그래서 `doGet`, `doPost` 같은 메서드를 **오버라이드**해서 필요한 부분만 채우면 된다.

```java
@Override
protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
```

- **`@Override`**: 부모(`HttpServlet`)가 이미 갖고 있는 메서드를 **재정의**한다는 표시다. 이름이나 매개변수가 부모와 조금이라도 다르면 컴파일러가 오류로 잡아준다.
- **`protected void doGet(...)`**: 메서드 이름 `doGet`은 자바가 정해둔 **약속된 이름**이다 — `GET` 방식 요청이 들어오면 톰캣이 내부적으로 이 이름의 메서드를 찾아 호출한다(`019` 노트에서 다룬 "이름을 맞춰야 인정되는 메서드"와 같은 원리다). `protected`는 이 메서드를 부모 클래스나 같은 패키지에서만 호출할 수 있게 제한한다는 뜻이다.
- **`(HttpServletRequest req, HttpServletResponse resp)`**: 매개변수 두 개가 각각 **요청 정보를 담은 객체**와 **응답을 만들어 보낼 객체**다. 톰캣이 이 메서드를 호출할 때 알아서 채워서 넘겨준다.
- **`throws ServletException, IOException`**: 이 메서드 안에서 발생할 수 있는 예외 두 종류를 **직접 처리하지 않고, 호출한 쪽(톰캣)에게 떠넘기겠다**는 선언이다. 그래서 메서드 몸통 안에서는 이 두 예외에 대해 `try-catch`를 강제로 쓰지 않아도 된다.

```java
Menu menu = null;
```

- 아직 아무 값도 없이, **참조형 변수 하나를 미리 선언만 해두는 것**이다. `null`은 "가리키는 대상이 아직 없다"는 뜻으로, 힙에 객체가 전혀 만들어지지 않은 상태를 나타낸다.
- 뒤에서 CSV/DB를 읽어 실제 `Menu` 객체를 만들면 그때 이 변수에 대입된다. 만약 데이터를 못 찾으면 이 변수는 끝까지 `null`로 남고, JSP 쪽에서 `if (menu != null)`로 그 상태를 확인해 화면을 다르게 그린다.
