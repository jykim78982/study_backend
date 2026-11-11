---
tags: [Docker, 배포, CI/CD, GitHubActions, 참고자료]
---

> 🔗 관련 노트: [[059_GitHub Actions CI_CD — 테스트, GHCR 이미지 푸시, SSH 배포까지 push 한 번으로]] · [[044_서버 배포와 HTTPS — nginx 리버스 프록시, mkcert, certbot, 팀별 서브도메인 참고자료]] · [[043_도커 컴포즈로 프론트·백엔드·PostgreSQL·Redis 한 번에 띄우기와 리프레시 토큰 Redis 저장 참고자료]] · [[060_블루그린 배포 — 새 버전을 옆에 띄우고 nginx upstream 전환, 무중단과 롤백]]

# CI/CD와 테스트 서버 배포

`develop`에 머지하면 GitHub Actions가 검사, 이미지 빌드, 테스트 서버 배포까지 자동으로 진행합니다. 이 문서는 그 흐름과, 처음 한 번 해 둬야 하는 GitHub·서버 설정을 정리한 것입니다.

- 워크플로: [.github/workflows/deploy.yml](../.github/workflows/deploy.yml), [.github/workflows/notify.yml](../.github/workflows/notify.yml)
- 서버용 compose: [compose.prod.yaml](../compose.prod.yaml)
- 서버용 팀 nginx 설정: [nginx/server.conf](../nginx/server.conf)
- 환경 변수 목록: [.env.example](../.env.example)

## 1. 전체 흐름

```
feature 브랜치 ─PR─▶ develop/main   [CI] 검사만 함
                       │
                  develop에 머지
                       ▼
              [CI] 검사 다시 실행
                       ▼
              [CD] 이미지 빌드 → GHCR에 푸시
                       ▼
              [CD] SSH로 테스트 서버 접속 → 새 이미지로 다시 띄움 → 응답 확인
```

| 언제 | 실행되는 것 | 결과 |
| --- | --- | --- |
| `develop`이나 `main`으로 PR을 열거나 커밋을 추가할 때 | 프론트 lint·build, 백엔드 test, Docker 이미지 빌드 확인 | 검사만 하고 이미지는 올리지 않음 |
| `develop`에 머지될 때 | 같은 검사 → 이미지 푸시 → 서버 배포 | 테스트 서버가 최신 `develop`으로 바뀜 |
| `main`에 머지될 때 | 없음 | 운영 단계에서 배포를 추가할 예정 |

같은 PR에 커밋이 새로 올라오면 이전 검사는 취소됩니다. `develop` 머지는 취소되지 않고 순서대로 실행됩니다.

push, PR 생성·머지 알림은 `notify.yml`이 Campfire로 보냅니다.

## 2. CI: PR 검사

세 가지 검사가 동시에 실행됩니다. 하나라도 실패하면 PR에 실패로 표시됩니다.

| 검사 | 하는 일 |
| --- | --- |
| Frontend lint·build | Node 24에서 `npm ci` → `npm run lint` → `npm run build` |
| Backend test | 테스트용 PostgreSQL 17을 함께 띄우고 `./gradlew test`. `@SpringBootTest`가 DB에 연결하기 때문입니다 |
| Docker build | backend와 frontend 운영 이미지가 빌드되는지 확인. 이미지를 올리지는 않습니다 |

## 3. CD: develop 머지 후 배포

### 3-1. 이미지 빌드·푸시 (`build-push`)

프론트와 백엔드 검사를 통과해야 실행됩니다.

- 이미지 주소: `ghcr.io/likelion-backendschool-9th/test-moa-backend`, `test-moa-frontend`
- 태그
  - `sha-<커밋 7자리>`: 배포와 롤백에 씁니다
  - `latest`: 가장 최근 이미지입니다
- `NEXT_PUBLIC_SITE_URL`은 프론트 이미지를 **빌드할 때** 코드에 들어갑니다. 그래서 서버 `.env`가 아니라 GitHub Variables에 넣어야 하고, 이 값이 비어 있으면 이 단계가 실패합니다.

### 3-2. 서버 배포 (`deploy`)

