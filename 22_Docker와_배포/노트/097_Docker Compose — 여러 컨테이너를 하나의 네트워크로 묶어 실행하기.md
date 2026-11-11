---
tags: [Docker, DockerCompose, 컨테이너, 네트워크, 볼륨, 환경변수, depends_on, 스프링부트, PostgreSQL]
---

> 🔗 관련 노트: [[096_Dockerfile로 스프링 부트 이미지 만들기 — 멀티 스테이지 빌드와 Compose 맛보기]] · [[077_도커란 무엇인가 — 가상 머신과의 차이, 이미지·컨테이너·엔진]]

# Docker Compose — 여러 컨테이너를 하나의 네트워크로 묶어 실행하기

## 1. 컨테이너가 여러 개가 되면 생기는 일

지난번에는 어려움을 줄이려고 백엔드 하나와 데이터베이스 하나만 도커로 따로 띄워 연결했다. 하지만 실제 서비스에는 프론트엔드도 있고, Nginx도 있고, 다른 서버가 더 있을 수도 있다. 컨테이너가 여러 개가 되면 골치 아픈 일이 생긴다.

- **하나씩 실행해야 한다.** 컨테이너마다 `docker run`을 따로 하고, 따로 관리해야 한다.
- **순서가 중요하다.** DB를 먼저 띄우고 정상적으로 열린 걸 확인한 뒤 백엔드를 띄우고, 백엔드가 뜬 걸 확인한 뒤 프론트엔드를 띄워야 한다. 이걸 전부 손으로 해야 한다.
- **포트가 부딪힌다.** 컨테이너끼리는 포트로 대화하는데, 그 포트가 호스트의 다른 프로그램 포트와 겹치면 문제가 된다.

컨테이너들의 순서를 알아서 잡고, 앞의 것이 뜬 다음에 다음 것을 띄우고, 명령 한 번에 전부 올리고 내려 주는 도구가 **Docker Compose**다.

```
docker-compose.yaml (컴포즈 설정)
        │  "순서대로 실행 및 종료!"
        ▼
실행:  DB 기동  →  백엔드 기동  →  프론트엔드 기동
종료:  프론트엔드 종료  →  백엔드 종료  →  DB 종료   (실행의 역순)
```

> 원문 바로잡기 — 강의 그림의 종료 단계에는 "1. 데이터베이스 종료 → 2. 백엔드 종료 → 3. 프론트엔드 종료"라고 번호가 붙어 있지만, 실제 종료 순서는 그림 아래 설명처럼 **실행의 역순**(프론트엔드 → 백엔드 → DB)이다. DB를 먼저 내리면 아직 살아 있는 백엔드가 DB를 잃기 때문이다. `docker compose down`은 `depends_on` 관계를 거꾸로 따라 내린다.

## 2. Compose는 격리된 가상 네트워크를 만든다

Compose의 더 중요한 기능은 **네트워크**다. Compose 파일 하나로 컨테이너들을 띄우는 순간, 그 컨테이너들만의 **격리된 가상 네트워크**가 만들어진다. 공유기를 하나 따로 끼운 것과 비슷하다.

```
┌───────────── Compose 가상 네트워크 ─────────────┐
│                                                 │
│  [프론트엔드] ──▶ [백엔드] ──▶ [데이터베이스]     │
│                                                 │
└───────┬─────────────────────────────────────────┘
        │ 밖으로 내는 문(포트)은 필요한 것만
     [호스트 / 외부 브라우저]
```

### 데이터베이스는 밖으로 열 이유가 없다

- DB를 쓰는 것은 같은 네트워크 안의 **백엔드**뿐이다.
- 그럼 프론트엔드는 DB를 안 쓰나? 여기서 프론트엔드는 프론트엔드 앱 서버가 아니라 **브라우저**로 봐야 한다. 브라우저가 DB에 직접 붙는 것은 불가능하다. 그래서 백엔드가 있는 것이다. **백엔드는 프론트엔드를 위한 API**이고, 프론트엔드가 원하는 데이터에 접근하는 유일한 길이다.
- 따라서 DB 포트는 네트워크 안에서만 쓰면 되고, 호스트의 다른 포트와 부딪힐까 걱정할 필요가 없다.

신경 쓸 것은 **밖으로 노출하는 컨테이너뿐**이다. 브라우저가 직접 접근하는 프론트엔드, 필요하면 백엔드 정도다. 프론트엔드가 **SSR로만** 동작한다면 백엔드 호출도 서버(네트워크 안)에서 일어나므로 백엔드조차 밖으로 열 이유가 없다.

