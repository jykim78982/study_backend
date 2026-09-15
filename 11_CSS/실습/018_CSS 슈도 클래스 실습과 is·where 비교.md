---
tags: [웹, CSS, 슈도클래스, is, where, has, 실습]
---

> 🔗 관련 노트: [[048_CSS 콤비네이터·우선순위 심화, 슈도 클래스·엘리먼트, 함수]] · [[015_CSS 속성 선택자 실습]] · [[016_CSS 결합자 실습]] · [[017_CSS 결합자·우선순위 테스트]]

# CSS 슈도 클래스 실습과 :is()·:where() 비교

`publishing/css/step1/ex4-pseudo-lab.html` 실습. 슈도 클래스를 4개 카테고리(사용자 동작, 폼 상태, 구조, 모던 논리)로 나눠 실무 UI 패턴 16개를 하나씩 만들어봤다.

## 가상 클래스 핵심 분류 체계

| 카테고리 | 핵심 가상 클래스 | 실무 적용 시나리오 |
|---|---|---|
| 1. 사용자 동작 및 접근성 | `:hover`, `:active`, `:focus-visible`, `:focus-within` | 마우스 피드백, 키보드 접근성(A11y), 입력 폼 그룹 하이라이트 |
| 2. 폼 상태 및 입력 검증 | `:placeholder-shown`, `:valid`, `:invalid`, `:checked`, `:disabled`, `:read-only` | 플로팅 라벨, 인라인 유효성 검사, 커스텀 토글/체크박스 |
| 3. 구조 및 트리 위치 | `:first-child`, `:last-child`, `:nth-child()`, `:nth-of-type()`, `:empty` | 데이터 테이블 제브라 패턴, 태그 배지 그리드, 빈 상태(Empty State) |
| 4. 최신 모던 논리 선택자 | `:not()`, `:is()`, `:where()`, `:has()` | 특정 요소 제외, 선택자 경량화, 부모 컨테이너 상태 제어 |

## [카테고리 1] 사용자 동작 및 인터랙션

### 01. `:hover` — 마우스 진입

```css
.btn-hover:hover {
  background: #2563eb;
  color: #ffffff;
}
```

- **목적**: 마우스 포인터가 요소 위에 올라왔을 때 스타일을 바꾼다.
- **동작 확인**: 버튼에 마우스를 올리는 즉시 파란 배경과 흰 글자로 전환된다.

### 02. `:active` — 클릭 압력

```css
.btn-active:active {
  background: #cbd5e1;
  transform: scale(0.92);
}
```

- **목적**: 마우스 왼쪽 버튼을 누르고 있는 그 순간만을 감지한다.
- **동작 확인**: 버튼을 누르고 있는 동안 크기가 살짝 작아지며(`scale(0.92)`) 눌리는 물리적 느낌을 준다.

### 03. `:focus` vs `:focus-visible` — 키보드 접근성 분리

```css
/* 마우스 클릭이든 키보드든 무조건 발동 */
.btn-focus:focus {
  outline: 2px solid #ef4444;
}
/* 마우스 클릭 시에는 안 보이고, 키보드 Tab 키로 이동했을 때만 발동 */
.btn-focus-visible:focus {
  outline: none;
}
.btn-focus-visible:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}
```

- **목적**: 마우스 클릭 시 생기는 불필요한 포커스 테두리는 지우고, 키보드로 `Tab` 이동할 때만 접근성 링을 보여준다.
- **동작 원리**: `.btn-focus`는 `:focus`만 걸어서 마우스로 클릭해도 빨간 테두리가 뜬다. `.btn-focus-visible`은 `:focus`로 기본 아웃라인을 지워버리고, `:focus-visible`로만 파란 아웃라인을 다시 그린다 — 이 둘의 조합으로 "키보드 사용자에게만" 접근성 표시를 보여준다.
- **동작 확인**: 마우스로 두 버튼을 클릭해보면 `btn-focus`만 빨간 테두리가 뜬다. `Tab` 키로 이동하면 `btn-focus-visible`에만 파란 아웃라인이 뜬다.

### 04. `:focus-within` — 자식 포커스 감지, 부모 활성화

```css
.form-container:focus-within {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}
```