이미지 두 개가 모두 올라간 뒤 서버에 SSH로 들어가 아래를 순서대로 실행합니다. 하나라도 실패하면 거기서 멈춥니다.

1. `cd ~/test-moa && git pull --ff-only`: `compose.prod.yaml`과 nginx 설정을 최신으로 맞춥니다.
2. `docker compose -f compose.prod.yaml pull`: 방금 올린 `sha-<커밋>` 이미지를 받습니다.
3. `docker compose -f compose.prod.yaml up -d --no-build`: 새 이미지로 컨테이너를 다시 띄웁니다.
4. 우리 저장소에서 만든 오래된 이미지만 지웁니다. 같은 서버를 쓰는 다른 팀 이미지는 건드리지 않습니다.
5. `127.0.0.1:3005`가 응답하는지 최대 30초 기다립니다. 응답이 없으면 배포 실패로 표시됩니다.

배포 이력은 GitHub의 Actions 탭이나 Environments → `develop`에서 볼 수 있습니다.

## 4. 서버 구조

한 서버를 여러 팀이 같이 씁니다. 우리 팀은 서버 계정 `team5`, 도메인 `test-moa.newlecture.com`, 포트 `3005`를 배정받았습니다.

```
브라우저
  │ https://test-moa.newlecture.com
  ▼
호스트 nginx (서버에 직접 설치, 443, certbot 인증서)    ← 서버 공용. sudo로 설정
  │ http://127.0.0.1:3005
  ▼
팀 nginx 컨테이너 (nginx/server.conf, 80)               ← 우리 저장소. 배포 때 자동 반영
  │
  ▼
frontend (Next.js, BFF) ──▶ backend (Spring) ──▶ db (PostgreSQL)
```

- **HTTPS는 호스트 nginx가 처리합니다.** 팀 nginx는 80번만 듣고, 호스트 nginx가 넘긴 `X-Forwarded-*` 헤더를 그대로 frontend에 전달합니다.
- **3005번은 `127.0.0.1`에만 열려 있습니다.** 밖에서 `서버IP:3005`로 들어올 수 없고, 도메인(HTTPS)을 거쳐야만 들어옵니다.
- **백엔드와 DB는 밖에 열려 있지 않습니다.** 브라우저는 Next 서버하고만 통신합니다(BFF).
- `COMPOSE_PROJECT_NAME=team5`로 네트워크와 볼륨 이름을 다른 팀과 나눕니다.
- 배포로 frontend 컨테이너의 IP가 바뀌어도 팀 nginx가 Docker 내부 DNS로 다시 찾습니다. 그래서 배포 후에 502가 나지 않습니다.

## 5. 처음 한 번 하는 설정

### 5-1. 배포용 SSH 키 만들기 (내 컴퓨터에서)

서버가 아니라 **내 컴퓨터**에서 만듭니다. 개인 키는 내 컴퓨터와 GitHub Secret에만 두고, 서버에는 공개 키만 둡니다.

```sh
# 1. 키 만들기
ssh-keygen -t ed25519 -f ~/.ssh/test-moa-deploy -N "" -C "github-actions-test-moa"

# 2. 공개 키를 서버 team5 계정에 등록 (<포트>는 SSH 포트. 22면 -p 생략)
ssh-copy-id -i ~/.ssh/test-moa-deploy.pub -p <포트> team5@<서버주소>

# 3. 새 키로 접속되고 docker를 쓸 수 있는지 확인
ssh -i ~/.ssh/test-moa-deploy -p <포트> team5@<서버주소> 'docker ps'

# 4. 개인 키를 복사해서 GitHub Secret DEPLOY_SSH_KEY에 붙여넣기 (macOS)
pbcopy < ~/.ssh/test-moa-deploy
```

3번에서 `permission denied while trying to connect to the docker API`가 나오면 계정이 docker 그룹에 없는 것입니다. sudo 권한자가 `sudo usermod -aG docker team5`를 실행한 뒤 다시 접속합니다.

### 5-2. GitHub 저장소 설정

Settings → Secrets and variables → Actions에 넣습니다. GitHub 화면에서는 Name 칸에 이름, Value 칸에 값만 넣습니다(`이름=값` 형식으로 넣지 않습니다).

