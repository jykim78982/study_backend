---
tags: [웹, 자바스크립트, Node.js, ES Module, 실습]
---

> 🔗 관련 노트: [[024_Node.js·npm 실습]]

# ES Module 실습

[[024_Node.js·npm 실습]]에서 CommonJS(`require`/`exports`)로 만든 `node-prj/`의 `math.js`, `app.js`를 그대로 ES Module(`import`/`export`) 문법으로 바꿔보며, `package.json`의 `"type": "module"` 설정과 두 모듈 시스템의 차이를 직접 확인한 실습이다.

## 1. `package.json`에 `"type": "module"` 추가하기

`math.js`, `app.js`는 지금까지 `require`/`exports`(CommonJS)로 작성되어 있다. `package.json`의 `"version"` 아래에 `"type": "module"`을 추가하면, 이 프로젝트 안의 모든 `.js` 파일이 ES Module로 해석된다.

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
    "dependencies": {
        "newlec-hello": "^0.0.2"
    },
    "devDependencies": {
        "nodemon": "^3.1.0"
    }
}
```

`"type": "module"`을 추가한 직후에는 아직 `math.js`·`app.js`가 CommonJS 문법 그대로이므로 실행하면 에러가 난다.

```
node app.js
```

```
ReferenceError: require is not defined in ES module scope
```

`"type": "module"`이 "이 프로젝트의 `.js`는 전부 ES Module이다"라고 선언해버렸기 때문에, 그 안에 남아있는 `require`가 더 이상 인식되지 않는 것이다. 반대로 `"type": "commonjs"`를 명시하거나 `type` 필드 자체를 생략하면 CommonJS 모드로 동작한다(생략 시 기본값이 `commonjs`).

## 2. `export` — ES Module의 내보내기

`math.js`의 `exports.add = add; exports.sub = sub;`를 ES Module 문법으로 바꾼다. ES Module은 **named export**(여러 개 가능)와 **default export**(파일당 하나만) 두 가지를 제공한다.

### 2-1. named export — 함수 선언에 바로 붙이기

```js
export function add(a, b) {
    return a + b;
}

export function sub(a, b) {
    return a - b;
}
```

`export function add(...)`는 함수를 먼저 만들고 나중에 `exports.add = add`로 등록하던 CommonJS 방식과 달리, 함수 선언 자체에 `export`를 붙여 한 번에 끝낸다.

### 2-2. named export — 한 줄로 모아서 내보내기

```js
function add(a, b) {
    return a + b;
}

function sub(a, b) {
    return a - b;
}

export { add, sub };
```

함수를 먼저 전부 정의한 뒤, 마지막에 `export { add, sub };` 한 줄로 내보낼 것들을 나열하는 방식이다. 내보낼 함수가 많아질수록 어디서 무엇을 내보내는지 한눈에 보기 편하다.

### 2-3. default export — 파일의 대표 하나 지정하기

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

`export default add;`는 "이 파일의 default는 `add` 함수다"라는 뜻이다. default export는 파일당 하나만 가능하며, 가져올 때(3-3) 이름을 자유롭게 지을 수 있다는 점이 named export와 다르다.

### 2-4. 내보낸 객체 확인하기

```
node -e "import('./math.js').then(m => console.log(m))"
```

```
{ add: [Function: add], sub: [Function: sub], default: [Function: add] }
```

`add`, `sub`는 named export로, `default`는 default export로 각각 구분되어 담긴다. `node -e`에서 ES Module을 다루려면 최상위 `import`가 아니라 4절에서 다룰 동적 `import()`를 써야 한다.

CommonJS의 `module.exports = { add, sub }`가 하나의 대표 객체만 가질 수 있는 것과 달리, ES Module은 named export를 여러 개 두고 default export를 추가로 하나 더 가질 수 있다. 실무에서는 named export를 기본으로 쓰고, "이 파일은 이 함수 하나만 담당한다"는 의도가 분명할 때만 default export를 쓴다.

## 3. `import` — ES Module의 가져오기

`math.js`를 ES Module로 바꿨으니, `app.js`의 `const math = require('./math');`도 `import` 문법으로 바꿔야 한다. 상황에 따라 쓰는 방식이 다르므로 하나씩 확인한다.

### 3-1. named import — 필요한 것만 꺼내오기

```js
import { add, sub } from './math.js';

console.log(add(1, 2)); // 3
console.log(sub(5, 3)); // 2
```

`from './math.js'`처럼 **확장자 `.js`가 필수**다. CommonJS의 `require('./math')`처럼 확장자를 생략하면 안 된다.

### 3-2. namespace import — 전체를 객체 하나로 받기

```js
import * as math from './math.js';

console.log(math.add(1, 2)); // 3
console.log(math.sub(5, 3)); // 2
```

`import * as math`는 `math.js`의 모든 export를 `math`라는 객체에 담아준다. CommonJS의 `const math = require('./math')`와 형태가 가장 비슷하다.

### 3-3. default import — default export 가져오기

```js
import add from './math.js';

