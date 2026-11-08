---
tags: [Docker, DockerCompose, Redis, PostgreSQL, RefreshToken, StringRedisTemplate, Dockerfile, 실습]
---

> 🔗 관련 노트: [[056_메뉴 API — 목업을 걷어내고 스프링 MenuResponse를 Next.js BFF로 연결]] · [[053_Refresh Token으로 조용히 갱신하기 — 재발급 API, RefreshTokenStore, proxy 문지기]] · [[055_스프링 시큐리티의 401·403 응답을 JSON으로 통일하기 — ErrorResponse, EntryPoint, AccessDeniedHandler]] · [[049_멀티 컨테이너 풀스택 환경 구축과 운영 — Docker Compose 완성하기]]

# 도커 컴포즈 — 프론트·백엔드·PostgreSQL·Redis를 한 번에, 리프레시 토큰은 Redis로

> **첨부 파일 안내**
> - 이 내용은 `ncafe-lesson-08-auth-error-response` 프로젝트에 적용되어 있다. (401·403, 메뉴 BFF 이후 이어서)
>
> 참고 프로젝트 경로: `ncafe-lesson-08-auth-error-response`  
> 프로젝트 해설: `README-Docker-Compose.md`

---

이전 노트([[056_메뉴 API — 목업을 걷어내고 스프링 MenuResponse를 Next.js BFF로 연결]])에서 메뉴 목록이 스프링 → Next.js → 브라우저로 흐르게 되었다. 그런데 두 가지가 아직 서버 프로세스 안에 갇혀 있다.

1. 메뉴 13개가 `MenuRepository`의 `List.of(...)` 안에 있다.
2. 리프레시 토큰이 `RefreshTokenStore`의 `ConcurrentHashMap` 안에 있다.

둘째가 더 급하다. 직접 확인해 보자. 로그인해서 리프레시 토큰을 받아 둔 뒤 스프링을 재시작하고 그 토큰으로 재발급을 요청한다.

```bash
curl -i -X POST http://localhost:8080/api/auth/refresh \
  -H 'Content-Type: application/json' -d '{"refreshToken":"<재시작 전에 받은 토큰>"}'

HTTP/1.1 401
{"status":401,"error":"UNAUTHORIZED","message":"이미 만료 처리된 리프레시 토큰입니다.", ...}
```

토큰은 14일짜리인데 서버가 한 번 재시작됐다고 모든 사용자가 로그아웃된다. 배포할 때마다, 서버가 두 대가 되면 요청이 다른 서버로 갈 때마다 같은 일이 생긴다. 저장소가 서버 밖에 있어야 한다.

메뉴와 사용자는 PostgreSQL로, 리프레시 토큰은 Redis로 옮길 것이다. 그러면 실행해야 할 것이 스프링, Next.js, PostgreSQL, Redis 넷이 된다. 터미널 네 개를 열고 각자 설치한 DB의 버전과 포트와 비밀번호를 맞추는 일을 팀원 전원이 해야 한다면 시간이 환경 문제로 새어 나간다. 이번 노트는 이 전부를 `docker compose up` 한 줄로 띄우는 것이 목표다. 백엔드와 프론트엔드는 Dockerfile을 써서 이미지로 만들고, PostgreSQL과 Redis는 공개 이미지를 받아 쓴다. 그 위에서 Redis를 처음 사용해 리프레시 토큰 저장소를 옮긴다. PostgreSQL은 띄우고 접속만 확인하며, JPA 연결은 다음 노트에서 한다.

이번 노트에서는 다음 순서로 진행한다.

1. 도커와 도커 컴포즈가 무엇을 해 주는지 정리한다.
2. 백엔드 Dockerfile을 쓴다.
3. 프론트엔드 Dockerfile을 쓴다.
4. `compose.yaml`에 다섯 서비스를 적는다.
5. `compose.override.yaml`로 개발 모드(소스 마운트)를 만든다.
6. 올리고 명령어와 확인 방법을 익힌다.
7. Redis가 무엇이고 어떤 용도에 쓰는지 정리한다.
8. `redis-cli`로 직접 명령을 쳐 본다.
9. 스프링에서 Redis를 쓰도록 `RefreshTokenStore`를 바꾼다.
10. Redis가 꺼졌을 때의 응답을 정리한다.
11. 확인한다.

---

## 1. 도커와 도커 컴포즈

도커는 프로그램을 설치하지 않고 실행하는 도구다. PostgreSQL을 설치하는 대신 `postgres:17` 이미지를 받아 컨테이너로 띄우면, 어느 컴퓨터에서든 같은 버전, 같은 설정으로 돈다. 지우고 싶으면 컨테이너를 지우면 끝이고 시스템에는 흔적이 남지 않는다.

