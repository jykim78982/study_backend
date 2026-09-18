---
tags: [웹, 자바스크립트, Node.js, npm, 실습]
---

> 🔗 관련 노트: [[054_자바스크립트 플랫폼의 진화 — DOM API에서 jQuery, MVC, React(Flux)까지]] · [[055_자바스크립트 데이터 타입 — 원시값과 래퍼 객체, 배열, 객체, JSON]] · [[063_자바스크립트 비동기 처리 — 콜백에서 async·await까지]]

# Node.js·npm 실습

**대상**: JavaScript 문법을 알지만 npm·Node.js 프로젝트를 처음 만드는 사람

**목표**: npm으로 외부 라이브러리를 설치하고, `package.json`의 `scripts`로 프로젝트를 실행하는 방법을 배운다

**완성물**: `npm run start` 한 줄로 실행되는 `node-prj/` 프로젝트

**환경**: VSCode + 터미널(Mac: `Cmd + J`, Windows/Linux: `Ctrl + ~` 또는 Terminal 메뉴 → New Terminal)

## 1. Node.js 설치 확인과 프로젝트 폴더 만들기

Node.js 프로젝트를 시작하려면 결국 `.js` 파일 하나면 된다. 하지만 나중에 npm으로 관리하려면 "프로젝트 폴더"가 필요하다. 그래서 먼저 빈 폴더를 만들고, 그 안에 첫 JavaScript 파일을 만들어서 `node` 명령어로 직접 실행해본다.

### 1-0. Node.js 설치 확인

VSCode에서 터미널을 연다(`Cmd + J` 또는 `Ctrl + ~`).

```
node -v
```

`v18.x.x` 또는 그 이상이 출력되면 OK다. `node: command not found`가 나오면 nodejs.org에서 LTS 버전을 설치하고 터미널을 다시 연다.

### 1-1. 프로젝트 폴더 만들기

VSCode 터미널에서 홈 폴더로 이동한 뒤 프로젝트 폴더를 만든다. 이 튜토리얼의 모든 파일은 `~/node-prj/` 폴더 안에 만든다(Mac: `~`는 `/Users/사용자명`, Windows: `~`는 `C:\Users\사용자명`).

```
cd ~
mkdir node-prj
cd node-prj
```

- `mkdir node-prj` → `node-prj` 폴더를 만든다.
- `cd node-prj` → 그 폴더 안으로 들어간다.

확인: 터미널 프롬프트가 `node-prj`로 바뀌었는지 확인한다(Mac: `user@MacBook node-prj %`, Windows: `C:\Users\사용자명\node-prj>`).

### 1-2. `app.js` 파일 만들기

VSCode에서 `app.js` 파일을 만든다.

방법 1 — VSCode 탐색기에서: 왼쪽 탐색기에서 `node-prj` 폴더를 우클릭 → 새 파일(New File) 선택 → 파일명 `app.js` 입력 → Enter

방법 2 — 터미널에서:

```
touch app.js
```

Windows PowerShell에서는 `touch`가 없으므로, VSCode 탐색기에서 직접 만들거나 `type nul > app.js`를 사용한다.

### 1-3. `app.js`에 코드 작성

VSCode에서 `app.js`를 열고 아래 내용을 입력한다.

파일: `app.js`

```js
console.log('Hello, Node.js!');
```

### 1-4. 실행

VSCode 터미널에서(현재 디렉터리가 `node-prj`인지 확인) 실행한다.

```
node app.js
```

**✅ 확인**

- 터미널에 `Hello, Node.js!`가 출력된다.

**🎓 newlec 쌤의 코멘트**

Node.js는 JavaScript를 브라우저 밖에서 실행하는 런타임이다. `node app.js` 한 줄이면 브라우저 없이 코드가 도는 것이다. 이 따라하기 실습의 목표는 npm을 사용하여 이 한 줄을 `npm run start`처럼 실행하게 만드는 것이다. npm이 프로젝트를 관리해주는 도구이기 때문이다 — 마치 Maven처럼.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `node: command not found` | Node.js 미설치 | nodejs.org에서 LTS 설치 후 터미널 다시 열기 |
| `Cannot find module 'app.js'` | `node-prj/` 폴더 안에 있지 않음 | `cd node-prj` 후 다시 실행 |

**📝 이 단계의 핵심**

- Node.js 프로젝트의 시작은 그냥 `.js` 파일 하나다.
- `node 파일명`으로 바로 실행할 수 있다.
- 항상 `node-prj/` 폴더 안에서 명령을 실행한다.

## 2. `npm install` — 남이 만든 코드를 내려받기

이제 우리 코드가 아니라, 다른 사람이 만든 코드를 써본다. npm은 "이 라이브러리 줘"라고 하면 알아서 내려받아주는 도구다. `newlec-hello`를 설치하고, 설치 후 프로젝트에 무엇이 새로 생겼는지 들여다본다.

### 2-1. `npm install` 실행

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
npm install newlec-hello
```

터미널에 `added 1 package in 1s` 같은 메시지가 나온다. `node-prj/` 폴더에 새 파일·폴더가 생긴다.

### 2-2. 무엇이 생겼는지 확인

VSCode 탐색기를 본다. `node-prj/` 안에 새로 생긴 것이 있다.

```
ls
```

- `node_modules/` 폴더가 생겼다.
- `package.json` 파일이 생겼다.
- `package-lock.json` 파일이 생겼다.

**`package-lock.json`은 왜 필요한가?**

`package.json`에 `"newlec-hello": "^0.0.2"`라고 적혀있는데, 이 `^`(캐럿)는 "0.0.2 정확히"가 아니라 "0.0.2 이상의 0.x.x"라는 범위를 뜻한다.

- 1월 1일에 `npm install` → 0.0.2 설치(아직 0.0.3이 안 나온 상태)
- 3월 1일에 팀원이 `npm install` → 0.0.3 설치(새 버전이 나온 상태)

`package.json`만 있으면 같은 파일인데, 언제 설치하느냐에 따라 다른 버전이 깔린다. `package-lock.json`이 있으면 "나 0.0.2로 설치했어. 너도 0.0.2로 해."라고 정확한 버전과 해시를 고정한다.

또 하나, 내가 직접 쓴 라이브러리만 `package.json`에 적혀있지, 그 라이브러리가 내부적으로 쓰는 "의존성의 의존성"까지 `package-lock.json`에 전부 적혀있다.

### 2-3. `node_modules/` 안 들여다보기

```
ls node_modules/newlec-hello
```

`index.js`, `package.json`이 보인다.

**✅ 확인**

- `node_modules/newlec-hello/index.js` 파일이 존재한다.
- `package.json`에 `"dependencies": { "newlec-hello": "^0.0.2" }`가 추가되었다.

**🎓 newlec 쌤의 코멘트**

`npm install`이 한 일을 정리하면 두 가지다.

1. 라이브러리 코드를 `node_modules/` 폴더에 다운로드
2. `package.json`에 "이 프로젝트는 `newlec-hello`를 쓴다"는 기록을 남김

`node_modules/`는 그냥 폴더다. 지워도 `npm install` 한 번이면 다시 생기는 것이다. 5단계에서 직접 확인한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `npm ERR! 404 Not Found` | 패키지 이름 오타 | `npm search newlec-hello`로 이름 확인 |
| `EACCES` 권한 에러 | macOS에서 권한 문제 | `sudo` 없이 `npm config set prefix ~/.npm` 후 재시도 |

**📝 이 단계의 핵심**

- `npm install 패키지명` → `node_modules/`에 코드 저장 + `package.json`에 기록
- `node_modules/`는 "지금 이 컴퓨터에 깔려있는 것"이고, `package.json`은 "무엇이 필요한지"의 목록이다.
- `package-lock.json`은 정확한 버전을 고정하는 파일이다.

## 3. `require` — 설치한 코드를 실제로 불러다 쓰기

설치만 하면 끝이 아니다. 실제로 불러와서 써봐야 한다. `require` 한 줄이면 끝인데, 이 한 줄이 React든 Express든 전부 같은 원리다.

### 3-1. `app.js` 수정

VSCode에서 `app.js`를 연다(탐색기에서 `app.js` 클릭).

현재 내용:

```js
console.log('Hello, Node.js!');
```

아래 내용으로 전체 교체한다.

파일: `app.js`

```js
const newlecHello = require('newlec-hello');

