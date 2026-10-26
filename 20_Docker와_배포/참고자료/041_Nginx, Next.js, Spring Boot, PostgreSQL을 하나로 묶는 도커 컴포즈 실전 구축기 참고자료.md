---
tags: [Docker, DockerCompose, Nginx, 리버스프록시, Nextjs, 스프링부트, PostgreSQL, healthcheck, override, HTTPS, Certbot, 참고자료]
---

> 🔗 관련 노트: [[038_도커 컴포즈로 스프링 부트와 PostgreSQL 한 번에 구동하기 참고자료]] · [[097_Docker Compose — 여러 컨테이너를 하나의 네트워크로 묶어 실행하기]] · [[037_Java 21 스프링 부트 앱을 도커 이미지로 배포하기 참고자료]]

# Nginx, Next.js, Spring Boot, PostgreSQL을 하나로 묶는 도커 컴포즈 실전 구축기

## 0. 프로젝트 소개 (ncafe 서비스 구조 및 최종 아키텍처)

단순히 백엔드와 데이터베이스 둘만 띄우는 단계를 넘어, 실제 서비스 환경처럼 프론트엔드와 웹 서버(리버스 프록시)까지 포함된 전체 시스템을 구축할 때가 되었다. 실습 프로젝트인 ncafe는 사용자 화면을 담당하는 **Next.js**, 비즈니스 로직을 처리하는 **Spring Boot**, 데이터를 저장하는 **PostgreSQL**, 그리고 모든 요청의 길잡이 역할을 하는 **Nginx** 웹 서버로 구성된다.

```
                 [브라우저 / 외부 요청]
                          │
                          │ Port 80 / 443
                          ▼
                 [Nginx (웹 서버 / 리버스 프록시)]
                  │                         │
           /api/* │                         │ /* (화면 요청)
                  ▼                         ▼
      [Spring Boot (백엔드)]        [Next.js (프론트엔드)]
                  │
                  │ DB 접속
                  ▼
          [PostgreSQL (DB)]
```

최종 아키텍처의 핵심은 외부에서 들려오는 모든 요청을 Nginx가 혼자서 먼저 받고, 요청 종류에 따라 화면(Next.js)이나 API(Spring Boot)로 전달하는 구조이다. 이제 이 시스템을 기초부터 시작해 실제 운영 환경 수준까지 단계별로 고쳐 나가본다.

이번 실습을 위해 첨부된 풀스택 프로젝트를 다운로드받아 사용한다. 백엔드 프로젝트는 JDK 25를 기반으로 동작하므로 해당 버전이 설치되어 있지 않다면 추가로 설치해야 한다. 기존 개발 환경에는 영향을 주지 않으므로 안심하고 진행해도 된다.

> **추가 설명 — 폴더 구조**: 이 자료의 경로(`./backend`, `./frontend`, `./nginx/default.conf`)는 아래 구조를 전제로 한다. 컴포즈 파일과 `.env`는 맨 위 폴더에 둔다.
>
> ```
> ncafe/
> ├─ .env
> ├─ docker-compose.yml
> ├─ docker-compose.override.yml   ← 개발용 (3절)
> ├─ docker-compose.prod.yml       ← 운영용 (3절)
> ├─ backend/                      ← Spring Boot 프로젝트 + Dockerfile
> ├─ frontend/                     ← Next.js 프로젝트 + Dockerfile
> └─ nginx/
>    ├─ default.conf
>    └─ certs/                     ← 4절에서 만드는 인증서
> ```

## 1. 일단 세 개만 띄워 보자 (기본 서비스 연동과 DB 헬스체크, 환경변수 분리)

Nginx를 붙이기 전에 핵심 서비스 세 개(Next.js, Spring Boot, PostgreSQL)를 먼저 연결한다. 서비스에 필요한 중요 정보나 비밀번호는 `docker-compose.yml`에 그대로 적으면 보안에 위험하므로 `.env` 파일로 따로 빼서 관리한다.

**환경 변수 파일 (.env)**

```bash
COMPOSE_PROJECT_NAME=ncafe
POSTGRES_DB=ncafedb
POSTGRES_USER=ncafeuser
POSTGRES_PASSWORD=ncafepassword123
```

> **추가 설명 — `.env`는 Git에 올리지 않는다**: 비밀번호를 뺀 이유가 저장소에 남기지 않기 위해서이므로 `.gitignore`에 `.env`를 넣는다. 팀원에게는 값을 비운 `.env.example`을 올려 어떤 변수가 필요한지 알려 준다. `.env`의 값은 **컴포즈가 yml을 읽을 때** `${POSTGRES_DB}` 자리에 끼워 넣는 용도이고, 컨테이너에 자동으로 전달되는 것은 아니다. 컨테이너에 넘기려면 아래처럼 `environment`에 다시 적어야 한다.

**초기 설정 (docker-compose.yml)**