console.log(add(1, 2)); // 3
```

`math.js`에 `export default add;`가 있으므로, `import add from './math.js'`처럼 원하는 이름으로 자유롭게 가져올 수 있다(`import foo from './math.js'`도 동작한다).

### 3-4. default + named import 함께 쓰기

```js
import add, { sub } from './math.js';

console.log(add(1, 2)); // 3
console.log(sub(5, 3)); // 2
```

### 3-5. alias — 이름 충돌 피하기

```js
import { add as plus, sub as minus } from './math.js';

console.log(plus(1, 2));  // 3
console.log(minus(5, 3)); // 2
```

`add as plus`는 "`math.js`의 `add`를 이 파일에서는 `plus`라고 부르겠다"는 뜻이다. 같은 이름의 함수를 여러 모듈에서 가져올 때 이름 충돌을 피하는 용도다.

### 3-6. 방식 정리

| 방식 | 예시 | 용도 |
|---|---|---|
| named import | `import { add, sub } from './math.js'` | 특정 함수만 가져올 때(가장 일반적) |
| namespace import | `import * as math from './math.js'` | 전체를 한 객체로 가져올 때 |
| default import | `import add from './math.js'` | default export 하나만 가져올 때 |
| default + named | `import add, { sub } from './math.js'` | default와 named를 함께 |
| alias | `import { add as plus } from './math.js'` | 이름 충돌 방지 |

`import`가 `require`와 다른 가장 큰 차이는 두 가지다. 첫째, 확장자가 필수다. 둘째, `import { add } from './math.js'`처럼 무엇을 가져오는지가 코드만 보고도 정적으로 분석되므로, 빌드 도구가 "이 파일은 `add`만 쓴다"를 실행 없이 파악해 tree-shaking을 할 수 있다. `const math = require('./math')`는 `math`의 무엇을 쓸지 런타임에야 알 수 있어 이 분석이 불가능하다.

## 4. `import()` — 동적 import로 조건부 로드하기

ES Module의 정적 `import`는 항상 파일 최상위에 있어야 해서 조건문 안에서 쓸 수 없다.

```js
// ❌ SyntaxError — import는 최상위에서만 가능
if (process.env.DEBUG) {
    import { logger } from './logger.js';
}
```

CommonJS의 `require`는 동기적이라 조건문 안에서도 자유롭게 쓸 수 있었던 것과 대비된다. 이 자리를 채우는 것이 함수 형태의 `import()`다.

```js
import { add, sub } from './math.js';

console.log(add(1, 2)); // 3
console.log(sub(5, 3)); // 2

const shouldLoad = true;
if (shouldLoad) {
    const math = await import('./math.js');
    console.log(math.add(10, 20)); // 30
}
```

```
node app.js
```

```
3
2
30
```

`import()`는 함수이며 Promise를 반환하므로 `await`가 필요하다. `await import('./math.js')`는 런타임에 `math.js`를 로드해서 모든 export가 담긴 객체를 반환하며, `shouldLoad`가 `false`라면 `math.js` 자체가 로드되지 않는다. 조건부 로드 외에도 "버튼을 클릭했을 때만 무거운 모듈을 로드"하는 지연 로드(lazy loading), `` await import(`./plugins/${name}.js`) ``처럼 런타임에 경로를 결정하는 동적 경로 로드에 쓰인다.

## 5. CommonJS vs ES Module 최종 비교

| | CommonJS | ES Module |
|---|---|---|
| 내보내기 | `module.exports = ...` / `exports.x = ...` | `export ...` / `export default ...` |
| 가져오기 | `const x = require(...)` | `import x from ...` / `import { x } from ...` |
| 확장자 | 생략 가능 | 필수 |
| 동기/비동기 | 동기 | 정적 import는 로드 시, 동적 `import()`는 비동기 |
| 조건부 로드 | 가능(`if` 안에서 `require`) | 정적 import는 불가, 동적 `import()`는 가능 |
| tree-shaking | 불가 | 가능 |
| 브라우저 | 불가 | 가능 |
| Node.js | 가능(기본값) | 가능(`"type": "module"` 필요) |

새 프로젝트는 표준이자 브라우저 호환·tree-shaking이 되는 ES Module로 시작하고, 이미 CommonJS로 짜인 기존 프로젝트는 전환 비용이 이득보다 크므로 그대로 유지하는 것이 실무 판단 기준이다. 다만 `node_modules` 안의 오래된 패키지가 CommonJS인 경우가 여전히 많고, "이 코드가 왜 안 되는지"를 이해하려면 CommonJS도 알아야 하므로 — CommonJS는 기존 코드를 "읽기" 위해, ES Module은 새 코드를 "쓰기" 위해 알아둔다.
