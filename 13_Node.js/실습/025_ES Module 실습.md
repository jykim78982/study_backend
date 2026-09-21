---
tags: [웹, 자바스크립트, Node.js, ES Module, 실습]
---

> 🔗 관련 노트: [[024_Node.js·npm 실습]]

# ES Module 실습

**대상**: [[024_Node.js·npm 실습|Node.js 모듈 시스템 — CommonJS 기초]]를 끝낸 사람

**목표**: ES Module의 `import`/`export` 문법을 배우고, CommonJS 프로젝트에서 배운 모듈 시스템을 ES Module로 전환하는 방법을 학습한다

**완성물**: `import`/`export`로 동작하는 `node-prj/` 프로젝트

**환경**: VSCode + 터미널(Mac: `Cmd + J`, Windows/Linux: `Ctrl + ~` 또는 Terminal 메뉴 → New Terminal)

**전제 조건**: CommonJS 실습을 끝냈다면, `~/node-prj/` 폴더에 아래 파일이 있어야 한다.

```
node-prj/
├── app.js              ← require('./math')로 math.js를 불러옴
├── math.js             ← exports.add = add; exports.sub = sub;
├── package.json
├── package-lock.json
└── node_modules/
```

VSCode 터미널에서 확인한다.

```
cd ~/node-prj
ls
```

`app.js`, `math.js`, `package.json`이 보이면 OK다. 없다면 CommonJS 실습을 먼저 끝낸다.

현재 파일 상태 확인. VSCode에서 `math.js`를 연다.

```js
function add(a, b) {
  return a + b;
}

function sub(a, b) {
  return a - b;
}

exports.add = add;
exports.sub = sub;
```

VSCode에서 `app.js`를 연다.

```js
const math = require('./math');

console.log(math.add(1, 2));   // 3
console.log(math.sub(5, 3));   // 2
```

이 튜토리얼은 이 두 파일을 ES Module 문법으로 전환하면서 진행한다.

## 1. CommonJS와 ES Module의 차이

CommonJS는 Node.js에서 잘 동작하지만, 브라우저에서는 안 되고, 동적 import도 못 한다. 하지만 이제 ES2015(ECMAScript 2015)에 표준화된 ES Module(`import`/`export`)을 사용하면 이 문제를 쉽게 해결할 수 있다.

이 모듈 시스템을 이해하기 위해서 CommonJS와의 차이를 먼저 이해하고, 이 튜토리얼에서 뭘 할지 알아본다.

### 1-1. CommonJS의 한계(복습)

| 한계 | 설명 |
|---|---|
| 브라우저에서 안 됨 | `require`/`exports`는 Node.js 전용 |
| 동적 import 불가 | 런타임에 "이제 이 모듈을 불러와야 해"라고 할 수 없음 |
| tree-shaking 불가 | 빌드 도구가 "어떤 export가 실제로 쓰이는지"를 정적 분석으로 알 수 없음 |

### 1-2. ES Module이 해결하는 것

| CommonJS 한계 | ES Module 해결 |
|---|---|
| 브라우저에서 안 됨 | `import`/`export`는 브라우저 + Node.js 모두 지원 |
| 동적 import 불가 | `import()` 함수로 런타임에 동적 로드 가능 |
| tree-shaking 불가 | `import { add } from './math'`로 "add만 쓴다"가 정적으로 분석 가능 |

### 1-3. 문법 비교

| | CommonJS | ES Module |
|---|---|---|
| 내보내기 | `module.exports = { add, sub }` | `export function add(...) {}` |
| 가져오기 | `const math = require('./math')` | `import { add } from './math.js'` |
| 동기/비동기 | 동기 | 정적 import는 파일 로드 시, 동적 `import()`는 비동기 |
| 사용 환경 | Node.js | Node.js + 브라우저 |
| 파일 확장자 | `.js`(기본) | `.js`(`"type": "module"`) 또는 `.mjs` |
| 경로에 확장자 | `require('./math')` — 확장자 생략 가능 | `import ... from './math.js'` — 확장자 필수 |

