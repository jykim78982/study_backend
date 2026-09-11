---
tags: [웹, 자바스크립트, Node.js, npm, 실습]
---

> 🔗 관련 노트: [[054_자바스크립트 플랫폼의 진화 — DOM API에서 jQuery, MVC, React(Flux)까지]] · [[055_자바스크립트 데이터 타입 — 원시값과 래퍼 객체, 배열, 객체, JSON]]

# Node.js·npm 실습

`node-prj/` 폴더 하나로 Node.js 프로젝트를 처음부터 만들면서, `npm install`이 실제로 무엇을 바꾸는지, `require`가 어떻게 그 코드를 찾아내는지, `package.json`의 `scripts`가 왜 필요한지를 직접 지우고 다시 설치해보며 확인한 실습이다.

## 1. Node.js 설치 확인과 프로젝트 폴더 만들기

VS Code 터미널(`Ctrl + ~` 또는 `Cmd + J`)에서 Node.js가 설치되어 있는지 먼저 확인한다.

```
node -v
```

`v18.x.x` 이상이 출력되면 정상이고, `node: command not found`가 나오면 nodejs.org에서 LTS 버전을 설치한 뒤 터미널을 다시 열어야 한다.

Node.js 프로젝트는 특별한 초기화 없이 빈 폴더 하나 + `.js` 파일 하나로 시작할 수 있다.

```
cd ~
mkdir node-prj
cd node-prj
```

`app.js`를 만들고 다음 한 줄만 작성한다.

```js
console.log('Hello, Node.js!');
```

```
node app.js
```

`Hello, Node.js!`가 출력되면 성공이다. 브라우저 없이 터미널만으로 자바스크립트 코드가 실행되는, Node.js의 가장 기본적인 동작이다.

## 2. `npm install` — 남이 만든 코드를 내려받기

이제 직접 짠 코드가 아니라 npm 레지스트리에 있는 남의 코드(`newlec-hello`)를 설치해서 써본다.

```
npm install newlec-hello
```

이 명령 하나가 `node-prj/` 안에 세 가지를 만들어낸다.

- **`node_modules/`** — 실제 라이브러리 코드가 저장되는 폴더 (`node_modules/newlec-hello/index.js` 등)
- **`package.json`** — 이 프로젝트가 `newlec-hello`를 쓴다는 기록(`"dependencies": { "newlec-hello": "^0.0.2" }`)이 새로 생김
- **`package-lock.json`** — 실제로 설치된 정확한 버전과 해시를 고정하는 파일

### 2-1. `package-lock.json`이 따로 필요한 이유

`package.json`에는 `"^0.0.2"`처럼 버전이 범위(`^`, 캐럿)로 적힌다. `^0.0.2`는 "정확히 0.0.2"가 아니라 "0.0.2 이상의 0.x.x 범위"를 뜻한다. 그래서 같은 `package.json`이라도 설치 시점에 따라 실제로 깔리는 버전이 달라질 수 있다 — 1월에 설치한 사람은 0.0.2를, 새 버전이 나온 뒤 3월에 설치한 팀원은 0.0.3을 받는 식이다.

`package-lock.json`은 "정확히 이 버전, 이 해시로 설치해야 한다"를 고정해서, 언제 누가 설치하든 완전히 같은 결과가 나오도록 보장한다. 또한 내가 직접 설치한 라이브러리뿐 아니라, 그 라이브러리가 내부적으로 의존하는 "의존성의 의존성"까지도 전부 여기에 기록된다.

## 3. `require` — 설치한 코드를 실제로 불러다 쓰기

설치만으로는 코드가 실행되지 않는다. `require`로 직접 불러와야 한다. `app.js`를 아래처럼 바꾼다.

```js
const newlecHello = require('newlec-hello');

console.log('Hello, Node.js!');
newlecHello.hello();
```