## 3. 프로젝트 구조와 Compose 파일 위치

```
ncafe/
├─ frontend/
│  └─ Dockerfile
├─ backend/
│  └─ Dockerfile
└─ docker-compose.yaml      ← 프론트엔드·백엔드·DB를 묶는 파일은 루트에
```

- 직접 만든 코드(프론트엔드, 백엔드)는 각자 **Dockerfile**로 이미지를 만든다.
- 데이터베이스처럼 이미 만들어진 이미지를 쓰는 것은 Dockerfile이 필요 없다.
- 이들을 묶는 **docker-compose.yaml**은 가장 바깥 루트에 둔다.

지금 실습 프로젝트는 백엔드 하나뿐이고 Dockerfile이 프로젝트 루트에 있으므로, 같은 루트에 `docker-compose.yaml`을 만든다(철자가 틀리면 인식하지 못한다).

### Dockerfile과 Compose 파일의 차이

| 파일 | 다루는 것 | 적는 내용 |
|---|---|---|
| **Dockerfile** | 가상 **컴퓨터** 하나(이미지) | 어떤 리눅스를 쓰고, 무엇을 배치하고, 무엇을 실행할지 — 이미지를 만드는 요리법 |
| **docker-compose.yaml** | 가상 **네트워크** | 어떤 이미지(컨테이너)들을 쓰고, 언제 실행·종료하고, 실행할 때 어떤 옵션을 줄지 |

## 4. docker-compose.yaml 작성하기

```yaml
services:
  # 1. PostgreSQL 데이터베이스
  postgres-db:
    image: postgres:16
    container_name: ncafe-db
    environment:
      POSTGRES_DB: ncafe-db
      POSTGRES_USER: ncafe
      POSTGRES_PASSWORD: 123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # 2. 스프링 부트 백엔드
  backend-app:
    build: .
    container_name: ncafe-backend
    ports:
      - "8080:8080"
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres-db:5432/ncafe-db
      SPRING_DATASOURCE_USERNAME: ncafe
      SPRING_DATASOURCE_PASSWORD: 123
    depends_on:
      - postgres-db

# 3. 데이터베이스 데이터를 보존할 공간 선언
volumes:
  postgres_data:
```

### services — 네트워크 안의 컴퓨터 목록

`services:` 아래에 적는 이름 하나하나가 이 네트워크 안의 **컴퓨터**다. YAML이라 들여쓰기(공백 2칸)로 계층을 나눈다.

**서비스 이름은 컴퓨터 이름이다.** 네트워크에서 컴퓨터를 찾는 방법은 두 가지다.

| 식별 방법 | 예 |
|---|---|
| IP 주소 | `192.168.0.10` |
| 컴퓨터 이름(호스트 이름) | Windows의 "이 PC 이름 바꾸기"에 나오는 이름, 리눅스의 `/etc/hostname` |

Compose 네트워크 안에서는 IP를 정해 두지 않으므로 **이름으로 서로를 찾는다.** 백엔드가 DB에 접속할 때 주소를 `localhost`가 아니라 `postgres-db`로 쓰는 이유다. 백엔드 컨테이너 안에서 `localhost`는 백엔드 자신이다.

### image와 build — 있는 것을 쓸지, 만들지

| 서비스 | 설정 | 의미 |
|---|---|---|
| `postgres-db` | `image: postgres:16` | Docker Hub의 공식 `postgres` 이미지를 그대로 쓴다. 태그 `16`으로 버전을 고정한다 |
| `backend-app` | `build: .` | 현재 디렉터리의 Dockerfile로 **직접 빌드**해서 이미지를 만든다(`docker build`) |

### container_name — 도커가 관리할 때 쓰는 이름

`docker ps`에 보이고, `stop`·`start`할 때 쓰는 이름이다. 서비스 이름과 같아도 되지만, 한 서버에 여러 프로젝트가 올라갈 때 알아보기 쉽게 `ncafe-db`, `ncafe-backend`처럼 **프로젝트 이름을 붙여** 짓는다.

> **추가 설명 — 서비스 이름과 컨테이너 이름**: 네트워크 안에서 주소로 쓰는 것은 기본적으로 **서비스 이름**(`postgres-db`)이다. `container_name`(`ncafe-db`)은 `docker ps` 목록용 이름이다(이 이름으로도 접속은 된다). 또 `container_name`은 서버 전체에서 하나만 존재할 수 있어서, 같은 서버에 같은 Compose 파일을 두 팀이 올리면 이름이 부딪혀 두 번째가 뜨지 않는다. 공용 서버라면 팀 이름까지 붙이거나 `container_name`을 빼서 Compose가 자동으로 짓게 한다.

