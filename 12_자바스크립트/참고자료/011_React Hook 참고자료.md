---
tags: [웹, 자바스크립트, React, Hook, 참고자료]
---

> 🔗 관련 노트: [[063_자바스크립트 비동기 처리 — 콜백에서 async·await까지]]

# React Hook 참고자료

React 16.8에서 도입된 Hook — 클래스 없이 함수형 컴포넌트에서 상태·생명주기 기능을 쓸 수 있게 해주는 내장 함수들 — 을 정리한 참고자료.

## 1. 등장 배경

클래스형 컴포넌트 시절에는 상태(`this.state`)와 생명주기 메서드(`componentDidMount` 등)를 쓰려면 복잡한 클래스 문법이 필요했다.

- `this` 바인딩 문제로 실수가 잦았다.
- 관련 없는 로직들이 하나의 생명주기 메서드에 몰려 코드가 복잡해졌다.
- 컴포넌트 간에 상태 관련 로직을 재사용하기 어려웠다.

Hook은 함수형 컴포넌트 안에서 이 기능들을 짧고 직관적으로 쓸 수 있게 하면서, 리액트 상태·생명주기 시스템에 "갈고리를 걸듯 연결한다"는 뜻에서 이름이 붙었다.

## 2. `useState` — 상태 관리

컴포넌트 안에서 값이 바뀌면 화면이 자동으로 다시 그려져야 하는 데이터(상태)를 만든다.

```jsx
import { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>현재 카운트: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        1 증가
      </button>
    </div>
  );
}
```

`useState(초기값)`은 `[현재 상태 값, 상태를 바꾸는 함수]` 형태의 배열을 반환한다. `setCount`를 호출하면 리액트가 변경을 감지해 리렌더링한다.

## 3. `useEffect` — 부수 효과·생명주기

컴포넌트가 화면에 나타날 때(마운트), 업데이트될 때, 사라질 때(언마운트) 실행할 로직(API 요청, 타이머, DOM 조작 등)을 처리한다.

```jsx
import { useState, useEffect } from 'react';

function UserProfile() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetch('https://api.example.com/user')
      .then(res => res.json())
      .then(data => setUser(data));
  }, []); // 빈 배열이면 처음 렌더링될 때 한 번만 실행

  return <div>{user ? user.name : '로딩 중...'}</div>;
}
```

두 번째 인자로 넘기는 의존성 배열이 `useEffect`의 실행 시점을 결정한다.

| 의존성 배열 | 실행 시점 |
|---|---|
| 생략 | 렌더링될 때마다 매번 실행 |
| `[]` | 처음 마운트될 때 단 한 번만 실행 |
| `[a, b]` | 처음 마운트될 때, 그리고 `a`나 `b`가 바뀔 때마다 실행 |

## 4. 그 밖의 자주 쓰는 내장 Hook

| Hook | 역할 |
|---|---|
| `useRef` | DOM 요소에 직접 접근하거나, 리렌더링을 일으키지 않는 값을 저장 |
| `useContext` | 전역 상태(테마, 로그인 정보 등)를 props 전달 없이 하위 컴포넌트에서 바로 꺼내 씀 |
| `useMemo`/`useCallback` | 연산 결과나 함수를 재사용(메모이제이션)해 성능 최적화 |
| `useReducer` | 복잡한 상태 변경 로직을 리듀서 패턴으로 관리 |

## 5. Hook 사용 규칙

1. **최상위(Top Level)에서만 호출한다.** 반복문·조건문·중첩 함수 안에서 호출하면 안 된다. 렌더링마다 Hook이 항상 같은 순서로 호출돼야, 리액트가 각 Hook의 상태를 순서(내부적으로는 연결 리스트 구조)로 추적할 수 있기 때문이다. 조건문 안에서 Hook 호출 여부가 렌더링마다 달라지면 이 순서가 어긋나 다른 Hook의 상태를 잘못 참조하게 된다.
2. **리액트 함수 컴포넌트 또는 커스텀 Hook 내부에서만 호출한다.** 일반 자바스크립트 함수 안에서는 호출할 수 없다.

## 6. 커스텀 Hook

이름이 `use`로 시작하는 함수를 직접 만들면, 그 안에서 다른 Hook들을 조합해 로직을 재사용할 수 있다.

```jsx
function useInput(initialValue) {
  const [value, setValue] = useState(initialValue);
  const onChange = (e) => setValue(e.target.value);
  return { value, onChange };
}

function LoginForm() {
  const email = useInput('');
  return <input type="text" {...email} />;
}
```

## 7. 정리

React Hook은 함수형 컴포넌트에서 `useState`로 상태를 저장하고, `useEffect`로 생명주기 이벤트를 처리하는 등, 리액트의 핵심 기능들을 함수 하나로 "연결"해주는 내장 함수들이다.
