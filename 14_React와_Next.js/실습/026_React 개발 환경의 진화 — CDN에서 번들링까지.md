---
tags: [웹, 자바스크립트, React, Vite, 실습]
---

> 🔗 관련 노트: [[024_Node.js·npm 실습]] · [[025_ES Module 실습]] · [[054_자바스크립트 플랫폼의 진화 — DOM API에서 jQuery, MVC, React(Flux)까지]]

# React 개발 환경의 진화 — CDN에서 번들링까지

**대상**: React CDN 방식으로 `render()`와 `createElement()`를 사용해 본 사람

**목표**: 브라우저 CDN 방식의 한계를 직접 경험하고, Node.js 기반 번들링 환경으로 전환하는 이유를 실습으로 이해한다

**완성물**: `nodeprj-for-react/` 폴더에서 `npm run dev` 명령으로 실행되는 번들링된 React 앱

**전제**: Node.js가 설치되어 있어야 한다. 이전 따라하기에서 React CDN으로 `ReactDOM.render()`와 `React.createElement()`를 사용해 본 경험이 필요하다.

## 1. Node.js 프로젝트로 등록하기

React 공식 개발 환경은 Node.js 기반이다. 먼저 프로젝트 폴더를 만들고 `package.json`을 생성해 Node.js 프로젝트로 등록한다.

### 1-1. 프로젝트 폴더 생성 및 이동

터미널에서 실행한다.

```
mkdir nodeprj-for-react
cd nodeprj-for-react
```

### 1-2. `package.json` 생성

```
npm init -y
```

### 1-3. `package.json` 확인

파일: `package.json`

생성된 파일의 `"name"` 필드가 `nodeprj-for-react`로 설정되어 있는지 확인한다.

**✅ 확인**

- 터미널에 `Wrote to .../package.json` 메시지가 출력된다.
- `package.json` 파일이 폴더에 생성된다.

**🎓 newlec 쌤의 코멘트**

이제부터 우리가 작성하는 코드는 브라우저가 직접 읽는 것이 아니라, Node.js 환경에서 처리된 후 브라우저로 전달된다. `package.json`은 이 프로젝트의 '신원증명' 격으로, 어떤 라이브러리를 사용하고 어떻게 실행할지 정의하는 파일이다. CDN 방식에서는 이 파일이 필요 없었지만, 이제부터는 모든 의존성 관리의 중심이 된다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `npm: command not found` | Node.js 미설치 또는 PATH 미설정 | Node.js LTS 설치 후 터미널 재시작 |
| `EEXIST: file already exists` | 이미 `package.json`이 존재함 | 기존 파일을 삭제하거나 `npm init`을 다른 폴더에서 실행 |

**📝 이 단계의 핵심**

- React 개발은 Node.js 프로젝트로 시작한다.
- `package.json`은 프로젝트의 의존성과 스크립트를 관리하는 핵심 파일이다.

## 2. CDN 방식 복원 — 지금까지의 방식 재현

이제 브라우저에서 직접 React를 로드하는 기존 방식을 Node.js 프로젝트 안에 그대로 구현한다. 이 단계는 '현재 상태'를 복원하는 과정이다.

### 2-1. `index.html` 생성

파일: `index.html`

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>React CDN Demo</title>
    <!-- React 18 CDN -->
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
</head>
<body>
    <div id="root"></div>
    <!-- 앱 로직 -->
    <script src="./app.js"></script>
</body>
</html>
```

### 2-2. `app.js` 생성

파일: `app.js`

```js
// CDN 방식에서는 React와 ReactDOM이 전역 변수로 사용 가능
const root = ReactDOM.createRoot(document.getElementById('root'));

function App() {
    return React.createElement('h1', null, 'CDN React App');
}

