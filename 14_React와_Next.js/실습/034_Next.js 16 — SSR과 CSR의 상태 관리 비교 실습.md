---
tags: [웹, 자바스크립트, React, Next.js, SSR, CSR]
---

> 🔗 관련 노트: [[067_Next.js - 컴포넌트 분리]] · [[064_리액트 컴포넌트 생명주기 — 서버·클라이언트 실행, 하이드레이션, useEffect와 상태 변수]] · [[032_Next.js 실무형 메뉴 목록 페이지 만들기 — SSR, 상태, 이벤트, 컴포넌트 분리 실습]]

# Next.js 16: SSR과 CSR의 상태 관리 비교 실습

**대상**: Next.js App Router, TypeScript, Server/Client 컴포넌트, useState, Link를 이미 아는 학생

**목표**: 동일한 UI에서 SSR과 CSR의 상태 관리 방식을 코드로 구현하고, searchParams가 Promise인 이유, 쿼리스트링의 필요성, SEO적 이유를 이해한다

**완성물**: `app/step1/ssr.tsx`와 `app/step1/csr.tsx` 두 페이지

**준비물**

- Next.js 16 프로젝트 (App Router, TypeScript 설정 완료)
- Newtil CSS가 설치되어 있어야 합니다. (`npm install newtil-css`)
- `app/layout.tsx`에 Newtil CSS가 import되어 있어야 합니다.

우리는 좌측에 카테고리 목록, 우측에 항목 목록과 페이지네이션이 있는 레이아웃을 만들 것입니다. 이 레이아웃은 SSR과 CSR 페이지에서 동일하게 사용됩니다. 먼저 이 구조가 왜 중요한지, 그리고 Newtil CSS의 어떤 클래스를 사용할지 확인해 볼게요.

## 1. 레이아웃 구조 분석

### 1-1. 레이아웃 구조 분석

우리가 만들 UI는 다음과 같은 구조입니다:

- 좌측 (Sidebar): 카테고리 목록 (예: 전체, 프론트엔드, 백엔드, 디자인)
- 우측 (Main):
  - 상단: 현재 선택된 카테고리 제목
  - 중간: 해당 카테고리의 항목 목록 (예: "React 기초", "Next.js 실습" 등)
  - 하단: 페이지네이션 버튼 (이전, 다음, 현재 페이지 표시)

이 구조는 "필터(카테고리)"와 "데이터(목록)"의 관계입니다. SSR에서는 이 필터 상태가 URL에 담기고, CSR에서는 메모리(useState)에 담깁니다.

**✅ 확인**

- 여러분은 이제 "좌측 카테고리, 우측 목록+페이지네이션"이라는 UI 구조를 머릿속에 그릴 수 있어야 합니다.
- Newtil CSS의 기본 유틸리티 클래스가 무엇인지 확인했습니다.

## 2. SSR 페이지 작성

이제 `app/step1/ssr.tsx` 파일을 만들어 보겠습니다. 이 페이지는 서버 컴포넌트이며, 상태는 URL의 쿼리스트링으로 관리됩니다. searchParams는 Promise이므로 await로 받아야 합니다.

### 2-1. app/step1/ssr/page.tsx 파일 생성

**파일**: `app/step1/ssr/page.tsx`