가장 큰 차이: ES Module은 `import ... from './math.js'`처럼 확장자를 반드시 써야 한다. CommonJS의 `require('./math')`처럼 확장자를 빼면 안 된다.

### 1-4. 이 튜토리얼에서 할 것

- `package.json`에 `"type": "module"`을 추가해서 ES Module 모드로 전환
- `math.js`를 `export` 문법으로 변환
- `app.js`를 `import` 문법으로 변환
- 다양한 import 방식(구조 분해, alias, default) 실습
- 동적 `import()` 실습

**✅ 확인**

- CommonJS의 한계와 ES Module이 해결하는 점을 이해했다.
- 문법 비교표를 확인했다.
- 이 튜토리얼의 흐름을 파악했다.

**🎓 newlec 쌤의 코멘트**

CommonJS는 2009년에 나왔고, ES Module은 2015년에 표준화되었다. 6년 차이가 있지만, Node.js는 이미 CommonJS 생태계가 너무 커서 쉽게 전환하지 못했다.

지금은 Node.js에서 둘 다 쓸 수 있다. `package.json`에 `"type": "module"`을 추가하면 ES Module로, 없으면 CommonJS로 동작한다.

이 튜토리얼에서 ES Module을 배우는 이유는, 새 프로젝트는 거의 다 ES Module로 시작하기 때문이다. React, Vite, Next.js — 전부 ES Module이다. CommonJS는 "구 프로젝트"를 볼 때 알아야 하고, ES Module은 "새 프로젝트"를 만들 때 써야 한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `require is not defined in ES module scope` | `"type": "module"`이 있는데 `require` 사용 | `import`로 전환 |
| `Unexpected token 'export'` | CommonJS 모드에서 `export` 사용 | `package.json`에 `"type": "module"` 추가 |

**📝 이 단계의 핵심**

- CommonJS: Node.js 전용, 동기, tree-shaking 불가
- ES Module: 표준, 브라우저+Node.js, tree-shaking 가능
- `package.json`의 `"type": "module"`으로 모드 전환
- ES Module은 경로에 확장자 필수

## 2. `package.json`에 `"type": "module"` 추가하기

Node.js는 `.js` 파일을 해석할 때 `package.json`에 `"type": "module"`이 있으면 ES Module로 동작하고, 없으면 CommonJS로 동작한다. 이 한 줄을 추가하는 순간, 기존 `require`/`exports` 코드가 전부 에러가 된다.

그걸 경험해보기 위해서 이번에는 3·4단계에서 `math.js`와 `app.js`를 모두 ES Module 문법으로 전환해본다.

### 2-1. `package.json` 확인

VSCode에서 `package.json`을 연다(탐색기에서 `package.json` 클릭).

현재 내용:

```json
{
  "name": "node-prj",
  "version": "1.0.0",
  "description": "npm 기초 튜토리얼 프로젝트",
  "main": "app.js",
  "scripts": {
    "test": "test",
    "start": "node app.js",
    "dev": "nodemon app.js"
  },
  "author": "",
  "license": "MIT",
  "dependencies": {
    "newlec-hello": "^0.0.2"
  },
  "devDependencies": {
    "nodemon": "^3.1.0"
  }
}
```

### 2-2. `"type": "module"` 추가

VSCode에서 `package.json`을 연다. `"version"` 줄 아래에 `"type": "module"`을 추가한다.

파일: `package.json`(변경 부분만)

```json
{
  "name": "node-prj",
  "version": "1.0.0",
  "type": "module",
  "description": "npm 기초 튜토리얼 프로젝트",
  "main": "app.js",
  "scripts": {
    "test": "test",
    "start": "node app.js",
    "dev": "nodemon app.js"
  },
  "author": "",
  "license": "MIT",
  "dependencies": {
    "newlec-hello": "^0.0.2"
  },
  "devDependencies": {
    "nodemon": "^3.1.0"
  }
}
```

