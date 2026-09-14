---
tags: [웹, 자바스크립트, React, Vite, 실습]
---

> 🔗 관련 노트: [[024_Node.js·npm 실습]] · [[025_ES Module 실습]] · [[054_자바스크립트 플랫폼의 진화 — DOM API에서 jQuery, MVC, React(Flux)까지]]

# React 개발 환경 구축 실습

`nodeprj-for-react/` 폴더에서 CDN으로 React를 로드하던 기존 방식을 그대로 복원해 그 한계(모듈 미지원, 네트워크 의존성)를 직접 겪어본 뒤, Vite 번들러 + npm React 패키지 + JSX 조합으로 전환하고 컴포넌트 분리·HMR·프로덕션 빌드까지 확인한 실습이다.

## 1. `npm init -y` — 프로젝트를 Node.js 프로젝트로 등록

```
mkdir nodeprj-for-react
cd nodeprj-for-react
npm init -y
```

`package.json`이 생성되고 `"name"` 필드가 `nodeprj-for-react`로 설정된다. 이제부터 작성하는 코드는 브라우저가 직접 읽는 것이 아니라, Node.js 환경에서 처리된 뒤 브라우저로 전달된다. CDN 방식에서는 필요 없던 `package.json`이 이제부터는 모든 의존성 관리의 중심이 된다.

## 2. CDN 방식 복원 — 지금까지의 방식 재현

`.js` 파일이 Node.js 프로젝트 안에 있을 뿐, 아직은 브라우저가 `index.html`을 열면 CDN에서 React를 내려받고 `app.js`를 실행하는 기존 구조 그대로다.

파일: `index.html`

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>React CDN Demo</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
</head>
<body>
    <div id="root"></div>
    <script src="./app.js"></script>
</body>
</html>
```

파일: `app.js`

```js
const root = ReactDOM.createRoot(document.getElementById('root'));

function App() {
    return React.createElement('h1', null, 'CDN React App');
}

root.render(React.createElement(App));
```

CDN 방식에서는 `React`, `ReactDOM`이 `<script>` 태그로 로드된 전역 변수라서, `import` 없이 그대로 쓸 수 있다.

## 3. 로컬 서버로 실행하기

`file://`로 직접 열면 일부 기능이 제한되므로, `http-server`로 간단한 로컬 서버를 띄운다.

```
npm install http-server
npx http-server .
```

`http://localhost:8080`으로 접속하면 `CDN React App` 제목이 보인다. `npx`는 설치된 패키지의 실행 파일을 바로 실행해주는 명령어다.

## 4. CDN 방식의 한계 직접 겪어보기

`app.js`에 `Button` 컴포넌트를 추가로 작성해본다.

```js
// CDN 방식에서는 모듈 임포트(import) 문법을 사용할 수 없음
// 모든 코드가 하나의 파일에 담겨야 함

function App() {
    return React.createElement('div', null,
        React.createElement('h1', null, 'CDN React App'),
        React.createElement('p', null, '이것은 단일 파일입니다.')
    );
}

function Button() {
    return React.createElement('button', null, '버튼');
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(React.createElement(App));
```

페이지는 정상 렌더링되지만, `Button`을 별도 파일로 분리해 `import`로 가져오려 하면 브라우저가 `SyntaxError`를 낸다. CDN 방식은 `import`/`export` 모듈 시스템을 지원하지 않아 모든 코드가 단일 파일에 담기거나 전역 변수로 공유되어야 하고, 프로젝트가 커질수록 유지보수가 불가능해진다. 또한 CDN에서 React를 매번 내려받으므로 네트워크 연결에 취약하다 — 이것이 번들러가 필요한 이유다.

## 5. Vite 설치 — 번들러 도입

```
npm install -D vite
```

파일: `vite.config.js`

```js
import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: 3000,
    open: true
  }
});
```

`package.json`의 `scripts`도 아래처럼 정리한다.

```json
{
    "scripts": {
        "dev": "vite",
        "build": "vite build",
        "preview": "vite preview"
    }
}
```

Vite는 개발 중 서버를 빠르게 시작하고 HMR(Hot Module Replacement)을 지원하며, 프로덕션 빌드 시 최적화된 코드를 생성하는 번들러다. `npm install -D`로 설치했으므로 `devDependencies`에 기록되고, 프로덕션 배포 시에는 제외된다([[024_Node.js·npm 실습]] 9절 참고).

