---
tags: [웹, 자바스크립트, Next.js, 스프링부트, 실습]
---

> 🔗 관련 노트: [[063_자바스크립트 비동기 처리 — 콜백에서 async·await까지]] · [[031_스프링 부트 백엔드 만들기 — PostgreSQL 연결과 JDBC Repository]]

# Next.js에서 스프링 부트 API 연동 — 메뉴 목록과 검색 폼 만들기 실습

`ncafe/frontend`의 메뉴 페이지가 `ncafe/backend`의 `/api/menus`를 실제로 호출해 목록을 렌더링하고, 이름 검색 폼을 추가해 URL 쿼리 파라미터로 필터링된 결과를 보여주도록 만든 실습이다. 아직 다루지 않은 Hook, CORS, 서버/클라이언트 컴포넌트 구분이 등장하므로, 지금은 "이렇게 동작하는구나" 정도로 미리 보는 단계다.

## 1. 기본 연결 확인

백엔드(`ncafe/backend`, 8080번 포트)와 프론트엔드(`ncafe/frontend`, 3000번 포트)가 각각 떠 있는 상태에서 시작한다.

```
curl http://localhost:8080/api/menus
curl http://localhost:3000
```

`curl`이 없으면 브라우저로 두 주소를 직접 열어 확인해도 된다. 이 시점의 메뉴 페이지는 목업 시절과 똑같이 `fetch`로 데이터를 받아 목록만 찍는 구조다.

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
            {menu.korName} - {menu.price}원
          </li>
        ))}
      </ul>
    </main>
  );
}
```

Next.js의 서버 컴포넌트(`async` 컴포넌트)는 서버 사이드에서 `fetch`를 직접 실행할 수 있어서, 그 코드가 클라이언트로 전송되지 않고 SEO에도 유리하다. 다만 이 방식은 "서버 렌더링 시점"에 데이터를 가져오므로, 사용자가 검색어를 입력해도 자동으로는 갱신되지 않는다 — 이 문제를 다음 단계에서 다룬다.

프론트엔드(3000)와 백엔드(8080)처럼 포트가 다르면 브라우저가 CORS 정책으로 요청을 막을 수 있다. 개발 단계에서는 백엔드에 `@CrossOrigin` 또는 `CorsFilter`로 `localhost:3000`을 허용해줘야 한다.

## 2. 서버 컴포넌트에서 `searchParams`로 쿼리 읽기

URL의 쿼리 파라미터(`?name=...`)를 서버 컴포넌트가 직접 읽어, 그 값을 백엔드 요청에 그대로 실어 보낸다. 클라이언트 컴포넌트에서 쓰는 `useSearchParams` 훅과 달리, 서버 컴포넌트는 `searchParams`를 함수의 props로 바로 받는다.

```js
export default async function MenusPage({ searchParams }) {
  const params = await searchParams;
  const name = params.name || '';
  const category = params.category || '';
  const minPrice = params.minPrice || '';
  const maxPrice = params.maxPrice || '';

  const getMenus = async () => {
    let url = 'http://localhost:8080/api/menus';

    const params = new URLSearchParams();
    if (name) params.append('name', name);
    if (category) params.append('category', category);
    if (minPrice) params.append('minPrice', minPrice);
    if (maxPrice) params.append('maxPrice', maxPrice);

    const queryString = params.toString();
    if (queryString) {
      url += `?${queryString}`;
    }

    const res = await fetch(url);
    const data = await res.json();
    return data;
  };

  const menus = await getMenus();
  // ...
}
```

브라우저 주소창에서 `http://localhost:3000/menus?name=아메리카노`로 직접 이동하면, 서버 컴포넌트가 다시 실행되면서 `name=아메리카노`를 백엔드에 그대로 전달하고, 목록에는 "아메리카노"만 남는다.

이 방식은 "서버 렌더링 기반 검색"이다. URL을 바꿀 때마다 서버가 데이터를 다시 가져와 HTML을 새로 만들기 때문에 SEO에 유리하고 초기 로딩부터 검색 결과가 바로 보이지만, 사용자가 입력할 때마다 페이지가 통째로 새로고침된다는 단점이 있다.

`URLSearchParams`로 쿼리 문자열을 만들면 한글 등의 값이 자동으로 인코딩된다 — 문자열을 직접 이어붙이면(`url + '?name=' + name`) 인코딩 문제가 생길 수 있으므로 피한다.

## 3. 클라이언트 컴포넌트로 검색 폼 만들기

폼은 입력값 같은 상태를 다뤄야 하므로 클라이언트 컴포넌트로 분리한다.

```js
// SearchForm.js
'use client';

import { useRouter } from 'next/navigation';

export default function SearchForm() {
  const router = useRouter();

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const name = formData.get('name');

    const params = new URLSearchParams();
    if (name) {
      params.append('name', name);
    }

    const queryString = params.toString();
    const newUrl = queryString ? `?${queryString}` : '';

    router.push(newUrl);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" name="name" placeholder="메뉴 이름으로 검색" />
      <button type="submit">검색</button>
    </form>
  );
}
```