`require('newlec-hello')`처럼 `./`로 시작하지 않는 이름을 넘기면, Node.js는 자동으로 `node_modules/` 폴더 안에서 그 이름의 패키지를 찾아간다. 그래서 상대 경로를 직접 쓰지 않아도 된다.

```
node app.js
```

```
Hello, Node.js!
Hello Javascript
```

`newlec-hello`의 실제 소스는 이 정도로 짧다.

```js
var msg = 'Hello Javascript';
exports.hello = function () {
    console.log(msg);
};
```

React든 Express든 원리는 이것과 똑같다 — 누군가 만들어 npm에 올린 코드를 `require`로 불러와 쓰는 것뿐이며, 그 코드가 몇 줄이냐(4줄짜리 `newlec-hello` vs 수천 줄짜리 React)의 차이만 있을 뿐 사용법은 동일하다.

## 4. `package.json`의 `scripts` — `npm run start`로 단축하기

`package.json`은 npm이 읽는 "이 프로젝트에 대한 설명서"다. 여기에 `scripts` 항목을 추가하면 긴 명령어를 짧은 이름으로 대신 실행할 수 있다.

```json
{
    "name": "node-prj",
    "version": "1.0.0",
    "scripts": {
        "start": "node app.js"
    },
    "dependencies": {
        "newlec-hello": "^0.0.2"
    }
}
```

```
npm run start
```

`node app.js`를 직접 친 것과 결과는 같지만, 앞에 `> node-prj@1.0.0 start` / `> node app.js`라는 줄이 추가로 출력되어 "어떤 스크립트가 실행됐는지"를 알려준다. `start`라는 이름은 특별 취급되어 `run` 없이 `npm start`로도 실행할 수 있다.

`scripts`는 결국 "이름 → 명령어"의 사전이다. 팀원 여러 명이 각자 실행 명령을 외우는 대신, `package.json`에 한 번 정의해두고 `npm start`, `npm run build`, `npm run test`처럼 통일된 이름으로 실행하기 위한 장치다.

## 5. `node_modules/`는 지워도 되는 캐시일 뿐

npm에서 가장 중요한 개념은, **`node_modules/`는 언제든 다시 만들어낼 수 있는 캐시일 뿐이고, 진짜 소스는 `package.json`이라는 것**이다. 이를 직접 지웠다가 복원해보며 확인한다.

```
rm -rf node_modules
```

이 상태에서 실행하면 오류가 난다.

```
npm run start
```

```
Error: Cannot find module 'newlec-hello'
```

`node_modules/`가 없으니 `require('newlec-hello')`가 그 코드를 찾지 못하는 것이다. 이제 `package.json`만 가지고 다시 설치한다.

```
npm install
```

패키지 이름을 주지 않고 `npm install`만 실행하면, `package.json`의 `dependencies`를 읽어서 거기 적힌 라이브러리들을 전부 `node_modules/`에 다시 받아온다.

```
npm run start
```

```
Hello, Node.js!
Hello Javascript
```

다시 정상 동작한다. 이 원리 덕분에, 프로젝트를 다른 컴퓨터로 옮기거나 팀원에게 전달할 때 `node_modules/`(수십~수백MB) 전체를 넘길 필요 없이 `git clone` 후 `npm install` 한 번이면 충분하다 — `node_modules/`를 git 저장소에 올리지 않는 이유이기도 하다.

## 6. `npm uninstall` — 설치와 기록을 한 번에 정리하기

라이브러리를 더 이상 쓰지 않을 때는 `npm uninstall`을 쓴다.

```
npm uninstall newlec-hello
```

이 명령은 두 가지를 동시에 처리한다.

- `node_modules/newlec-hello/` 폴더를 삭제한다.
- `package.json`의 `dependencies`에서 `newlec-hello` 항목을 제거한다.

만약 `node_modules/newlec-hello`만 수동으로 지우고 `package.json`은 그대로 두면, `package.json`에는 여전히 의존성이 남아있으므로 다음에 `npm install`을 실행하는 순간 다시 설치되어버린다. `npm uninstall`은 이 두 가지를 한 번에 처리해준다.

