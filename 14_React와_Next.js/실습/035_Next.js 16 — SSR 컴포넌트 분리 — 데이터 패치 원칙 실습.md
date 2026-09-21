---
tags: [웹, 자바스크립트, React, Next.js, SSR]
---

> 🔗 관련 노트: [[034_Next.js 16 — SSR과 CSR의 상태 관리 비교 실습]] · [[067_Next.js - 컴포넌트 분리]] · [[032_Next.js 실무형 메뉴 목록 페이지 만들기 — SSR, 상태, 이벤트, 컴포넌트 분리 실습]]

# Next.js 16: SSR 컴포넌트 분리 — 데이터 패치 원칙 실습

**대상**: 앞 편(SSR과 CSR 상태 관리 비교)을 완료하고, Next.js 16 App Router, TypeScript, Server/Client 컴포넌트, searchParams await, Link를 이미 아는 학생

**목표**: SSR 페이지를 CategoryList와 CourseList 두 컴포넌트로 분리하며, "데이터는 자식이 스스로 패치하는 것이 기본"이라는 원칙과 부모-자식 결합도 낮추는 설계 철학을 실습으로 체득한다

**완성물**: `app/step2/ssr/page.tsx`, `app/step2/ssr/CategoryList.tsx`, `app/step2/ssr/CourseList.tsx` 세 파일로 구성된 분리된 SSR 페이지

**준비물**

- Next.js 16 프로젝트 (App Router, TypeScript 설정 완료)
- Newtil CSS가 설치되어 있어야 합니다. (`npm install newtil-css`)
- `app/layout.tsx`에 Newtil CSS가 import되어 있어야 합니다.
- 앞 편에서 만든 `app/step1/ssr/page.tsx` 코드가 참고용으로 존재하면 좋습니다.

앞 편에서 만든 단일 파일 구조를 새 폴더로 복사하고, 어떤 부분이 "카테고리 목록"이고 어떤 부분이 "코스 목록 + 페이지네이션"인지 식별해 볼게요. 이 단계에서는 아직 코드를 분리하지 않고, 구조를 파악하는 데 집중합니다.

## 1. 분리 전 구조 파악

### 1-1. app/step2/ssr/ 폴더 생성

터미널에서 다음 명령을 실행합니다:

```
mkdir -p app/step2/ssr
```

Windows PowerShell에서는 `mkdir app\step2\ssr` 또는 `New-Item -ItemType Directory -Path "app\step2\ssr"`를 사용할 수 있습니다.

### 1-2. page.tsx 파일 생성

앞 편 `app/step1/ssr/page.tsx`의 코드를 그대로 복사하여 새 위치에 파일을 만듭니다. 이 파일은 아직 분리 전 상태입니다.

**파일**: `app/step2/ssr/page.tsx`

```tsx
import Link from "next/link";

export default async function SSRPage({
  searchParams,
}: {
  searchParams: Promise<{ category?: string; page?: string }>;
}) {
  const params = await searchParams;
  const category = params.category || "all";
  const page = parseInt(params.page || "1", 10);

  const categories = ["all", "frontend", "backend", "design"];

  const items = [
    { id: 1, title: "React 기초", category: "frontend" },
    { id: 2, title: "Next.js 실습", category: "frontend" },
    { id: 3, title: "Node.js 서버", category: "backend" },
    { id: 4, title: "UI 디자인 원칙", category: "design" },
    { id: 5, title: "TypeScript 입문", category: "frontend" },
  ];

  const filteredItems = items.filter((item) => (category === "all" ? true : item.category === category));
  const itemsPerPage = 3;
  const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
  const currentPageItems = filteredItems.slice((page - 1) * itemsPerPage, page * itemsPerPage);

  return (
    <div className="site-body site-body:aside padding:4">
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
                    href={`/step2/ssr?category=${cat}&page=1`}
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

      <main className="site-content">
        <h1 className="font-size:heading-md font-weight:bold margin-bottom:4">
          {category === "all" ? "전체" : category} 항목
        </h1>

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

        <div className="display:flex justify-content:center align-items:center gap:2">
          {page > 1 ? (
            <Link href={`/step2/ssr?category=${category}&page=${page - 1}`} className="m3-btn btn:outlined btn-size:sm">
              이전
            </Link>
          ) : (
            <button className="m3-btn btn:outlined btn-size:sm" disabled>이전</button>
          )}

          <span className="font-size:body-sm font-weight:medium padding-x:2">
            {page} / {totalPages || 1}
          </span>

          {page < totalPages ? (
            <Link href={`/step2/ssr?category=${category}&page=${page + 1}`} className="m3-btn btn:outlined btn-size:sm">
              다음
            </Link>
          ) : (
            <button className="m3-btn btn:outlined btn-size:sm" disabled>다음</button>
          )}
        </div>
      </main>
    </div>
  );
}
```

