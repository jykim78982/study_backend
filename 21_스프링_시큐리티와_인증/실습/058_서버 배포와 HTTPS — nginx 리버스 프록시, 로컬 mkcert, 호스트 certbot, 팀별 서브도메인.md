---
tags: [HTTPS, nginx, mkcert, certbot, DockerCompose, 리버스프록시, 배포, 서브도메인, 실습]
---

> 🔗 관련 노트: [[057_도커 컴포즈 — 프론트·백엔드·PostgreSQL·Redis를 한 번에, 리프레시 토큰은 Redis로]] · [[056_메뉴 API — 목업을 걷어내고 스프링 MenuResponse를 Next.js BFF로 연결]] · [[052_Next.js 쿠키 기반 인증과 미들웨어 권한 제어 코드]] · [[054_인증 JWT+BFF·도커 컴포즈·CI_CD — 팀 프로젝트 공통 구조]]

# 서버 배포와 HTTPS — nginx 리버스 프록시, 로컬 mkcert, 호스트 certbot, 팀별 서브도메인

> **첨부 파일 안내**
> - `ncafe-prep-11-deploy-https.zip`: 이 노트 적용 **전**
> - `ncafe-lesson-11-deploy-https.zip`: 이 노트 적용 **후**
>
> 참고 프로젝트 경로: `ncafe-lesson-11-deploy-https`  
> 프로젝트 해설: `README-HTTPS-Deploy.md`

---

이전 노트([[057_도커 컴포즈 — 프론트·백엔드·PostgreSQL·Redis를 한 번에, 리프레시 토큰은 Redis로]])에서 프로젝트 전체가 `docker compose up -d` 한 줄로 올라오게 되었다. 다섯 컨테이너가 내 컴퓨터에서 돈다. 이제 그것을 다른 사람이 접속할 수 있는 서버에 올린다.

그 전에 지금 구조의 빈 자리를 보자. 브라우저는 `http://localhost:3000`으로 Next.js 컨테이너에 직접 들어오고, 백엔드도 `localhost:8080`으로 열려 있고, 모두 HTTP다. 개발 중에는 편하지만 서버에서는 셋 다 문제다.

1. **HTTPS가 아니면 쿠키가 위험하다.** 06 노트의 쿠키 옵션 `secure: process.env.NODE_ENV === "production"`은 운영에서 HTTPS가 아니면 브라우저가 쿠키를 보내지 않는다는 뜻이다. HTTP 서버에 운영 이미지를 올리면 로그인이 되는 듯하다가 다음 요청에서 쿠키가 빠져 로그아웃된 것처럼 보인다. 그리고 HTTPS가 아니면 토큰이 네트워크에서 그대로 읽힌다.
2. **포트가 노출되어 있다.** 백엔드 8080, PostgreSQL 5432, Redis 6379가 서버의 공개 IP에 열리면 인터넷 어디서나 두드릴 수 있다. Redis는 비밀번호도 없다.
3. **한 호스트를 여러 팀이 쓴다.** 팀마다 3000 포트를 열 수는 없다. 누가 어느 요청을 받을지 도메인으로 나눠야 한다.

세 문제를 한 가지 구조로 푼다. nginx를 앞에 두고, 모든 요청이 그것을 거쳐 HTTPS로 들어오게 한다. 로컬에서는 mkcert로 만든 인증서로, 서버에서는 Let's Encrypt 인증서로 같은 구조를 돌린다.

이번 노트에서는 다음 순서로 진행한다.

1. 리버스 프록시가 무엇이고 왜 nginx를 앞에 두는지 정리한다.
2. 로컬에 팀 nginx를 추가하고 mkcert로 `https://localhost`를 만든다.
3. 서버용 `compose.prod.yaml`을 만든다. 포트를 닫고 nginx 하나만 연다.
4. 호스트 컴퓨터 준비: 점검 스크립트로 무엇이 되어 있는지 보고, 없는 것만 설정 스크립트로 채운다. 계정, 도커, 호스트 nginx, certbot, DNS.
5. 팀별 배포: 호스트에 들어가 올리고, `https://team1.newlecture.com`에서 확인한다.
6. 재배포 때 끊김을 직접 본다. 다음 노트(블루그린)의 동기다.

---

## 1. 리버스 프록시 — 앞에 서는 서버

리버스 프록시는 클라이언트의 요청을 대신 받아서 뒤의 서버에 넘겨 주는 서버다. 브라우저는 프록시만 보고, 뒤에 무엇이 몇 대 있는지 모른다. nginx가 이 역할의 표준이다.

왜 Next.js가 직접 443을 열지 않고 nginx를 앞에 두는가.

