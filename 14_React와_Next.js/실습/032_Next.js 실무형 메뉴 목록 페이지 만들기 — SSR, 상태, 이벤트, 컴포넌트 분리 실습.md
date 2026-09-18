---
tags: [웹, 자바스크립트, TypeScript, Next.js, 스프링부트, 실습]
---

> 🔗 관련 노트: [[063_자바스크립트 비동기 처리 — 콜백에서 async·await까지]] · [[031_스프링 부트 백엔드 만들기 — PostgreSQL 연결과 JDBC Repository]] · [[033_ncafe 메뉴·카테고리 API 만들기 — DTO와 DI]] · [[064_리액트 컴포넌트 생명주기 — 서버·클라이언트 실행, 하이드레이션, useEffect와 상태 변수]] · [[066_타입스크립트 — 왜 필요한가, 타입 시스템과 인터페이스, 그리고 생성자 함수]]

# Next.js 실무형 메뉴 목록 페이지 만들기 — SSR, 상태, 이벤트, 컴포넌트 분리 실습

**대상**: Spring Boot API를 만들었지만 Next.js 프론트엔드와 연동 경험이 없거나, TypeScript와 React 컴포넌트 생명주기가 헷갈리는 사람

**목표**: `localhost:8080`의 Spring Boot API 데이터를 Next.js App Router로 가져와서, 카테고리 필터링과 검색 기능이 포함된 `MenuCard` 목록을 렌더링한다

**완성물**: `localhost:3000/menus`에서 카테고리 탭을 클릭하거나 검색어를 입력하면 서버 API를 호출해 메뉴 목록이 실시간으로 갱신되는 Next.js 페이지

이 노트의 번호가 사전 조건이 되는 백엔드 노트의 번호보다 앞서 있다는 점을 짚어둔다. 노트 번호는 각 노트를 작성한 순서를 나타낼 뿐 학습 순서를 보장하지 않는데, 이 프론트엔드 실습은 원래 먼저 만들어져 있던 노트를 나중에 새로 만든 백엔드 DTO 실습의 구조에 맞춰 갱신하면서 이런 역전이 생겼다. 실제로 진행할 때는 백엔드의 DTO·컨트롤러 작업을 먼저 끝내고 이 노트를 따라가면 된다.

**사전 조건**

- Next.js 14+ (App Router), TypeScript, Tailwind CSS(또는 자체 CSS 유틸리티) 프로젝트가 준비되어 있어야 한다.
- [[033_ncafe 메뉴·카테고리 API 만들기 — DTO와 DI]]에서 만든 Spring Boot 애플리케이션(`localhost:8080`)이 실행 중이어야 한다.
- `app/(anon)/menus/` 폴더가 이미 존재한다고 가정한다.

## 1. 서버 컴포넌트와 클라이언트 컴포넌트의 차이

React 18 이후 Next.js에서는 컴포넌트가 실행되는 위치(서버/클라이언트)를 명시해야 한다. 이 단계에서는 왜 두 가지가 필요한지, 그리고 어떤 컴포넌트가 어디에 속하는지 개념을 정리한다.

### 1-1. 서버 컴포넌트와 클라이언트 컴포넌트의 차이

**서버 컴포넌트(Server Component)**

- 서버에서 실행되어 HTML 문자열을 생성한다.
- `useEffect`, `useState`, 이벤트 핸들러(`onClick`)를 사용할 수 없다.
- 데이터베이스에 직접 접근할 수 있다.
- 번들 사이즈가 0이다(클라이언트로 전송되는 JS 코드가 없음).

**클라이언트 컴포넌트(Client Component)**

- 브라우저에서 실행된다.
- `useEffect`, `useState`, 이벤트 핸들러를 사용할 수 있다.
- 서버에서 데이터를 가져와야 할 때는 `fetch`를 사용해야 한다.
- 인터랙션(클릭, 입력)이 필요한 컴포넌트는 반드시 클라이언트 컴포넌트여야 한다.

### 1-2. 이번 실습의 구조 설계

우리가 만들 `menus/page.tsx`는 초기 데이터(전체 메뉴 목록)를 서버에서 가져와야 하므로 서버 컴포넌트로 시작한다. 하지만 사용자가 카테고리를 클릭하거나 검색어를 입력할 때 데이터를 다시 가져와야 하므로, 이 인터랙션을 처리하는 하위 컴포넌트(`MenuList` 등)는 클라이언트 컴포넌트로 만든다.

