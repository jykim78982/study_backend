---
tags: [웹, 자바스크립트, 비동기, Node.js, Next.js]
---

> 🔗 관련 노트: [[024_Node.js·npm 실습]] · [[028_Next.js App Router와 공통 레이아웃 실습]] · [[032_Next.js에서 스프링 부트 API 연동 — 메뉴 목록과 검색 폼 만들기 실습]]

# 자바스크립트 비동기 처리 — 콜백에서 async·await까지

파일 읽기·쓰기를 예로, 자바스크립트가 비동기를 처리해온 방식이 동기 → 콜백 → Promise → `async`/`await` 순서로 어떻게 바뀌어왔는지, 그리고 이것이 Next.js에서 서버 API 데이터를 가져올 때 어떻게 쓰이는지를 다룬다.

## 1. 왜 비동기를 다시 짚어야 하는가

목업 배열로 채워져 있던 데이터를, 실제로는 서버 API에서 가져와야 하는 순간이 온다. 데이터를 원격에서 가져오는 작업 자체가 시간이 걸리는 비동기 작업이므로, `fetch` 같은 도구가 왜 지금의 모양(`Promise`를 반환하고 `await`로 기다리는 방식)을 갖게 됐는지 이해하려면 그 이전 단계들을 먼저 봐야 한다.

## 2. Node.js 파일 API의 세 가지 형태

Node.js의 내장 파일 모듈은 같은 작업(쓰기·읽기)에 대해 세 가지 API 형태를 제공한다.

| 형태 | 특징 |
|---|---|
| 동기(Sync) | 끝날 때까지 다음 줄이 기다린다 |
| 비동기(콜백) | 즉시 빠져나가고, 끝나면 콜백을 호출한다 |
| 비동기(Promise) | 콜백 대신 `Promise` 객체를 반환한다 |

### 2-1. 동기 방식

```js
const fs = require('fs');

function handler() {
    try {
        fs.writeFileSync('example.txt', content, 'utf8');
        console.log('저장 완료');

        const data = fs.readFileSync('example.txt', 'utf8');
        console.log(data);
    } catch (err) {
        console.error('오류:', err);
    }
}

handler();
console.log("hello~");
```

실행 결과는 코드에 적힌 순서 그대로 찍힌다.

```
저장 완료
(파일 내용)
hello~
```

`writeFileSync`는 쓰기가 완전히 끝날 때까지 다음 줄을 막는다. 코드를 이해하기는 가장 쉽지만, 파일이 크거나 저장 장치가 느리면 그동안 프로그램 전체가 멈춘 것처럼 보인다 — 사용자와 상호작용하는 코드가 뒤에 있다면 그 사이 화면은 먹통이 된다. 그래서 실행 결과도 `handler()`가 전부 끝난 뒤에야 `"hello~"`가 찍힌다.

### 2-2. 콜백 기반 비동기

```js
fs.writeFile('example.txt', content, 'utf8', function (err) {
    console.log('저장 완료');
    fs.readFile('example.txt', 'utf8', (err, data) => {
        console.log(data);
    });
});
```

`Sync`를 뗀 `writeFile`은 명령만 내리고 즉시 다음 줄로 빠진다. 대신 "다 끝나면 불러줘"에 해당하는 콜백 함수를 마지막 인자로 받는다. 문제는 **읽기가 쓰기 뒤에 이어져야 하는** 순서 의존성이다 — 이 순서를 지키려면 읽기 코드를 쓰기의 콜백 안에 넣을 수밖에 없고, 이런 식으로 이어지는 작업이 늘어날수록 코드가 오른쪽으로 계속 들여쓰기되며 중첩된다(콜백 지옥). 동기 코드는 위→아래 직선으로 흐르지만, 콜백 코드는 안으로, 안으로 파고드는 흐름이 된다.

## 3. `async`/`await` — 콜백 없이 동기처럼 쓰기

```js
const fs = require('fs').promises;

// 비동기로 호출되는 함수여야만 await를 사용할 수 있다
async function handler() {
    try {
        await fs.writeFile('example.txt', content, 'utf8');
        console.log('저장 완료');

        const data = await fs.readFile('example.txt', 'utf8');
        console.log(data);
    } catch (err) {
        console.error('오류:', err);
    }
}

handler();
console.log("hello~");
```