root.render(React.createElement(App));
```

**✅ 확인**

- `index.html`과 `app.js` 파일이 `nodeprj-for-react/` 폴더에 생성된다.
- `app.js`에는 `React.createElement`를 사용한 코드가 있다.

**🎓 newlec 쌤의 코멘트**

이 코드는 이전 따라하기에서 작성했던 것과 거의 동일하다. 하지만 이제는 이 파일들이 Node.js 프로젝트 안에 있다. 아직까지는 브라우저가 `index.html`을 열면 CDN에서 React를 다운로드하고 `app.js`를 실행하는 구조다. 다음 단계에서 이 구조를 실행해 보고, 그 한계를 직접 확인해본다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `React is not defined` | CDN 스크립트 로드 실패 또는 순서 문제 | `index.html`의 `<script>` 태그 순서가 react → react-dom → app.js인지 확인 |
| `Uncaught TypeError: ReactDOM.createRoot is not a function` | React 18 CDN URL 오류 | `react-dom@18/umd/react-dom.production.min.js` 경로가 정확한지 확인 |

**📝 이 단계의 핵심**

- CDN 방식은 HTML에 스크립트 태그를 직접 포함하는 구조다.
- `app.js`는 브라우저에서 직접 실행되는 파일이다.

## 3. 로컬 서버로 실행하기

브라우저에서 파일을 직접 열면 `file://` 프로토콜로 인해 일부 기능이 제한될 수 있다. Node.js로 간단한 로컬 서버를 만들어 페이지를 띄운다.

### 3-1. `http-server` 설치

```
npm install http-server
```

### 3-2. 서버 실행

```
npx http-server .
```

### 3-3. 브라우저로 접속

브라우저 주소창에 `http://localhost:8080`을 입력한다.

**✅ 확인**

- 터미널에 `Starting up http-server, serving .` 메시지가 출력된다.
- 브라우저에 `CDN React App`이라는 제목이 보인다.

**🎓 newlec 쌤의 코멘트**

`http-server`는 개발 중 빠른 테스트를 위한 도구다. 실제 프로젝트에서는 더 복잡한 기능을 가진 개발 서버를 사용하지만, 지금은 단순히 파일을 서빙하는 용도로 충분하다. 이 단계에서 중요한 것은 페이지가 정상적으로 렌더링된다는 점이다. 아직까지는 CDN 방식이 잘 작동하고 있다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `EADDRINUSE: address already in use` | 포트 8080이 이미 사용 중 | `npx http-server . -p 3000`으로 다른 포트 지정 |
| 브라우저에 404 에러 | 현재 폴더가 `nodeprj-for-react/`가 아님 | `cd nodeprj-for-react` 후 다시 실행 |

**📝 이 단계의 핵심**

- 로컬 서버는 개발 중 파일 서빙과 캐시 문제를 해결한다.
- `npx`는 설치된 패키지의 실행 파일을 즉시 실행하는 명령어다.

## 4. CDN 방식의 한계 직접 겪어보기

이제 CDN 방식의 한계를 직접 경험한다. `app.js`를 수정해서 컴포넌트를 추가하고, 그 과정에서 발생하는 불편함을 확인한다.

### 4-1. `app.js` 수정 — 컴포넌트 분리 시도

파일: `app.js`

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

### 4-2. 서버 재시작 후 확인

터미널에서 `Ctrl+C`로 서버를 종료하고 다시 실행한다.

```
npx http-server .
```

브라우저에서 `http://localhost:8080`을 새로고침한다.

**✅ 확인**

- 페이지가 정상적으로 렌더링된다.
- 하지만 `Button` 컴포넌트를 `App` 안에 사용하려면 `app.js` 안의 코드를 직접 수정해야 한다.
- `import` 문법을 사용하면 브라우저가 `SyntaxError`를 발생시킨다.

**🎓 newlec 쌤의 코멘트**