우리가 만든 스프링과 Next.js도 같은 방식으로 띄울 수 있다. 다만 공개 이미지가 없으니 이미지를 직접 만들어야 하고, 그 레시피가 Dockerfile이다. "JDK가 있는 이미지에서 시작해, 소스를 복사하고, 빌드하고, 결과 jar를 실행한다"를 적어 두면 `docker build`가 이미지를 만든다.

도커 컴포즈는 컨테이너가 여러 개일 때 한 파일에 모아 한 명령으로 올리고 내리는 도구다. "프론트는 3000, 백엔드는 8080이고 Redis가 준비된 뒤에 시작, PostgreSQL 비밀번호는 이것, 데이터는 이 볼륨에"를 `compose.yaml`에 적어 두면 `docker compose up -d` 한 줄로 전부 뜬다. 컨테이너끼리는 자동으로 같은 네트워크에 묶여 서비스 이름으로 서로를 찾는다. 모두가 같은 파일을 쓰니 환경이 갈리지 않는다.

이번 노트가 끝나면 프로젝트는 이렇게 돈다.

```
docker compose up -d
  ├─ frontend   (Next.js, 우리가 만든 이미지)   :3000  ← 브라우저
  ├─ backend    (스프링, 우리가 만든 이미지)     :8080  ← frontend 가 backend:8080 으로 호출
  ├─ postgres   (postgres:17)                  :5432  ← 다음 노트에서 backend 가 사용
  ├─ redis      (redis:7-alpine)               :6379  ← backend 가 redis:6379 로 리프레시 토큰 저장
  └─ adminer    (adminer:5)                    :8082  ← 브라우저로 PostgreSQL 보기
```

---

## 2. 백엔드 Dockerfile

`backend/Dockerfile`을 만든다. 스테이지가 셋인데, 아래 두 개(`build`, 마지막 실행 스테이지)가 운영 이미지를 만드는 본체이고, 맨 위의 `dev`는 5절의 개발 모드가 쓴다.

```dockerfile
# ---- 개발용 스테이지 (compose.override.yaml 이 target: dev 로 쓴다) -------------------------
# 소스는 바인드 마운트로 들어오고, 컨테이너 안에서 ./gradlew bootRun 을 실행한다.
# 받은 Gradle 과 의존성은 gradle_cache 볼륨(/root/.gradle)에 남아 두 번째부터는 빠르다.
FROM eclipse-temurin:25-jdk AS dev
WORKDIR /app
EXPOSE 8080
CMD ["./gradlew", "bootRun", "--no-daemon"]

# ---- 1단계: 빌드. bootJar 를 만든다 -----------------------------------------------------------
FROM eclipse-temurin:25-jdk AS build
WORKDIR /app
# 의존성 목록이 바뀌지 않으면 이 층은 캐시된다 (소스만 고쳤을 때 다시 내려받지 않는다)
COPY gradlew build.gradle settings.gradle ./
COPY gradle ./gradle
RUN chmod +x gradlew && ./gradlew dependencies --no-daemon -q || true
COPY src ./src
RUN ./gradlew bootJar --no-daemon -x test

# ---- 2단계: 실행. JRE 만 있는 가벼운 이미지 ----------------------------------------------------
FROM eclipse-temurin:25-jre
WORKDIR /app
RUN useradd --system --create-home app
USER app
COPY --from=build /app/build/libs/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]

```

- **멀티 스테이지 빌드.** `FROM`이 여러 번 나온다. `build` 스테이지는 JDK와 Gradle로 jar를 만들고, 마지막 스테이지는 JRE만 있는 이미지에 그 jar 하나만 복사한다. 결과 이미지에는 소스도 Gradle도 JDK도 없다. 가볍고, 공격면도 작다.
- **의존성 층을 먼저 만든다.** `build.gradle`과 wrapper만 먼저 복사해 `dependencies`를 돌리고, 그 다음에 `src`를 복사한다. 도커는 각 명령의 결과를 층으로 캐시하는데, 소스만 고쳤을 때 의존성 층은 그대로 재사용되어 라이브러리를 다시 내려받지 않는다. `|| true`는 이 단계가 실패해도(네트워크 등) 다음으로 넘어가게 한다. 어차피 `bootJar`에서 다시 받는다.
- **`-x test`:** 이미지를 만들 때 테스트를 건너뛴다. 지금 테스트는 스프링 컨텍스트를 띄우므로 Redis가 필요한데 빌드 중에는 없다. 테스트는 CI에서 따로 돌린다(뒤의 노트).
- **`USER app`:** 컨테이너 안에서 root로 실행하지 않는다. 운영 이미지의 기본 습관이다.
- **`dev` 스테이지**는 JDK만 있고 소스가 없다. 소스는 컨테이너를 띄울 때 마운트로 들어온다(5절).

