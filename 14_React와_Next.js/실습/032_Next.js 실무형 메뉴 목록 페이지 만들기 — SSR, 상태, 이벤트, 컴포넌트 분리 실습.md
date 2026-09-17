---
tags: [웹, 자바스크립트, Next.js, 스프링부트, 실습]
---

> 🔗 관련 노트: [[063_자바스크립트 비동기 처리 — 콜백에서 async·await까지]] · [[031_스프링 부트 백엔드 만들기 — PostgreSQL 연결과 JDBC Repository]] · [[064_리액트 컴포넌트 생명주기 — 서버·클라이언트 실행, 하이드레이션, useEffect와 상태 변수]]

# Next.js 실무형 메뉴 목록 페이지 만들기 — SSR, 상태, 이벤트, 컴포넌트 분리 실습

`app/(anon)/menus/page.js`를 중심으로, `http://localhost:8080/api/menus`를 Server Component와 Client Component로 조합해 조회·검색·필터링·정렬하는 메뉴 목록 페이지를 단계별로 완성하는 실습이다. Node.js 20.9 이상, Next.js 16.3 이상(기본으로 Turbopack 사용, `--turbopack` 옵션 불필요)을 기준으로 한다.

## 1. Server Component에서 직접 fetch — SSR의 기본 패턴

```js
export default async function MenusPage() {
  const res = await fetch("http://localhost:8080/api/menus", {
    cache: "no-store", // 요청마다 새로 렌더링(동적 렌더링)하도록 명시
  });

  if (!res.ok) {
    throw new Error(`API 요청 실패: ${res.status}`);
  }

  const menus = await res.json();

  return (
    <main>
      <h1>메뉴</h1>
      <ul>
        {menus.map((m) => (
          <li key={m.id}>{m.korName} - {m.price}원</li>
        ))}
      </ul>
    </main>
  );
}
```

Server Component는 `async` 함수로 작성할 수 있고, 이 안의 `fetch`는 브라우저가 아니라 Next.js 서버에서 실행된다. 개발자 도구 Network 탭에서 `/menus` 문서 응답 HTML에 이미 메뉴 데이터가 포함돼 있고, `localhost:8080` 요청 자체는 보이지 않는 것으로 이를 확인할 수 있다.

**클라이언트에서 `useEffect`로 가져오지 않고 서버에서 가져오는 이유는 세 가지다.**

1. **초기 렌더링 속도**: 클라이언트에서 가져오면 브라우저가 HTML을 받아도 빈 화면(또는 "로딩 중...")을 먼저 그리고, JS가 실행된 뒤에야 데이터가 채워진다. 서버에서 미리 채워 보내면 HTML을 받는 순간 바로 완성된 화면이 보인다.
2. **SEO**: 검색엔진 크롤러는 JS를 실행하지 않을 수 있다. 서버 렌더링 HTML에 데이터가 없으면 크롤러는 그 내용을 알 수 없다.
3. **보안**: 서버에서만 실행되는 코드에는 API 키나 내부 URL을 안전하게 둘 수 있다.

> Next.js 15부터 `fetch`는 기본적으로 캐시되지 않지만, `searchParams`·`cookies` 같은 요청 시점 API를 쓰지 않는 페이지는 빌드 시 정적으로 미리 렌더링될 수 있다. `cache: "no-store"`로 동적 렌더링을 명시해두면, `next build && next start` 후 DB 내용이 바뀌어도 목록이 그대로인 문제를 피할 수 있다.

## 2. Server Component가 할 수 없는 것 — 이벤트와 상태

Server Component는 `useState`, `useEffect` 같은 훅과 `onClick`, `onChange` 같은 이벤트 핸들러를 쓸 수 없다. 사용자가 입력창에 타이핑하는 값은 브라우저에만 존재하는데, 이 값을 추적하는 일은 서버에서는 불가능하다.

이 문제를 푸는 방법은 역할을 세 갈래로 나누는 것이다.

| 데이터 성격 | 관리 위치 |
|---|---|
| 서버에서 가져와 그대로 보여주는 목록 데이터 | Server Component의 지역 변수 |
| 입력 중인 값(입력창의 글자 등, 아직 확정 안 됨) | Client Component의 `useState` |
| 새로고침·공유 후에도 유지돼야 하는 조건(검색어, 필터, 정렬) | URL의 query parameter |

Server Component는 "어떤 데이터를 보여줄지"를 결정하고, Client Component는 "사용자의 입력을 받아 URL(조건)을 바꾸는 일"을 담당한다. 이 분리가 App Router의 핵심이다.

### 2-1. 왜 함수를 그냥 넘기면 안 되는가

React를 먼저 배운 사람은 "부모가 핸들러 함수를 만들어 자식에게 넘기는" 방식을 시도하기 쉽다.

```js
// ⚠️ 오류가 나는 코드
export default async function MenusPage() {
  function handleSearch(query) {
    console.log(query);
  }
  // ...
  return <SearchBar onSearch={handleSearch} />; // Functions cannot be passed...
}
```

