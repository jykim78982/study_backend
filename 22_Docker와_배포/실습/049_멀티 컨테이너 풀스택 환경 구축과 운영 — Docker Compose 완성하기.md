---
tags: [Docker, DockerCompose, Nginx, 리버스프록시, Nextjs, 스프링부트, PostgreSQL, healthcheck, override, mkcert, HTTPS, 백업, 실습]
---

> 🔗 관련 노트: [[041_Nginx, Next.js, Spring Boot, PostgreSQL을 하나로 묶는 도커 컴포즈 실전 구축기 참고자료]] · [[038_도커 컴포즈로 스프링 부트와 PostgreSQL 한 번에 구동하기 참고자료]] · [[097_Docker Compose — 여러 컨테이너를 하나의 네트워크로 묶어 실행하기]] · [[043_Docker로 팀 공용 PostgreSQL 개발 DB 만들기]]

# 멀티 컨테이너 풀스택 환경 구축과 운영 — Docker Compose 완성하기

**대상**: 도커 기본 명령어와 컨테이너 개념을 익히고 멀티 컨테이너 서비스 구축을 시작하려는 개발자

**목표**: Docker Compose를 활용해 풀스택 서비스(프론트, 백엔드, DB, Nginx)를 연결하고 개발 및 운영 환경까지 구축한다

**완성물**: Nginx 프록시, HTTPS 보안, 개발용 라이브 리로드, 운영용 자원 제한 및 백업 스크립트가 적용된 `ncafe/` 시스템

**준비물**

이 따라하기를 진행하려면 아래 도구가 설치되어 있어야 한다.

- Docker Desktop (또는 Docker Engine 및 docker compose plugin)
- mkcert (HTTPS 사설 인증서 생성용)

> 이 노트는 수업 자료를 **실습용 스타터(`ncafe-starter.zip`)의 실제 소스와 맞춰 본** 결과다. 원문 코드를 그대로 쓰면 스타터와 맞지 않아 **2단계(API가 전부 실패), 3단계(빌드 실패), 4단계(API 실패)** 에서 막힌다. 각 단계에 바로잡은 코드를 적어 두었고, 맨 끝 「최종 파일 모음」에 완성본을 모았다.

> **추가 설명 — 스타터에 들어 있는 것**: 프론트·백엔드 소스와 각각의 Dockerfile은 완성되어 있고, **Compose 설정만 비어 있다.** 실습 내내 참고할 사실은 다음과 같다.
>
> | 항목 | 내용 |
> |---|---|
> | 프론트엔드 | Next.js 16, 3000 포트. Dockerfile은 `deps` → `build` → `runner` 3단계, `output: "standalone"`으로 `node server.js` 실행 |
> | 백엔드 | Spring Boot 4.1 + JPA + Security(JWT), JDK 25, 8080 포트. Dockerfile은 `build`(JDK) → 실행(JRE) 2단계 |
> | API 경로 | 모든 컨트롤러가 **`/api`로 시작**한다 (`/api/user/menus`, `/api/member/auth/login`, `/api/admin/...`) |
> | 프론트의 API 호출 | 브라우저는 항상 **같은 출처의 `/api/...`** 로만 부른다(`app/_lib/api-client.ts`). Nginx 없이 띄울 때는 Next.js가 `/api`를 `API_PROXY_TARGET`(빌드 시 기본 `http://backend:8080`)으로 넘겨 준다(`next.config.ts`의 rewrites) |
> | 백엔드 환경 변수 | `DB_URL`, `DB_USERNAME`, `DB_PASSWORD`, `DDL_AUTO`, `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` (전부 기본값이 있음) |
> | 프록시 대비 | `server.forward-headers-strategy=framework`가 이미 켜져 있다 |
> | 관리자 계정 | 백엔드가 처음 뜰 때 자동 생성. 기본 `admin@ncafe.local` / `admin1234` |
> | 테이블 | 백엔드가 기동하면서 만든다(`DDL_AUTO=update`). 처음엔 메뉴가 비어 있으므로 `/admin`에서 카테고리·메뉴를 등록해야 화면에 나온다 |
> | `.gitignore` | 루트에 `.env`, `*.pem`, `backups/`가 이미 들어 있다 |

## 1단계: 3개 서비스 묶기와 실행 순서 제어

독립된 3개 컨테이너(Next.js, Spring Boot, PostgreSQL)를 단일 네트워크로 묶는다. DB 준비 상태를 확인 후 백엔드가 실행되도록 순서를 제어하고 환경변수로 비밀번호를 분리한다.

**사전준비**

상단에 포함된 첨부파일(`ncafe-starter.zip`)을 다운로드해 압축을 해제하고 다음 내용을 이어가도록 하자.

```
ncafe/
├── .gitignore
├── README.md
├── backend/      Spring Boot 4 + JPA. Dockerfile 포함
└── frontend/     Next.js 16. Dockerfile 포함
```

> **추가 설명 — 폴더 이름이 프로젝트명이 된다**: Compose는 `docker-compose.yml`이 있는 폴더 이름(`ncafe`)을 프로젝트명으로 써서 볼륨·네트워크 이름 앞에 붙인다(`ncafe_postgres_data`, `ncafe_default`). 팀원끼리 같은 이름을 쓰는 것이 좋다. 또 **IDE에서 백엔드를 띄워 둔 상태**라면 이후 단계에서 8080 포트가 겹칠 수 있으니 하나만 실행한다.

**1-1. 환경변수 파일 작성**

프로젝트 루트 폴더에 `.env` 파일을 만들고 DB 접속 정보를 정의한다.

파일: `.env`

```bash
POSTGRES_DB=ncafedb
POSTGRES_USER=ncafeuser
POSTGRES_PASSWORD=ncafepassword123
```

> **추가 설명 — 백엔드 비밀값도 같이 넣어 둔다**: 스타터 백엔드는 JWT 서명 키와 관리자 계정도 환경 변수로 받는다. 기본값이 개발용이라 지금은 없어도 동작하지만, 5단계(운영)에서는 반드시 바꿔야 하므로 처음부터 `.env`에 자리를 만들어 두면 편하다.
>
> ```bash
> JWT_SECRET=ncafe-local-secret-key-at-least-32-bytes-long!!
> ADMIN_EMAIL=admin@ncafe.local
> ADMIN_PASSWORD=admin1234
> ```
>
> `JWT_SECRET`은 **32바이트 이상**이어야 한다(서명 알고리즘 HS256의 최소 길이).

**1-2. 기본 docker-compose.yml 작성**

파일: `docker-compose.yml`

```yaml
version: '3.8'

services:
  db:
    image: postgres:17
    container_name: ncafe-db
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    container_name: ncafe-backend
    restart: always
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://db:5432/${POSTGRES_DB}
      SPRING_DATASOURCE_USERNAME: ${POSTGRES_USER}
      SPRING_DATASOURCE_PASSWORD: ${POSTGRES_PASSWORD}
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build: ./frontend
    container_name: ncafe-frontend
    restart: always
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8080
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

> 원문 바로잡기 — `frontend`의 `NEXT_PUBLIC_API_URL: http://backend:8080`은 **아무 효과가 없으므로 뺀다.** 스타터 프론트 코드는 이 변수를 읽지 않고, 항상 같은 출처의 `/api/...`로 호출한다. 게다가 `NEXT_PUBLIC_` 변수는 **빌드할 때** 브라우저용 코드에 박히는 값이라 실행 시 `environment`로 넣어도 반영되지 않는다. 설령 반영되더라도 브라우저는 사용자 PC에서 돌기 때문에 `backend`라는 내부 이름을 찾지 못한다. 첫 줄의 `version: '3.8'`도 현재 Compose에서는 무시되고 경고만 띄우므로 지운다.