- **목적**: 자식 요소가 포커스를 받았을 때 부모 래퍼 전체의 스타일을 바꾼다.
- **동작 원리**: `input`은 `.form-container` 안에 있는 자식이다. 이 `input`에 포커스가 들어가면, 슈도 클래스가 자식이 아니라 **부모인 `.form-container`에** 적용된다.
- **동작 확인**: 입력 필드를 클릭하면 바깥 부모 박스의 테두리가 파란색으로, 그림자가 함께 반응한다.

## [카테고리 2] 폼 상태 및 입력 검증

### 05. `:placeholder-shown` — 플레이스홀더 노출 여부

```css
.input-placeholder:placeholder-shown {
  border-color: #cbd5e1;
  background-color: #ffffff;
}
.input-placeholder:not(:placeholder-shown) {
  border-color: #2563eb;
  background-color: #eff6ff;
}
```

- **목적**: 자바스크립트 없이 순수 CSS만으로 입력창이 비어 있는지(플레이스홀더가 보이는 상태인지)를 감지한다.
- **동작 원리**: 글자가 하나도 없어서 플레이스홀더가 보이는 동안은 `:placeholder-shown`이 걸리고, 사용자가 한 글자라도 입력하면 플레이스홀더가 사라지므로 `:not(:placeholder-shown)`이 걸린다.
- **동작 확인**: 글자를 입력하면 배경이 연한 파란색으로 바뀌고 테두리가 진한 파란색으로 활성화된다.

### 06. `:valid` & `:invalid` — 양식 무결성 검증

```css
.input-validation:invalid { border-color: #ef4444; }
.input-validation:valid { border-color: #10b981; }
```

- **목적**: `type="email"`, `required` 같은 HTML5 검증 속성과 연동해서 실시간으로 시각 피드백을 준다.
- **동작 확인**: 이메일 형식을 온전히 갖추기 전까지는 빨간 테두리(`:invalid`)가, `@`와 도메인까지 완성하는 순간 초록 테두리(`:valid`)로 바뀐다.

### 07. `:checked` — 선택 상태 제어

```css
.cb-target:checked + .cb-label {
  color: #2563eb;
  font-weight: bold;
  text-decoration: underline;
}
```

- **목적**: 체크박스·라디오 버튼의 켜짐/꺼짐 상태를 다른 요소의 스타일과 연동한다.
- **동작 원리**: 체크박스 자신이 아니라, **인접 형제 결합자(`+`)로 옆에 있는 `.cb-label`**을 타겟팅한다. 체크박스가 켜졌을 때만 그 형제 라벨이 스타일을 받는다.
- **동작 확인**: 체크박스를 켜면 옆의 안내 텍스트가 굵은 파란색 밑줄로 바뀐다.

### 08. `:disabled` & `:read-only` — 비활성 vs 읽기 전용 구분

```css
.input-disabled:disabled {
  background: #f1f5f9;
  color: #94a3b8;
  border: 1px dashed #cbd5e1;
  cursor: not-allowed;
}
.input-readonly:read-only {
  background: #fefce8;
  border: 1px solid #fde047;
  color: #713f12;
}
```

- **목적**: "완전히 수정 불가능한 상태(`disabled`)"와 "값은 보이지만 고칠 수 없는 상태(`readonly`)"를 시각적으로 다르게 구분한다.
- **동작 확인**: `disabled` 필드는 회색 점선 테두리와 금지 커서로, `readonly` 필드는 연노란 배경으로 표시되어 한눈에 다른 상태임을 알 수 있다.

## [카테고리 3] 구조 및 트리 위치

### 09. `:first-child` & `:last-child` — 경계 요소 처리

```css
.list-edges li:first-child {
  background: #eff6ff;
  font-weight: bold;
}
.list-edges li:last-child {
  border-bottom: none;
}
```

- **목적**: 목록의 첫 번째·마지막 항목의 여백이나 테두리를 정리한다.
- **동작 확인**: 첫 번째 항목만 파란 배경과 굵은 글씨가 적용되고, 마지막 항목은 아래쪽 구분선이 제거돼 목록 전체 테두리와 겹치지 않는다.

### 10. `:nth-child()` — 수열 규칙 반복

```css
.list-striped li:nth-child(even) { background: #f1f5f9; }
.list-striped li:nth-child(3n) { color: #dc2626; font-weight: bold; }
```