`backend/.dockerignore`도 만든다. 호스트의 `build/`, `.gradle/`이 이미지에 복사되지 않게 한다.

```
build/
.gradle/
bin/
*.iml
.idea/
HELP.md

```

---

## 3. 프론트엔드 Dockerfile

Next.js는 빌드 결과물 중 실행에 필요한 파일만 추려 내는 모드가 있다. `next.config.ts`에 한 줄을 더한다.

```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 도커 이미지용. 실행에 필요한 파일만 .next/standalone 에 모아 준다 (frontend/Dockerfile 참고)
  output: "standalone",
  cacheComponents: true,
  partialPrefetching: true,
};

export default nextConfig;
```

`output: "standalone"`을 켜면 `next build`가 `.next/standalone/`에 `server.js`와 그것이 실제로 import하는 `node_modules`만 모아 준다. 수백 MB짜리 `node_modules` 전체를 이미지에 넣지 않아도 된다.

```dockerfile
# ---- 1단계: 의존성 설치 -------------------------------------------------------------------
FROM node:24-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---- 개발용 스테이지 (compose.override.yaml 이 target: dev 로 쓴다) -----------------------
# 소스는 바인드 마운트로 덮이고, node_modules 는 이미지 안의 것을 익명 볼륨으로 유지한다.
FROM node:24-alpine AS dev
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# ---- 2단계: 빌드. next.config.ts 의 output: "standalone" 이 실행에 필요한 파일만 추려 낸다 ----
FROM node:24-alpine AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ---- 3단계: 실행 ------------------------------------------------------------------------
# BACKEND_URL 은 서버 코드가 실행 시점에 읽으므로(NEXT_PUBLIC_ 아님) 이미지에 굳지 않는다.
# compose 가 BACKEND_URL=http://backend:8080 을 넣어 준다.
FROM node:24-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0
ENV PORT=3000
RUN addgroup -S app && adduser -S app -G app
USER app
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]

```

- `deps` → `build` → `runner` 세 스테이지가 운영 이미지를 만든다. `runner`에는 `standalone/`, `static/`, `public/` 셋만 복사된다.
- `npm ci`는 `package-lock.json`에 적힌 버전을 그대로 설치한다. `npm install`은 lock 파일을 고칠 수 있어서 이미지 빌드에는 쓰지 않는다.
- **`BACKEND_URL`은 이미지에 굳지 않는다.** `env.ts`가 `process.env.BACKEND_URL`을 서버 코드가 실행될 때 읽기 때문이다. `NEXT_PUBLIC_` 접두어가 붙은 변수는 빌드 때 브라우저 번들에 박히지만, 접두어 없는 서버 변수는 실행 시 환경에서 온다. 06 노트에서 접두어를 안 붙인 결정이 여기서 보답한다. compose가 실행 시점에 `BACKEND_URL=http://backend:8080`을 넣어 준다.
- **`HOSTNAME=0.0.0.0`:** standalone 서버는 기본으로 localhost에만 귀를 열어 컨테이너 밖에서 접속이 안 된다. 모든 주소에서 받게 바꾼다.

`frontend/.dockerignore`:

```
node_modules/
.next/
.env*
Dockerfile
README.md
AGENTS.md

```

`.env*`를 제외하는 것이 중요하다. 호스트의 `.env.local`이 이미지에 들어가면 `BACKEND_URL=http://localhost:8080`처럼 컨테이너 안에서 틀린 값이 박힌다.

---

## 4. compose.yaml — 다섯 서비스

프로젝트 루트(`backend/`, `frontend/`와 같은 층)에 만든다. 파일 이름은 `compose.yaml`이 현재 표준이고, 예전 이름인 `docker-compose.yml`도 인식된다. 맨 위의 `version:` 줄은 더 이상 쓰지 않는다(있으면 경고가 난다).