**✅ 확인**

- 서버 컴포넌트는 `async` 함수를 사용할 수 있고, 데이터베이스에 직접 접근할 수 있다.
- 클라이언트 컴포넌트는 `'use client'` 지시어가 필요하고, `useState`와 `useEffect`를 사용할 수 있다.
- 인터랙션(클릭, 입력)이 필요한 컴포넌트는 클라이언트 컴포넌트여야 한다.

**🎓 newlec 쌤의 코멘트**

많은 분들이 "React는 클라이언트에서 돌리는 거 아닌가?"라고 묻는다. Next.js App Router에서는 기본값이 서버 컴포넌트다. 서버 컴포넌트는 서버에서 실행되어 HTML을 만들어 클라이언트로 보내므로, 초기 로딩 속도가 빠르고 보안이 좋다. 하지만 사용자가 버튼을 누르는 순간, 서버는 그 이벤트를 알 수 없다. 그래서 "사용자가 뭔가 할 때" 반응해야 하는 컴포넌트만 `'use client'`를 붙여 클라이언트로 내려보낸다. 이 경계를 잘 잡는 것이 Next.js 실력의 핵심이다.

**📝 이 단계의 핵심**

- 서버 컴포넌트: 데이터 가져오기, HTML 생성.
- 클라이언트 컴포넌트: 상태 관리, 이벤트 처리.

## 2. 타입 정의와 API 호출 함수

TypeScript는 컴파일 타임에 타입 오류를 잡아준다. API에서 오는 데이터의 구조를 정확히 정의해야 한다.

### 2-1. 타입 파일 만들기

이 파일은 API 서버가 DTO로 보내온 내용을 담는 그릇이다. API의 구조와 일치하도록 작성해야 한다.

파일: `app/(anon)/menus/types.ts`

```ts
// 카테고리 정보
export interface Category {
  id: number;
  name: string;
  count: number;
}

// 메뉴 요약 정보 (API가 반환하는 형태)
export interface MenuSummary {
  id: number;
  slug: string;
  korName: string;
  engName: string;
  price: number;
  categoryId: number;
  categoryName: string;
  status: string;
  isNew: boolean;
  imgSrc: string;
  favoriteCount: number;
  createdAt: string;
}
```

### 2-2. API 호출 함수 만들기

파일: `app/(anon)/menus/api.ts`

```ts
import { Category, MenuSummary } from './types';

// Spring Boot API의 기본 URL
const API_BASE_URL = 'http://localhost:8080/api';

// 카테고리 목록 가져오기
export async function fetchCategories(): Promise<Category[]> {
  const res = await fetch(`${API_BASE_URL}/categories`, {
    // 서버 컴포넌트에서 fetch를 사용할 때 캐시를 방지하기 위해
    // next: { revalidate: 0 } 또는 cache: 'no-store' 를 사용할 수 있다.
    // 여기서는 간단히 no-store로 설정한다.
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error('Failed to fetch categories');
  }

  return res.json();
}

// 메뉴 목록 가져오기 (필터 파라미터 포함)
export async function fetchMenus(params: {
  name?: string;
  category?: number;
  minPrice?: number;
  maxPrice?: number;
}): Promise<MenuSummary[]> {
  const searchParams = new URLSearchParams();

  if (params.name) searchParams.append('name', params.name);
  if (params.category) searchParams.append('category', params.category.toString());
  if (params.minPrice) searchParams.append('minPrice', params.minPrice.toString());
  if (params.maxPrice) searchParams.append('maxPrice', params.maxPrice.toString());

  const queryString = searchParams.toString();
  const url = `${API_BASE_URL}/menus${queryString ? `?${queryString}` : ''}`;

  const res = await fetch(url, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error('Failed to fetch menus');
  }

  return res.json();
}
```

**✅ 확인**

- `types.ts`에 `Category`와 `MenuSummary` 인터페이스가 정의되어 있다.
- `api.ts`에 `fetchCategories`와 `fetchMenus` 함수가 있다.
- `fetchMenus`는 `name`, `category`, `minPrice`, `maxPrice` 파라미터를 받아 URL 쿼리 스트링을 생성한다.