라이브러리를 지운 뒤에는 코드에서 쓰던 `require`문도 함께 정리해야 한다.

```js
console.log('Hello, Node.js!');
```

## 7. 설치 전에 먼저 확인하기 — `npm view`, `npm search`

실무에서는 새 패키지를 설치하기 전에 버전·라이선스·의존성을 먼저 확인하는 습관이 중요하다.

```
npm view newlec-hello
```

버전, 라이선스, 의존성, 유지보수자 정보 등이 한꺼번에 출력된다. 특정 항목만 보고 싶으면 필드명을 이어서 쓴다.

```
npm view newlec-hello version
npm view newlec-hello license
npm view newlec-hello dependencies
```

패키지 이름이 정확히 기억나지 않을 때는 검색도 가능하다.

```
npm search hello
```

라이선스가 명시되어 있지 않은(`none`) 패키지는 상업적으로 쓰기에 제약이 있을 수 있으므로, 설치 전에 `npm view 패키지명 license`로 확인해두는 것이 안전하다.

## 8. `npm init` — package.json을 직접 만들기

지금까지의 `package.json`은 `npm install newlec-hello`를 실행했을 때 자동으로 생겨난 것이었다. 실무에서는 프로젝트를 시작할 때 `npm init`으로 직접 만들어서 이름·설명·라이선스 같은 프로젝트 정보를 채워 넣는다.

### 8-1. `npm init -y` — 질문 없이 기본값으로 생성

```
npm init -y
```

`-y`는 "모든 질문에 Yes"라는 뜻이다. **이미 `package.json`이 있으면 건드리지 않고, 없을 때만 기본값으로 새로 만든다** — 그래서 지금처럼 `package.json`이 이미 있는 상태에서 실행해도 기존 내용이 그대로 유지된다.

### 8-2. `npm init` — 대화형으로 하나씩 입력

```
npm init
```

`name`, `version`, `description`, `entry point`, `test script`, `repository url`, `keywords`, `author`, `license` 순서로 질문이 나오고, 그냥 Enter를 누르면 기본값이 적용된다. `description`에 "npm 기초 튜토리얼 프로젝트", `entry point`에 `app.js`, `license`에 `MIT`를 입력하고 마지막 `Is this OK?`에 `y`를 입력하면 아래처럼 필드가 추가된다.

```json
{
    "name": "node-prj",
    "version": "1.0.0",
    "description": "npm 기초 튜토리얼 프로젝트",
    "main": "app.js",
    "scripts": {
        "test": "test",
        "start": "node app.js"
    },
    "author": "",
    "license": "MIT",
    "dependencies": {
        "newlec-hello": "^0.0.2"
    }
}
```

`description`, `main`, `author`, `license`가 새로 생겼고, 기존에 있던 `scripts.start`는 그대로 유지된다.

### 8-3. `package.json` 주요 필드

| 필드 | 의미 | 예시 |
|---|---|---|
| `name` | 패키지 이름(npm에 배포할 때 쓰임) | `"node-prj"` |
| `version` | 버전(semver 형식) | `"1.0.0"` |
| `description` | 프로젝트 설명 | `"npm 기초 튜토리얼"` |
| `main` | 진입점 파일 — 다른 프로젝트가 `require`할 때 로드되는 파일 | `"app.js"` |
| `scripts` | `npm run 이름`으로 실행할 명령어 모음 | `"start": "node app.js"` |
| `dependencies` | 프로덕션(실서비스)에 필요한 패키지 | `"newlec-hello": "^0.0.2"` |
| `devDependencies` | 개발 중에만 필요한 패키지 | `"nodemon": "^3.0.0"` |
| `author` | 작성자 | `"newlec"` |
| `license` | 라이선스 | `"MIT"` |

`main` 필드가 중요한 이유는, 다른 프로젝트에서 이 패키지를 `require('node-prj')`로 불러오면 `main`이 가리키는 파일(`app.js`)이 로드되기 때문이다.