### environment — 이미지가 정해 둔 설정 변수

DB를 실행하려면 DB 이름, 계정, 비밀번호 같은 설정이 필요하다. 이 변수 이름은 **내 마음대로 정하는 것이 아니라 이미지가 정해 둔 것**이다. Docker Hub의 `postgres` 공식 이미지 페이지에 있는 환경 변수 목록을 보고 필요한 것만 쓴다.

| 변수 | 뜻 |
|---|---|
| `POSTGRES_DB` | 처음 실행할 때 만들 데이터베이스 이름 |
| `POSTGRES_USER` | 만들 사용자 계정 |
| `POSTGRES_PASSWORD` | 그 계정의 비밀번호(필수) |

> **추가 설명 — 이 값들은 처음 한 번만 적용된다**: `POSTGRES_*` 변수는 데이터 디렉터리가 **비어 있을 때**, 즉 DB를 처음 초기화할 때만 쓰인다. 볼륨에 이미 데이터가 있으면 비밀번호를 바꿔도 반영되지 않는다. 강의 중 "데이터베이스가 이미 존재한다"는 메시지가 나와 기존 것을 지우고 다시 한 것도 같은 맥락이다. 설정을 바꿔 처음부터 다시 만들려면 `docker compose down -v`로 볼륨까지 지운다.

## 5. ports — 오른쪽이 컨테이너, 왼쪽이 밖

```yaml
ports:
  - "5432:5432"     # "호스트 포트 : 컨테이너 포트"
```

```
[호스트(내 컴퓨터)] 5432 ──▶ [Compose 네트워크] ──▶ [postgres-db 컨테이너] 5432
   ↑ 왼쪽: 밖에서 들어오는 문                          ↑ 오른쪽: 컨테이너 안의 PostgreSQL
   다른 프로그램과 부딪힐 수 있다                      컨테이너마다 따로라 부딪히지 않는다
```

- **오른쪽(컨테이너 포트)**은 그 컨테이너 안의 프로그램이 쓰는 포트다. 컨테이너마다 따로라서 아무 번호여도 서로 충돌하지 않는다. PostgreSQL은 5432, 스프링 부트는 8080을 그대로 둔다.
- **왼쪽(호스트 포트)**은 네트워크 밖, 즉 호스트 컴퓨터에 내는 문이다. 여기는 다른 프로그램과 **부딪힐 수 있으니** 신경 써야 한다.

백엔드의 `"8080:8080"`도 같은 원리다. 한 서버에 여러 팀이 각자 Compose를 올리면 모두 호스트의 8080을 달라고 해서 부딪힌다. 그래서 공용 서버에서는 팀별로 바깥 번호를 정해야 한다(예: 1조 `"8081:8080"`, 2조 `"8082:8080"`).

> 원문 바로잡기 — 강의 중 "지금 설정하는 포트는 안쪽이라 아무렇게나 해도 상관없다"고 설명한 부분이 있었는데, `ports:` 항목 자체는 **컨테이너 포트를 호스트에 공개하는 설정**이다. 그래서 왼쪽 번호는 충돌을 신경 써야 한다. 반대로 같은 Compose 네트워크 안의 컨테이너끼리는 `ports:`가 **없어도** 서비스 이름과 컨테이너 포트(`postgres-db:5432`)로 바로 통신한다. 즉 DB를 밖에서 쓸 일이 없다면 `ports:`를 아예 빼는 것이 2절에서 말한 "DB는 밖으로 열 이유가 없다"를 실제로 지키는 방법이다. 이번 실습에서는 내 컴퓨터의 DB 도구(DBeaver 등)로 접속해 보려고 `5432:5432`를 열어 두었다.

## 6. volumes — 데이터를 컨테이너 밖에 둔다