Server Component가 Client Component에 넘기는 props는 네트워크를 건너 브라우저로 전달되므로 **직렬화 가능한 값**(문자열, 숫자, 배열, 일반 객체, JSX 등)이어야 한다. 일반 함수는 직렬화할 수 없어 오류가 난다. 그래서 URL을 바꾸는 일은 `SearchBar` 스스로 `useRouter`로 처리하도록 만든다.

## 3. 검색 — Client Component가 스스로 URL을 바꾼다

```js
// _components/SearchBar.js
"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function SearchBar() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // 새로고침·공유된 URL로 들어와도 입력창에 현재 검색어가 보이도록 초기화
  const [query, setQuery] = useState(searchParams.get("name") ?? "");

  const handleSubmit = (e) => {
    e.preventDefault();

    // 기존 파라미터(category, minPrice 등)는 유지하고 name만 바꾼다
    const params = new URLSearchParams(searchParams.toString());
    const keyword = query.trim();
    if (keyword) params.set("name", keyword);
    else params.delete("name");

    const queryString = params.toString();
    router.push(`/menus${queryString ? `?${queryString}` : ""}`);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="메뉴 검색..."
      />
      <button type="submit">검색</button>
    </form>
  );
}
```

`SearchBar`가 `router.push`로 URL을 바꾸면, Next.js가 서버에서 `page.js`를 다시 실행한다. `page.js`는 바뀐 `searchParams`를 읽어 데이터를 다시 가져온다 — 페이지 전체를 새로고침하는 게 아니라 서버에서 다시 렌더링된 결과(RSC Payload)만 받아오므로 `SearchBar`의 입력 상태 같은 클라이언트 쪽 상태는 그대로 유지된다.

**Next.js 16 주의사항**: `searchParams`는 Promise다. Next.js 15까지는 동기 접근(`searchParams.name`)이 경고와 함께 동작했지만, 16에서는 동기 접근이 완전히 제거됐다. 반드시 `await searchParams`로 꺼내야 한다.

```js
export default async function MenusPage({ searchParams }) {
  const sp = await searchParams;         // ✅ 반드시 await
  const searchQuery = sp.name || "";     // sp?.name처럼 접근하면 항상 undefined
  // ...
}
```

## 4. 필터 — 카테고리와 가격도 URL로 관리

검색어와 똑같은 원리로, 카테고리·가격 필터도 `useSearchParams`로 현재 값을 읽고 `router.push`로 URL을 바꾼다.

```js
// _components/CategoryFilter.js (핵심만)
"use client";
import { useRouter, useSearchParams } from "next/navigation";

export default function CategoryFilter() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentCategory = searchParams.get("category");

  const handleCategoryChange = (categoryId) => {
    const params = new URLSearchParams(searchParams.toString());
    if (categoryId === null) params.delete("category");
    else params.set("category", categoryId.toString());

    const queryString = params.toString();
    // scroll: false — 필터를 바꿀 때마다 페이지 맨 위로 튀지 않게 한다
    router.push(`/menus${queryString ? `?${queryString}` : ""}`, { scroll: false });
  };
  // ...
}
```

`page.js`는 `sp.category`, `sp.minPrice`, `sp.maxPrice`를 모두 읽어 백엔드 fetch URL에 그대로 실어 보낸다. 검색어 + 카테고리 + 가격을 동시에 선택해도, 매번 `new URLSearchParams(searchParams.toString())`으로 **기존 파라미터를 복사한 뒤** 필요한 값만 수정하므로 서로 다른 필터가 지워지지 않는다.

**URL에 상태를 두는 이유는 상태의 영속성이다.** `useState`로 필터를 관리하면 새로고침 시 사라지지만, URL에 두면 새로고침해도 유지되고, URL을 공유하면 다른 사람도 같은 필터 상태를 보며, 뒤로 가기로 이전 상태로 돌아갈 수도 있다.

> `useSearchParams`를 쓰는 Client Component를 **빌드 시 정적으로 렌더링되는 페이지**에서 재사용하려면 `<Suspense>`로 감싸야 한다(`<Suspense fallback={null}><CategoryFilter /></Suspense>`). 이 페이지는 `searchParams`를 쓰는 동적 페이지라 문제없지만, 다른 페이지에 재사용할 때는 주의한다.

## 5. 정렬 — `select`의 `onChange`도 Client Component 몫

```js
// _components/SortSelect.js (핵심만)
"use client";
export default function SortSelect() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentSort = searchParams.get("sort") || "popular";

  const handleSortChange = (e) => {
    const params = new URLSearchParams(searchParams.toString());
    if (e.target.value === "popular") params.delete("sort");
    else params.set("sort", e.target.value);
    router.push(`/menus?${params.toString()}`, { scroll: false });
  };
  // <select value={currentSort} onChange={handleSortChange}>...
}
```

백엔드가 정렬을 아직 지원하지 않는다면, `page.js`(Server Component) 안에서 받아온 배열을 직접 정렬한다 — 이 정렬 코드는 브라우저가 아니라 **Next.js 서버에서** 실행된다.