```yaml
# ncafe 전체를 한 번에 띄운다: 프론트엔드(Next.js), 백엔드(스프링), PostgreSQL, Redis, Adminer
#
#   docker compose up -d --build   # 처음 또는 Dockerfile·의존성이 바뀌었을 때
#   docker compose up -d           # 그 다음부터
#   docker compose ps              # 상태 (postgres, redis 가 healthy 인지)
#   docker compose logs -f backend # 한 서비스의 로그
#   docker compose down            # 컨테이너 중지·삭제 (데이터 볼륨은 남는다)
#   docker compose down -v         # 데이터까지 삭제
#
# 같은 폴더의 compose.override.yaml 이 자동으로 합쳐져 backend·frontend 는 "개발 모드"(소스 마운트)로 뜬다.
# 운영 이미지 그대로 띄워 보려면:  docker compose -f compose.yaml up -d --build
#
# 값은 .env 파일로 바꿀 수 있다 (.env.example 참고). 없으면 ":-" 뒤의 기본값을 쓴다.
# 컨테이너끼리는 서비스 이름이 호스트 이름이다 (backend → redis:6379, frontend → backend:8080).
services:

  # Next.js. 브라우저는 여기만 본다. 스프링은 backend:8080 으로 서버 안에서만 부른다 (BFF)
  frontend:
    build: ./frontend
    environment:
      BACKEND_URL: http://backend:8080
    ports:
      - "${FRONTEND_PORT:-3000}:3000"
    depends_on:
      - backend

  # 스프링. 리프레시 토큰은 redis 서비스에 저장한다
  backend:
    build: ./backend
    environment:
      REDIS_HOST: redis
      REDIS_PORT: 6379
    ports:
      - "${BACKEND_PORT:-8080}:8080"
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy

  # 영구 데이터: 사용자, 메뉴, 주문 ... (다음 노트에서 JPA 로 연결)
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-ncafe}
      POSTGRES_USER: ${POSTGRES_USER:-ncafe}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-ncafe1234}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-ncafe} -d ${POSTGRES_DB:-ncafe}"]
      interval: 5s
      timeout: 5s
      retries: 5

  # 수명이 있는 데이터: 리프레시 토큰 (이번 노트), 나중에 캐시·블랙리스트
  redis:
    image: redis:7-alpine
    # appendonly: 쓰기를 디스크에 기록해 두어 컨테이너를 재시작해도 키가 살아 있게 한다.
    # 리프레시 토큰은 14일짜리라, 사라지면 모든 사용자가 한꺼번에 로그아웃된다.
    command: ["redis-server", "--appendonly", "yes"]
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # 브라우저로 PostgreSQL 을 들여다보는 도구. http://localhost:8082
  adminer:
    image: adminer:5
    ports:
      - "8082:8080"
    volumes:
      # 로그인 화면을 PostgreSQL 하나로 고정 (기본 화면은 MySQL 이 먼저 선택되어 있다)
      - ./docker/adminer/login-servers.php:/var/www/html/plugins-enabled/login-servers.php:ro
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  postgres_data:
  redis_data:

```

### 1) 우리가 만드는 서비스: frontend, backend

- `build: ./frontend`: `image` 대신 `build`를 쓰면 그 폴더의 Dockerfile로 이미지를 만든다. `docker compose up --build`가 빌드까지 한다.
- `BACKEND_URL: http://backend:8080`: localhost가 아니다. 컴포즈가 만든 네트워크 안에서는 서비스 이름이 호스트 이름이다. frontend 컨테이너에서 `backend`라는 이름은 backend 컨테이너의 주소로 풀린다. 포트도 호스트에 연 포트가 아니라 컨테이너 안의 포트(8080)다.
- `REDIS_HOST: redis`: 같은 이유다. `application.yml`의 `${REDIS_HOST:localhost}`가 이 값을 받는다.
- `depends_on` + `condition: service_healthy`: backend는 redis와 postgres가 healthy가 된 뒤에 시작한다. `condition` 없이 `depends_on`만 쓰면 시작 순서만 보장하고 준비 여부는 보장하지 않아, 스프링이 먼저 떠서 Redis 연결 실패로 죽을 수 있다. frontend는 backend가 꺼져 있어도 502 처리를 하므로(메뉴 BFF 노트) 순서만 지킨다.
- `"${FRONTEND_PORT:-3000}:3000"`: 호스트:컨테이너. 호스트 쪽은 `.env`로 바꿀 수 있게 했다.

### 2) 받아 쓰는 서비스: postgres, redis, adminer

- `image`에 버전 태그를 꼭 붙인다. `latest`로 두면 사람마다 다른 버전이 뜰 수 있다.
- `environment`: postgres 이미지는 `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`로 첫 DB와 계정을 만든다.
- `volumes`: 컨테이너는 지우면 안의 파일도 사라진다. 데이터를 남기려면 볼륨에 둔다.
- `healthcheck`: "떠 있다"와 "준비됐다"는 다르다. PostgreSQL은 시작 직후 몇 초 동안 연결을 받지 못한다.
- Redis의 `command`: `--appendonly yes`를 붙인다. 모든 쓰기를 디스크 파일에 기록해 두어 컨테이너를 재시작해도 데이터가 남는다(7절 5항).

