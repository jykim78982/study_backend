---
tags: [Docker, DockerCompose, Dockerfile, 멀티스테이지빌드, override, Redis, RefreshToken, StringRedisTemplate, PostgreSQL, Adminer, 참고자료]
---

> 🔗 관련 노트: [[097_Docker Compose — 여러 컨테이너를 하나의 네트워크로 묶어 실행하기]] · [[041_Nginx, Next.js, Spring Boot, PostgreSQL을 하나로 묶는 도커 컴포즈 실전 구축기 참고자료]] · [[053_Refresh Token으로 조용히 갱신하기 — 재발급 API, RefreshTokenStore, proxy 문지기]] · [[044_서버 배포와 HTTPS — nginx 리버스 프록시, mkcert, certbot, 팀별 서브도메인 참고자료]]

# 도커 컴포즈로 프론트·백엔드·PostgreSQL·Redis 한 번에 띄우기와 리프레시 토큰 Redis 저장

## 0. 왜 하는가

이전 단계까지 두 가지가 서버 프로세스 안에 갇혀 있었다.

- 메뉴 13개가 `MenuRepository`의 `List.of(...)` 안에 있다.
- 리프레시 토큰이 `RefreshTokenStore`의 `ConcurrentHashMap` 안에 있다.

둘째가 더 급하다. 로그인해서 리프레시 토큰을 받은 뒤 스프링을 재시작하고 그 토큰으로 재발급을 요청하면 401("이미 만료 처리된 리프레시 토큰입니다")이 온다. 토큰은 14일짜리인데, **서버가 한 번 재시작되면 모든 사용자가 로그아웃된다.** 배포할 때마다, 서버가 두 대일 때 요청이 다른 서버로 갈 때마다 같은 일이 생긴다. 저장소는 서버 밖에 있어야 한다.

- 메뉴·사용자 → PostgreSQL (JPA 연결은 다음 단계)
- 리프레시 토큰 → Redis (이번 단계)

실행할 것이 스프링, Next.js, PostgreSQL, Redis 넷이 된다. 팀원마다 DB를 설치하고 버전·포트·비밀번호를 맞추면 시간이 환경 문제로 샌다. 그래서 전부를 `docker compose up` 한 줄로 띄운다.

```
docker compose up -d
  ├─ frontend   (Next.js, 직접 만든 이미지)   :3000  ← 브라우저
  ├─ backend    (스프링, 직접 만든 이미지)     :8080  ← frontend 가 backend:8080 으로 호출
  ├─ postgres   (postgres:17)                :5432  ← 다음 단계에서 backend 가 사용
  ├─ redis      (redis:7-alpine)             :6379  ← backend 가 redis:6379 에 리프레시 토큰 저장
  └─ adminer    (adminer:5)                  :8082  ← 브라우저로 PostgreSQL 보기
```

## 1. 도커와 도커 컴포즈

| 도구 | 하는 일 |
| --- | --- |
| 도커 | 프로그램을 설치하지 않고 이미지로 받아 컨테이너로 실행한다. 어느 컴퓨터에서든 같은 버전·같은 설정으로 돌고, 지우면 흔적이 남지 않는다 |
| Dockerfile | 공개 이미지가 없는 우리 앱(스프링, Next.js)의 이미지를 만드는 레시피. `docker build`가 읽는다 |
| 도커 컴포즈 | 컨테이너 여러 개를 한 파일(`compose.yaml`)에 적고 한 명령으로 올리고 내린다. 컨테이너들은 같은 네트워크에 묶여 **서비스 이름으로 서로를 찾는다** |

## 2. 백엔드 Dockerfile