console.log('Hello, Node.js!');
newlecHello.hello();
```

`require('newlec-hello')` — `./`가 없으므로 Node.js가 `node_modules/` 안을 찾아간다.

### 3-2. 실행

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
node app.js
```

**✅ 확인**

터미널에 두 줄이 출력된다.

```
Hello, Node.js!
Hello Javascript
```

**🎓 newlec 쌤의 코멘트**

`newlec-hello`의 소스를 보면 이렇다.

```js
var msg = 'Hello Javascript';
exports.hello = function () {
    console.log(msg);
};
```

8년 전에 누군가 이 4줄을 npm에 올렸고, 지금 우리가 `require` 한 줄로 그걸 쓰고 있다. React든 Express든 원리는 똑같다 — 누군가의 코드를 `require`해서 쓰는 것이다. 그 "누군가의 코드"가 수천 줄이 되는 게 React이고, 4줄인 게 `newlec-hello`일 뿐이다. 공력의 차이가 있을 뿐, 사용법은 같다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Cannot find module 'newlec-hello'` | `node_modules/`가 없거나, `node-prj/` 폴더 밖에서 실행 | `npm install newlec-hello` 후 `node-prj/` 안에서 실행 |
| `newlecHello.hello is not a function` | `require`한 변수명이 다름 | `const newlecHello = require('newlec-hello');` 확인 |

**📝 이 단계의 핵심**

- `require('패키지명')` → `node_modules/패키지명`의 코드를 불러온다.
- 패키지 이름은 경로를 안 써도 되는 이유: Node.js가 자동으로 `node_modules/` 안을 찾아간다.

## 4. `package.json`의 `scripts` — `npm run start`로 단축하기

지금까지 `node app.js`를 매번 직접 쳤다. 하지만 실무에서는 `npm run start`처럼 단축 명령을 쓴다. 왜 그런지, `package.json`이 여기서 어떤 역할을 하는지, 그리고 실제로 `npm run start`를 설정해서 실행해본다.

### 4-1. `package.json`이 뭔지

VSCode에서 `package.json`을 연다(탐색기에서 `package.json` 클릭). 현재 내용은 대충 이렇다.

```json
{
  "name": "node-prj",
  "version": "1.0.0",
  "dependencies": {
    "newlec-hello": "^0.0.2"
  }
}
```

npm은 빌드 도구다. `package.json`을 읽어서 "이 프로젝트에 뭐가 필요한지, 어떤 명령을 실행해야 하는지"를 안다. `package.json`은 npm이 사용하는 프로젝트 설명 파일이다.

### 4-2. `scripts`에 `start` 추가

VSCode에서 `package.json`을 연다. `"version"` 줄 아래에 `"scripts"` 블록을 추가한다.

파일: `package.json`

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

주의: JSON은 콤마(`,`)에 민감하다. `"version": "1.0.0",` 뒤에 콤마가 있는지, `"scripts"` 블록 앞뒤에 콤마가 올바른지 확인한다.

### 4-3. `npm run start`로 실행

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
npm run start
```

**✅ 확인**

`node app.js`와 똑같은 결과가 나온다.

```
> node-prj@1.0.0 start
> node app.js

Hello, Node.js!
Hello Javascript
```

앞에 `> node-prj@1.0.0 start`라는 줄이 추가된 게 차이다. npm이 "어떤 스크립트를 실행한다"고 알려주는 메시지다.

### 4-4. `npm start`도 가능

```
npm start
```

`npm run start`의 줄임말이다. `start`만 특별히 `run` 없이 쓸 수 있다.

**🎓 newlec 쌤의 코멘트**

`scripts`는 "이름 → 명령어"의 사전이다. `"start": "node app.js"`는 `npm run start`를 치면 `node app.js`가 실행된다는 뜻이다.

왜 이렇게 하는가? 팀원 10명이 각자 `node app.js`를 외우는 것보다, `package.json`에 한 번 적어두고 `npm start`만 알면 되기 때문이다. 나중에 `build`, `test`, `lint` 같은 스크립트를 추가하면 `npm run build` 한 줄로 복잡한 명령을 실행할 수 있다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Missing script name` | `npm run` 뒤에 스크립트 이름 누락 | `npm run start`(`start`를 꼭 붙여야 함) |
| `ENOENT: no such file` | `scripts.start`의 파일 경로 오타 | `"start": "node app.js"`의 `app.js`가 실제로 존재하는지 확인 |
| `Unexpected token`(JSON 에러) | `package.json`에 콤마 누락/과다 | JSON 포맷 확인 — 콤마 위치 |

**📝 이 단계의 핵심**

- `package.json`의 `scripts`는 "이름 → 명령어" 매핑이다.
- `npm run 이름` = 해당 명령어 실행
- `npm start`는 `npm run start`의 줄임말이다.

## 5. `node_modules/`는 지워도 되는 캐시일 뿐

여기서 npm의 가장 중요한 개념을 체감해본다. `node_modules/`를 통째로 지워도 `package.json`만 있으면 다시 돌아온다. "이 폴더는 지워도 되는 거구나, 진짜 소스는 `package.json`이구나"를 직접 지워보고 다시 설치하면서 확인한다.

### 5-1. `node_modules/` 삭제

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
rm -rf node_modules
```

Windows PowerShell에서는 `rm -rf`가 안 된다. 대신:

```
Remove-Item -Recurse -Force node_modules
```

또는 VSCode 탐색기에서 `node_modules` 폴더를 우클릭 → 삭제한다.

### 5-2. 실행해보기 — 실패

```
npm run start
```

에러가 나온다: `Cannot find module 'newlec-hello'`. `node_modules/`가 없으니까 `require('newlec-hello')`를 못 찾는 것이다.

### 5-3. 다시 설치

```
npm install
```

`package.json`의 `dependencies`를 읽고 `node_modules/`를 다시 만든다. 터미널에 `added 1 package in 1s` 같은 메시지가 나온다.

### 5-4. 다시 실행

```
npm run start
```

다시 정상 동작한다.

```
Hello, Node.js!
Hello Javascript
```

**✅ 확인**

- `rm -rf node_modules` → `npm install` → `npm run start` 순서로 다시 돌아온다.

**🎓 newlec 쌤의 코멘트**

이게 npm의 가장 중요한 개념이다.