### 3) `${POSTGRES_PASSWORD:-ncafe1234}` — 기본값과 `.env`

`${변수:-기본값}`은 "환경 변수나 `.env` 파일에 그 변수가 있으면 그 값을, 없으면 기본값을" 쓴다는 뜻이다. `.env.example`:

```
# docker compose 가 읽는 값. 복사해서 .env 로 만들면 compose.yaml 의 기본값을 덮어쓴다.
#   cp .env.example .env
# .env 는 커밋하지 않는다 (.gitignore).

# 호스트에 여는 포트. 이미 쓰는 포트가 있으면 여기서 바꾼다
FRONTEND_PORT=3000
BACKEND_PORT=8080

POSTGRES_DB=ncafe
POSTGRES_USER=ncafe
POSTGRES_PASSWORD=ncafe1234

```

`.env`는 `.gitignore`에 들어 있어 커밋되지 않는다.

### 4) Adminer의 로그인 화면 고정

```php
<?php
// Adminer 로그인 화면의 "System" 선택을 없애고 PostgreSQL 서버 하나만 보여준다.
// (기본 화면은 MySQL 이 먼저 선택되어 있어 헷갈린다)
// compose.yaml 이 이 파일을 /var/www/html/plugins-enabled/ 에 마운트한다.
require_once('plugins/login-servers.php');

return new AdminerLoginServers([
    'PostgreSQL (ncafe)' => ['server' => 'postgres', 'driver' => 'pgsql'],
]);

```

compose에서 이 파일을 컨테이너의 `plugins-enabled/`에 읽기 전용(`:ro`)으로 마운트한다. `server`에 적은 `postgres`는 역시 서비스 이름이다.

---

## 5. compose.override.yaml — 개발 모드

4절대로만 쓰면 코드를 한 줄 고칠 때마다 `docker compose up --build`로 이미지를 다시 만들어야 한다. 개발 중에는 소스 폴더를 컨테이너에 마운트하고, 그 안에서 `bootRun`과 `next dev`를 실행한다.

컴포즈는 `compose.yaml` 옆에 `compose.override.yaml`이 있으면 자동으로 둘을 합친다.

```yaml
# 개발 모드. docker compose 가 compose.yaml 과 자동으로 합친다.
#
# 운영 이미지(빌드 결과물)를 띄우는 대신, 소스 폴더를 컨테이너에 마운트하고
# 그 안에서 bootRun / next dev 를 실행한다. 코드를 고치면 이미지를 다시 만들지 않아도 된다.
#  - frontend: 저장하면 바로 반영된다 (next dev 의 핫 리로드)
#  - backend : 저장 후 `docker compose restart backend` (bootRun 이 다시 컴파일한다)
services:

  frontend:
    build:
      context: ./frontend
      target: dev
    volumes:
      - ./frontend:/app
      - /app/node_modules   # 이미지 안의 node_modules 를 유지 (호스트 것과 섞이지 않게)
      - /app/.next          # 빌드 캐시도 컨테이너 안에
    environment:
      NODE_ENV: development
    command: ["npm", "run", "dev"]

  backend:
    build:
      context: ./backend
      target: dev
    volumes:
      - ./backend:/app
      - gradle_cache:/root/.gradle   # 받은 Gradle 과 라이브러리를 재사용
    command: ["./gradlew", "bootRun", "--no-daemon"]

volumes:
  gradle_cache:

```

- `target: dev`: Dockerfile의 여러 스테이지 중 `dev`까지만 빌드한다.
- `./frontend:/app`: 호스트의 소스 폴더를 컨테이너의 `/app`에 그대로 보인다.
- `/app/node_modules` (왼쪽이 없는 볼륨): 컨테이너는 이미지 안에서 설치한 것을 쓴다.
- `gradle_cache:/root/.gradle`: 받은 Gradle과 라이브러리를 재사용한다.
- 백엔드는 핫 리로드가 아니다. 자바 코드를 고쳤으면 `docker compose restart backend`를 친다.

| 하고 싶은 것 | 명령 |
|---|---|
| 개발 (소스 마운트, 핫 리로드) | `docker compose up -d` |
| 운영 이미지 그대로 띄워 보기 | `docker compose -f compose.yaml up -d --build` |

`-f compose.yaml`로 파일을 명시하면 override가 합쳐지지 않는다.

---

## 6. 올리고 확인하기

```bash
docker compose up -d --build
```

처음에는 이미지를 받고 두 이미지를 만들고 Gradle이 라이브러리를 내려받는다. 네트워크에 따라 5분 안팎이다. 그 다음부터는 `docker compose up -d`로 몇 초면 뜬다.