`fs.promises`의 `writeFile`/`readFile`은 콜백을 받지 않고 대신 **`Promise` 객체를 반환**한다. `await`는 이 `Promise`가 끝날 때까지 그 자리에서 기다리게 하는 키워드라서, 콜백 없이도 동기 코드처럼 위에서 아래로 읽히는 코드를 쓸 수 있다.

다만 조건이 있다 — **`await`는 반드시 `async` 함수 안에서만 쓸 수 있다.** 자바스크립트는 메인 스레드 전체를 멈추는 것을 막기 위해, 기다리는 코드 블록 자체를 비동기 블록 안에만 있도록 강제한다. 실제로 실행 순서를 보면 `handler()`가 파일을 쓰는 동안 `console.log("hello~")`가 먼저 찍힌다 — `handler` 자체는 비동기 함수이므로 호출한 즉시 다음 줄로 넘어가기 때문이다.

### 3-1. 비동기로 만들어야 하는 기준

모든 함수를 비동기로 만들 필요는 없다. **시간이 오래 걸리거나 소요 시간이 들쭉날쭉한 작업, 특히 외부 호출(I/O)이 걸리는 작업**만 비동기로 만든다. 반대로 순서가 뒤 결과에 의존하는 작업(여러 사람이 순서대로 처리해야 하는 경우처럼)은 애초에 동기적으로 짜야 한다 — 비동기가 항상 이상적인 것은 아니고, 문제가 되는 부분만 골라 비동기로 빼는 것이 현실적인 방식이다.

## 4. `setTimeout`과 콜백 위임

```js
function order() {
    console.log("주문 완료");
    return 3;
}

function cook(amount, callback) {
    console.log("요리를 시작하겠습니다.");
    setTimeout(() => {
        console.log(`피자 ${amount}개가 완성`);
        callback();
    }, 3000);
}

let amount = order();
cook(amount, () => {
    console.log("결제금액은 얼마입니다.");
    console.log("맛있게 먹겠습니다.");
});
```

`setTimeout`은 지정한 시간(밀리초) 뒤에 넘겨준 함수를 실행하는 브라우저/Node 공통 기능이다(브라우저에서는 `window.setTimeout`, Node에서는 `global.setTimeout`이며, 전역 객체 이름은 생략할 수 있다). 여기서는 "피자가 다 만들어진 뒤에만 결제·수령 안내가 나와야 한다"는 순서를 지키기 위해, 결제·수령 로직을 `cook`의 콜백으로 넘긴다 — 콜백으로 코드 흐름 순서를 강제로 맞추는 전형적인 방식이다.

이 방식의 문제는 **콜백 인자 안에 업무 데이터(피자 개수 등)와 실행 순서 제어용 데이터가 뒤섞인다**는 점이다. 함수를 만들 때 비동기 로직이 하나라도 들어가면, 그 함수를 쓰는 모든 곳이 콜백을 받아야 하는 구조가 강제로 이어진다.

## 5. `Promise`를 직접 만들기

```js
function cook(amount) {
    return new Promise((resolve, reject) => {
        console.log("요리를 시작하겠습니다.");
        setTimeout(() => {
            console.log(`피자 ${amount}개가 완성`);
            let pizs = [
                { name: "페페로니 피자", price: 8000 },
                { name: "페페로니 피자", price: 8000 },
            ];
            resolve(pizs);
            // 실패했다면 reject()를 호출한다
        }, 3000);
    });
}

let promise = cook(order());

promise
    .then(pizs => pizs[0])
    .then(piz => piz.name)
    .then((name) => {
        console.log(name);
        console.log("결제금액은 얼마입니다.");
    })
    .catch(() => {
        console.log("실패했습니다.");
    });
```