### 1-3. 구조 식별

위 코드를 보고 두 영역을 구분해 보세요.

- 좌측 사이드바 영역: `categories` 배열을 map하여 Link 리스트를 렌더링하는 부분.
- 우측 메인 영역: `items` 배열을 필터링하고 슬라이싱하여 `currentPageItems`를 렌더링하는 부분.

**✅ 확인**

- `app/step2/ssr/page.tsx` 파일이 생성되었습니다.
- 브라우저에서 `http://localhost:3000/step2/ssr`으로 접속하면 앞 편과 동일한 UI가 표시됩니다.
- 코드에서 `categories.map` 블록과 `currentPageItems.map` 블록의 위치를 눈으로 확인할 수 있습니다.

**🎓 newlec 쌤의 코멘트**

이제 우리는 이 긴 파일을 두 개의 컴포넌트로 쪼개야 합니다. 하지만 단순히 코드를 잘라내는 것이 아닙니다. "무엇을 props(속성들)로 넘길지"와 "무엇을 자식 내부에 둘지"를 결정하는 설계 과정입니다. 이 단계에서는 아직 분리하지 않고, 어떤 데이터가 부모(page.tsx)에 있고, 어떤 데이터가 자식에게 필요한지 파악하는 시간을 갖습니다.

**📝 이 단계의 핵심**

- `app/step2/ssr/` 폴더에 분리 전 상태의 page.tsx를 준비했습니다.
- UI를 "카테고리 목록"과 "코스 목록 + 페이지네이션" 두 영역으로 인식했습니다.

## 2. CategoryList 컴포넌트 분리

이제 좌측 카테고리 목록을 CategoryList 컴포넌트로 분리해 볼게요. 이 컴포넌트는 `activeCategory`만 props(속성)로 받습니다.

### 2-1. CategoryList.tsx 파일 생성

**파일**: `app/step2/ssr/CategoryList.tsx`

```tsx
import Link from "next/link";

interface CategoryListProps {
  activeCategory: string;
}

export default function CategoryList({ activeCategory }: CategoryListProps) {
  // categories 배열은 자식 내부에서 정의합니다.
  // 부모로부터 props로 받지 않습니다.
  const categories = ["all", "frontend", "backend", "design"];

  return (
    <section className="m3-card card:outlined card-padding:self">
      <div className="card-header">
        <div className="card-titles">
          <h2 className="card-subhead">카테고리</h2>
        </div>
      </div>
      <ul className="m3-list list-size:compact">
        {categories.map((cat) => {
          const isActive = activeCategory === cat;
          return (
            <li key={cat}>
              <Link
                href={`/step2/ssr?category=${cat}&page=1`}
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
  );
}
```

**✅ 확인**

- `app/step2/ssr/CategoryList.tsx` 파일이 생성되었습니다.
- 이 파일은 `activeCategory`를 props로만 받습니다.
- `categories` 배열은 컴포넌트 내부에 정의되어 있습니다.

**🎓 newlec 쌤의 코멘트**