> **추가 설명 — `SPRING_DATASOURCE_*`가 스타터에서도 통하는 이유**: 스타터의 `application.properties`는 `spring.datasource.url=${DB_URL:jdbc:postgresql://localhost:5432/ncafe}`처럼 `DB_URL`이라는 변수를 기다린다. 그런데 환경 변수 `SPRING_DATASOURCE_URL`은 스프링이 **속성 `spring.datasource.url`로 직접** 읽고, 환경 변수가 properties 파일보다 우선순위가 높아서 위 줄 자체를 덮어쓴다. 그래서 원문처럼 써도 동작한다. 스타터가 의도한 이름으로 맞추고 싶다면 아래처럼 써도 결과는 같다.
>
> ```yaml
>     environment:
>       DB_URL: jdbc:postgresql://db:5432/${POSTGRES_DB}
>       DB_USERNAME: ${POSTGRES_USER}
>       DB_PASSWORD: ${POSTGRES_PASSWORD}
>       JWT_SECRET: ${JWT_SECRET:-ncafe-dev-only-secret-key-change-me-in-production!}
>       ADMIN_EMAIL: ${ADMIN_EMAIL:-admin@ncafe.local}
>       ADMIN_PASSWORD: ${ADMIN_PASSWORD:-admin1234}
> ```
>
> `${변수:-기본값}`은 `.env`에 값이 없거나 비어 있으면 `:-` 뒤의 값을 쓰라는 Compose 문법이다. 스타터 README가 1단계 과제로 요구하는 것이 이것이다.

> **추가 설명 — 1단계에서는 브라우저 → 프론트 → 백엔드로 간다**: `backend`에는 `ports`가 없어 호스트에서 `localhost:8080`으로는 들어갈 수 없다. 그런데도 화면에서 API가 동작하는 것은 스타터의 **Next.js rewrites** 덕분이다. 브라우저가 `localhost:3000/api/user/menus`를 부르면, 프론트 컨테이너 안의 Next.js 서버가 그 요청을 내부 네트워크로 `http://backend:8080/api/user/menus`에 대신 전달한다. 이 주소는 프론트 Dockerfile의 `ARG API_PROXY_TARGET=http://backend:8080`으로 **빌드할 때** 정해진다.
>
> ```
> 브라우저 ─:3000─▶ [frontend: Next.js] ─rewrites /api/*─▶ [backend:8080] ─▶ [db:5432]
> ```

> **추가 설명 — `postgres:18`로 올릴 때는 볼륨 경로가 다르다**: 이 실습은 17을 쓴다. PostgreSQL 공식 이미지 18부터는 데이터 위치가 바뀌어 볼륨을 `/var/lib/postgresql`(뒤의 `/data` 없이)에 연결하도록 안내한다. 버전만 올리고 경로를 그대로 두면 데이터가 볼륨에 저장되지 않을 수 있다.

**1-3. 서비스 실행 및 상태 확인**

VSCode 터미널에서 아래 명령을 실행한다.

```bash
docker compose up -d --build
```

> **추가 설명 — 첫 빌드는 오래 걸린다**: 백엔드는 Gradle 배포판(약 100MB+)과 의존성을, 프론트는 `npm ci`로 패키지를 받으므로 첫 빌드에 수 분이 걸린다. 진행 상황은 `-d` 없이 실행하거나 `docker compose logs -f backend`로 볼 수 있다. 백엔드는 컨테이너가 뜬 뒤에도 스프링 기동에 10~30초가 더 걸린다.

**✅ 확인**

- `docker compose ps` 실행 시 3개 컨테이너(`ncafe-db`, `ncafe-backend`, `ncafe-frontend`)의 상태가 모두 running 또는 healthy로 표시된다.

> **추가 설명 — 실제로 동작하는지까지 확인하기**: 상태가 `Up`이어도 백엔드가 DB 접속에 실패해 재시작을 반복하는 중일 수 있다. 아래 세 가지로 확인한다.
>
> ```bash
> docker compose ps                                     # ncafe-db 는 Up (healthy)
> curl http://localhost:3000/menus                      # Next.js 페이지 HTML (200)
> curl http://localhost:3000/api/user/categories        # [] ← 프론트를 거쳐 백엔드가 준 JSON
> docker compose logs backend | grep "관리자 계정"       # 관리자 계정을 생성했습니다: admin@ncafe.local
> ```
>
> `/api/user/categories`가 `[]`(빈 배열)로 오면 브라우저 → 프론트 → 백엔드 → DB가 모두 연결된 것이다. 윈도우 PowerShell에서는 `curl` 대신 `curl.exe`를 쓰거나 브라우저 주소창에 넣는다.

**🎓 newlec 쌤의 코멘트**: 단순히 `depends_on`만 작성하면 DB 컨테이너만 먼저 켜질 뿐, PostgreSQL 프로세스가 포트를 열고 요청을 받을 준비가 되었는지는 보장하지 않는다. 이 때문에 백엔드가 실행 시점에 DB 연결에 실패하며 종료될 수 있다. `healthcheck` 속성과 `condition: service_healthy`를 조합해야 완벽한 실행 순서 제어가 가능하다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| 백엔드 컨테이너가 계속 재시작됨 | DB 준비 완료 전에 연결 시도 | `docker-compose.yml`의 `healthcheck` 조건 및 사용자명 오타 확인 |
| `${POSTGRES_DB}` 값이 적용 안 됨 | `.env` 파일의 위치가 잘못됨 | `docker-compose.yml`과 같은 위치에 `.env` 파일 작성 |
| `password authentication failed for user "ncafeuser"` | `.env`의 계정·비밀번호를 **바꾸기 전에** 이미 볼륨이 만들어짐. `POSTGRES_*`는 볼륨이 처음 생길 때만 적용됨 | 데이터가 필요 없으면 `docker compose down -v`로 볼륨까지 지우고 다시 `up` |
| `The "POSTGRES_DB" variable is not set` 경고 | `.env`가 없거나 다른 폴더에서 명령을 실행함 | `ncafe/` 루트에서 실행, `docker compose config`로 치환 결과 확인 |

**📝 이 단계의 핵심**

- `.env` 파일을 활용해 중요한 비밀번호와 설정 정보를 소스코드와 분리한다.
- `healthcheck`를 통해 컨테이너 내부 서비스의 실제 준비 상태를 확인하고 부팅 순서를 제어한다.

## 2단계: Nginx 리버스 프록시로 입구 통합

개별 포트로 접근하던 방식을 Nginx 리버스 프록시 하나로 통합한다. 사용자는 80번 포트 하나로 접속하며, Nginx가 경로에 따라 내부 컨테이너로 요청을 전달한다.

**2-1. Nginx 설정 파일 작성**

프로젝트 내 `nginx/default.conf` 파일을 생성한다.

파일: `nginx/default.conf`

```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api/ {
        proxy_pass http://backend:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

> 원문 바로잡기 — **`proxy_pass http://backend:8080/;` 끝의 `/` 때문에 모든 API가 실패한다.** `proxy_pass` 주소 뒤에 경로(`/`)가 붙어 있으면 Nginx는 `location`에 걸린 부분(`/api/`)을 **그 경로로 바꿔서** 넘긴다. 그래서 브라우저의 `/api/user/menus`가 백엔드에는 `/user/menus`로 들어간다. 스타터 백엔드는 모든 컨트롤러가 `/api/...`로 시작하고, `SecurityConfig`가 목록에 없는 경로를 `anyRequest().denyAll()`로 막으므로 API가 전부 401·403·404로 실패한다. 끝의 `/`를 지워 경로를 **그대로** 넘긴다.
>
> | `proxy_pass` | 브라우저 요청 | 백엔드가 받는 경로 | 스타터에서 |
> |---|---|---|---|
> | `http://backend:8080/` (원문) | `/api/user/menus` | `/user/menus` | ✗ 실패 |
> | `http://backend:8080` (수정) | `/api/user/menus` | `/api/user/menus` | ✓ |
>
> 원문 방식은 백엔드 컨트롤러가 `/user/menus`처럼 **`/api` 없이** 만들어져 있을 때 쓰는 설정이다.

