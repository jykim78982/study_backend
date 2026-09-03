---
tags: [웹, CSS, position, 실습]
---

> 🔗 관련 노트: [[051_CSS — 배경 이미지·컬러·마스크·인라인 박스·포지션]] · [[050_플렉스박스 아이템 속성과 박스 사이징]]

# CSS position 속성 실습

`publishing/css/position/position.html` 실습. `position: static`(기본)을 제외한 네 가지 값(`relative`/`absolute`/`fixed`/`sticky`)을 `.box-2`(파랑) 하나에 순서대로 적용해보며 차이를 확인했다.

## 기본 베이스 코드

모든 단계의 기준이 되는 초기 마크업. `body`에 `height: 300vh`를 줘서 스크롤이 생기도록 했다.

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>CSS Position 실습</title>
  <style>
    body {
      margin: 0;
      padding: 20px;
      height: 300vh; /* 스크롤 관찰용 높이 */
      font-family: sans-serif;
    }
    .wrapper {
      width: 400px;
      height: 300px;
      border: 3px dashed #333;
      margin: 40px auto;
      background-color: #f0f0f0;
    }
    .box {
      width: 100px;
      height: 100px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      color: white;
    }
    .box-1 { background-color: #e74c3c; } /* 빨강 */
    .box-2 { background-color: #3498db; } /* 파랑 (실습 대상) */
    .box-3 { background-color: #2ecc71; } /* 초록 */
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="box box-1">1</div>
    <div class="box box-2">2</div>
    <div class="box box-3">3</div>
  </div>
</body>
</html>
```

초기 상태에서는 세 박스 모두 `position: static`(기본값)이라 문서 흐름대로 세로로 나란히 배치된다.

## Step 1. `position: relative` — 상대 위치

```css
.box-2 {
  background-color: #3498db;
  position: relative;
  top: 30px;
  left: 50px;
}
```

- **동작**: 파란 박스(2번)가 원래 위치에서 아래로 30px, 오른쪽으로 50px 이동한다.
- **핵심 특징**: `relative`는 **자신이 원래 있어야 할 자리를 기준으로** 좌표만큼 이동한다. 2번 박스가 이동했는데도 3번 박스는 밀려나거나 올라오지 않는다 — 2번 박스가 원래 차지하던 공간(고스트 스페이스, ghost space)이 그대로 남아 있기 때문이다.

## Step 2. `position: absolute` — 절대 위치

### 기준점(offset parent)이 없을 때

```css
.box-2 {
  background-color: #3498db;
  position: absolute;
  top: 0;
  right: 0;
}
```

- **동작**: 파란 박스가 `.wrapper`가 아니라 **브라우저 화면(뷰포트) 맨 오른쪽 상단**으로 날아간다.
- **핵심 특징**: `absolute`는 문서 흐름에서 완전히 벗어나며(자리를 아예 비워버림), 2번 박스가 빠진 자리를 3번 초록 박스가 그대로 채워 1번 박스 바로 아래로 올라온다.

### 기준점 부여하기 — 부모에 `position: relative`

```css
.wrapper {
  position: relative; /* absolute의 기준점 설정 */
  width: 400px;
  height: 300px;
  border: 3px dashed #333;
  margin: 40px auto;
  background-color: #f0f0f0;
}
```

- **원리**: `absolute` 요소는 좌표 기준점을 지정하지 않으면 문서의 좌/상단 꼭짓점을 기준으로 삼는다. 하지만 부모나 조상 중에 `position`이 `relative`(또는 `absolute`)로 설정된 요소가 있으면, 그 요소가 **옵셋 영역(offset parent)**이 되어 자식의 좌표 기준이 그 요소의 좌/상단 꼭짓점으로 바뀐다.
- **동작**: `.wrapper`에 `position: relative`를 추가하면, 파란 박스가 이제 화면 전체가 아니라 회색 테두리 상자(`.wrapper`)의 오른쪽 상단 모서리에 정확히 고정된다.
- **핵심 특징**: `absolute` 요소는 `static`이 아닌(보통 `relative`가 걸린) **가장 가까운 조상**을 찾아 기준점으로 삼는다.

## Step 3. `position: fixed` — 화면 고정 위치

```css
.box-2 {
  background-color: #3498db;
  position: fixed;
  bottom: 20px;
  right: 20px;
}
```

- **동작**: 파란 박스가 화면 오른쪽 하단 구석에 배치된다.
- **핵심 특징**:
  - `.wrapper`의 테두리 바깥으로 완전히 이탈한다 — 부모 요소와 무관하게 항상 **브라우저 창(뷰포트)**을 기준으로 고정된다.
  - 마우스 휠로 페이지를 스크롤해도 2번 박스는 화면의 고정된 위치에 그대로 머무른다.
  - 웹사이트의 "상단으로 이동" 버튼이나 플로팅 배너 제작에 사용된다.

## Step 4. `position: sticky` — 스크롤 임계점 고정

평소에는 일반 흐름을 따르다가, 스크롤이 특정 위치에 도달하면 `fixed`처럼 화면에 달라붙는다. `.box-2`를 되돌리는 대신, 독립적인 내비게이션 바로 따로 테스트했다.

`<body>` 바로 아래에 요소 추가:

```html
<body>
  <div class="sticky-bar">STICKY NAV BAR</div>

  <div class="wrapper">
    ...
```

`<style>`에 규칙 추가:

```css
.sticky-bar {
  background-color: #f39c12;
  color: white;
  padding: 15px;
  text-align: center;
  font-weight: bold;

  position: sticky;
  top: 0; /* 스크롤 시 화면 상단 0 위치에 닿으면 고정 */
}
```

- **동작**:
  - 처음에는 페이지 상단에 일반 텍스트 블록처럼 위치한다.
  - 아래로 스크롤하다가 상단 테두리가 화면 상단(`top: 0`)에 닿는 순간, 스크롤을 더 내려도 그 자리에 붙어 움직이지 않는다.
- **주의 사항**: `sticky`가 동작하려면 `top`/`bottom`/`left`/`right` 중 최소 하나 이상의 임계점 값이 반드시 지정되어야 한다. 또한 `sticky`는 **부모 요소의 범위 안에서만** 적용되므로, 부모 요소의 높이가 끝나면 함께 스크롤되어 화면 밖으로 사라진다.

## 실제 실습 코드 — `position.html` (주석 토글 방식)

실습 파일에서는 단계마다 파일을 새로 만들지 않고, 한 파일 안에서 `.box-2`·`.box-3`·`.wrapper`의 CSS를 주석으로 켰다 껐다 하며 네 가지 값을 순서대로 확인했다.

```css
.wrapper {
  width: 400px;
  height: 300px;
  border: 3px dashed #333;
  margin: 40px auto;
  background-color: #f0f0f0;

  /* position: relative; */
  /* 자식 박스의 포지션이 absolute로 설정되었을 때
  부모, 또는 조상의 포지션을 relative로 설정하면
  옵셋 영역으로 설징이 됨 */
}
.box-2 {
    background-color: #3498db;
    /* 파랑 (실습 대상) */
    /* position: relative;
    top: 30px;
    left: 50px; */
    /* 현재 위치를 기준으로 이동
     - 원래 차지하던 공간(Ghost Space)이 유지됨 */

    /* position: absolute;
    top: 0;
    right: 0; */
    /* 기준점이 없을 때 문서의 좌표를 기준으로 이동 */
    /* 부모 또는 조상중에 포지션을 absolute, relative로
    설정한 박스가 있으면 그 박스가 좌표의 기준이 됨 */

    /* position: fixed;
    bottom: 20px;
    right: 20px; */
    /* 현재 보이는 브라우저 화면의 해당 위치에 고정됨
    스크롤 해도 해당 박스는 고정된 위치에 있음
    웹사이트의 '상단으로 이동' 버튼, '플로팅 배너' */
}
.box-3 {
    background-color: #2ecc71;
    /* 초록 */
    /* position: sticky;
    top: 0; */
    /* sticky는 부모 요소의 범위 내에서만 적용됨
    부모 요소의 높이가 끝나면 스크롤 되어서 화면을 벗어남 */
}
.sticky-bar {
    background-color: #f39c12;
    color: white;
    padding: 15px;
    text-align: center;
    font-weight: bold;

    position: sticky;
    top: 0;
    /* 스크롤 시 화면 상단 0 위치에 닿으면 고정 */
}
```

가이드 문서와 다르게, 실제 파일에서는 `sticky` 테스트를 `.box-2`가 아니라 `.box-3`(초록)의 주석 처리된 코드로도 남겨뒀다 — `.sticky-bar`가 실질적인 sticky 테스트 대상이고, `.box-3`의 주석은 "같은 속성을 다른 요소에도 적용해보면 부모 범위 제약이 어떻게 나타나는지" 참고용으로 남겨둔 메모로 보인다.

## 차이점 요약

| 값 | 원래 자리 | 좌표 기준 | 스크롤 동작 |
|---|---|---|---|
| `relative` | 그대로 보존(고스트 스페이스 유지) | 자기 자신의 원래 위치 | 문서 흐름을 따라 같이 스크롤 |
| `absolute` | 완전히 사라짐(다른 요소가 채움) | 가장 가까운 `relative`(또는 `absolute`) 조상, 없으면 문서 | 그 기준 요소와 함께 스크롤 |
| `fixed` | 완전히 사라짐 | 브라우저 창(뷰포트) | 스크롤해도 고정, 움직이지 않음 |
| `sticky` | 평소엔 `relative`처럼 유지 | 스크롤 도달 전은 원래 자리, 도달 후는 `fixed`처럼 고정 | 임계점(`top`/`bottom` 등) 전엔 흐름을 따르다가, 도달하면 화면에 붙음. 부모 범위를 벗어나면 다시 스크롤되어 사라짐 |

- `relative`: 원래 내 자리 보존 + 내 자리를 기준으로 살짝 이동.
- `absolute`: 내 자리 사라짐(붕 뜸) + `relative` 부모를 기준으로 원하는 곳에 강제 배치.
- `fixed`: 내 자리 사라짐(붕 뜸) + 화면 창(뷰포트) 기준으로 완전히 고정되어 스크롤되지 않음.
- `sticky`: 스크롤 전에는 `relative`처럼 동작하다가, 특정 스크롤 지점 도달 시 `fixed`처럼 화면에 달라붙음.
