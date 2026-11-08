---
tags: [블루그린, 무중단배포, nginx, DockerCompose, CI, CD, 헬스체크, 롤백, 실습]
---

> 🔗 관련 노트: [[059_GitHub Actions CI_CD — 테스트, GHCR 이미지 푸시, SSH 배포까지 push 한 번으로]] · [[058_서버 배포와 HTTPS — nginx 리버스 프록시, 로컬 mkcert, 호스트 certbot, 팀별 서브도메인]] · [[057_도커 컴포즈 — 프론트·백엔드·PostgreSQL·Redis를 한 번에, 리프레시 토큰은 Redis로]]

# 블루그린 배포 — 새 버전을 옆에 띄우고 nginx upstream 전환, 무중단과 롤백

> **첨부 파일 안내**
> - `ncafe-prep-13-blue-green.zip`: 이 노트 적용 **전**
> - `ncafe-lesson-13-blue-green.zip`: 이 노트 적용 **후**
>
> 참고 프로젝트 경로: `ncafe-lesson-13-blue-green`  
> 프로젝트 해설: `README-Blue-Green.md`

---

이전 노트([[059_GitHub Actions CI_CD — 테스트, GHCR 이미지 푸시, SSH 배포까지 push 한 번으로]])에서 `git push`가 배포의 전부가 되었다. 테스트가 돌고, 이미지가 GHCR에 올라가고, 호스트가 그것을 받아 올린다. 그런데 **올리는 순간**은 아직 거칠다. `docker compose up -d`는 바뀐 서비스의 컨테이너를 지우고 새로 만든다. 스프링이 다시 뜨는 10~20초 동안 로그인과 재발급이 실패하고, Next.js가 교체되는 몇 초는 nginx가 502 Bad Gateway를 낸다. 새 버전에 문제가 있어도 이미 옛 버전은 사라진 뒤라서, 되돌리려면 또 한 번 그 끊김을 겪어야 한다.

이번 노트는 그 두 가지, **끊김**과 **되돌리기**를 해결한다. 방법은 **블루그린 배포**다. 프론트엔드와 백엔드를 두 벌(`blue`, `green`) 두고 한 벌만 트래픽을 받는다. 새 버전은 쉬고 있는 벌에 띄워 먼저 확인하고, 통과하면 nginx가 보내는 곳을 바꾼다. 통과하지 못하면 바꾸지 않는다. 그게 롤백이다.

11 노트에서 팀 nginx의 `upstream frontend_upstream` 블록을 미리 분리해 둔 것이 여기서 쓰인다. 12 노트의 deploy job 마지막 줄이 이번 노트의 스크립트로 바뀐다.

이번 노트에서는 다음 순서로 진행한다.

1. 배포 전략 셋을 비교하고 블루그린을 고르는 이유를 본다.
2. `compose.prod.yaml`에 frontend·backend를 두 벌 둔다. YAML 앵커와 프로필.
3. 팀 nginx의 upstream을 파일로 빼서 바꿔 끼울 수 있게 한다.
4. 전환 스크립트 `deploy/blue-green.sh`: 띄우기 → 헬스체크 → 전환 → 정지, 그리고 롤백.
5. 12 노트의 워크플로에 연결한다.
6. 로컬에서 전환 중에 요청을 계속 보내 끊김이 0인지, 로그인이 유지되는지, 롤백과 실패 처리를 확인한다.

---

## 1. 배포 전략 — 왜 블루그린인가

새 버전을 올리는 방법은 크게 셋이다.

| 전략 | 방식 | 끊김 | 롤백 | 비용 |
|---|---|---|---|---|
| Recreate (지금까지) | 옛것을 멈추고 새것을 켠다 | 기동 시간만큼 | 다시 배포 (또 끊김) | 없음 |
| Rolling | 인스턴스 여럿을 하나씩 교체 | 없음 | 교체를 되감기 | 인스턴스가 여럿이어야 함 |
| Blue/Green | 두 벌 중 한 벌만 트래픽. 새 버전을 쉬는 벌에 올려 검증 후 한 번에 전환 | 없음 | 보내는 곳을 되돌리기 (몇 초) | 전환 전후 잠깐 두 배 |

Rolling은 두 버전이 동시에 트래픽을 받는 시간이 있고, 쿠버네티스처럼 인스턴스를 여럿 두는 환경에서 자연스럽다. 우리는 팀마다 컨테이너 한 벌이고, 전환 지점(nginx)을 이미 가지고 있다. **블루그린이 맞다.**