```tsx
import Link from "next/link";

// 서버 컴포넌트이므로 "use client"가 없습니다.
// searchParams는 Promise<string | string[] | undefined> 타입입니다.
export default async function SSRPage({
  searchParams,
}: {
  searchParams: Promise<{ category?: string; page?: string }>;
}) {
  // searchParams는 Promise이므로 await로 값을 꺼냅니다.
  const params = await searchParams;

  // 기본값 설정: 카테고리는 'all', 페이지는 '1'
  const category = params.category || "all";
  const page = parseInt(params.page || "1", 10);

  // 카테고리 목록 (실제 앱에서는 DB에서 올 수 있음)
  const categories = ["all", "frontend", "backend", "design"];

  // 현재 카테고리에 따른 항목 목록 (모의 데이터)
  const items = [
    { id: 1, title: "React 기초", category: "frontend" },
    { id: 2, title: "Next.js 실습", category: "frontend" },
    { id: 3, title: "Node.js 서버", category: "backend" },
    { id: 4, title: "UI 디자인 원칙", category: "design" },
    { id: 5, title: "TypeScript 입문", category: "frontend" },
  ];

  // 현재 카테고리로 필터링
  const filteredItems = items.filter((item) => (category === "all" ? true : item.category === category));

  // 페이지네이션 로직 (간단화: 페이지당 3개)
  const itemsPerPage = 3;
  const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
  const currentPageItems = filteredItems.slice((page - 1) * itemsPerPage, page * itemsPerPage);

  return (
    <div className="site-body site-body:aside padding:4">
      {/* 좌측: 카테고리 목록 */}
      <aside className="site-aside">
        <section className="m3-card card:outlined card-padding:self">
          <div className="card-header">
            <div className="card-titles">
              <h2 className="card-subhead">카테고리</h2>
            </div>
          </div>
          <ul className="m3-list list-size:compact">
            {categories.map((cat) => {
              const isActive = category === cat;
              return (
                <li key={cat}>
                  <Link
                    href={`/step1/ssr?category=${cat}&page=1`}
                    className={`list-item${isActive ? " list-active" : ""}`}
                    aria-current={isActive ? "page" : undefined}
                  >
                    <span className="list-content">{cat === "all" ? "전체" : cat}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </section>
      </aside>

      {/* 우측: 항목 목록 + 페이지네이션 */}
      <main className="site-content">
        <h1 className="font-size:heading-md font-weight:bold margin-bottom:4">
          {category === "all" ? "전체" : category} 항목
        </h1>

        {/* 항목 목록 */}
        <ul className="display:flex flex-direction:column gap:2 margin-bottom:6">
          {currentPageItems.map((item) => (
            <li key={item.id} className="m3-card card:outlined card-padding:self padding:3">
              <div className="display:flex justify-content:space-between align-items:center">
                <span className="font-weight:medium">{item.title}</span>
                <span className="m3-badge badge:inline badge-color:neutral font-size:body-xs">{item.category}</span>
              </div>
            </li>
          ))}
          {currentPageItems.length === 0 && (
            <li className="text-align:center padding-y:8 color:text-muted">항목이 없습니다.</li>
          )}
        </ul>

        {/* 페이지네이션 */}
        <div className="display:flex justify-content:center align-items:center gap:2">
          {page > 1 ? (
            <Link
              href={`/step1/ssr?category=${category}&page=${page - 1}`}
              className="m3-btn btn:outlined btn-size:sm"
            >
              이전
            </Link>
          ) : (
            <button className="m3-btn btn:outlined btn-size:sm" disabled>
              이전
            </button>
          )}

          <span className="font-size:body-sm font-weight:medium padding-x:2">
            {page} / {totalPages || 1}
          </span>

          {page < totalPages ? (
            <Link
              href={`/step1/ssr?category=${category}&page=${page + 1}`}
              className="m3-btn btn:outlined btn-size:sm"
            >
              다음
            </Link>
          ) : (
            <button className="m3-btn btn:outlined btn-size:sm" disabled>
              다음
            </button>
          )}
        </div>
      </main>
    </div>
  );
}
```

### 2-2. 서버에서 실행

터미널에서 다음 명령을 실행합니다:

```
npm run dev
```

### 2-3. 브라우저에서 확인

브라우저에서 `http://localhost:3000/step1/ssr`로 이동합니다.

**✅ 확인**

- 페이지가 열리면 좌측에 카테고리 목록, 우측에 항목 목록이 보입니다.
- 좌측의 "frontend"를 클릭하면 URL이 `?category=frontend&page=1`로 바뀝니다.
- 우측 목록이 "React 기초", "Next.js 실습", "TypeScript 입문"으로 필터링됩니다.
- "다음" 버튼을 클릭하면 URL의 page 값이 2로 바뀝니다.
- 중요: 브라우저 DevTools의 Network 탭을 열고, 카테고리 클릭 시 새로운 요청(Request)이 발생하는지 확인하세요. (Next.js App Router는 부분 재렌더링을 하지만, SSR 페이지의 searchParams 변경 시 서버에 다시 요청을 보냅니다.)

**🎓 newlec 쌤의 코멘트**