- **TLS 종단.** 인증서를 들고 HTTPS를 푸는 일은 nginx가 하고, 뒤의 Next.js와 스프링은 평범한 HTTP로 돈다. 인증서 갱신이 애플리케이션 코드와 분리된다.
- **한 포트, 여러 서비스.** 443은 하나인데 팀은 여럿이다. nginx가 `Host` 헤더(`team1.newlecture.com`)를 보고 어느 팀으로 보낼지 정한다.
- **공격면 축소.** 밖에 열리는 것은 nginx의 80, 443뿐이다. 나머지는 모두 내부 네트워크에만 있다.
- **전환 지점.** 다음 노트에서 새 버전과 옛 버전 사이를 끊김 없이 바꾸는 일도 nginx가 보내는 곳을 바꾸는 것으로 끝난다.

우리 구조에서 nginx가 알아야 할 뒤쪽 서버는 frontend 하나다. 브라우저는 Next.js만 부르고, 스프링은 Next.js가 서버 안에서 `backend:8080`으로 부른다(BFF). Route Handler까지 BFF로 통일해 둔 덕에 nginx 설정에 `/api`를 백엔드로 보내는 분기가 필요 없다.

서버에서는 nginx가 두 층이 된다.

```
인터넷 ─HTTPS─▶ 호스트 nginx (443, 호스트에 직접 설치, certbot 인증서)
                  │  Host 헤더로 팀을 고른다
                  ├─ team1.newlecture.com ─HTTP─▶ 127.0.0.1:3101 ─▶ team1 팀 nginx ─▶ frontend ─▶ backend ─▶ postgres, redis
                  ├─ team2.newlecture.com ─HTTP─▶ 127.0.0.1:3102 ─▶ team2 팀 nginx ─▶ ...
                  └─ ...
```

호스트 nginx는 호스트 컴퓨터에 직접 설치되어 하나만 있고 인증서와 도메인 분기를 맡는다. 팀 nginx는 각 팀의 compose 안에 있는 컨테이너로, 팀이 자기 손으로 다룰 수 있는 지점이다. 지금은 frontend에 넘기기만 하지만 다음 노트에서 블루/그린 전환을 여기서 한다. 로컬에서는 호스트 nginx가 없으니 팀 nginx가 HTTPS까지 직접 맡는다.

---

## 2. 로컬 HTTPS — 팀 nginx와 mkcert

### 1) mkcert로 인증서 만들기

HTTPS에는 인증서가 필요하고, 브라우저는 신뢰하는 기관이 서명한 인증서만 경고 없이 받아 준다. localhost에는 공인 기관이 인증서를 내주지 않는다. mkcert는 내 컴퓨터에만 신뢰되는 기관(CA)을 하나 만들어 OS와 브라우저에 등록하고, 그 기관으로 localhost 인증서를 발급한다.

```bash
# 설치
#   Windows : choco install mkcert     (또는 scoop install mkcert)
#   macOS   : brew install mkcert
#   Ubuntu  : sudo apt install mkcert
# WSL 에서 쓸 때는 윈도우 쪽에 설치하고 윈도우 터미널에서 -install 을 한다 (브라우저가 윈도우에 있다)

mkcert -install                       # 로컬 CA 를 만들고 OS·브라우저 신뢰 목록에 넣는다 (처음 한 번)

cd ncafe                              # 프로젝트 루트
mkdir certs
mkcert -cert-file certs/localhost.pem -key-file certs/localhost-key.pem localhost 127.0.0.1 ::1
```

`certs/` 폴더에 `localhost.pem`(인증서)과 `localhost-key.pem`(개인 키)이 생긴다. 개인 키는 커밋하지 않는다. `.gitignore`에 `certs/`를 추가했다. 각자 발급해서 쓴다.

### 2) 팀 nginx 설정 — `nginx/local.conf`

```nginx
# 로컬 HTTPS 용 nginx 설정 (compose.yaml 의 nginx 서비스, --profile https)
#
# 브라우저 → https://localhost (이 nginx, mkcert 인증서) → http://frontend:3000
# 백엔드는 프론트엔드가 서버 안에서 backend:8080 으로 부르므로(BFF) nginx 가 알 필요가 없다.

# 80 으로 들어오면 https 로 보낸다
server {
    listen 80;
    server_name localhost;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name localhost;

    # mkcert 가 만든 파일. compose 가 ./certs 를 /etc/nginx/certs 로 마운트한다
    ssl_certificate     /etc/nginx/certs/localhost.pem;
    ssl_certificate_key /etc/nginx/certs/localhost-key.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://frontend:3000;

        # Next.js 가 "원래 요청"을 알 수 있게 넘겨 준다.
        #  - Host: 리다이렉트 주소와 Server Action 의 출처(Origin) 검사에 쓰인다
        #  - X-Forwarded-Proto: https 로 들어왔음을 알린다 (안 넘기면 http 로 리다이렉트한다)
        proxy_set_header Host              $http_host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host  $http_host;

        # next dev 의 핫 리로드(웹소켓)가 nginx 를 통과하도록
        proxy_http_version 1.1;
        proxy_set_header Upgrade    $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

```