> **추가 설명 — 컨테이너를 다시 만들어도 502가 나지 않게 (resolver)**: `proxy_pass http://backend:8080;`처럼 이름을 직접 적으면 Nginx는 **시작할 때 한 번** IP를 찾아 기억한다. 이후 `docker compose up -d --build backend`로 백엔드만 새로 만들면 IP가 바뀌어 Nginx가 옛 주소로 보내다 **502 Bad Gateway**가 난다. 또 Nginx가 뜰 때 백엔드가 아직 없으면 `host not found in upstream` 오류로 Nginx 자체가 켜지지 않는다. 도커 내부 DNS(`127.0.0.11`)를 `resolver`로 지정하고 주소를 **변수**에 담으면 요청 때마다 최신 IP를 찾는다. 스타터 README의 2단계 과제("컨테이너 재생성에도 502가 안 나는 resolver 설정")가 이것이다.
>
> ```nginx
> server {
>     listen 80;
>     server_name localhost;
>
>     resolver 127.0.0.11 valid=10s;
>
>     location /api/ {
>         set $backend http://backend:8080;
>         proxy_pass $backend;                  # 변수 + 경로 없음 → 요청 경로 그대로 전달
>         proxy_set_header Host $host;
>         proxy_set_header X-Real-IP $remote_addr;
>         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
>         proxy_set_header X-Forwarded-Proto $scheme;
>     }
>
>     location / {
>         set $frontend http://frontend:3000;
>         proxy_pass $frontend;
>         proxy_set_header Host $host;
>         proxy_set_header X-Real-IP $remote_addr;
>         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
>         proxy_set_header X-Forwarded-Proto $scheme;
>     }
> }
> ```
>
> 백엔드에는 `server.forward-headers-strategy=framework`가 이미 켜져 있어서 `X-Forwarded-*` 헤더로 원래 사용자 IP와 프로토콜을 복원한다.

**2-2. docker-compose.yml에 Nginx 서비스 추가**

`docker-compose.yml` 파일의 `services` 항목 하단에 `proxy`를 추가하고 외부 포트 노출은 Nginx만 담당하도록 설정한다.

파일: `docker-compose.yml`

```yaml
  proxy:
    image: nginx:1.27
    container_name: ncafe-proxy
    restart: always
    ports:
      - "80:80"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - frontend
      - backend
```

기존 `frontend` 서비스에 있던 `ports: - "3000:3000"` 설정은 삭제하거나 주석 처리한다. 외부 노출을 차단하여 보안을 강화한다.

> **추가 설명 — 들여쓰기 위치**: `proxy:`는 `db:`, `backend:`, `frontend:`와 **같은 깊이**(공백 2칸)로, 맨 아래 `volumes:`(공백 0칸) **위에** 넣는다. `volumes:` 아래에 넣으면 볼륨 이름으로 해석되어 `volumes.proxy Additional property image is not allowed` 같은 오류가 난다.

**2-3. 변경사항 적용**

```bash
docker compose up -d
```

**✅ 확인**

- 브라우저에서 `http://localhost` 접속 시 Next.js 메인 화면이 정상 출력된다.
- 브라우저에서 `http://localhost/api/health` 접속 시 Spring Boot의 응답이 출력된다.

> 원문 바로잡기 — 스타터 백엔드에는 **`/api/health` 경로가 없다.** `SecurityConfig`에 `/actuator/health`가 허용되어 있긴 하지만 actuator 의존성이 들어 있지 않고, 경로도 `/api/`로 시작하지 않아 Nginx가 백엔드로 보내지 않는다. 대신 누구나 호출할 수 있는 실제 API로 확인한다.
>
> - `http://localhost` → "커피 한 잔, 함께 몰입하는 시간" 메인 화면
> - `http://localhost/api/user/categories` → `[]` (JSON)
> - `http://localhost/login`에서 `admin@ncafe.local` / `admin1234`로 로그인 → `/admin`에서 카테고리·메뉴 등록 → `http://localhost/menus`에 표시
> - `http://localhost:3000` → **접속 안 됨** (프론트 포트를 닫았으므로 정상)

**🎓 newlec 쌤의 코멘트**: 리버스 프록시를 도입하면 클라이언트는 내부 서비스들의 포트 번호(3000, 8080 등)를 몰라도 된다. Nginx가 Docker internal DNS를 사용해 서비스 이름(`frontend`, `backend`)으로 내부 통신을 처리하므로, 컨테이너 IP가 바뀌어도 설정 파일을 수정할 필요가 없다.

> **추가 설명 — "설정 파일 수정"은 필요 없지만 "다시 찾기"는 필요하다**: 코멘트처럼 서비스 이름으로 적으니 IP가 바뀌어도 설정 파일은 그대로 둔다. 하지만 이름→IP 변환을 **언제** 하느냐가 문제다. 원문 설정은 시작할 때 한 번만 찾으므로, 백엔드만 다시 만든 뒤에는 `docker compose restart proxy`로 Nginx를 다시 켜야 한다. 위의 `resolver` + 변수 방식이면 그것도 필요 없다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| 502 Bad Gateway 에러 | Nginx가 지정한 서비스 이름을 찾을 수 없음 | `default.conf` 내 `proxy_pass` 주소의 오타 확인 (`http://frontend:3000`) |
| 포트 충돌 에러 (`bind: address already in use`) | 호스트 80번 포트를 다른 프로그램이 사용 중 | 기존 80 포트 사용 프로세스 종료 또는 Nginx 매핑 포트 변경 |
| 화면은 뜨는데 API만 401·403·404 | `proxy_pass` 끝의 `/`로 `/api`가 잘려서 전달됨 | `proxy_pass http://backend:8080;` (끝 `/` 제거) |
| 백엔드만 재빌드한 뒤 502 | Nginx가 옛 IP를 기억함 | `resolver` + 변수 방식으로 바꾸거나 `docker compose restart proxy` |
| 처음 `up` 직후 잠깐 502 | 스프링이 아직 기동 중 | 10~30초 뒤 새로고침, `docker compose logs -f backend`로 `Started NcafeApplication` 확인 |

> **추가 설명 — 윈도우에서 80번을 쓰는 프로그램 찾기**: IIS, 다른 Nginx·Apache, Skype 구버전 등이 80을 잡고 있을 수 있다. PowerShell에서 `netstat -ano | findstr :80`으로 PID를 찾고 작업 관리자에서 확인한다. 끌 수 없다면 `"8080:80"`처럼 호스트 포트를 바꾸고 `http://localhost:8080`으로 접속한다.

**📝 이 단계의 핵심**

- Docker Compose 네트워크 내부에서는 서비스명이 도메인 주소 역할을 한다.
- Nginx를 앞단에 두어 프론트엔드와 백엔드의 접근 창구를 단일화한다.

## 3단계: 개발 환경 분리와 라이브 리로드

소스코드 수정 시 매번 이미지를 다시 빌드하지 않도록 바인드 마운트 기반의 개발용 Compose 설정(`docker-compose.override.yml`)을 분리한다.

**3-1. 개발 전용 설정 파일 생성**