```bash
docker compose ps
```

| 명령 | 뜻 |
|---|---|
| `docker compose up -d` | 올린다 |
| `docker compose up -d --build` | 이미지를 다시 만들고 올린다 |
| `docker compose ps` | 상태 |
| `docker compose logs -f backend` | 한 서비스 로그 |
| `docker compose exec redis redis-cli` | 컨테이너 안에서 명령 |
| `docker compose restart backend` | 한 서비스만 재시작 |
| `docker compose stop` / `start` | 멈춤·재시작 |
| `docker compose down` | 컨테이너와 네트워크 삭제. 볼륨은 남는다 |
| `docker compose down -v` | 볼륨까지 삭제 |

`down`과 `down -v`의 차이를 꼭 기억한다.

```bash
curl http://localhost:8080/api/menus | head -c 200
docker compose exec postgres pg_isready -U ncafe -d ncafe
docker compose exec postgres psql -U ncafe -d ncafe -c '\dt'
docker compose exec redis redis-cli ping
```

Adminer는 `http://localhost:8082`. 사용자 `ncafe`, 비밀번호 `ncafe1234`, DB `ncafe`. 지금은 빈 DB다.

---

## 7. Redis란 무엇인가

### 1) 메모리에 있는 키-값 저장소

Redis는 데이터를 메모리에 두는 키-값 저장소다. 이름은 REmote DIctionary Server의 줄임말로, "네트워크 너머에 있는 거대한 해시맵"이라고 보면 정확하다. 지금 `RefreshTokenStore`의 `ConcurrentHashMap`을 자바 프로세스 밖으로 꺼내 별도 서버로 만든 것이 Redis다.

### 2) PostgreSQL과 무엇이 다른가

| | PostgreSQL | Redis |
|---|---|---|
| 데이터 위치 | 디스크 | 메모리 (디스크에는 복구용 기록만) |
| 구조 | 테이블, 행, 컬럼, 관계 | 키 하나에 값 하나 |
| 조회 방식 | SQL. WHERE, JOIN, 집계 | 키를 알아야 꺼낸다 |
| 속도 | 밀리초 | 마이크로초 |
| 만료 | 직접 지워야 함 | 키마다 TTL을 붙이면 자동 삭제 |
| 어울리는 데이터 | 오래 남기고 관계가 있는 것 | 잠시 쓰고 버리는 것, 아주 자주 읽는 것 |

### 3) 어디에 쓰는가

- 세션·토큰 보관 (이번 노트)
- 캐시
- 카운터와 요청 제한
- 서버 간 공유 상태 (인스턴스 여러 대)
- 분산 락, 메시지 전달 (범위 밖)

JWT를 쓰는 이유는 STATELESS인데, 리프레시 토큰을 서버에 저장하는 순간 상태가 다시 생긴다. 그 최소한의 공유 상태를 두는 곳이 Redis다.

### 4) 디스크 기록: RDB와 AOF

- **RDB:** 주기 스냅샷. 마지막 스냅샷 이후 유실 가능.
- **AOF:** 쓰기마다 덧붙임. compose의 `--appendonly yes`.

### 5) 보안

개발용 compose의 Redis에는 비밀번호가 없다. 운영에서는 `requirepass`, 호스트 포트 비공개, 필요 시 TLS.

---

## 8. redis-cli로 직접 써 보기

```bash
docker compose exec redis redis-cli
```

```
SET demo:hello world              → OK
GET demo:hello                    → "world"
SET demo:code 1234 EX 60          → OK
TTL demo:code                     → 57
EXPIRE demo:hello 10              → 1
EXISTS demo:hello                 → 1
INCR demo:count                   → 1
DEL demo:hello demo:count         → 2
KEYS demo:*                       → ...
```

재시작 실험: `SET demo:keep alive` → `docker compose restart redis` → `GET demo:keep`이 `"alive"`면 AOF 동작.

키 접두어 관례: `refresh:newlec`, `cache:menus`. 운영에서는 `KEYS` 대신 `SCAN`.

---

## 9. 스프링에서 Redis 쓰기 — RefreshTokenStore

### 1) 의존성과 접속 설정

`build.gradle`:

```gradle
implementation 'org.springframework.boot:spring-boot-starter-data-redis'
```

`application.yml`:

```yaml
spring:
  application:
    name: backend
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
jwt:
  secret: ${JWT_SECRET:v9y$B&E)H@McQfTjWnZr4u7x!A%C*F-JaNdR}
  access-token-expiration: 1800000
  refresh-token-expiration: 1209600000
```