- 80은 443으로 보내기만 한다.
- `proxy_pass http://frontend:3000`: compose 네트워크 안의 서비스 이름.
- `X-Forwarded-Proto`와 `Host`를 꼭 넘긴다. Next.js가 HTTPS로 왔음을 알아야 secure 쿠키와 리다이렉트가 맞다.
- 웹소켓 업그레이드: `next dev` 핫 리로드용.

### 3) compose에 nginx 추가 — 프로필

인증서가 없는 사람도 `docker compose up`이 되어야 하므로 `profiles: ["https"]`로 기본 비활성.

전체 `compose.yaml`:

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
# 로컬 HTTPS(https://localhost)까지 띄우려면: docker compose --profile https up -d   (certs/ 에 mkcert 인증서 필요)
# 서버 배포는 별도 파일을 쓴다: compose.prod.yaml
#
# 값은 .env 파일로 바꿀 수 있다 (.env.example 참고). 없으면 ":-" 뒤의 기본값을 쓴다.
# 컨테이너끼리는 서비스 이름이 호스트 이름이다 (backend → redis:6379, frontend → backend:8080).
services:

  # 로컬 HTTPS. --profile https 를 붙여야 뜬다 (mkcert 인증서가 ./certs 에 있어야 한다)
  # 브라우저 → https://localhost → frontend:3000
  nginx:
    image: nginx:1.27
    profiles: ["https"]
    ports:
      - "${HTTP_PORT:-80}:80"
      - "${HTTPS_PORT:-443}:443"
    volumes:
      - ./nginx/local.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - frontend

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

### 4) 확인

```bash
docker compose --profile https up -d
docker compose ps        # nginx 가 추가로 떠 있다
```

브라우저에서 `https://localhost`. 자물쇠가 뜨고 메뉴·로그인이 되면 성공. `http://localhost`는 https로 301.

---

## 3. 서버용 compose.prod.yaml

개발용은 포트를 다 열고 소스를 마운트한다. 서버용 파일을 따로 둔다.

```yaml
# 서버용 compose. 개발용(compose.yaml + compose.override.yaml)과 따로 둔다.
#
#   docker compose -f compose.prod.yaml up -d --build
#
# 개발용과 다른 점
#  - 호스트에 여는 포트는 nginx 의 80 하나뿐이고, 그것도 127.0.0.1 에만 묶는다.
#    외부에서는 호스트 nginx(team1.newlecture.com, HTTPS)를 거쳐야만 들어올 수 있다.
#  - frontend, backend, postgres, redis 는 포트를 열지 않는다. 컨테이너끼리 서비스 이름으로만 통신한다.
#  - adminer 는 띄우지 않는다. DB 는 서버에서 psql 로 본다.
#  - 소스 마운트 없음. 이미지를 빌드해서 그대로 실행한다.
#
# .env 에 COMPOSE_PROJECT_NAME(team1)과 TEAM_PORT(3101)를 둔다.
# 프로젝트 이름이 컨테이너·볼륨·네트워크 이름의 접두어가 되어, 한 호스트에서 팀끼리 섞이지 않는다.
services:

  # 팀 nginx. 호스트 nginx 가 127.0.0.1:${TEAM_PORT} 로 넘겨 준 요청을 frontend 에 전달한다
  nginx:
    image: nginx:1.27
    ports:
      - "127.0.0.1:${TEAM_PORT:-3101}:80"
    volumes:
      - ./nginx/server.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - frontend
    restart: unless-stopped

  frontend:
    build: ./frontend
    environment:
      BACKEND_URL: http://backend:8080
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    build: ./backend
    environment:
      REDIS_HOST: redis
      REDIS_PORT: 6379
      JWT_SECRET: ${JWT_SECRET:?JWT_SECRET 을 .env 에 설정하세요}
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-ncafe}
      POSTGRES_USER: ${POSTGRES_USER:-ncafe}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD 를 .env 에 설정하세요}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-ncafe} -d ${POSTGRES_DB:-ncafe}"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

```

핵심:

- 호스트에 여는 포트는 `127.0.0.1:${TEAM_PORT}:80` 하나. `127.0.0.1:`이 없으면 공개 IP에 열려 HTTPS를 우회한다.
- frontend/backend/postgres/redis는 `ports` 없음.
- `${JWT_SECRET:?...}`, `${POSTGRES_PASSWORD:?...}`로 비밀값 강제.
- `restart: unless-stopped`, Adminer 없음.
- `COMPOSE_PROJECT_NAME`으로 팀 간 컨테이너·볼륨 격리.