여기서 중요한 질문이 있습니다. "왜 categories 배열을 props(속성들)로 넘기지 않는가?" 만약 categories가 DB에서 오는 동적 데이터라면, 부모가 fetch해서 넘겨줄 수도 있습니다. 하지만 이 예제에서는 “자식이 스스로 정의하거나 fetch할 수 있는 데이터는 부모의 의존성이 아닙니다.” 를 설명하려고 하는 것입니다. 자식이 스스로 데이터를 관리하면, 부모는 자식의 내부 구현을 몰라도 됩니다. 이것이 결합도를 낮추는 첫걸음입니다.

**📝 이 단계의 핵심**

- CategoryList는 `activeCategory`만 props로 받습니다.
- categories 배열은 자식 내부에 정의하여, 부모의 의존성을 줄였습니다.

## 3. "데이터는 자식이 스스로 패치하는 것이 기본" 원칙

이 단계에서는 "데이터는 자식이 스스로 패치하는 것이 기본"이라는 원칙을 깊이 이해해 볼게요.

### 3-1. 결합도(Coupling)와 응집도(Cohesion)

소프트웨어 설계에서 결합도가 낮을수록 컴포넌트 간 의존성이 적어지고, 응집도가 높을수록 컴포넌트 내부의 관련성이 강해집니다.

- 높은 결합도: 부모가 categories를 정의하고, 자식에게 props로 전달. → 부모가 바뀌면 자식도 영향을 받을 수 있음.
- 낮은 결합도: 자식이 categories를 스스로 정의. → 부모는 activeCategory만 알면 되고, categories가 어떻게 생겼는지 몰라도 됨.

### 3-2. "스스로 패치" 원칙

실제 앱에서는 categories가 API에서 올 수 있습니다.

- 부모가 fetch: page.tsx에서 `const categories = await fetchCategories()` 후 props로 전달.
- 자식이 fetch: CategoryList에서 `const categories = await fetchCategories()` 후 렌더링.

자식이 fetch하는 방식이 더 나은 이유는, CategoryList가 "카테고리 목록을 보여주는 컴포넌트"라는 정체성을 더 잘 유지하기 때문입니다. 부모는 "현재 어떤 카테고리가 선택되었는지"만 알면 되고, "카테고리 목록이 어떻게 생겼는지"는 자식의 문제입니다.

**✅ 확인**

- categories 배열을 props로 넘기지 않는 것이 결합도를 낮추는 방법임을 이해했습니다.
- 자식이 스스로 데이터를 정의하거나 fetch하는 것이 기본 원칙임을 이해했습니다.

**🎓 newlec 쌤의 코멘트**

"데이터는 자식이 스스로 패치하는 것이 기본"이라는 원칙은, 컴포넌트가 자기 자신의 데이터를 스스로 관리하도록 하는 것입니다. 부모는 자식의 상태(현재 선택된 값)만 전달하고, 자식의 데이터(목록, 설정값 등)는 자식이 스스로 처리하게 합니다. 이렇게 하면 컴포넌트가 독립적으로 테스트되고, 재사용하기 쉬워집니다.

**📝 이 단계의 핵심**

- "데이터는 자식이 스스로 패치하는 것이 기본" 원칙을 이해했습니다.
- 부모는 상태만 전달하고, 자식은 데이터를 스스로 관리하도록 설계합니다.

## 4. activeCategory를 props로 전달하는 이유

이제 왜 activeCategory는 props로 전달해야 하는지 설명해 볼게요.

### 4-1. 상태의 소스와 표시의 분리

- 상태의 소스(Source of Truth): page.tsx의 category 변수. 이 값은 URL의 searchParams에서 옵니다.
- 표시(Presentation): CategoryList가 "어떤 카테고리가 활성인지"를 표시하는 것.

CategoryList는 "현재 어떤 카테고리가 선택되었는지"를 알기 위해 activeCategory를 props로 받아야 합니다. 만약 CategoryList가 스스로 activeCategory를 결정하려 한다면, URL과 동기화되지 않는 문제가 생깁니다.

### 4-2. 부모가 "현재 상태"를 알고 자식은 "무엇이 활성인지"를 받음