```dockerfile
# ---- 개발용 (compose.override.yaml 이 target: dev 로 쓴다) ----
# 소스는 바인드 마운트로 들어오고, 컨테이너 안에서 bootRun 을 실행한다
FROM eclipse-temurin:25-jdk AS dev
WORKDIR /app
EXPOSE 8080
CMD ["./gradlew", "bootRun", "--no-daemon"]

# ---- 1단계: 빌드 ----
FROM eclipse-temurin:25-jdk AS build
WORKDIR /app
COPY gradlew build.gradle settings.gradle ./
COPY gradle ./gradle
RUN chmod +x gradlew && ./gradlew dependencies --no-daemon -q || true
COPY src ./src
RUN ./gradlew bootJar --no-daemon -x test

# ---- 2단계: 실행 (JRE 만) ----
FROM eclipse-temurin:25-jre
WORKDIR /app
RUN useradd --system --create-home app
USER app
COPY --from=build /app/build/libs/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

| 포인트 | 설명 |
| --- | --- |
| 멀티 스테이지 빌드 | build 단계에서 JDK·Gradle로 jar를 만들고, 실행 단계에는 JRE와 jar만 둔다. 소스·Gradle·JDK가 없어 가볍고 공격면이 작다 |
| 의존성 층 먼저 | `build.gradle`과 wrapper만 먼저 복사해 의존성을 받고 그 다음에 `src`를 복사한다. 소스만 고치면 의존성 층은 캐시를 재사용한다. `|| true`는 이 단계가 실패해도 넘어가게 한다(어차피 `bootJar`에서 다시 받는다) |
| `-x test` | 테스트가 스프링 컨텍스트를 띄우면서 Redis를 찾는데, 빌드 중에는 없다. 테스트는 CI에서 따로 돌린다 |
| `USER app` | 컨테이너 안에서 root로 실행하지 않는다 |
| dev 단계 | JDK만 있고 소스는 없다. 실행할 때 마운트로 들어온다(5절) |

`backend/.dockerignore`로 `build/`, `.gradle/`, `bin/`, `*.iml`, `.idea/`가 이미지에 들어가지 않게 한다.

## 3. 프론트엔드 Dockerfile

`next.config.ts`에 `output: "standalone"`을 켠다. `next build`가 `.next/standalone/`에 `server.js`와 실제로 쓰는 `node_modules`만 모아 준다.

```dockerfile
FROM node:24-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# 개발용 (compose.override.yaml 이 target: dev 로 쓴다)
FROM node:24-alpine AS dev
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

FROM node:24-alpine AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:24-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
RUN addgroup -S app && adduser -S app -G app
USER app
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

| 포인트 | 설명 |
| --- | --- |
| `npm ci` | lock 파일 버전 그대로 설치한다. `npm install`은 lock 파일을 고칠 수 있어 이미지 빌드에 쓰지 않는다 |
| `BACKEND_URL`은 이미지에 굳지 않는다 | `NEXT_PUBLIC_` 접두어가 없는 서버 변수는 **실행할 때** 환경에서 읽는다. compose가 `BACKEND_URL=http://backend:8080`을 넣어 준다. `NEXT_PUBLIC_` 변수는 빌드 때 브라우저 번들에 박힌다 |
| `HOSTNAME=0.0.0.0` | standalone 서버는 기본으로 localhost에만 열려 컨테이너 밖에서 접속이 안 된다 |
| `.dockerignore`의 `.env*` | 호스트의 `.env.local`(`BACKEND_URL=http://localhost:8080` 등)이 이미지에 들어가면 컨테이너 안에서 틀린 값이 된다 |

## 4. compose.yaml — 다섯 서비스

```yaml
services:
  frontend:
    build: ./frontend
    environment:
      BACKEND_URL: http://backend:8080
    ports:
      - "${FRONTEND_PORT:-3000}:3000"
    depends_on:
      - backend

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

  redis:
    image: redis:7-alpine
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

  adminer:
    image: adminer:5
    ports:
      - "8082:8080"
    volumes:
      - ./docker/adminer/login-servers.php:/var/www/html/plugins-enabled/login-servers.php:ro
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  postgres_data:
  redis_data:
```

파일 이름은 `compose.yaml`이 현재 표준이다(`docker-compose.yml`도 인식). 맨 위 `version:` 줄은 더 이상 쓰지 않는다.

