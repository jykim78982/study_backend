# useState 오답노트

### 1. `useState`로 얻는 반환값의 구조와 그 사용법으로 옳은 설명은?

**문제**: `useState`로 얻는 반환값의 구조와 그 사용법으로 옳은 설명은?

1. 현재 상태 값과 상태 변경 함수를 배열 구조 분해 할당으로 받는다.
2. 상태 변경은 직접 변수에 대입하여 수행한다.
3. 객체 형태로 현재 상태와 변경 함수를 제공한다.
4. `useState`는 항상 문자열만 관리할 수 있다.

**정답: 1번**

`useState`를 호출하면 리액트는 딱 2개의 요소를 가진 배열 `[currentState, setterFunction]`을 반환한다.

- 첫 번째 요소: 현재의 상태(state) 값
- 두 번째 요소: 상태를 새롭게 업데이트해주는 상태 변경 함수(setter)

자바스크립트의 배열 구조 분해 할당(array destructuring) 문법으로 이 두 요소를 원하는 이름으로 꺼내 쓴다.

```js
import { useState } from 'react';

function Counter() {
  // [현재 상태 값, 상태 변경 함수] = useState(초기값)
  const [count, setCount] = useState(0);

  return (
    <button onClick={() => setCount(count + 1)}>
      클릭 횟수: {count}
    </button>
  );
}
```

- **2번이 오답인 이유**: `count = count + 1`처럼 변수에 직접 대입해서 값을 바꾸면, 리액트는 값이 바뀐 사실을 알 방법이 없어 화면이 다시 그려지지 않는다(리렌더링 미발생). 반드시 두 번째 반환값인 setter 함수(`setCount(count + 1)`)를 호출해야만 리액트가 변경을 감지하고 화면을 갱신한다.
- **3번이 오답인 이유**: `useState`는 객체(`{ value, setValue }`)가 아니라 **배열**(`[value, setValue]`)을 반환한다. 배열을 쓰는 이유는, 배열 구조 분해 할당을 이용하면 한 컴포넌트 안에서 `useState`를 여러 번 써도 변수 이름을 원하는 대로 자유롭게 지을 수 있기 때문이다.

  ```js
  // 객체였다면 키 이름이 고정되어 이름을 바꿔 쓰기 번거로웠을 것이다.
  const [name, setName] = useState('홍길동');
  const [age, setAge] = useState(20);
  ```

- **4번이 오답인 이유**: `useState`는 숫자·문자열·불리언 같은 기본형부터 객체·배열·`null`·`undefined`까지, 자바스크립트의 어떤 데이터 타입이든 제약 없이 관리할 수 있다.

**핵심 요약**

```js
const [state, setState] = useState(initialValue);
```

- `useState`는 2개짜리 배열을 반환한다.
- 배열 구조 분해 할당으로 값을 꺼낸다.
- 상태 변경은 직접 대입 금지, 반드시 setter 함수를 호출해야 리렌더링이 일어난다.

tags: #웹 #자바스크립트 #React #useState #상태변수 #구조분해할당

> 🔗 관련 노트: [[011_React Hook 참고자료]]