실무에서는 보통 `npm init -y`로 빠르게 생성한 뒤, `package.json`을 직접 열어서 필요한 필드만 수정하는 방식을 더 많이 쓴다. 대화형 `npm init`은 프로젝트를 새로 시작할 때 한 번 정도만 쓰는 경우가 많다.

## 9. `dependencies` vs `devDependencies`

패키지를 설치할 때 `npm install`로 하느냐 `npm install -D`로 하느냐에 따라 `package.json`의 서로 다른 항목에 기록된다.

| | `dependencies` | `devDependencies` |
|---|---|---|
| 의미 | 프로덕션(실서비스)에 필요한 패키지 | 개발 중에만 필요한 패키지 |
| 설치 명령 | `npm install 패키지명` | `npm install -D 패키지명` |
| 예시 | Express, React, newlec-hello | nodemon, jest, eslint |
| 프로덕션 배포(`npm install --production`) 시 | 설치됨 | 설치 안 됨 |

핵심은, 프로덕션 서버에 배포할 때 `npm install --production`을 실행하면 `devDependencies`에 있는 패키지는 아예 설치되지 않는다는 점이다 — "개발할 때만 쓰는 도구"를 실제 서비스 서버까지 끌고 갈 필요가 없기 때문이다.

### 9-1. `nodemon`을 devDependencies로 설치하기

`nodemon`은 코드를 수정하면 서버를 자동으로 재시작해주는, 개발 중에만 쓰는 도구다. 그래서 `devDependencies`에 설치한다.

```
npm install -D nodemon
```

`-D`는 `--save-dev`의 줄임말이다. 설치 후 `package.json`을 보면 `dependencies`와 별도로 `devDependencies`가 새로 생긴다.

```json
{
    "dependencies": {
        "newlec-hello": "^0.0.2"
    },
    "devDependencies": {
        "nodemon": "^3.1.0"
    }
}
```

`dependencies`에는 `newlec-hello`만 남아있고, `nodemon`은 `devDependencies`로 따로 분리되어 기록된다. 다만 `node_modules/` 안에는 `dependencies`든 `devDependencies`든 똑같이 설치된다 — 차이는 오직 `package.json`의 **어느 항목에 기록되느냐**일 뿐이다.

"프로덕션에서 실제로 쓰는가?"가 두 항목을 나누는 기준이다 — 실제 서비스 코드가 의존하는 라이브러리(`newlec-hello`)는 `dependencies`, 개발 편의를 위한 도구(`nodemon`)는 `devDependencies`에 둔다.

## 10. `npm run dev` — nodemon으로 자동 재시작하기

`nodemon`을 설치했으니 `package.json`의 `scripts`에 `dev` 항목을 추가해서 실행해본다.

```json
"scripts": {
    "test": "test",
    "start": "node app.js",
    "dev": "nodemon app.js"
}
```

```
npm run dev
```

`nodemon`이 `app.js`를 실행하고, 종료되지 않은 채 파일 변경을 계속 지켜보는 상태가 된다.

```
[nodemon] 3.1.0
[nodemon] searching for source files...
Hello, Node.js!
```

이 상태에서 `app.js`의 내용을 바꾸고 저장하면, 터미널에서 아무 명령도 치지 않았는데 자동으로 재시작된다.

```
[nodemon] file change detected...
[nodemon] restarting...
Hello, Node.js! (수정됨)
```

`npm run start`(`node app.js`)는 파일을 고칠 때마다 직접 다시 실행해야 하지만, `npm run dev`(`nodemon app.js`)는 저장하는 순간 알아서 재시작해준다. 그래서 관례적으로 **개발 중에는 `npm run dev`, 실제 배포 후 서버를 띄울 때는 `npm start`**를 쓴다. `nodemon`이 `devDependencies`에 있는 이유도 이와 같다 — 프로덕션에서는 `npm start`만 쓰므로 `nodemon` 자체가 필요 없다.

