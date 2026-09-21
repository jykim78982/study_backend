---
tags: [웹, 자바스크립트, 비동기, Node.js, Next.js]
---

> 🔗 관련 노트: [[024_Node.js·npm 실습]] · [[028_Next.js App Router와 공통 레이아웃 실습]] · [[032_Next.js 실무형 메뉴 목록 페이지 만들기 — SSR, 상태, 이벤트, 컴포넌트 분리 실습]]

# 자바스크립트 비동기 처리 — 콜백에서 async·await까지

파일 읽기·쓰기를 예로, 자바스크립트가 비동기를 처리해온 방식이 동기 → 콜백 → Promise → `async`/`await` 순서로 어떻게 바뀌어왔는지, 그리고 `Promise` 체인(`.then`)·`util.promisify`·`Promise.all` 같은 주변 도구, 마지막으로 Next.js에서 서버 API 데이터를 가져올 때 이것이 어떻게 쓰이는지를 다룬다.

## 1. 자바스크립트 API의 두 얼굴 — 동기와 비동기

자바스크립트(Node.js)는 단일 스레드 이벤트 루프 기반으로 동작한다. 이 특성 때문에 시간이 걸리는 작업(파일 입출력, 네트워크 요청 등)을 처리하는 방식이 성능과 직결된다. Node.js의 내장 모듈(`fs` 등)은 같은 작업에 대해 동기형과 비동기형 두 가지 API를 함께 제공한다.

| 형태 | 이름 규칙 | 특징 | 장점 | 단점 |
|---|---|---|---|---|
| 동기(Sync) | 함수명 뒤에 `Sync` | 작업이 끝날 때까지 실행을 막는다(블로킹) | 코드가 직관적, `try...catch`로 예외 처리가 쉬움 | 작업 중 이벤트 루프가 멈춰 다른 요청을 처리 못함 |
| 비동기(Async) | `Sync` 접미사 없음 | 즉시 다음 코드로 넘어가고, 완료되면 콜백/`Promise`로 결과 전달 | 이벤트 루프를 막지 않아 응답성 유지 | 코드 흐름이 끊겨 가독성이 떨어질 수 있음 |

## 2. 동기형 함수 — 단순하지만 위험한 선택

```js
const fs = require('fs');

function handler() {
    const content = '...';
    try {
        fs.writeFileSync('example.txt', content, 'utf8');
        console.log('파일이 성공적으로 저장되었습니다!');

        const data = fs.readFileSync('example.txt', 'utf8');
        console.log('파일 내용:');
        console.log(data);
    } catch (err) {
        console.error('파일을 쓰는 중 오류가 발생했습니다:', err);
    }
}

handler();
console.log("hello~");
```

실행 결과는 코드에 적힌 순서 그대로 찍힌다.

```
파일이 성공적으로 저장되었습니다!
(파일 내용)
hello~
```

`writeFileSync`가 실행되는 동안 Node.js 프로세스는 완전히 멈춘다. `example.txt`가 1GB짜리 대용량 파일이거나 네트워크 지연이 있는 API 호출이었다면, 그 사이 다른 클라이언트의 요청은 전혀 처리되지 않는다. 서버 환경에서는 이런 블로킹을 피해야 하므로 비동기 처리가 필수적이다.

## 3. 콜백 기반 비동기 — 그리고 콜백 지옥

```js
const fs = require('fs');

function handler() {
    const content = '...';

    fs.writeFile('example.txt', content, 'utf8', function (err) {
        if (err) {
            console.error('쓰기 오류:', err);
            return;
        }
        console.log('파일이 성공적으로 저장되었습니다!');

        fs.readFile('example.txt', 'utf8', (err, data) => {
            if (err) {
                console.error('읽기 오류:', err);
                return;
            }
            console.log('파일 내용:');
            console.log(data);
        });
    });

    // fs.writeFile이 완료되기 전에 즉시 실행된다!
    console.log("안녕? (비동기 시작)");
}

handler();
console.log("hello~ (마지막 로그)");
```

`Sync`를 뗀 `writeFile`은 명령만 내리고 즉시 다음 줄로 빠진다. 그래서 실행 순서는 코드에 적힌 순서와 다르게 나온다.

```
hello~ (마지막 로그)
안녕? (비동기 시작)
파일이 성공적으로 저장되었습니다!
파일 내용: ...
```