주의: `"type": "module"`을 추가하는 순간, 프로젝트 안의 모든 `.js` 파일이 ES Module로 해석된다. 기존 `require`/`exports` 코드는 전부 에러가 된다. 3·4단계에서 바로 고친다.

### 2-3. 현재 상태 확인 — 에러 발생

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
node app.js
```

에러가 나온다.

```
ReferenceError: require is not defined in ES module scope
```

`"type": "module"`을 추가했으므로 Node.js가 `app.js`를 ES Module로 해석한다. 그런데 `app.js`에는 아직 `require`가 남아있으므로 에러다.

이 에러는 정상이다. 3·4단계에서 `math.js`와 `app.js`를 ES Module 문법으로 전환하면 해결된다.

**✅ 확인**

- `package.json`에 `"type": "module"`을 추가했다.
- 기존 `require` 코드가 에러가 되는 것을 확인했다.
- 3·4단계에서 고칠 것임을 알았다.

**🎓 newlec 쌤의 코멘트**

`"type": "module"`은 "이 프로젝트의 `.js` 파일은 전부 ES Module이다"라고 Node.js에 알려주는 선언이다.

이 한 줄을 추가하면:

- `require` → 에러
- `module.exports` → 에러
- `import`/`export` → 정상

반대로 `"type": "commonjs"`를 명시하면 CommonJS 모드다(없으면 기본값이 `commonjs`).

실무 팁: 새 프로젝트는 처음부터 `"type": "module"`을 넣는다. Vite, Next.js, Create React App — 전부 ES Module로 시작한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `require is not defined in ES module scope` | `"type": "module"` + `require` 사용 | `import`로 전환(3·4단계) |
| `Unexpected token 'export'` | `"type": "module"` 없이 `export` 사용 | `"type": "module"` 추가 |
| `node_modules` 안의 패키지가 에러 | 그 패키지가 CommonJS인데 ES Module에서 import | 대부분 호환됨. 안 되면 `createRequire` 사용(고급) |

**📝 이 단계의 핵심**

- `"type": "module"` → `.js` 파일이 ES Module로 해석
- `"type": "commonjs"` 또는 없음 → `.js` 파일이 CommonJS로 해석
- 전환 후 기존 `require`/`exports` 코드는 에러 → 바로 전환해야 함

## 3. `export` — ES Module의 내보내기

`math.js`의 `exports.add = add; exports.sub = sub;`를 ES Module 방식인 `export` 문법으로 바꾼다. 모듈에서 외부로 노출할 때는 named export와 default export 두 가지 방식이 있는데 이 두 가지 모두 실습한다.

### 3-1. named export 방법

VSCode에서 `math.js`를 연다(탐색기에서 `math.js` 클릭).

현재 내용:

```js
function add(a, b) {
  return a + b;
}

function sub(a, b) {
  return a - b;
}

exports.add = add;
exports.sub = sub;
```

아래 내용으로 전체 교체한다.

파일: `math.js`

```js
export function add(a, b) {
  return a + b;
}

export function sub(a, b) {
  return a - b;
}
```

`export function add(...)` — "이 함수를 외부에 공개한다"는 뜻이다. `exports.add = add`처럼 "먼저 만들고, 나중에 `exports`에 추가"하는 대신, 함수 선언 자체에 `export`를 붙여 한 번에 끝낸다.

### 3-2. named export 방법의 다른 형태

`export`를 함수 선언에 붙이지 않고, 아래에 따로 쓸 수도 있다.

```js
function add(a, b) {
  return a + b;
}

function sub(a, b) {
  return a - b;
}

