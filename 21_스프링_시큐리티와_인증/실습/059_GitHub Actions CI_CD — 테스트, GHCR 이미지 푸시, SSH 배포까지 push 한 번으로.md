---
tags: [GitHubActions, CI, CD, GHCR, Docker, SSH, 배포, 워크플로, 실습]
---

> 🔗 관련 노트: [[058_서버 배포와 HTTPS — nginx 리버스 프록시, 로컬 mkcert, 호스트 certbot, 팀별 서브도메인]] · [[057_도커 컴포즈 — 프론트·백엔드·PostgreSQL·Redis를 한 번에, 리프레시 토큰은 Redis로]] · [[054_인증 JWT+BFF·도커 컴포즈·CI_CD — 팀 프로젝트 공통 구조]]

# GitHub Actions CI/CD — 테스트, GHCR 이미지 푸시, SSH 배포까지 push 한 번으로

> **첨부 파일 안내**
> - `ncafe-prep-12-github-actions.zip`: 이 노트 적용 **전**
> - `ncafe-lesson-12-github-actions.zip`: 이 노트 적용 **후**
>
> 참고 프로젝트 경로: `ncafe-lesson-12-github-actions`  
> 프로젝트 해설: `README-CICD.md`

---

이전 노트([[058_서버 배포와 HTTPS — nginx 리버스 프록시, 로컬 mkcert, 호스트 certbot, 팀별 서브도메인]])에서 프로젝트가 서버에 올라갔다. 그런데 배포는 아직 손으로 한다. 서버에 SSH로 들어가 `git pull`, `docker compose -f compose.prod.yaml up -d --build`를 친다. 팀원 여럿이 번갈아 고치는 프로젝트에서 이 방식은 금방 문제가 된다.

1. 누가 언제 무엇을 올렸는지 남지 않는다. "서버에 있는 코드가 main인가?"에 답할 수 없다.
2. 테스트를 돌리지 않고 올리게 된다. 깨진 코드가 서버에서 발견된다.
3. 호스트에서 빌드한다. 여러 팀이 동시에 빌드하면 호스트가 버겁고, 빌드가 실패하면 반쪽 상태가 남는다.

이번 노트는 이 세 가지를 GitHub Actions 하나로 해결한다. `main`에 push하면 GitHub의 컴퓨터가 테스트를 돌리고, 이미지를 만들어 저장소에 올리고, 서버에 들어가 받아 올린다. 사람이 하는 일은 `git push`까지다.

이 노트는 각 팀이 자기 저장소에 적용하는 참고 노트다. 워크플로 파일에는 저장소 이름이나 팀 번호가 없다. 저장소 소유자는 GitHub가 알려 주고, 호스트 정보는 Secrets로 받는다. 그래서 파일을 그대로 복사해 넣으면 어느 저장소에서든 돈다. 배포 대상 컴퓨터는 11 노트와 같이 **호스트 컴퓨터**라고 부르고, 호스트에 필요한 설정이 되어 있는지는 점검 스크립트로 확인한다.

이번 노트에서는 다음 순서로 진행한다.

1. CI와 CD가 각각 무엇인지, 우리 파이프라인의 세 단계를 정한다.
2. 저장소를 GitHub에 올리고 GHCR(이미지 저장소)을 이해한다.
3. 워크플로 파일을 쓴다. `test` → `build-push` → `deploy` 세 job.
4. `compose.prod.yaml`이 이미지를 받아 쓰도록 바꾼다.
5. 호스트 컴퓨터를 점검하고, 호스트와 GitHub에 열쇠(SSH 키, Secrets)를 둔다.
6. push하고 Actions 탭에서 확인한다. 롤백도 해 본다.

---

## 1. CI와 CD — 세 단계

**CI**(Continuous Integration)는 코드가 저장소에 들어올 때마다 자동으로 빌드하고 테스트하는 것이다. 깨진 코드가 `main`에 들어오기 전에 잡는다. **CD**(Continuous Deployment)는 그 통과한 코드를 자동으로 서버에 올리는 것이다. 둘을 합쳐 파이프라인이라고 부른다.

우리 파이프라인은 세 단계다.

```
git push
  │
  ▼
[test]        ./gradlew test, tsc --noEmit, next build        ← 모든 브랜치에서
  │ 통과하면
  ▼
[build-push]  Dockerfile 로 이미지 빌드 → ghcr.io 에 push      ← main 만
  │
  ▼
[deploy]      호스트에 SSH → git pull, compose pull, compose up  ← main 만
```