![[blue-green-deploy.png]]

핵심은 **상태는 색 밖에 둔다**는 것이다. PostgreSQL과 Redis는 한 벌이고 두 색이 같이 쓴다. 그래서 blue에서 로그인한 사용자가 green으로 넘어가도 Redis의 리프레시 토큰이 그대로 있어 로그아웃되지 않는다. 10 노트에서 토큰 저장소를 백엔드 메모리에서 Redis로 옮긴 결정이 여기서 값을 한다. 메모리에 있었다면 색을 바꿀 때마다 전원 로그아웃이다.

왜 프론트엔드만 아니라 백엔드까지 색을 나누는가. 프론트와 백엔드는 한 커밋에서 같이 바뀐다. 09 노트처럼 백엔드 응답 모양이 바뀌면 프론트도 같이 바뀌는데, 프론트만 교체하고 백엔드는 그대로면 새 프론트가 옛 백엔드를 부르는 짝이 안 맞는 순간이 생긴다. 그래서 `frontend-green`은 `backend-green`만 보고, 둘이 한 벌로 움직인다.

---

## 2. compose.prod.yaml — frontend·backend 두 벌

```yaml
# 서버용 compose. 개발용(compose.yaml + compose.override.yaml)과 따로 둔다.
#
# 개발용과 다른 점
#  - 호스트에 여는 포트는 nginx 의 80 하나뿐이고, 그것도 127.0.0.1 에만 묶는다.
#    외부에서는 호스트 nginx(team1.newlecture.com, HTTPS)를 거쳐야만 들어올 수 있다.
#  - frontend, backend, postgres, redis 는 포트를 열지 않는다. 컨테이너끼리 서비스 이름으로만 통신한다.
#  - adminer 는 띄우지 않는다. DB 는 서버에서 psql 로 본다.
#  - 소스 마운트 없음. GitHub Actions 가 GHCR 에 올린 이미지를 받아 그대로 실행한다 (.env 의 GITHUB_OWNER, IMAGE_TAG).
#
# .env 에 COMPOSE_PROJECT_NAME(team1)과 TEAM_PORT(3101)를 둔다.
# 프로젝트 이름이 컨테이너·볼륨·네트워크 이름의 접두어가 되어, 한 호스트에서 팀끼리 섞이지 않는다.
#
# 블루그린: frontend 와 backend 가 blue, green 두 벌이다. 한 벌만 트래픽을 받고(nginx upstream),
# 배포는 쉬고 있는 색에 새 이미지를 띄워 헬스체크를 통과하면 nginx 를 그쪽으로 돌리는 것이다.
# postgres, redis, nginx 는 한 벌을 두 색이 같이 쓴다. 이 파일을 직접 up 하지 않고 스크립트로 다룬다.
#   bash deploy/blue-green.sh deploy      # 쉬는 색에 새 버전 → 헬스체크 → 전환 → 이전 색 정지
#   bash deploy/blue-green.sh rollback    # 이전 색을 다시 켜서 되돌림
#   bash deploy/blue-green.sh status      # 어느 색이 트래픽을 받고 있는지

# 두 색이 공통으로 쓰는 설정. 아래에서 <<: *frontend 로 끌어다 쓴다 (YAML 앵커)
x-frontend: &frontend
  image: ghcr.io/${GITHUB_OWNER:?GITHUB_OWNER 를 .env 에 설정하세요}/ncafe-frontend:${IMAGE_TAG:-latest}
  build: ./frontend
  restart: unless-stopped

x-backend: &backend
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

services:

  # 팀 nginx. 호스트 nginx 가 127.0.0.1:${TEAM_PORT} 로 넘겨 준 요청을 활성 색의 frontend 에 전달한다.
  # 어느 색인지는 nginx/upstream/active.conf 에 있고, 이 파일은 블루그린 스크립트가 쓴다 (git 에 없다).
  nginx:
    image: nginx:1.27
    ports:
      - "127.0.0.1:${TEAM_PORT:-3101}:80"
    volumes:
      - ./nginx/server.conf:/etc/nginx/conf.d/default.conf:ro
      - ./nginx/upstream:/etc/nginx/upstream:ro
    restart: unless-stopped

  # ---- blue ----
  frontend-blue:
    <<: *frontend
    profiles: ["blue"]
    environment:
      BACKEND_URL: http://backend-blue:8080
    depends_on:
      - backend-blue

  backend-blue:
    <<: *backend
    profiles: ["blue"]

  # ---- green ----
  frontend-green:
    <<: *frontend
    profiles: ["green"]
    environment:
      BACKEND_URL: http://backend-green:8080
    depends_on:
      - backend-green

  backend-green:
    <<: *backend
    profiles: ["green"]

  # ---- 두 색이 공유 ----
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

- `x-frontend: &frontend`: compose는 최상위에서 `x-`로 시작하는 키를 무시한다. 그 자리에 공통 설정을 적고 YAML 앵커(`&frontend`)를 붙인 뒤, 서비스에서 `<<: *frontend`로 끌어다 쓴다(YAML merge key). blue와 green의 이미지, 빌드, 재시작 정책이 한 곳에만 적힌다. 서비스 안에 같은 키를 다시 쓰면 그것이 이긴다. `frontend-blue`의 `environment`와 `depends_on`이 그렇다.
- `profiles: ["blue"]`: 프로필이 붙은 서비스는 그냥 `up` 하면 뜨지 않는다. `--profile blue`를 붙이거나 서비스 이름을 직접 쓰면(`up -d frontend-blue backend-blue`) 그때만 뜬다. 스크립트는 후자를 쓴다. postgres, redis, nginx는 프로필이 없어 늘 뜬다.
- `BACKEND_URL: http://backend-blue:8080`: 색마다 자기 백엔드를 본다. 1절의 "한 벌로 움직인다"가 이 한 줄이다.
- `./nginx/upstream:/etc/nginx/upstream:ro`: 파일 하나가 아니라 **폴더**를 마운트한다. 안의 `active.conf`를 스크립트가 바꿔 쓰는데, 파일 하나를 마운트하면 교체(inode가 바뀜) 때 컨테이너 안에서 옛 파일이 보이는 문제가 있다. 폴더면 안전하다.