이 페이지에서 가장 중요한 점은 이벤트 핸들러가 없다는 것입니다. onClick이 없습니다. 모든 상태 변경은 `<Link>`를 통해 URL을 변경하는 방식으로 이루어집니다. 왜냐하면 이 컴포넌트는 서버에서 실행되기 때문입니다. 서버는 브라우저의 클릭 이벤트를 알 수 없습니다. 서버가 알 수 있는 유일한 상태 변경 신호는 "새로운 URL로 요청이 왔다"는 것입니다. 따라서 상태는 URL에 담겨야 하고, 서버는 그 URL을 읽어서(searchParams) 상태를 복원합니다. 이것이 SSR의 핵심입니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| searchParams가 undefined | 타입 정의가 잘못됨 또는 await 누락 | `searchParams: Promise<{...}>`로 타입을 명시하고 `await searchParams`를 사용하세요. |
| 카테고리 클릭 시 페이지가 새로고침되지 않음 | Link가 아닌 a 태그를 사용함 | 반드시 next/link의 Link 컴포넌트를 사용하세요. |
| page 값이 NaN | parseInt 누락 또는 잘못된 파라미터 | `parseInt(params.page \|\| "1", 10)`처럼 기본값과 함께 parseInt를 사용하세요. |

**📝 이 단계의 핵심**

- SSR 페이지는 서버 컴포넌트이며, 이벤트 핸들러를 사용할 수 없습니다.
- 상태는 URL의 쿼리스트링으로 관리되며, searchParams는 await로 받아야 합니다.
- `<Link>`는 URL을 변경하는 것이므로, 서버에 새로운 요청을 보내는 것과 같습니다.

## 3. searchParams가 Promise인 이유

이제 왜 searchParams가 Promise인지, 그리고 왜 await해야 하는지 깊이 이해해 보겠습니다.

### 3-1. 요청 시 동적 데이터

searchParams는 서버가 요청을 받을 때(알 수 있는) 값입니다. 서버는 요청이 오기 전에는 어떤 URL로 요청이 올지 모릅니다. 따라서 searchParams는 요청이 도착할 때까지 "미래의 값"을 나타내며, 이는 Promise로 표현됩니다.

### 3-2. Suspense 스트리밍

Next.js는 서버 컴포넌트를 스트리밍으로 렌더링합니다. searchParams가 Promise이므로, Next.js는 이 Promise가 해결(resolve)될 때까지 해당 컴포넌트의 렌더링을 일시정지할 수 있습니다. 이 덕분에 다른 부분(예: 헤더, 푸터)은 먼저 전송되고, searchParams에 의존하는 부분은 나중에 전송됩니다.

### 3-3. 병렬 패칭

여러 서버 컴포넌트가 동시에 searchParams를 사용할 수 있습니다. Promise는 비동기 처리를 가능하게 하여, 여러 데이터 소스에서 데이터를 병렬로 가져올 수 있게 합니다.

**✅ 확인**

- searchParams가 Promise인 이유는 요청 시 동적 데이터이기 때문입니다.
- await를 사용하면 Next.js가 스트리밍 렌더링을 올바르게 처리할 수 있습니다.

**🎓 newlec 쌤의 코멘트**

많은 학생들이 "왜 그냥 객체로 안 주나?"라고 묻습니다. 하지만 서버는 요청이 오기 전에는 아무것도 모릅니다. searchParams는 요청의 일부이며, 요청이 도착해야만 값을 알 수 있습니다. Promise는 "아직 값이 없지만, 곧 올 것"을 나타내는 표준적인 JavaScript 패턴입니다. Next.js는 이 Promise를 활용하여, 데이터가 준비될 때까지 UI를 스트리밍으로 최적화합니다.

**📝 이 단계의 핵심**

- searchParams는 요청 시 동적 데이터이므로 Promise입니다.
- await는 Next.js의 스트리밍 렌더링을 가능하게 합니다.

## 4. 왜 URL에 상태를 담아야 하는가

이제 왜 SSR에서 상태를 URL의 쿼리스트링으로 관리해야 하는지 설명하겠습니다.

### 4-1. 서버와 클라이언트 간 상태 공유 매개체 부재