| 종류 | Name | Value |
| --- | --- | --- |
| Variable | `NEXT_PUBLIC_SITE_URL` | `https://test-moa.newlecture.com` (끝에 `/` 없이) |
| Secret | `DEPLOY_HOST` | 서버 주소 |
| Secret | `DEPLOY_USER` | `team5` |
| Secret | `DEPLOY_SSH_KEY` | 5-1에서 만든 개인 키 전체 |
| Secret | `DEPLOY_PORT` | SSH 포트가 22가 아닐 때만 |
| Secret | `CAMPFIRE_WEBHOOK_URL` | 알림용 웹훅 주소 |

`develop` Environment는 첫 배포 때 자동으로 생깁니다.

### 5-3. 호스트 nginx에 우리 도메인 연결 (sudo 필요)

`test-moa.newlecture.com`으로 들어온 요청을 `127.0.0.1:3005`로 넘기는 설정입니다. 다른 팀과 같은 방식으로, 팀 이름의 파일을 따로 만듭니다.

강의 자료(`ncafe-lesson-12`)의 `deploy/host/setup-host.sh`를 서버 `/tmp/`에 복사해 두고, 설정을 만드는 기능(`--render-nginx`)만 씁니다.

```sh
# 1. 다른 팀 파일 이름 규칙 확인 (예: team1이면 우리는 team5)
ls -l /etc/nginx/sites-enabled/

# 2. 설정 생성 → 맨 아래 444 블록 제거 → 우리 파일로 저장
DOMAIN=newlecture.com TEAMS=test-moa BASE_PORT=3004 bash /tmp/setup-host.sh --render-nginx \
  | sed '/^# 팀 도메인이 아닌 Host/,$d' \
  | sudo tee /etc/nginx/sites-available/<이름> >/dev/null

# 3. 링크 걸고 문법 검사
sudo ln -sf /etc/nginx/sites-available/<이름> /etc/nginx/sites-enabled/<이름>
sudo nginx -t

# 4. 적용하고 확인. 502가 나오면 성공 (우리 컨테이너가 아직 안 떠 있어서 502)
sudo systemctl reload nginx
curl -s -o /dev/null -w '%{http_code}\n' -H "Host: test-moa.newlecture.com" http://127.0.0.1/
```

- `nginx -t`가 실패하면 `sudo rm /etc/nginx/sites-enabled/<이름>`으로 링크를 지웁니다. reload 전이라 다른 팀에는 영향이 없습니다.
- **`setup-host.sh`를 옵션 없이 실행하지 않습니다.** 이 스크립트는 빈 서버를 처음 구성하는 용도라, 이 서버에서 실행하면 필요 없는 계정을 만들고 `default` 사이트를 지우고, 다른 서비스로 가는 요청까지 끊는 444 블록을 넣습니다.
- 생성된 파일에는 업로드 크기 제한이 없어서, 1MB가 넘는 업로드는 호스트 nginx에서 413으로 막힙니다. 이미지 업로드를 쓸 때는 `server {` 아래에 `client_max_body_size 10m;`를 추가합니다.
- 나중에 다른 팀도 같은 스크립트로 파일을 만들면 `$team_upstream` 변수 이름이 겹칠 수 있습니다. 미리 `test_moa_upstream`처럼 바꿔 두면 안전합니다.

### 5-4. HTTPS 인증서 (sudo 필요)

5-3이 끝난 뒤에 합니다. certbot은 80번 `server` 블록을 찾아 HTTPS 설정을 덧붙이는 방식이라 라우팅이 먼저 있어야 합니다.

```sh
sudo certbot --nginx -d test-moa.newlecture.com      # 리다이렉트 질문에는 리다이렉트 선택
curl -s -o /dev/null -w '%{http_code}\n' https://test-moa.newlecture.com/   # 502면 성공
```

인증서는 서버의 `certbot.timer`가 자동으로 갱신합니다.

### 5-5. 서버에 저장소와 .env 준비 (team5 계정)