파일: `docker-compose.override.yml`

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      target: dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    environment:
      NODE_ENV: development
    command: npm run dev

  backend:
    volumes:
      - ./backend:/app
      - ~/.m2:/root/.m2
    command: ./gradlew bootRun
```

> 원문 바로잡기 — 이 파일은 스타터와 맞지 않아 **그대로 실행하면 빌드부터 실패한다.**
>
> | 원문 | 스타터에서 일어나는 일 | 고칠 점 |
> |---|---|---|
> | `frontend`의 `target: dev` | 프론트 Dockerfile에는 `deps`, `build`, `runner` 단계만 있어 `target stage "dev" could not be found` 빌드 오류 | `target: deps` (node_modules가 설치된 단계) |
> | `backend`에 `target` 없음 | 마지막 단계(JRE만 있는 실행 이미지)가 쓰인다. JRE에는 컴파일러가 없어 `./gradlew bootRun`이 Gradle 툴체인(JDK 25)을 찾지 못하고 실패한다. 실행 이미지는 `USER app`(일반 사용자)이라 권한 문제도 생긴다 | `target: build` (JDK 25가 있는 빌드 단계, root 사용자) |
> | `~/.m2:/root/.m2` | `.m2`는 **Maven** 캐시 폴더다. 스타터는 **Gradle** 프로젝트라 쓰이지 않는다 | Gradle 캐시(`/root/.gradle`)를 이름 있는 볼륨으로 보존 |
> | `ports` 없음 | 개발 서버에 직접 붙어 볼 수 없다 | 필요하면 `"3000:3000"`, `"8080:8080"` 추가 |
>
> 바로잡은 파일은 다음과 같다.
>
> ```yaml
> services:
>   frontend:
>     build:
>       context: ./frontend
>       target: deps               # npm ci 까지 끝난 단계
>     command: npm run dev         # next dev (파일 변경 감지 + 화면 자동 갱신)
>     environment:
>       NODE_ENV: development
>       API_PROXY_TARGET: http://backend:8080   # 3000으로 직접 붙을 때 /api 를 백엔드로
>       WATCHPACK_POLLING: "true"                # 윈도우 폴더 바인드 마운트에서 변경 감지용
>     ports:
>       - "3000:3000"
>     volumes:
>       - ./frontend:/app
>       - /app/node_modules
>       - /app/.next
>
>   backend:
>     build:
>       context: ./backend
>       target: build              # JDK 25 + Gradle wrapper 가 있는 단계
>     command: ./gradlew bootRun --no-daemon
>     ports:
>       - "8080:8080"
>     volumes:
>       - ./backend:/app
>       - /app/build               # 호스트의 build/ 결과물과 섞이지 않게
>       - /app/.gradle
>       - gradle_cache:/root/.gradle
>
> volumes:
>   gradle_cache:
> ```
>
> 마지막 `volumes: gradle_cache:`는 기본 파일의 `postgres_data`와 합쳐진다.

> **추가 설명 — 익명 볼륨 세 줄의 역할**: `./frontend:/app`으로 폴더를 통째로 덮으면 이미지 안에서 만든 폴더들도 내 PC 폴더로 가려진다. 하위 경로에 이름 없는 볼륨을 걸면 그 자리만 컨테이너 쪽 내용이 유지된다.
>
> | 줄 | 지키는 것 |
> |---|---|
> | `/app/node_modules` | 이미지에서 `npm ci`로 설치한 **리눅스(alpine)용** 패키지. 윈도우에서 설치한 `node_modules`는 네이티브 바이너리가 달라 컨테이너에서 실패한다 |
> | `/app/.next` | 개발 서버의 빌드 캐시. 호스트와 섞이면 느려지고 꼬인다 |
> | `/app/build`, `/app/.gradle` (백엔드) | 컨테이너 안 Gradle 빌드 결과물. 호스트에서 IDE로 빌드한 결과와 섞이지 않게 한다 |

> **추가 설명 — 3000번을 다시 연 이유와 `API_PROXY_TARGET`**: 2단계에서 3000을 닫았지만, 개발 중에는 Nginx를 거치지 않고 개발 서버에 직접 붙는 것이 문제를 나눠 보기 좋다. 이때 `next.config.ts`의 rewrites가 `/api`를 넘길 곳이 필요한데, 개발 서버는 이 값을 **실행할 때** 읽는다(운영 이미지는 빌드할 때 고정). 설정하지 않으면 기본값 `http://localhost:8080`, 즉 **프론트 컨테이너 자신**으로 보내서 API가 실패한다. override 파일에만 넣으므로 운영에는 열리지 않는다.

**3-2. 개발 환경 실행 테스트**

별도의 파일 지정 없이 명령을 실행하면 Docker Compose가 `docker-compose.yml`과 `docker-compose.override.yml`을 자동으로 합쳐서 실행한다.

```bash
docker compose up -d
```

> **추가 설명 — 이번에는 `--build`가 필요하다**: override에서 `target`을 바꿨으므로 프론트·백엔드 이미지를 **다른 단계로** 새로 만들어야 한다. 처음 한 번은 `docker compose up -d --build`로 실행한다. 합쳐진 결과는 `docker compose config`로 미리 볼 수 있다.

**3-3. 코드 수정 및 핫 리로딩 확인**

`frontend/src/app/page.tsx` 파일의 텍스트를 일부 수정하고 저장한다.

> 원문 바로잡기 — 스타터에는 `src/` 폴더가 없다. 메인 화면 문구는 **`frontend/app/(user)/_components/Hero/Hero.tsx`** 에 있다(`app/(user)/page.tsx`는 `<Hero />`만 불러온다). 예를 들어 `커피 한 잔,`을 `커피 두 잔,`으로 바꾸고 저장한다.

**✅ 확인**

- 이미지를 다시 빌드(`--build`)하지 않아도 브라우저 화면이 실시간으로 새로고침되며 변경사항이 반영된다.

> **추가 설명 — Nginx(`http://localhost`)로 볼 때 자동 갱신이 안 된다면**: Next.js 개발 서버는 **웹소켓**(`/_next/webpack-hmr`)으로 "파일이 바뀌었다"를 브라우저에 알려 준다. Nginx는 기본 설정으로는 웹소켓 연결을 넘기지 않아서, `http://localhost:3000`에서는 바로 바뀌는데 `http://localhost`에서는 수동 새로고침을 해야 바뀐다. `location /`에 아래 세 줄을 넣으면 Nginx로 봐도 자동 갱신된다(운영에서도 웹소켓을 쓸 때 필요한 설정이라 넣어 둬도 해가 없다).
>
> ```nginx
>     location / {
>         ...
>         proxy_http_version 1.1;
>         proxy_set_header Upgrade $http_upgrade;
>         proxy_set_header Connection "upgrade";
>     }
> ```

> **추가 설명 — 백엔드는 "저장 즉시"가 아니다**: 프론트 개발 서버는 소스 파일을 직접 감시하지만, 자바는 **컴파일**을 거쳐야 한다. 컨테이너 안에서 컴파일해 주는 것이 없으므로 자바 파일을 고친 뒤에는 `docker compose restart backend`로 다시 띄워야 한다(`bootRun`이 시작할 때 다시 컴파일한다). 이미지를 다시 만들 필요는 없다는 점이 개발용 설정의 이점이다. 스타터에 `spring-boot-devtools`가 들어 있긴 하지만, devtools는 **컴파일된 클래스 파일**이 바뀌어야 재시작하므로 이 구성에서는 저절로 동작하지 않는다. 그래서 실무에서는 개발할 때 **DB(와 필요하면 프론트)만 컨테이너로 띄우고 백엔드는 IDE에서 실행**하는 경우가 많다. 그때는 IDE의 백엔드와 컨테이너 백엔드가 8080을 두고 겹치므로 `docker compose up -d db frontend proxy`처럼 서비스를 골라 띄운다.