```yaml
services:
  postgres-db:
    image: postgres:17
    container_name: ncafe-db
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend-app:
    build: ./backend
    container_name: ncafe-backend
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres-db:5432/${POSTGRES_DB}
      SPRING_DATASOURCE_USERNAME: ${POSTGRES_USER}
      SPRING_DATASOURCE_PASSWORD: ${POSTGRES_PASSWORD}
    depends_on:
      postgres-db:
        condition: service_healthy

  frontend-app:
    build: ./frontend
    container_name: ncafe-frontend
    ports:
      - "3000:3000"

volumes:
  postgres_data:
```

> **추가 설명 — 이 단계에서 백엔드는 밖에서 안 보인다**: `backend-app`에는 `ports`가 없으므로 브라우저에서 `localhost:8080`으로는 접속할 수 없다. 이 단계에서 브라우저가 열 수 있는 것은 `localhost:3000`(Next.js)뿐이다. Next.js **서버 쪽 코드**(서버 컴포넌트, SSR)는 내부 네트워크로 `http://backend-app:8080`에 닿지만, **브라우저에서 도는 코드**는 `backend-app`이라는 이름을 모르므로 백엔드를 부를 길이 없다. 이 문제를 2절의 Nginx가 해결한다.

### 데이터베이스 헬스체크(healthcheck)가 필요한 이유

스프링 부트에 `depends_on: - postgres-db`만 설정하면 데이터베이스 컨테이너가 '켜지기 시작할 때' 스프링 부트가 바로 실행되어 버린다. 하지만 데이터베이스는 상자가 켜진 뒤 내부 엔진이 완전히 준비될 때까지 수 초의 시간이 걸린다. 준비가 안 된 DB에 스프링 부트가 접속을 시도하면 연결 오류가 발생하며 서버가 뻗는다.

이 문제를 막기 위해 `healthcheck` 속성을 사용한다. `pg_isready` 명령어로 DB가 진짜 요청을 받을 준비가 되었는지 주기적으로 확인하고, 완전히 준비되었을 때(`condition: service_healthy`) 비로소 백엔드 앱을 띄우도록 차례를 정해준다.

> **추가 설명 — 헬스체크 항목 읽는 법**:
>
> | 항목 | 뜻 |
> |---|---|
> | `test` | 상태 확인 명령. 종료 코드가 0이면 정상 |
> | `interval: 5s` | 5초마다 검사 |
> | `timeout: 5s` | 한 번 검사가 5초 안에 끝나지 않으면 실패로 침 |
> | `retries: 5` | 연속 5번 실패하면 `unhealthy`로 표시 |
> | `start_period` (선택) | 처음 이 시간 동안의 실패는 횟수에 안 셈. 초기화가 긴 DB에 쓴다 |
>
> `docker compose ps`의 STATUS에 `Up (healthy)`, `Up (health: starting)`, `Up (unhealthy)`로 보인다. DB가 끝내 `unhealthy`면 백엔드는 시작되지 않고 `dependency failed to start` 오류로 멈춘다.

> **추가 설명 — `${POSTGRES_USER}`가 언제 바뀌나**: `test` 안의 `${POSTGRES_USER}`는 컴포즈가 yml을 읽을 때 `.env` 값으로 바꿔 넣는다. 컨테이너 안의 환경 변수를 그대로 쓰고 싶다면 `$$POSTGRES_USER`처럼 `$`를 두 번 쓴다(컴포즈가 치환하지 않고 `$`로 남겨 둠).

## 2. 문을 하나로: 리버스 프록시 Nginx

프론트엔드와 백엔드를 따로 띄우면 브라우저에서 백엔드로 API 요청을 보낼 때 **CORS(교차 출처 리소스 공유)** 문제가 발생한다. 웹 브라우저가 보안상의 이유로 주소가 다른 곳으로의 데이터 요청을 막기 때문이다.

이 문제를 해결하기 위해 맨 앞에 Nginx(리버스 프록시)를 문지기로 세운다. 브라우저는 오직 Nginx의 주소로만 통신하고, Nginx가 내부 네트워크에서 알아서 프론트엔드와 백엔드로 요청을 나눠서 전달하도록 만든다. 이렇게 하면 브라우저 입장에서는 하나의 입구만 바라보므로 CORS 문제가 자연스럽게 사라진다.

> **추가 설명 — "출처가 같다"의 기준**: 출처(origin)는 **프로토콜 + 호스트 + 포트** 세 가지가 모두 같아야 같은 출처다. `http://localhost:3000`(화면)과 `http://localhost:8080`(API)은 포트가 달라 다른 출처다. Nginx 뒤로 숨기면 둘 다 `http://localhost`(80)로 보이므로 같은 출처가 된다. 정확히는 브라우저가 요청 자체를 막는다기보다, 서버가 허용 헤더(`Access-Control-Allow-Origin`)를 주지 않으면 **응답을 자바스크립트에 넘겨주지 않는** 것이다.

**Nginx 설정 파일 (nginx/default.conf)**