```sh
git clone -b develop https://github.com/likelion-backendschool-9th/test-moa.git ~/test-moa
cd ~/test-moa
cp .env.example .env
nano .env
```

| 키 | 값 | 설명 |
| --- | --- | --- |
| `POSTGRES_DB`, `POSTGRES_USER` | 예: `testmoa` | |
| `POSTGRES_PASSWORD` | `openssl rand -hex 12` 결과 | DB를 처음 만들 때만 적용됩니다. 나중에 바꾸면 백엔드가 접속하지 못하니 처음부터 최종 값으로 정합니다 |
| `GITHUB_OWNER` | `likelion-backendschool-9th` | 소문자. 비어 있으면 이미지 주소가 깨져 pull이 실패합니다 |
| `IMAGE_TAG` | `latest` | 서버에서 compose 명령을 직접 칠 때 씁니다. 자동 배포 때는 워크플로가 `sha-<커밋>`으로 덮어씁니다 |
| `COMPOSE_PROJECT_NAME` | `team5` | |
| `TEAM_PORT` | `3005` | |

`NEXT_PUBLIC_SITE_URL`은 서버 `.env`에 넣어도 효과가 없습니다(3-1 참고). `.env`는 커밋하지 않습니다.

### 5-6. 첫 배포 후 확인

1. Actions 탭에서 `Build·push image`와 `Deploy to test server`가 성공했는지 봅니다.
2. 조직 페이지 → Packages에서 `test-moa-backend`, `test-moa-frontend`를 **Public**으로 바꿉니다. GHCR 패키지는 처음에 private으로 만들어지고, 배포 스크립트는 로그인 없이 pull합니다. private으로 두려면 서버에서 `read:packages` 권한이 있는 토큰으로 `docker login ghcr.io`를 한 번 해 둬야 합니다.
3. 브라우저로 `https://test-moa.newlecture.com`에 접속합니다.

첫 배포에서 자주 막히는 곳은 SSH 키, 서버 계정의 docker 권한, 패키지 권한입니다. 실패하면 Actions 로그에서 실패한 단계를 먼저 봅니다.

## 6. 운영

### 상태와 로그 보기 (서버, `~/test-moa`)

```sh
docker compose -f compose.prod.yaml ps
docker compose -f compose.prod.yaml logs -f backend
```

### 롤백

이전 커밋의 이미지 태그를 골라 다시 띄웁니다. 태그는 Actions 로그나 Packages 화면에서 확인합니다.

```sh
IMAGE_TAG=sha-abc1234 docker compose -f compose.prod.yaml up -d
```

다음에 `develop`에 머지하면 다시 최신 이미지로 배포됩니다.

### 서버 재부팅

컨테이너가 `restart: unless-stopped`라서 Docker가 자동으로 다시 띄웁니다. 재부팅 직후 수십 초 동안은 502가 날 수 있지만, 모든 컨테이너가 뜨면 정상으로 돌아옵니다. `docker compose down`으로 컨테이너를 지운 경우에는 자동으로 뜨지 않으니 `up -d`를 다시 실행합니다.

## 7. 서버 점검 명령

호스트 설정이 맞는지 한 번에 보려면 강의 자료의 점검 스크립트를 씁니다. 아무것도 바꾸지 않습니다.

```sh
sudo DOMAIN=newlecture.com TEAMS=test-moa BASE_PORT=3004 bash /tmp/check-host.sh
```

이 서버는 강의 자료와 구성이 달라서 `2. 팀 계정`의 `test-moa 계정`과 `3. 호스트 nginx`의 `팀 라우팅 설정(teams)`은 늘 `[없음]`으로 나옵니다. 무시하면 됩니다. **`5. 끝에서 끝`이 OK(200이나 502)면 호스트 쪽 준비는 끝난 것입니다.**

| `5. 끝에서 끝` 결과 | 의미 |
| --- | --- |
| 200 | 전부 정상 |
| 502 | 호스트는 정상. 우리 컨테이너가 안 떠 있음 |
| 인증서가 유효하지 않다 | 5-4 인증서를 아직 발급하지 않음 |
| 443에 연결되지 않는다 | 호스트 nginx나 certbot 설정 확인 |