실행 중인 `nodemon`은 `Ctrl + C`로 종료한다.

## 11. `npm run` 명령어 정리

| 명령 | 실제 실행되는 내용 | 용도 |
|---|---|---|
| `npm start` / `npm run start` | `node app.js` | 프로덕션 실행 |
| `npm run dev` | `nodemon app.js` | 개발 중 자동 재시작 |
| `npm test` | `scripts.test`에 등록된 명령 | 테스트 실행 |

`start`와 `test`는 npm이 특별 취급하는 이름이라 `run` 없이 `npm start`, `npm test`로 바로 쓸 수 있고, 그 외의 이름(`dev`, `build` 등)은 반드시 `npm run 이름` 형태로 써야 한다.

지금 이 프로젝트에 어떤 스크립트들이 있는지 한눈에 보고 싶을 때는 다음 명령으로 목록을 확인할 수 있다.

```
npm run --help
```

`package.json`을 직접 열어보지 않고도 이 프로젝트에 `dev` 스크립트가 있는지 같은 걸 바로 확인할 수 있어서, 실무에서 `build`·`lint`·`test`·`deploy`처럼 스크립트가 여러 개로 늘어날수록 유용하다.

## 12. 모듈 시스템 이전 — 전역 스코프 공유와 그 한계

자바스크립트는 원래 모듈 시스템이 없었다. 브라우저에서 여러 `.js` 파일을 로드하는 방법은 `<script>` 태그를 여러 개 나열하는 것뿐이었다.

```html
<script src="math.js"></script>
<script src="utils.js"></script>
<script src="app.js"></script>
```

이 구조에서 중요한 점은, **스크립트 파일 하나가 다른 스크립트 파일을 스스로 불러올 방법이 없다**는 것이다. `math.js`가 "나는 `utils.js`가 필요해"라고 코드로 말할 수 없고, 오직 HTML이 `<script>` 태그를 적어놓은 순서대로 로드해주는 것에 전적으로 의존해야 했다.

이렇게 로드된 스크립트들은 전부 **같은 전역 스코프를 공유**한다. 그래서 `math.js`에서 만든 함수를 `app.js`에서 쓰려면, 그 함수가 전역 변수로 노출되어 있어야만 한다.

```js
// math.js
function add(a, b) {
    return a + b;
}

// utils.js — 같은 이름을 또 정의
function add(a, b) {
    return a + b;
}
```

두 파일 모두 `add`라는 이름을 전역에 올리면, 나중에 로드된 파일의 `add`가 먼저 로드된 파일의 `add`를 그냥 덮어써버린다. `app.js`에서 `add(1, 2)`를 호출했을 때 실제로 어느 파일의 `add`가 실행될지 코드만 보고는 알 수 없다 — 이것이 **전역 변수 오염** 문제다.

이 문제를 해결하려면, 각 파일이 "나는 이 함수만 외부에 공개하겠다"고 스스로 결정할 수 있는 장치가 필요하다. 이렇게 각 파일이 자신의 변수·함수를 외부에 공개할지 말지를 스스로 결정하는 것을 **고립화(isolation)**라 하고, 외부에서 "이 파일의 이것만 가져다 쓰겠다"고 명시적으로 요청하는 것을 **명시적 요청**이라 한다. Node.js는 이 두 가지를 해결하기 위한 모듈 시스템으로 **CommonJS**를 채택했다.

## 13. CommonJS — `exports`와 `module.exports`

CommonJS는 "내보내기"와 "가져오기"라는 두 가지 역할을 각각 다른 문법으로 제공한다.

| 역할 | 문법 |
|---|---|
| 내보내기 — 이 파일에서 무엇을 공개할지 | `exports` 또는 `module.exports` |
| 가져오기 — 다른 파일에서 무엇을 쓸지 | `require('경로')` |