**볼륨**은 컨테이너 밖에 있는 저장 공간이다. DB 데이터를 컨테이너 안에 두면 데이터와 컨테이너의 **생명주기가 같아진다.** 컨테이너를 지우고 다시 만들 때 데이터도 함께 사라진다. 팀원에게 내 데이터를 넘기려면 컨테이너 자체를 넘겨야 하는 이상한 상황이 된다. 그래서 데이터는 밖에 둔다.

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
#   └ 왼쪽: 바깥(호스트 쪽)  └ 오른쪽: 컨테이너 안의 경로(PostgreSQL이 데이터를 쓰는 곳)
```

`ports`와 마찬가지로 **오른쪽이 컨테이너, 왼쪽이 바깥**이다. PostgreSQL이 `/var/lib/postgresql/data`에 쓰는 내용이 실제로는 바깥 공간에 쓰인다. 바깥 공간을 컨테이너 안의 경로에 연결하는 것을 **마운트**라고 한다.

### 왼쪽에 무엇을 쓰느냐에 따라 두 가지

| 방식 | 예 | 뜻 |
|---|---|---|
| **named volume**(이름 붙인 볼륨) | `postgres_data:/var/lib/postgresql/data` | 도커가 관리하는 저장 공간에 이름을 붙여 쓴다. 이 이름은 파일 맨 아래 **최상위 `volumes:`에 선언**해야 한다(변수 선언처럼) |
| **bind mount**(경로 지정) | `/home/team1/postgres-data:/var/lib/postgresql/data` | 호스트의 **특정 폴더**를 직접 연결한다. 선언이 필요 없다 |

이름 붙인 볼륨을 쓰면서 최상위 `volumes:`에 선언하지 않으면 Compose가 "정의되지 않은 볼륨"이라며 실행하지 않는다. 그래서 파일 맨 아래(들여쓰기 없이 루트 위치)에 `volumes: postgres_data:`를 적는다.

### 공용 서버에서는 팀별로 나눈다

운영 서버 하나에 4개 팀이 같은 이름의 데이터를 만들면 좋지 않다. 이럴 때는 경로를 직접 지정해 팀 폴더(`/home/team1/...`)를 쓰거나, 볼륨 이름을 팀마다 다르게 짓는다.

> **추가 설명 — 이름 붙인 볼륨은 프로젝트 이름이 앞에 붙는다**: Compose는 볼륨을 만들 때 **프로젝트 이름**(기본은 Compose 파일이 있는 폴더 이름)을 앞에 붙인다. 폴더가 `ncafe`라면 실제 볼륨 이름은 `ncafe_postgres_data`가 된다(`docker volume ls`로 확인). 그래서 팀마다 폴더 이름이 다르면 볼륨은 자동으로 나뉜다. 부딪히는 것은 같은 폴더 이름으로 올렸을 때이고, 이때는 `docker compose -p team1 up -d`처럼 프로젝트 이름을 직접 정해 주면 된다. 앞에서 본 `container_name`은 이런 자동 구분이 없어서 더 잘 부딪힌다.

## 7. 백엔드에 DB 접속 정보 넘기기 — 환경 변수

백엔드가 DB에 접속하려면 접속 정보(URL, 계정, 비밀번호)가 필요하다. 지금까지는 `application.yml`에 적었지만, Compose의 `environment`로 넘길 수 있다.

```yaml
environment:
  SPRING_DATASOURCE_URL: jdbc:postgresql://postgres-db:5432/ncafe-db
  SPRING_DATASOURCE_USERNAME: ncafe
  SPRING_DATASOURCE_PASSWORD: 123
```

```
jdbc:postgresql://postgres-db:5432/ncafe-db
                  └ 서버 = DB 서비스 이름
                              └ 포트 = DB 컨테이너 포트(오른쪽)
                                   └ 데이터베이스 = POSTGRES_DB에 적은 이름