- `node_modules/` = 지금 이 컴퓨터에 깔려있는 것(지워도 됨, git에 올리지 않음)
- `package.json` = 무엇이 필요한지(이것만 있으면 어디서든 재설치 가능)

그래서 팀원에게 "프로젝트 받아서 실행해봐"라고 하면, `git clone` 후 `npm install` 한 줄이면 끝이다. `node_modules/`를 git에 올리지 않는 이유도 이것이다 — 100MB짜리 폴더를 올릴 필요 없이, `package.json`에 "`newlec-hello`가 필요해"라고 적혀있으니까.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `npm install` 후에도 에러 | `package.json`에 `dependencies`가 비어있음 | `npm install newlec-hello`(패키지명 명시)로 재설치 |
| `rm -rf` 실수로 다른 폴더 삭제 | 경로 오타 | `rm -rf node_modules` — 폴더명만 정확히 |

**📝 이 단계의 핵심**

- `node_modules/`는 재생산 가능한 캐시다.
- `package.json`의 `dependencies`가 진짜 "소스"다.
- 프로젝트 이동을 `git clone` + `npm install` 두 줄로 해결한다.

## 6. `npm uninstall` — 설치와 기록을 한 번에 정리하기

라이브러리를 더 이상 안 쓰게 되면 어떻게 정리하나? `node_modules/`에서 폴더만 지워도 되나? 아니면 `package.json`도 같이 고쳐야 하나? `npm uninstall`이 이 두 가지를 한 번에 처리하는지 직접 확인한다.

### 6-1. `npm uninstall`

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
npm uninstall newlec-hello
```

### 6-2. 확인

```
ls node_modules/
```

`newlec-hello` 폴더가 사라졌다(빈 폴더이거나 다른 패키지만 있음). VSCode에서 `package.json`을 연다.

```
cat package.json
```

`dependencies`에서 `newlec-hello`가 제거되었다.

### 6-3. `app.js`에서 `require`도 제거

VSCode에서 `app.js`를 연다.

현재 내용:

```js
const newlecHello = require('newlec-hello');

console.log('Hello, Node.js!');
newlecHello.hello();
```

아래 내용으로 전체 교체한다.

파일: `app.js`

```js
console.log('Hello, Node.js!');
```

### 6-4. 실행

```
npm run start
```

**✅ 확인**

- `Hello, Node.js!`만 출력되고 에러 없이 끝난다.

**🎓 newlec 쌤의 코멘트**

`npm uninstall`이 한 일도 두 가지다.

1. `node_modules/newlec-hello/` 폴더 삭제
2. `package.json`의 `dependencies`에서 제거

수동으로 `rm -rf node_modules/newlec-hello`만 하면 `package.json`에는 여전히 남아있어서, 다음에 `npm install`하면 다시 깔린다. `npm uninstall`은 두 가지를 한 번에 처리한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `node_modules`에서 삭제했는데 다시 `npm install`하면 돌아옴 | `package.json`에 여전히 `dependencies`로 남아있음 | `npm uninstall newlec-hello` 사용 |

**📝 이 단계의 핵심**

- `npm uninstall 패키지명` = `node_modules/` 삭제 + `package.json`에서 제거
- 수동 삭제는 `package.json`을 안 고치므로 `npm uninstall`을 사용한다.

## 7. 설치 전에 먼저 확인하기 — `npm view`, `npm search`

실무에서 새 패키지를 쓰기 전에 "이거 뭐야? 버전은? 라이선스는?"을 먼저 확인한다. `npm view`와 `npm search`로 설치 전에 정보를 조회하는 방법을 알아본다.

### 7-1. `npm view`

VSCode 터미널에서 실행한다.

```
npm view newlec-hello
```

버전, 라이선스, 의존성, 유지보수자 정보가 나온다.

### 7-2. 특정 필드만 보기

```
npm view newlec-hello version
npm view newlec-hello license
npm view newlec-hello dependencies
```

각각 한 줄씩만 출력된다.

### 7-3. `npm search`

```
npm search hello
```

npm 레지스트리에서 "hello"를 포함한 패키지 목록을 테이블 형태로 출력한다.

**✅ 확인**

- `npm view newlec-hello version` → `0.0.2`
- `npm search hello` → 여러 패키지 목록이 나온다.

**🎓 newlec 쌤의 코멘트**

`npm view`는 설치 전에 "이 패키지 뭐야?"를 확인하는 도구다. 실무에서 새 패키지를 쓸 때 `npm view 패키지명`으로 버전과 라이선스를 먼저 확인하는 습관을 들이면 좋다. 특히 라이선스가 `none`인 패키지(예: `newlec-hello`)는 상업적 사용이 제한될 수 있으니 주의한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `npm ERR! 404` | 패키지명이 없거나 오타 | `npm search`로 정확한 이름 찾기 |

**📝 이 단계의 핵심**

- `npm view 패키지명` → 패키지 메타정보 확인
- `npm search 키워드` → npm 레지스트리에서 패키지 검색
- 설치 전에 정보 확인하는 습관이 실무에서 중요하다.

**여기까지의 정리**

1단계 — Node.js 프로젝트는 `.js` 파일 + `node` 명령어부터 시작한다.
2단계 — `npm install`은 `node_modules/`에 코드 저장 + `package.json`에 기록한다.
3단계 — `require('패키지명')`으로 외부 코드를 불러온다.
4단계 — `package.json`의 `scripts`로 `npm run start` 같은 단축 명령을 만든다.
5단계 — `node_modules/`는 지워도 되고, `package.json`만 있으면 `npm install`으로 복원한다.
6단계 — `npm uninstall`로 `node_modules/` + `package.json`을 한 번에 정리한다.
7단계 — `npm view`·`npm search`로 설치 전 정보를 확인한다.

여기까지가 npm 기초 따라하기의 범위이고, 아래부터는 그 이후 실습에서 다룬 `npm init`·`devDependencies`·CommonJS 모듈 시스템 내용이다.

## 8. Node.js 프로젝트 — npm init과 devDependencies

**대상**: [[024_Node.js·npm 실습|Node.js 프로젝트 만들기 — npm 기초]](1~7단계)를 끝낸 사람

**목표**: 이전 예제에서는 노드 프로젝트를 생성하지 않았고, 자동으로 생성된 `package.json`의 모습을 보고 사용해보는 방법만 보았다. 이번에는 정식으로 노드 프로젝트를 생성하는 방법을 알아본다. `npm init`으로 `package.json`을 직접 만들고, `dependencies`와 `devDependencies`의 차이를 실습으로 이해한다.

**완성물**: `npm run dev`로 `nodemon`이 실행되는 `node-prj/` 프로젝트

**환경**: VSCode + 터미널(Mac: `Cmd + J`, Windows/Linux: `Ctrl + ~` 또는 Terminal 메뉴 → New Terminal)

**전제 조건**: 이전 따라하기 실습예제를 끝냈다면, `~/node-prj/` 폴더에 아래 파일이 있어야 한다.

```
node-prj/
├── app.js
├── package.json
├── package-lock.json
└── node_modules/
```

VSCode 터미널에서 확인한다.

```
cd ~/node-prj
ls
```

`app.js`, `package.json`, `package-lock.json`, `node_modules`가 보이면 OK다. 없다면 이전 예제를 먼저 끝낸다.

현재 `app.js` 상태(VSCode에서 `app.js`를 열어 확인):

```js
console.log('Hello, Node.js!');
```

이 튜토리얼은 이 `app.js`를 계속 사용한다.

### 8-1. `npm init` — package.json을 직접 만들기

지금까지 `package.json`은 `npm install`을 했을 때 자동으로 생긴 파일이었다. 하지만 실무에서는 `npm init`으로 직접 만들어서 프로젝트 정보를 설정한다. `npm init -y`와 `npm init` 두 가지 방식을 비교하면서, `package.json`의 각 필드가 뭔지 직접 확인한다.

#### 8-1-1. 현재 `package.json` 확인

VSCode에서 `package.json`을 연다(탐색기에서 `package.json` 클릭).

현재 내용:

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

이 파일은 2단계에서 `npm install newlec-hello`를 했을 때 자동으로 생성된 것이다. `name`은 폴더명, `version`은 기본값 `1.0.0`이다.

#### 8-1-2. `npm init -y`(자동 생성)

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
npm init -y
```