**🎓 newlec 쌤의 코멘트**

TypeScript의 `interface`는 객체의 "모양"을 정의한다. `MenuSummary`의 `price`가 `number`라고 정의하면, 나중에 API에서 `price`가 문자열로 오면 컴파일러가 에러를 낸다. 이는 런타임 에러보다 훨씬 일찍 문제를 발견하게 해준다. `fetch` 함수의 `cache: 'no-store'` 옵션은 Next.js가 응답을 캐시하지 않고 항상 서버에 새로운 요청을 보내라는 뜻이다. 메뉴 목록처럼 실시간성이 중요한 데이터에는 이 옵션이 중요하다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Type 'unknown' is not assignable to type 'Category[]'` | `res.json()`의 반환 타입이 `unknown` | `res.json() as Promise<Category[]>` 또는 `await res.json()` 후 타입 명시 |
| CORS Error | Spring Boot에서 CORS 설정 누락 | Spring Boot의 `WebMvcConfigurer`에 CORS 설정 추가 |

**📝 이 단계의 핵심**

- TypeScript 인터페이스로 API 응답의 구조를 정의한다.
- `fetch`의 `cache: 'no-store'`로 캐시를 방지한다.

## 3. `page.tsx`에서 초기 데이터 가져오기

`page.tsx`는 서버 컴포넌트다. 여기서 `fetch`를 사용하여 초기 데이터(전체 메뉴, 카테고리)를 가져온다.

### 3-1. `page.tsx` 수정

파일: `app/(anon)/menus/page.tsx`

```tsx
import { fetchCategories, fetchMenus } from './api';
import MenuList from './MenuList'; // 아직 만들지 않은 컴포넌트, 다음 단계에서 만들 것

// 서버 컴포넌트는 async 함수를 사용할 수 있다.
export default async function MenuPage() {
  // 서버에서 실행되는 시점에 데이터를 가져온다.
  // 이 코드는 브라우저에서 실행되지 않는다.
  const [categories, initialMenus] = await Promise.all([
    fetchCategories(),
    fetchMenus({}),
  ]);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">NCafe 메뉴</h1>

      {/*
        MenuList는 클라이언트 컴포넌트다.
        서버에서 가져온 데이터를 props로 전달한다.
      */}
      <MenuList
        initialCategories={categories}
        initialMenus={initialMenus}
      />
    </div>
  );
}
```

**✅ 확인**

- `page.tsx`가 `async` 함수다.
- `Promise.all`로 카테고리와 메뉴를 동시에 가져온다.
- `MenuList` 컴포넌트에 `initialCategories`와 `initialMenus`를 props로 전달한다.

**🎓 newlec 쌤의 코멘트**

`Promise.all`은 여러 개의 비동기 작업을 동시에 실행하고, 모두 완료되면 결과를 배열로 반환한다. 카테고리와 메뉴는 서로 독립적인 요청이므로, 순차적으로 기다리는 것보다 `Promise.all`을 사용하는 것이 빠르다. 서버 컴포넌트에서 `fetch`를 사용하면, Next.js가 서버에서 데이터를 가져와 HTML로 변환한 후 클라이언트로 보내므로, 초기 화면이 빠르게 렌더링된다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Cannot read properties of undefined (reading 'map')` | fetch 실패 시 `undefined` 반환 | `try-catch` 블록으로 에러 처리 |
| Hydration Error | 서버와 클라이언트에서 렌더링된 HTML이 다름 | 서버에서 랜덤 값(날짜, ID)을 렌더링하지 않도록 주의 |

**📝 이 단계의 핵심**

- 서버 컴포넌트에서 `async`/`await`로 데이터를 가져온다.
- `Promise.all`로 병렬 요청을 처리한다.

## 4. `MenuList` — 클라이언트 컴포넌트에서 상태와 이벤트 처리

이제 사용자가 카테고리를 클릭하거나 검색어를 입력할 때 데이터를 다시 가져와야 한다. 이 로직은 클라이언트 컴포넌트에서 처리한다.

### 4-1. `MenuList` 컴포넌트 만들기

파일: `app/(anon)/menus/MenuList.tsx`