```

계정과 비밀번호도 DB 서비스의 `POSTGRES_USER`, `POSTGRES_PASSWORD`에 적은 값을 그대로 쓴다. 이렇게 하면 백엔드는 **같은 Compose 안의 DB를 내장한 것처럼** 쓰게 되고, H2 같은 임시 DB를 쓸 필요가 없어진다.

### 스프링 부트는 운영체제 환경 변수를 자동으로 읽는다

Compose의 `environment`는 컨테이너 안 리눅스의 **환경 변수**(`PATH` 같은 것)를 설정한다. 스프링 부트는 운영체제 환경 변수를 자동으로 설정값으로 받아들인다. 그래서 `application.yml`에 DB 설정을 따로 쓰지 않아도, 환경 변수를 읽어 DB에 연결하는 `DataSource` 객체를 만든다.

| 환경 변수 | 스프링 설정 키 |
|---|---|
| `SPRING_DATASOURCE_URL` | `spring.datasource.url` |
| `SPRING_DATASOURCE_USERNAME` | `spring.datasource.username` |
| `SPRING_DATASOURCE_PASSWORD` | `spring.datasource.password` |

스프링이 알아듣는 형식이어야 하므로 **철자가 틀리면 적용되지 않는다.** 점(`.`)을 밑줄(`_`)로, 소문자를 대문자로 바꾼 형태다.

> 원문 바로잡기 — 강의에서는 "`application.yml`의 H2는 테스트용 임시 저장소라 스프링이 무시하고 환경 변수를 쓴다"고 설명했는데, 이유는 H2라서가 아니라 **설정값의 우선순위** 때문이다. 스프링 부트는 같은 설정이 여러 곳에 있으면 **운영체제 환경 변수를 `application.yml`보다 우선**한다. 그래서 `application.yml`에 MySQL을 적어 두었더라도 환경 변수 `SPRING_DATASOURCE_URL`이 있으면 환경 변수가 이긴다. 같은 이미지를 로컬·서버에서 그대로 쓰고, 접속 정보만 실행할 때 바꿔 끼울 수 있는 이유다.

### .env 파일로 비밀 정보를 빼기

접속 정보를 Compose 파일에 그대로 적으면 Git에 올라간다. 강의에서는 완성형이 아니라 직접 적었지만, 보통은 `.env` 파일로 뺀다.

```
# .env  (Compose 파일과 같은 폴더, .gitignore에 추가)
DB_NAME=ncafe-db
DB_USER=ncafe
DB_PASSWORD=123
```

```yaml
environment:
  POSTGRES_PASSWORD: ${DB_PASSWORD}
  SPRING_DATASOURCE_PASSWORD: ${DB_PASSWORD}
```

> **추가 설명 — `.env`는 Compose가 자동으로 읽는다**: Compose 파일과 같은 폴더의 `.env`에 적은 값은 `${변수}` 자리에 자동으로 채워진다. 파일 안 어디에도 비밀번호가 하드코딩되지 않고, 서버마다 `.env`만 다르게 두면 된다. 저장소에는 값을 비운 `.env.example`을 올려 어떤 변수가 필요한지 알려 준다.

## 8. depends_on — DB가 먼저

백엔드는 DB가 있어야 뜰 수 있으므로 DB가 먼저 실행되어야 한다. 이것을 알려 주는 것이 `depends_on`이다.

```yaml
backend-app:
  depends_on:
    - postgres-db      # postgres-db를 먼저 띄운 뒤 backend-app을 띄운다
