---
tags: [Docker, DockerCompose, Nginx, 리버스프록시, HTTPS, TLS, mkcert, Certbot, LetsEncrypt, 서브도메인, 배포, 참고자료]
---

> 🔗 관련 노트: [[043_도커 컴포즈로 프론트·백엔드·PostgreSQL·Redis 한 번에 띄우기와 리프레시 토큰 Redis 저장 참고자료]] · [[041_Nginx, Next.js, Spring Boot, PostgreSQL을 하나로 묶는 도커 컴포즈 실전 구축기 참고자료]] · [[042_CI_CD와 테스트 서버 배포 참고자료]]

# 서버 배포와 HTTPS — nginx 리버스 프록시, mkcert, certbot, 팀별 서브도메인

> 원문은 4절의 호스트 점검 스크립트(DNS 점검 부분)에서 잘려 있다. 이 노트는 받은 부분까지 정리했고, 호스트 설정 스크립트·팀별 배포·재배포 끊김(원문 4절 뒷부분~6절)은 목차만 남겼다.

## 0. 지금 구조의 빈 자리

직전 단계에서 다섯 컨테이너가 `docker compose up -d` 한 줄로 뜬다. 하지만 브라우저가 `http://localhost:3000`으로 Next.js에 직접 들어오고, 백엔드도 `localhost:8080`으로 열려 있고, 모두 HTTP다. 서버에서는 셋 다 문제다.

| 문제 | 왜 |
| --- | --- |
| HTTPS가 아니다 | 쿠키 옵션 `secure: process.env.NODE_ENV === "production"` 때문에 운영에서 HTTPS가 아니면 브라우저가 쿠키를 보내지 않는다. 로그인이 되는 듯하다가 다음 요청에서 로그아웃된 것처럼 보인다. 토큰도 네트워크에서 그대로 읽힌다 |
| 포트가 노출된다 | 백엔드 8080, PostgreSQL 5432, Redis 6379(비밀번호 없음)가 공개 IP에 열리면 어디서나 두드릴 수 있다 |
| 한 호스트를 여러 팀이 쓴다 | 팀마다 3000을 열 수 없다. 도메인으로 나눠야 한다 |

해법은 하나다. **nginx를 앞에 두고 모든 요청이 그것을 거쳐 HTTPS로 들어오게 한다.** 로컬은 mkcert 인증서, 서버는 Let's Encrypt 인증서로 같은 구조를 돌린다.

## 1. 리버스 프록시 — 앞에 서는 서버

클라이언트 요청을 대신 받아 뒤의 서버에 넘겨 주는 서버다. 브라우저는 프록시만 보고, 뒤에 무엇이 몇 대 있는지 모른다. nginx가 표준이다.

| 왜 앞에 두는가 | 설명 |
| --- | --- |
| TLS 종단 | 인증서를 들고 HTTPS를 푸는 일은 nginx가 하고, 뒤의 Next.js·스프링은 평범한 HTTP로 돈다. 인증서 갱신이 앱 코드와 분리된다 |
| 한 포트, 여러 서비스 | 443은 하나인데 팀은 여럿이다. `Host` 헤더(`team1.newlecture.com`)로 어느 팀에 보낼지 정한다 |
| 공격면 축소 | 밖에 열리는 것은 80, 443뿐이고 나머지는 내부 네트워크에만 있다 |
| 전환 지점 | 다음 단계(블루그린)에서 새 버전과 옛 버전 전환도 nginx가 보내는 곳을 바꾸는 것으로 끝난다 |

nginx가 알아야 할 뒤쪽 서버는 **frontend 하나**다. 브라우저는 Next.js만 부르고, 스프링은 Next.js가 서버 안에서 `backend:8080`으로 부른다(BFF). 그래서 `/api`를 백엔드로 보내는 분기가 필요 없다.

서버에서는 nginx가 두 층이다.