- `-y`는 "모든 질문에 Yes"라는 뜻이다.
- 기존 `package.json`이 있으면 덮어쓰지 않는다(기존 내용 유지).
- 기존 `package.json`이 없으면 기본값으로 생성한다.

확인: `package.json`을 다시 열어본다. 내용이 그대로다. `npm init -y`는 기존 파일이 있으면 건드리지 않는다.

#### 8-1-3. `npm init`(대화형)

VSCode 터미널에서 실행한다.

```
npm init
```

터미널에 질문이 하나씩 나온다.

```
name: node-prj
version: 1.0.0
description:
entry point: (index.js)
test script: (test)
repository url:
keywords:
author:
license: (ISC)
Is this OK? (y)
```

각 질문에 Enter를 누르면 기본값이 적용된다.

- `description`에 "npm 기초 튜토리얼 프로젝트"라고 입력하고 Enter
- `entry point`에 `app.js`라고 입력하고 Enter
- `license`에 `MIT`라고 입력하고 Enter
- `Is this OK?`에 `y` 입력 → Enter

#### 8-1-4. 변경된 `package.json` 확인

VSCode에서 `package.json`을 연다.

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

`description`, `main`, `author`, `license`가 추가되었다. 기존 `scripts.start`는 그대로 유지된다.

#### 8-1-5. `package.json` 필드 설명

| 필드 | 의미 | 예시 |
|---|---|---|
| `name` | 패키지 이름(npm에 올릴 때 사용) | `"node-prj"` |
| `version` | 버전(semver 형식) | `"1.0.0"` |
| `description` | 프로젝트 설명 | `"npm 기초 튜토리얼"` |
| `main` | 진입점 파일(다른 프로젝트에서 `require`할 때) | `"app.js"` |
| `scripts` | `npm run 이름`으로 실행할 명령어 | `"start": "node app.js"` |
| `dependencies` | 프로덕션에 필요한 패키지 | `"newlec-hello": "^0.0.2"` |
| `devDependencies` | 개발에만 필요한 패키지(8-2에서 배움) | `"nodemon": "^3.0.0"` |
| `author` | 작성자 | `"newlec"` |
| `license` | 라이선스 | `"MIT"` |

**✅ 확인**

- `npm init -y`는 기존 `package.json`이 있으면 건드리지 않는다.
- `npm init` 대화형으로 `description`, `main`, `author`, `license`를 설정했다.
- `package.json`의 각 필드가 뭔지 확인했다.

**🎓 newlec 쌤의 코멘트**

`npm init -y`는 "package.json이 없으면 기본값으로 만들어줘"라는 명령이다. 실무에서는 `npm init -y`를 먼저 치고, 나중에 VSCode에서 `package.json`을 직접 수정하는 경우가 많다.

`npm init` 대화형은 처음 프로젝트를 만들 때 한 번 쓰는 정도다. 매번 대화형으로 답할 필요는 없다.

`main` 필드가 중요한 이유: 다른 프로젝트에서 `require('node-prj')`를 하면, `main`이 가리키는 파일이 로드된다. `"main": "app.js"`라면 `app.js`가 로드되는 것이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `npm init` 후 `package.json`이 안 생김 | `Is this OK?`에 `n` 입력 | `y` 입력 후 Enter |
| `npm init -y` 후 기존 내용이 사라짐 | 기존 `package.json`이 없었음(새 폴더) | 정상 동작 — 기본값으로 생성된 것 |

**📝 이 단계의 핵심**

- `npm init -y` → 기본값으로 `package.json` 생성(기존 파일 있으면 건드리지 않음)
- `npm init` → 대화형으로 필드 설정
- `package.json`은 프로젝트의 "명함" — 이름, 버전, 설명, 의존성, 스크립트

## 9. `dependencies` vs `devDependencies`

`npm install`로 설치하면 `dependencies`에, `npm install -D`로 설치하면 `devDependencies`에 기록된다. 이 둘의 차이가 뭔지, 왜 구분하는지 실습으로 확인한다.

### 9-1. 개념

| | `dependencies` | `devDependencies` |
|---|---|---|
| 의미 | 프로덕션(실서비스)에 필요한 패키지 | 개발 중에만 필요한 패키지 |
| 설치 명령 | `npm install 패키지명` | `npm install -D 패키지명` |
| 예시 | Express, React, newlec-hello | nodemon, jest, eslint |
| `npm install` 시 | ✅ 설치됨 | ❌ 설치 안 됨(프로덕션 배포 시) |
| `npm install --dev` 시 | ❌ 설치 안 됨 | ✅ 설치됨 |

핵심: 프로덕션 서버에 배포할 때 `npm install --production`을 하면 `devDependencies`는 설치되지 않는다. "개발 중에만 쓰는 도구"를 프로덕션에 올리지 않는 것이다.

### 9-2. `nodemon` 설치(devDependencies)

`nodemon`은 개발 중에 코드를 수정하면 자동으로 서버를 재시작해주는 도구다. 프로덕션에서는 안 쓰므로 `devDependencies`에 설치한다.

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
npm install -D nodemon
```

`-D`는 `--save-dev`의 줄임말이다. 터미널에 `added 1 package in 2s` 같은 메시지가 나온다.

### 9-3. `package.json` 확인

VSCode에서 `package.json`을 연다.

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
  },
  "devDependencies": {
    "nodemon": "^3.1.0"
  }
}
```

`dependencies`에는 `newlec-hello`만 있다. `devDependencies`에 `nodemon`이 추가되었다.

### 9-4. `node_modules` 확인

```
ls node_modules/ | grep nodemon
```

`nodemon` 폴더가 `node_modules/` 안에 있다. `devDependencies`도 `node_modules/`에 설치된다(차이는 `package.json`에 어디에 기록되느냐다).

**✅ 확인**

- `npm install -D nodemon` 후 `package.json`에 `devDependencies`가 생겼다.
- `dependencies`에는 `newlec-hello`만 있고, `devDependencies`에는 `nodemon`이 있다.

**🎓 newlec 쌤의 코멘트**

"왜 `devDependencies`를 따로 구분하냐?"는 실무에서 가장 많이 받는 질문이다.

답은 간단하다. 프로덕션 서버에 `nodemon`을 올릴 필요가 없기 때문이다.