export { add, sub };
```

이 방식은 "함수를 먼저 정의하고, 마지막에 한 줄로 내보낼 것들을 나열"하는 방식이다. 코드가 길 때 편하다.

### 3-3. default export 방법

`export default`는 "이 파일의 대표 내보내기"를 지정한다. 파일당 하나만 가능하다.

파일: `math.js`(default export 버전)

```js
function add(a, b) {
  return a + b;
}

function sub(a, b) {
  return a - b;
}

export { add, sub };
export default add;
```

`export default add` — "이 파일의 default는 `add` 함수다"라는 뜻이다. import할 때 이름을 자유롭게 정할 수 있다(4단계에서 확인).

### 3-4. 실행 확인

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
node -e "import('./math.js').then(m => console.log(m))"
```

`{ add: [Function: add], sub: [Function: sub], default: [Function: add] }`가 출력된다. `add`, `sub`가 named export로, `default`가 default export로 보인다.

`node -e`에서 ES Module을 쓰려면 `import()`(동적 import)를 써야 한다. 5단계에서 자세히 다룬다.

**✅ 확인**

- `math.js`가 `export function` / `export { }` / `export default` 문법으로 동작한다.
- `node -e "import('./math.js')..."`로 내보낸 객체를 확인했다.

**🎓 newlec 쌤의 코멘트**

CommonJS의 `module.exports = { add, sub }`가 ES Module의 `export { add, sub }`에 해당한다.

하지만 ES Module은 여러 개의 export를 가질 수 있다.

- `export function add(...)` — named export
- `export function sub(...)` — named export
- `export default add` — default export(하나만)

CommonJS는 `module.exports`가 하나이므로, "이 파일의 대표"가 하나다. ES Module은 named export를 여러 개 가질 수 있고, default export를 하나 더 가질 수 있다.

실무에서: named export를 기본으로 쓰고, "이 파일은 이 함수 하나만 담당한다"는 명확한 의도가 있을 때만 default export를 쓴다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Unexpected token 'export'` | `"type": "module"`이 없음 | `package.json`에 `"type": "module"` 추가 |
| `SyntaxError: Unexpected identifier` | `export` 위치가 잘못됨(함수 바깥이 아닌 안쪽) | `export`는 항상 최상위 스코프에 |
| `export default`를 두 번 사용 | default export는 파일당 하나만 | 하나만 `export default` |

**📝 이 단계의 핵심**

- `export function add(...)` — named export(여러 개 가능)
- `export { add, sub }` — named export(별칭 나열)
- `export default add` — default export(파일당 하나만)
- CommonJS의 `module.exports = { add, sub }` ≈ ES Module의 `export { add, sub }`

## 4. `import` — ES Module의 가져오기

`math.js`를 ES Module로 바꿨으니, 이제 그것을 가져다 사용하는 `app.js`도 ES6 모듈 시스템에 맞게 `import` 문법으로 바꿔야 한다.

import 방법도 다양하게 여러 가지가 있기 때문에 import 방식들을 직접 하나씩 써보면서 "어떤 상황에서 어떤 방식을 쓰는지"를 익혀본다.

### 4-1. 기본 import(named)

VSCode에서 `app.js`를 연다(탐색기에서 `app.js` 클릭).

현재 내용:

```js
const math = require('./math');

console.log(math.add(1, 2));   // 3
console.log(math.sub(5, 3));   // 2
```

아래 내용으로 전체 교체한다.

파일: `app.js`

```js
import { add, sub } from './math.js';

console.log(add(1, 2));   // 3
console.log(sub(5, 3));   // 2
```

주의: `from './math.js'` — 확장자 `.js`가 필수다. CommonJS의 `require('./math')`처럼 확장자를 빼면 안 된다.

### 4-2. 실행

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
node app.js
```

**✅ 확인**

터미널에 다음이 나온다.

```
3
2
```

### 4-3. 전체 import(namespace)

`math.js`의 모든 export를 한 번에 가져올 수도 있다.

파일: `app.js`