이 파일을 직접 `up` 하지 않는다. 어느 색을 띄울지, 언제 nginx를 돌릴지는 스크립트가 정한다. 11, 12 노트의 `docker compose -f compose.prod.yaml up -d --no-build`는 이제 `bash deploy/blue-green.sh deploy`다.

---

## 3. 팀 nginx — upstream을 파일로

```nginx
# 서버용 "팀 nginx" 설정 (compose.prod.yaml 의 nginx 서비스)
#
# 인터넷 → 호스트 nginx (team1.newlecture.com, 443, certbot 인증서)
#        → http://127.0.0.1:3101 (이 nginx, 80)
#        → http://frontend-blue:3000 또는 frontend-green:3000  (활성 색)
#
# HTTPS 는 호스트 nginx 가 끝냈으므로 여기는 80 만 듣는다.
# 호스트 nginx 가 넘겨 준 X-Forwarded-* 헤더를 그대로 frontend 에 전달한다.
#
# upstream 은 nginx/upstream/active.conf 에 따로 있다. 블루그린 스크립트가 그 파일의 서버 한 줄을
# 바꾸고 nginx -s reload 하는 것으로 트래픽이 넘어간다. 이 파일은 바뀌지 않는다.
include /etc/nginx/upstream/active.conf;

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

upstream 블록이 사라지고 `include /etc/nginx/upstream/active.conf;` 한 줄이 왔다. 그 파일은 스크립트가 쓰고, 내용은 이렇다.

```nginx
# deploy/blue-green.sh 가 쓴다. 손으로 고치지 않는다
upstream frontend_upstream {
    zone frontend_upstream 64k;
    resolver 127.0.0.11 valid=5s;
    server frontend-blue:3000 resolve;
}