- **목적**: 짝수/홀수 패턴이나 `An+B` 형태의 수열로 반복 요소를 선택한다.
- **동작 확인**: 2행·4행(짝수 번째)에는 회색 줄무늬 배경이, 3행(3의 배수 번째)에는 빨간 굵은 글씨가 적용된다. 두 규칙이 동시에 해당하는 행이 없어서 겹치는 케이스는 이 예제에서는 발생하지 않는다.

### 11. `:nth-of-type()` — 동일 태그 기준 순번 계산

```css
.type-container p:nth-of-type(1) {
  color: #2563eb;
  font-weight: bold;
}
```

- **목적**: 다른 태그가 섞여 있어도, 지정한 태그(`p`)들 사이에서만 순번을 센다.
- **동작 원리**: `.type-container` 안에는 `h3` 1개와 `p` 2개가 있다. `:nth-of-type(1)`은 `h3`를 순번에 넣지 않고, `p`들 중 첫 번째("문단 1")만 순번 1로 센다. 실습 가이드 원문은 `:nth-of-type(2)`(두 번째 `p`, "문단 2")를 예시로 들었지만, 실제 작성한 코드는 `:nth-of-type(1)`이라 "문단 1"이 파란 글씨가 된다.
- **`:nth-child()`와의 차이**: `:nth-child()`는 태그 종류에 상관없이 형제 전체를 기준으로 순번을 센다. 만약 `:nth-child(1)`을 썼다면 첫 번째 자식인 `h3`가 걸렸을 것이다 — 형제 전체 순번이냐, 같은 태그 안에서의 순번이냐가 두 슈도 클래스의 핵심 차이다.
- **동작 확인**: "문단 1"만 파란 굵은 글씨가 되고, "제목"과 "문단 2"는 그대로 남는다.

### 12. `:empty` — 내용이 빈 태그 처리

```css
.empty-box:empty {
  background: #fee2e2;
  border: 1px dashed #ef4444;
}
.empty-box:empty::before {
  content: "(데이터가 비어 있습니다)";
  color: #dc2626;
  font-size: 12px;
}
```

- **목적**: 텍스트든 자식 요소든 공백까지 포함해 아무 내용도 없는 요소를 감지해서, 빈 상태(Empty State) 안내를 자동으로 보여준다.
- **동작 원리**: `:empty`로 상태를 감지하고, `::before` 슈도 엘리먼트로 안내 문구를 실제 HTML 수정 없이 삽입한다 — `[[048_CSS 콤비네이터·우선순위 심화, 슈도 클래스·엘리먼트, 함수]]` 6절에서 다룬 "데코레이션은 슈도 엘리먼트로" 원칙이 그대로 적용된 사례다.
- **동작 확인**: 내용이 있는 첫 번째 박스는 그대로지만, 내용이 없는 두 번째 박스는 빨간 점선 테두리와 함께 "(데이터가 비어 있습니다)" 문구가 자동으로 나타난다.

## [카테고리 4] 모던 논리 및 관계 선택자

### 13. `:not()` — 부정 조건 필터링

```css
.tag.special { background: #7c3aed; color: #ffffff; }
.tag:not(.special) { background: #f1f5f9; color: #64748b; }
```

- **목적**: 특정 클래스를 가진 요소만 제외하고 나머지 전체를 한 번에 선택한다.
- **동작 확인**: `.special` 태그만 보라색으로 강조되고, 나머지 일반 태그들은 `:not(.special)`에 걸려 회색 톤으로 일괄 처리된다.

### 14. `:is()` — 중복 축소 그룹화

```css
.group-is :is(h3, p, span) {
  color: #0d9488;
  letter-spacing: 0.5px;
}
```

- **목적**: `.group-is h3`, `.group-is p`, `.group-is span`처럼 반복되는 부분을 괄호로 묶어서 코드량을 줄인다.
- **동작 확인**: `h3`, `p`, `span` 세 태그 모두 청록색(`#0d9488`)으로 한 번에 적용된다.

### 15. `:where()` — 명시도 0점 리셋

```css
:where(.group-where) a {
  color: #9333ea;
}
a {
  color: #16a34a;
}
```