서버와 클라이언트는 서로 다른 환경에서 실행됩니다. 서버는 Node.js 환경에서, 클라이언트는 브라우저 환경에서 실행됩니다. 이 두 환경은 메모리를 공유하지 않습니다. 따라서 서버가 "현재 카테고리는 frontend다"라는 상태를 클라이언트에게 전달할 수 있는 유일한 방법은 URL입니다.

### 4-2. URL이 유일한 공유 수단

URL은 서버와 클라이언트 모두에게 가시적입니다. 서버는 URL에서 searchParams를 읽을 수 있고, 클라이언트는 URL을 변경할 수 있습니다. 따라서 URL은 서버와 클라이언트 간의 "공통 언어"입니다.

**✅ 확인**

- 서버와 클라이언트는 메모리를 공유하지 않습니다.
- URL은 서버와 클라이언트 모두에게 가시적인 유일한 상태 공유 수단입니다.

**🎓 newlec 쌤의 코멘트**

만약 서버가 클라이언트에게 상태를 전달할 수 있는 다른 방법이 있다면, 쿼리스트링은 필요 없을 것입니다. 하지만 현재 웹 아키텍처에서는 URL이 그 역할을 합니다. 이것이 왜 SSR에서 상태가 URL에 담겨야 하는지, 그리고 왜 CSR에서는 useState를 사용할 수 있는지 설명합니다. CSR에서는 클라이언트 메모리가 상태의 저장소이므로, URL에 담지 않아도 됩니다.

**📝 이 단계의 핵심**

- 서버와 클라이언트는 메모리를 공유하지 않으므로, URL이 유일한 상태 공유 수단입니다.
- SSR에서는 상태가 URL에 담겨야 서버가 상태를 복원할 수 있습니다.

## 5. SEO 관점에서 본 URL 상태

이제 왜 SSR에서 상태를 URL에 담고, 서버에서 완전한 HTML을 내려줘야 하는지 SEO 관점에서 설명하겠습니다.

### 5-1. 크롤러와 JavaScript

검색 엔진 크롤러는 기본적으로 HTML을 파싱합니다. 일부 크롤러(예: Google)는 JavaScript를 실행할 수 있지만, 모든 크롤러가 그렇지는 않습니다. 또한, JavaScript 실행은 크롤링 비용이 높습니다.

### 5-2. 서버에서 완전한 HTML을 내려줘야

SSR은 서버에서 완전한 HTML을 생성하여 클라이언트에게 전송합니다. 이 HTML에는 이미 상태(카테고리, 페이지)에 따라 필터링된 데이터가 포함되어 있습니다. 따라서 크롤러는 JavaScript를 실행하지 않아도, HTML에서 내용을 읽을 수 있습니다.

### 5-3. 상태가 URL에 담겨야 하는 이유

만약 상태가 URL에 담겨 있지 않으면, 크롤러는 "현재 페이지가 어떤 상태인지"를 알 수 없습니다. 예를 들어, `?category=frontend`가 URL에 없다면, 크롤러는 "이 페이지가 frontend 카테고리를 보여주는지"를 알 수 없습니다. 따라서 상태가 URL에 담겨야, 크롤러가 각 상태를 인덱싱할 수 있습니다.

**✅ 확인**

- SSR은 서버에서 완전한 HTML을 내려줘야 크롤러가 내용을 인덱싱할 수 있습니다.
- 상태가 URL에 담겨야 크롤러가 각 상태를 인덱싱할 수 있습니다.

**🎓 newlec 쌤의 코멘트**

SEO는 단순히 "검색에 잘 나오게 하는 것"이 아닙니다. 그것은 "사용자가 원하는 정보를 정확하게 전달하는 것"입니다. 만약 사용자가 "frontend 카테고리"를 검색하고, 해당 페이지로 왔는데, HTML에 frontend 항목이 없다면, 사용자는 실망할 것입니다. 또한, 검색 엔진은 그 페이지를 "frontend"와 관련이 없다고 판단할 수 있습니다. 따라서 상태가 URL에 담기고, 서버에서 해당 상태에 맞는 HTML이 생성되어야 합니다.

**📝 이 단계의 핵심**