### 1) 직접 만드는 서비스: frontend, backend
- `build: ./frontend`: 그 폴더의 Dockerfile로 이미지를 만든다. `docker compose up --build`가 빌드까지 한다.
- `BACKEND_URL: http://backend:8080`, `REDIS_HOST: redis`: compose 네트워크 안에서는 **서비스 이름이 호스트 이름**이고, 포트는 컨테이너 안의 포트다.
- `depends_on` + `condition: service_healthy`: redis·postgres가 healthy가 된 뒤 backend를 시작한다. condition 없이 쓰면 시작 순서만 보장하고 준비 여부는 보장하지 않아, 스프링이 먼저 떠서 Redis 연결 실패로 죽을 수 있다.
- `"${FRONTEND_PORT:-3000}:3000"`: 호스트:컨테이너. 호스트 쪽은 `.env`로 바꿀 수 있다.

### 2) 받아 쓰는 서비스: postgres, redis, adminer
- 이미지에는 **버전 태그를 꼭 붙인다.** `latest`면 사람마다 다른 버전이 뜰 수 있다.
- `volumes`: 컨테이너를 지우면 안의 파일도 사라지므로 데이터는 볼륨에 둔다.
- `healthcheck`: "떠 있다"와 "준비됐다"는 다르다. PostgreSQL은 시작 직후 몇 초 동안 연결을 받지 못한다.
- Redis의 `command`: `--appendonly yes`로 모든 쓰기를 디스크에 기록해, 재시작해도 키가 남게 한다(7절).

### 3) `${변수:-기본값}`과 .env
환경 변수나 `.env`에 값이 있으면 그 값을, 없으면 기본값을 쓴다. `.env` 없이도 뜨고, 바꾸려면 `.env.example`을 복사해 `.env`를 만든다. `.env`는 커밋하지 않는다.

### 4) Adminer 로그인 화면 고정
Adminer는 기본으로 MySQL이 선택돼 헷갈린다. 이미지에 들어 있는 `login-servers` 플러그인을 켜서 서버 목록을 PostgreSQL 하나로 고정한다. 호스트 경로(`./docker/...`)를 붙이는 것을 **바인드 마운트**라고 한다.

```php
<?php
require_once('plugins/login-servers.php');
return new AdminerLoginServers([
    'PostgreSQL (ncafe)' => ['server' => 'postgres', 'driver' => 'pgsql'],
]);
```

## 5. compose.override.yaml — 개발 모드

4절대로만 쓰면 코드 한 줄을 고칠 때마다 이미지를 다시 만들어야 한다. 개발 중에는 소스 폴더를 컨테이너에 마운트하고 그 안에서 `bootRun`과 `next dev`를 실행한다. compose는 `compose.yaml` 옆에 `compose.override.yaml`이 있으면 **자동으로 합친다.**

```yaml
services:
  frontend:
    build:
      context: ./frontend
      target: dev
    volumes:
      - ./frontend:/app
      - /app/node_modules   # 이미지 안의 node_modules 유지
      - /app/.next
    environment:
      NODE_ENV: development
    command: ["npm", "run", "dev"]

  backend:
    build:
      context: ./backend
      target: dev
    volumes:
      - ./backend:/app
      - gradle_cache:/root/.gradle
    command: ["./gradlew", "bootRun", "--no-daemon"]

volumes:
  gradle_cache:
```

| 포인트 | 설명 |
| --- | --- |
| `target: dev` | Dockerfile의 dev 단계까지만 빌드한다. 운영 단계(jar 빌드, next build)는 실행되지 않는다 |
| `./frontend:/app` | 저장하면 `next dev`가 바로 반영한다(핫 리로드) |
| `/app/node_modules` | 왼쪽이 없는 볼륨. 호스트(Windows·macOS)의 네이티브 모듈과 섞이지 않게 이미지 안의 것을 쓴다 |
| `gradle_cache:/root/.gradle` | 받은 Gradle과 라이브러리를 재사용한다. 처음만 몇 분 걸린다 |
| 백엔드는 핫 리로드가 아니다 | 자바 코드를 고쳤으면 `docker compose restart backend` (20초 안팎) |

| 하고 싶은 것 | 명령 |
| --- | --- |
| 개발 (소스 마운트, 핫 리로드) | `docker compose up -d` |
| 운영 이미지 그대로 띄워 보기 | `docker compose -f compose.yaml up -d --build` (`-f`로 지정하면 override가 합쳐지지 않는다) |