부모(page.tsx)는 URL을 읽어서 category를 추출합니다. 이 값을 자식(CategoryList)에게 전달하면, 자식은 그 값을 바탕으로 UI를 렌더링합니다. 이렇게 하면, URL이 바뀌면 부모가 다시 렌더링되고, 자식에게 새로운 activeCategory가 전달되어 UI가 업데이트됩니다.

**✅ 확인**

- activeCategory는 부모가 URL에서 추출한 상태이므로, props로 전달해야 합니다.
- 자식은 이 값을 바탕으로 활성 상태를 표시합니다.

**🎓 newlec 쌤의 코멘트**

상태는 항상 단일 소스(Source of Truth)를 가져야 합니다. 이 경우 소스는 URL입니다. page.tsx가 URL을 읽고 category를 추출하며, 이를 자식에게 전달합니다. 자식은 이 값을 "읽기 전용"으로 받아 UI를 렌더링합니다. 이렇게 하면 상태의 일관성이 유지되고, 버그가 줄어듭니다.

**📝 이 단계의 핵심**

- activeCategory는 상태의 소스(URL)에서 온 값이므로, props로 전달해야 합니다.
- 자식은 이 값을 바탕으로 활성 상태를 표시합니다.

## 5. page.tsx에 CategoryList 통합

이제 page.tsx에서 기존 인라인 코드를 `<CategoryList activeCategory={category} />`로 대체하고 동작을 확인해 볼게요.

### 5-1. page.tsx 수정

**파일**: `app/step2/ssr/page.tsx`

- 상단에 CategoryList를 import합니다.
- categories 배열과 categories.map 블록을 삭제합니다.
- `<aside>` 태그 안에 `<CategoryList activeCategory={category} />`를 넣습니다.

```tsx
import Link from "next/link";
import CategoryList from "./CategoryList";

export default async function SSRPage({
  searchParams,
}: {
  searchParams: Promise<{ category?: string; page?: string }>;
}) {
  const params = await searchParams;
  const category = params.category || "all";
  const page = parseInt(params.page || "1", 10);

  const items = [
    { id: 1, title: "React 기초", category: "frontend" },
    { id: 2, title: "Next.js 실습", category: "frontend" },
    { id: 3, title: "Node.js 서버", category: "backend" },
    { id: 4, title: "UI 디자인 원칙", category: "design" },
    { id: 5, title: "TypeScript 입문", category: "frontend" },
  ];

  const filteredItems = items.filter((item) => (category === "all" ? true : item.category === category));
  const itemsPerPage = 3;
  const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
  const currentPageItems = filteredItems.slice((page - 1) * itemsPerPage, page * itemsPerPage);

  return (
    <div className="site-body site-body:aside padding:4">
      <aside className="site-aside">
        {/* CategoryList 컴포넌트로 교체 */}
        <CategoryList activeCategory={category} />
      </aside>

      <main className="site-content">
        <h1 className="font-size:heading-md font-weight:bold margin-bottom:4">
          {category === "all" ? "전체" : category} 항목
        </h1>

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

        <div className="display:flex justify-content:center align-items:center gap:2">
          {page > 1 ? (
            <Link href={`/step2/ssr?category=${category}&page=${page - 1}`} className="m3-btn btn:outlined btn-size:sm">
              이전
            </Link>
          ) : (
            <button className="m3-btn btn:outlined btn-size:sm" disabled>이전</button>
          )}

          <span className="font-size:body-sm font-weight:medium padding-x:2">
            {page} / {totalPages || 1}
          </span>

          {page < totalPages ? (
            <Link href={`/step2/ssr?category=${category}&page=${page + 1}`} className="m3-btn btn:outlined btn-size:sm">
              다음
            </Link>
          ) : (
            <button className="m3-btn btn:outlined btn-size:sm" disabled>다음</button>
          )}
        </div>
      </main>
    </div>
  );
}
```

### 5-2. 브라우저에서 확인

브라우저에서 `http://localhost:3000/step2/ssr`으로 이동합니다.

**✅ 확인**