- SSR은 서버에서 완전한 HTML을 내려줘야 SEO에 유리합니다.
- 상태가 URL에 담겨야 크롤러가 각 상태를 인덱싱할 수 있습니다.

## 6. CSR 페이지 작성

이제 `app/step1/csr.tsx` 파일을 만들어 보겠습니다. 이 페이지는 클라이언트 컴포넌트이며, 상태는 useState로 관리됩니다.

### 6-1. app/step1/csr/page.tsx 파일 생성

**파일**: `app/step1/csr/page.tsx`

```tsx
"use client";

import { useState } from "react";

// 클라이언트 컴포넌트이므로 "use client"가 필요합니다.
export default function CSRPage() {
  // 상태는 클라이언트 메모리에 저장됩니다.
  const [category, setCategory] = useState("all");
  const [page, setPage] = useState(1);

  // 카테고리 목록
  const categories = ["all", "frontend", "backend", "design"];

  // 항목 목록 (모의 데이터)
  const items = [
    { id: 1, title: "React 기초", category: "frontend" },
    { id: 2, title: "Next.js 실습", category: "frontend" },
    { id: 3, title: "Node.js 서버", category: "backend" },
    { id: 4, title: "UI 디자인 원칙", category: "design" },
    { id: 5, title: "TypeScript 입문", category: "frontend" },
  ];

  // 현재 카테고리로 필터링
  const filteredItems = items.filter((item) => (category === "all" ? true : item.category === category));

  // 페이지네이션 로직 (간단화: 페이지당 3개)
  const itemsPerPage = 3;
  const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
  const currentPageItems = filteredItems.slice((page - 1) * itemsPerPage, page * itemsPerPage);

  // 카테고리 선택 핸들러
  const handleCategoryChange = (cat: string) => {
    setCategory(cat);
    setPage(1); // 카테고리 변경 시 페이지를 1로 리셋
  };

  // 페이지 변경 핸들러
  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage);
    }
  };

  return (
    <div className="site-body site-body:aside padding:4">
      {/* 좌측: 카테고리 목록 */}
      <aside className="site-aside">
        <section className="m3-card card:outlined card-padding:self">
          <div className="card-header">
            <div className="card-titles">
              <h2 className="card-subhead">카테고리</h2>
            </div>
          </div>
          <ul className="m3-list list-size:compact">
            {categories.map((cat) => {
              const isActive = category === cat;
              return (
                <li key={cat}>
                  {/* onClick 이벤트 핸들러로 상태를 변경합니다. */}
                  <button
                    type="button"
                    onClick={() => handleCategoryChange(cat)}
                    className={`list-item${isActive ? " list-active" : ""}`}
                    aria-current={isActive ? "page" : undefined}
                  >
                    <span className="list-content">{cat === "all" ? "전체" : cat}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </section>
      </aside>

      {/* 우측: 항목 목록 + 페이지네이션 */}
      <main className="site-content">
        <h1 className="font-size:heading-md font-weight:bold margin-bottom:4">
          {category === "all" ? "전체" : category} 항목
        </h1>

        {/* 항목 목록 */}
        <ul className="display:flex flex-direction:column gap:2 margin-bottom:6">
          {currentPageItems.map((item) => (
            <li key={item.id} className="m3-card card:outlined card-padding:self padding:3">
              <div className="display:flex justify-content:space-between align-items:center">
                <span className="font-weight:medium">{item.title}</span>
                <span className="m3-badge badge:inline badge-color:neutral font-size:body-xs">{item.category}</span>
              </div>
            </li>
          ))}
          {currentPageItems.length === 0 && (
            <li className="text-align:center padding-y:8 color:text-muted">항목이 없습니다.</li>
          )}
        </ul>

        {/* 페이지네이션 */}
        <div className="display:flex justify-content:center align-items:center gap:2">
          {page > 1 ? (
            <button
              type="button"
              onClick={() => handlePageChange(page - 1)}
              className="m3-btn btn:outlined btn-size:sm"
            >
              이전
            </button>
          ) : (
            <button type="button" className="m3-btn btn:outlined btn-size:sm" disabled>
              이전
            </button>
          )}

          <span className="font-size:body-sm font-weight:medium padding-x:2">
            {page} / {totalPages || 1}
          </span>

          {page < totalPages ? (
            <button
              type="button"
              onClick={() => handlePageChange(page + 1)}
              className="m3-btn btn:outlined btn-size:sm"
            >
              다음
            </button>
          ) : (
            <button type="button" className="m3-btn btn:outlined btn-size:sm" disabled>
              다음
            </button>
          )}
        </div>
      </main>
    </div>
  );
}
```