**🎓 newlec 쌤의 코멘트**: `docker-compose.override.yml`은 기본 `docker-compose.yml`의 설정을 덮어쓰거나 추가한다. 개발용 설정에서 볼륨 바인드 마운트를 적용하면 컨테이너 내부로 파일이 즉시 동기화되어 소스 변경을 실시간으로 감지할 수 있다. 배포 시에는 override 파일을 제외하고 빌드된 전용 이미지만 사용한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `node_modules` 관련 실행 오류 | 호스트의 `node_modules`가 컨테이너 설정을 덮어씀 | override 파일에 익명 볼륨 `- /app/node_modules` 명시 확인 |
| `target stage "dev" could not be found` | 프론트 Dockerfile에 `dev` 단계가 없음 | `target: deps` |
| 백엔드 `bootRun` 실패 (툴체인·권한 오류) | JRE만 있는 실행 단계로 빌드됨 | 백엔드에 `target: build` 지정 후 `--build` |
| 파일을 저장해도 화면이 안 바뀜 (윈도우) | 윈도우 폴더를 WSL2 도커에 연결하면 파일 변경 알림이 전달되지 않음 | `WATCHPACK_POLLING: "true"`. 그래도 안 되면 프로젝트를 WSL 안(`\\wsl$\Ubuntu\home\...`)으로 옮기면 가장 확실하다 |
| `localhost:3000`은 되는데 `localhost`(Nginx)는 수동 새로고침 필요 | Nginx가 HMR 웹소켓을 넘기지 않음 | `location /`에 `Upgrade`/`Connection` 헤더 추가 |
| 3000으로 직접 접속하면 API만 실패 | 개발 서버의 rewrites가 `localhost:8080`(자기 자신)으로 보냄 | override에 `API_PROXY_TARGET: http://backend:8080` |

**📝 이 단계의 핵심**

- Compose는 `docker-compose.override.yml`을 자동으로 병합 처리한다.
- 개발 환경에서는 바인드 마운트를 사용하여 생산성을 높인다.

## 4단계: mkcert로 로컬 HTTPS 적용

mkcert를 활용해 로컬 전용 인증서를 생성하고, Nginx 설정에 TLS/SSL을 적용하여 운영 환경과 동일한 HTTPS 접속을 구현한다.

> **추가 설명 — mkcert 설치**: 윈도우는 PowerShell에서 `winget install FiloSottile.mkcert`(또는 `choco install mkcert`), macOS는 `brew install mkcert`. 인증서를 믿어야 하는 쪽은 **브라우저가 있는 PC**이므로, Docker를 WSL에서 돌리더라도 `mkcert -install`은 **윈도우 쪽**에서 실행해야 윈도우의 Chrome·Edge가 신뢰한다. Firefox는 자체 인증서 저장소를 쓰므로 설치 후 Firefox를 재시작해야 반영된다.

**4-1. 인증서 생성 및 저장**

프로젝트 루트에서 `certs` 폴더를 생성하고 로컬 도메인 인증서를 발급받는다.

```bash
mkdir certs
cd certs
mkcert -install
mkcert localhost 127.0.0.1 ::1
cd ..
```

> **추가 설명 — 무엇이 만들어지나**:
>
> | 명령 | 결과 |
> |---|---|
> | `mkcert -install` | 내 PC 전용 **사설 CA**(인증 기관)를 만들고 운영체제 신뢰 목록에 등록한다. PC당 한 번만 하면 된다 |
> | `mkcert localhost 127.0.0.1 ::1` | 그 CA로 서명한 인증서를 만든다. 이름이 3개라 `localhost+2.pem`(인증서), `localhost+2-key.pem`(개인키)로 저장된다 |
>
> `*-key.pem`은 **개인키**라 절대 공유하면 안 된다. 스타터 `.gitignore`에 `*.pem`이 이미 들어 있어 Git에 올라가지 않는다. CA의 개인키는 `mkcert -CAROOT`가 알려 주는 폴더에 있으며, 이것이 유출되면 남이 내 PC가 믿는 가짜 인증서를 만들 수 있으므로 역시 공유하지 않는다.

**4-2. Nginx SSL 설정 추가**

`nginx/default.conf` 파일 전체를 SSL 대응 설정으로 변경한다.

파일: `nginx/default.conf`

```nginx
server {
    listen 80;
    server_name localhost;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name localhost;

    ssl_certificate /etc/nginx/certs/localhost+2.pem;
    ssl_certificate_key /etc/nginx/certs/localhost+2-key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /api/ {
        proxy_pass http://backend:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

> 원문 바로잡기 — 여기서도 `/api/`의 `proxy_pass http://backend:8080/;` 끝 `/` 때문에 API가 실패한다(2단계와 같은 이유). 2단계에서 고친 `resolver` + 변수 방식과 3단계의 웹소켓 헤더까지 합친 443 블록은 다음과 같다.
>
> ```nginx
> server {
>     listen 443 ssl;
>     server_name localhost;
>
>     ssl_certificate     /etc/nginx/certs/localhost+2.pem;
>     ssl_certificate_key /etc/nginx/certs/localhost+2-key.pem;
>     ssl_protocols TLSv1.2 TLSv1.3;
>     ssl_ciphers HIGH:!aNULL:!MD5;
>
>     resolver 127.0.0.11 valid=10s;
>
>     location /api/ {
>         set $backend http://backend:8080;
>         proxy_pass $backend;
>         proxy_set_header Host $host;
>         proxy_set_header X-Real-IP $remote_addr;
>         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
>         proxy_set_header X-Forwarded-Proto https;
>     }
>
>     location / {
>         set $frontend http://frontend:3000;
>         proxy_pass $frontend;
>         proxy_set_header Host $host;
>         proxy_set_header X-Real-IP $remote_addr;
>         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
>         proxy_set_header X-Forwarded-Proto https;
>         proxy_http_version 1.1;
>         proxy_set_header Upgrade $http_upgrade;
>         proxy_set_header Connection "upgrade";
>     }
> }
> ```

> **추가 설명 — HTTPS는 Nginx에서 끝난다**: 브라우저↔Nginx 구간만 암호화되고, Nginx↔프론트·백엔드는 내부 네트워크라 그대로 http다(SSL 종료). 그래서 인증서는 Nginx에만 있으면 된다. 대신 백엔드는 원래 요청이 https였다는 것을 `X-Forwarded-Proto https` 헤더로 알게 되고, 스타터의 `server.forward-headers-strategy=framework` 설정이 이 헤더를 믿어서 리다이렉트·URL 생성 시 `https://`를 쓴다.

**4-3. docker-compose.yml 수정**

`proxy` 서비스에 443 포트와 인증서 볼륨 마운트를 추가한다.

파일: `docker-compose.yml`

```yaml
  proxy:
    image: nginx:1.27
    container_name: ncafe-proxy
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - frontend
      - backend
```

**4-4. 설정 적용**

```bash
docker compose up -d
```

> **추가 설명 — 설정 파일만 바꿨을 때**: `docker-compose.yml`의 `ports`·`volumes`가 바뀌었으므로 `up -d`가 `proxy` 컨테이너를 새로 만든다. 이후 `default.conf`만 고칠 때는 컨테이너를 다시 만들 필요 없이 아래처럼 검사 후 다시 읽게 하면 된다.
>
> ```bash
> docker compose exec proxy nginx -t          # 문법 검사 (인증서 경로 오류도 여기서 잡힘)
> docker compose exec proxy nginx -s reload   # 무중단 재적용
> ```