```

- `server frontend-blue:3000 resolve;`: 전환은 이 줄의 blue를 green으로 바꾸고 `nginx -s reload` 하는 것이 전부다.
- `resolve`와 `resolver 127.0.0.11`: nginx는 보통 설정을 읽을 때 호스트 이름을 한 번 IP로 바꿔 두고 끝이다. 컨테이너가 재시작해 IP가 바뀌면 nginx는 옛 IP로 보내 502가 난다. `resolve`를 붙이면 도커 내장 DNS(`127.0.0.11`)에 `valid=5s`마다 다시 물어 따라간다. `zone`은 resolve가 요구하는 공유 메모리다. 오픈소스 nginx 1.27.3부터 되고, 우리는 `nginx:1.27`(1.27.5)이다.
- `nginx -s reload`는 끊지 않는다. 새 설정으로 워커 프로세스를 새로 띄우고, 옛 워커는 처리 중이던 요청을 끝낸 뒤 내려간다. 새 연결은 새 워커가 받는다. 그래서 전환 중에 실패하는 요청이 없다. 6절에서 숫자로 확인한다.

`active.conf`는 호스트마다 다른 상태이므로 git에 넣지 않는다. 폴더에 `.gitignore`를 두었다.

```gitignore
# active.conf 는 블루그린 스크립트가 쓰는 상태 파일이다. 서버마다 다르므로 커밋하지 않는다
active.conf

```

같은 폴더의 `README.md`가 이 폴더가 무엇인지 적어 둔다. git은 빈 폴더를 저장하지 않으므로, 이 두 파일이 있어야 저장소를 받은 호스트에 폴더가 생기고 compose가 마운트할 수 있다.

```markdown
`deploy/blue-green.sh` 가 여기에 `active.conf` 를 쓴다. 내용은 한 블록이다.

```nginx
upstream frontend_upstream {
    server frontend-blue:3000;     # 또는 frontend-green:3000
}
```

팀 nginx(`nginx/server.conf`)가 이 파일을 `include` 하고, 스크립트가 서버 이름을 바꾼 뒤 `nginx -s reload` 하면 트래픽이 다른 색으로 넘어간다. 이 폴더는 compose 가 nginx 컨테이너의 `/etc/nginx/upstream` 에 마운트한다.

```

---

## 4. 전환 스크립트 — deploy/blue-green.sh

```bash
#!/usr/bin/env bash
# 블루그린 배포 스크립트. 서버의 프로젝트 폴더(compose.prod.yaml 이 있는 곳)에서 실행한다. 어디서 실행해도 그 폴더로 이동한다.
#
#   bash deploy/blue-green.sh deploy      # 쉬는 색에 새 이미지 → 헬스체크 → nginx 전환 → 이전 색 정지
#   bash deploy/blue-green.sh rollback    # 정지해 둔 이전 색을 다시 켜서 되돌린다 (헬스체크 뒤 전환)
#   bash deploy/blue-green.sh status      # 활성 색과 컨테이너 상태
#   IMAGE_TAG=sha-abc1234 bash deploy/blue-green.sh deploy    # 특정 태그를 배포 (롤백의 다른 길)
#   SKIP_PULL=1 bash deploy/blue-green.sh deploy               # 로컬에서 시험할 때: GHCR 에서 받지 않고 로컬 이미지 사용
#
# 상태는 nginx/upstream/active.conf 한 파일이다. 팀 nginx 가 이 파일을 include 하고,
# 여기 적힌 색(frontend-blue 또는 frontend-green)이 트래픽을 받는다. git 에는 들어가지 않는다.
set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE="docker compose -f compose.prod.yaml"
ACTIVE_FILE=nginx/upstream/active.conf
HEALTH_RETRIES=${HEALTH_RETRIES:-30}        # 2초 × 30 = 최대 60초 기다린다

log() { printf '[blue-green] %s\n' "$*"; }

# active.conf 에서 지금 트래픽을 받는 색을 읽는다. 파일이 없으면(첫 배포) 빈 문자열
active_color() {
  [ -f "$ACTIVE_FILE" ] && sed -n 's/.*frontend-\(blue\|green\):3000.*/\1/p' "$ACTIVE_FILE" || true
}
other() { [ "$1" = blue ] && echo green || echo blue; }

# upstream 파일을 쓴다. resolve 를 붙여 컨테이너가 재시작해 IP 가 바뀌어도 nginx 가 5초 안에 따라가게 한다
write_active() {
  cat > "$ACTIVE_FILE" <<CONF
# deploy/blue-green.sh 가 쓴다. 손으로 고치지 않는다
upstream frontend_upstream {
    zone frontend_upstream 64k;
    resolver 127.0.0.11 valid=5s;
    server frontend-$1:3000 resolve;
}
CONF
}

