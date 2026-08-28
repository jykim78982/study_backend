---
tags: [웹, HTML, 태그, 블록태그, 인라인태그, 참고자료]
---

> 🔗 관련 노트: [[045_인라인·인라인블록 태그]] · [[047_인라인 태그 27종 — 쓰임과 예문]]

# HTML 블록·인라인 태그 분류표

[[045_인라인·인라인블록 태그]]에서 다루는 분류의 실제 태그 목록·계층 구조를 정리한 참고자료.

## 1. 블록 태그 계층 구조

```
div
├── table
│   ├── thead
│   └── tbody
│       └── tr
│           └── td
├── ul, ol, dl
│   ├── ol
│   ├── ul
│   └── dl
└── form
    └── fieldset
```

- `div`가 가장 범용적인 블록 태그이고, 그 아래로 표 관련 태그(`table`→`thead`/`tbody`→`tr`→`td`), 목록 관련 태그(`ul`/`ol`/`dl`), 폼 관련 블록 태그(`form`→`fieldset`)가 각각 하위 계층을 이룬다.

## 2. MDN 기준 인라인 요소 전체 목록

```
a, abbr, acronym, audio, b, bdi, bdo, big, br, button,
canvas, cite, code, data, datalist, del, dfn, em, embed,
i, iframe, img, input, ins, kbd, label, map, mark, meter,
noscript, object, output, picture, progress, q, ruby, s,
samp, script, select, slot, small, span, strong, sub, sup,
svg, template, textarea, time, tt, u, var, video, wbr
```

(HTML5는 엄밀히는 블록/인라인 요소를 구분하지 않고 "컨텐츠 카테고리"로 정의하지만, 실무 관점에서는 여전히 이 목록을 인라인 요소로 취급한다.)

## 3. 인라인 레벨 태그 카테고리

| 분류 | 태그 |
|---|---|
| 의미를 부여하는 태그 | `a`, `map`, `del`, `s`, `ins`, `kbd`, `data`, `var`, `time`, `abbr`, `dfn`, `cite`, `q`, `samp`, `mark`, `figcaption` |
| 스타일을 위주로 하는 태그 | `sup`, `sub`, `small`, `bdi`, `bdo`, `u`, `i`, `b`, `br`, `wbr` |
| 사용하지 않는(폐기) 태그 | `acronym`, `embed`, `tt`, `big`, `object` |
| Form 관련 태그 | `input`, `button`, `textarea`, `progress`, `output`, `label`, `datalist`, `select`, `meter`, `template` |
| 콘텐츠 태그 | `img`, `picture`, `iframe`, `slot` |
| 멀티미디어·API 태그 | `noscript`, `script`, `audio`, `video`, `svg` |

- 범용 인라인 태그인 `span`은 특정 의미가 없어 위 어느 분류에도 속하지 않고, 스타일 타겟팅 전용으로 별도 취급한다.

## 4. CSS 이전 시절 스타일 태그의 재정의된 의미

| 태그 | 약어 풀이 |
|---|---|
| `<u>` | **U**narticulated Annotation |
| `<i>` | **I**diomatic |
| `<b>` | **B**ring Attention |
| `<s>` | **S**trikethrough |
| `<br>` | Line **Br**eak |
| `<em>` | stress emphasis of its contents |
| `<strong>` | strong importance, seriousness, or urgency |
| `<del>` | **D**eleted from a document |
| `<wbr>` | **W**ord **Br**eak Opportunity |