```
인터넷 ─HTTPS─▶ 호스트 nginx (443, 호스트에 직접 설치, certbot 인증서)
                  │  Host 헤더로 팀을 고른다
                  ├─ team1.newlecture.com ─HTTP─▶ 127.0.0.1:3101 ─▶ team1 팀 nginx ─▶ frontend ─▶ backend ─▶ postgres, redis
                  ├─ team2.newlecture.com ─HTTP─▶ 127.0.0.1:3102 ─▶ team2 팀 nginx ─▶ ...
                  └─ ...
```

- **호스트 nginx:** 호스트에 하나. 인증서와 도메인 분기를 맡는다.
- **팀 nginx:** 각 팀 compose 안의 컨테이너. 지금은 frontend에 넘기기만 하지만 블루그린 전환을 여기서 한다.
- 로컬에는 호스트 nginx가 없으니 팀 nginx가 HTTPS까지 직접 맡는다.

## 2. 로컬 HTTPS — 팀 nginx와 mkcert

### 1) mkcert로 인증서 만들기
브라우저는 신뢰하는 기관이 서명한 인증서만 경고 없이 받는데, `localhost`에는 공인 기관이 인증서를 내주지 않는다. mkcert는 **내 컴퓨터에서만 신뢰되는 기관(CA)**을 만들어 OS·브라우저에 등록하고, 그 기관으로 localhost 인증서를 발급한다.

```sh
# 설치: Windows choco/scoop install mkcert, macOS brew install mkcert, Ubuntu sudo apt install mkcert
# WSL 에서는 윈도우 쪽에 설치하고 윈도우 터미널에서 -install (브라우저가 윈도우에 있다)
mkcert -install                 # 로컬 CA 만들고 신뢰 목록에 등록 (처음 한 번)

mkdir certs
mkcert -cert-file certs/localhost.pem -key-file certs/localhost-key.pem localhost 127.0.0.1 ::1
```

개인 키는 커밋하지 않는다(`.gitignore`에 `certs/`). 각자 발급한다.

### 2) 팀 nginx 설정 — `nginx/local.conf`

```nginx
# 80 으로 들어오면 https 로 보낸다
server {
    listen 80;
    server_name localhost;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name localhost;

    ssl_certificate     /etc/nginx/certs/localhost.pem;
    ssl_certificate_key /etc/nginx/certs/localhost-key.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://frontend:3000;

        proxy_set_header Host              $http_host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host  $http_host;

        # next dev 의 핫 리로드(웹소켓)
        proxy_http_version 1.1;
        proxy_set_header Upgrade    $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

- **`X-Forwarded-Proto`와 `Host`를 꼭 넘긴다.** Next.js 입장에서 요청은 nginx에게서 HTTP로 온다. 브라우저가 원래 `https://localhost`로 왔다는 사실은 이 헤더로만 안다. 안 넘기면 리다이렉트가 `http://`로 가거나, Server Action이 "출처가 다르다"며 거절한다.
- **웹소켓 업그레이드:** `Upgrade`, `Connection`을 넘기지 않으면 페이지는 뜨는데 저장해도 갱신이 안 된다.

### 3) compose에 nginx 추가 — 프로필

인증서가 없는 사람도 `docker compose up`이 되어야 하므로 기본으로는 뜨지 않게 한다.

```yaml
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
```

- `profiles: ["https"]`: `docker compose --profile https up -d`일 때만 뜬다.
- `nginx:1.27`의 기본 설정 파일 `/etc/nginx/conf.d/default.conf`를 우리 파일로 덮어쓴다.

### 4) 확인
`https://localhost`에서 자물쇠가 뜨고 경고가 없으면 mkcert CA가 신뢰된 것이다. `http://localhost`는 `https://`로 바뀐다. 로컬에서는 `localhost:3000` 직접 접속도 열어 두고, 서버용 설정에서 닫는다.

## 3. 서버용 compose.prod.yaml

개발용(`compose.yaml` + `compose.override.yaml`)은 포트를 다 열고 소스를 마운트하고 Adminer까지 띄운다. 서버에서는 전부 반대라, override로 되돌리기보다 **서버용 파일을 따로 둔다.**