### 6-2. 브라우저에서 확인

브라우저에서 `http://localhost:3000/step1/csr`로 이동합니다.

그냥 페이지만 확인하지 말고 브라우저의 개발자 도구를 열고 네트워크 탭에서 두 종류의 페이지가 어떤 것들을 내려 받는지 카테고리를 클릭할 때마다 네트워크 창의 변화를 확인하세요.

**✅ 확인**

- 페이지가 열리면 좌측에 카테고리 목록, 우측에 항목 목록이 보입니다.
- 좌측의 "frontend"를 클릭하면 URL은 변하지 않습니다.
- 우측 목록이 "React 기초", "Next.js 실습", "TypeScript 입문"으로 필터링됩니다.
- "다음" 버튼을 클릭하면 페이지 번호가 2로 바뀝니다.
- 중요: 브라우저 DevTools의 Network 탭을 열고, 카테고리 클릭 시 새로운 요청이 발생하지 않는지 확인하세요. (CSR은 클라이언트에서 상태가 변경되므로, 서버에 요청을 보내지 않습니다.)

**🎓 newlec 쌤의 코멘트**

이 페이지에서 가장 중요한 점은 URL이 변하지 않는다는 것입니다. 상태는 클라이언트 메모리(useState)에 저장됩니다. 이 방식의 장점은 즉시 반응한다는 것입니다. 사용자가 카테고리를 클릭하면, 서버에 요청을 보내지 않고 바로 UI가 변경됩니다. 하지만 단점도 있습니다. 사용자가 새로고침을 하면, 상태가 초기화됩니다. 또한, 크롤러는 이 상태를 알 수 없습니다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| useState가 undefined | "use client" 누락 | 파일 상단에 `'use client';`를 추가하세요. |
| 상태 변경 시 UI가 업데이트되지 않음 | 상태 변경 후 리렌더링이 안 됨 | useState의 setter 함수를 올바르게 사용했는지 확인하세요. |
| 새로고침 시 상태가 초기화됨 | CSR의 특성 | 이는 의도된 동작입니다. 상태가 클라이언트 메모리에 저장되기 때문입니다. |

**📝 이 단계의 핵심**

- CSR 페이지는 클라이언트 컴포넌트이며, useState로 상태를 관리합니다.
- 상태 변경은 이벤트 핸들러로 이루어지며, URL은 변하지 않습니다.
- CSR은 즉시 반응하지만, 새로고침 시 상태가 유실됩니다.

## 7. CSR의 장점과 단점

이제 CSR의 장점과 단점을 정리해 보겠습니다.

### 7-1. 장점: 즉시 반응, 매끄러운 UX

CSR은 클라이언트에서 상태가 변경되므로, 서버에 요청을 보내지 않아도 됩니다. 이 덕분에 UI가 즉시 반응하며, 매끄러운 사용자 경험을 제공합니다.

### 7-2. 단점: 초기 빈 렌더링

CSR은 초기 로드 시, 서버에서 빈 HTML을 내려줍니다. 클라이언트에서 JavaScript가 실행된 후에야 UI가 표시됩니다. 이 때문에 초기에 빈 화면이 보일 수 있습니다.

### 7-3. 단점: SEO 불리

CSR은 서버에서 완전한 HTML을 내려주지 않으므로, 크롤러가 내용을 인덱싱하기 어렵습니다.

### 7-4. 단점: 새로고침 시 상태 유실

CSR은 상태가 클라이언트 메모리에 저장되므로, 새로고침 시 상태가 초기화됩니다.

**✅ 확인**

- CSR의 장점: 즉시 반응, 매끄러운 UX
- CSR의 단점: 초기 빈 렌더링, SEO 불리, 새로고침 시 상태 유실

**🎓 newlec 쌤의 코멘트**