## 6. 올리고 확인하기

처음 `docker compose up -d --build`는 이미지 받기와 빌드, Gradle 다운로드로 5분 안팎 걸린다. 그 다음부터는 `docker compose up -d`로 몇 초면 뜬다. 컨테이너 이름은 `프로젝트-서비스-번호`이고, 프로젝트 이름은 폴더 이름이다.

| 명령 | 뜻 |
| --- | --- |
| `docker compose up -d` | 올린다. 떠 있으면 바뀐 것만 다시 만든다 |
| `docker compose up -d --build` | 이미지를 다시 만들고 올린다(Dockerfile·의존성이 바뀌었을 때) |
| `docker compose ps` | 상태 |
| `docker compose logs -f backend` | 한 서비스의 로그 |
| `docker compose exec redis redis-cli` | 컨테이너 안에서 명령 실행 |
| `docker compose restart backend` | 한 서비스만 재시작 |
| `docker compose stop` / `start` | 컨테이너는 두고 멈춤·재시작 |
| `docker compose down` | 컨테이너와 네트워크 삭제. **볼륨은 남는다** |
| `docker compose down -v` | **볼륨까지 삭제.** DB와 Redis 데이터가 모두 사라진다 |

```sh
curl http://localhost:8080/api/menus | head -c 200          # 백엔드
docker compose exec postgres pg_isready -U ncafe -d ncafe    # accepting connections
docker compose exec postgres psql -U ncafe -d ncafe -c '\dt' # Did not find any relations (아직 테이블 없음)
docker compose exec redis redis-cli ping                     # PONG
```

Adminer는 `http://localhost:8082`에서 사용자 `ncafe`, 비밀번호 `ncafe1234`, DB `ncafe`로 들어간다.

## 7. Redis란 무엇인가

### 1) 메모리에 있는 키-값 저장소
REmote DIctionary Server. **"네트워크 너머에 있는 거대한 해시맵"**이다. `RefreshTokenStore`의 `ConcurrentHashMap`을 자바 프로세스 밖으로 꺼내 별도 서버로 만든 것이라고 보면 된다. 2009년 살바토레 산필리포가 실시간 웹 로그 분석기의 "최근 방문 N건"을 MySQL로 처리하다 쓰기 부하를 견디지 못해 만들었다. 처음부터 캐시가 아니라 그 데이터의 유일한 저장소였기 때문에 디스크에 복구용 기록을 남기는 기능도 처음부터 있었다.

### 2) PostgreSQL과 비교

| | PostgreSQL | Redis |
| --- | --- | --- |
| 데이터 위치 | 디스크 | 메모리 (디스크에는 복구용 기록만) |
| 구조 | 테이블, 행, 컬럼, 관계 | 키 하나에 값 하나 |
| 값의 종류 | 컬럼 타입 | 문자열, 리스트, 집합, 해시, 정렬된 집합 |
| 조회 | SQL (WHERE, JOIN, 집계) | 키를 알아야 꺼낸다. 조건 검색 없음 |
| 속도 | 밀리초 | 마이크로초 |
| 만료 | 직접 지워야 함 | 키마다 수명(TTL)을 붙이면 자동 삭제 |
| 어울리는 데이터 | 오래 남기고 관계가 있는 것 | 잠시 쓰고 버리는 것, 아주 자주 읽는 것 |

핵심은 둘이다. **키로 바로 꺼낸다**, **키에 수명이 있다.** "만료가 3일 이내인 토큰 전부"처럼 조건으로 찾아야 하는 데이터는 PostgreSQL에 둔다.

### 3) 쓰임새
- **세션·토큰 보관:** 로그인 세션, 리프레시 토큰, 이메일 인증 코드. 수명을 함께 주면 만료 처리 코드가 없어진다(이번 단계).
- **캐시:** 비싸게 조회한 결과를 잠시 들고 있다가 같은 요청에 바로 돌려준다.
- **카운터와 요청 제한:** 조회수, "1분에 로그인 5회까지". `INCR`로 원자적으로 증가한다.
- **서버 간 공유 상태:** 서버가 여러 대면 각 서버 메모리는 서로 안 보인다. Redis에 두면 모두 같은 값을 본다.
- 분산 락, 발행/구독 (이번 범위 밖)