```yaml
services:
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

| 개발용과 다른 점 | 설명 |
| --- | --- |
| 여는 포트는 `127.0.0.1:${TEAM_PORT}:80` 하나 | `127.0.0.1:` 접두어로 같은 서버 안에서만 접속된다. 빼면 `0.0.0.0`(모든 주소)에 열린다 |
| frontend·backend·postgres·redis는 `ports` 없음 | 서비스 이름으로만 통신한다. Redis에 비밀번호를 안 건 전제("내부 네트워크에서만")가 여기서 지켜진다 |
| 비밀값은 `:?`로 강제 | 변수가 없으면 메시지를 내고 기동을 거부한다. 기본 비밀번호로 뜨는 사고를 막는다 |
| `restart: unless-stopped` | 재부팅되거나 죽으면 도커가 다시 올린다. 직접 `stop`한 것은 올리지 않는다 |
| Adminer 없음 | 운영 DB 관리 화면을 인터넷에 두지 않는다. 필요하면 `docker compose exec postgres psql` |
| `COMPOSE_PROJECT_NAME` | `.env`에 `team1`이면 컨테이너 `team1-backend-1`, 볼륨 `team1_postgres_data`, 네트워크 `team1_default`. 팀끼리 섞이지 않는다 |

### 팀 nginx 서버용 설정 — `nginx/server.conf`

```nginx
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

- **80만 듣고 인증서가 없다.** TLS는 호스트 nginx가 끝냈다.
- **X-Forwarded 헤더를 만들지 않고 넘긴다.** `$http_x_forwarded_proto`는 호스트 nginx가 붙인 값이다. 여기서 `$scheme`을 쓰면 `http`가 되어 Next.js가 HTTP로 왔다고 오해한다. **프록시가 두 층일 때 흔한 실수다.**
- `upstream`으로 이름을 분리해 둔 것은 블루그린 전환 때 `server` 줄만 바꾸기 위해서다.

`.env.example`에는 서버용 항목(`COMPOSE_PROJECT_NAME=team1`, `TEAM_PORT=3101`, 로컬 HTTPS용 `HTTP_PORT`, `HTTPS_PORT`)을 더한다. 팀 번호에 맞춰 team1 → 3101, team2 → 3102 순서다.

### 로컬에서 서버 모양 미리 돌려 보기

```sh
TEAM_PORT=3101 JWT_SECRET='32바이트가-넘는-충분히-긴-비밀-문자열!!' POSTGRES_PASSWORD=team1pw \
  docker compose -f compose.prod.yaml -p team1 up -d --build

docker compose -p team1 ps
# backend 8080/tcp, frontend 3000/tcp, postgres 5432/tcp, redis 6379/tcp  ← 호스트에 안 열림
# nginx   127.0.0.1:3101->80/tcp                                          ← 이것 하나만

# 호스트 nginx 가 붙여 줄 헤더를 흉내 낸다
curl -i -H "Host: team1.newlecture.com" -H "X-Forwarded-Proto: https" http://127.0.0.1:3101/menus   # 200

docker compose -p team1 down -v
```

`-p team1`은 `.env`의 `COMPOSE_PROJECT_NAME`을 명령줄에서 준 것이다. 개발용 스택(폴더 이름 프로젝트)이 떠 있어도 이름이 달라 충돌하지 않는다.

## 4. 호스트 컴퓨터 준비 — 확인하고, 없으면 설정한다

여러 팀의 스택이 함께 올라가는 배포 대상 컴퓨터를 **호스트**라고 부른다. sudo 권한자가 한 번 해 두는 작업이고, 팀원도 요청이 어디를 거쳐 들어오는지 알기 위해 읽는다. 순서는 늘 같다. **점검 스크립트로 무엇이 되어 있는지 보고, 없는 것만 설정 스크립트로 채운다.** 설정 스크립트는 여러 번 실행해도 안전하다(이미 된 것은 건너뛴다).

```sh
bash deploy/host/check-host.sh        # 1) 무엇이 없는지 본다. 바꾸는 것은 없다
sudo bash deploy/host/setup-host.sh   # 2) 없는 것만 채운다
bash deploy/host/check-host.sh        # 3) 다시 본다. 남는 것은 사람이 하는 세 가지(DNS, 인증서, SSH 키)
```