## 6. React를 npm 패키지로 설치, `import` 문법 사용

```
npm install react react-dom
```

파일: `index.html`(CDN 스크립트 태그 제거, 모듈로 로드)

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>React Bundled App</title>
</head>
<body>
    <div id="root"></div>
    <script type="module" src="/app.js"></script>
</body>
</html>
```

파일: `app.js`

```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';

function App() {
    return (
        <div>
            <h1>React Bundled App</h1>
            <p>이제 import/export를 사용할 수 있습니다.</p>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
```

`import React from 'react'` 한 줄이면 로컬 `node_modules`에서 React가 로드되어, CDN 없이 오프라인에서도 개발이 가능하다. 다만 아직 Vite가 JSX를 처리하지 못하므로 다음 단계에서 Babel 플러그인이 필요하다.

## 7. `@vitejs/plugin-react` — JSX 처리하기

```
npm install -D @vitejs/plugin-react
```

파일: `vite.config.js`

```js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true
  }
});
```

`@vitejs/plugin-react`는 내부적으로 Babel을 사용해 JSX를 `React.createElement()` 호출로 변환한다. 2절에서 직접 손으로 썼던 `React.createElement()` 호출을, 이제부터는 JSX로 작성하면 이 플러그인이 자동으로 변환해준다.

## 8. 개발 서버 실행 — 번들링 확인

```
npm run dev
```

`http://localhost:3000`에서 `React Bundled App` 제목이 보이고, 브라우저 개발자 도구의 Network 탭에는 CDN 요청(`react.production.min.js` 등)이 더 이상 없다. 코드가 Node.js 환경에서 번들링·최적화된 뒤 브라우저로 전달되는 것이다 — CDN 방식의 한계(모듈 미지원, 네트워크 의존성, 단일 파일 제한)가 모두 해결된 상태다.

## 9. 컴포넌트 분리 실습 — 모듈 시스템과 HMR

파일: `components/Button.js`

```jsx
import React from 'react';

function Button({ onClick, children }) {
    return (
        <button onClick={onClick}>
            {children}
        </button>
    );
}

export default Button;
```

파일: `app.js`

```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import Button from './components/Button';

function App() {
    const handleClick = () => {
        alert('버튼이 클릭되었습니다!');
    };

    return (
        <div>
            <h1>React Bundled App</h1>
            <p>이제 import/export를 사용할 수 있습니다.</p>
            <Button onClick={handleClick}>클릭하세요</Button>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
```

`Button` 컴포넌트를 별도 파일에 작성하고 `import`로 가져와 쓰는 것은 CDN 방식에서는 불가능했던 분리다. Vite는 파일 변경을 감지해 서버를 재시작하지 않고도 브라우저를 즉시 갱신하는 HMR을 제공하므로, 저장하는 즉시 버튼이 반영된다.

## 10. 프로덕션 빌드

```
npm run build
ls dist
ls dist/assets
```

`dist/` 폴더가 생성되고, `dist/index.html`과 `dist/assets/` 안에 `.js`·`.css` 파일이 들어있다. `dist/assets/`의 파일명에는 `index-abc123.js`처럼 해시 값이 포함되는데, 프로덕션 빌드에서 코드가 최소화(minify)되고 캐시 busting을 위해 파일명에 해시가 붙기 때문이다. 실제 배포 시에는 `dist/` 폴더의 내용만 서버에 올리면 된다.

## 11. 전체 흐름 정리

| 단계 | 내용 |
|---|---|
| 1 | `npm init -y`로 `package.json` 생성, Node.js 프로젝트 초기화 |
| 2~3 | CDN 기반 React 앱 구조 복원, `http-server`로 로컬 실행 |
| 4 | CDN 방식의 한계(모듈 미지원, 네트워크 의존성) 확인 |
| 5 | Vite 번들러 설치 |
| 6 | React를 npm 패키지로 설치, `import` 문법 사용 |
| 7 | `@vitejs/plugin-react`로 JSX 처리 |
| 8 | 번들링된 앱 실행, CDN 의존성 제거 확인 |
| 9 | 컴포넌트 분리 실습, HMR 경험 |
| 10 | 프로덕션 빌드로 `dist/` 폴더 생성 |