GitHub Actions는 이 단계를 GitHub가 빌려 주는 컴퓨터(runner)에서 실행해 주는 서비스다. `.github/workflows/` 폴더에 YAML 파일을 두면 그것이 곧 파이프라인 정의다.

11 노트와 비교하면 **빌드하는 장소**가 바뀐다. 전에는 호스트에서 `--build`로 이미지를 만들었다. 이제 GitHub runner가 만들어 레지스트리에 올리고, 호스트는 완성된 이미지를 받기만 한다.

---

## 2. 저장소와 GHCR

### 1) GitHub에 올리기

```bash
cd ncafe
git remote add origin https://github.com/<팀-아이디>/ncafe.git
git push -u origin main
```

### 2) GHCR — 이미지 저장소

Dockerfile로 만든 이미지는 git에 커밋할 수 없다. 이미지를 올리고 받는 곳이 컨테이너 레지스트리다. GitHub 저장소와 붙여 쓰기에는 **GHCR**(`ghcr.io`)이 편하다.

- 워크플로 안에서는 `GITHUB_TOKEN`이 자동 발급되어 로그인에 쓴다.
- 이미지 이름: `ghcr.io/<소유자>/ncafe-backend` (소유자는 소문자).
- Packages 탭에 보인다.

호스트가 받으려면:

| 방법 | 비고 |
|---|---|
| 패키지를 공개로 | 호스트에 비밀값 없음. 권장 |
| `docker login ghcr.io` + PAT | 소스 비공개가 중요할 때 |

---

## 3. 워크플로 — `.github/workflows/deploy.yml`

```yaml
# CI/CD — push 마다 테스트하고, main 이면 이미지를 만들어 GHCR 에 올리고, 서버에 배포한다.
#
# 저장소 이름이나 팀 번호를 여기 적지 않는다. 어느 저장소에 넣어도 그대로 돈다.
#  - 이미지 이름: ghcr.io/<저장소 소유자>/ncafe-backend, ncafe-frontend  (github.repository_owner 에서 자동)
#  - 서버 정보: Settings → Secrets and variables → Actions 의 Secrets 세 개
#      DEPLOY_HOST     호스트 컴퓨터 주소 (예: 1.2.3.4 또는 newlecture.com)
#      DEPLOY_USER     호스트의 팀 계정 (예: team1)
#      DEPLOY_SSH_KEY  그 계정으로 들어가는 SSH 개인 키 (공개 키는 서버 ~/.ssh/authorized_keys 에)
name: CI/CD

on:
  push:
    branches: ["**"]          # 모든 브랜치: test 까지. main 만 build-push 와 deploy 로 이어진다
  pull_request:
  workflow_dispatch:          # Actions 탭에서 수동 실행

jobs:
  # 1) 테스트와 빌드 검증. 어느 브랜치든 push 하면 돈다
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # 백엔드: JDK 25 + Gradle 캐시
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "25"
      - uses: gradle/actions/setup-gradle@v4
      - name: Backend test
        working-directory: backend
        run: ./gradlew test --no-daemon

      # 프론트엔드: Node 24 + npm 캐시
      - uses: actions/setup-node@v4
        with:
          node-version: "24"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - name: Frontend type check and build
        working-directory: frontend
        run: |
          npm ci
          npx tsc --noEmit
          npm run build

  # 2) 이미지 빌드 → GHCR 푸시. main 에 push 됐을 때만
  build-push:
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write           # GITHUB_TOKEN 으로 GHCR 에 쓸 수 있게
    strategy:
      matrix:
        service: [backend, frontend]      # 두 이미지를 병렬로
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}    # 저장소마다 자동 발급. 따로 만들 것 없다

      # 태그: latest 와 sha-<커밋 7자리>. 이미지 이름은 소문자로 바꿔 준다 (GHCR 규칙)
      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository_owner }}/ncafe-${{ matrix.service }}
          tags: |
            type=raw,value=latest
            type=sha

      - uses: docker/build-push-action@v6
        with:
          context: ./${{ matrix.service }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha,scope=${{ matrix.service }}
          cache-to: type=gha,scope=${{ matrix.service }},mode=max

  # 3) 서버에 SSH 로 들어가 새 이미지를 받아 올린다
  deploy:
    needs: build-push
    runs-on: ubuntu-latest
    environment: production     # Actions 탭에 배포 이력이 남는다
    steps:
      - uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_SSH_KEY }}
          # 11 노트에서 손으로 치던 명령 그대로. 빌드는 하지 않고(--no-build) 받기만 한다
          script: |
            set -e
            cd ~/ncafe
            git pull --ff-only
            docker compose -f compose.prod.yaml pull
            docker compose -f compose.prod.yaml up -d --no-build
            docker image prune -f
            docker compose -f compose.prod.yaml ps

```