문제는 **읽기가 쓰기 뒤에 이어져야 하는** 순서 의존성이다. 이 순서를 지키려면 읽기 코드를 쓰기의 콜백 안에 넣을 수밖에 없다. 두 단계(쓰기 → 읽기)만으로도 코드가 오른쪽으로 중첩되기 시작하고, 여기에 3단계, 4단계가 더해지면 중첩 깊이가 계속 깊어지며 코드가 피라미드 모양으로 변형된다 — 이를 **콜백 지옥(Callback Hell)**이라 부른다. 동기 코드는 위→아래 직선으로 흐르지만, 콜백 코드는 안으로, 안으로 파고드는 흐름이 된다. 필요했던 해결책은 "동기 코드처럼 위에서 아래로 읽히지만, 비동기로 동작하는 방식"이었고, 이것이 `Promise`다.

## 4. `async`/`await` — 콜백 없이 동기처럼 쓰기

```js
const fs = require('fs').promises;

// 비동기로 호출되는 함수여야만 await를 사용할 수 있다
async function handler() {
    const content = '...';
    try {
        await fs.writeFile('example.txt', content, 'utf8');
        console.log('파일이 성공적으로 저장되었습니다!');

        const data = await fs.readFile('example.txt', 'utf8');
        console.log('파일 내용:');
        console.log(data);
    } catch (err) {
        console.error('파일을 쓰는 중 오류가 발생했습니다:', err);
    }
}

handler();
console.log("hello~");
```

`fs.promises`의 `writeFile`/`readFile`은 콜백을 받지 않고 대신 **`Promise` 객체를 반환**한다. `async`는 함수가 비동기임을 선언하고 그 함수의 반환값이 `Promise`가 되게 만들며, `await`는 그 `Promise`가 해결(resolve)될 때까지 그 자리에서 기다리게 하는 키워드다. 덕분에 콜백 없이도 동기 코드처럼 위에서 아래로 읽히는 코드를 쓸 수 있고, `try...catch`로 에러 처리도 깔끔해진다.

다만 조건이 있다 — **`await`는 반드시 `async` 함수 안에서만 쓸 수 있다.** 자바스크립트는 메인 스레드 전체를 멈추는 것을 막기 위해, 기다리는 코드 블록 자체를 비동기 블록 안에만 있도록 강제한다. 실제로 실행 순서를 보면 `handler()`가 파일을 쓰는 동안 `console.log("hello~")`가 먼저 찍힌다 — `handler` 자체는 비동기 함수이므로 호출한 즉시 다음 줄로 넘어가기 때문이다.

### 4-1. 비동기로 만들어야 하는 기준

모든 함수를 비동기로 만들 필요는 없다. **시간이 오래 걸리거나 소요 시간이 들쭉날쭉한 작업, 특히 외부 호출(I/O)이 걸리는 작업**만 비동기로 만든다. 반대로 순서가 뒤 결과에 의존하는 작업은 애초에 동기적으로 짜야 한다 — 비동기가 항상 이상적인 것은 아니고, 문제가 되는 부분만 골라 비동기로 빼는 것이 현실적인 방식이다.

## 5. 비동기 함수를 만드는 입장에서는 여전히 콜백이 필요하다

`async`/`await`는 이미 `Promise`를 반환하는 함수를 **쓰는** 입장에서의 해결책이다. 하지만 시간이 걸리는 작업(피자 굽기 같은)을 직접 수행하는 함수를 **만드는** 입장이라면 얘기가 다르다 — 작업이 끝났다는 사실을 호출자에게 알리려면 여전히 콜백을 매개변수로 받아야 한다.

```js
function order() {
    console.log("주문 완료");
    return 3;
}

// cook 함수는 비동기 작업(3초 대기)을 수행한다.
// 작업 완료 후 결과를 전달하기 위해 callback 매개변수가 필수적이다.
function cook(amount, callback) {
    console.log("피자 주문이 들어왔습니다. 요리를 시작하겠습니다.");

    setTimeout(() => {
        console.log(`갓 구운 페페로니 피자 ${amount}개가 완성`);
        callback();
    }, 3000);
}

let amount = order();
cook(amount, () => {
    console.log("결제금액은 얼마입니다.");
    console.log("피자 잘 받았습니다. 맛있게 먹겠습니다.");
});
```