**✅ 확인**

- 브라우저에서 `http://localhost` 접속 시 `https://localhost`로 자동으로 리다이렉트된다.
- 주소창 옆에 자물쇠 아이콘이 표시되며 보안 경고 없이 접속된다.

> **추가 설명 — API와 로그인까지 확인**: `https://localhost/api/user/categories`가 JSON으로 오고, `https://localhost/login`에서 관리자 로그인 후 `/admin`이 열리면 HTTPS 뒤에서 프론트·백엔드가 모두 정상이다. 명령줄에서는 `curl -I http://localhost`의 응답에 `301`과 `Location: https://localhost/`가 보이면 리다이렉트가 동작하는 것이다.

**🎓 newlec 쌤의 코멘트**: 개발 시 HTTP를 사용하고 운영에서 HTTPS를 적용하면 쿠키의 `SameSite`, `Secure` 옵션이나 Web API 호환성 문제로 예기치 못한 에러가 발생할 수 있다. mkcert로 신뢰할 수 있는 로컬 CA를 등록하고 개발 단계부터 HTTPS를 설정하는 것이 실무에서 안전하다.

> **추가 설명 — HTTPS에서만 되는 것들**: `Secure` 속성이 붙은 쿠키는 https에서만 저장·전송되고, `SameSite=None` 쿠키는 반드시 `Secure`여야 한다. 브라우저 API 중에도 클립보드(`navigator.clipboard`), 카메라·마이크, 위치, 서비스 워커처럼 **보안 컨텍스트**(https 또는 `localhost`)에서만 열리는 것들이 있다. `localhost`는 예외로 http여도 허용되지만, 같은 와이파이의 휴대폰에서 `http://192.168.x.x`로 접속해 테스트하면 막힌다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| 브라우저 경고 (`NET::ERR_CERT_AUTHORITY_INVALID`) | mkcert 로컬 CA 미등록 | `mkcert -install` 명령 재실행 후 브라우저 완전히 종료 후 재열기 |
| Nginx 실행 실패 | 인증서 파일명 불일치 | `certs/` 폴더 내 파일명과 `default.conf` 내부 파일명 매칭 확인 |
| `cannot load certificate "/etc/nginx/certs/..."` | `certs` 폴더를 `ncafe/` 루트가 아닌 곳에 만들었거나, `cd certs` 없이 루트에서 `mkcert`를 실행해 파일이 루트에 생김 | 두 `.pem` 파일이 `ncafe/certs/` 안에 있는지 확인 |
| 경고가 계속 뜸 (WSL 사용 시) | `mkcert -install`을 WSL 안에서만 실행해 윈도우 브라우저는 CA를 모름 | 윈도우 PowerShell에서 `mkcert -install` 실행 |
| HTTPS로 바꾼 뒤 API만 실패 | 443 블록의 `proxy_pass` 끝 `/` | 2단계와 같이 `/` 제거 |

**📝 이 단계의 핵심**

- 80번 포트 요청은 443번 HTTPS로 리다이렉트 처리한다.
- 인증서 파일은 `ro`(Read-Only) 옵션으로 안전하게 볼륨 마운트한다.

## 5단계: 운영 환경 — 자원 제한, 로그 관리, DB 백업

운영 환경에서 서비스 안정성을 확보하기 위해 자원(CPU, 메모리) 사용량을 제한하고, 로그 파일 증식을 막으며, DB 백업 자동화 스크립트를 작성한다.

**5-1. 운영 전용 Compose 파일 작성**

파일: `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  db:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1024M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  backend:
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 2048M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1024M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

> **추가 설명 — 원문에 더하면 좋은 것들**: `version` 줄은 지운다. 그 밖에 운영에서 빠지면 곤란한 것은 다음과 같다.
>
> | 더할 것 | 이유 |
> |---|---|
> | `proxy`에도 `logging` | Nginx 접근 로그가 가장 빨리 쌓인다 |
> | 백엔드 `DDL_AUTO: validate`, `JWT_SECRET`, `ADMIN_PASSWORD` | 운영에서 테이블이 멋대로 바뀌지 않게 하고, 개발용 비밀값(`admin1234` 등)을 쓰지 않게 한다. 값은 **서버의 `.env`** 에 둔다 |
> | 백엔드 `JAVA_TOOL_OPTIONS: "-XX:MaxRAMPercentage=75.0"` | 자바는 컨테이너 메모리 제한의 **25%만** 힙으로 잡는다. 2048M 제한이면 힙이 512MB뿐이므로 비율을 올린다 |
>
> ```yaml
>   backend:
>     environment:
>       DDL_AUTO: validate
>       JWT_SECRET: ${JWT_SECRET:?JWT_SECRET 을 .env 에 설정하세요}
>       ADMIN_PASSWORD: ${ADMIN_PASSWORD:?ADMIN_PASSWORD 를 .env 에 설정하세요}
>       JAVA_TOOL_OPTIONS: "-XX:MaxRAMPercentage=75.0"
>
>   proxy:
>     logging:
>       driver: "json-file"
>       options:
>         max-size: "10m"
>         max-file: "3"
> ```
>
> `${변수:?메시지}`는 값이 없으면 **실행을 멈추고** 메시지를 보여 주는 Compose 문법이다. 개발용 기본값으로 운영이 뜨는 사고를 막는다. `DDL_AUTO: validate`는 첫 배포처럼 테이블이 아직 없을 때는 기동에 실패하므로, 처음 한 번은 `update`로 띄워 테이블을 만든 뒤 바꾼다.

> **추가 설명 — 같은 서버를 여러 팀이 쓴다면**: 스타터 README의 5단계는 컨테이너 Nginx 대신 **서버에 설치한 Nginx + Certbot**(Let's Encrypt 공인 인증서)을 앞에 두는 구조를 요구한다. 그 경우 `proxy` 서비스는 띄우지 않고(서버의 80·443은 호스트 Nginx가 쓰므로), 백엔드·프론트 포트를 `"127.0.0.1:18080:8080"`처럼 **서버 내부에서만** 열어 호스트 Nginx가 그 포트로 보내게 한다. 팀마다 `.env`에 `COMPOSE_PROJECT_NAME`과 포트 번호를 다르게 두어 볼륨·컨테이너 이름·포트가 겹치지 않게 한다. 이때는 `container_name`을 고정해 두면 팀끼리 이름이 충돌하므로 빼는 것이 낫다. 자세한 구조는 [[041_Nginx, Next.js, Spring Boot, PostgreSQL을 하나로 묶는 도커 컴포즈 실전 구축기 참고자료]] 5절에 정리해 두었다.

**5-2. DB 자동 백업 스크립트 작성**

파일: `backup.sh`

```bash
#!/bin/bash

# 설정 정보
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILE_NAME="ncafe_backup_${DATE}.sql"

# 백업 디렉토리 생성
mkdir -p ${BACKUP_DIR}

# .env 파일 로드
source .env

# PostgreSQL 덤프 수행
docker exec ncafe-db pg_dump -U ${POSTGRES_USER} -d ${POSTGRES_DB} > ${BACKUP_DIR}/${FILE_NAME}

# 7일 이상 된 백업 파일 삭제
find ${BACKUP_DIR} -type f -name "*.sql" -mtime +7 -delete