CommonJS의 `require`는 **동기적**으로 동작한다 — `require`를 호출하는 순간 그 파일이 바로 로드된다. 또한 CommonJS는 **Node.js 전용**이며, 브라우저에서는 동작하지 않는다(브라우저에서는 뒤에서 다룰 ES Module을 쓴다).

### 13-1. `math.js` 모듈 만들기

```js
function add(a, b) {
    return a + b;
}

function sub(a, b) {
    return a - b;
}

exports.add = add;
exports.sub = sub;
```

`exports`는 애초에 빈 객체(`{}`)다. `exports.add = add`는 이 빈 객체에 `add`라는 키를 추가하는 것뿐이다.

### 13-2. `exports` vs `module.exports`

`exports`는 사실 `module.exports`를 가리키는 참조(별칭)다. 그래서 이 둘의 관계를 정확히 알아야 실수를 피할 수 있다.

```js
// 방식 A — exports에 속성을 하나씩 추가
exports.add = add;
exports.sub = sub;

// 방식 B — module.exports 자체를 새 객체로 교체 (가장 흔한 방식)
module.exports = { add, sub };

// 방식 C — 함수 하나만 통째로 내보내기
module.exports = add;
```

| | `exports` | `module.exports` |
|---|---|---|
| 초기값 | `{}` | `{}` |
| 속성 추가(`.add = ...`) | 가능 | 가능 |
| 객체 자체를 교체(`= {...}`) | **안 됨** | 가능 |

`exports`는 `module.exports`를 가리키는 참조일 뿐이므로, `exports = { add }`처럼 `exports` 자체에 새 객체를 대입해버리면 그 순간 참조가 끊어져서 원래의 `module.exports`에는 아무 변화도 생기지 않는다. 즉 `exports`는 **속성을 덧붙이는 용도로만** 안전하게 쓸 수 있고, 객체 자체를 통째로 바꾸고 싶다면 반드시 `module.exports`를 써야 한다.

실무에서는 `module.exports = { add, sub };`처럼 한 줄로 객체를 통째로 내보내는 방식이 가장 흔히 쓰인다. `module.exports = add;`처럼 함수 하나만 내보내는 방식은 "이 파일은 이 함수 하나만 담당한다"는 의도가 분명할 때 쓴다.

### 13-3. 내보낸 객체 직접 확인하기

```
node -e "console.log(require('./math'))"
```

```
{ add: [Function: add], sub: [Function: sub] }
```

`exports.add = add; exports.sub = sub;`로 내보낸 두 함수가 그대로 객체 형태로 보인다.

## 14. `require`로 모듈 불러오기

### 14-1. 기본 사용법

```js
const math = require('./math');

console.log(math.add(1, 2)); // 3
console.log(math.sub(5, 3)); // 2
```

`require('./math')`처럼 `./`로 시작하는 경로는 "현재 폴더의 `math.js`"를 뜻한다. 반대로 `./`가 없으면(`require('math')`) Node.js는 `node_modules/` 안에서 그 이름의 패키지를 찾는다 — 상대 경로 여부가 "내 파일이냐, 설치한 패키지냐"를 가르는 기준이 되는 셈이다.

### 14-2. 구조 분해로 필요한 함수만 꺼내 쓰기

```js
const { add, sub } = require('./math');

console.log(add(1, 2)); // 3
console.log(sub(5, 3)); // 2
```

`math` 객체 전체를 변수에 담는 대신, 객체 구조 분해로 필요한 함수만 바로 꺼내서 `math.add(...)`가 아니라 `add(...)`처럼 더 짧게 쓸 수 있다.

### 14-3. `require`는 동기적이며 캐싱된다

```
node -e "const a = require('./math'); const b = require('./math'); console.log(a === b)"
```

```
true
```

같은 경로의 모듈을 여러 번 `require`해도 실제로는 처음 한 번만 로드되고, 이후에는 캐시된 결과를 그대로 반환한다. `require`가 동기적으로 동작한다는 특성 덕분에, 아래처럼 조건문 안에서 필요할 때만 모듈을 불러오는 것도 가능하다.