```js
import * as math from './math.js';

console.log(math.add(1, 2));   // 3
console.log(math.sub(5, 3));   // 2
```

`import * as math` — "`math.js`의 모든 export를 `math`라는 객체에 담아줘"라는 뜻이다. CommonJS의 `const math = require('./math')`와 가장 비슷한 형태다.

### 4-4. 실행

```
node app.js
```

**✅ 확인**

터미널에 다음이 나온다.

```
3
2
```

### 4-5. default import

`math.js`에 `export default add;`가 있으므로 다음처럼 쓸 수 있다.

파일: `app.js`

```js
import add from './math.js';

console.log(add(1, 2));   // 3
```

`import add from './math.js'` — "`math.js`의 default export를 `add`라는 이름으로 가져와"라는 뜻이다. 이름을 자유롭게 정할 수 있다(`import foo from './math.js'`도 된다).

### 4-6. default + named import 조합

파일: `app.js`

```js
import add, { sub } from './math.js';

console.log(add(1, 2));   // 3
console.log(sub(5, 3));   // 2
```

`import add, { sub }` — "default export를 `add`로, named export `sub`를 가져와"라는 뜻이다.

### 4-7. alias(별칭)

파일: `app.js`

```js
import { add as plus, sub as minus } from './math.js';

console.log(plus(1, 2));   // 3
console.log(minus(5, 3));  // 2
```

`add as plus` — "`math.js`의 `add`를 이 파일에서는 `plus`라고 불러"라는 뜻이다. 이름 충돌을 피할 때 사용한다.

### 4-8. 실행

```
node app.js
```

**✅ 확인**

터미널에 다음이 나온다.

```
3
2
```

### 4-9. import 방식 정리

| 방식 | 예시 | 용도 |
|---|---|---|
| named import | `import { add, sub } from './math.js'` | 특정 함수만 가져올 때(가장 일반적) |
| namespace import | `import * as math from './math.js'` | 전체 가져올 때 |
| default import | `import add from './math.js'` | default export 하나만 가져올 때 |
| default + named | `import add, { sub } from './math.js'` | default + named 함께 |
| alias | `import { add as plus } from './math.js'` | 이름 충돌 방지 |

**🎓 newlec 쌤의 코멘트**

ES Module의 `import`는 CommonJS의 `require`와 가장 큰 차이가 두 가지다.

- 확장자 필수: `import ... from './math.js'` — `.js`를 빼면 안 된다.
- 정적 분석 가능: `import { add } from './math.js'`라고 쓰면, 빌드 도구가 "이 파일은 `add`만 쓴다"를 코드를 실행하지 않고도 알 수 있다. 그래서 tree-shaking이 가능하다.

CommonJS의 `const math = require('./math')`는 "`math`의 뭐를 쓸지"를 런타임에야 알기 때문에 tree-shaking이 안 된다.