# 새 색의 frontend 가 BFF 로 backend 까지 응답하는지 본다. 컨테이너 안에서 자기 자신을 부른다.
# localhost 가 아니라 127.0.0.1 인 이유: alpine 에서 localhost 는 ::1 로 풀리고 Next.js 는 IPv4 만 듣는다
health() {
  local color=$1 i
  for ((i = 1; i <= HEALTH_RETRIES; i++)); do
    if $COMPOSE exec -T "frontend-$color" wget -qO /dev/null http://127.0.0.1:3000/api/menus 2>/dev/null; then
      log "헬스체크 통과: frontend-$color → backend-$color (${i}번째 시도)"
      return 0
    fi
    sleep 2
  done
  log "헬스체크 실패: frontend-$color 가 $((HEALTH_RETRIES * 2))초 안에 응답하지 않았다"
  return 1
}

# upstream 파일을 바꾸고 nginx 를 reload 한다. 열려 있던 연결은 끝까지 처리되고 새 연결부터 새 색으로 간다
switch_to() {
  write_active "$1"
  $COMPOSE exec -T nginx nginx -s reload
  log "nginx 전환 → frontend-$1"
}

cmd_status() {
  local cur; cur=$(active_color)
  log "활성 색: ${cur:-없음}   (IMAGE_TAG=${IMAGE_TAG:-latest})"
  $COMPOSE --profile blue --profile green ps -a --format 'table {{.Service}}\t{{.Image}}\t{{.Status}}'
}

cmd_deploy() {
  local cur new
  cur=$(active_color)
  if [ -z "$cur" ]; then
    new=blue
    log "첫 배포: blue 로 시작한다"
    write_active "$new"                        # nginx 가 뜨려면 이 파일이 있어야 한다
  else
    new=$(other "$cur")
    log "활성 색은 $cur. 새 버전(${IMAGE_TAG:-latest})을 $new 에 띄운다"
  fi

  if [ "${SKIP_PULL:-0}" = 1 ]; then
    log "SKIP_PULL=1: 이미지를 받지 않고 로컬에 있는 것을 쓴다 (로컬 시험용)"
  else
    $COMPOSE pull --quiet "backend-$new" "frontend-$new"
  fi
  $COMPOSE up -d --no-build postgres redis nginx            # 공유 서비스. 이미 떠 있으면 그대로
  $COMPOSE up -d --no-build "backend-$new" "frontend-$new"  # 쉬는 색을 새 이미지로 교체. 활성 색은 건드리지 않는다

  if ! health "$new"; then
    log "전환하지 않는다. ${cur:+$cur 가 그대로 트래픽을 받는다. }원인은:  $COMPOSE logs backend-$new frontend-$new"
    $COMPOSE stop "frontend-$new" "backend-$new"
    exit 1
  fi

  switch_to "$new"
  if [ -n "$cur" ]; then
    $COMPOSE stop "frontend-$cur" "backend-$cur"            # 지우지 않고 멈춘다. rollback 이 다시 켠다
    log "$cur 정지. 되돌리려면:  bash deploy/blue-green.sh rollback"
  fi
  docker image prune -f >/dev/null
  cmd_status
}

cmd_rollback() {
  local cur prev
  cur=$(active_color)
  [ -n "$cur" ] || { log "활성 색이 없다. 먼저 deploy 한다"; exit 1; }
  prev=$(other "$cur")
  log "활성 색은 $cur. 멈춰 둔 $prev 를 다시 켠다"
  $COMPOSE start "backend-$prev" "frontend-$prev"           # up 이 아니라 start: 이미지를 바꾸지 않고 그대로 켠다
  if ! health "$prev"; then
    log "$prev 도 응답하지 않는다. 전환하지 않는다"
    exit 1
  fi
  switch_to "$prev"
  $COMPOSE stop "frontend-$cur" "backend-$cur"
  cmd_status
}

case "${1:-}" in
  deploy)   cmd_deploy ;;
  rollback) cmd_rollback ;;
  status)   cmd_status ;;
  *) echo "사용법: bash deploy/blue-green.sh deploy | rollback | status"; exit 2 ;;
esac