```nginx
server {
    listen 80;
    server_name localhost;

    # 동적 IP 해소를 위한 도커 내부 DNS 지정
    resolver 127.0.0.11 valid=30s;

    # /api/ 로 시작하는 요청은 스프링 부트로 전달
    location /api/ {
        set $backend_upstream http://backend-app:8080;
        proxy_pass $backend_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 나머지 모든 요청은 Next.js 프론트엔드로 전달
    location / {
        set $frontend_upstream http://frontend-app:3000;
        proxy_pass $frontend_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

> **추가 설명 — `/api/`는 떼지 않고 그대로 넘어간다**: 위처럼 변수에 주소만 담아 `proxy_pass $backend_upstream;`으로 넘기면, 브라우저가 요청한 경로가 **그대로** 백엔드에 전달된다. `/api/menus` 요청은 스프링에도 `/api/menus`로 들어간다. 그래서 스프링 컨트롤러가 `@RequestMapping("/api/menus")`처럼 `/api`를 포함하고 있어야 한다. 컨트롤러가 `/menus`로만 되어 있다면 `/api` 접두사를 떼는 설정이 따로 필요하다.
>
> ```nginx
> location /api/ {
>     rewrite ^/api/(.*)$ /$1 break;   # /api/menus → /menus
>     proxy_pass $backend_upstream;
> }
> ```

> **추가 설명 — 프록시 서비스를 컴포즈에 추가하기**: 위 설정을 쓰려면 Nginx 컨테이너를 서비스로 넣고, 외부 포트는 **Nginx에만** 연다. 1절에서 열어 둔 `frontend-app`의 `"3000:3000"`도 이제는 빼도 된다.
>
> ```yaml
>   proxy:
>     image: nginx:1.27
>     container_name: ncafe-proxy
>     ports:
>       - "80:80"
>     volumes:
>       - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
>     depends_on:
>       - backend-app
>       - frontend-app
> ```
>
> `:ro`는 읽기 전용(read-only)으로 연결한다는 뜻이다. 설정 파일을 고친 뒤에는 `docker compose exec proxy nginx -s reload`로 Nginx를 다시 읽게 하고, 그 전에 `docker compose exec proxy nginx -t`로 문법을 검사할 수 있다.

### 도커 내부 DNS(resolver 127.0.0.11)와 변수 설정

Nginx는 기본적으로 실행될 때 접속할 서비스들의 IP를 미리 찾아서 기억해 둔다. 하지만 도커 컴포즈 환경에서는 컨테이너가 재부팅될 때마다 내부 IP 주소가 계속 변한다. Nginx가 옛날 IP를 기억하고 있으면 접속 에러가 발생한다.

이 문제를 막기 위해 Nginx 설정 안에 `resolver 127.0.0.11 valid=30s;`를 적어준다. `127.0.0.11`은 도커 엔진이 제공하는 내부 DNS 서버 주소이다. 그리고 `proxy_pass`에 `http://backend-app:8080`을 직접 적지 않고 `$backend_upstream` 변수로 만들어 전달하면, Nginx는 요청이 들어올 때마다 변하는 컨테이너의 최신 IP를 도커 DNS에 물어보고 정확하게 찾아간다.

> **추가 설명 — 변수를 쓰면 생기는 또 하나의 이점**: `proxy_pass http://backend-app:8080;`처럼 주소를 직접 적으면 Nginx는 **시작할 때** 이 이름을 찾는다. 그 순간 백엔드 컨테이너가 아직 없거나 죽어 있으면 `host not found in upstream "backend-app"` 오류를 내고 **Nginx 자체가 켜지지 않는다.** 변수로 넘기면 이름 찾기가 요청이 들어오는 시점으로 미뤄지므로, 백엔드가 늦게 떠도 Nginx는 먼저 켜지고 백엔드가 준비된 뒤부터 정상 응답한다(그 전에는 502).
>
> | 적는 방식 | 이름을 찾는 시점 | 백엔드가 없을 때 |
> |---|---|---|
> | `proxy_pass http://backend-app:8080;` | Nginx 시작할 때 한 번 | Nginx가 아예 안 켜짐 |
> | `set $u http://backend-app:8080;` + `proxy_pass $u;` + `resolver` | 요청마다(`valid=30s` 동안 기억) | Nginx는 켜지고 해당 요청만 502 |
>
> 변수를 쓰면 **반드시 `resolver`가 있어야 한다.** 없으면 `no resolver defined to resolve backend-app` 오류가 난다.

또한 `X-Real-IP`나 `X-Forwarded-For` 헤더를 붙여주어야 전달받은 스프링 부트나 Next.js가 실제 접속한 사용자의 진짜 IP 주소를 식별할 수 있다.

> **추가 설명 — 스프링 쪽도 설정해야 헤더를 믿는다**: 헤더를 보내기만 하면 스프링은 기본적으로 이것을 무시하고, 요청 보낸 쪽을 **Nginx 컨테이너**로 본다. 특히 4절에서 HTTPS를 붙이면 Nginx→스프링 구간은 http이므로, 스프링이 로그인 후 리다이렉트 주소를 `http://`로 만들어 버리는 문제가 생긴다. 아래 설정을 켜면 `X-Forwarded-*` 헤더를 읽어 원래 IP와 프로토콜을 복원한다.
>
> ```yaml
> # backend application.yml
> server:
>   forward-headers-strategy: framework
> ```