- `nodemon`은 개발 중에 "코드를 수정하면 자동으로 재시작"해주는 도구다.
- 프로덕션 서버에서는 코드를 수정하지 않으므로, `nodemon`이 필요 없다.
- `npm install --production`을 하면 `devDependencies`는 설치되지 않으므로, 프로덕션 서버에 `nodemon`이 깔리지 않는다.

반대로 `newlec-hello`는 프로덕션에서도 실제로 쓰이므로 `dependencies`에 있어야 한다.

한 줄 요약: "프로덕션에서 실제로 쓰나?" → 예: `dependencies`, 아니오: `devDependencies`

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `npm install -D` 후 `dependencies`에 들어감 | `-D` 누락 → `npm install nodemon` | `npm uninstall nodemon` 후 `npm install -D nodemon` |
| 프로덕션에서 `nodemon not found` | `devDependencies`가 프로덕션에 설치 안 됨 | 정상 동작 — `nodemon`은 개발 전용 |

**📝 이 단계의 핵심**

- `npm install 패키지명` → `dependencies`에 기록(프로덕션용)
- `npm install -D 패키지명` → `devDependencies`에 기록(개발용)
- 프로덕션 배포 시 `devDependencies`는 설치 안 됨
- "프로덕션에서 실제로 쓰나?"로 구분

## 10. `npm run dev` — nodemon으로 자동 재시작하기

`nodemon`을 설치했으니, `npm run dev` 명령으로 실행해본다. `nodemon`은 `node`와 비슷하게 파일을 실행하지만, 파일이 수정되면 자동으로 재시작한다.

### 10-1. `package.json`에 `dev` 스크립트 추가

VSCode에서 `package.json`을 연다. `scripts` 블록에 `"dev"`를 추가한다.

파일: `package.json`(`scripts` 부분만)

```json
"scripts": {
  "test": "test",
  "start": "node app.js",
  "dev": "nodemon app.js"
}
```

`"dev": "nodemon app.js"` — `npm run dev`를 치면 `nodemon app.js`가 실행된다.

### 10-2. `npm run dev` 실행

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
npm run dev
```

터미널에 다음이 나온다.

```
[nodemon] 3.1.0
[nodemon] searching for source files...
[nodemon] file change detected...
Hello, Node.js!
[nodemon] file change detected...
```

`nodemon`이 실행되고, `app.js`가 로드된다. 터미널이 잠겨있는 상태다(서버가 계속 도는 중).

### 10-3. 파일 수정 → 자동 재시작

VSCode에서 `app.js`를 연다.

현재 내용:

```js
console.log('Hello, Node.js!');
```

아래 내용으로 전체 교체한다.

파일: `app.js`

```js
console.log('Hello, Node.js! (수정됨)');
```

VSCode에서 `Cmd + S`(Mac) 또는 `Ctrl + S`(Windows/Linux)로 저장한다.

터미널에 자동으로 다음이 나온다.

```
[nodemon] file change detected...
[nodemon] restarting...
Hello, Node.js! (수정됨)
```

터미널에서 아무것도 안 쳤는데 자동으로 재시작되었다.

### 10-4. `nodemon` 종료

VSCode 터미널에서 실행한다.

```
Ctrl + C
```

`nodemon`이 종료되고 터미널이 돌아온다.

**✅ 확인**

- `npm run dev`로 `nodemon`이 실행되었다.
- `app.js`를 수정하고 저장하면 자동으로 재시작되었다.
- `Ctrl + C`로 종료했다.

**🎓 newlec 쌤의 코멘트**

`nodemon`은 개발 생산성을 가장 많이 올려주는 도구 중 하나다.

- `npm run start` → `node app.js` → 파일 수정 후 수동으로 다시 실행
- `npm run dev` → `nodemon app.js` → 파일 수정 후 자동으로 재시작

실무에서는 개발 중에는 `npm run dev`, 프로덕션에서는 `npm start`를 사용한다.

`nodemon`이 `devDependencies`에 있는 이유도 이것이다. 프로덕션에서는 `npm start`만 쓰니까, `nodemon`이 필요 없다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `nodemon: command not found` | `node_modules/.bin`이 PATH에 없음 | `npm run dev`(npm이 자동으로 `.bin`을 찾음) |
| `nodemon`이 안 재시작됨 | VSCode에서 저장 안 함 | `Cmd + S`/`Ctrl + S`로 저장 |
| 터미널이 잠겨있음 | `nodemon`이 계속 도는 중 | `Ctrl + C`로 종료 |

**📝 이 단계의 핵심**

- `npm run dev` → `nodemon app.js` → 파일 수정 시 자동 재시작
- 개발 중: `npm run dev`, 프로덕션: `npm start`
- `nodemon`은 `devDependencies`에 있음(프로덕션에 안 올라감)

## 11. `npm run` 명령어 정리

지금까지 배운 `npm run` 명령어를 정리한다.

### 11-1. 현재 `package.json`의 `scripts`

VSCode에서 `package.json`을 연다.

```json
"scripts": {
  "test": "test",
  "start": "node app.js",
  "dev": "nodemon app.js"
}
```

### 11-2. 명령어 정리

| 명령 | 실행 내용 | 용도 |
|---|---|---|
| `npm start` | `node app.js` | 프로덕션 실행 |
| `npm run start` | `node app.js` | 프로덕션 실행(위와 동일) |
| `npm run dev` | `nodemon app.js` | 개발 중 자동 재시작 |
| `npm test` | `test` | (아직 안 만든 스크립트) |

`npm start`, `npm test`는 `run` 없이 쓸 수 있는 특별한 이름이다. 다른 이름은 `npm run 이름`으로 써야 한다.

### 11-3. `npm run`

VSCode 터미널에서 실행한다.

```
npm run
```

사용 가능한 스크립트 목록이 나온다.

**✅ 확인**

- `npm start`, `npm run dev`가 정상 동작한다.
- `npm run`으로 사용 가능한 스크립트를 확인할 수 있다.

**🎓 newlec 쌤의 코멘트**

`npm run`은 "이 프로젝트에서 어떤 스크립트가 있는지"를 빠르게 확인하는 방법이다.

팀 프로젝트에서 `package.json`을 열어보지 않고도 `npm run`으로 "아, `dev` 스크립트가 있구나"를 알 수 있다.

실무에서는 `scripts`에 `build`, `lint`, `test`, `deploy` 같은 스크립트를 많이 추가한다. `npm run build` 한 줄로 복잡한 빌드 명령을 실행하는 것이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Missing script name` | `npm run` 뒤에 이름 누락 | `npm run dev` |
| `Unknown command: npm dev` | `npm run` 누락 | `npm run dev`(`start`, `test`만 `run` 없이 가능) |

**📝 이 단계의 핵심**

- `npm start`, `npm test` → `run` 없이 가능(특별한 이름)
- 다른 이름 → `npm run 이름`
- `npm run` → 사용 가능한 스크립트 목록 확인

### 11-4. 최종 확인

VSCode 터미널에서 실행한다.

```
ls
```

```
node-prj/
├── app.js              ← console.log('Hello, Node.js! (수정됨)')
├── package.json        ← scripts: start, dev / dependencies / devDependencies
├── package-lock.json
└── node_modules/
    ├── newlec-hello/   ← dependencies
    └── nodemon/        ← devDependencies
```