```js
if (process.env.DEBUG) {
    const logger = require('./logger');
}
```

이는 파일 최상단에서만 쓸 수 있고 조건부로는 쓸 수 없는 ES Module의 `import`와 대비되는 CommonJS만의 특징이다.

## 15. Node.js 내장 모듈 — `path`, `fs`, `os`

Node.js에는 `npm install` 없이 곧바로 `require`해서 쓸 수 있는 내장 모듈들이 있다. 내장 모듈은 `./`를 붙이지 않고 이름만으로 불러온다.

### 15-1. `path` — 파일 경로 조작

```js
const path = require('path');

console.log(path.join(__dirname, 'math.js'));
// /Users/사용자명/node-prj/math.js

console.log(path.dirname(__filename));
// /Users/사용자명/node-prj

console.log(path.extname('math.js'));
// .js
```

| 함수 | 역할 |
|---|---|
| `path.join(...)` | 여러 경로 조각을 이어 붙임 |
| `path.dirname(p)` | 디렉터리 부분만 추출 |
| `path.basename(p)` | 파일명만 추출 |
| `path.extname(p)` | 확장자만 추출 |

문자열을 직접 `'a' + '/' + 'b'`처럼 이어 붙이면 윈도우에서는 구분자가 `\`라서 깨질 수 있는데, `path.join`을 쓰면 운영체제에 맞는 구분자로 자동 처리되므로 실무에서 경로를 만들 때는 문자열 이어붙이기 대신 `path.join`을 쓰는 것이 안전하다.

### 15-2. `fs` — 파일 읽기

```js
const fs = require('fs');

const content = fs.readFileSync('math.js', 'utf-8');
console.log(content);
```

`fs`는 동기 함수(`readFileSync`)와 비동기 함수(`readFile`) 두 가지 계열을 모두 제공한다.

### 15-3. `os` — 시스템 정보

```js
const os = require('os');

console.log(os.platform());    // darwin / win32 / linux
console.log(os.arch());        // arm64 / x64
console.log(os.cpus().length); // CPU 코어 수
```

## 16. CommonJS의 한계와 ES Module 예고

CommonJS는 Node.js 안에서는 잘 동작하지만 몇 가지 한계가 있다.

| 한계 | 설명 |
|---|---|
| 브라우저에서 동작하지 않음 | `require`/`exports`는 Node.js 전용 문법이다 |
| 동적 import 불가 | 런타임에 조건에 따라 모듈을 유연하게 불러오는 표준 방법이 없다 |
| tree-shaking 불가 | 빌드 도구가 "어떤 export가 실제로 쓰이는지"를 정적으로 분석하기 어렵다 |

ES2015(ES6)부터 표준화된 **ES Module**(`import`/`export`)이 이 한계를 해결하기 위해 등장했다.

```js
// math.js (ES Module)
export function add(a, b) { return a + b; }
export function sub(a, b) { return a - b; }

// app.js (ES Module)
import { add, sub } from './math.js';
console.log(add(1, 2));
```

| | CommonJS | ES Module |
|---|---|---|
| 내보내기 | `module.exports = ...` | `export function ...` |
| 가져오기 | `const x = require(...)` | `import x from ...` |
| 사용 환경 | Node.js 전용 | Node.js + 브라우저 |

CommonJS(2009년)와 ES Module(2015년 표준화) 사이에는 시간차가 있었고, Node.js는 이미 CommonJS 생태계가 워낙 커진 뒤라 바로 전환하지 못했다. 지금의 Node.js는 `package.json`에 `"type": "module"`을 추가하면 ES Module로, 없으면 기본값인 CommonJS로 동작하는 방식으로 둘 다 지원한다. 같은 `math.js`·`app.js`를 실제로 ES Module 문법으로 바꿔보는 실습은 [[025_ES Module 실습]]에서 이어간다.
