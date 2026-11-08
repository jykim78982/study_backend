---
tags: [자바스크립트, typeof, 자료형, 오답노트]
---

# typeof 연산자 오답노트

### 1. typeof 연산자가 반환하는 값과 관련된 진술로 옳지 않은 것은?

**문제**: `typeof` 연산자가 반환하는 값과 관련된 진술로 옳지 않은 것은?

1. `typeof undefined`는 `'undefined'`를 반환한다
2. `typeof []`는 `'array'`를 반환한다
3. `typeof 3`은 `'number'`를 반환한다
4. `typeof null`은 `'object'`를 반환한다

**정답: 2번 (옳지 않은 것)**

- 배열은 자바스크립트에서 독립된 데이터 타입이 아니라 **객체(Object)의 한 종류**다. 그래서 `typeof []`는 `'array'`가 아니라 `'object'`를 반환한다. 정확히 배열인지 확인하려면 `typeof` 대신 `Array.isArray([])`를 써야 한다.

  ```js
  console.log(typeof []);        // "object"
  console.log(Array.isArray([])); // true
  ```

- **1번은 옳은 설명**: `undefined`는 그 자체가 고유한 타입이라, `typeof undefined`는 `'undefined'`를 반환한다.
- **3번은 옳은 설명**: 정수든 실수든 자바스크립트는 숫자를 하나의 `Number` 타입으로 통일해서 다루므로 `typeof 3`은 `'number'`다.
- **4번은 옳은 설명(단, 언어 설계상의 결함)**: `typeof null`은 `'null'`이 아니라 `'object'`를 반환한다. 이는 자바스크립트 초창기 구현의 버그로 알려져 있는데, 이미 너무 많은 웹사이트가 이 동작에 의존하게 되어 지금까지도 고쳐지지 못하고 그대로 유지되고 있는 대표적인 언어적 결함이다.

**참고 — `typeof`로 정확히 구분되지 않는 것들**

| 값 | `typeof` 결과 | 비고 |
|---|---|---|
| `[]` (배열) | `"object"` | `Array.isArray()`로 별도 확인 필요 |
| `null` | `"object"` | 역사적 버그, `=== null`로 직접 비교해야 함 |
| `new String("a")` | `"object"` | 리터럴 `"a"`는 `"string"`으로 구분됨 |

이처럼 `typeof`는 배열·`null`·래퍼 객체를 세밀하게 구분해주지 못하므로, 정확한 타입 판별이 필요할 때는 `Array.isArray()`나 `=== null` 같은 별도의 검사를 함께 써야 한다.

tags: #웹 #자바스크립트 #typeof #배열 #null

> 🔗 관련 노트: [[055_자바스크립트 데이터 타입 — 원시값과 래퍼 객체, 배열, 객체, JSON]]