여기서 핵심 문제가 드러난다. CDN 방식에서는 `import`와 `export`를 사용할 수 없다. 모든 코드가 하나의 파일에 담겨야 하거나, 전역 변수로 공유해야 한다. 프로젝트가 커지면 이 방식은 유지보수가 불가능해진다. 또한, CDN에서 React를 로드할 때마다 네트워크 요청이 발생하고, 인터넷 연결이 불안정하면 앱이 로딩되지 않는다. 이것이 바로 번들러가 필요한 이유다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `SyntaxError: Unexpected token 'import'` | 브라우저가 ES 모듈 문법을 지원하지 않음(또는 설정 미적용) | CDN 방식에서는 `import`를 사용할 수 없다. 번들러가 필요하다. |
| `Uncaught ReferenceError: Button is not defined` | 함수 선언 순서 문제 | 함수 선언은 호이스팅되지만, CDN 방식에서는 모듈화가 어려워 구조가 복잡해짐 |

**📝 이 단계의 핵심**

- CDN 방식은 `import`/`export` 모듈 시스템을 지원하지 않는다.
- 모든 코드가 단일 파일에 담기면 프로젝트가 커질수록 관리가 불가능해진다.
- CDN 의존성은 네트워크 연결에 취약하다.

## 5. Vite 설치 — 번들러 도입

이제 Node.js 기반 번들러를 설치해서 이 문제를 해결한다. React 공식 문서에서 권장하는 Vite를 사용한다.

### 5-1. Vite 설치

```
npm install -D vite
```

### 5-2. Vite 설정 파일 생성

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

### 5-3. `package.json` 스크립트 추가

파일: `package.json`

`"scripts"` 섹션을 다음과 같이 수정한다.

```json
{
  "name": "nodeprj-for-react",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "vite": "^5.0.0"
  }
}
```

**✅ 확인**

- `node_modules/` 폴더에 `vite` 폴더가 생성된다.
- `vite.config.js` 파일이 생성된다.
- `package.json`에 `"dev": "vite"` 스크립트가 추가된다.

**🎓 newlec 쌤의 코멘트**

Vite는 현대적인 웹 개발을 위한 번들러다. 개발 중에는 서버를 빠르게 시작하고, HMR(Hot Module Replacement)을 지원하며, 프로덕션 빌드 시에는 최적화된 코드를 생성한다. `npm install -D`는 개발 전용 의존성으로 설치하는 명령어로, `node_modules`에만 기록되고 프로덕션 배포 시에는 제외된다([[024_Node.js·npm 실습]] 9절 참고).

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `vite: command not found` | `npx` 없이 직접 실행 | `npx vite` 또는 `npm run dev`로 실행 |
| 포트 충돌 | 3000 포트 사용 중 | `vite.config.js`에서 `port`를 변경 |

**📝 이 단계의 핵심**

- 번들러는 모듈 시스템을 지원하고, 코드를 최적화한다.
- Vite는 개발 중 빠른 서버 시작과 HMR을 제공한다.

## 6. React를 npm 패키지로 설치, `import` 문법 사용

이제 CDN에서 React를 로드하는 대신, npm으로 React를 설치해서 로컬에서 사용할 준비를 한다.

### 6-1. React 설치

```
npm install react react-dom
```

### 6-2. `index.html` 수정

파일: `index.html`

CDN 스크립트 태그를 제거하고, `app.js`를 모듈로 로드하도록 수정한다.

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>React Bundled App</title>
</head>
<body>
    <div id="root"></div>
    <!-- Vite는 index.html을 엔트리 포인트로 인식 -->
    <script type="module" src="/app.js"></script>
</body>
</html>
```

### 6-3. `app.js` 수정 — `import` 문법 사용

파일: `app.js`

```jsx
// 이제 import 문법을 사용할 수 있습니다
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

**✅ 확인**

- `node_modules/` 폴더에 `react`와 `react-dom` 폴더가 생성된다.
- `index.html`에 CDN 스크립트 태그가 없다.
- `app.js`에 `import`문과 JSX 문법이 있다.

**🎓 newlec 쌤의 코멘트**