실무에서: named import(`import { add } from ...`)를 기본으로 쓴다. React의 `import React from 'react'`는 default import, `import { useState } from 'react'`는 named import다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Cannot find module './math'` | 확장자 `.js` 누락 | `from './math.js'` |
| `The requested module does not provide an export named 'add'` | `math.js`에 export가 없거나 이름 다름 | `math.js`의 export 확인 |
| `add is not a function` | `import add from ...`인데 `math.js`에 `export default`가 없음 | `export default add` 추가 또는 named import 사용 |
| `require is not defined` | `import`로 전환했는데 `require`가 남아있음 | `require`를 `import`로 교체 |

**📝 이 단계의 핵심**

- `import { add } from './math.js'` — named import(가장 일반적)
- `import * as math from './math.js'` — namespace import
- `import add from './math.js'` — default import
- 확장자 `.js` 필수
- `import`는 항상 파일 최상위에 있어야 함(조건부 불가)

## 5. `import()` — 동적 import로 조건부 로드하기

ES Module에서는 코드를 실행하다가 런타임에 모듈을 동적으로 불러와야 하는 경우 사용할 수 있는 도구가 있다. 바로 `import()` 함수다. CommonJS의 `require`는 "조건에 따라 다른 모듈을 로드"할 수 있지만, ES Module에서는 기본적으로 `import`를 사용하기 때문에 파일 최상위에 있어야 하고 정적인 특징을 가지는 명령어라 조건부로 모듈을 가져올 수 없다. 이런 부분을 해소할 수 있도록 `import()` 함수를 제공하고 있다.

### 5-1. 정적 import의 한계

```js
// ❌ 이렇게 쓸 수 없음
if (process.env.DEBUG) {
  import { logger } from './logger.js';  // SyntaxError!
}
```

`import`는 항상 파일 최상위에 있어야 한다. `if`문 안에 쓸 수 없다.

### 5-2. 동적 `import()`

```js
// ✅ 이렇게 쓰는 것
if (process.env.DEBUG) {
  const { logger } = await import('./logger.js');
  logger.log('debug mode');
}
```

`import()`는 함수다. Promise를 반환하므로 `await`가 필요하다.

### 5-3. 실습 — 조건부 import

VSCode에서 `app.js`를 연다. 아래 내용으로 전체 교체한다.

파일: `app.js`

```js
import { add, sub } from './math.js';

console.log(add(1, 2));   // 3
console.log(sub(5, 3));   // 2

// 동적 import — 조건에 따라 로드
const shouldLoad = true;
if (shouldLoad) {
  const math = await import('./math.js');
  console.log(math.add(10, 20));  // 30
}
```

`await import('./math.js')` — 런타임에 `math.js`를 로드하고, 모든 export가 담긴 객체를 반환한다. `shouldLoad`가 `false`라면 `math.js`가 로드되지 않는다.

### 5-4. 실행

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
node app.js
```

**✅ 확인**

터미널에 다음이 나온다.

```
3
2
30
```

### 5-5. 동적 import의 실용적 용도

| 용도 | 예시 |
|---|---|
| 조건부 로드 | `if (isMobile) { const Mobile = await import('./Mobile.js') }` |
| 지연 로드(lazy loading) | 버튼 클릭 시에만 무거운 모듈 로드 |
| 동적 경로 | `` await import(`./plugins/${name}.js`) `` — 런타임에 경로 결정 |

**🎓 newlec 쌤의 코멘트**

`import()`는 "CommonJS의 `require`가 할 수 있었던 것"을 ES Module에서 다시 가능하게 해주는 문법이다.

- CommonJS: `const x = require('./x')` — 동기, 조건부 가능
- ES Module 정적: `import x from './x'` — 정적, 조건부 불가
- ES Module 동적: `const x = await import('./x')` — 비동기, 조건부 가능

실무에서 React에서 `React.lazy(() => import('./HeavyComponent'))`를 쓰는 게 바로 이 `import()`다. "이 컴포넌트는 사용자가 보일 때만 로드해"라는 뜻이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `await is only valid in async function` | `await import()`를 async 함수 밖에서 사용 | Node.js 최상위 `await`는 ES Module에서 가능(Node 14+). 안 되면 `async function`으로 감싸기 |
| `import() is not a function` | CommonJS 모드에서 `import()` 사용 | `"type": "module"` 확인 |

**📝 이 단계의 핵심**

- `import()`는 함수 — Promise 반환, `await` 필요
- 조건부 로드, 지연 로드, 동적 경로에 사용
- CommonJS의 `require`가 할 수 있었던 "조건부 로드"를 ES Module에서 가능하게 함

## 6. CommonJS vs ES Module 최종 비교

이제 두 시스템을 모두 실습했다. 실무에서 "어떤 걸 쓸까?"를 판단할 수 있도록 최종 비교한다.

### 6-1. 비교표