echo "Backup completed: ${BACKUP_DIR}/${FILE_NAME}"
```

스크립트에 실행 권한을 부여한다.

```bash
chmod +x backup.sh
```

> **추가 설명 — 스크립트가 하는 일**: `pg_dump`는 **DB 컨테이너 안에서** 실행되어 DB 내용을 SQL 문(CREATE·INSERT)으로 출력하고, 그 출력이 `>`로 **호스트**의 `backups/` 파일에 저장된다. 컨테이너 안에서 접속하므로 비밀번호 없이 실행된다(공식 이미지는 컨테이너 내부 접속을 신뢰함). `backups/`는 스타터 `.gitignore`에 이미 들어 있다.

> **추가 설명 — 이대로 쓰기 전에 고칠 점**:
>
> | 문제 | 상황 | 고치는 법 |
> |---|---|---|
> | 실패해도 "Backup completed"가 찍힘 | 컨테이너가 꺼져 있으면 `docker exec`가 실패하지만 `>`가 **빈 파일**을 먼저 만들고, 다음 줄이 계속 실행된다. 빈 백업이 쌓이다 7일 뒤엔 정상 백업이 모두 지워질 수 있다 | 맨 위에 `set -euo pipefail`을 넣어 오류 시 즉시 멈추게 한다 |
> | 다른 폴더에서 실행하면 실패 | `./backups`, `.env`가 **현재 폴더** 기준이라 cron 등에서 실행하면 못 찾는다 | `cd "$(dirname "$0")"`로 스크립트 위치로 먼저 이동 |
> | 용량이 큼 | SQL은 텍스트라 압축이 잘 된다 | `| gzip > ....sql.gz` |
>
> ```bash
> #!/bin/bash
> set -euo pipefail
> cd "$(dirname "$0")"
>
> BACKUP_DIR="./backups"
> DATE=$(date +%Y%m%d_%H%M%S)
> FILE_NAME="ncafe_backup_${DATE}.sql.gz"
>
> mkdir -p "${BACKUP_DIR}"
> source .env
>
> docker exec ncafe-db pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" | gzip > "${BACKUP_DIR}/${FILE_NAME}"
>
> find "${BACKUP_DIR}" -type f -name "*.sql.gz" -mtime +7 -delete
> echo "Backup completed: ${BACKUP_DIR}/${FILE_NAME}"
> ```

> **추가 설명 — 윈도우에서 만든 `.sh`가 리눅스에서 안 돌 때**: 윈도우 편집기는 줄 끝을 `CRLF`로 저장하는 경우가 있다. 리눅스 서버에서 실행하면 `/bin/bash^M: bad interpreter` 또는 `$'\r': command not found` 오류가 난다. VSCode 오른쪽 아래 상태 표시줄의 `CRLF`를 눌러 `LF`로 바꿔 저장하거나, 서버에서 `sed -i 's/\r$//' backup.sh`로 고친다. 윈도우에서 직접 테스트할 때는 **Git Bash**나 **WSL** 터미널에서 실행한다(PowerShell에서는 `.sh`가 실행되지 않는다).

> **추가 설명 — "자동" 백업으로 만들기와 복구**: 위 스크립트는 실행할 때만 백업한다. 리눅스 서버에서는 `crontab -e`로 매일 정해진 시각에 실행되게 등록한다.
>
> ```bash
> # 매일 새벽 3시에 백업, 결과를 로그 파일에 남김
> 0 3 * * * /home/ubuntu/ncafe/backup.sh >> /home/ubuntu/ncafe/backups/backup.log 2>&1
> ```
>
> 백업은 **복구가 되는지 확인해야** 의미가 있다. 복구는 SQL을 다시 `psql`에 넣으면 된다. 기존 테이블이 있으면 충돌하므로, 연습할 때는 빈 DB(예: `docker compose down -v` 후 `up`으로 다시 만든 DB)에 넣는다.
>
> ```bash
> # .sql 백업
> docker exec -i ncafe-db psql -U ncafeuser -d ncafedb < backups/ncafe_backup_20261026_030000.sql
> # .sql.gz 백업
> gunzip -c backups/ncafe_backup_20261026_030000.sql.gz | docker exec -i ncafe-db psql -U ncafeuser -d ncafedb
> ```
>
> `-i`가 있어야 호스트의 파일 내용이 컨테이너 안 `psql`의 입력으로 들어간다. 또 백업을 같은 서버에만 두면 서버 디스크가 망가질 때 함께 잃으므로, 운영에서는 다른 저장소(다른 서버, 클라우드 스토리지)로도 복사해 둔다.

**5-3. 운영 모드 실행 및 백업 실행 테스트**

운영 전용 설정을 적용하여 실행한다.

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
./backup.sh
```

> **추가 설명 — 개발 모드에서 운영 모드로 바꿀 때**: `-f`로 파일을 지정하면 `docker-compose.override.yml`은 **자동으로 합쳐지지 않는다.** 그런데 3단계에서 만든 프론트·백엔드 이미지는 `target: deps`·`build` 단계(개발용)라서, 운영 모드로 처음 띄울 때는 `--build`를 붙여 **운영용 마지막 단계로** 다시 빌드해야 한다.
>
> ```bash
> docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
> ```
>
> 개발용 3000·8080 포트도 이때 사라진다. 매번 `-f`를 두 번 적기 번거로우면 서버의 `.env`에 `COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml`을 넣어 두면 `docker compose up -d`만으로 같은 효과가 난다(윈도우에서는 구분자가 `;`).

**✅ 확인**

- `docker stats` 명령 실행 시 설정한 메모리 제한(Memory Limit)이 적용되어 출력된다.
- `backups/` 폴더 내에 백업된 `.sql` 파일이 정상적으로 생성된다.

> **추가 설명 — 확인 결과 읽는 법**:
>
> ```
> $ docker stats --no-stream
> NAME             CPU %   MEM USAGE / LIMIT     MEM %
> ncafe-backend    0.52%   412MiB / 2GiB         20.1%
> ncafe-frontend   0.01%   58MiB / 1GiB          5.7%
> ncafe-db         0.03%   41MiB / 1GiB          4.0%
> ncafe-proxy      0.00%   4MiB / 15.5GiB        0.0%    ← 제한이 없으면 PC 전체 메모리가 LIMIT
> ```
>
> 숫자는 PC마다 다르다. **LIMIT 열**이 설정한 값(2GiB, 1GiB)으로 보이면 적용된 것이다. 백업 파일은 크기가 **0바이트가 아닌지**, 열었을 때 `CREATE TABLE public.menus ...` 같은 문장이 있는지 확인한다(`.gz`면 `gunzip -c 파일 | head -50`). 로그 제한은 `docker inspect ncafe-backend --format '{{.HostConfig.LogConfig}}'`로 `{json-file map[max-file:3 max-size:10m]}`가 보이면 적용된 것이다.

**🎓 newlec 쌤의 코멘트**: 무제한으로 메모리를 사용하는 컨테이너는 특정 상황에서 메모리 누수가 발생했을 때 호스트 OS 전체를 다운시킬 수 있다. 운영 환경에서는 반드시 서비스별로 `limits` 설정을 추가해야 하며, 도커 로그 파일이 디스크 용량을 전부 차지하지 않도록 `max-size` 조절이 필수적이다.