```tsx
// 메뉴 목록의 본문 — 왼쪽 필터(카테고리·가격) + 오른쪽 목록(툴바·카드·페이지). 마크업은 초기 목업 페이지 그대로.
// 필터·검색·정렬을 상태로 들고 있어야 해서(페이지 리로드 없이 반응) 클라이언트 컴포넌트. 첫 화면 데이터는 page.tsx 가 준다.
'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import Pager from '@/app/_components/Pager';
import { Category, MenuSummary } from './types';
import { fetchMenus } from './api';
import MenuCard from './MenuCard';

// 백엔드는 minPrice·maxPrice 를 둘 다 받아야 가격 필터가 걸린다 → 상한 없는 구간은 충분히 큰 값으로.
const PRICES = [
    { value: '0-5000', label: '~5,000원', min: 0, max: 5000 },
    { value: '5000-7000', label: '5,000~7,000원', min: 5000, max: 7000 },
    { value: '7000-', label: '7,000원~', min: 7000, max: 1_000_000 },
];

type Sort = 'popular' | 'latest' | 'priceAsc' | 'priceDesc';
const SORTS: Record<Sort, (a: MenuSummary, b: MenuSummary) => number> = {
    popular: (a, b) => b.favoriteCount - a.favoriteCount,
    latest: (a, b) => b.createdAt.localeCompare(a.createdAt),
    priceAsc: (a, b) => a.price - b.price,
    priceDesc: (a, b) => b.price - a.price,
};

interface MenuListProps {
    initialCategories: Category[];
    initialMenus: MenuSummary[];
    initialCategory?: number | null;
}

export default function MenuList({ initialCategories, initialMenus, initialCategory = null }: MenuListProps) {
    // 상태 관리: 선택된 카테고리·가격 구간, 검색어, 정렬, 목록, 로딩
    const [category, setCategory] = useState<number | null>(initialCategory);
    const [price, setPrice] = useState<string | null>(null);
    const [search, setSearch] = useState<string>('');
    const [sort, setSort] = useState<Sort>('popular');
    const [menus, setMenus] = useState<MenuSummary[]>(initialMenus);
    const [loading, setLoading] = useState<boolean>(false);

    // 첫 화면은 page.tsx 가 준 목록을 그대로 쓰고, 필터가 바뀔 때부터 API 를 부른다.
    // (백엔드 우선순위: name > category > price — 하나만 적용된다)
    const first = useRef(true);
    useEffect(() => {
        if (first.current) {
            first.current = false;
            return;
        }

        const range = PRICES.find((p) => p.value === price);
        const params: { name?: string; category?: number; minPrice?: number; maxPrice?: number } = {};
        if (search) {
            params.name = search;
        } else if (category !== null) {
            params.category = category;
        } else if (range) {
            params.minPrice = range.min;
            params.maxPrice = range.max;
        }

        let stale = false;
        setLoading(true);
        fetchMenus(params)
            .then((data) => {
                if (!stale) setMenus(data);
            })
            .catch((error) => console.error('Failed to load menus:', error))
            .finally(() => {
                if (!stale) setLoading(false);
            });
        return () => {
            stale = true;
        };
    }, [category, price, search]);

    // "전체" 는 API 에 없고 프론트가 합계로 만든다
    const TOTAL = initialCategories.reduce((n, c) => n + c.count, 0);
    const sorted = [...menus].sort(SORTS[sort]);

    // 링크는 원래 주소(?category= · ?price=)를 그대로 두고, 클릭만 가로채 상태로 처리한다(새 탭 열기 등은 그대로 동작).
    // 카테고리와 가격은 백엔드가 동시에 받지 않으므로 하나를 고르면 다른 쪽은 푼다.
    const pickCategory = (id: number | null) => {
        setCategory(id);
        setPrice(null);
    };
    const pickPrice = (value: string) => {
        setPrice(value);
        setCategory(null);
    };

    return (
        <div className="site-body site-body:aside">
            {/* ----- 좌측 필터: m3-card + m3-list (가구·물품) ----- */}
            <aside className="site-aside">
                <section className="m3-card card:outlined card-padding:self">
                    <div className="card-header">
                        <div className="card-titles">
                            <h2 className="card-subhead">카테고리</h2>
                        </div>
                    </div>
                    <ul className="m3-list list-size:compact">
                        {[{ id: null, name: '전체', count: TOTAL }, ...initialCategories].map((c) => {
                            const active = price === null && c.id === category;
                            return (
                                <li key={c.name}>
                                    <Link
                                        href={c.id === null ? '/menus' : `/menus?category=${c.id}`}
                                        className={`list-item${active ? ' list-active' : ''}`}
                                        aria-current={active ? 'page' : undefined}
                                        onClick={(e) => {
                                            e.preventDefault();
                                            pickCategory(c.id);
                                        }}
                                    >
                                        <span className="list-content">{c.name}</span>
                                        <span className="list-trailing">{c.count}</span>
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                </section>

                <section className="m3-card card:outlined card-padding:self">
                    <div className="card-header">
                        <div className="card-titles">
                            <h2 className="card-subhead">가격</h2>
                        </div>
                    </div>
                    <ul className="m3-list list-size:compact">
                        {PRICES.map((p) => {
                            const active = p.value === price;
                            return (
                                <li key={p.value}>
                                    <Link
                                        href={`/menus?price=${p.value}`}
                                        className={`list-item${active ? ' list-active' : ''}`}
                                        aria-current={active ? 'page' : undefined}
                                        onClick={(e) => {
                                            e.preventDefault();
                                            pickPrice(p.value);
                                        }}
                                    >
                                        <span className="list-content">{p.label}</span>
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                </section>
            </aside>

            {/* ----- 우측 목록: 툴바 + m3-grid(MenuCard) + m3-pager ----- */}
            <section className="site-content">
                <div className="m3-toolbar">
                    <p className="toolbar-start" aria-live="polite">
                        {loading ? (
                            '불러오는 중...'
                        ) : (
                            <>
                                총 <strong>{menus.length}</strong>개의 메뉴
                            </>
                        )}
                    </p>
                    <div className="toolbar-end">
                        <div className="m3-text-field field:outlined field-label:none width:ex" style={{ '--width-ex': '12rem' }}>
                            <input
                                type="search"
                                name="name"
                                placeholder="메뉴 검색"
                                aria-label="메뉴 검색"
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                            />
                        </div>
                        <div className="m3-text-field field:outlined field-label:none width:ex" style={{ '--width-ex': '9rem' }}>
                            <select name="sort" value={sort} aria-label="정렬" onChange={(e) => setSort(e.target.value as Sort)}>
                                <option value="popular">인기순</option>
                                <option value="latest">최신순</option>
                                <option value="priceAsc">낮은 가격순</option>
                                <option value="priceDesc">높은 가격순</option>
                            </select>
                        </div>
                    </div>
                </div>

                {sorted.length === 0 && !loading ? (
                    <p className="text-align:center color:text-muted">조건에 맞는 메뉴가 없습니다.</p>
                ) : (
                    <ul className="m3-grid grid-cols:3">
                        {sorted.map((menu) => (
                            <MenuCard key={menu.id} menu={menu} />
                        ))}
                    </ul>
                )}

                {/* API 가 아직 전체 목록을 한 번에 주므로 1페이지. 페이징 응답이 생기면 page·totalPages 를 그 값으로. */}
                <Pager page={1} totalPages={1} href="/menus" params={{}} className="margin-top:9" />
            </section>
        </div>
    );
}
```