이제 `import React from 'react'` 한 줄이면 React 라이브러리가 로컬 `node_modules`에서 로드된다. CDN에 의존하지 않고, 오프라인에서도 개발이 가능하다. 또한, `import`문 덕분에 코드를 여러 파일로 분리할 수 있게 된다. 하지만 아직 Vite가 JSX를 처리하지 못하므로, 다음 단계에서 Babel 플러그인을 추가해야 한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Failed to parse source` | Vite가 JSX를 처리하지 못함 | 다음 단계에서 `@vitejs/plugin-react` 설치 필요 |
| `Cannot find module 'react'` | `npm install react` 실행 안 함 | `npm install react react-dom` 실행 |

**📝 이 단계의 핵심**

- npm 패키지로 설치하면 CDN 의존성이 제거된다.
- `import` 문법은 모듈 시스템을 활성화한다.

## 7. `@vitejs/plugin-react` — JSX 처리하기

Vite는 기본적으로 JavaScript를 처리하지만, JSX 문법은 추가 처리가 필요하다. `@vitejs/plugin-react`를 설치해서 JSX를 변환한다.

### 7-1. React 플러그인 설치

```
npm install -D @vitejs/plugin-react
```

### 7-2. `vite.config.js` 수정

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

**✅ 확인**

- `node_modules/` 폴더에 `@vitejs/plugin-react` 폴더가 생성된다.
- `vite.config.js`에 `plugins: [react()]`이 추가된다.

**🎓 newlec 쌤의 코멘트**

`@vitejs/plugin-react`는 Babel을 내부적으로 사용해서 JSX를 `React.createElement()` 호출로 변환한다. 이전 따라하기에서 수동으로 `React.createElement()`를 작성했던 기억이 나는가? 이제부터는 JSX로 작성하면 이 플러그인이 자동으로 변환해준다. 이것이 바로 번들링 환경의 강력함이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Failed to parse source` | 플러그인 미설치 또는 설정 누락 | `vite.config.js`에 `plugins: [react()]` 확인 |
| `Cannot find module '@vitejs/plugin-react'` | 설치 안 됨 | `npm install -D @vitejs/plugin-react` 실행 |

**📝 이 단계의 핵심**

- JSX는 브라우저가 이해할 수 없는 문법이므로 변환이 필요하다.
- `@vitejs/plugin-react`는 Babel을 사용해 JSX를 변환한다.

## 8. 개발 서버 실행 — 번들링 확인

이제 모든 설정이 완료되었다. Vite 개발 서버를 실행해서 번들링된 React 앱을 확인한다.

### 8-1. 개발 서버 실행

```
npm run dev
```

### 8-2. 브라우저 확인

브라우저가 자동으로 열리거나, `http://localhost:3000`을 입력한다.

**✅ 확인**

- 터미널에 `VITE v5.x.x ready in xxx ms` 메시지가 출력된다.
- 브라우저에 `React Bundled App`이라는 제목과 "이제 import/export를 사용할 수 있습니다."라는 문장이 보인다.
- 브라우저 개발자 도구(Network 탭)에서 `react.production.min.js` 같은 CDN 요청이 없다.

**🎓 newlec 쌤의 코멘트**