최종 실행:

```
npm run dev
```

`Hello, Node.js! (수정됨)`이 출력되면 성공이다. `Ctrl + C`로 종료한다.

**여기까지의 정리**

1단계 — `npm init -y`(자동) / `npm init`(대화형)으로 `package.json` 직접 만들기
2단계 — `npm install`(dependencies) vs `npm install -D`(devDependencies) 차이
3단계 — `npm run dev`로 `nodemon` 실행 → 파일 수정 시 자동 재시작
4단계 — `npm run` 명령어 정리(`start`, `test`는 `run` 없이 가능)

## 12. Node.js 모듈 시스템 — CommonJS 기초

**목표**: 노드에서 기본적으로 사용하는 CommonJS 모듈 시스템을 학습한다. 모듈 시스템은 무엇인지, 왜 그것을 사용해야 하는지를 관심 있게 본다. CommonJS는 노드에서는 자바스크립트의 모듈 시스템이 없을 때 노드가 선택한 모듈 시스템이다. `exports`/`module.exports`로 모듈을 만들고, `require`로 불러와 쓰는 방법을 사용한다.

**완성물**: `math.js` 모듈을 만들어 `app.js`에서 `require`로 사용하는 프로젝트(`node-prj/` 프로젝트를 계속 사용)

**환경**: VSCode + 터미널(Mac: `Cmd + J`, Windows/Linux: `Ctrl + ~` 또는 Terminal 메뉴 → New Terminal)

**전제 조건**: 이전 따라하기를 끝냈다면, `~/node-prj/` 폴더에 아래 파일이 있어야 한다.

```
node-prj/
├── app.js
├── package.json
├── package-lock.json
└── node_modules/
```

VSCode 터미널에서 확인한다.

```
cd ~/node-prj
ls
```

`app.js`, `package.json`, `package-lock.json`, `node_modules`가 보이면 OK다. 없다면 이전 따라하기를 먼저 끝낸다.

현재 `app.js` 상태 확인(VSCode에서 `app.js`를 열어 확인):

```js
console.log('Hello, Node.js!');
```

이 튜토리얼은 이 `app.js`를 계속 수정하면서 진행한다.

### 12-1. 모듈 시스템 이전 — 전역 스코프 공유와 그 한계

JavaScript는 원래 모듈 시스템이 없었다. 브라우저에서 여러 `.js` 파일을 `<script>` 태그로 로드하는 방식이 전부였고, 모든 스크립트는 전역 스코프를 공유했다.

그래서 함수를 정의하면 그 함수의 이름은 모든 파일에서 유일한 이름이어야만 했고, 사실상 이름 충돌을 피할 수 없었다. 뿐만 아니라 자바스크립트는 스스로 다른 파일을 직접 임포트할 수도 없어서 오로지 브라우저와 HTML의 도움을 받아야만 스크립트 파일을 가져올 수 있었다.

이 구조의 근본적인 한계를 알아보고, "고립화"가 왜 필요한지 이해해본다.

#### 12-1-1. 브라우저에서 여러 스크립트를 로드하는 방식

HTML에서 여러 `.js` 파일을 로드하는 방법은 `<script>` 태그를 여러 개 쓰는 것이다.

```html
<script src="math.js"></script>
<script src="utils.js"></script>
<script src="app.js"></script>
```

이 구조에서 중요한 한 가지: 스크립트 1이 스크립트 2를 "load"할 수 없다.

```
┌──────────────────────┐
│  <script src="">     │
│  </script>           │
└──────────┬───────────┘
           │ load
           ▼
┌──────────────────────┐
│     스크립트 1        │
└──────────┬───────────┘
           │ load  ← ❌ 불가능
           ▼
┌──────────────────────┐
│     스크립트 2        │
└──────────┬───────────┘
           │ load  ← ❌ 불가능
           ▼
┌──────────────────────┐
│     스크립트 3        │
└──────────────────────┘
```

- 스크립트 1이 "나 스크립트 2를 불러와야 해"라고 할 수 있는 방법이 없다.
- 모든 스크립트는 HTML이 순서대로 로드하는 것뿐이다.
- 스크립트 1이 스크립트 2의 함수를 쓰려면, 스크립트 2가 전역 변수로 그 함수를 노출해줘야 한다.

#### 12-1-2. 전역 변수 오염 문제

모든 스크립트가 전역 스코프를 공유하면, 이름 충돌이 일어난다.

파일: `math.js`

```js
function add(a, b) {
  return a + b;
}
```

파일: `utils.js`

```js
function add(a, b) {
  return a + b;  // 같은 이름!
}
```

두 파일 모두 `add`를 전역에 올리면, 후에 로드된 파일이 먼저 로드된 파일을 덮어쓴다. `app.js`에서 `add(1, 2)`를 부르면 어느 `add`가 실행될지 알 수 없다.

#### 12-1-3. 고립화(Isolation)란?

이 문제를 해결하려면 각 파일이 스스로 "나는 이 함수만 외부에 공개한다"고 결정해야 한다.

| 개념 | 의미 |
|---|---|
| 고립화 | 각 파일이 자신의 변수·함수를 외부에 "공개할 것"을 스스로 결정하는 것 |
| 명시적 요청 | 외부에서 "이 파일의 `add`만 가져다 쓸게"라고 명시적으로 요청하는 것 |

CommonJS는 이 두 가지를 `exports`(내보내기)와 `require`(가져오기)로 해결한다. 2단계에서 직접 써본다.

**✅ 확인**

- 브라우저의 `<script>` 태그 구조에서 스크립트가 서로를 `load`할 수 없다는 점을 이해했다.
- 전역 스코프 공유 → 이름 충돌 → 고립화가 필요하다는 흐름을 이해했다.

**🎓 newlec 쌤의 코멘트**

JavaScript가 모듈 시스템을 갖기 전까지, "여러 파일로 코드를 나누는 것"은 브라우저에서 `<script>` 태그 순서로만 가능했다. 스크립트 1이 "나 스크립트 2를 불러와야 해"라고 할 수 없었다.

그래서 모든 스크립트가 전역 스코프를 공유했고, 이름이 겹치면 나중에 로드된 게 먼저 로드된 걸 덮어썼다. 이게 "전역 변수 오염"이다.

Node.js가 CommonJS를 선택한 이유도 이것이다. "이 파일은 이 함수만 공개한다"고 명시적으로 말할 수 있는 시스템이 필요했다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `add is not a function` | 스크립트 로드 순서 오류 또는 전역 변수 덮어쓰기 | CommonJS로 모듈화(2단계) |
| `ReferenceError: add is not defined` | 전역에 노출되지 않은 함수를 다른 파일에서 사용 | `exports`로 명시적으로 내보내기 |

**📝 이 단계의 핵심**

- JS는 원래 모듈 시스템이 없었다 — `<script>` 태그 + 전역 스코프 공유
- 스크립트가 서로를 `load`할 수 없으므로, 전역 변수로만 공유 가능
- 전역 변수 공유 → 이름 충돌 → 고립화가 필요
- CommonJS는 `exports`/`require`로 고립화를 해결

## 13. CommonJS — `exports`와 `module.exports`

Node.js는 자바스크립트 자체적으로 고립화를 유지하고 코드 파일을 직접 가져올 수 있도록 AMD와 CommonJS 중에서 고민하다가 CommonJS를 선택했다.