**✅ 확인**

- `MenuList.tsx` 파일 상단에 `'use client'`가 있다.
- `useState`로 `category`, `price`, `search`, `sort`, `menus`, `loading`을 관리한다.
- `useEffect`의 의존성 배열에 `[category, price, search]`가 있다.
- 카테고리·가격 목록과 검색 입력창, 정렬 셀렉트가 렌더링된다.

**🎓 newlec 쌤의 코멘트**

`useEffect`의 의존성 배열 `[category, price, search]`가 매우 중요하다. 이 배열에 있는 값이 변경될 때마다 `useEffect` 내부의 함수가 다시 실행된다. 즉, 사용자가 카테고리를 클릭하면 `category`가 변경되고, `useEffect`가 실행되어 새로운 데이터를 가져온다. `useEffect`는 컴포넌트가 마운트된 후에도 실행되므로, 초기 데이터(`initialMenus`)를 가져온 후에도 사용자가 필터를 변경하면 자동으로 갱신된다. 다만 마운트 시점에는 이미 `page.tsx`가 넘겨준 초기 데이터가 있으므로, `useRef(true)`로 첫 실행 여부를 표시해두고 첫 실행에는 API를 다시 부르지 않는다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `useEffect`가 무한 루프 | 의존성 배열에 객체나 배열을 직접 넣음 | 의존성 배열에 원시 타입(숫자, 문자열)만 넣기 |
| `Cannot read properties of undefined (reading 'map')` | `menus`가 초기값 없이 `undefined` | `useState<MenuSummary[]>(initialMenus)`로 초기값 설정 |
| `useEffect`가 마운트 직후에도 불필요하게 API를 호출함 | 첫 실행을 구분하지 않음 | `useRef`로 첫 실행 여부를 표시하고 조기 `return` |
| 빠르게 검색어를 바꾸면 화면이 이전 결과로 되돌아감 | 오래된 요청의 응답이 최신 요청보다 늦게 도착 | `stale` 플래그로 낡은 응답의 `setState` 무시 |