```

> **추가 설명 — "먼저 띄운다"이지 "준비될 때까지 기다린다"가 아니다**: 기본 `depends_on`은 DB **컨테이너가 시작된 뒤** 백엔드를 띄울 뿐, PostgreSQL이 접속을 받을 준비가 됐는지는 확인하지 않는다. DB가 초기화되는 몇 초 사이에 백엔드가 먼저 접속하면 연결 실패로 죽을 수 있다. 준비될 때까지 기다리게 하려면 DB에 **healthcheck**를 달고 조건을 건다.
>
> ```yaml
> postgres-db:
>   healthcheck:
>     test: ["CMD-SHELL", "pg_isready -U ncafe -d ncafe-db"]
>     interval: 5s
>     retries: 10
>
> backend-app:
>   depends_on:
>     postgres-db:
>       condition: service_healthy   # DB가 "건강"하다고 확인된 뒤에 시작
> ```

## 9. Compose 명령어

Compose 명령은 **docker-compose.yaml이 있는 폴더**에서 실행한다.

| 명령 | 하는 일 |
|---|---|
| `docker compose up -d` | 이미지를 받거나 빌드하고, 컨테이너를 만들어 전부 실행한다. `-d`는 백그라운드 실행 |
| `docker compose down` | 전부 중지하고 컨테이너와 네트워크를 **삭제**한다(볼륨은 남는다. `-v`를 붙이면 볼륨까지) |
| `docker compose stop` / `start` / `restart` | 컨테이너를 지우지 않고 멈추거나 다시 켠다 |
| `docker compose logs -f` | 묶인 컨테이너 전체의 로그(`logs -f backend-app`처럼 하나만도 가능) |
| `docker compose ps` | 이 Compose의 컨테이너 상태 |

- `-d` 없이 `up`하면 모든 로그가 터미널에 쏟아지고, 터미널을 닫으면 함께 멈춘다. 보통 `-d`로 띄우고 로그는 `logs`로 본다.
- `up`은 이미 실행 중이고 바뀐 게 없는 컨테이너는 **건너뛰고**, 새로 만들어야 할 것만 만든다.
- Compose로 띄운 것도 결국 도커 컨테이너라서 `docker ps`로도 똑같이 보인다.
- 기존 도커 명령(`docker start`, `docker logs`)에 `compose`를 붙이면 **묶음 단위**로 동작한다고 기억하면 된다.

> **추가 설명 — 코드를 고친 뒤에는 `--build`**: `build:`로 만드는 서비스는 이미지가 한 번 만들어지면 `up`을 다시 해도 **예전 이미지를 그대로** 쓴다. 백엔드 코드를 고쳤다면 `docker compose up -d --build`로 다시 빌드해야 반영된다.

강의에서는 `up` 후 백엔드가 에러로 뜨지 않았는데, Compose 문제가 아니라 지난 시간에 다루다 만 스프링 시큐리티 설정 때문이었다. DB 컨테이너는 정상적으로 올라왔다. 이런 경우 `docker compose logs backend-app`으로 에러를 확인한다.

## 10. 곁다리 — 프로필로 설정 나누기

설정 파일을 환경별로 나누는 방법도 있다.

```
application.yml           ← 공통. spring.profiles.active: prod 처럼 쓸 프로필을 고른다
application-test.yml      ← 테스트용 (H2 등)
application-prod.yml      ← 운영용
```

`application-{프로필 이름}.yml` 형식으로 만들고 `spring.profiles.active`로 고르면, 그 프로필의 파일이 함께 읽힌다. 프로필 이름은 마음대로 정한다.

강사는 도커를 쓰면서부터 이 방식을 잘 쓰지 않는다고 했다. Compose로 개발할 때는 내 로컬의 DB를 쓰고, GitHub에 올려 서버에서 실행하면 서버의 DB(완전히 별개)를 쓰기 때문에, 개발용 설정을 따로 둘 필요가 거의 없다는 것이다.

> **추가 설명 — 프로필도 여전히 많이 쓴다**: 환경 변수로 접속 정보를 바꾸는 방식과 프로필은 함께 쓰는 경우가 많다. 로그 수준, 외부 API 주소처럼 환경마다 다른 설정이 많으면 프로필로 묶어 두고, Compose에서 `SPRING_PROFILES_ACTIVE: prod`처럼 환경 변수로 프로필을 고른다.

> 원문 바로잡기 — 강의 중 YAML의 대시(`-`)를 "길어서 내려 쓸 때 이어진다는 표시"라고 설명했는데, YAML에서 줄 앞의 `-`는 **목록(배열)의 한 항목**이라는 뜻이다(`ports:` 아래 `- "8080:8080"`처럼). 긴 문자열을 여러 줄로 쓸 때는 `|`(줄바꿈 유지)나 `>`(한 줄로 이어 붙임)를 쓴다. 파일 이름의 `application-test.yml`에 들어간 `-`는 프로필 이름을 붙이는 규칙이다.

## 11. 한 줄 정리

- 컨테이너가 여러 개면 실행 순서와 포트 관리가 골치 아프다. **Docker Compose**는 여러 컨테이너를 한 파일로 묶어 순서대로 올리고(역순으로) 내린다.
- Compose는 **격리된 가상 네트워크**를 만든다. 그 안의 컨테이너는 **서비스 이름**으로 서로를 찾고(`postgres-db:5432`), 밖으로 열 것만 `ports`로 연다. 브라우저가 쓸 수 없는 DB는 밖으로 열 이유가 없다.
- Dockerfile은 **컴퓨터(이미지)**를 만드는 요리법, Compose 파일은 **네트워크**에 어떤 컨테이너를 어떻게 띄울지 정하는 설정이다. 이미 있는 이미지는 `image`, 직접 만드는 것은 `build`.
- `ports`와 `volumes`는 **오른쪽이 컨테이너, 왼쪽이 바깥**이다. 충돌을 신경 쓸 곳은 왼쪽이다.
- DB 데이터는 **볼륨**으로 밖에 둔다. 이름 붙인 볼륨은 최상위 `volumes:`에 선언하고, 공용 서버에서는 팀별로 나눈다.
- `environment`로 넘긴 `SPRING_DATASOURCE_*`는 스프링 부트가 자동으로 읽고, `application.yml`보다 **우선**한다. 비밀 정보는 `.env`로 뺀다.
- `depends_on`으로 DB를 먼저 띄운다(준비까지 기다리려면 healthcheck). 실행은 `docker compose up -d`, 종료는 `down`, 로그는 `logs`.
