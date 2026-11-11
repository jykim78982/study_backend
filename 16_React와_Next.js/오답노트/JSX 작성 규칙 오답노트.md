---
tags: [React, JSX, 오답노트]
---

# JSX 작성 규칙 오답노트

### 1. JSX 작성 시 주의할 점으로 옳지 않은 것은?

**문제**: JSX 작성 시 주의할 점으로 옳지 않은 것은?

1. style 속성은 문자열로 그대로 전달한다
2. 단일 태그(input, img 등)도 닫아야 한다
3. JSX는 브라우저가 직접 이해하지 못하므로 변환이 필요하다
4. HTML의 class 속성은 JSX에서 className으로 쓴다

**정답: 1번 (옳지 않은 것)**

- **1번이 틀린 이유**: JSX의 `style` 속성은 HTML처럼 `"color: red; font-size: 16px;"`같은 문자열이 아니라, **자바스크립트 객체**로 전달해야 한다.

  ```jsx
  // HTML 방식 (JSX에서는 불가능)
  <div style="color: red; font-size: 16px;">

  // JSX 방식 — 올바른 형태
  <div style={{ color: "red", fontSize: "16px" }}>
  ```

  바깥 중괄호는 "여기부터 자바스크립트 표현식"이라는 JSX 표시이고, 안쪽 중괄호가 실제 객체 리터럴이라서 중괄호가 두 번 겹친다. `font-size`처럼 하이픈이 든 CSS 속성명은 객체 키로 쓸 수 없으므로 `fontSize`처럼 카멜케이스로 바꿔 써야 한다.

- **2번은 옳은 설명**: JSX는 XML 기반 규격(well-formed)을 따르므로, HTML에서는 안 닫아도 되던 `<input>`, `<img>` 같은 단일 태그도 반드시 `<input type="text" />`처럼 자기 자신을 닫는 표기를 붙여야 한다.

- **3번은 옳은 설명**: JSX는 브라우저가 직접 해석할 수 있는 문법이 아니다. Babel 같은 트랜스파일러가 `React.createElement(...)` 호출 형태의 순수 자바스크립트로 변환해줘야 실행할 수 있다.

- **4번은 옳은 설명**: `class`는 자바스크립트의 예약어(클래스 선언 키워드)와 이름이 겹치기 때문에, JSX에서는 HTML의 `class` 속성 대신 `className`을 쓴다(`<div className="container">`).

tags: #웹 #자바스크립트 #JSX #React #Babel

> 🔗 관련 노트: [[054_자바스크립트 플랫폼의 진화 — DOM API에서 jQuery, MVC, React(Flux)까지]]