### 1) 호스트와 DNS
- Ubuntu 24.04 한 대 기준. 팀당 1.5GB 정도로 보아 다섯 팀이면 메모리 8GB 이상이 좋다.
- DNS에서 팀 도메인(`team1~team5.newlecture.com`)이 호스트 공개 IP를 가리키게 한다. 와일드카드(`*.newlecture.com`) A 레코드 하나면 팀이 늘어도 손댈 것이 없다.
- 도메인과 팀 목록은 스크립트 맨 위 `DOMAIN`, `TEAMS` 변수다. 팀 nginx 포트는 `BASE_PORT`(3100) + 순번이다.

```sh
sudo DOMAIN=example.com TEAMS="team1 team2 team3" bash deploy/host/setup-host.sh
DOMAIN=example.com TEAMS="team1 team2 team3" bash deploy/host/check-host.sh
```

### 2) 점검 — check-host.sh가 보는 것
바꾸는 것은 없다. `[OK]` / `[없음]` / `[sudo 필요]`로 표시하고, `[없음]` 아래에 채우는 명령(`→`)을 알려 준다.

| 구역 | 확인 항목 | 없으면 |
| --- | --- | --- |
| 1. 도커 | docker 설치, 데몬 실행, compose 플러그인 | `setup-host.sh`, `sudo systemctl enable --now docker` |
| 2. 팀 계정 | 팀 계정 존재, docker 그룹, SSH 공개 키(`~/.ssh/authorized_keys`), `.env` 초안(`~/ncafe.env.example`) | `setup-host.sh`, `sudo usermod -aG docker <팀>`(다시 로그인), 공개 키 추가 |
| 3. 호스트 nginx | nginx 설치·실행, 팀 라우팅 설정(`/etc/nginx/sites-enabled/teams`)에 팀 도메인, HTTPS 적용(`listen 443`), certbot과 자동 갱신 타이머, 80·443 듣는 중 | `setup-host.sh`, `sudo certbot --nginx -d team1.<도메인> ...`, `sudo systemctl enable --now certbot.timer` |
| 4. DNS | 팀 도메인이 공개 IP를 가리키는지 | (원문이 여기서 잘림) |

다른 계정의 홈은 볼 수 없어서, 팀 계정으로 실행하면 일부 항목이 `[sudo 필요]`로 나온다. 전부 보려면 `sudo`로 실행한다.

### (받지 못한 부분)
원문은 4절의 DNS 점검 이후로 잘려 있다. 남은 목차는 다음과 같다.
- 호스트 설정 스크립트(`setup-host.sh`): 계정, 도커, 호스트 nginx, certbot
- 팀별 배포: 호스트에 들어가 올리고 `https://team1.newlecture.com`에서 확인
- 재배포 때 끊김을 직접 보기 → 다음 단계(블루그린 배포)의 동기

## 정리

| 위치 | 하는 일 | 인증서 |
| --- | --- | --- |
| 로컬 | 팀 nginx가 443으로 HTTPS를 직접 풀고 `frontend:3000`에 넘김 (`--profile https`) | mkcert (내 컴퓨터에서만 신뢰) |
| 서버 | 호스트 nginx가 HTTPS를 풀고 도메인으로 팀을 골라 `127.0.0.1:팀포트`로, 팀 nginx가 `frontend`로 넘김 | Let's Encrypt (certbot, 자동 갱신) |

- 밖에 열리는 것은 호스트 nginx의 80·443뿐이고, 팀 nginx는 `127.0.0.1`에만, 나머지 서비스는 내부 네트워크에만 있다.
- 프록시가 두 층이면 안쪽 nginx는 `X-Forwarded-*`를 **만들지 말고 넘긴다.**

다음 단계: GitHub Actions CI/CD([[042_CI_CD와 테스트 서버 배포 참고자료]]) → 블루그린 배포 → JPA로 PostgreSQL 연결.