파일 맨 위의 `'use client'`가 꼭 필요하다 — `useRouter`는 클라이언트 사이드에서만 쓸 수 있는 Hook이다. 폼을 제출하면 `router.push`로 URL을 쿼리 파라미터가 붙은 형태로 바꾸고, 그 URL 변경이 서버 컴포넌트를 다시 실행시켜 새로운 검색 결과를 가져오게 만든다 — 페이지 새로고침 없이 부드럽게 전환하려면 `useTransition`이나 서버 액션이 필요하지만, 여기서는 URL 기반 서버 렌더링 방식을 그대로 쓴다.

`page.js`에서는 이 컴포넌트를 목록 위에 배치하기만 하면 된다.

```js
import SearchForm from './SearchForm';
// ...
<h1>메뉴</h1>
<SearchForm />
<ul>...</ul>
```

## 4. 검색 상태 표시와 전체 보기

검색 중인지, 결과가 비어 있는지를 사용자에게 명확히 보여주고, 손쉽게 초기 상태로 돌아갈 수 있는 버튼을 추가한다.

```js
// app/(anon)/menus/page.js
import SearchForm from './SearchForm';

export default async function MenusPage({ searchParams }) {
  const params = await searchParams;
  const name = params.name || '';
  const category = params.category || '';
  const minPrice = params.minPrice || '';
  const maxPrice = params.maxPrice || '';

  const getMenus = async () => {
    let url = 'http://localhost:8080/api/menus';
    const params = new URLSearchParams();
    if (name) params.append('name', name);
    if (category) params.append('category', category);
    if (minPrice) params.append('minPrice', minPrice);
    if (maxPrice) params.append('maxPrice', maxPrice);

    const queryString = params.toString();
    if (queryString) {
      url += `?${queryString}`;
    }

    const res = await fetch(url);
    const data = await res.json();
    return data;
  };

  const menus = await getMenus();
  const isSearching = name || category || minPrice || maxPrice;

  return (
    <main>
      <h1>메뉴</h1>

      <SearchForm />

      {isSearching && (
        <p style={{ color: 'gray', fontSize: '14px' }}>
          검색 조건: {name && `이름: ${name}`}
        </p>
      )}

      {menus.length === 0 ? (
        <p>검색 결과가 없습니다.</p>
      ) : (
        <ul>
          {menus.map((menu) => (
            <li key={menu.id}>
              {menu.korName} - {menu.price}원
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
```

"전체 보기" 버튼은 `SearchForm` 안에 함께 둔다. 모든 쿼리 파라미터를 지우고 기본 페이지로 돌아가려면 `router.push('/menus')`처럼 경로만 넘기면 된다.

```js
// SearchForm.js — 전체 보기 버튼 추가
const handleReset = () => {
  router.push('/menus');
};

// ...
<button type="button" onClick={handleReset}>전체 보기</button>
```

검색을 했는지, 어떤 조건으로 검색했는지, 결과가 없을 때 무엇을 보여줄지, 쉽게 초기 상태로 돌아갈 수 있는지 — 이런 부분들이 API 연동만큼 사용자 경험에 중요하다.

## 5. 자주 하는 실수

| 증상 | 원인 | 해결 |
|---|---|---|
| `Failed to fetch`/`Network Error` | 백엔드(8080)가 꺼져 있거나 URL 불일치 | 백엔드 서버 실행 여부, URL 확인 |
| CORS 에러(`Access-Control-Allow-Origin`) | 브라우저가 다른 포트로의 요청을 막음 | 백엔드에 `@CrossOrigin` 또는 `CorsFilter`로 `localhost:3000` 허용 |
| `searchParams`가 `undefined` | 페이지가 서버 컴포넌트가 아니거나 Next.js 버전 문제 | `export default async function`으로 서버 컴포넌트인지 확인 |
| 한글 검색 시 400 에러 | URL을 문자열로 직접 이어붙임 | `URLSearchParams`로 쿼리 문자열 생성 |
| `useRouter is not a function` | `'use client'` 지시어 누락 | 파일 맨 위에 `'use client';` 추가 |
| 폼 제출 시 페이지 전체 새로고침 | `e.preventDefault()` 누락 | `handleSubmit`에서 확인 |

## 6. 정리

| 단계 | 내용 |
|---|---|
| 1 | 서버 컴포넌트에서 `fetch`로 스프링 API 기본 연결 확인 |
| 2 | `searchParams`로 URL 쿼리를 읽어 서버 렌더링 기반 검색 구현 |
| 3 | `'use client'` 검색 폼에서 `router.push`로 URL을 바꿔 서버 컴포넌트 재실행 유도 |
| 4 | 검색 상태 메시지, 빈 결과 처리, 전체 보기 버튼으로 UX 보완 |