이 순간이 바로 React 개발 환경의 진화다. 이제 코드는 Node.js 환경에서 번들링되고, 최적화된 상태로 브라우저에 전달된다. `import`문 덕분에 코드를 여러 파일로 분리할 수 있고, JSX로 작성하면 자동으로 변환된다. CDN 방식의 한계(모듈 미지원, 네트워크 의존성, 단일 파일 제한)가 모두 해결되었다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Port 3000 is in use` | 포트 충돌 | `vite.config.js`에서 port 변경 또는 기존 서버 종료 |
| 페이지가 하얗게 보임 | 콘솔 에러 존재 | 브라우저 개발자 도구(Console 탭)에서 에러 메시지 확인 |

**📝 이 단계의 핵심**

- `npm run dev`는 Vite 개발 서버를 실행한다.
- 번들링된 앱은 CDN 의존성 없이 로컬에서 실행된다.

## 9. 컴포넌트 분리 실습 — 모듈 시스템과 HMR

이제 모듈 시스템의 이점을 직접 경험한다. `App` 컴포넌트에서 `Button` 컴포넌트를 분리해서 다른 파일에 작성한다.

### 9-1. `Button` 컴포넌트 파일 생성

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

### 9-2. `app.js` 수정 — `Button` 임포트

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

### 9-3. 서버 자동 재시작 확인

Vite는 파일 변경을 감지해서 자동으로 서버를 재시작한다. 브라우저가 자동으로 새로고침된다.

**✅ 확인**

- `components/Button.js` 파일이 생성된다.
- 브라우저에서 "클릭하세요" 버튼이 보인다.
- 버튼을 클릭하면 "버튼이 클릭되었습니다!" 알림이 표시된다.
- 터미널에 `page reload` 또는 `hmr update` 메시지가 출력된다.

**🎓 newlec 쌤의 코멘트**

이것이 바로 모듈 시스템의 힘이다. `Button` 컴포넌트를 별도의 파일에 작성하고, `import`로 가져와서 사용했다. CDN 방식에서는 이런 분리가 불가능했다. 또한, Vite의 HMR(Hot Module Replacement) 덕분에 코드를 수정하면 브라우저가 즉시 업데이트된다. 서버를 재시작할 필요 없이, 개발 효율이 크게 향상된다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Cannot find module './components/Button'` | 파일 경로 오류 | `components/` 폴더가 `app.js`와 같은 폴더에 있는지 확인 |
| `Button is not a function` | `export default` 누락 | `Button.js` 마지막에 `export default Button;` 확인 |

**📝 이 단계의 핵심**

- 모듈 시스템 덕분에 코드를 여러 파일로 분리할 수 있다.
- Vite의 HMR은 개발 중 즉각적인 피드백을 제공한다.

## 10. 프로덕션 빌드

마지막으로, 프로덕션 환경에서 배포할 때의 빌드 과정을 확인한다.

### 10-1. 빌드 실행

```
npm run build
```

### 10-2. 빌드 결과 확인

```
ls dist
```

### 10-3. 빌드된 파일 구조 확인

```
ls dist/assets
```

**✅ 확인**

- `dist/` 폴더가 생성된다.
- `dist/index.html` 파일이 있다.
- `dist/assets/` 폴더에 `.js`와 `.css` 파일이 있다.
- `dist/assets/`의 `.js` 파일 이름이 해시 값이 포함된 형태다(예: `index-abc123.js`).

**🎓 newlec 쌤의 코멘트**

프로덕션 빌드에서는 코드가 최소화(minify)되고, 캐시 busting을 위해 파일 이름에 해시 값이 추가된다. `dist/` 폴더의 내용만 서버에 배포하면 된다. `index.html`은 여전히 `app.js`를 참조하지만, 실제 JS 파일은 `dist/assets/`에 있는 해시된 파일로 변경된다. 이것이 바로 번들링의 최종 결과물이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `dist/` 폴더가 생성되지 않음 | `npm run build` 실행 안 함 | `npm run build` 명령 실행 |
| `dist/index.html`에 `app.js` 참조 | 정상 동작 | 실제 JS 파일은 `dist/assets/`에 있음 |

**📝 이 단계의 핵심**

- 프로덕션 빌드는 `dist/` 폴더에 최적화된 파일을 생성한다.
- 파일 이름에 해시 값이 추가되어 캐시 busting이 가능하다.

## 정리

1단계: Node.js 프로젝트 초기화로 `package.json` 생성
2단계: CDN 기반 React 앱 구조 복원
3단계: 로컬 서버로 페이지 실행
4단계: CDN 방식의 문제점(모듈 미지원, 네트워크 의존성) 발견
5단계: Vite 번들러 설치
6단계: React를 npm 패키지로 설치, `import` 문법 사용
7단계: `@vitejs/plugin-react` 플러그인으로 JSX 처리
8단계: 번들링된 앱 실행, CDN 의존성 제거 확인
9단계: 컴포넌트 분리 실습, HMR 경험
10단계: 프로덕션 빌드 테스트, `dist/` 폴더 생성