CSR은 "빠름"이 강점입니다. 하지만 "빠름"은 "완전함"을 희생하는 대가로 얻어집니다. SSR은 "완전함"이 강점입니다. 하지만 "완전함"은 "느림"을 감수해야 합니다. 어떤 방식을 선택할지는, 앱의 성격에 따라 다릅니다. 소셜 미디어, 대시보드 같은 인터랙티브한 앱은 CSR이 적합하고, 블로그, 뉴스 사이트 같은 콘텐츠 중심 앱은 SSR이 적합합니다.

**📝 이 단계의 핵심**

- CSR은 즉시 반응하지만, 초기 빈 렌더링, SEO 불리, 새로고침 시 상태 유실이 단점입니다.
- SSR은 완전한 HTML을 내려주지만, 서버 요청이 필요합니다.

## 8. SSR vs CSR 최종 비교

이제 두 페이지를 비교하며, 상태 관리 방식의 차이를 정리해 보겠습니다.

### 8-1. 상태 저장 위치

- SSR: URL의 쿼리스트링
- CSR: 클라이언트 메모리 (useState)

### 8-2. 상태 변경 방식

- SSR: `<Link>`로 URL 변경 → 서버에 요청 → 서버에서 상태 복원
- CSR: 이벤트 핸들러로 useState 변경 → 클라이언트에서 UI 업데이트

### 8-3. 서버 요청

- SSR: 상태 변경 시 서버에 요청 발생
- CSR: 상태 변경 시 서버에 요청 없음

### 8-4. SEO

- SSR: 서버에서 완전한 HTML을 내려줌 → SEO에 유리
- CSR: 서버에서 빈 HTML을 내려줌 → SEO에 불리

### 8-5. 새로고침

- SSR: URL이 상태이므로, 새로고침 시 상태 유지
- CSR: 상태가 메모리에 있으므로, 새로고침 시 상태 유실

**✅ 확인**

- SSR은 URL로 상태를 관리하고, 서버에서 렌더링합니다.
- CSR은 useState로 상태를 관리하고, 클라이언트에서 렌더링합니다.
- SSR은 SEO에 유리하고, CSR은 즉시 반응합니다.

**🎓 newlec 쌤의 코멘트**

이 비교를 통해, "상태 관리"가 단순히 "값을 저장하는 것"이 아님을 알 수 있습니다. 상태 관리는 "어디서, 어떻게, 누구와 공유하는가"의 문제입니다. SSR은 서버와 클라이언트 모두에게 가시적인 URL로 상태를 공유하고, CSR은 클라이언트만의 메모리로 상태를 관리합니다. 이 차이를 이해하면, 어떤 상황에서 어떤 방식을 선택해야 하는지 판단할 수 있습니다.

**📝 이 단계의 핵심**

- SSR은 URL로 상태를 관리하고, 서버에서 렌더링합니다.
- CSR은 useState로 상태를 관리하고, 클라이언트에서 렌더링합니다.
- 상태 관리 방식은 SEO, UX, 아키텍처에 영향을 미칩니다.

## 정리

1단계: 공통 UI 구조(카테고리, 목록, 페이지네이션)를 이해했습니다.
2단계: SSR 페이지를 작성하며, searchParams를 await로 받고, `<Link>`로 URL을 변경하는 방식을 실습했습니다.
3단계: searchParams가 Promise인 이유(요청 시 동적 데이터, 스트리밍, 병렬 패칭)를 이해했습니다.
4단계: 서버와 클라이언트 간 상태 공유 매개체 부재로 인해, URL이 유일한 공유 수단임을 이해했습니다.
5단계: SEO적 필요성으로 인해, 서버에서 완전한 HTML을 내려주고, 상태가 URL에 담겨야 함을 이해했습니다.
6단계: CSR 페이지를 작성하며, useState와 이벤트 핸들러로 상태를 관리하는 방식을 실습했습니다.
7단계: CSR의 장점(즉시 반응)과 단점(초기 빈 렌더링, SEO 불리, 새로고침 시 상태 유실)을 정리했습니다.
8단계: 두 페이지의 상태 관리 방식 차이를 비교하며, 상태 관리가 아키텍처에 미치는 영향을 이해했습니다.