`setTimeout`은 지정한 시간(밀리초) 뒤에 넘겨준 함수를 실행하는 브라우저/Node 공통 기능이다(브라우저에서는 `window.setTimeout`, Node에서는 `global.setTimeout`이며, 전역 객체 이름은 생략할 수 있다). `cook`을 만드는 사람 입장에서는 "다 끝나면 이걸 불러줘"에 해당하는 `callback` 매개변수가 필수이고, `cook`을 호출하는 쪽 코드도 함께 중첩된 구조를 갖게 된다. 여기에 `cook` 이후 또 다른 비동기 작업이 이어진다면 중첩은 계속 깊어진다.

## 6. `Promise`를 반환해서 콜백에서 벗어나기

해결책은 함수가 콜백을 매개변수로 받는 대신 `Promise` 객체를 반환하도록 만드는 것이다. 그러면 호출하는 쪽은 `await`나 `.then()`으로 깔끔하게 처리할 수 있다.

```js
function cook(amount) {
    console.log("피자 주문이 들어왔습니다. 요리를 시작하겠습니다.");

    return new Promise((resolve, reject) => {
        setTimeout(() => {
            console.log(`갓 구운 페페로니 피자 ${amount}개가 완성`);
            resolve([{ name: 'Pepperoni', price: 15000 }]);
        }, 3000);
    });
}

async function handler() {
    let amount = order();

    const pizzas = await cook(amount);

    console.log("결제금액은 얼마입니다.");
    console.log(`총 금액: ${pizzas[0].price * amount}원`);
    console.log("피자 잘 받았습니다. 맛있게 먹겠습니다.");
}

handler();
```

`Promise` 생성자에 넘기는 함수는 `resolve`(성공 시 호출)와 `reject`(실패 시 호출) 두 콜백을 인자로 받는데, 이 두 콜백을 **함수 내부에서 대신 받아 관리해주는 그릇**이 바로 `Promise`다. 즉 콜백을 함수 인자로 직접 받는 대신, 콜백을 받아줄 객체(`Promise`)를 반환하는 형태로 바뀐 것이다. `cook`은 이제 순수하게 "작업 수행"에만 집중하고, 호출 측은 `await cook(amount)` 한 줄로 결과를 받을 수 있어 콜백 지옥이 사라진다.

## 7. `Promise` 체인(`.then`) — 미들웨어 시스템

`await`가 가장 직관적이지만, `.then()` 체인은 데이터 파이프라인이나 미들웨어 시스템에서 유용하다. 각 `.then()`은 이전 단계의 반환값을 받아 처리하고, 다음 단계로 넘긴다.

```js
let promise = cook(amount);

promise
    .then(pizzas => {
        console.log("1단계: 피자 목록 수신");
        return pizzas[0];
    })
    .then(pizza => {
        console.log("2단계: 이름 추출 ->", pizza.name);
        return pizza.name;
    })
    .then((name) => {
        console.log("3단계: 최종 결과 ->", name);
        console.log("결제금액은 얼마입니다.");
    })
    .catch((err) => {
        console.log("실패했습니다.", err);
    });
```

`.then`은 앞 단계의 반환값을 다음 `.then`으로 그대로 넘기므로, 값을 가공하는 단계(인코딩·변환 등)를 필요한 만큼 자유롭게 끼워 넣거나 뺄 수 있다. 이렇게 처리 단계를 체인 중간에 꽂았다 뺐다 할 수 있는 구조를 **미들웨어 방식**이라 부른다 — Express.js의 미들웨어나 데이터 처리 파이프라인처럼, 이전 단계의 결과를 변환해 다음 단계로 넘기는 구조에서는 `.then` 체인이 더 명확한 경우가 많다.

### 7-1. `await` vs `.then` 체인

| 구분 | `async`/`await` | `.then()` 체인 |
|---|---|---|
| 가독성 | 동기 코드와 비슷해 직관적 | 데이터 흐름(파이프라인)이 명확 |
| 에러 처리 | `try...catch`로 블록 단위 처리 | `.catch()`로 체인 전체 처리 |
| 활용 분야 | 일반적인 순차 로직 | 데이터 변환, 미들웨어, 파이프라인 |
| 단점 | 중첩이 깊어지면 다시 복잡해질 수 있음 | 체인이 길어지면 읽기 어려울 수 있음 |

## 8. `Promise`를 알아야 하는 사람은 누구인가