- **목적**: 선택자를 그룹으로 묶되, 명시도는 전혀 올리지 않아서 나중에 훨씬 단순한 선택자로도 쉽게 덮어쓸 수 있게 한다.
- **동작 원리**: `:where(.group-where)`는 괄호 안에 `.group-where`가 있어도 명시도를 0으로 취급한다. 그래서 `:where(.group-where) a`의 실질 명시도는 `a` 태그 하나(1점)와 같아진다. 뒤이어 선언한 단순한 `a { color: #16a34a; }`도 똑같이 1점이라, **명시도가 같으면 나중 선언이 이긴다**는 캐스케이딩 규칙에 따라 나중에 온 `a` 규칙이 이긴다.
- **동작 확인**: 링크가 보라색(`:where()` 규칙)이 아니라 초록색(나중에 선언된 단순 `a` 규칙)으로 표시된다.

### 16. `:has()` — 부모 요소 역방향 선택

```css
.parent-card:has(.toggle-card:checked) {
  background: #f0fdf4;
  border-color: #22c55e;
}
.parent-card:has(.toggle-card:checked) .desc {
  color: #15803d;
  font-weight: bold;
}
```

- **목적**: 지금까지의 결합자·슈도 클래스는 모두 "부모 → 자식" 또는 "형 → 동생" 방향으로만 선택할 수 있었는데, `:has()`는 **자식의 상태를 보고 부모를 선택**하는 역방향 선택을 가능하게 한다.
- **동작 원리**: `.parent-card` 안에 있는 `.toggle-card`가 체크된 상태(`:checked`)인지를 부모 기준에서 검사한다. 체크되어 있으면 부모 카드 전체와, 그 안의 `.desc` 문단까지 스타일이 함께 바뀐다.
- **동작 확인**: 체크박스를 켜면 자바스크립트 없이도 부모 카드의 배경·테두리와 하위 설명 글자색이 한꺼번에 전환된다.

## `:is()` vs `:where()` — 명시도 계산 비교

두 함수 모두 선택자를 괄호로 묶어 그룹화한다는 점은 같지만, **명시도를 계산하는 방식이 정반대**다.

| 구분 | `:is()` | `:where()` |
|---|---|---|
| 명시도 | 괄호 안에서 **가장 높은** 선택자의 점수를 그대로 적용 | 괄호 안에 무엇이 오든 **항상 0점** |
| 핵심 동작 | 약한 선택자도 최강 선택자 점수로 부풀려짐 | 점수 변동 없이 순수 그룹화·스타일 초기화에 유리 |
| 덮어쓰기 난이도 | 점수가 높아질 수 있어 나중에 다른 규칙으로 덮어쓰기 어려움 | 0점이라 단일 태그·클래스만으로도 쉽게 덮어씀 |

```css
/* 1. 일반 쉼표 그룹화 — 각자 본래 점수 유지 */
.group h3,
.group p,
.group #id { color: red; }
/* h3: 11점(.group 10 + h3 1) */
/* p:  11점(.group 10 + p 1) */
/* #id: 110점(.group 10 + #id 100) */

/* 2. :is() 사용 — 괄호 안 최고점(#id=100)에 맞춰 전부 인상 */
.group :is(h3, p, #id) { color: red; }
/* h3, p, #id 전부 110점(.group 10 + 100) */

/* 3. :where() 사용 — 괄호 안이 전부 0점으로 처리 */
.group :where(h3, p, #id) { color: red; }
/* h3, p, #id 전부 10점(.group 10 + 0) */
```

- **실무 적용 요약**
  - 점수 인상 없이 코드만 깔끔하게 그룹화하고 싶을 때 → `:where()`가 가장 안전하다.
  - 특정 그룹 전체에 확실히 높은 우선순위를 한 번에 부여하고 싶을 때 → `:is()`를 활용한다.
- **관대한 구문 분석**: 두 함수 모두 괄호 안에 유효하지 않거나 오타가 난 선택자가 섞여 있어도, 나머지 정상적인 선택자는 무시되지 않고 그대로 동작한다.
- 위 15번 실습(`:where(.group-where) a`)이 바로 이 표의 3번 케이스에 해당한다 — 명시도가 0으로 리셋되기 때문에, 나중에 온 아주 단순한 `a` 선택자에조차 쉽게 덮어써졌다.