CommonJS는 `exports`와 `module.exports` 두 가지 방식으로 "이 파일에서 무엇을 공개할지"를 결정할 수 있다. 1단계에서 만든 `add` 함수를 CommonJS 모듈로 변환하면서 export 방식을 직접 사용해본다.

### 13-1. CommonJS란?

CommonJS는 Node.js가 선택한 모듈 시스템이다.

| 역할 | 문법 |
|---|---|
| 내보내기(이 파일에서 뭘 공개할지) | `exports` 또는 `module.exports` |
| 가져오기(다른 파일에서 뭘 쓸지) | `require('경로')` |

- 동기적이다 — `require`를 부르면 바로 그 파일이 로드된다(비동기 아님).
- Node.js 전용이다 — 브라우저에서는 안 된다(ES Module이 브라우저용).

### 13-2. `math.js` 파일 만들기

VSCode에서 `node-prj/` 폴더 안에 `math.js` 파일을 만든다.

방법: VSCode 탐색기에서 `node-prj` 폴더를 우클릭 → 새 파일(New File) → `math.js`

파일: `math.js`

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

`exports`는 **빈 객체(`{}`)**다. `exports.add = add`는 "이 객체에 `add`라는 키를 추가한다"는 뜻이다.

### 13-3. `exports` vs `module.exports` 차이

`exports`는 `module.exports`의 별칭이다. 하지만 `module.exports`는 객체 자체를 교체할 수 있다.

방식 A: `exports`로 속성 추가(위 13-2에서 쓴 방식)

```js
exports.add = add;
exports.sub = sub;
```

방식 B: `module.exports`로 객체 교체(가장 일반적)

```js
module.exports = { add, sub };
```

방식 C: `module.exports`로 함수 하나만 내보내기

```js
module.exports = add;
```

| | `exports` | `module.exports` |
|---|---|---|
| 초기값 | `{}`(빈 객체) | `{}`(빈 객체) |
| 속성 추가 | `exports.add = ...` ✅ | `module.exports.add = ...` ✅ |
| 객체 교체 | `exports = { add }` ❌(안 됨) | `module.exports = { add }` ✅(됨) |

`exports`는 `module.exports`를 가리키는 참조다. `exports = { add }`라고 하면 참조를 끊어서 새로운 객체를 만들게 되므로, `module.exports`에는 아무것도 안 남는다.

### 13-4. 직접 확인 — `require`로 내보낸 객체 보기

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
node -e "console.log(require('./math'))"
```

`{ add: [Function: add], sub: [Function: sub] }`가 출력된다. `exports.add = add; exports.sub = sub;`로 내보낸 두 함수가 보인다.

**✅ 확인**

- `math.js` 파일이 `exports` 또는 `module.exports`로 함수를 내보내고 있다.
- `node -e "console.log(require('./math'))"`로 내보낸 객체를 직접 확인했다.

**🎓 newlec 쌤의 코멘트**

`exports`와 `module.exports`가 왜 둘이나 있냐고 묻는 사람이 많다.

`exports`는 "이 객체에 속성을 추가한다"는 용도이고, `module.exports`는 "이 객체 자체를 교체한다"는 용도다.

실무에서는 `module.exports = { add, sub }`를 가장 많이 쓴다. 한 줄로 끝이기 때문이다. `exports.add = add; exports.sub = sub;`처럼 줄을 늘려서 쓰는 건 코드가 길어질 때만 편하다.

`module.exports = add`처럼 함수 하나만 내보내는 경우도 있다. "이 파일은 `add` 함수 하나만 담당한다"는 명확한 의도가 있을 때다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `require('./math')`이 `{}`(빈 객체) | `exports = { add }`로 참조를 끊음 | `module.exports = { add }` 또는 `exports.add = add` |
| `math.add is not a function` | `module.exports = add`로 함수 하나만 내보냈는데 `math.add`로 접근 | `const add = require('./math')`로 직접 함수로 받기 |

**📝 이 단계의 핵심**

- `exports` = `module.exports`의 별칭(추가만 가능, 교체 불가)
- `module.exports` = 객체 자체를 교체 가능
- 실무에서는 `module.exports = { add, sub }`가 가장 일반적
- `module.exports = add`처럼 함수 하나만 내보내는 것도 가능

## 14. `require`로 모듈 불러오기

모듈을 만들었으면 불러와야 한다. `require()`는 "이 파일에서 뭘 가져올지"를 명시적으로 요청하는 문법이다. 다양한 `require` 방식을 직접 써보면서 "어떤 상황에서 어떤 방식을 쓰는지"를 익힌다.

### 14-1. `app.js` 수정 — 기본 `require`

VSCode에서 `app.js`를 연다(탐색기에서 `app.js` 클릭).

현재 내용:

```js
console.log('Hello, Node.js!');
```

아래 내용으로 전체 교체한다.

파일: `app.js`

```js
const math = require('./math');

console.log(math.add(1, 2));   // 3
console.log(math.sub(5, 3));   // 2
```

`./math` → 현재 폴더의 `math.js`. `./`가 없으면 Node.js가 `node_modules/`를 찾아간다.

### 14-2. 실행

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
node app.js
```

**✅ 확인**

터미널에 다음이 나온다.

```
3
2
```

### 14-3. 구조 분해로 특정 함수만 가져오기

VSCode에서 `app.js`를 연다. 아래 내용으로 전체 교체한다.

파일: `app.js`

```js
const { add, sub } = require('./math');

console.log(add(1, 2));   // 3
console.log(sub(5, 3));   // 2
```

`math` 객체에서 `add`와 `sub`만 꺼내서 바로 쓰는 방식이다. `math.add(1, 2)` 대신 `add(1, 2)`로 더 짧게 쓸 수 있다.

### 14-4. 실행

```
node app.js
```

**✅ 확인**

터미널에 다음이 나온다.

```
3
2
```

### 14-5. `require`의 캐싱 확인

VSCode 터미널에서 실행한다.

```
node -e "const a = require('./math'); const b = require('./math'); console.log(a === b)"
```

`true`가 출력된다. `require`는 같은 경로의 모듈을 두 번 로드하지 않는다. 첫 번째 로드 후 캐시에 저장하고, 이후에는 캐시에서 반환한다.

**🎓 newlec 쌤의 코멘트**

`require('./math')`의 `./`를 빼먹으면 안 된다. `require('math')`라고 쓰면 Node.js가 `node_modules/math`를 찾아간다. "내 폴더의 `math.js`"를 뜻하려면 `./math`가 필수다.

또 하나, `require`는 동기적이다. `require`를 부르는 순간 그 파일이 바로 로드된다. 그래서 `require`를 `if`문 안에 써서 "조건에 따라 모듈을 로드한다"는 것도 가능하다.

```js
if (process.env.DEBUG) {
  const logger = require('./logger');
}
```