- 페이지가 정상적으로 렌더링됩니다.
- 좌측 카테고리 목록이 CategoryList 컴포넌트로 렌더링됩니다.
- 카테고리 클릭 시 URL이 변경되고, 활성 카테고리가 올바르게 표시됩니다.
- 우측 코스 목록은 아직 page.tsx에 인라인으로 남아 있습니다.

**🎓 newlec 쌤의 코멘트**

이제 좌측은 분리되었습니다. 우측의 CourseList도 같은 방식으로 분리해 보겠습니다. 하지만 이번에는 학생들이 직접 코드를 작성해 보고, 다음 단계에서 완성 설명을 이어가도록 하겠습니다.

**📝 이 단계의 핵심**

- CategoryList를 page.tsx에 통합했습니다.
- activeCategory를 props로 전달하여, 상태의 소스와 표시를 분리했습니다.

## 6. CourseList 분리 — 직접 작성해보기

이제 우측의 CourseList를 분리해 차례입니다. 하지만 이번에는 여러분들이 먼저 컴포넌트를 분리해보는 시간을 가져보도록 하겠습니다.

걱정마세요. 여러분들이 쉽게 할 수 있도록 힌트를 드리도록 하겠습니다.

### 6-1. 힌트

CourseList 컴포넌트를 만들 때 다음 사항을 고려하세요.

- Props: 목록을 구현하기 위한 퀴리스트링 상태 값은 page 이고, 또 하단에 있는 페이저를 구현할 때는 category 정보도 필요합니다. 그래서 category와 page를 props로 받습니다.
- 데이터: courses 배열은 자식 내부에서 정의합니다. (앞 편과 동일한 데이터)
- 로직: 필터링(filter)과 슬라이싱(slice) 로직은 자식 내부에서 처리합니다.
- 렌더링: currentPageItems를 렌더링하고, 페이지네이션 버튼을 포함합니다.

### 6-2. 직접 작성

`app/step2/ssr/CourseList.tsx` 파일을 직접 작성해 보세요.

**✅ 확인**

- `app/step2/ssr/CourseList.tsx` 파일을 직접 작성했습니다.
- category와 page를 props로 받도록 설계했습니다.
- courses 배열과 필터링·슬라이싱 로직을 내부에서 처리했습니다.

**🎓 newlec 쌤의 코멘트**

직접 작성해 보았나요? 만약 courses 배열을 props로 넘기려 했다면, "왜 안 되는지"를 생각해 보세요. courses는 정적 데이터이고, CourseList가 스스로 정의할 수 있습니다. 따라서 props로 넘길 필요가 없습니다. category와 page는 부모가 URL에서 추출한 상태이므로, props로 전달해야 합니다.

**📝 이 단계의 핵심**

- CourseList는 category와 page를 props로 받습니다.
- courses 데이터와 필터링·슬라이싱 로직은 자식 내부에서 처리합니다.

## 7. CourseList 완성 코드

이제 CourseList의 완성 코드를 함께 확인하고, 왜 이렇게 설계했는지 알아보도록 하겠습니다.

### 7-1. CourseList.tsx 완성 코드

**파일**: `app/step2/ssr/CourseList.tsx`

```tsx
import Link from "next/link";

interface CourseListProps {
  category: string;
  page: number;
}

export default function CourseList({ category, page }: CourseListProps) {
  // courses 배열은 자식 내부에서 정의합니다.
  const courses = [
    { id: 1, title: "React 기초", category: "frontend" },
    { id: 2, title: "Next.js 실습", category: "frontend" },
    { id: 3, title: "Node.js 서버", category: "backend" },
    { id: 4, title: "UI 디자인 원칙", category: "design" },
    { id: 5, title: "TypeScript 입문", category: "frontend" },
  ];

  // 필터링과 슬라이싱 로직은 자식 내부에서 처리합니다.
  const filteredItems = courses.filter((item) => (category === "all" ? true : item.category === category));
  const itemsPerPage = 3;
  const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
  const currentPageItems = filteredItems.slice((page - 1) * itemsPerPage, page * itemsPerPage);

  return (
    <>
      <h1 className="font-size:heading-md font-weight:bold margin-bottom:4">
        {category === "all" ? "전체" : category} 항목
      </h1>

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

      <div className="display:flex justify-content:center align-items:center gap:2">
        {page > 1 ? (
          <Link href={`/step2/ssr?category=${category}&page=${page - 1}`} className="m3-btn btn:outlined btn-size:sm">
            이전
          </Link>
        ) : (
          <button className="m3-btn btn:outlined btn-size:sm" disabled>이전</button>
        )}

        <span className="font-size:body-sm font-weight:medium padding-x:2">
          {page} / {totalPages || 1}
        </span>

        {page < totalPages ? (
          <Link href={`/step2/ssr?category=${category}&page=${page + 1}`} className="m3-btn btn:outlined btn-size:sm">
            다음
          </Link>
        ) : (
          <button className="m3-btn btn:outlined btn-size:sm" disabled>다음</button>
        )}
      </div>
    </>
  );
}
```

