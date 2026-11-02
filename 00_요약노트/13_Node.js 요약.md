---
tags: [요약, Node.js, 비동기, 콜백, Promise, async-await]
---

# Node.js 요약

Node.js는 **브라우저 밖에서 실행되는 자바스크립트**다. 이 카테고리의 중심은 Node.js의 동시성 모델과, 그 위에서 쓰는 **비동기 처리**(콜백 → Promise → async/await)다.

## 1. 한눈에 보기

| 주제 | 핵심 |
|---|---|
| Node.js의 탄생 | V8 엔진을 브라우저 밖으로 꺼내 서버에서 자바스크립트를 실행한다 |
| 스레드 대신 콜백 | 요청마다 스레드를 만드는 대신, 이벤트 루프와 콜백으로 동시성을 처리한다 |
| npm | 패키지 관리자. 생태계가 빠르게 커졌다 |
| ES Module | `import` / `export` 표준 모듈 시스템 |
| 동기형 API | 단순하지만, 오래 걸리는 작업이 전체를 멈춘다 |
| 콜백 기반 비동기 | 논블로킹이지만 중첩되면 콜백 지옥이 된다 |
| `async` / `await` | 콜백 없이 동기처럼 쓴다 |
| `Promise` | 비동기 결과를 나중에 받는 객체. `.then` 체인으로 연결한다 |
| `util.promisify` | 기존 콜백 함수를 Promise로 바꾼다 |
| `Promise.all` | 여러 작업을 동시에 실행하고 모두 끝나길 기다린다 |

## 2. 개념 정리

### 2-1. 비동기 처리의 변화

```js
// 1. 콜백 — 중첩되면 읽기 어렵다
fs.readFile("a.txt", (err, data) => { /* … */ });

// 2. Promise
readFile("a.txt").then(data => { /* … */ });

// 3. async / await — 동기 코드처럼 읽힌다
const data = await readFile("a.txt");
```

### 2-2. 동시 실행

```js
const [a, b] = await Promise.all([fetchA(), fetchB()]);   // 둘이 동시에 진행
```

순서대로 `await`하면 각 작업이 끝나길 기다리므로 느리다. 서로 의존하지 않는 작업은 `Promise.all`로 묶는다.

### 2-3. 어디서 쓰는가

Next.js 서버 컴포넌트에서 실제 데이터를 가져올 때 `async` / `await`를 그대로 쓴다.

## 3. 자주 헷갈리는 것

- **비동기 함수를 만드는 입장**에서는 여전히 콜백이나 Promise가 필요하다. `await`는 쓰는 쪽의 편의다.
- Promise를 직접 다룰 일이 많은 사람은 도구나 라이브러리를 만드는 사람이다. 일반 개발에서는 `async` / `await` 중심으로 쓴다.
- 프로세스와 스레드의 차이를 알아야 Node.js가 스레드 대신 콜백을 선택한 이유가 이해된다.

## 4. 이 카테고리의 실습과 오답노트

- 실습: Node.js·npm, ES Module, 배열 메서드로 데이터 다루기
- 오답노트: V8 엔진과 Node.js