```js
const sortedMenus = [...menus]; // sort()는 원본을 바꾸므로 복사본에 적용
if (sort === "priceAsc") sortedMenus.sort((a, b) => a.price - b.price);
else if (sort === "priceDesc") sortedMenus.sort((a, b) => b.price - a.price);
else if (sort === "latest") sortedMenus.sort((a, b) => new Date(b.createTime) - new Date(a.createTime));
```

데이터가 많아지면 이 정렬은 DB의 `ORDER BY`로 옮기는 것이 효율적이다. 이미 fetch URL에 `sort` 파라미터를 실어 보내고 있으므로, 나중에 백엔드가 정렬을 지원하면 `page.js`의 정렬 코드만 지우면 되고 `SortSelect` 같은 화면 컴포넌트는 손댈 필요가 없다.

## 6. 컴포넌트 분리 — 코로케이션과 `MenuCard`

`page.js`가 커질수록 `MenuCard`처럼 반복되는 조각을 분리한다. 이때 원칙은 **코로케이션(Colocation)** — "함께 변하는 코드를 함께 두는 것"이다. `MenuCard`는 `/menus` 페이지에서만 쓰이므로 `app/`의 공용 `components/` 폴더가 아니라 `page.js`와 같은 디렉토리(`app/(anon)/menus/_components/`)에 둔다.

App Router에서 `_`로 시작하는 폴더는 **Private Folder**라서 라우팅 대상(URL로 접근되는 페이지)에서 제외된다. `import`가 막히는 것은 아니며, "이 컴포넌트는 이 라우트 전용"이라는 팀 내 약속(의도 표현)에 가깝다.

```js
// _components/MenuCard.js — "use client" 없음, Server Component로 렌더링
export default function MenuCard({ menu }) {
  return (
    <li>
      <img src={menu.imgSrc} alt={menu.korName} />
      <h3>{menu.korName}</h3>
      <p>{menu.engName}</p>
      <strong>{menu.price.toLocaleString("ko-KR")}원</strong>
    </li>
  );
}
```

`MenuCard`는 이벤트가 필요 없는 순수 표시용이라 `"use client"`가 없어도 되고, `page.js`(Server Component)에서 그대로 import해 서버에서 렌더링된다. 좋아요·담기 버튼처럼 이벤트가 필요한 부분만 나중에 별도의 작은 Client Component로 더 쪼갤 수 있다.

## 7. 자주 하는 실수

| 증상 | 원인 | 해결 |
|---|---|---|
| `TypeError: fetch failed (ECONNREFUSED)` | 백엔드가 8080에서 실행 중이 아님 | 백엔드 실행 확인. 켜져 있는데도 `ECONNREFUSED ::1:8080`이면 `localhost` 대신 `127.0.0.1` 사용 |
| `You're importing a component that needs useState/useSearchParams...` | 해당 파일에 `"use client"` 누락 | 파일 맨 첫 줄(주석·import보다 위)에 `"use client";` 추가 |
| `Functions cannot be passed directly to Client Components` | Server Component에서 일반 함수를 prop으로 전달 | 함수를 넘기지 말고 Client Component 안에서 `useRouter`로 직접 처리 |
| URL은 바뀌는데 데이터가 안 바뀜 | `searchParams?.name`처럼 Promise를 동기로 접근해 항상 `undefined` | `const sp = await searchParams;` 후 `sp.name` 사용 |
| 여러 필터를 조합하면 일부가 사라짐 | `URLSearchParams`를 새로 만들 때 기존 파라미터를 복사하지 않음 | `new URLSearchParams(searchParams.toString())`으로 기존 값 복사 후 수정 |
| `next build`에서 `useSearchParams() should be wrapped in a suspense boundary` | 정적 렌더링 페이지에서 `useSearchParams` 사용 | 해당 컴포넌트를 `<Suspense>`로 감싸기 |
| 정렬해도 원본 목록 순서까지 바뀜 | `menus.sort()`를 직접 호출 (원본 배열 변경) | `[...menus]`로 복사한 뒤 정렬 |

## 8. 정리

| 단계 | 내용 |
|---|---|
| 1 | Server Component에서 `fetch`로 SSR 기본 연동 — 초기 렌더링 속도·SEO·보안 이점 |
| 2 | Server Component는 훅·이벤트를 못 씀. 함수도 Client Component에 못 넘김 |
| 3 | 검색어는 Client Component의 `useState` + `router.push`로 URL 반영 |
| 4 | 필터(카테고리·가격)도 URL의 query parameter로 관리해 새로고침·공유에도 유지 |
| 5 | 정렬 값도 URL로 관리. 정렬 로직은 서버(Server Component)에서 실행 |
| 6 | 코로케이션 원칙으로 `_components`(Private Folder)에 `MenuCard` 등을 분리 |

핵심 흐름은 한 문장으로 요약된다: **Client Component가 URL을 바꾸면, Next.js가 서버에서 Server Component를 다시 실행해 데이터를 새로 가져온다.** 이벤트 처리는 Client, 데이터 조회는 Server라는 원칙만 지키면 검색·필터·정렬 모두 같은 패턴으로 확장된다.
