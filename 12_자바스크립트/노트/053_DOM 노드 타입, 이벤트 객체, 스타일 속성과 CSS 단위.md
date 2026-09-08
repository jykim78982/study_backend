---
tags: [웹, 자바스크립트, DOM, 이벤트, CSS단위]
날짜: 2026-09-08
---

> 🔗 관련 노트: [[052_자바스크립트와 브라우저 플랫폼 — 탄생 배경, DOM, 이벤트, 함수]]

# DOM 노드 타입, 이벤트 객체, 스타일 속성과 CSS 단위

## 1. 모든 DOM 구성 요소는 `Node`를 물려받는다

문서(DOM)를 이루는 개체들은 태그뿐 아니라 속성, 텍스트, 주석까지 전부 **노드(Node)**라는 하나의 개념으로 통칭된다. 다만 노드는 추상화된 개념이라서, 실제로는 그 아래에 여러 구체적인 종류로 나뉜다.

```
Node
 ├ Element(1)
 ├ Attr(2)
 ├ Document(9)
 ├ DocumentType(10)
 ├ Notation(12)
 ├ EntityReference(5)
 ├ Entity(6)
 └ CharacterData
     ├ CDATASection(4)
     ├ Comment(8)
     └ Text(3)
```

- **Document(9)**: 노드들을 전부 담고 있는 최상위 그릇. `#document`가 여기 해당한다.
- **DocumentType(10)**: `<!DOCTYPE html ...>` 선언이 메모리에 올라간 형태.
- **Element(1)**: 우리가 흔히 아는 일반 태그(`<div>`, `<p>`, `<font>` 등)가 메모리에 올라간 형태.
- **Attr(2)**: 태그에 붙은 속성(`rows="30"` 등).
- **Entity(6)** / **EntityReference(5)**: `&lt;`, `&gt;`, `&nbsp;` 같은 문자 참조(엔티티) 관련 노드. 예를 들어 `&lt;뉴렉처&gt;&nbsp;`는 화면에는 `<뉴렉처>`(뒤에 빈칸 하나)로 보인다.
- **Comment(8)**: `<!-- 주석 -->`이 메모리에 올라간 형태.
- **CDATASection(4)**: `<![CDATA[ <, >, ] ]>`처럼 특수 문자를 그대로 담기 위한 구간.
- **Notation(12)**: 문서 내에 특수한 표기 형식이 들어가는 경우를 위한 노드로, 실무에서는 거의 쓰이지 않는다.
- **Text(3)**, **Comment(8)**, **CDATASection(4)**는 공통적으로 **CharacterData**라는 중간 단계를 물려받는다 — 셋 다 "문자 데이터를 담는다"는 공통점이 있기 때문이다.

## 2. `nodeType` / `nodeName` / `nodeValue` — 노드를 식별하는 세 속성

모든 노드는 종류와 상관없이 다음 세 가지 공통 속성을 갖는다.

```js
readonly attribute unsigned short nodeType;
readonly attribute DOMString nodeName;
readonly attribute DOMString nodeValue;
```

`nodeType`에는 노드 종류를 나타내는 숫자 상수가 담긴다.

```js
ELEMENT_NODE = 1;
ATTRIBUTE_NODE = 2;
TEXT_NODE = 3;
CDATA_SECTION_NODE = 4;
ENTITY_REFERENCE_NODE = 5;
ENTITY_NODE = 6;
COMMENT_NODE = 8;
DOCUMENT_NODE = 9;
DOCUMENT_TYPE_NODE = 10;
DOCUMENT_FRAGMENT_NODE = 11;
NOTATION_NODE = 12;
```

실무에서 실제로 비교할 일이 있는 것은 거의 `1`(엘리먼트)과 `3`(텍스트) 두 가지뿐이다.

`nodeName`과 `nodeValue`는 노드 종류에 따라 담기는 내용이 달라진다.

| 노드 종류 | nodeName | nodeValue |
|---|---|---|
| `Element` | 태그명 | `null` |
| `Attr` | 속성명 | 속성값 |
| `Text` | `#text` | 텍스트 내용 |
| `Comment` | `#comment` | 주석 내용 |
| `Document` | `#document` | `null` |

엘리먼트는 이름(태그명)은 있지만 값이 없고, 텍스트나 주석은 이름이 의미 없는 대신 값에 실제 내용이 담긴다는 점이 대조적이다.

