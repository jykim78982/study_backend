---
tags: [웹, 자바스크립트, React, Next.js, 실습]
---

> 🔗 관련 노트: [[057_프론트엔드의 변화와 Next.js의 필요성]] · [[026_React 개발 환경 구축 실습]]

# Next.js 프로젝트 생성 실습

`ncafe/frontend/`에 TypeScript·`src/`·App Router 없이 가장 단순한 구조로 Next.js(Pages Router) 프로젝트를 생성하고, 기본 랜딩 페이지를 전부 지워 `Hello NextJS` 한 줄만 남긴 뒤 개발 서버로 확인한 실습이다.

## 1. `create-next-app`으로 프로젝트 생성하기

먼저 작업할 상위 폴더에 `ncafe` 폴더를 만든다.

```
mkdir ncafe
cd ncafe
```

`npx create-next-app@latest`만 실행하면 옵션을 하나씩 대화형으로 묻지만, 옵션을 미리 지정하면 질문 없이 한 번에 설치된다.

```
npx create-next-app@latest frontend --no-typescript --no-src-dir --no-eslint --no-tailwind --no-app --no-turbopack
```

| 옵션 | 의미 |
|---|---|
| `--no-typescript` | TypeScript를 쓰지 않고 순수 자바스크립트로 생성 |
| `--no-src-dir` | `src/` 폴더 없이 프로젝트 루트에 바로 `pages/` 등을 둠 |
| `--no-app` | App Router 대신 **Pages Router**(`pages/` 디렉터리 기반)를 사용 |
| `--no-tailwind` | Tailwind CSS를 설치하지 않음 |
| `--no-eslint` / `--no-turbopack` | ESLint, Turbopack 설정을 생략 |

`npx`가 없으면 `npm i -g npx`로 먼저 설치한다. Windows PowerShell에서도 같은 명령을 그대로 쓸 수 있다.

터미널에 `Success! Created frontend at ...`가 출력되면 완료다. `ncafe/frontend/`에 `package.json`과 `node_modules`가 생기고, `--no-src-dir`·`--no-app` 옵션 덕분에 `src/` 폴더와 `app/` 폴더 없이 `pages/` 디렉터리 기반 구조가 만들어진다.

`create-next-app`은 Next.js 공식 스캐폴딩 도구다. 지금 지정한 옵션들은 프로젝트 구조를 최대한 단순하게 만들어 초보자가 이해하기 쉽게 하려는 목적이며, 실무에서는 보통 TypeScript와 App Router를 함께 쓴다.

## 2. 랜딩 페이지 초기화 — "Hello NextJS"만 남기기

Pages Router에서 `pages/index.js`는 루트 경로(`/`)를 담당하는 페이지다. 여기에 있는 기본 랜딩 페이지 내용을 전부 지우고 아래로 교체한다.

파일: `frontend/pages/index.js`

```jsx
export default function Home() {
  return <h1>Hello NextJS</h1>;
}
```

`export default`로 내보낸 함수를 Next.js가 자동으로 이 경로의 페이지로 렌더링해준다.

### 2-1. 불필요한 CSS 삭제

```
rm frontend/styles/globals.css
```

Windows PowerShell에서는 `del frontend\styles\globals.css`를 쓴다. `styles/` 폴더 안에 남은 파일이 없으면 폴더째로 지운다.

```
rmdir frontend/styles
```

### 2-2. 불필요한 이미지 삭제

```
rm frontend/public/vercel.svg
rm frontend/public/next.svg
```

Windows PowerShell에서는 `del frontend\public\vercel.svg`, `del frontend\public\next.svg`를 쓴다. `public/` 폴더에 다른 파일이 없으면 폴더째로 지운다.

```
rmdir frontend/public
```

CSS와 이미지를 지우면 번들 크기가 줄고 프로젝트가 빈 캔버스 상태가 된다. `index.js`에 `import '../styles/globals.css'` 같은 줄이 남아 있으면 `Module not found` 에러가 나므로, CSS 파일을 지울 때는 이를 참조하던 `import`문도 함께 지워야 한다.

## 3. 개발 서버 실행과 확인

`frontend/` 폴더로 이동해 개발 서버를 띄운다.

```
cd frontend
npm run dev
```

터미널에 `ready - started server on http://localhost:3000`이 표시되면, 브라우저에서 `http://localhost:3000`을 열어 "Hello NextJS"가 크게 표시되는지 확인한다. 서버는 `Ctrl + C`로 멈출 수 있다.

`npm run dev`는 코드 변경 시 즉시 반영되는 핫 리로딩을 지원하는 개발 서버를 실행한다. 3000번 포트가 이미 사용 중이면 `npm run dev -- -p 3001`처럼 다른 포트를 지정할 수 있다. 실무에서는 이 개발 서버 대신, `npm run build`로 프로덕션 빌드를 만들고 `npm start`로 프로덕션 서버를 띄운다.

## 4. 전체 흐름 정리

| 단계 | 내용 |
|---|---|
| 1 | `create-next-app`에 `--no-typescript --no-src-dir --no-app` 등 옵션을 지정해 `ncafe/frontend/`에 Pages Router 기반 Next.js 프로젝트 생성 |
| 2 | `pages/index.js`를 `Hello NextJS` 한 줄로 초기화하고, 불필요한 CSS·이미지 삭제 |
| 3 | `npm run dev`로 개발 서버 실행 후 `http://localhost:3000`에서 결과 확인 |