팀 nginx `nginx/server.conf`:

```nginx
# 서버용 "팀 nginx" 설정 (compose.prod.yaml 의 nginx 서비스)
#
# 인터넷 → 호스트 nginx (team1.newlecture.com, 443, certbot 인증서)
#        → http://127.0.0.1:3101 (이 nginx, 80)
#        → http://frontend:3000
#
# HTTPS 는 호스트 nginx 가 끝냈으므로 여기는 80 만 듣는다.
# 호스트 nginx 가 넘겨 준 X-Forwarded-* 헤더를 그대로 frontend 에 전달한다.
#
# 지금은 frontend 하나지만 upstream 으로 분리해 두었다.
# 다음 노트(블루그린)에서 이 블록의 서버 한 줄을 바꾸는 것으로 트래픽을 전환한다.
upstream frontend_upstream {
    server frontend:3000;
}

server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://frontend_upstream;

        proxy_set_header Host              $http_host;
        proxy_set_header X-Real-IP         $http_x_real_ip;
        proxy_set_header X-Forwarded-For   $http_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
        proxy_set_header X-Forwarded-Host  $http_x_forwarded_host;
    }
}

```

- 80만. TLS는 호스트 nginx가 끝냄.
- `X-Forwarded-*`는 **넘긴다** (`$http_x_forwarded_proto`). 여기서 `$scheme`을 쓰면 http로 덮어쓴다.
- `upstream frontend_upstream`: 다음 노트 블루그린용으로 분리.

`.env.example`:

```
# docker compose 가 읽는 값. 복사해서 .env 로 만들면 compose.yaml 의 기본값을 덮어쓴다.
#   cp .env.example .env
# .env 는 커밋하지 않는다 (.gitignore).

# 호스트에 여는 포트. 이미 쓰는 포트가 있으면 여기서 바꾼다
FRONTEND_PORT=3000
BACKEND_PORT=8080
# 로컬 HTTPS (docker compose --profile https)
HTTP_PORT=80
HTTPS_PORT=443

# 서버 배포 (compose.prod.yaml). 팀 번호에 맞춰 바꾼다: team1 → 3101, team2 → 3102 ...
COMPOSE_PROJECT_NAME=team1
TEAM_PORT=3101

POSTGRES_DB=ncafe
POSTGRES_USER=ncafe
POSTGRES_PASSWORD=ncafe1234

```

로컬에서 서버 모양 미리 보기:

```bash
TEAM_PORT=3101 JWT_SECRET='32바이트가-넘는-충분히-긴-비밀-문자열!!' POSTGRES_PASSWORD=team1pw \
  docker compose -f compose.prod.yaml -p team1 up -d --build

curl -i -H "Host: team1.newlecture.com" -H "X-Forwarded-Proto: https" http://127.0.0.1:3101/menus
docker compose -p team1 down -v
```

---

## 4. 호스트 컴퓨터 준비 — 확인하고, 없으면 설정한다

여러 팀의 스택이 함께 올라가는 배포 대상 컴퓨터를 **호스트**라고 부른다. 순서는 늘 같다.

```bash
bash deploy/host/check-host.sh            # 1) 무엇이 없는지 본다
sudo bash deploy/host/setup-host.sh       # 2) 없는 것만 채운다
bash deploy/host/check-host.sh            # 3) 다시 본다
```

도메인·팀 목록은 스크립트 맨 위 `DOMAIN`, `TEAMS` (기본 `newlecture.com`, team1~5). 포트는 team1→3101 …

```bash
sudo DOMAIN=example.com TEAMS="team1 team2 team3" bash deploy/host/setup-host.sh
```

### 1) 점검 — `check-host.sh`