### 1) `on` — 언제 도는가

- `push: branches: ["**"]`: 어느 브랜치든 `test`까지.
- `pull_request`: PR 화면에 체크.
- `workflow_dispatch`: Actions 탭 수동 실행.
- `main`만 `build-push`/`deploy`는 job의 `if`로 거른다.

### 2) `test` job

빈 Ubuntu에 JDK 25, Node 24를 깔고 `./gradlew test`, `npx tsc --noEmit`, `npm run build`. 하나라도 실패하면 뒷 단계 중단. Gradle/npm 캐시로 재실행을 빠르게.

### 3) `build-push` job

- `needs: test`, `main`만.
- `permissions: packages: write` — 없으면 GHCR push denied.
- `matrix.service: [backend, frontend]` 병렬.
- 태그: `latest` + `sha-<커밋7자>` (롤백용).
- `cache-from/to: type=gha`로 층 캐시.

### 4) `deploy` job

11 노트에서 손으로 친 명령을 SSH 스크립트로. `--build` → `pull` + `--no-build`.

- `appleboy/ssh-action` + Secrets.
- `git pull --ff-only`, `compose pull`, `up -d --no-build`, `image prune`.
- `environment: production` — 배포 이력.

---

## 4. compose.prod.yaml — 이미지를 받아 쓰기

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
#
# 이미지: GitHub Actions 가 만들어 GHCR 에 올린 것을 받는다 (.env 의 GITHUB_OWNER, IMAGE_TAG).
#   docker compose -f compose.prod.yaml pull && docker compose -f compose.prod.yaml up -d --no-build
# 서버에서 직접 빌드하려면 예전처럼:  docker compose -f compose.prod.yaml up -d --build
# 롤백은 태그를 바꿔 다시 올리는 것:  IMAGE_TAG=sha-abc1234 docker compose -f compose.prod.yaml up -d --no-build
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
    image: ghcr.io/${GITHUB_OWNER:?GITHUB_OWNER 를 .env 에 설정하세요}/ncafe-frontend:${IMAGE_TAG:-latest}
    build: ./frontend
    environment:
      BACKEND_URL: http://backend:8080
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    image: ghcr.io/${GITHUB_OWNER:?GITHUB_OWNER 를 .env 에 설정하세요}/ncafe-backend:${IMAGE_TAG:-latest}
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

- `image:`와 `build:` 둘 다: 평소는 pull, 비상시 `--build` 가능.
- `${GITHUB_OWNER:?...}` — 소문자, `.env`에서.
- `${IMAGE_TAG:-latest}` — 롤백 시 `sha-...`.

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
# GitHub Actions 가 올린 이미지를 받을 때. 소유자는 소문자 (ghcr.io/<owner>/ncafe-backend)
GITHUB_OWNER=your-github-id
IMAGE_TAG=latest

POSTGRES_DB=ncafe
POSTGRES_USER=ncafe
POSTGRES_PASSWORD=ncafe1234

