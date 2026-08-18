---
tags: [자바, 서블릿, JSP, 포워딩, request, 컬렉션, ArrayList]
날짜: 2026-08-15
---

> 🔗 관련 노트: [[035_MVC 패턴과 모델2(서블릿·JSP 분리)]] · [[015_배열과 참조, 메모리 구조]] · [[001_기본형과 참조형, 박싱언박싱과 Object 배열, ArrayList]]

# 포워딩과 request 속성, 배열에서 컬렉션으로 전환

퀴즈로 정리해본 세 가지 — 포워딩(forward)이 리다이렉트와 뭐가 다른지,
`request.setAttribute()`/`getAttribute()`가 왜 매번 캐스팅을 요구하는지,
배열 코드를 컬렉션 코드로 바꿀 때 뭐가 달라지는지.

## 1. 포워딩(Forward) — 요청은 딱 한 번, 서버 안에서만 이어짐

Controller(서블릿)가 View(JSP)로 제어권을 넘기는 것을 **포워딩**이라고
한다.

- 클라이언트(브라우저) 입장에서는 **요청을 딱 한 번만** 보낸 상태다.
- URL이 바뀌지 않고, 서버 내부에서 같은 `request`/`response` 객체를
  그대로 이어받아 처리한다.
- 그래서 Controller가 `request.setAttribute("data", result)`로 담아둔
  값을, View가 `request.getAttribute("data")`로 그대로 꺼낼 수 있다 —
  같은 요청 안이라 데이터가 유지되기 때문.

### 포워딩 vs 리다이렉트

| | 포워딩 (`RequestDispatcher.forward`) | 리다이렉트 (`response.sendRedirect()`) |
|---|---|---|
| 요청 횟수 | 1번 (서버 내부에서만 이동) | 2번 (브라우저가 새로 요청) |
| URL 표시 | 그대로 유지됨 | 바뀐 URL로 변경됨 |
| `request` 데이터 | 그대로 유지됨 | **사라짐** — 새 요청이라 별개의 request |
| 동작 방식 | 서버가 내부적으로 흐름만 이어줌 | 브라우저에 302 응답 → "다른 URL로 다시 요청해" |

리다이렉트 이후에도 값을 유지하고 싶다면 `request` 범위가 아니라
`session`이나 `application` 범위에 담아둬야 한다 — 포워딩은 **단일
요청·응답 주기 동안만 유지되는 `request` 범위**를 그대로 활용하는
것이라 별도 저장소가 필요 없다는 게 장점이다.

## 2. `request.setAttribute()` / `getAttribute()` — 반환형이 `Object`인 이유

`HttpServletRequest`라는 상자에는 `String`, `Integer`, `List`, 사용자
정의 객체 등 **무엇이든** 담길 수 있어야 한다. 그래서 이 API는 이렇게
설계되어 있다.

```java
void setAttribute(String name, Object o);
Object getAttribute(String name);
```

담을 때는 어떤 타입이든 `Object`로 받아주지만, **꺼낼 때도 항상
`Object` 타입으로 돌려준다.** 그래서 꺼낸 값의 원래 타입 전용 메서드
(`List`의 `.get()`, `String`의 `.length()` 등)를 쓰려면 **반드시 원래
타입으로 캐스팅**해야 한다.

```java
List<Menu> menus = (List<Menu>) request.getAttribute("menus");
```

- 서블릿 API는 내부적으로 제네릭을 지원하지 않는다 — `getAttribute()`가
  자동으로 `List<Menu>`를 돌려주는 방법은 없다. 컴파일 시점엔 실제로
  뭐가 들어있는지 알 방법이 없으니, 타입 검사도 캐스팅 시점(실행 시점)
  에야 이루어진다. 엉뚱한 타입으로 캐스팅하면 그 순간
  `ClassCastException`이 난다 ([[001_기본형과 참조형, 박싱언박싱과 Object 배열, ArrayList]] 5번 섹션의 함정 1과 같은 원리).
- `request.setAttribute()`는 **현재 요청(request) 범위**에 저장하는
  것이다. 세션에 저장하고 싶다면 `request.getSession().setAttribute()`
  를 따로 호출해야 한다 — 범위가 다르다.

## 3. 배열 → 컬렉션(`ArrayList`) 전환 — 문법이 통째로 바뀐다

| | 배열(`Menu[]`) | 컬렉션(`List<Menu>`/`ArrayList<Menu>`) |
|---|---|---|
| 정체 | 문법 레벨의 연속된 메모리 공간 | 자바 클래스로 구현된 객체 자료구조 |
| 크기 확인 | `.length` (필드) | `.size()` (메서드) |
| 값 꺼내기 | `arr[i]` (대괄호 연산자) | `list.get(i)` (메서드) |
| 크기 관리 | 직접 카운터(`count`)를 따로 들고 다녀야 함 | `add()`가 알아서 늘려주고 `size()`로 바로 개수 확인 |

컬렉션 객체에 `[]`나 `.length`를 그대로 쓰면 **컴파일 에러**가 난다 —
배열 문법과 컬렉션 문법은 서로 호환되지 않는, 완전히 다른 API다.

**컬렉션도 참조형 객체이므로 포워딩 제약은 전혀 없다.** `Menu[]`든
`List<Menu>`든 `request.setAttribute()`에 그대로 담아 View로 넘길 수
있다 — MVC 모델에서 가변적인 데이터를 다룰 땐 크기 고정이 없는
`ArrayList` 쪽이 훨씬 유연해서 배열 대신 자주 쓰인다.

## 4. 한 흐름으로 정리

1. **Controller**: DB에서 조회한 데이터를 `ArrayList`로 담아
   `request.setAttribute("list", list)`로 저장한다.
2. **Forwarding**: `RequestDispatcher`로 같은 요청 흐름을 유지한 채
   View(JSP)로 제어권을 넘긴다.
3. **View**: `(List<Data>) request.getAttribute("list")`로 다운캐스팅해
   꺼낸 뒤, `.size()`/`.get(i)`(또는 JSTL/EL)로 화면에 출력한다.