**📝 이 단계의 핵심**

- `useEffect`의 의존성 배열로 데이터 갱신을 트리거한다.
- `useState`로 UI 상태를 관리한다.

## 5. `MenuCard` 컴포넌트 만들기

개별 메뉴를 표시하는 `MenuCard` 컴포넌트를 만든다. 이 컴포넌트는 인터랙션이 없으므로 서버 컴포넌트로 만들 수도 있지만, `MenuList`가 클라이언트 컴포넌트이므로 자식 컴포넌트도 클라이언트 컴포넌트로 만드는 것이 일반적이다.

### 5-1. `MenuCard` 컴포넌트 만들기

파일: `app/(anon)/menus/MenuCard.tsx`

```tsx
// 메뉴 카드 — m3-card. 사진(4:3) · 카테고리 · 이름 · 영문명 · 가격 · 동작(좋아요·담기).
// 사진 위 표시(NEW·품절)는 card-media-badge 에. 값은 백엔드의 MenuSummary 그대로.
'use client';

import Link from 'next/link';
import { MenuSummary } from './types';

interface MenuCardProps {
    menu: MenuSummary;
}

export default function MenuCard({ menu }: MenuCardProps) {
    const href = `/menus/${menu.slug}`;
    const imgSrc = menu.imgSrc ?? `/images/menus/${menu.slug}.svg`;

    return (
        <li className="m3-card card:outlined card-size:compact">
            {/* 이미지 + 배지 */}
            <Link href={href} className="card-media card-media:landscape">
                <img src={imgSrc} alt={menu.korName} />
                {menu.status === 'soldout' ? (
                    <span className="card-media-badge">
                        <span className="m3-badge badge:inline badge-color:neutral">품절</span>
                    </span>
                ) : menu.isNew ? (
                    <span className="card-media-badge">
                        <span className="m3-badge badge:inline badge-color:primary">NEW</span>
                    </span>
                ) : null}
            </Link>

            {/* 카테고리 이름 · 메뉴 이름 */}
            <div className="card-header">
                <div className="card-titles">
                    <p className="card-subhead">{menu.categoryName}</p>
                    <h2 className="card-headline">
                        <Link href={href}>{menu.korName}</Link>
                    </h2>
                </div>
            </div>
            <p className="card-content">{menu.engName}</p>

            {/* 가격 · 동작 */}
            <div className="card-actions">
                <strong className="font-size:body-lg font-weight:bold">{menu.price.toLocaleString('ko-KR')}원</strong>
                <div className="card-actions-end">
                    <button
                        type="button"
                        className="m3-icon-btn icon-btn:outlined icon-btn-size:sm"
                        aria-label={`좋아요 ${menu.favoriteCount}`}
                    >
                        <i className="m3-icon icon:favorite" aria-hidden="true"></i>
                    </button>
                    {menu.status !== 'on' ? (
                        <button type="button" className="m3-btn btn-size:xs" disabled>
                            품절
                        </button>
                    ) : (
                        <button type="button" className="m3-btn btn-size:xs">
                            담기
                        </button>
                    )}
                </div>
            </div>
        </li>
    );
}
```

**✅ 확인**