compose 안에서는 `REDIS_HOST=redis`, IDE에서만 띄우면 `localhost:6379`.

### 2) StringRedisTemplate

키·값 모두 문자열. `opsForValue().set/get`, `delete`, `hasKey`.

### 3) 바뀐 RefreshTokenStore

```java
package com.ncafe.backend.security.jwt;

import java.time.Duration;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import com.ncafe.backend.config.JwtProperties;

/**
 * 발급한 리프레시 토큰을 기억해 두는 저장소. 이제 Redis 에 둔다.
 *
 * 액세스 토큰은 서명만 맞으면 통과시키지만(STATELESS),
 * 리프레시 토큰은 수명이 길어서 "서버가 아직 인정하는 토큰인지"를 따로 확인해야 한다.
 * 로그아웃하면 여기서 지우고, 그 뒤로는 같은 토큰으로 재발급받을 수 없다.
 *
 * 메모리 Map 에서 Redis 로 바뀐 이유 두 가지
 *  - 서버를 재시작하거나 여러 대로 늘려도 같은 토큰 목록을 본다.
 *  - 키에 수명(TTL)을 붙이면 14일 뒤 Redis 가 스스로 지운다. 만료 청소 코드가 없다.
 *
 * 키 모양: refresh:{username}  →  값: 그 사용자에게 마지막으로 발급한 리프레시 토큰
 */
@Component
public class RefreshTokenStore {

    private static final String KEY_PREFIX = "refresh:";

    private final StringRedisTemplate redis;
    private final Duration ttl;

    public RefreshTokenStore(StringRedisTemplate redis, JwtProperties jwtProperties) {
        this.redis = redis;
        // 토큰 자체의 만료 시간과 같게 둔다. 토큰이 죽은 뒤에도 키가 남아 있을 이유가 없다.
        this.ttl = Duration.ofMillis(jwtProperties.getRefreshTokenExpiration());
    }

    /** SET refresh:{username} {token} EX {ttl} — 같은 사용자의 이전 토큰은 덮어써진다 */
    public void save(String username, String refreshToken) {
        redis.opsForValue().set(key(username), refreshToken, ttl);
    }

    /** GET refresh:{username} 과 비교. 로그아웃했거나 다른 기기에서 다시 로그인했으면 false */
    public boolean matches(String username, String refreshToken) {
        return refreshToken.equals(redis.opsForValue().get(key(username)));
    }

    /** DEL refresh:{username} */
    public void remove(String username) {
        redis.delete(key(username));
    }

    private String key(String username) {
        return KEY_PREFIX + username;
    }
}

```

메서드 시그니처(`save`, `matches`, `remove`)가 그대로라 `AuthService`는 한 줄도 안 바뀐다. TTL은 토큰 만료와 같다.

```bash
docker compose up -d --build backend
```

---

## 10. Redis가 꺼져 있으면 — 503

`docker compose stop redis` 후 로그인하면 연결 예외 → 기본 500. `DataAccessException`을 `GlobalExceptionHandler`에서 503 `ErrorResponse`로 바꾼다.

```java
package com.ncafe.backend.controller;

import com.ncafe.backend.dto.common.ErrorResponse;
import com.ncafe.backend.security.jwt.InvalidTokenException;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.dao.DataAccessException;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 컨트롤러 안에서 던져진 예외를 ErrorResponse 로 바꾼다.
 *
 * 필터 단계의 401/403 은 시큐리티 핸들러(JsonAuthenticationEntryPoint, JsonAccessDeniedHandler)가 맡고,
 * 컨트롤러·서비스 단계의 예외는 여기서 맡는다. 두 곳 모두 같은 ErrorResponse 형식을 쓴다.
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    /** 로그인: 아이디·비밀번호 불일치. AuthenticationManager 가 던진다 */
    @ExceptionHandler(BadCredentialsException.class)
    @ResponseStatus(HttpStatus.UNAUTHORIZED)
    public ErrorResponse handleBadCredentials(BadCredentialsException e, HttpServletRequest request) {
        return ErrorResponse.of(
                HttpStatus.UNAUTHORIZED.value(),
                HttpStatus.UNAUTHORIZED.name(),
                "아이디 또는 비밀번호가 올바르지 않습니다.",
                request.getRequestURI()
        );
    }

    /** 재발급: 리프레시 토큰이 위조·만료·폐기됨. AuthService.refresh() 가 던진다 */
    @ExceptionHandler(InvalidTokenException.class)
    @ResponseStatus(HttpStatus.UNAUTHORIZED)
    public ErrorResponse handleInvalidToken(InvalidTokenException e, HttpServletRequest request) {
        return ErrorResponse.of(
                HttpStatus.UNAUTHORIZED.value(),
                HttpStatus.UNAUTHORIZED.name(),
                e.getMessage(),
                request.getRequestURI()
        );
    }

    /**
     * 저장소(Redis, 다음 노트부터는 DB) 연결 실패. 스프링 데이터 계열 예외의 공통 부모가 DataAccessException 이다.
     * 사용자 잘못이 아니라 서버 사정이므로 503 으로 알리고, 내부 사정(타임아웃, 호스트 이름)은 응답에 쓰지 않는다.
     */
    @ExceptionHandler(DataAccessException.class)
    @ResponseStatus(HttpStatus.SERVICE_UNAVAILABLE)
    public ErrorResponse handleDataAccess(DataAccessException e, HttpServletRequest request) {
        return ErrorResponse.of(
                HttpStatus.SERVICE_UNAVAILABLE.value(),
                HttpStatus.SERVICE_UNAVAILABLE.name(),
                "일시적으로 요청을 처리할 수 없습니다. 잠시 후 다시 시도해 주세요.",
                request.getRequestURI()
        );
    }
}

```