### 7-2. page.tsx에서 CourseList로 교체

**파일**: `app/step2/ssr/page.tsx`

- 상단에 CourseList를 import합니다.
- items 배열, filteredItems, itemsPerPage, totalPages, currentPageItems 변수를 삭제합니다.
- `<main>` 태그 안에 `<CourseList category={category} page={page} />`를 넣습니다.

```tsx
import Link from "next/link";
import CategoryList from "./CategoryList";
import CourseList from "./CourseList";

export default async function SSRPage({
  searchParams,
}: {
  searchParams: Promise<{ category?: string; page?: string }>;
}) {
  const params = await searchParams;
  const category = params.category || "all";
  const page = parseInt(params.page || "1", 10);

  return (
    <div className="site-body site-body:aside padding:4">
      <aside className="site-aside">
        <CategoryList activeCategory={category} />
      </aside>

      <main className="site-content">
        <CourseList category={category} page={page} />
      </main>
    </div>
  );
}
```

**✅ 확인**

- `app/step2/ssr/CourseList.tsx` 파일이 완성되었습니다.
- page.tsx는 CategoryList와 CourseList 두 컴포넌트만 호출합니다.
- 브라우저에서 `http://localhost:3000/step2/ssr`으로 접속하면, 앞 편과 동일한 UI가 표시됩니다.
- 카테고리 클릭, 페이지네이션이 정상적으로 동작합니다.

**🎓 newlec 쌤의 코멘트**

이제 page.tsx는 매우 짧아졌습니다. searchParams를 읽고, category와 page를 추출한 후, 두 컴포넌트에게 전달하는 역할만 합니다. CategoryList와 CourseList는 각각 자기 자신의 데이터를 스스로 관리하고, 렌더링합니다. 이것이 "데이터는 자식이 스스로 패치하는 것이 기본" 원칙의 결과입니다.

**📝 이 단계의 핵심**

- CourseList는 category와 page를 props로 받고, courses 데이터와 로직을 내부에서 처리합니다.
- page.tsx는 상태 추출과 props 전달만 담당합니다.

## 8. 결합도 관점에서의 정리

이제 분리 후의 구조를 결합도 관점에서 정리해 볼게요.

### 8-1. "어쩔 수 없이 부모와 관계를 가지는 것"

- activeCategory (CategoryList)
- category, page (CourseList)

이 값들은 URL에서 온 상태이므로, 부모가 알고 자식에게 전달해야 합니다. 이것이 필수적인 결합입니다.

### 8-2. "스스로 가질 수 있는 것"

- categories 배열 (CategoryList)
- courses 배열, 필터링·슬라이싱 로직 (CourseList)

이 값들은 자식이 스스로 정의하거나 계산할 수 있습니다. 따라서 props로 넘길 필요가 없습니다. 이것이 불필요한 결합을 제거한 것입니다.

### 8-3. 결합도 낮추기의 효과

- 독립성: CategoryList는 page.tsx가 어떻게 category를 추출하는지 몰라도 됩니다.
- 재사용성: CategoryList를 다른 페이지에서도 사용할 수 있습니다. (다른 URL 구조에 맞게 href만 수정)
- 테스트 용이성: CategoryList를 단독으로 테스트할 수 있습니다.