- `MenuCard.tsx`가 `MenuSummary` 타입을 받아 렌더링한다.
- 이미지, 카테고리 이름, 메뉴 이름, 가격, NEW 배지, 즐겨찾기 수가 표시된다.

**🎓 newlec 쌤의 코멘트**

`MenuCard`는 순수하게 데이터를 받아서 표시만 하는 컴포넌트다. 상태 관리나 이벤트 처리가 없으므로, 서버 컴포넌트로 만들 수도 있다. 하지만 `MenuList`가 클라이언트 컴포넌트이고 `MenuCard`가 그 자식이므로, `'use client'`를 붙여두면 의도가 명확해진다.

**📝 이 단계의 핵심**

- `MenuCard`는 `MenuSummary` 데이터를 받아 렌더링한다.
- `toLocaleString()`으로 가격을 포맷팅한다.

## 6. 애플리케이션 실행과 테스트

Next.js 개발 서버를 실행하고, API 연동이 제대로 되는지 확인한다. 우선 백엔드 API 스프링 서버가 동작 중인지 확인한다.

### 6-1. Next.js 서버 실행

```
npm run dev
```
(`yarn dev` 또는 `pnpm dev`도 가능)

**⚠️ CORS 오류 주의**

Next.js 개발 서버(`localhost:3000`)가 백엔드 API(`localhost:8080`)를 호출할 때 CORS(Cross-Origin Resource Sharing) 오류가 발생할 수 있다. 이 경우 Spring Boot 프로젝트에 아래 `WebConfig` 클래스를 추가하여 CORS를 허용하도록 설정해야 한다.

파일: `src/main/java/com/newlecture/backend/config/WebConfig.java`

```java
package com.newlecture.backend.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

// Next.js 개발 서버(localhost:3000)에서 API(localhost:8080)를 호출할 수 있도록 CORS 허용
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins("http://localhost:3000")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                .allowedHeaders("*");
    }
}
```

### 6-2. 브라우저에서 테스트

브라우저에서 `http://localhost:3000/menus`로 이동한다.

- 초기 로딩: 전체 메뉴 목록이 표시된다.
- 카테고리 클릭: "커피" 카테고리를 클릭하면, 커피 메뉴만 표시된다.
- 검색: "라떼"를 입력하면, "라떼"가 포함된 메뉴만 표시된다.
- 로딩 상태: 데이터가 로딩되는 동안 "불러오는 중..."이 표시된다.

**✅ 확인**

- `http://localhost:3000/menus`에서 메뉴 목록이 표시된다.
- 카테고리를 클릭하면 해당 카테고리의 메뉴만 표시된다.
- 검색어를 입력하면 검색 결과가 표시된다.
- 로딩 중일 때 "불러오는 중..."이 표시된다.

**🎓 newlec 쌤의 코멘트**

이제 `localhost:3000/menus`에서 Spring Boot API와 연동된 메뉴 페이지를 사용할 수 있다. 서버 컴포넌트에서 초기 데이터를 가져와 빠르게 렌더링하고, 클라이언트 컴포넌트에서 사용자 인터랙션에 반응하여 데이터를 갱신한다. 이 구조는 Next.js App Router의 핵심 패턴이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Failed to fetch` | Spring Boot 서버가 실행되지 않음 | `mvn spring-boot:run` 실행 |
| CORS Error | Spring Boot에서 CORS 설정 누락 | 위 `WebConfig` 추가 |
| Hydration Error | 서버와 클라이언트에서 렌더링된 HTML이 다름 | `useEffect`에서 상태 변경을 주의 |

**📝 이 단계의 핵심**

- `npm run dev`로 Next.js 서버를 실행한다.
- 브라우저에서 API 연동을 테스트한다.

## 정리

1단계: 서버 컴포넌트와 클라이언트 컴포넌트의 차이를 이해한다.
2단계: TypeScript 타입과 API 호출 함수를 만든다.
3단계: 서버 컴포넌트에서 초기 데이터를 가져온다.
4단계: 클라이언트 컴포넌트에서 상태 관리와 데이터 갱신을 처리한다.
5단계: `MenuCard` 컴포넌트를 만들어 메뉴를 렌더링한다.
6단계: 애플리케이션을 실행하고 API 연동을 테스트한다.