### 4) 왜 세션·토큰에 맞는가
읽기가 잦고, 수명이 짧고, 사라져도 다시 로그인하면 되는 데이터라 디스크 영구 저장과 인덱스 관리 비용이 어울리지 않는다. JWT는 "서버에 상태를 두지 않는다(STATELESS)"가 장점이었지만, 리프레시 토큰을 저장하는 순간 상태가 다시 생긴다. 로그아웃과 토큰 폐기를 하려면 피할 수 없는 **최소한의 공유 상태**이고, 그것을 두는 곳이 Redis다. **액세스 토큰은 여전히 저장하지 않고 서명만 검증한다.**

### 5) 디스크 기록: RDB와 AOF
- **RDB(스냅샷):** 일정 주기로 메모리 전체를 파일로 떨어뜨린다. 기본값이고 빠르지만, 마지막 스냅샷 이후의 쓰기는 재시작하면 사라진다.
- **AOF(append only file):** 쓰기 명령마다 파일 끝에 덧붙이고, 재시작하면 처음부터 다시 실행해 복구한다. 유실이 거의 없다.

compose에서 `--appendonly yes`를 켠 이유다. 읽고 쓰는 것은 여전히 메모리에서 일어난다.

### 6) 보안
개발용 Redis에는 비밀번호가 없다. Redis는 신뢰할 수 있는 내부 네트워크에서만 쓰는 것을 전제로 설계됐다. 운영에서는 `requirepass`로 비밀번호를 걸고, `ports`를 지워 호스트에 열지 않고(서비스 이름으로만 접근), 필요하면 TLS를 붙인다.

## 8. redis-cli로 직접 써 보기

```
docker compose exec redis redis-cli

SET demo:hello world          → OK            키에 값 저장
GET demo:hello                → "world"
SET demo:code 1234 EX 60      → OK            60초 수명을 함께 지정
TTL demo:code                 → 57            남은 초. 수명 없음 -1, 키 없음 -2
EXPIRE demo:hello 10          → 1             있는 키에 수명 붙이기
EXISTS demo:hello             → 1
INCR demo:count               → 1             없던 키를 0으로 보고 1 증가
DEL demo:hello demo:count     → 2             지운 개수
KEYS demo:*                   → 1) "demo:code"  (개발용. 운영에서는 SCAN)
```

- 60초 뒤 `GET demo:code`는 `(nil)`이다. 아무도 지우지 않았는데 사라지는 것이 TTL이다.
- `SET demo:keep alive` → `docker compose restart redis` → `GET demo:keep`이 `"alive"`면 AOF가 동작하는 것이다.
- **키 이름:** 테이블이 없으니 `용도:식별자`(`refresh:newlec`, `cache:menus`, `ratelimit:login:1.2.3.4`) 형태로 접두어를 붙인다. 콜론은 관례지만 GUI 도구가 폴더처럼 보여 준다.
- `KEYS *`는 모든 키를 훑는 동안 다른 요청을 받지 못한다. 운영에서는 `SCAN`을 쓴다.

## 9. 스프링에서 Redis 쓰기 — RefreshTokenStore

### 1) 의존성과 설정

```groovy
implementation 'org.springframework.boot:spring-boot-starter-data-redis'   // Spring Data Redis + Lettuce
```

```yaml
spring:
  data:
    redis:
      host: ${REDIS_HOST:localhost}   # compose 안에서는 REDIS_HOST=redis
      port: ${REDIS_PORT:6379}
```

`${REDIS_HOST:localhost}`는 환경 변수가 있으면 그 값, 없으면 localhost다. compose 안에서는 `redis:6379`, IDE에서 스프링만 띄우면 `localhost:6379`로 붙는다. 이것만으로 스프링이 `StringRedisTemplate` 빈을 만들어 준다.