```bash
#!/usr/bin/env bash
# 호스트 컴퓨터 점검 스크립트. 바꾸는 것은 없다. 누구나 실행해 필요한 설정이 되어 있는지 본다.
# [없음] 이 나온 항목은 그 아래 → 에 적힌 명령으로 채운다. 대부분은 setup-host.sh 한 번으로 끝난다.
#
#   bash deploy/host/check-host.sh                      # 팀 계정으로. 다른 계정의 홈은 못 보므로 일부 항목은 [sudo 필요]
#   sudo bash deploy/host/check-host.sh                 # 전부 본다
#   DOMAIN=example.com TEAMS="team1 team2" bash deploy/host/check-host.sh
set -u

DOMAIN="${DOMAIN:-newlecture.com}"
TEAMS="${TEAMS:-team1 team2 team3 team4 team5}"
BASE_PORT="${BASE_PORT:-3100}"
SITE=/etc/nginx/sites-enabled/teams
SETUP="sudo bash deploy/host/setup-host.sh"
MISSING=0
ME=$(id -un)

ok()   { printf '  [OK]    %s\n' "$1"; }
miss() { printf '  [없음]  %s\n          → %s\n' "$1" "$2"; MISSING=$((MISSING + 1)); }
skip() { printf '  [sudo 필요] %s\n' "$1"; }
can_read_home() { [ "$(id -u)" -eq 0 ] || [ "$1" = "$ME" ]; }

echo "== 1. 도커"
if command -v docker >/dev/null 2>&1; then
  ok "docker: $(docker --version)"
  systemctl is-active --quiet docker && ok "docker 데몬 실행 중" || miss "docker 데몬이 꺼져 있다" "sudo systemctl enable --now docker"
  docker compose version >/dev/null 2>&1 && ok "docker compose: $(docker compose version --short)" || miss "docker compose 플러그인" "$SETUP"
else
  miss "docker" "$SETUP"
fi

echo "== 2. 팀 계정"
i=1
for team in $TEAMS; do
  port=$((BASE_PORT + i)); i=$((i + 1))
  if ! id "$team" >/dev/null 2>&1; then
    miss "$team 계정" "$SETUP"
    continue
  fi
  if id -nG "$team" | tr ' ' '\n' | grep -qx docker; then
    ok "$team 계정, docker 그룹 (→ 127.0.0.1:$port)"
  else
    miss "$team 이 docker 그룹에 없다" "sudo usermod -aG docker $team  (그 계정은 다시 로그인)"
  fi
  if can_read_home "$team"; then
    keys="/home/$team/.ssh/authorized_keys"
    if [ -s "$keys" ]; then
      ok "$team SSH 공개 키 $(grep -c . "$keys")개"
    else
      miss "$team SSH 공개 키가 없다" "공개 키 한 줄을 $keys 에 추가 (sudo)"
    fi
    [ -f "/home/$team/ncafe.env.example" ] && ok "$team .env 초안 (~/ncafe.env.example)" || miss "$team .env 초안" "$SETUP"
  else
    skip "$team SSH 공개 키, .env 초안"
  fi
done

echo "== 3. 호스트 nginx"
if command -v nginx >/dev/null 2>&1; then
  ok "nginx: $(nginx -v 2>&1 | cut -d/ -f2)"
  systemctl is-active --quiet nginx && ok "nginx 실행 중" || miss "nginx 가 꺼져 있다" "sudo systemctl enable --now nginx"
  if [ -f "$SITE" ]; then
    ok "팀 라우팅 설정 ($SITE)"
    for team in $TEAMS; do
      grep -q "$team\.$DOMAIN" "$SITE" && ok "  라우팅: $team.$DOMAIN" \
        || miss "라우팅에 $team.$DOMAIN 이 없다" "/etc/nginx/sites-available/teams 의 map 과 server_name 에 추가 후 sudo nginx -t && sudo systemctl reload nginx"
    done
    grep -q 'listen 443' "$SITE" && ok "HTTPS 설정 (certbot 적용됨)" \
      || miss "HTTPS 미적용 (listen 443 없음)" "sudo certbot --nginx $(for t in $TEAMS; do printf -- '-d %s.%s ' "$t" "$DOMAIN"; done)"
  else
    miss "팀 라우팅 설정 ($SITE)" "$SETUP"
  fi
else
  miss "nginx" "$SETUP"
fi
command -v certbot >/dev/null 2>&1 && ok "certbot: $(certbot --version 2>&1)" || miss "certbot" "$SETUP"
systemctl list-timers --all 2>/dev/null | grep -q certbot && ok "certbot 자동 갱신 타이머" || miss "certbot 갱신 타이머" "certbot 설치 뒤 자동 등록된다. sudo systemctl enable --now certbot.timer"
for p in 80 443; do
  ss -ltnH "sport = :$p" 2>/dev/null | grep -q . && ok "포트 $p 듣는 중" || miss "포트 $p 를 듣는 프로세스가 없다" "nginx 와 HTTPS 설정을 확인"
done

echo "== 4. DNS"
PUBLIC_IP=$(curl -s --max-time 3 https://api.ipify.org 2>/dev/null || true)
echo "  이 호스트의 공개 IP: ${PUBLIC_IP:-알 수 없음}  (DNS 의 A 레코드가 이 값이어야 한다)"
for team in $TEAMS; do
  ip=$(getent ahostsv4 "$team.$DOMAIN" 2>/dev/null | awk 'NR==1{print $1}')
  if [ -z "$ip" ]; then
    miss "$team.$DOMAIN 이 DNS 에 없다" "DNS 에 A 레코드 추가: $team.$DOMAIN → ${PUBLIC_IP:-호스트 공개 IP}"
  elif [ -n "$PUBLIC_IP" ] && [ "$ip" != "$PUBLIC_IP" ]; then
    miss "$team.$DOMAIN → $ip (이 호스트가 아니다)" "DNS A 레코드를 $PUBLIC_IP 로"
  else
    ok "$team.$DOMAIN → $ip"
  fi
done

echo "== 5. 끝에서 끝 (이 호스트의 443 으로 직접 접속해 인증서와 라우팅을 본다)"
for team in $TEAMS; do
  host="$team.$DOMAIN"
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 --resolve "$host:443:127.0.0.1" "https://$host/")
  rc=$?
  case "$rc:$code" in
    0:200|0:30?) ok "https://$host → $code" ;;
    0:502|0:503) ok "https://$host → $code (호스트 nginx 는 정상. 팀 스택이 아직 안 떠 있다: docker compose -f compose.prod.yaml up -d)" ;;
    0:*)         miss "https://$host → $code" "호스트 nginx 라우팅과 팀 nginx(127.0.0.1:310N)를 확인" ;;
    60:*)        miss "https://$host 인증서가 유효하지 않다" "sudo certbot --nginx -d $host ..." ;;
    7:*)         miss "https://$host 443 에 연결되지 않는다" "nginx 와 certbot 적용을 확인" ;;
    *)           miss "https://$host curl 종료 코드 $rc" "curl -v --resolve $host:443:127.0.0.1 https://$host/ 로 원인 확인" ;;
  esac
done

echo
if [ "$MISSING" -eq 0 ]; then
  echo "모든 항목이 준비되어 있습니다."
else
  echo "$MISSING 개 항목이 없습니다. 위의 → 명령으로 채우거나  $SETUP  를 실행하세요."
  exit 1
fi

```