`nodeName`으로 비교할 때 주의할 점 하나 — 태그명 비교값은 항상 **대문자**로 들어온다. `"input" === e.target.nodeName`처럼 소문자로 비교하면 절대 일치하지 않고, 반드시 `"INPUT"`처럼 대문자로 비교해야 한다.

## 3. 이벤트 객체로 조건 분기하기 — 조기 반환(early return) 패턴

`e.target.nodeName`을 이용하면 이벤트 위임 상황에서 특정 태그일 때만 로직을 실행하도록 걸러낼 수 있다. 이때 조건에 맞는 코드 전체를 `if` 블록으로 감싸는 방식보다, 조건에 맞지 않으면 먼저 함수를 빠져나가는 방식이 더 바람직하다.

```js
// 좋지 않은 방식 — 처리할 내용 전체를 if 블록으로 감싼다
box.onclick = function(e) {
    if (e.target.nodeName == "INPUT") {
        var value = txtInput.value;
        console.log(e.target.value);
        value += e.target.value;
        txtInput.value = value;
    }
};

// 바람직한 방식 — 조건에 안 맞으면 먼저 빠져나간다
var box = section.querySelector("div");
box.onclick = function(e) {
    if (e.target.nodeName != "INPUT") return;

    var value = txtInput.value;
    console.log(e.target.value);
    value += e.target.value;
    txtInput.value = value;
};
```

블록 안에 로직 전체를 감싸면 들여쓰기가 깊어지고 코드 흐름을 읽기 어려워지므로, 조건에 맞지 않는 경우를 먼저 걸러내고 나가는 흐름이 가독성 면에서 더 낫다.

타겟이 같은 엘리먼트인지 비교할 때는 노드 이름 대신 참조 자체를 비교할 수도 있다 — `e.target === 특정엘리먼트` 형태로 `===`(일치 연산자)를 쓰면 두 값이 같은 객체를 가리키는지 확인할 수 있다.

## 4. 태그의 기본 행위(Default Action)와 `preventDefault()`

`<a>`, `<button>`, `<input type="submit">` 같은 몇몇 태그는 브라우저가 자체적으로 처리하는 **기본 행위**를 갖고 있다 — `<a>`는 클릭 시 `href`로 이동하고, `submit` 버튼은 감싸고 있는 `<form>`의 `action`/`method`에 따라 서버로 요청을 보내며, 이 요청은 대개 페이지를 새로고침시킨다.

문제는 이 기본 행위가 자바스크립트로 등록한 이벤트 핸들러보다 우선해서 실행된다는 점이다. 예를 들어 `submit` 버튼에 클릭 이벤트를 걸어 화면 내용을 바꾸는 코드를 짜도, 클릭하는 순간 폼 전송(페이지 새로고침)이 함께 일어나 버려서 방금 적용한 변경 사항이 사라진 것처럼 보인다.

이 기본 행위를 막으려면 이벤트 객체가 제공하는 `preventDefault()` 메서드를 호출하면 된다.

```js
box.onclick = function(e) {
    e.preventDefault(); // 이 요소의 기본 행위(폼 전송, 링크 이동 등)를 막는다
    // ...나머지 로직
};
```

임시방편으로 `<a>`나 `submit` 버튼을 `<input type="button">`처럼 기본 행위가 없는 태그로 바꿔서 문제를 피해가는 방법도 있지만, 이는 태그가 원래 갖고 있어야 할 의미(시맨틱)를 깨뜨리는 것이므로 바람직하지 않다 — 기본 행위가 있는 태그는 그대로 쓰고, `preventDefault()`로 필요한 부분만 막는 것이 올바른 방법이다.

## 5. 버블링을 막는 `stopPropagation()`

이벤트 위임으로 부모에 핸들러 하나만 걸어둔 상황에서, 특정 자식 하나만 예외적으로 다른 동작을 시키고 싶을 때가 있다. 그 자식에게 별도로 핸들러를 하나 더 달아도, 클릭 시 그 자식의 핸들러와 버블링되어 올라간 부모의 핸들러가 **둘 다** 실행되어 버린다.

이때 자식의 핸들러가 부모까지 전파되지 않도록 막는 메서드가 `stopPropagation()`이다.

```js
button3.onclick = function(e) {
    e.stopPropagation(); // 이 이벤트가 부모로 버블링되는 것을 막는다
    alert("Hello");
};
```