```

위에서부터 읽는다.

### 1) 상태는 active.conf 하나

어느 색이 트래픽을 받는지는 어디에도 따로 적지 않는다. nginx가 실제로 읽는 파일에서 `frontend-blue` 또는 `frontend-green`을 `sed`로 뽑는다(`active_color`). 상태를 두 곳에 두면 어긋난다. 파일이 없으면 첫 배포다.

### 2) health — 전환해도 되는가

새 색의 frontend 컨테이너 안에서 `wget`으로 자기 자신의 `/api/menus`를 부른다. 이 한 요청이 Next.js 기동 → Route Handler(BFF) → `backend-<색>:8080` → 스프링 기동까지 **한 벌 전체**를 통과한다. 2초마다 최대 30번(60초) 기다린다. 스프링 기동이 보통 5~15초이므로 넉넉하다.

`localhost`가 아니라 `127.0.0.1`인 데는 이유가 있다. alpine의 `localhost`는 IPv6 `::1`로 먼저 풀리는데 Next.js standalone은 IPv4(`0.0.0.0`)만 듣는다. `localhost`로 부르면 Connection refused가 나와 헬스체크가 늘 실패한다.

### 3) switch_to — 바꾸고 reload

`active.conf`를 다시 쓰고 nginx 컨테이너에 `nginx -s reload`를 보낸다. `exec -T`의 `-T`는 터미널을 붙이지 않는다는 뜻으로, GitHub Actions의 SSH처럼 터미널이 없는 곳에서 필요하다.

### 4) deploy — 순서가 전부다

1. 활성 색을 읽는다. 없으면 blue로 시작하고 `active.conf`를 먼저 쓴다(nginx가 뜨려면 파일이 있어야 한다).
2. 쉬는 색의 이미지만 `pull` 한다.
3. 공유 서비스(postgres, redis, nginx)를 `up -d`. 이미 떠 있으면 아무 일도 없다.
4. 쉬는 색을 `up -d --no-build`. 이미지가 바뀌었으면 compose가 그 컨테이너를 새로 만든다. **활성 색은 한 번도 건드리지 않는다.**
5. 헬스체크. 실패하면 전환하지 않고, 새 색을 멈추고, 종료 코드 1로 끝난다. 활성 색은 그동안 계속 트래픽을 받고 있었다.
6. 통과하면 전환. 그 다음에야 이전 색을 `stop` 한다. 지우지 않는다. 롤백이 다시 켤 것이기 때문이다.
7. 쓰지 않는 이미지를 지우고 상태를 찍는다.

### 5) rollback — 멈춰 둔 것을 켠다

이전 색을 `start` 한다. `up`이 아니다. `up`은 compose 파일과 비교해 컨테이너를 새로 만들 수 있지만, `start`는 멈춘 그 컨테이너를 그대로 켠다. 직전까지 돌던 바로 그 버전이다. 헬스체크를 통과하면 전환하고, 지금 색을 멈춘다. 되돌리는 데 몇 초면 된다.

### 6) status, SKIP_PULL, HEALTH_RETRIES

`status`는 활성 색과 두 색의 컨테이너를 멈춘 것까지(`ps -a`) 보여 준다. `docker compose -f compose.prod.yaml ps`를 그냥 치면 프로필이 꺼져 있어 색 컨테이너가 안 보인다는 점을 기억한다. `SKIP_PULL=1`은 GHCR에서 받지 않고 로컬 이미지를 쓴다. 6절에서 쓴다. `HEALTH_RETRIES`는 기다리는 횟수다.

---

## 5. 워크플로에 연결

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
          # 블루그린 스크립트가 pull → 쉬는 색에 기동 → 헬스체크 → nginx 전환 → 이전 색 정지를 한다.
          # 헬스체크에 실패하면 전환하지 않고 종료 코드 1 로 끝나 이 job 이 빨간불이 된다. 서비스는 이전 색이 계속 받는다
          script: |
            set -e
            cd ~/ncafe
            git pull --ff-only
            bash deploy/blue-green.sh deploy

```

바뀐 것은 deploy job의 `script` 세 줄이다. `compose pull`, `up -d`, `image prune`, `ps`가 모두 스크립트 안으로 들어갔다. 바깥에 남은 것은 `git pull --ff-only` 하나로, compose 파일이나 nginx 설정, 스크립트 자체가 바뀌었을 수 있으니 먼저 맞춘다.

헬스체크가 실패하면 스크립트가 1로 끝나고 `set -e` 때문에 job이 빨간불이 된다. 그런데 **서비스는 멀쩡하다.** 이전 색이 계속 받고 있다. "배포 실패 = 장애"가 아니게 된 것이 이번 노트의 결과다. Actions 탭의 빨간불을 보고 `docker compose -f compose.prod.yaml logs backend-green`을 보면 된다.

---

## 6. 로컬에서 확인