### 2) StringRedisTemplate
키와 값을 문자열로 다룬다. `RedisTemplate<Object, Object>`는 기본 직렬화가 자바 직렬화라 redis-cli에서 키가 깨져 보인다.

| Redis 명령 | 자바 |
| --- | --- |
| `SET key value EX ttl` | `redis.opsForValue().set(key, value, Duration)` |
| `GET key` | `redis.opsForValue().get(key)` |
| `DEL key` | `redis.delete(key)` |
| `EXISTS key` | `redis.hasKey(key)` |
| `INCR key` | `redis.opsForValue().increment(key)` |

`opsForValue()`는 문자열 값 명령 묶음이고, 리스트는 `opsForList()`, 해시는 `opsForHash()`다.

### 3) 바뀐 RefreshTokenStore

```java
@Component
public class RefreshTokenStore {

    private static final String KEY_PREFIX = "refresh:";

    private final StringRedisTemplate redis;
    private final Duration ttl;

    public RefreshTokenStore(StringRedisTemplate redis, JwtProperties jwtProperties) {
        this.redis = redis;
        // 토큰 자체의 만료 시간과 같게 둔다
        this.ttl = Duration.ofMillis(jwtProperties.getRefreshTokenExpiration());
    }

    /** SET refresh:{username} {token} EX {ttl} — 같은 사용자의 이전 토큰은 덮어써진다 */
    public void save(String username, String refreshToken) {
        redis.opsForValue().set(key(username), refreshToken, ttl);
    }

    /** GET 과 비교. 로그아웃했거나 다른 기기에서 다시 로그인했으면 false */
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

- 메서드 세 개(`save`, `matches`, `remove`)의 이름과 시그니처가 그대로라 **`AuthService`는 한 줄도 바뀌지 않는다.** 저장소를 클래스로 분리해 둔 덕이다.
- 다시 로그인하면 키가 덮어써져 이전 토큰은 자동으로 무효가 된다(Map일 때와 같은 동작).
- TTL을 토큰 만료와 같게 두니, Map일 때 로그아웃하지 않은 사용자의 토큰이 메모리에 영원히 남던 문제가 사라진다.
- 키가 없으면 `get()`이 null이고 `equals(null)`은 false라 null 처리 코드가 필요 없다.

의존성이 바뀌었으니 이번만 `docker compose up -d --build backend`.

## 10. Redis가 꺼져 있으면 — 503

Redis를 끄고 로그인하면 `set()`이 연결 타임아웃 예외를 던지고, 잡는 곳이 없어 500과 스택 트레이스가 나간다. 스프링 데이터 계열(Redis, JPA, JDBC) 예외는 모두 `DataAccessException`을 상속하므로 전역 예외 처리에 하나를 더한다.

```java
@ExceptionHandler(DataAccessException.class)
@ResponseStatus(HttpStatus.SERVICE_UNAVAILABLE)
public ErrorResponse handleDataAccess(DataAccessException e, HttpServletRequest request) {
    return ErrorResponse.of(
            HttpStatus.SERVICE_UNAVAILABLE.value(),
            HttpStatus.SERVICE_UNAVAILABLE.name(),
            "일시적으로 요청을 처리할 수 없습니다. 잠시 후 다시 시도해 주세요.",
            request.getRequestURI());
}
```

- **503 Service Unavailable:** 사용자 잘못이 아니라 서버가 지금 일을 못 하는 상태다. 500(서버 버그)과 구분되고 "잠시 후 다시"라는 뜻이 담긴다.
- 메시지에 내부 사정(타임아웃, 호스트 이름)을 쓰지 않는다. 로그에만 남긴다.
- 다음 단계에서 PostgreSQL이 꺼졌을 때도 같은 핸들러가 받는다.

## 11. 확인하기

각 단계 뒤에 `docker compose exec redis redis-cli <명령>`으로 키를 들여다보는 것이 요점이다.

| # | 하는 일 | 기대 | redis-cli로 볼 것 |
| --- | --- | --- | --- |
| 1 | 로그인 | 200 | `KEYS refresh:*`, `GET`이 응답의 refreshToken과 같음, `TTL` ≈ 1209600 |
| 2 | 그 토큰으로 재발급 | 200 | 키 그대로 |
| 3 | 엉터리 토큰으로 재발급 | 401 유효하지 않음 | — |
| 4 | 다시 로그인 후 1번 토큰으로 재발급 | 401 이미 만료 처리됨 | `GET`이 새 토큰 |
| 5 | 로그아웃 | 204 | `EXISTS` → 0 |
| 6 | 로그인 → `restart redis` → 재발급 | 200 | `EXISTS` → 1 (AOF) |
| 7 | 로그인 → `restart backend` → 재발급 | **200** | 처음에 401이던 것 |
| 8 | `stop redis` → 로그인 | 503 ErrorResponse | — |
| 9 | 그 상태에서 메뉴 조회 | 200 | 메뉴는 Redis와 무관 |

**7번이 목표다.** 서버가 재시작돼도, 여러 대여도, 같은 Redis를 보는 한 리프레시 토큰은 살아 있다. 프론트엔드 코드는 바꿀 것이 없다. 프론트는 스프링이 토큰을 어디에 두는지 모른다.

## 12. 주의할 것과 정리

1. **컨테이너 안과 밖의 호스트 이름이 다르다.** 컨테이너 안에서는 `backend:8080`, `redis:6379`, 호스트의 브라우저·Postman에서는 `localhost:3000`, `localhost:8080`, `localhost:6379`다. 그래서 설정을 `${REDIS_HOST:localhost}`처럼 환경 변수로 받고 기본값을 둔다. compose에서 가장 자주 걸리는 지점이다.
2. **로그인이 Redis에 의존하게 됐다.** Redis가 꺼지면 로그인·재발급·로그아웃만 503이고, 메뉴 조회와 이미 받은 액세스 토큰(30분)은 멀쩡하다. 액세스 토큰을 저장하지 않는 설계 덕이다.
3. **`down -v`는 토큰도 지운다.** DB만 초기화하려면 `docker volume rm ncafe_postgres_data`처럼 볼륨 이름을 지정한다(`docker volume ls`로 확인).
4. **IDE에서 스프링만 띄우고 싶을 때:** `docker compose stop backend`로 컨테이너 백엔드만 내리고 IDE에서 실행한다. Redis·PostgreSQL은 호스트 포트(6379, 5432)로 열려 있으니 localhost 기본값으로 붙는다. 이때 프론트 컨테이너는 `backend:8080`을 찾으므로 프론트도 호스트에서 `npm run dev`로 띄운다.
5. **더 조일 수 있는 것:** 재발급마다 새 리프레시 토큰을 주고 이전 것을 무효화하는 회전(rotation), 로그아웃한 액세스 토큰을 남은 수명만큼 막는 블랙리스트(`SET blacklist:{jti} 1 EX 남은초`).

| 데이터 | 저장소 | 이유 |
| --- | --- | --- |
| 액세스 토큰 | 저장 안 함 | 서명만 검증 (STATELESS) |
| 리프레시 토큰 | Redis, TTL 14일 | 폐기가 필요해 서버가 기억해야 하고, 수명이 있고, 키로 바로 찾는다 |
| 메뉴, 사용자 | PostgreSQL (다음 단계) | 오래 남기고, 조건으로 검색하고, 관계가 있다 |

### 이번 단계에서 추가·수정된 파일
- 루트(추가): `compose.yaml`, `compose.override.yaml`, `.env.example`, `docker/adminer/login-servers.php`
- 백엔드(추가): `Dockerfile`, `.dockerignore` / (수정): `build.gradle`, `application.yml`, `RefreshTokenStore.java`, `GlobalExceptionHandler.java`
- 프론트엔드(추가): `Dockerfile`, `.dockerignore` / (수정): `next.config.ts`

### 다음 단계
서버 배포 + HTTPS([[044_서버 배포와 HTTPS — nginx 리버스 프록시, mkcert, certbot, 팀별 서브도메인 참고자료]]) → GitHub Actions CI/CD → 블루그린 배포 → JPA로 PostgreSQL 연결(`Menu` 엔티티, `data.sql`).