**✅ 확인**

- "어쩔 수 없이 부모와 관계를 가지는 것(현재 상태)"과 "스스로 가질 수 있는 것(데이터, 계산)"을 구분했습니다.
- 결합도를 낮추면 관리가 편해진다는 점을 이해했습니다.

**🎓 newlec 쌤의 코멘트**

소프트웨어 설계에서 가장 중요한 것은 "무엇을 어디에 둘 것인가"입니다. 데이터를 부모에 두면, 부모가 자식의 내부 구현을 알게 되고, 결합도가 높아집니다. 데이터를 자식에 두면, 자식이 독립적으로 관리되고, 결합도가 낮아집니다. 이 원칙을 기억하면, 복잡한 앱도 관리 가능한 구조로 설계할 수 있습니다.

**📝 이 단계의 핵심**

- "어쩔 수 없이 부모와 관계를 가지는 것"은 상태입니다.
- "스스로 가질 수 있는 것"은 데이터와 계산입니다.
- 결합도를 낮추면 관리가 편해집니다.

## 9. 분리 후 동작 최종 확인

이제 분리 후에도 SSR 동작이 동일한지, searchParams → 상태 추출 → props 전달 → 자식 내부 데이터 패치 흐름이 깨지지 않는지 확인해 볼게요.

### 9-1. 브라우저에서 최종 확인

브라우저에서 `http://localhost:3000/step2/ssr`으로 이동합니다.

- 초기 상태: `?category=all&page=1`
- "frontend" 클릭: `?category=frontend&page=1`
- "다음" 클릭: `?category=frontend&page=2`
- 새로고침: URL이 유지되고, 상태가 복원됩니다.

### 9-2. DevTools Network 탭 확인

카테고리 클릭 시, 서버에 요청이 발생하는지 확인합니다. (SSR이므로 요청이 발생합니다.)

**✅ 확인**

- 분리 후에도 SSR 동작이 동일합니다.
- searchParams → 상태 추출 → props 전달 → 자식 내부 데이터 패치 흐름이 깨지지 않습니다.
- URL이 상태의 소스이며, 새로고침 시 상태가 유지됩니다.

**🎓 newlec 쌤의 코멘트**

이제 우리는 SSR 페이지를 두 개의 컴포넌트로 분리했습니다. 이 과정에서 "데이터는 자식이 스스로 패치하는 것이 기본"이라는 원칙을 실습으로 체득했습니다. 이 원칙은 CSR에서도 동일하게 적용됩니다. 다음 편에서는 CSR 페이지를 같은 방식으로 분리해 보겠습니다.

**📝 이 단계의 핵심**

- 분리 후에도 SSR 동작이 동일합니다.
- searchParams → 상태 추출 → props 전달 → 자식 내부 데이터 패치 흐름이 유지됩니다.

## 정리

1단계: `app/step2/ssr/` 폴더에 분리 전 상태의 page.tsx를 준비했습니다.
2단계: CategoryList 컴포넌트를 분리하고, activeCategory만 props로 받도록 설계했습니다.
3단계: "데이터는 자식이 스스로 패치하는 것이 기본" 원칙을 이해했습니다.
4단계: activeCategory는 상태의 소스(URL)에서 온 값이므로, props로 전달해야 함을 이해했습니다.
5단계: page.tsx에서 CategoryList로 교체하고, activeCategory를 props로 전달했습니다.
6단계: CourseList 분리 힌트를 제공하고, 학생들이 직접 작성해 보았습니다.
7단계: CourseList 완성 코드를 확인하고, page.tsx에서 CourseList로 교체했습니다.
8단계: 결합도 관점에서 "어쩔 수 없이 부모와 관계를 가지는 것"과 "스스로 가질 수 있는 것"을 구분했습니다.
9단계: 분리 후에도 SSR 동작이 동일한지, searchParams → 상태 추출 → props 전달 → 자식 내부 데이터 패치 흐름이 깨지지 않는지 확인했습니다.