호스트에 올리기 전에 내 컴퓨터에서 같은 파일, 같은 스크립트로 전부 확인한다. 10 노트의 개발용 스택이 떠 있어도 프로젝트 이름이 달라 섞이지 않는다. GHCR에는 아직 이미지가 없으니 로컬에서 빌드하고 `SKIP_PULL=1`로 띄운다.

```bash
# .env 대신 셸 변수로 (프로젝트 이름 team1, 포트 3101)
export COMPOSE_PROJECT_NAME=team1 TEAM_PORT=3101 GITHUB_OWNER=<github-아이디> \
       JWT_SECRET=로컬-시험용-32바이트-이상-비밀 POSTGRES_PASSWORD=pw SKIP_PULL=1

# GHCR 이름으로 로컬 빌드 (image: 에 적힌 이름으로 태그된다)
docker compose -f compose.prod.yaml build frontend-blue backend-blue

# 1) 첫 배포 → blue
bash deploy/blue-green.sh deploy
# [blue-green] 첫 배포: blue 로 시작한다
# [blue-green] 헬스체크 통과: frontend-blue → backend-blue (3번째 시도)
# [blue-green] nginx 전환 → frontend-blue
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: team1.newlecture.com' -H 'X-Forwarded-Proto: https' http://127.0.0.1:3101/menus
# 200
```

### 1) 전환 중 끊김 — 0이어야 한다

한쪽 터미널에서 0.1초마다 요청을 보내며 응답 코드를 쌓고, 그동안 다른 터미널에서 배포한다.

```bash
# 터미널 A — 45초 동안 계속 요청
( end=$((SECONDS+45)); while [ $SECONDS -lt $end ]; do
    curl -s -o /dev/null -w '%{http_code}\n' --max-time 5 \
         -H 'Host: team1.newlecture.com' -H 'X-Forwarded-Proto: https' http://127.0.0.1:3101/menus
    sleep 0.1
  done ) > codes.txt

# 터미널 B — 그 사이에 배포 (blue → green)
bash deploy/blue-green.sh deploy

# 터미널 A 가 끝난 뒤
sort codes.txt | uniq -c
#     357 200
```

357건 전부 200이다. 11 노트에서 `up -d --build`로 재배포하며 보았던 502가 하나도 없다.

### 2) 로그인이 유지된다

blue에서 로그인해 받은 리프레시 토큰이 green에서도 통하는지 본다. 백엔드는 포트를 열지 않았으니 컨테이너 안에서 부른다.

```bash
# (전환 전) blue 에서 로그인
RT=$(docker compose -f compose.prod.yaml exec -T frontend-blue wget -qO- \
       --header 'Content-Type: application/json' \
       --post-data '{"username":"newlec","password":"123"}' \
       http://backend-blue:8080/api/auth/login | sed -n 's/.*"refreshToken":"\([^"]*\)".*/\1/p')

# (전환 뒤) green 에서 그 토큰으로 재발급
docker compose -f compose.prod.yaml exec -T frontend-green wget -S -qO- \
       --header 'Content-Type: application/json' \
       --post-data "{\"refreshToken\":\"$RT\"}" http://backend-green:8080/api/auth/refresh
#   HTTP/1.1 200
```

`backend-blue`가 Redis에 저장한 토큰을 `backend-green`이 읽었다. 브라우저 사용자는 전환을 모른다.

### 3) 롤백

```bash
bash deploy/blue-green.sh rollback
# [blue-green] 활성 색은 green. 멈춰 둔 blue 를 다시 켠다
# [blue-green] 헬스체크 통과: frontend-blue → backend-blue
# [blue-green] nginx 전환 → frontend-blue
```

### 4) 고장난 버전 — 전환하지 않는다

```bash
docker tag nginx:1.27     ghcr.io/<github-아이디>/ncafe-frontend:bad
docker tag redis:7-alpine ghcr.io/<github-아이디>/ncafe-backend:bad

IMAGE_TAG=bad HEALTH_RETRIES=5 bash deploy/blue-green.sh deploy
# 헬스체크 실패 → 전환하지 않는다. blue 가 그대로 트래픽을 받는다
echo $?        # 1
```

실패했는데 사용자는 아무것도 못 느꼈다.

### 5) 특정 태그로 배포

```bash
IMAGE_TAG=sha-abc1234 bash deploy/blue-green.sh deploy
```

### 6) 정리

```bash
docker compose -f compose.prod.yaml --profile blue --profile green down -v
rm nginx/upstream/active.conf
```