`Promise`를 직접 쓰는 이유는 딱 하나다 — **비동기 로직이 들어간 함수를 내가 직접 만들 때, 콜백을 인자로 받는 대신 `Promise`를 반환하도록 만들기 위해서다.** 이미 `Promise`를 반환하는 함수(`fetch`, `fs.promises.*` 등)를 가져다 쓰기만 하는 입장이라면 `Promise`의 내부 동작을 몰라도 `await`만으로 충분하다. 배열을 다룰 때 인덱스를 직접 쓰는 것이 하수인 것처럼, 이미 있는 것을 그대로 쓸 수 있는데 `Promise` 문법을 직접 조립하는 것은 불필요하다 — 직접 함수를 설계하는 사람만 이 구조를 알면 된다.

## 9. 기존 콜백 함수를 `Promise`로 바꾸기 — `util.promisify`

이미 콜백 기반으로 짜여 있는 함수를 매번 `new Promise`로 직접 감싸는 게 번거롭다면, Node 내장 모듈 `util`의 `promisify`로 자동 변환할 수 있다.

```js
const util = require('util');

// 기존 콜백 기반 함수
function oldCook(amount, callback) {
    setTimeout(() => {
        console.log(`갓 구운 페페로니 피자 ${amount}개가 완성`);
        callback(null, [{ name: 'Pepperoni', price: 15000 }]); // (err, data) 형식
    }, 3000);
}

const promisifiedCook = util.promisify(oldCook);

async function handler() {
    const pizzas = await promisifiedCook(3);
    console.log("결과:", pizzas);
}

handler();
```

`promisify`는 `(err, data)` 형식의 콜백을 마지막 인자로 받는 함수를 그대로 `Promise` 반환 함수로 바꿔준다. `fs.promises`처럼 이미 `Promise` 버전이 제공되는 경우는 쓸 필요가 없고, 제3자 라이브러리나 직접 만든 콜백 함수를 변환할 때 유용하다. 다만 콜백이 `(err, data)` 형식이 아니거나 여러 번 호출되는 경우(스트림 등)에는 제대로 동작하지 않을 수 있다.

## 10. 여러 작업을 동시에 — `Promise.all`

여러 비동기 작업을 동시에 시작하고, 모두 끝난 뒤에 한 번에 처리해야 할 때는 `Promise.all`을 쓴다.

```js
function fetchPizzaData() {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({ name: 'Pepperoni', price: 15000 });
        }, 4000);
    });
}

function fetchDrinkData() {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({ name: 'Cola', price: 3000 });
        }, 3000);
    });
}

async function handler() {
    const [pizza, drink] = await Promise.all([
        fetchPizzaData(),
        fetchDrinkData()
    ]);

    console.log("모든 데이터 수신 완료!");
    console.log(`총 결제 금액: ${pizza.price + drink.price}원`);
}

handler();
```

`Promise.all`은 넘겨받은 모든 `Promise`가 성공하면 그 결과들을 배열로 반환한다. 이 예에서는 피자(4초)와 음료(3초)가 동시에 시작되므로, 순서대로 `await`했다면 7초가 걸렸을 일이 약 4초 만에 끝난다 — 서로 의존하지 않는 비동기 작업을 병렬로 실행해 성능을 최적화하는 방법이다. 단, 전달한 `Promise` 중 하나라도 실패(reject)하면 `Promise.all` 전체가 즉시 실패한다.

## 11. Next.js 서버 컴포넌트에서 실제 데이터 가져오기

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

## 12. 정리

| 방식/도구 | 코드 흐름 | 적합한 상황 |
|---|---|---|
| 동기 | 위→아래 직선 | 순서 의존적인 작업, 짧은 작업 |
| 콜백 비동기 | 안으로 중첩 | 레거시 API, 단순 1회 후속 처리 |
| `Promise` 반환 + `await` | 위→아래 직선(비동기 함수 내부) | 대부분의 최신 비동기 코드, 데이터 페칭 |
| `.then` 체인 | 단계별 파이프라인 | 값을 여러 단계로 가공해야 하는 흐름 |
| `util.promisify` | 콜백 함수를 `Promise`로 변환 | 레거시 콜백 함수·라이브러리 재사용 |
| `Promise.all` | 여러 `Promise`를 동시에 기다림 | 서로 의존하지 않는 비동기 작업의 병렬 처리 |
