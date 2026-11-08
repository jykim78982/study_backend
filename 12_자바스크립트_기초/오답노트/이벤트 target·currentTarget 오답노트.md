---
tags: [자바스크립트, DOM, 이벤트, target, currentTarget, 오답노트]
---

# 이벤트 target·currentTarget 오답노트

### 1. 이벤트 객체의 `target` 속성은 무엇을 가리키는가?

**문제**: 이벤트 객체의 `target` 속성은 무엇을 가리키는가?

1. 이벤트를 처리한 브라우저 모듈
2. 이벤트 리스너가 등록된 요소
3. 이벤트가 실제로 시작된 가장 안쪽 요소
4. 이벤트 발생 시점의 `window` 객체

**정답: 3번**

- `target`은 사용자가 실제로 클릭하거나 조작한 **가장 안쪽(최하위) DOM 요소**를 가리킨다. 이벤트가 버블링되어 부모, 조상까지 전파되어도 `target`이 가리키는 대상은 처음 발생한 그 요소로 고정되어 절대 바뀌지 않는다.
- 2번은 오답처럼 보이지만 사실 `target`이 아니라 **`currentTarget`**에 대한 설명이다 — `currentTarget`은 지금 이 핸들러가 걸려 있는(이벤트 리스너를 등록한) 요소를 가리키며, 버블링 과정에서 여러 조상의 핸들러가 차례로 실행될 때마다 그 값이 매번 현재 실행 중인 핸들러의 요소로 바뀐다.
- 1번(브라우저 모듈)과 4번(`window` 객체)은 이벤트 객체의 속성과 무관한 오답이다.

**`target` vs `currentTarget` 비교**

```html
<div id="parent" style="padding: 20px; background: lightgray;">
  <button id="child">클릭하세요</button>
</div>
```

```js
var parent = document.getElementById("parent");

parent.addEventListener("click", function (event) {
    console.log("target:", event.target);
    console.log("currentTarget:", event.currentTarget);
});
```

`#child` 버튼을 클릭하면:

- `event.target` → `<button id="child">` — 실제로 클릭이 발생한 최하위 요소이므로 고정.
- `event.currentTarget` → `<div id="parent">` — 이 핸들러가 등록된 요소이므로, 버블링돼서 실행되고 있는 지금 이 시점 기준으로 `parent`가 된다.

**실무 활용 — 이벤트 위임(Event Delegation)**: `target`이 "실제로 클릭된 요소"를 정확히 짚어준다는 점을 이용해, `<ul>` 안에 `<li>`가 수십 개 있어도 각 `<li>`마다 핸들러를 달지 않고 부모 `<ul>` 하나에만 이벤트 리스너를 등록한 뒤 `event.target`으로 실제 클릭된 `<li>`를 판별할 수 있다. 이렇게 하면 핸들러 개수를 줄이고, 나중에 동적으로 추가된 `<li>`에도 별도 등록 없이 자동으로 반응하게 만들 수 있다.

tags: #웹 #자바스크립트 #이벤트 #target #currentTarget

> 🔗 관련 노트: [[052_자바스크립트와 브라우저 플랫폼 — 탄생 배경, DOM, 이벤트, 함수]] · [[053_DOM 노드 타입, 이벤트 객체, 스타일 속성과 CSS 단위]] · [[023_자바스크립트 계산기 실습 — DOM 속성 조작과 이벤트 위임]]