항목: 도커, 팀 계정·SSH 키·`.env` 초안, 호스트 nginx·certbot·443, DNS, 끝에서 끝 curl.

### 2) 설정 — `setup-host.sh`

```bash
#!/usr/bin/env bash
# 호스트 컴퓨터 준비 스크립트 (Ubuntu 24.04 기준). sudo 권한이 있는 사람이 호스트에서 실행한다.
# 여러 번 실행해도 안전하다. 이미 되어 있는 것은 건너뛰고 없는 것만 설정한다.
# 적용 여부는 같은 폴더의 check-host.sh 로 확인한다.
#
#   sudo bash deploy/host/setup-host.sh
#   sudo DOMAIN=example.com TEAMS="team1 team2 team3" bash deploy/host/setup-host.sh   # 도메인·팀 목록을 바꿀 때
#   bash deploy/host/setup-host.sh --render-nginx                                    # 만들어질 nginx 설정만 미리 본다
#
# 하는 일
#  1. 도커 설치 (공식 저장소)
#  2. 팀별 리눅스 계정 생성, docker 그룹에 넣기, 팀별 .env 초안(~/ncafe.env.example) 작성
#  3. nginx, certbot 설치. 팀 도메인 → 팀 nginx(127.0.0.1:310N) 라우팅 설정을 /etc/nginx/sites-available/teams 에 생성
#  인증서 발급(certbot)은 DNS 가 이 호스트를 가리킨 뒤 한 번 실행한다 (끝의 안내 참고).
set -euo pipefail

DOMAIN="${DOMAIN:-newlecture.com}"
TEAMS="${TEAMS:-team1 team2 team3 team4 team5}"
BASE_PORT="${BASE_PORT:-3100}"          # team1 → 3101, team2 → 3102 ...
SITE=/etc/nginx/sites-available/teams

# 호스트 nginx 설정을 DOMAIN, TEAMS 로 만들어 표준 출력에 쓴다
render_nginx_conf() {
  local i=1 team names=""
  for team in $TEAMS; do names="$names $team.$DOMAIN"; done
  cat <<HEAD
# 호스트 nginx 설정 — deploy/host/setup-host.sh 가 생성 (DOMAIN=$DOMAIN, TEAMS=$TEAMS)
# 팀 도메인으로 들어온 요청을 Host 헤더로 구분해 각 팀의 nginx(127.0.0.1:310N) 로 넘긴다.
# HTTPS 는 certbot --nginx 가 이 파일에 listen 443 ssl, 인증서 경로, 80 → 443 리다이렉트를 써 넣는다.
# 팀을 추가하려면 map 과 server_name 에 한 줄씩 더하고: sudo nginx -t && sudo systemctl reload nginx

map \$host \$team_upstream {
HEAD
  for team in $TEAMS; do
    printf '    %-32s 127.0.0.1:%d;\n' "$team.$DOMAIN" "$((BASE_PORT + i))"
    i=$((i + 1))
  done
  cat <<BODY
}

server {
    listen 80;
    server_name$names;

    location / {
        proxy_pass http://\$team_upstream;

        proxy_set_header Host              \$host;
        proxy_set_header X-Real-IP         \$remote_addr;
        proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host  \$host;

        # 웹소켓 업그레이드도 통과시킨다
        proxy_http_version 1.1;
        proxy_set_header Upgrade    \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# 팀 도메인이 아닌 Host(IP 직접 접속 등)는 연결을 끊는다
server {
    listen 80 default_server;
    server_name _;
    return 444;
}
BODY
}

if [ "${1:-}" = "--render-nginx" ]; then
  render_nginx_conf
  exit 0
fi

[ "$(id -u)" -eq 0 ] || { echo "sudo 로 실행하세요:  sudo bash $0"; exit 1; }

echo "== 1. 도커"
if command -v docker >/dev/null; then
  echo "  이미 설치됨: $(docker --version)"
else
  apt-get update
  apt-get install -y ca-certificates curl
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi
systemctl enable --now docker >/dev/null
docker compose version

echo "== 2. 팀 계정"
i=1
for team in $TEAMS; do
  port=$((BASE_PORT + i))
  home="/home/$team"
  if id "$team" >/dev/null 2>&1; then
    echo "  $team: 계정 있음"
  else
    adduser --disabled-password --gecos "" "$team"
    echo "  $team: 계정 생성"
  fi
  usermod -aG docker "$team"                       # sudo 없이 docker 명령을 쓸 수 있게
  install -d -o "$team" -g "$team" -m 700 "$home/.ssh"
  touch "$home/.ssh/authorized_keys"
  chown "$team:$team" "$home/.ssh/authorized_keys"
  chmod 600 "$home/.ssh/authorized_keys"
  # 팀별 .env 초안. 비밀값은 무작위로 채워 둔다. 팀이 그대로 쓰거나 바꾼다
  if [ ! -f "$home/ncafe.env.example" ]; then
    cat > "$home/ncafe.env.example" <<ENV
# 이 파일을 프로젝트 폴더의 .env 로 복사한다:  cp ~/ncafe.env.example ~/ncafe/.env
# 비밀값은 setup-host.sh 가 무작위로 채웠다. 바꿔도 된다
COMPOSE_PROJECT_NAME=$team
TEAM_PORT=$port
POSTGRES_DB=ncafe
POSTGRES_USER=ncafe
POSTGRES_PASSWORD=$(openssl rand -hex 12)
JWT_SECRET=$(openssl rand -hex 32)
ENV
    chown "$team:$team" "$home/ncafe.env.example"
    chmod 600 "$home/ncafe.env.example"
    echo "  $team: ~/ncafe.env.example 작성"
  fi
  echo "  $team → 127.0.0.1:$port"
  i=$((i + 1))
done

echo "== 3. nginx + certbot"
if command -v nginx >/dev/null && command -v certbot >/dev/null; then
  echo "  이미 설치됨: $(nginx -v 2>&1), $(certbot --version 2>&1)"
else
  apt-get install -y nginx certbot python3-certbot-nginx
fi
# certbot 이 이 파일에 443 블록을 써 넣으므로, 이미 있으면 덮어쓰지 않는다
if [ -f "$SITE" ]; then
  echo "  $SITE 있음 (건너뜀). 팀을 추가했다면 직접 한 줄 더한다"
else
  render_nginx_conf > "$SITE"
  echo "  $SITE 생성"
fi
ln -sf "$SITE" /etc/nginx/sites-enabled/teams
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable --now nginx >/dev/null
systemctl reload nginx

cat <<MSG

== 남은 일 (사람이 한 번 한다). 확인은:  bash deploy/host/check-host.sh
1) DNS: $(for t in $TEAMS; do printf '%s.%s ' "$t" "$DOMAIN"; done)
   A 레코드가 이 호스트의 공개 IP 를 가리키게 한다 (와일드카드 *.$DOMAIN 하나로도 된다).
2) 인증서: DNS 가 반영된 뒤 한 번 실행한다. 80 포트가 인터넷에서 열려 있어야 한다.
     sudo certbot --nginx $(for t in $TEAMS; do printf -- '-d %s.%s ' "$t" "$DOMAIN"; done)
   자동 갱신은 certbot 이 systemd 타이머로 등록한다:  systemctl list-timers | grep certbot
3) 팀별 SSH 공개 키를 /home/<팀>/.ssh/authorized_keys 에 한 줄씩 넣는다. 팀원이 접속하는 키와,
   GitHub Actions 가 배포할 때 쓰는 키(CI/CD 노트)가 여기 들어간다.
MSG

```

