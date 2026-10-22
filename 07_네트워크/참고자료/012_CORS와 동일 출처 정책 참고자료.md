---
tags: [웹, 네트워크, CORS, SOP, 참고자료]
---

> 🔗 관련 노트: [[CORS·동일 출처 정책 오답노트]]

# CORS와 동일 출처 정책 참고자료

[[CORS·동일 출처 정책 오답노트]]에서 다룬 SOP·CORS의 개념과 동작 원리를 더 자세히 정리한 참고자료.

## 1. 출처(Origin)란

출처는 URL에서 **프로토콜 + 호스트(도메인) + 포트**의 조합을 말한다. 셋 중 하나라도 다르면 교차 출처(Cross-Origin)다.

| 요청 주소 | 대상 주소 | 같은 출처? | 이유 |
|---|---|---|---|
| `http://localhost:3000` | `http://localhost:3000/api` | O | 세 요소 모두 동일 |
| `http://localhost:3000` | `https://localhost:3000` | X | 프로토콜이 다름 |
| `http://localhost:3000` | `http://api.example.com` | X | 도메인이 다름 |
| `http://localhost:3000` | `http://localhost:8000` | X | 포트가 다름 |

## 2. SOP(동일 출처 정책)가 존재하는 이유

브라우저는 기본적으로 **자신의 출처와 다른 서버로는 함부로 데이터를 주고받을 수 없다**는 SOP(Same-Origin Policy)를 따른다. 이 규칙이 없다면 다음과 같은 공격이 가능해진다.

1. 사용자가 악성 사이트(`evil.com`)에 접속한다.
2. 그 사이트의 스크립트가, 사용자가 이미 로그인해 브라우저에 남아 있는 쿠키·세션을 이용해 은행 서버(`bank.com/transfer`)로 몰래 송금 요청을 보낸다.
3. 브라우저가 이를 막지 않으면 사용자도 모르는 사이에 돈이 빠져나간다(CSRF류 공격).

SOP는 이런 무단 교차 출처 요청을 브라우저 차원에서 차단해 사용자를 보호한다.

## 3. CORS는 SOP의 예외 규칙

프론트엔드(`localhost:3000`)와 백엔드 API 서버(`localhost:8000` 등)를 분리해 개발하는 것이 현대 웹의 기본 구조이므로, "안전이 확인된 특정 출처에 한해 SOP를 풀어주는" 예외 규칙이 필요하다 — 이것이 **CORS(Cross-Origin Resource Sharing)**다.

### 3-1. 동작 순서

1. 브라우저가 요청을 보낼 때 `Origin` 헤더에 자신의 출처를 담는다.
   ```
   Origin: http://localhost:3000
   ```
2. 서버는 응답에 "이 출처는 허용한다"는 헤더를 담아 돌려준다.
   ```
   Access-Control-Allow-Origin: http://localhost:3000
   ```
3. 브라우저가 이 헤더를 확인한다 — 자신의 출처가 포함돼 있거나 `*`(전체 허용)이면 데이터를 그대로 넘겨주고, 없거나 다르면 콘솔에 CORS 에러를 띄우며 데이터를 버린다.

> 서버는 요청을 정상적으로 처리해 응답까지 보낸 상태다. **차단은 서버가 아니라 브라우저가 응답을 받은 뒤에** 수행한다.

### 3-2. 단순 요청과 프리플라이트(Preflight) 요청

모든 교차 출처 요청이 바로 서버로 전달되는 것은 아니다.

| 구분 | 조건(대표적) | 동작 |
|---|---|---|
| 단순 요청 | `GET`/`POST`/`HEAD`, 기본적인 헤더만 사용 | 바로 요청을 보내고, 응답 헤더로 허용 여부를 확인 |
| 프리플라이트 요청 | `PUT`/`DELETE` 등, `Content-Type: application/json` 등 커스텀 헤더 사용 | 본요청 전에 브라우저가 `OPTIONS` 메서드로 먼저 "이 요청을 보내도 되는지" 서버에 확인하고, 허용 응답을 받은 뒤에야 실제 요청을 보낸다 |

## 4. 개발 중 CORS 해결 방법

### 4-1. 서버에서 CORS 헤더 설정(정석)

```js
// Node.js(Express)
const cors = require('cors');
app.use(cors({ origin: 'http://localhost:3000' }));
```

```java
// Spring Boot
@CrossOrigin(origins = "http://localhost:3000")
@RestController
public class ApiController { /* ... */ }
```

### 4-2. 개발 서버 프록시로 우회

백엔드 코드를 당장 수정하기 어렵다면, 프론트엔드 개발 서버의 프록시 기능으로 브라우저가 같은 출처라고 착각하게 만들 수 있다.

```js
// vite.config.js 예시
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
});
```

이 원리는 Next.js에서 브라우저가 같은 출처의 Next.js 서버에만 요청하고, Next.js 서버가 서버 대 서버 통신으로 백엔드에 요청을 대신 전달하는 구조([[CORS·동일 출처 정책 오답노트]] 참고)와 동일하다.

## 5. 정리

- SOP/CORS를 검사하고 차단하는 주체는 **서버가 아니라 브라우저**다.
- 교차 출처 판정 기준은 **프로토콜 + 도메인 + 포트** 세 가지 전부다.
- `PUT`/`DELETE`나 커스텀 헤더를 쓰는 요청은 본요청 전에 `OPTIONS` 프리플라이트 요청이 먼저 나간다.
- 근본적인 해결은 서버가 `Access-Control-Allow-Origin`을 내려주는 것이고, 개발 단계에서는 프록시로 우회할 수 있다.