## 3. 개발과 운영은 다르다: 오버라이드 (override/prod 분리)

내 컴퓨터에서 개발할 때 사용하는 설정과 실제 서버에서 운영할 때 사용하는 설정은 달라야 한다. 개발할 때는 코드를 수정하면 바로 반영되는 소스 코드 연결(바인드 마운트)이 필요하지만, 실제 서버에서는 완성된 이미지만 깔끔하게 실행되어야 한다.

도커 컴포즈는 파일 분리 기능을 제공하여 이를 깔끔하게 해결한다.

### 기본 설정 (docker-compose.yml)

공통적으로 사용되는 기본 구조만 담아둔다.

```yaml
services:
  postgres-db:
    image: postgres:17
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend-app:
    build: ./backend
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres-db:5432/${POSTGRES_DB}

  frontend-app:
    build: ./frontend

  proxy:
    image: nginx:1.27
    ports:
      - "80:80"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro

volumes:
  postgres_data:
```

> 원문 바로잡기 — 이 파일은 구조를 보여 주려고 줄인 것이라, 그대로 쓰면 1절에서 만든 것이 빠져 동작하지 않는다. 기본 파일에는 **1절의 내용을 그대로 유지**하고 Nginx만 더하는 것이 맞다.
>
> | 빠진 것 | 결과 |
> |---|---|
> | `SPRING_DATASOURCE_USERNAME`, `SPRING_DATASOURCE_PASSWORD` | `application.yml`의 값과 다르면 DB 접속 실패(`password authentication failed`) |
> | DB의 `healthcheck`, 백엔드의 `depends_on: condition: service_healthy` | 1절에서 해결한 "DB 준비 전 접속" 문제가 다시 생김 |
> | `proxy`의 `depends_on` | 시작 순서가 정해지지 않음 (변수 방식이면 치명적이진 않음) |

### 개발 전용 설정 (docker-compose.override.yml)

도커 컴포즈는 별도 옵션 없이 `docker compose up`을 실행하면 `docker-compose.yml`과 `docker-compose.override.yml`을 자동으로 합쳐서 실행한다.

```yaml
services:
  backend-app:
    volumes:
      - ./backend:/app
    environment:
      SPRING_PROFILES_ACTIVE: dev

  frontend-app:
    volumes:
      - ./frontend:/app
      - /app/node_modules # 호스트의 node_modules와 덮어씌워지는 것을 방지

  proxy:
    ports:
      - "3000:3000" # 개발 편의를 위한 프론트엔드 직접 접근 포트 열기
```

> 원문 바로잡기 — 이 파일에는 그대로 쓰면 문제가 되는 곳이 세 군데 있다.
>
> **① `proxy`에 `"3000:3000"`을 열면 프론트엔드로 가지 않는다.** `ports`는 **그 서비스의 컨테이너** 포트를 여는 것이다. `proxy`에 적으면 호스트 3000 → **Nginx 컨테이너**의 3000으로 연결되는데, Nginx는 80만 듣고 있으므로 접속이 안 된다. 프론트엔드에 직접 들어가려면 `frontend-app`에 적어야 한다.
>
> ```yaml
>   frontend-app:
>     ports:
>       - "3000:3000"
> ```
>
> **② 바인드 마운트만으로는 코드 수정이 반영되지 않는다.** 각 Dockerfile은 보통 운영용으로 짜여 있다. 백엔드는 빌드한 JAR를 `java -jar`로, 프론트엔드는 빌드한 결과를 `next start`로 실행한다. 소스 폴더를 연결해도 실행 중인 것은 **이미 빌드된 결과물**이라 수정이 화면에 나오지 않는다. 즉시 반영되게 하려면 실행 명령을 **개발 서버**로 바꿔야 한다.
>
> **③ `/app`을 통째로 덮으면 이미지 안의 결과물이 가려진다.** `./backend:/app`을 연결하면 컨테이너의 `/app` 폴더가 내 소스 폴더로 **덮여서**, 이미지가 `/app/app.jar`에 넣어 둔 JAR가 보이지 않게 된다. 그러면 `Unable to access jarfile app.jar`로 컨테이너가 바로 죽는다. 프론트엔드도 이미지 안에서 빌드한 `.next` 폴더가 가려진다.
>
> 그래서 개발용 오버라이드는 보통 아래처럼 **개발 서버 명령**과 함께 쓴다. 프론트엔드는 개발 서버(`next dev`)가 파일 변경을 감지해 바로 다시 그려 준다. 백엔드는 자바 특성상 즉시 반영이 번거로워서, 개발 중에는 DB만 컨테이너로 띄우고 스프링은 IDE에서 실행하는 경우가 더 많다.
>
> ```yaml
>   frontend-app:
>     build:
>       context: ./frontend
>       target: deps            # (멀티 스테이지라면) 의존성 설치까지만 된 단계 사용
>     command: npm run dev      # next dev
>     ports:
>       - "3000:3000"
>     volumes:
>       - ./frontend:/app
>       - /app/node_modules
>     environment:
>       WATCHPACK_POLLING: "true"   # 윈도우·WSL 바인드 마운트에서 파일 변경 감지가 안 될 때
> ```