이건 ES Module의 `import`로는 못 하는 일이다. `import`는 항상 파일 최상단에 있어야 하고, 조건부로 쓸 수 없다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Cannot find module 'math'` | `./` 누락 → `node_modules/math`를 찾음 | `require('./math')` |
| `math.add is not a function` | `module.exports = add`로 함수 하나만 내보냈는데 `math.add`로 접근 | `const add = require('./math')` |
| `require is not defined` | 브라우저에서 실행 | CommonJS는 Node.js 전용 — 브라우저에서는 ES Module 사용 |

**📝 이 단계의 핵심**

- `require('./파일명')` → 상대경로(현재 폴더)
- `require('패키지명')` → `node_modules/`에서 찾기
- 구조 분해 `const { add } = require('./math')`로 특정 함수만 가져올 수 있음
- `require`는 동기적 + 캐싱(같은 모듈은 한 번만 로드)

## 15. Node.js 내장 모듈 — `path`, `fs`, `os`

Node.js에는 `fs`, `path`, `os` 같은 내장 모듈이 이미 들어있다. `require`로 불러와서 바로 쓸 수 있다. npm으로 설치할 필요도 없다.

### 15-1. `path` 모듈 — 파일 경로 조작

VSCode에서 `app.js`를 연다. 아래 내용으로 전체 교체한다.

파일: `app.js`

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
| `path.join(...)` | 경로를 연결 |
| `path.dirname(p)` | 디렉터리 부분만 추출 |
| `path.basename(p)` | 파일명만 추출 |
| `path.extname(p)` | 확장자만 추출 |

### 15-2. 실행

VSCode 터미널에서(현재 디렉터리: `node-prj`) 실행한다.

```
node app.js
```

**✅ 확인**

- 절대경로 3줄이 출력된다(경로 앞부분은 자신의 홈 폴더로 다르다).

### 15-3. `fs` 모듈 — 파일 읽기

VSCode에서 `app.js`를 연다. 아래 내용으로 전체 교체한다.

파일: `app.js`

```js
const fs = require('fs');

const content = fs.readFileSync('math.js', 'utf-8');
console.log(content);
```

`fs`는 동기(`readFileSync`)와 비동기(`readFile`) 두 가지가 있다. 이 튜토리얼에서는 동기 버전만 쓰고, 비동기는 나중에 다룬다.

### 15-4. 실행

```
node app.js
```

**✅ 확인**

- `math.js`의 전체 코드가 터미널에 출력된다.

### 15-5. `os` 모듈 — 시스템 정보

VSCode에서 `app.js`를 연다. 아래 내용으로 전체 교체한다.

파일: `app.js`

```js
const os = require('os');

console.log(os.platform());    // darwin / win32 / linux
console.log(os.arch());        // arm64 / x64
console.log(os.cpus().length); // CPU 코어 수
```

### 15-6. 실행

```
node app.js
```

**✅ 확인**

- 플랫폼, 아키텍처, CPU 코어 수가 출력된다.

**🎓 newlec 쌤의 코멘트**

내장 모듈은 `require` 뒤에 `./`를 안 쓴다. `require('path')`, `require('fs')` — 그냥 이름만 쓰면 된다.

`./`가 있으면 "내 폴더의 `path.js`"를 찾고, `./`가 없으면 "내장 모듈 또는 `node_modules`"를 찾는다. 이 차이를 3단계에서 배웠다.

실무에서 `path.join`을 가장 많이 쓴다. `'a' + '/' + 'b'`처럼 문자열로 경로를 만들면 Windows에서는 `\`가 필요해서 깨진다. `path.join('a', 'b')`는 OS에 맞게 자동으로 처리한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `Cannot find module './path'` | 내장 모듈에 `./`를 붙임 | `require('path')` |
| `ENOENT: no such file or directory` | `fs.readFileSync`의 파일 경로 오타 | `path.join(__dirname, '파일명')`으로 절대경로 사용 |

**📝 이 단계의 핵심**

- 내장 모듈: `require('이름')` — `./` 없이
- `path` — 파일 경로 조작(OS별 호환)
- `fs` — 파일 읽기/쓰기
- `os` — 시스템 정보

## 16. CommonJS의 한계와 ES Module 예고

CommonJS는 Node.js에서 잘 동작하지만, 브라우저에서는 안 되고, 동적 import도 못 한다. ES2015부터 표준화된 ES Module(`import`/`export`)이 이 문제를 해결한다.

### 16-1. CommonJS의 한계

| 한계 | 설명 |
|---|---|
| 브라우저에서 안 됨 | `require`/`exports`는 Node.js 전용. 브라우저에서는 ES Module 사용 |
| 동적 import 불가 | `import()`처럼 런타임에 모듈을 동적으로 불러올 수 없음 |
| tree-shaking 불가 | 빌드 도구가 "어떤 export가 실제로 쓰이는지"를 정적 분석으로 알 수 없음 |

### 16-2. ES Module 문법 예고

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
| 동기/비동기 | 동기 | 비동기(브라우저) |
| 사용 환경 | Node.js | Node.js + 브라우저 |
| 파일 확장자 | `.js`(기본) | `.js`(`"type": "module"`) 또는 `.mjs` |

**✅ 확인**

- CommonJS의 한계를 이해했다.
- ES Module의 기본 문법을 미리 확인했다.

**🎓 newlec 쌤의 코멘트**

CommonJS는 2009년에 나왔고, ES Module은 2015년에 표준화되었다. 6년 차이가 있지만, Node.js는 이미 CommonJS 생태계가 너무 커서 쉽게 전환하지 못했다.

지금은 Node.js에서 둘 다 쓸 수 있다. `package.json`에 `"type": "module"`을 추가하면 ES Module로, 없으면 CommonJS로 동작한다.

이 튜토리얼에서 CommonJS를 먼저 배운 이유는, 실무에서 아직 CommonJS를 쓰는 프로젝트가 많기 때문이다. ES Module은 [[025_ES Module 실습]]에서 자세히 다룬다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `require is not defined in ES module scope` | `package.json`에 `"type": "module"`이 있는데 `require` 사용 | `import`로 전환 또는 `"type": "commonjs"`로 변경 |
| `Unexpected token 'export'` | CommonJS 파일에서 `export` 사용 | `module.exports`로 전환 또는 `"type": "module"` 추가 |

**📝 이 단계의 핵심**

- CommonJS: Node.js 전용, 동기, tree-shaking 불가
- ES Module: 표준, 브라우저+Node.js, 비동기, tree-shaking 가능
- `package.json`의 `"type"` 필드로 모드 전환

### 16-3. 최종 확인

VSCode 터미널에서 실행한다.

```
ls
```

```
node-prj/
├── app.js              ← require로 math.js를 불러와 실행
├── math.js             ← CommonJS 모듈 (exports로 add, sub 내보내기)
├── package.json
├── package-lock.json
└── node_modules/
```

최종 실행:

```
node app.js
```

`math.js`의 `add`, `sub`가 정상 동작하면 성공이다.

**여기까지의 정리**

1단계 — JS는 원래 모듈 시스템이 없었다. `<script>` 태그 + 전역 스코프 공유 → 이름 충돌 → 고립화 필요
2단계 — CommonJS의 `exports`/`module.exports`로 "이 파일에서 뭘 공개할지" 결정
3단계 — `require('./파일명')`로 모듈을 불러온다. 구조 분해, 캐싱 포함
4단계 — `path`, `fs`, `os` 등 내장 모듈은 `require('이름')`으로 바로 사용
5단계 — CommonJS의 한계(브라우저 불가, 동적 import 불가)

같은 `math.js`·`app.js`를 실제로 ES Module 문법으로 바꿔보는 실습은 [[025_ES Module 실습]]에서 이어간다.