- 503: 서버 사정. 사용자 잘못이 아님.
- 메시지에 내부 사정(타임아웃, 호스트)을 쓰지 않는다.
- 다음 노트에서 PostgreSQL이 꺼져도 같은 핸들러가 받는다.

---

## 11. 확인하기

| # | 하는 일 | 기대 | redis-cli |
|---|---|---|---|
| 1 | newlec / 123 로그인 | 200 | `KEYS refresh:*` → `refresh:newlec`, TTL ≈ 1209600 |
| 2 | 그 refresh로 `/refresh` | 200 | 키 그대로 |
| 3 | 위조 refresh | 401 | — |
| 4 | 다시 로그인 후 옛 토큰 재발급 | 401 | GET이 새 토큰 |
| 5 | logout | 204 | `EXISTS` → 0 |
| 6 | 로그인 → `restart redis` → 재발급 | 200 | AOF |
| 7 | 로그인 → `restart backend` → 재발급 | 200 | **목표** |
| 8 | `stop redis` → 로그인 | 503 ErrorResponse | — |
| 9 | 그 상태 `GET /api/menus` | 200 | Redis 무관 |

프론트 코드는 바꿀 것 없다. 저장소가 어디인지는 프론트가 모른다.

---

## 12. 주의할 사항과 정리

### 1) 컨테이너 안과 밖의 호스트 이름

컨테이너: `backend:8080`, `redis:6379`. 호스트: `localhost:8080`, `localhost:6379`. `${REDIS_HOST:localhost}`로 둘 다 처리.

### 2) 로그인이 Redis에 의존

Redis 다운 → 로그인·재발급·로그아웃 503. 메뉴 조회와 이미 받은 Access(서명만)는 유지.

### 3) `down -v`는 토큰도 지운다

Redis 볼륨까지 사라지면 전원 로그아웃.

### 4) IDE에서 스프링만

`docker compose stop backend` 후 IDE 실행. Redis/Postgres는 localhost 포트. 프론트도 호스트 `npm run dev`.

### 5) 더 조일 수 있는 것

Refresh Rotation, Access 블랙리스트(`SET blacklist:{jti} 1 EX …`) — 이후 노트.

### 6) 정리

| 데이터 | 저장소 | 이유 |
|---|---|---|
| 액세스 토큰 | 저장 안 함 | 서명만 (STATELESS) |
| 리프레시 토큰 | Redis, TTL 14일 | 폐기·공유·수명 |
| 메뉴, 사용자 | PostgreSQL (다음) | 영구·관계·검색 |

### 7) 이번 노트에서 추가·수정된 파일

**루트 (추가)** `compose.yaml`, `compose.override.yaml`, `.env.example`, `docker/adminer/login-servers.php`

**백엔드 (추가)** `Dockerfile`, `.dockerignore`

**백엔드 (수정)** `build.gradle`, `application.yml`, `RefreshTokenStore.java`, `GlobalExceptionHandler.java`

**프론트 (추가)** `Dockerfile`, `.dockerignore`

**프론트 (수정)** `next.config.ts` — `output: "standalone"`

---

## 마무리

프로젝트 전체가 `docker compose up -d` 한 줄로 올라온다. 리프레시 토큰은 서버 프로세스 밖으로 나가 재시작해도 로그인 상태가 유지된다. PostgreSQL은 떠 있지만 아직 비어 있다. JPA로 채우는 일과 서버 배포·HTTPS·CI/CD는 이후 노트에서 이어진다.