> **추가 설명 — `/app/node_modules` 한 줄의 정체**: 경로만 있고 앞에 `호스트경로:`가 없는 것은 **이름 없는 볼륨**(anonymous volume)이다. `./frontend:/app`으로 폴더를 통째로 덮으면 이미지 안에서 `npm install`로 만든 `node_modules`도 내 PC의 폴더(비어 있거나 윈도우용 패키지가 깔린)로 가려진다. 그 하위 경로에 별도 볼륨을 하나 더 걸어 두면, 그 자리만 이미지의 `node_modules`가 그대로 보인다.
>
> ```
> /app                ← 내 PC의 ./frontend (바인드 마운트)
> /app/node_modules   ← 이미지 안의 node_modules (이름 없는 볼륨이 보존)
> ```

### 운영 전용 설정 (docker-compose.prod.yml)

운영 환경에서는 오버라이드 파일 대신 이 파일을 덮어씌워서 실행한다.

```yaml
services:
  backend-app:
    restart: always
    environment:
      SPRING_PROFILES_ACTIVE: prod

  frontend-app:
    restart: always

  proxy:
    restart: always
```

운영 환경에서 실행할 때는 `-f` 옵션으로 사용할 파일들을 직접 지정한다.

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

> **추가 설명 — `-f`를 쓰면 override 파일은 자동으로 안 읽힌다**: `-f`로 파일을 하나라도 지정하면 컴포즈는 `docker-compose.override.yml`을 자동으로 합치지 않는다. 그래서 운영 서버에 override 파일이 같이 올라가 있어도 위 명령에는 섞이지 않는다.

> **추가 설명 — 파일을 합치는 규칙**: 뒤에 오는 파일이 앞 파일을 덮어쓰지만, 항목마다 방식이 다르다.
>
> | 항목 | 합치는 방식 |
> |---|---|
> | `image`, `command`, `restart` 같은 단일 값 | 뒤 파일 값으로 **교체** |
> | `environment` | 같은 키는 교체, 다른 키는 **추가** |
> | `ports`, `volumes` 같은 목록 | 앞 파일 목록에 **추가** (뺄 수 없음) |
>
> 목록은 뒤 파일에서 **빼는 것이 안 된다**는 점이 중요하다. 그래서 개발에서만 열 포트는 기본 파일이 아니라 override에 넣어야, 운영에서 저절로 빠진다. 최종적으로 어떻게 합쳐졌는지는 `docker compose -f docker-compose.yml -f docker-compose.prod.yml config`로 확인할 수 있다.

> **추가 설명 — `restart` 정책**: 운영에서는 DB에도 붙이는 것이 보통이다(원문에는 `postgres-db`가 빠져 있다).
>
> | 값 | 동작 |
> |---|---|
> | `no` (기본) | 죽어도 다시 켜지 않음 |
> | `always` | 항상 다시 켬. 서버 재부팅 후 도커가 켜지면 같이 켜짐 |
> | `unless-stopped` | `always`와 같지만, 사람이 직접 `stop`한 것은 재부팅 후에도 켜지 않음 |
> | `on-failure` | 오류로 종료됐을 때만 다시 켬 |

## 4. 로컬에서도 HTTPS (사설 CA 생성 및 로컬 SSL 환경)

결제 연동이나 쿠키 처리, 웹소켓 등을 테스트할 때 로컬 개발 환경에서도 `https://` 접속 환경이 필요한 경우가 발생한다. OpenSSL 명령어로 발급한 가짜 인증서를 Nginx에 등록하여 로컬 HTTPS 환경을 만든다.

**1단계: 인증서 생성 스크립트 실행**

```bash
# 가짜 인증서와 비밀키 생성
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./nginx/certs/localhost.key \
  -out ./nginx/certs/localhost.crt \
  -subj "/CN=localhost"
```

> 원문 바로잡기 — 위 명령은 **사설 CA**를 만드는 것이 아니라, 스스로 서명한 **자체 서명 인증서**(self-signed) 한 장을 만드는 것이다. 그래서 브라우저는 "연결이 비공개로 설정되어 있지 않습니다"(`NET::ERR_CERT_AUTHORITY_INVALID`) 경고를 띄우고, "고급 → 계속"을 눌러야 들어갈 수 있다. 또 최신 Chrome은 `CN`이 아니라 **SAN**(Subject Alternative Name) 항목만 보고 도메인을 확인하므로, `-subj "/CN=localhost"`만으로는 인증서를 신뢰 목록에 넣어도 `ERR_CERT_COMMON_NAME_INVALID`가 난다. 아래처럼 고친다.
>
> ```bash
> mkdir -p ./nginx/certs          # 폴더가 없으면 openssl이 파일을 못 만든다
> openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
>   -keyout ./nginx/certs/localhost.key \
>   -out ./nginx/certs/localhost.crt \
>   -subj "/CN=localhost" \
>   -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
> ```
>
> 윈도우의 **Git Bash**에서 실행하면 `"/CN=localhost"`가 윈도우 경로(`C:/Program Files/Git/CN=localhost`)로 바뀌어 오류가 난다. `"//CN=localhost"`로 쓰거나 명령 앞에 `MSYS_NO_PATHCONV=1`을 붙인다. WSL 터미널에서는 그대로 된다.