| | CommonJS | ES Module |
|---|---|---|
| 내보내기 | `module.exports = ...` / `exports.x = ...` | `export ...` / `export default ...` |
| 가져오기 | `const x = require(...)` | `import x from ...` / `import { x } from ...` |
| 확장자 | 생략 가능(`require('./math')`) | 필수(`import ... from './math.js'`) |
| 동기/비동기 | 동기 | 정적: 로드 시 / 동적 `import()`: 비동기 |
| 조건부 로드 | ✅ `if (...) { require(...) }` | ❌ 정적 / ✅ 동적 `import()` |
| tree-shaking | ❌ | ✅ |
| 브라우저 | ❌ | ✅ |
| Node.js | ✅(기본) | ✅(`"type": "module"`) |
| 캐싱 | ✅(동일) | ✅(동일) |
| 호환성 | 구 Node.js | Node 12+ |

### 6-2. 실무에서 어떤 걸 쓸까?

| 상황 | 선택 | 이유 |
|---|---|---|
| 새 프로젝트 | ES Module | 표준, 브라우저 호환, tree-shaking |
| 기존 Node.js 프로젝트 | CommonJS 유지 | 전환 비용 > 이득 |
| React/Vite/Next.js | ES Module | 빌드 도구가 ES Module을 전제로 함 |
| npm 패키지 작성 | ES Module(권장) | `exports` 필드로 CJS/ESM 듀얼 지원 가능 |

### 6-3. 최종 실행 확인

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
node app.js
```

`3`, `2`, `30`이 출력되면 성공이다.

**✅ 확인**

- CommonJS와 ES Module의 차이를 비교했다.
- 실무에서 어떤 걸 쓸지 판단 기준을 알았다.
- 최종 실행이 정상 동작한다.

**🎓 newlec 쌤의 코멘트**

"CommonJS를 배울 필요 있나?"라는 질문을 많이 받는다.

답은 있다.

- 실무에서 아직 CommonJS를 쓰는 프로젝트가 많다(특히 2015~2020년 사이 만들어진 프로젝트).
- `node_modules` 안의 패키지가 CommonJS인 경우가 많다.
- "이 코드가 왜 안 되는지"를 알려면 CommonJS를 알아야 한다.

하지만 새 프로젝트는 ES Module로 시작한다. Vite, Next.js, Create React App — 전부 ES Module이다.

한 줄 요약: CommonJS는 "읽기"를 위해, ES Module은 "쓰기"를 위해 배운다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `require is not defined in ES module scope` | ES Module 모드에서 `require` 사용 | `import`로 전환 |
| `Unexpected token 'export'` | CommonJS 모드에서 `export` 사용 | `"type": "module"` 추가 |
| `Cannot find module './math'` | ES Module에서 확장자 누락 | `from './math.js'` |

**📝 이 단계의 핵심**

- 새 프로젝트 → ES Module
- 기존 프로젝트 → CommonJS 유지(전환 비용 고려)
- CommonJS는 "읽기"를 위해, ES Module은 "쓰기"를 위해

### 6-4. 최종 확인

VSCode 터미널에서 실행한다.

```
ls
```

```
node-prj/
├── app.js              ← import { add, sub } from './math.js'
├── math.js             ← export function add / export function sub / export default
├── package.json        ← "type": "module"
├── package-lock.json
└── node_modules/
```

최종 실행:

```
node app.js
```

`3`, `2`, `30`이 출력되면 성공이다.

**여기까지의 정리**

1단계 — CommonJS의 한계(브라우저 불가, 동적 import 불가, tree-shaking 불가) → ES Module이 해결
2단계 — `package.json`에 `"type": "module"` 추가 → ES Module 모드 전환
3단계 — `export function` / `export { }` / `export default`로 모듈 내보내기
4단계 — `import { }` / `import * as` / `import default` / alias로 모듈 가져오기
5단계 — `import()`로 동적 로드(조건부, 지연 로드)
6단계 — CommonJS vs ES Module 최종 비교 + 실무 선택 기준