| 확인 | 결과 |
|---|---|
| 전환(blue → green) 중 요청 | 전부 200 |
| 롤백(green → blue) 중 요청 | 전부 200 |
| 고장난 이미지 배포 중 요청 | 전부 200, 전환 안 함, 종료 코드 1 |
| blue 리프레시 → green 재발급 | 200 |
| `IMAGE_TAG=sha-...` 배포 | 그 태그가 쉬는 색에 뜨고 status에 찍힘 |

---

## 7. 주의할 사항과 정리

1. **실패한 배포는 롤백 자리를 쓴다** — `deploy`가 실패하면 쉬는 색에 고장난 컨테이너가 남는다. 이 상태에서 `rollback`을 치면 그 고장난 것을 켜려다 헬스체크에 실패해 전환하지 않는다(안전하다). 이전 정상 버전으로 가려면 `IMAGE_TAG=sha-<이전 커밋> bash deploy/blue-green.sh deploy`로 태그를 지정해 배포한다. `rollback`은 "직전 배포가 성공했는데 문제가 있더라"일 때 쓰는 명령이다.

2. **DB 스키마는 두 버전과 호환되어야 한다** — 전환 전후로 blue와 green이 같은 PostgreSQL을 본다. 규칙은 추가는 한 번에, 삭제·변경은 두 번에다.

3. **전환 전후에 자원이 두 배다** — 헬스체크부터 이전 색 정지까지 JVM이 둘 돈다. 정지한 색은 메모리를 쓰지 않는다.

4. **헬스체크가 보는 것은 하나다** — `/api/menus` 하나가 200이면 통과다. 다음 노트들에서 DB가 들어오면 Actuator `/actuator/health`로 넓히는 것이 다음 단계다.

5. **`docker compose ps`에 색이 안 보인다** — 프로필 때문이다. `--profile blue --profile green`을 붙이거나 `bash deploy/blue-green.sh status`를 친다. `down`도 같다.

6. **상태 파일은 git 밖에 있다** — `nginx/upstream/active.conf`는 호스트에만 있다. 호스트를 새로 받으면 파일이 없고, 첫 `deploy`가 blue로 만든다.

| 상황 | 명령 | 일어나는 일 |
|---|---|---|
| 새 버전 배포 | `bash deploy/blue-green.sh deploy` (CD가 친다) | 쉬는 색 교체 → 헬스체크 → 전환 → 이전 색 정지 |
| 배포 뒤 문제 발견 | `bash deploy/blue-green.sh rollback` | 멈춰 둔 이전 색 켜기 → 헬스체크 → 전환 |
| 특정 커밋으로 | `IMAGE_TAG=sha-abc1234 bash deploy/blue-green.sh deploy` | 그 태그를 쉬는 색에 |
| 헬스체크 실패 | (자동) | 전환 안 함, 새 색 정지, 종료 코드 1, 서비스는 그대로 |
| 상태 보기 | `bash deploy/blue-green.sh status` | 활성 색, 두 색의 컨테이너(멈춘 것 포함) |

### 이번 노트에서 추가·수정된 파일

**추가**

- `deploy/blue-green.sh` — deploy, rollback, status
- `nginx/upstream/.gitignore`, `nginx/upstream/README.md` — `active.conf`(상태 파일, git 밖)가 놓이는 폴더

**수정**

- `compose.prod.yaml` — `x-frontend`/`x-backend` 앵커, `frontend-blue`/`green`, `backend-blue`/`green` (프로필), nginx가 `nginx/upstream` 폴더 마운트
- `nginx/server.conf` — upstream 블록 대신 `include /etc/nginx/upstream/active.conf`
- `.github/workflows/deploy.yml` — deploy job의 script가 `bash deploy/blue-green.sh deploy`

---

## 마무리

이번 노트로 배포가 끊기지 않고, 실패해도 안전하고, 몇 초에 되돌릴 수 있게 되었다. 사용자는 전환을 모르고, 로그인도 그대로다. 09에서 시작한 흐름이 여기서 한 바퀴 돈다. 데이터가 스프링에서 흐르고(09), 전부 컨테이너로 올라가고(10), HTTPS로 도메인에 열리고(11), push 한 번으로 배포되고(12), 그 배포가 무중단이다(13). 이제 업무 기능을 만들 차례다. 어떤 기능을 넣어도 push하면 몇 분 뒤 끊김 없이 올라간다.