> **추가 설명 — 경고 없는 로컬 HTTPS는 `mkcert`**: 제목대로 **사설 CA**를 만들어 내 PC가 믿게 하려면 `mkcert`를 쓰는 것이 가장 간단하다. 내 PC 전용 CA를 만들어 운영체제·브라우저 신뢰 목록에 등록하고, 그 CA로 서명한 인증서를 발급해 주므로 주소창에 경고 없이 자물쇠가 뜬다.
>
> ```bash
> mkcert -install                                   # 내 PC 전용 CA 생성 + 신뢰 등록 (한 번만)
> mkcert -key-file ./nginx/certs/localhost.key \
>        -cert-file ./nginx/certs/localhost.crt localhost 127.0.0.1
> ```
>
> 인증서 파일과 특히 `.key`는 Git에 올리지 않는다(`nginx/certs/`를 `.gitignore`에 추가).

**2단계: Nginx SSL 설정 추가 (nginx/default.conf)**

```nginx
server {
    listen 80;
    server_name localhost;
    # 모든 HTTP 요청을 HTTPS로 자동 전달
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name localhost;

    ssl_certificate /etc/nginx/certs/localhost.crt;
    ssl_certificate_key /etc/nginx/certs/localhost.key;

    resolver 127.0.0.11 valid=30s;

    location /api/ {
        set $backend_upstream http://backend-app:8080;
        proxy_pass $backend_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }

    location / {
        set $frontend_upstream http://frontend-app:3000;
        proxy_pass $frontend_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

> **추가 설명 — HTTPS는 Nginx에서 끝난다**: 브라우저↔Nginx 구간만 암호화되고, Nginx↔백엔드·프론트엔드 구간은 내부 네트워크라 그대로 http다. 이것을 **SSL 종료**(SSL termination)라고 한다. 인증서를 Nginx 한 곳에만 두면 되므로 스프링·Next.js는 HTTPS를 몰라도 된다. 대신 스프링이 "원래 요청이 https였다"는 것을 알 수 있도록 `X-Forwarded-Proto https`를 넘기고, 2절의 `forward-headers-strategy` 설정을 켠다. 1단계 설정에 있던 `X-Real-IP`, `X-Forwarded-For`도 이 블록에 같이 넣어 두는 것이 좋다.

**3단계: 도커 컴포즈 파일에 인증서 폴더 마운트**

```yaml
  proxy:
    image: nginx:1.27
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
```

## 5. 운영 서버: 호스트 Nginx + Certbot 과 자원 제한

실제 운영 서버에서는 컨테이너 내부의 Nginx 대신, 서버 호스트 본체에 Nginx와 Certbot을 직접 설치하여 무료 공인 SSL 인증서(Let's Encrypt)를 자동으로 발급받고 갱신하는 방식을 자주 사용한다.

또한 여러 팀이나 프로젝트가 서버 하나를 같이 쓸 때는 무분별한 자원 사용을 막기 위한 한계치 설정과 로그 크기 제한이 필수적이다.

> **추가 설명 — 왜 호스트에 Nginx를 두나**: 서버 한 대에 여러 프로젝트가 올라가면 80·443 포트는 서버에 하나뿐이라 **한 프로젝트의 컨테이너 Nginx가 독차지할 수 없다.** 그래서 호스트에 Nginx를 하나 두고, 도메인별로 각 프로젝트의 포트로 나눠 보낸다. Certbot도 호스트 Nginx 설정을 직접 고쳐 주는 기능(`--nginx`)이 있어 이 구조와 잘 맞는다.
>
> ```
> 인터넷 ─:443─▶ [호스트 Nginx + Let's Encrypt 인증서]
>                    ├─ ncafe.example.com     /api/ ─▶ 127.0.0.1:8080 (ncafe 백엔드 컨테이너)
>                    │                        /     ─▶ 127.0.0.1:3000 (ncafe 프론트 컨테이너)
>                    └─ teamb.example.com           ─▶ 127.0.0.1:3100 (다른 팀 컨테이너)
> ```
>
> 이 구조에서는 컴포즈의 `proxy` 서비스를 **띄우지 않는다.** 기본 파일에 `proxy`가 `"80:80"`으로 남아 있으면 호스트 Nginx와 80번을 두고 충돌한다(`address already in use`). 운영용 실행에서 `proxy`를 빼려면 기본 파일에서 `proxy`를 override 쪽으로 옮기거나, `profiles: ["local-proxy"]`를 붙여 기본 실행에서 제외한다.

> **추가 설명 — Certbot 사용 흐름** (Ubuntu 기준, 도메인의 DNS가 이 서버 IP를 가리키고 있어야 한다):
>
> ```bash
> sudo apt install nginx certbot python3-certbot-nginx
> sudo certbot --nginx -d ncafe.example.com     # 인증서 발급 + Nginx에 443 설정 자동 추가
> sudo certbot renew --dry-run                  # 자동 갱신이 되는지 시험
> ```
>
> Let's Encrypt 인증서는 **90일**짜리지만, 설치할 때 함께 등록되는 타이머(systemd timer)가 만료 전에 자동으로 갱신한다.

### 호스트 Nginx 구조에서의 포트 흐름

호스트 Nginx가 80, 443 포트를 잡고 있다가 요청을 받으면, 도커 컴포즈가 포트 포워딩으로 열어둔 3000번(Next.js)이나 8080번(Spring Boot) 포트로 분기해준다.

```yaml
# 운영 서버용 docker-compose.prod.yml 일부
services:
  backend-app:
    ports:
      - "127.0.0.1:8080:8080" # 호스트 본체 내부에서만 접속 가능하도록 제한
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend-app:
    ports:
      - "127.0.0.1:3000:3000"
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

> **추가 설명 — 호스트 Nginx 설정 예시**: 컨테이너 Nginx와 달리 호스트 Nginx는 도커 DNS를 쓸 수 없으므로, 서비스 이름 대신 `127.0.0.1:포트`로 보낸다(위에서 `127.0.0.1`에 열어 둔 포트).
>
> ```nginx
> # /etc/nginx/sites-available/ncafe
> server {
>     server_name ncafe.example.com;
>
>     location /api/ {
>         proxy_pass http://127.0.0.1:8080;
>         proxy_set_header Host $host;
>         proxy_set_header X-Real-IP $remote_addr;
>         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
>         proxy_set_header X-Forwarded-Proto $scheme;
>     }
>
>     location / {
>         proxy_pass http://127.0.0.1:3000;
>         proxy_set_header Host $host;
>         proxy_set_header X-Forwarded-Proto $scheme;
>     }
>     # listen 443 ssl; 과 인증서 경로는 certbot --nginx 가 자동으로 추가한다
> }
> ```

### 다중 팀 공유 서버를 위한 안전 운영 규칙

- **포트 바인딩 제한 (`127.0.0.1:포트:포트`)**: 포트를 열 때 그냥 `"8080:8080"`으로 열면 외부 세상 모든 사람이 직접 백엔드 포트로 들어올 수 있게 된다. 앞에 `127.0.0.1:`을 붙여주면 서버 본체 안의 호스트 Nginx를 통해서만 접속할 수 있어 안전하다.
- **자원 한계치 설정 (`deploy.resources.limits`)**: 특정 서비스에 메모리 누수가 발생해 서버 전체가 멈추는 불상사를 막기 위해 사용할 수 있는 최대 CPU와 메모리 크기를 강제로 제한한다.
- **로그 용량 제한 (`logging`)**: 도커 컨테이너가 내뱉는 로그 파일이 무한정 쌓이다가 서버 용량이 꽉 차서 터지는 사고를 막는다. 파일당 최대 10MB, 최대 3개까지만 보관하도록 설정한다.

> **추가 설명 — 방화벽(ufw)이 있어도 `127.0.0.1`이 필요하다**: 도커는 포트를 열 때 리눅스 방화벽 규칙(iptables)을 **직접** 추가하기 때문에, `ufw`로 8080을 막아 두어도 `"8080:8080"`으로 연 포트는 외부에서 그대로 들어온다. 그래서 방화벽에 기대지 말고 컴포즈에서 `127.0.0.1:`로 묶는 것이 확실하다.

> **추가 설명 — 메모리를 제한하면 넘쳤을 때 강제 종료된다**: 컨테이너가 `memory: 1G`를 넘으면 리눅스가 프로세스를 강제로 끝낸다(OOM Kill, `docker inspect`에 `OOMKilled: true`). `restart` 정책이 있으면 다시 켜지지만 그 사이 요청은 실패한다. 자바는 최근 버전부터 컨테이너 제한을 인식해 힙을 기본 **제한의 25%**만 잡으므로, 1G 제한이면 힙이 256MB 정도다. 힙을 더 쓰게 하려면 비율을 지정한다.
>
> ```yaml
>   backend-app:
>     environment:
>       JAVA_TOOL_OPTIONS: "-XX:MaxRAMPercentage=75.0"   # 1G 중 약 750MB를 힙으로
> ```
>
> 실제 사용량은 `docker stats`로 실시간 확인한다.

> **추가 설명 — 로그 제한을 서버 전체 기본값으로**: 서비스마다 `logging`을 적는 대신 도커 엔진 설정(`/etc/docker/daemon.json`)에 기본값을 두면, 이후 **새로 만드는** 모든 컨테이너에 적용된다(이미 있는 컨테이너는 다시 만들어야 적용).
>
> ```json
> {
>   "log-driver": "json-file",
>   "log-opts": { "max-size": "10m", "max-file": "3" }
> }
> ```

## 정리

### 자주 발생하는 트러블슈팅

| 문제 상황 | 원인 | 해결 방법 |
|---|---|---|
| 502 Bad Gateway | Nginx가 목적지 서비스(백엔드/프론트엔드)의 IP를 찾지 못함 | Nginx 설정에 `resolver 127.0.0.11 valid=30s;` 선언 및 `proxy_pass`에 변수 적용 |
| DB 연결 실패 (Connection Refused) | DB 상자는 켜졌으나 내부 엔진 준비가 완료되지 않음 | `docker-compose.yml`에 `healthcheck` 설정 후 `condition: service_healthy` 적용 |
| 소스 수정이 안 바뀜 | 로컬 개발 환경에서 오버라이드 파일이 안 들어감 | 파일명이 `docker-compose.override.yml`이 맞는지 확인하거나 `-f` 옵션 사용 |
| 로그 파일로 인한 용량 부족 | 도커 기본 로그 기록 장치가 무제한으로 쌓임 | 각 서비스 설정에 `logging` 용량 제한(`max-size`, `max-file`) 추가 |

> **추가 설명 — 표에 덧붙일 원인들**:
>
> | 문제 상황 | 더 흔한 원인 | 확인·해결 |
> |---|---|---|
> | 502 Bad Gateway | 백엔드가 **아직 기동 중**이거나 오류로 **죽어 있음**. 또는 포트 번호가 틀림 | `docker compose ps`로 상태, `docker compose logs backend-app`으로 오류 확인. 스프링은 뜨는 데 수십 초가 걸리므로 잠시 뒤 다시 시도 |
> | 소스 수정이 안 바뀜 | 컨테이너가 **개발 서버가 아니라 빌드 결과물**을 실행 중 (3절 바로잡기 ②) | 개발용 `command`(`npm run dev`)로 바꾸거나, 운영용 이미지라면 `docker compose up -d --build` |
> | 프론트 변경 감지가 안 됨 (윈도우) | 윈도우 폴더를 WSL2 도커에 연결하면 파일 변경 알림이 전달되지 않음 | `WATCHPACK_POLLING=true` 또는 프로젝트를 WSL 안(`~/`)에 두기 |
> | `port is already allocated` / `address already in use` | 호스트의 같은 포트를 다른 프로그램(호스트 Nginx, 로컬 PostgreSQL 등)이 사용 중 | 왼쪽(호스트) 포트 번호 변경, 또는 해당 서비스의 `ports` 제거 |
> | 로그인 후 `http://`로 튕김 | 스프링이 원래 요청이 https였다는 것을 모름 | `X-Forwarded-Proto` 헤더 + `server.forward-headers-strategy: framework` |

### 명령어 치트시트

```bash
# 개발 환경 실행 (docker-compose.override.yml 자동 포함)
docker compose up -d

# 개발 환경 재빌드 실행
docker compose up -d --build

# 운영 환경 실행
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 서비스 전체 로그 실시간 확인
docker compose logs -f

# 특정 서비스 실행 상태 및 포트 확인
docker compose ps
```

> **추가 설명 — 자주 같이 쓰는 명령**:
>
> ```bash
> # 합쳐진 최종 설정 확인 (override·prod가 어떻게 섞였는지)
> docker compose -f docker-compose.yml -f docker-compose.prod.yml config
>
> # Nginx 설정 문법 검사 후 다시 읽기 (컨테이너 재시작 없이)
> docker compose exec proxy nginx -t
> docker compose exec proxy nginx -s reload
>
> # 서비스 하나만 다시 빌드해서 교체
> docker compose up -d --build backend-app
>
> # 컨테이너별 CPU·메모리 사용량
> docker stats
> ```

### 실습 과제

1. 제공된 `docker-compose.yml` 설정을 바탕으로 로컬 컴퓨터에서 `docker compose up -d`를 실행한 후, `docker compose ps`를 입력해 4개의 컨테이너(Nginx, Next.js, Spring Boot, PostgreSQL)가 모두 정상 작동하는지 확인해 본다.
2. `docker-compose.override.yml`에 적힌 `frontend-app` 전용 볼륨 마운트 설정을 빼보고, 프론트엔드 소스 코드를 고쳤을 때 화면이 즉시 바뀌는지 안 바뀌는지 비교하며 오버라이드 파일의 편리함을 직접 체감해 본다.

> **추가 설명 — 과제 2를 할 때**: 3절 바로잡기 ②처럼, 프론트엔드 컨테이너가 `next start`(운영 모드)로 실행 중이라면 볼륨 마운트가 **있어도** 화면은 바뀌지 않는다. 비교가 제대로 되려면 override에서 `command: npm run dev`로 개발 서버를 띄운 상태여야 한다. 마운트가 있을 때는 저장 즉시 화면이 바뀌고, 마운트를 빼면 `docker compose up -d --build`로 이미지를 다시 만들어야만 바뀌는 것을 확인할 수 있다.