```

호스트 `~/ncafe/.env`에도 `GITHUB_OWNER`를 채운다. `check-host.sh`가 비어 있거나 대문자면 알려 준다.

---

## 5. 호스트 점검과 열쇠

### 0) 준비되어 있는가

팀 계정·docker 그룹, `~/ncafe`, `.env`의 `GITHUB_OWNER`, 배포용 SSH 공개 키, 호스트 nginx·인증서.

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
    # CI/CD 노트: deploy job 이 들어갈 ~/ncafe 와 .env 의 GITHUB_OWNER
    if [ -d "/home/$team/ncafe/.git" ]; then
      ok "$team ~/ncafe 저장소"
      env="/home/$team/ncafe/.env"
      owner=$(grep -E '^GITHUB_OWNER=' "$env" 2>/dev/null | cut -d= -f2-)
      if [ -z "$owner" ] || [ "$owner" = "github-id-here" ] || [ "$owner" = "your-github-id" ]; then
        miss "$team ~/ncafe/.env 의 GITHUB_OWNER 가 비어 있다" "GITHUB_OWNER=<GitHub 아이디, 소문자> 를 $env 에 적는다"
      elif [ "$owner" != "$(printf '%s' "$owner" | tr 'A-Z' 'a-z')" ]; then
        miss "$team GITHUB_OWNER=$owner 에 대문자가 있다" "ghcr.io 이미지 이름은 소문자다. 소문자로 바꾼다"
      else
        ok "$team GITHUB_OWNER=$owner"
      fi
    else
      miss "$team ~/ncafe 저장소가 없다" "그 계정으로: git clone <저장소 주소> ~/ncafe && cp ~/ncafe.env.example ~/ncafe/.env"
    fi
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

```bash
ssh team1@호스트주소
cd ~/ncafe && git pull
bash deploy/host/check-host.sh
```

### 1) 배포 전용 키

```bash
ssh-keygen -t ed25519 -C "ncafe-deploy" -f ncafe-deploy -N ""
# 공개 키 → 호스트 authorized_keys
# 개인 키 → GitHub Secrets DEPLOY_SSH_KEY
ssh -i ncafe-deploy team1@호스트주소 'docker compose version'
```

### 2) GitHub Secrets

| 이름 | 값 |
|---|---|
| `DEPLOY_HOST` | 호스트 주소 |
| `DEPLOY_USER` | `team1` |
| `DEPLOY_SSH_KEY` | 개인 키 전체 |

워크플로에는 `${{ secrets.DEPLOY_HOST }}`처럼 이름만. 공개 저장소에 둬도 된다.

---

## 6. push하고 확인하기

```bash
git add .github/workflows/deploy.yml compose.prod.yaml .env.example
git commit -m "ci: GitHub Actions 로 테스트·이미지 빌드·배포"
git push origin main
```

Actions 탭: `test` → `build-push`(병렬) → `deploy`. deploy 로그 끝의 `compose ps`가 Up이면 끝.

### 흔한 첫 실패

| 증상 | 원인 |
|---|---|
| GHCR denied | `packages: write` 또는 Workflow permissions |
| `~/ncafe` 없음 | clone 안 함 |
| Permission denied (publickey) | 공개 키/Secrets 키 |
| pull unauthorized | 패키지 비공개 |
| manifest unknown | `GITHUB_OWNER` 오타·대문자 |
| gradlew Permission denied | `git update-index --chmod=+x backend/gradlew` |

### 롤백

```bash
IMAGE_TAG=sha-abc1234 docker compose -f compose.prod.yaml up -d --no-build
```

또는 `git revert` 후 push.

재배포 중 잠깐 502는 아직 있다 → 다음 노트 블루그린.

---

## 7. 주의할 사항과 정리

1. **로컬 Gradle vs compose 마운트** — 호스트에서 `./gradlew test` 칠 때 `docker compose stop backend`.
2. **워크플로에 비밀·팀 정보 없음** — 복사해도 고칠 곳 없음.
3. **main = 배포** — PR·리뷰 습관, branch protection.
4. **호스트 `--build`는 비상용** — Actions 이미지와 섞이면 추적이 깨짐.

| 단계 | 어디서 | 조건 |
|---|---|---|
| test | runner | 모든 push, PR |
| build-push | runner → GHCR | main |
| deploy | 호스트 SSH | build-push 성공 |

### 이번 노트에서 추가·수정된 파일

**추가** `.github/workflows/deploy.yml`

**수정** `compose.prod.yaml` (`image:`), `.env.example`, `deploy/host/setup-host.sh`, `deploy/host/check-host.sh`

**GitHub** Secrets 세 개, Packages 공개(또는 login)

**호스트** 배포용 공개 키, `GITHUB_OWNER`

---

## 마무리

`git push`가 배포의 전부가 되었다. 테스트가 깨지면 호스트에 가지 않고, 호스트에는 GitHub가 만든 이미지만 올라가며, 어느 커밋이 돌고 있는지는 태그로 남는다. 다음 노트는 블루그린으로 교체 중 끊김을 없앤다.