`cook`은 콜백을 인자로 받는 대신 `Promise` 객체를 반환한다. `Promise` 생성자에 넘기는 함수는 `resolve`(성공 시 호출)와 `reject`(실패 시 호출) 두 콜백을 인자로 받는데, 이 두 콜백을 **함수 내부에서 대신 받아 관리해주는 그릇**이 바로 `Promise`다. 즉 콜백을 함수 인자로 직접 받는 대신, 콜백을 받아줄 객체(`Promise`)를 반환하는 형태로 바꾼 것이다.

이렇게 만들어두면 사용하는 쪽은 두 가지 방식을 고를 수 있다.

- `.then(...)`/`.catch(...)`로 체이닝해서 쓰거나
- (`async` 함수 안이라면) `await`로 기다렸다가 동기처럼 쓰거나

`.then`은 앞 단계의 반환값을 다음 `.then`으로 그대로 넘기므로, 값을 가공하는 단계를 필요한 만큼 자유롭게 끼워 넣거나 뺄 수 있다(인코딩·암호화·복호화 등). 이렇게 처리 단계를 체인 중간에 꽂았다 뺐다 할 수 있는 구조를 **미들웨어 방식**이라 부른다.

## 6. `Promise`를 알아야 하는 사람은 누구인가

`Promise`를 직접 쓰는 이유는 딱 하나다 — **비동기 로직이 들어간 함수를 내가 직접 만들 때, 콜백을 인자로 받는 대신 `Promise`를 반환하도록 만들기 위해서다.** 이미 `Promise`를 반환하는 함수(`fetch`, `fs.promises.*` 등)를 가져다 쓰기만 하는 입장이라면 `Promise`의 내부 동작을 몰라도 `await`만으로 충분하다. 배열을 다룰 때 인덱스를 직접 쓰는 것이 하수인 것처럼, 이미 있는 것을 그대로 쓸 수 있는데 `Promise` 문법을 직접 조립하는 것은 불필요하다 — 직접 함수를 설계하는 사람만 이 구조를 알면 된다.

## 7. Next.js 서버 컴포넌트에서 실제 데이터 가져오기

지금까지 본 흐름의 종착지가 `fetch`다. Next.js의 서버 컴포넌트는 `async` 함수로 선언할 수 있고, 그 안에서 `fetch`로 백엔드 API를 호출해 렌더링에 쓸 데이터를 직접 가져올 수 있다.

```js
export default async function MenusPage() {
  const getMenus = async () => {
    const res = await fetch('http://localhost:8080/api/menus');
    const data = await res.json();
    return data;
  };

  const menus = await getMenus();

  return (
    <main>
      <h1>메뉴</h1>
      <ul>
        {menus.map((menu) => (
          <li key={menu.id}>
            {menu.name} - {menu.price}원
          </li>
        ))}
      </ul>
    </main>
  );
}
```

`fetch`는 원래 브라우저 전용 API이지만, Next.js는 서버에서 실행되는 컴포넌트에서도 같은 `fetch`를 쓸 수 있도록 지원한다 — 브라우저용으로 짠 코드가 서버에서도 그대로 호환되게 하려는 목적이다. `fetch`도 `Promise`를 반환하므로, 컴포넌트 함수 자체를 `async`로 선언하고 `await`로 응답과 JSON 파싱을 순서대로 기다린다.

프론트엔드와 백엔드가 서로 다른 포트에서 떠 있으면(예: 3000과 8080), 백엔드가 CORS를 허용하지 않는 한 이 `fetch`는 실패할 수 있다 — 이 설정은 별도로 다룬다.

## 8. 정리

| 방식 | 코드 흐름 | 콜백 필요 여부 | 적합한 상황 |
|---|---|---|---|
| 동기 | 위→아래 직선 | 없음 | 순서 의존적인 작업, 짧은 작업 |
| 콜백 비동기 | 안으로 중첩 | 필수 | 레거시 API, 단순 1회 후속 처리 |
| `Promise` | `.then` 체이닝 | 반환값으로 대체 | 단계별 가공이 필요한 비동기 흐름 |
| `async`/`await` | 위→아래 직선(비동기 함수 내부) | 없음(문법적으로 숨김) | 대부분의 최신 비동기 코드, 데이터 페칭 |