> **추가 설명 — 제한을 넘으면**: 메모리 제한을 넘은 컨테이너는 리눅스가 **강제 종료**한다(OOM Kill, `docker inspect`에서 `OOMKilled: true`). 서버 전체가 멈추는 대신 그 컨테이너 하나만 죽고, `restart: always`로 다시 켜진다. CPU 제한은 넘어도 죽지 않고 **느려지기만** 한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `backup.sh` 실행 시 권한 거부 에러 | 파일 실행 권한 미부여 | `chmod +x backup.sh` 실행 |
| `docker stats`에 자원 제한 안 보임 | prod 파일 누락 | 실행 시 `-f docker-compose.yml -f docker-compose.prod.yml` 두 파일 지정 확인 |
| `Error response from daemon: No such container: ncafe-db` | DB 컨테이너가 꺼져 있거나 `container_name`을 바꿈 | `docker compose ps`로 이름 확인. 수정 스크립트(`set -e`)는 여기서 멈추고 빈 파일을 남기지 않는다 |
| `bad interpreter` / `$'\r': command not found` | 윈도우 줄바꿈(CRLF)으로 저장됨 | `LF`로 바꿔 저장 |
| 백엔드가 주기적으로 재시작됨, `OOMKilled: true` | 메모리 제한보다 실제 사용량이 큼 | 제한을 늘리거나 `MaxRAMPercentage`로 힙 크기 조정 |
| 운영 모드로 바꿨는데 개발 서버(`next dev`)가 돌고 있음 | 개발용 단계로 만든 이미지를 그대로 사용 | `--build`로 다시 빌드 |

**📝 이 단계의 핵심**

- 운영 자원 제한과 로그 로테이션 설정으로 서버의 생존성을 확보한다.
- 데이터 손실에 대비해 주기적인 DB 덤프 백업 스크립트를 운영한다.

## 전체 정리

- **1단계**: `.env` 환경변수 처리와 `healthcheck` 조건으로 데이터베이스 기반 서비스 실행 순서를 완벽히 제어했다.
- **2단계**: Nginx 리버스 프록시를 적용해 포트를 단일화하고 컨테이너 간 내부 통신을 구성했다.
- **3단계**: `docker-compose.override.yml`로 바인드 마운트를 설정하여 라이브 리로딩 기반 개발 환경을 분리했다.
- **4단계**: mkcert와 Nginx SSL 설정을 조합해 로컬 환경에 완벽한 HTTPS 보안 단계를 적용했다.
- **5단계**: 운영 환경에 맞춘 컨테이너 자원 제한, 로그 용량 제한 및 DB 백업 스크립트를 구현했다.

```
                         ┌─────────────── ncafe_default 네트워크 ───────────────┐
브라우저 ─:80 → 301 ─┐    │                                                      │
         ─:443(TLS)──┴──▶│ [proxy: nginx] ─/api/*─▶ [backend:8080] ─▶ [db:5432]  │
                         │        └──────/*─────▶ [frontend:3000]      │         │
                         └──────────────────────────────────────────────┼─────────┘
                                                                ncafe_postgres_data (볼륨)
                                                                        │
                                                         backup.sh ─▶ ./backups/*.sql.gz
```

| 파일 | 언제 쓰이나 | 담는 것 |
|---|---|---|
| `.env` | 항상 (Git 제외) | DB 계정, JWT 비밀키, 관리자 계정 |
| `docker-compose.yml` | 항상 | 4개 서비스 공통 구조, healthcheck, 볼륨, 80·443 |
| `docker-compose.override.yml` | `docker compose up` (개발) | 개발 단계 빌드, 소스 마운트, 개발 서버, 3000·8080 노출 |
| `docker-compose.prod.yml` | `-f ... -f ...prod.yml` (운영) | 자원·로그 제한, 운영용 환경 변수 |
| `nginx/default.conf` | proxy 컨테이너 | 80→443 리다이렉트, 경로 분기, resolver, 헤더 |
| `certs/*.pem` | proxy 컨테이너 (Git 제외) | mkcert 로컬 인증서 |
| `backup.sh` | 수동 또는 cron | DB 덤프와 7일 보관 |

## 최종 파일 모음

원문 코드에 각 단계의 바로잡기를 모두 반영한 완성본이다.

**`.env`**

```bash
POSTGRES_DB=ncafedb
POSTGRES_USER=ncafeuser
POSTGRES_PASSWORD=ncafepassword123
JWT_SECRET=ncafe-local-secret-key-at-least-32-bytes-long!!
ADMIN_EMAIL=admin@ncafe.local
ADMIN_PASSWORD=admin1234
```

**`docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:17
    container_name: ncafe-db
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    container_name: ncafe-backend
    restart: always
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://db:5432/${POSTGRES_DB}
      SPRING_DATASOURCE_USERNAME: ${POSTGRES_USER}
      SPRING_DATASOURCE_PASSWORD: ${POSTGRES_PASSWORD}
      JWT_SECRET: ${JWT_SECRET:-ncafe-dev-only-secret-key-change-me-in-production!}
      ADMIN_EMAIL: ${ADMIN_EMAIL:-admin@ncafe.local}
      ADMIN_PASSWORD: ${ADMIN_PASSWORD:-admin1234}
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build: ./frontend
    container_name: ncafe-frontend
    restart: always
    depends_on:
      - backend

  proxy:
    image: nginx:1.27
    container_name: ncafe-proxy
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
```

**`docker-compose.override.yml`**

```yaml
services:
  frontend:
    build:
      context: ./frontend
      target: deps
    command: npm run dev
    environment:
      NODE_ENV: development
      API_PROXY_TARGET: http://backend:8080
      WATCHPACK_POLLING: "true"
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next

  backend:
    build:
      context: ./backend
      target: build
    command: ./gradlew bootRun --no-daemon
    ports:
      - "8080:8080"
    volumes:
      - ./backend:/app
      - /app/build
      - /app/.gradle
      - gradle_cache:/root/.gradle

volumes:
  gradle_cache:
```

**`docker-compose.prod.yml`**

```yaml
x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"

services:
  db:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1024M
    logging: *default-logging

  backend:
    environment:
      JWT_SECRET: ${JWT_SECRET:?JWT_SECRET 을 .env 에 설정하세요}
      ADMIN_PASSWORD: ${ADMIN_PASSWORD:?ADMIN_PASSWORD 를 .env 에 설정하세요}
      JAVA_TOOL_OPTIONS: "-XX:MaxRAMPercentage=75.0"
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 2048M
    logging: *default-logging

  frontend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1024M
    logging: *default-logging

  proxy:
    logging: *default-logging
```

> **추가 설명 — `x-logging`과 `&`·`*`**: 같은 `logging` 블록을 네 번 반복하는 대신 YAML **앵커**(`&default-logging`)로 한 번 정의하고 **별칭**(`*default-logging`)으로 가져다 쓴 것이다. `x-`로 시작하는 최상위 항목은 Compose가 무시하므로 이런 공용 조각을 두는 자리로 쓴다. 결과는 원문처럼 서비스마다 적은 것과 같다.

**`nginx/default.conf`**

```nginx
server {
    listen 80;
    server_name localhost;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name localhost;

    ssl_certificate     /etc/nginx/certs/localhost+2.pem;
    ssl_certificate_key /etc/nginx/certs/localhost+2-key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    resolver 127.0.0.11 valid=10s;

    location /api/ {
        set $backend http://backend:8080;
        proxy_pass $backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location / {
        set $frontend http://frontend:3000;
        proxy_pass $frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**`backup.sh`** — 5-2의 수정본(`set -euo pipefail`, `gzip`)을 사용한다.

**폴더 구조**

```
ncafe/
├── .env                          ← 직접 작성 (Git 제외)
├── .gitignore                    ← 스타터 제공 (.env, *.pem, backups/)
├── docker-compose.yml
├── docker-compose.override.yml
├── docker-compose.prod.yml
├── backup.sh
├── nginx/
│   └── default.conf
├── certs/
│   ├── localhost+2.pem           ← mkcert 생성 (Git 제외)
│   └── localhost+2-key.pem
├── backups/                      ← backup.sh 가 생성 (Git 제외)
├── backend/                      ← 스타터 제공
└── frontend/                     ← 스타터 제공
```