`preventDefault()`가 "이 요소의 기본 행위 자체를 막는 것"이라면, `stopPropagation()`은 "이 이벤트가 조상들에게 전파(버블링)되는 것을 막는 것"이라는 차이가 있다.

## 6. 스타일 속성을 다룰 때 주의할 점

### 6-1. 하이픈이 들어간 CSS 속성명은 점(`.`) 표기로 쓸 수 없다

```js
txt1.style.background-color = "red"; // 불가능 — "background 빼기 color"로 해석됨
```

CSS 속성명에 있는 하이픈(`-`)은 자바스크립트에서 뺄셈 연산자로 해석되기 때문에, 점 표기법으로는 하이픈이 든 속성을 쓸 수 없다. 해결 방법은 두 가지다.

```js
// 1. 대괄호 + 문자열로 속성명을 그대로 사용
txt1.style["background-color"] = "red";

// 2. 카멜케이스로 변환된 속성명 사용
txt1.style.backgroundColor = "red";
```

자바스크립트 객체는 원래 점 표기법 대신 대괄호와 문자열로도 속성에 접근할 수 있는데(`obj["속성명"]`), 이 방식을 이용하면 하이픈처럼 식별자로 쓸 수 없는 문자가 포함된 이름도 그대로 쓸 수 있다. 동시에 CSS 스타일 객체는 자바스크립트에서 쓰기 편하도록 하이픈을 없앤 카멜케이스 이름(`backgroundColor`)도 함께 제공한다.

### 6-2. 스타일 값은 반드시 단위가 붙은 문자열이어야 한다

```js
txt1.style.width = 100;      // 불가능 — 스타일 값에 숫자는 올 수 없다
txt1.style.width = "100";    // 불가능 — 단위가 없어서 적용되지 않는다
txt1.style.width = "100px";  // 올바른 형식
```

CSS 스타일 속성의 값은 항상 문자열이어야 하며, 크기를 나타내는 값에는 반드시 단위(`px`, `em` 등)가 붙어야 한다. 숫자만 대입하거나 단위 없는 문자열만 대입하면 값이 적용되지 않는다.

## 7. CSS 단위 — 고정 크기와 가변(상대) 크기

- **고정 크기**: `in`, `px`, `pt`, `pc`, `cm`, `mm` — 화면 밀도나 부모 요소와 상관없이 지정한 크기 그대로 고정된다.
- **가변(상대) 크기**: `rem`, `em`, `ex`, `vh`, `vw` — 기준이 되는 다른 값에 따라 상대적으로 크기가 정해진다.

`em`은 **부모 요소의 `font-size`**를 기준으로 한 배수다. `font-size`는 CSS 속성 중 자식에게 **상속**되는 몇 안 되는 속성이라서(대부분의 속성은 상속되지 않는다), 부모의 `font-size`가 바뀌면 그 영향이 자식에게도 전달되고, 자식이 `em` 단위로 지정한 크기도 함께 달라진다. 예를 들어 부모 `font-size`가 `10px`이고 자식이 `height: 2em`이면 실제 높이는 `20px`이 되고, 부모의 `font-size`를 `30px`로 늘리면 자식의 높이도 자동으로 `60px`로 함께 커진다 — 콘텐츠 크기가 커질 때 박스 크기를 매번 따로 조정하지 않아도 되게 하려는 것이 `em`을 쓰는 이유다.

단, `<input>`처럼 일부 요소는 예외적으로 부모의 `font-size`를 상속받지 않으므로, 그런 요소에 `em`을 써도 부모의 `font-size` 변화에 영향을 받지 않는다.

`rem`(Root em)은 `em`과 달리 **가장 가까운 부모가 아니라 문서 최상위(`<html>` 태그)에 설정된 `font-size`**를 기준으로 한다. 중간에 낀 부모들의 `font-size`와는 무관하게, 오직 `html` 요소에 지정한 값만 따른다.

```css
html { font-size: 16px; }
.box { height: 2rem; } /* 항상 32px — 중간 부모의 font-size와 무관 */
```

인쇄용 화면(프린트 레이아웃)을 만들 때는 `px` 대신 `cm`/`mm`/`in`을 써야 한다. 화면 픽셀과 프린터 잉크 해상도(밀도)가 서로 다르기 때문에, `px`로 지정한 크기는 화면과 인쇄물에서 실제 크기가 다르게 나온다 — 반면 `cm`/`mm`/`in`은 출력 장치와 무관하게 실제 물리적 크기를 그대로 맞춰준다.