하는 일: 도커 설치, 팀 계정+docker 그룹+`~/ncafe.env.example`(무작위 비밀값), nginx·certbot, `/etc/nginx/sites-available/teams` 생성. 여러 번 실행해도 안전. certbot 발급은 DNS 반영 뒤 사람이 한 번.

### 3) 호스트 nginx map

`Host` → `127.0.0.1:310N`. `X-Forwarded-Proto $scheme`은 **여기서** 만든다. certbot이 이 파일에 443을 써 넣는다. `default_server`는 444.

### 4) Let's Encrypt

```bash
sudo certbot --nginx -d team1.newlecture.com -d team2.newlecture.com \
                     -d team3.newlecture.com -d team4.newlecture.com -d team5.newlecture.com
```

90일, systemd 타이머로 자동 갱신. HTTP 인증이라 공개 IP·열린 80·실제 도메인 필요 → localhost는 mkcert.

### 5) 사람이 하는 세 가지

| 항목 | 없을 때 |
|---|---|
| DNS | A 레코드 (또는 `*.도메인`) |
| 인증서 | `sudo certbot --nginx -d ...` |
| SSH 공개 키 | `authorized_keys`에 한 줄 |

---

## 5. 팀별 배포

```bash
ssh team1@호스트주소
git clone https://github.com/<팀-저장소>/ncafe.git
cd ncafe
cp ~/ncafe.env.example .env
docker compose -f compose.prod.yaml up -d --build
docker compose -f compose.prod.yaml logs -f backend
```

브라우저 `https://team1.newlecture.com` — 자물쇠, 메뉴 13개, 로그인. 통했다는 뜻:

1. 호스트 nginx가 Host로 3101
2. 팀 nginx가 `X-Forwarded-Proto: https` 보존 → secure 쿠키
3. Next.js → `backend:8080`
4. 스프링 → `redis:6379`에 리프레시 토큰

```bash
F="docker compose -f compose.prod.yaml"
$F ps
$F logs -f backend
$F exec postgres psql -U ncafe -d ncafe
$F exec redis redis-cli KEYS 'refresh:*'
$F restart backend
$F down
```

---

## 6. 재배포 — 그리고 끊김

```bash
git pull
docker compose -f compose.prod.yaml up -d --build
```

컨테이너 교체 중 로그인 실패·502가 난다. 다음 노트 블루그린이 이것을 없앤다 (`upstream`을 미리 분리한 이유). Redis는 안 바뀌면 로그인 상태는 유지된다.

---

## 7. 주의할 사항과 정리

### 1) X-Forwarded-Proto를 두 층이 다르게 다룬다

HTTPS를 처음 받은 서버는 `$scheme`으로 만들고, 뒤 층은 `$http_x_forwarded_proto`로 넘긴다.

### 2) `127.0.0.1:` 접두어

빼면 팀 nginx가 공개 IP에 열려 HTTPS를 우회한다. 도커는 ufw를 우회한다.

### 3) 서버에서 빌드는 임시다

다음 노트에서 GHCR 이미지 pull로 바뀐다.

### 4) 비밀값

`.env`는 커밋하지 않는다. `JWT_SECRET`은 팀마다 달라야 한다.

### 5) 정리

| | 로컬 | 서버 |
|---|---|---|
| 주소 | `https://localhost` | `https://team1.newlecture.com` |
| compose | `docker compose --profile https up -d` | `docker compose -f compose.prod.yaml up -d --build` |
| HTTPS | 팀 nginx (mkcert) | 호스트 nginx (certbot) → 팀 nginx 80 |
| 열린 포트 | 80/443 (+ 개발용) | 호스트 80/443만. 팀은 127.0.0.1 |

### 6) 이번 노트에서 추가·수정된 파일

**루트 (추가)** `compose.prod.yaml`, `nginx/local.conf`, `nginx/server.conf`, `deploy/host/check-host.sh`, `deploy/host/setup-host.sh`

**루트 (수정)** `compose.yaml` — nginx `profiles: ["https"]`, `.env.example`, `.gitignore` — `certs/`

---

## 마무리

프로젝트가 HTTPS로, 도메인으로, 다른 사람에게 열렸다. 로컬은 mkcert로 운영과 같은 조건을 재현하고, 호스트 nginx 하나가 여러 팀을 도메인으로 나눈다. 밖에 열린 포트는 80과 443뿐이다.

배포는 아직 손(`git pull` + `up -d --build`)이고 잠깐 끊긴다. 다음은 GitHub Actions CI/CD와 블루그린이다.
