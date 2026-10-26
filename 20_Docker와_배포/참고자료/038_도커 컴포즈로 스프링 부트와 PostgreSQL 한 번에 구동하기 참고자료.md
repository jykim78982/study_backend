---
tags: [Docker, DockerCompose, PostgreSQL, 스프링부트, 볼륨, 네트워크, 포트포워딩, expose, 참고자료]
---

> 🔗 관련 노트: [[097_Docker Compose — 여러 컨테이너를 하나의 네트워크로 묶어 실행하기]] · [[037_Java 21 스프링 부트 앱을 도커 이미지로 배포하기 참고자료]] · [[096_Dockerfile로 스프링 부트 이미지 만들기 — 멀티 스테이지 빌드와 Compose 맛보기]]

# 도커 컴포즈로 스프링 부트와 PostgreSQL 한 번에 구동하기

## 1. 왜 도커 컴포즈를 써야 할까?

지난 글에서는 스프링 부트 앱을 도커 이미지로 만들고 컨테이너 하나를 띄우는 방법을 다루었다. 하지만 진짜 서비스를 작동시키려면 백엔드 앱 혼자서만 일할 수 없다. 데이터를 안전하게 저장해 둘 데이터베이스가 반드시 필요하다.

만약 도커 명령어만 사용해서 백엔드와 데이터베이스를 같이 띄운다면 과정이 매우 복잡해진다. 먼저 PostgreSQL 데이터베이스 컨테이너를 실행하고, 데이터베이스가 사용할 네트워크를 직접 만든 뒤, 백엔드 컨테이너를 띄우면서 방금 만든 네트워크에 연결해야 한다. 게다가 순서가 틀어지거나 설정값 하나만 잘못 적어도 백엔드가 데이터베이스를 찾지 못해 터지고 만다.

> **추가 설명 — 컴포즈 없이 하면 이런 명령이 필요하다**:
>
> ```bash
> docker network create my-net
> docker volume create postgres_data
> docker run -d --name postgres-db --network my-net \
>   -e POSTGRES_DB=mydatabase -e POSTGRES_USER=myuser -e POSTGRES_PASSWORD=mypassword \
>   -v postgres_data:/var/lib/postgresql/data postgres:16
> docker build -t my-backend .
> docker run -d --name my-backend --network my-net -p 8080:8080 \
>   -e SPRING_DATASOURCE_URL=jdbc:postgresql://postgres-db:5432/mydatabase \
>   -e SPRING_DATASOURCE_USERNAME=myuser -e SPRING_DATASOURCE_PASSWORD=mypassword my-backend
> ```
>
> 컴포즈는 이 명령들의 내용을 `docker-compose.yml` 하나에 적어 두고 `docker compose up` 한 줄로 실행하게 해 준다.

서로 다른 상자 여러 개를 매번 일일이 손으로 띄우는 불편함을 없애기 위해 등장한 것이 바로 **도커 컴포즈(Docker Compose)**이다.

```
                시작점: 도커 컴포즈 (docker-compose.yml)

[실행]  설정에 따라 차근차근 실행
   ① 데이터베이스(PostgreSQL) ──▶ ② 백엔드(Spring Boot) ──▶ ③ 프론트엔드
        DB 기동                       백엔드 기동                프론트엔드 기동

[종료]  안전하게 거꾸로 종료
   ③ 프론트엔드 종료 ──▶ ② 백엔드 종료 ──▶ ① DB 종료
```

도커 컴포즈는 설정된 순서에 맞게 데이터베이스 → 백엔드 → 프론트엔드를 차근차근 실행하고, 종료할 때는 그 역순(프론트엔드 → 백엔드 → 데이터베이스)으로 안전하게 멈춘다. 의존하는 쪽을 먼저 끄고 다른 서비스가 기대고 있는 DB를 마지막에 꺼야, 백엔드가 살아 있는 동안 DB가 먼저 사라져 연결 오류가 나는 일이 없다.

도커 컴포즈는 여러 컨테이너를 실행할 때 필요한 정보를 하나의 설계도 파일에 모아서 작성해 두는 도구이다. 이 설계도를 바탕으로 외부와 분리된 전용 네트워크를 자동으로 만들고, 그 안에서 모든 컨테이너를 한꺼번에 띄워 서로 손쉽게 통신할 수 있도록 도와주는 일종의 조종사 역할을 한다.

### 1-1. 고립된 네트워크는 덤

도커 컴포즈는 `docker-compose.yml`에 정의된 서비스들을 실행할 때 외부와 격리된 가상 네트워크를 자동으로 생성한다.

```
 docker-compose.yml ──docker compose up──▶  ┌──── 격리된 가상 네트워크 ────┐
                                             │                              │      외부
                                             │        [프론트엔드]          │   (Internet)
                                             │         ↗      ↖             │
                                             │   [백엔드] ⇄ [데이터베이스]  │
                                             └──────────────────────────────┘
```

컴포즈로 포함된 서비스들은 컴포즈 밖에 있는 호스트 컴퓨터의 프로세스와 충돌하지 않도록 전용 네트워크를 갖는다. 이에 따른 주요 장점은 다음과 같다.

- **이름 기반 통신**: 변하는 IP 주소 대신 서비스 이름(예: `postgres-db`)으로 쉽게 통신할 수 있다.
- **보안성 향상**: 외부 노출이 불필요한 내부 서비스는 포트를 열지 않고 가상 네트워크 안에 보호할 수 있다.
- **충돌 방지**: 호스트나 다른 프로젝트의 네트워크와 분리되어 포트나 이름 충돌이 발생하지 않는다.

> 원문 바로잡기 — "포트 충돌이 발생하지 않는다"는 **컨테이너 안쪽 포트**에 한정된 말이다. 프로젝트 A와 B의 DB가 각자 네트워크 안에서 5432를 써도 문제없다. 하지만 `ports: - "5432:5432"`처럼 **호스트로 공개한 포트**는 호스트 하나에 하나뿐이라, 다른 프로젝트나 호스트에 설치된 PostgreSQL이 이미 5432를 쓰고 있으면 `port is already allocated` 오류가 난다. 이때는 왼쪽(호스트) 번호를 바꾸거나, 외부에서 접속할 필요가 없으면 `ports`를 빼면 된다.

> **추가 설명 — 네트워크 이름**: 컴포즈가 만드는 기본 네트워크 이름은 `프로젝트명_default`다(예: `ncafe_default`). `docker network ls`로 확인할 수 있고, 같은 네트워크에 붙은 컨테이너끼리만 서비스 이름으로 서로를 찾는다.

## 2. docker-compose.yml 파일 구성하기

여러 도커 컨테이너들을 한꺼번에 조종하기 위한 컴포즈 레시피는 별도로 준비해야 한다. 프로젝트의 맨 위쪽 폴더(최상위 경로)에 `docker-compose.yml`이라는 이름으로 파일을 만든다.

이 파일 안에 데이터베이스(PostgreSQL) 컨테이너와 백엔드(Spring Boot) 컨테이너를 구동할 규칙을 적어준다.

```yaml
version: '3.8'

services:
  # 1. PostgreSQL 데이터베이스 상자 설정
  postgres-db:
    image: postgres:16
    container_name: my-postgres
    environment:
      POSTGRES_DB: mydatabase
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: mypassword
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # 2. 스프링 부트 백엔드 앱 상자 설정
  backend-app:
    build: .
    container_name: my-backend
    ports:
      - "8080:8080"
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres-db:5432/mydatabase
      SPRING_DATASOURCE_USERNAME: myuser
      SPRING_DATASOURCE_PASSWORD: mypassword
    depends_on:
      - postgres-db

# 3. 데이터베이스 데이터를 보존하기 위한 공간 선언
volumes:
  postgres_data:
```

> **추가 설명 — `version`은 이제 쓰지 않는다**: 현재 Docker Compose(V2, `docker compose` 명령)는 `version` 항목을 무시하고, 적어 두면 `the attribute 'version' is obsolete`라는 경고를 띄운다. 새로 작성할 때는 첫 줄의 `version: '3.8'`을 빼고 `services:`부터 시작하면 된다. 파일 이름도 `docker-compose.yml`, `docker-compose.yaml`, `compose.yaml` 모두 인식한다.

`services` 섹션에 작성하는 항목은 도커 컴포즈가 관리할 실행 단위인 각각의 컨테이너 정의이다. 각 서비스는 별도의 Dockerfile을 통해 이미지를 직접 빌드하여 컨테이너로 띄우거나, 도커 허브(Docker Hub)에 이미 등록되어 있는 공식 이미지를 불러와 실행하도록 설정한다.

파일 최하단의 `volumes: postgres_data:`에서 `postgres_data`라는 이름은 사용자가 임의로 정하는 **이름 있는 볼륨(Named Volume)**의 식별자이다. 원하는 다른 이름(예: `my_db_volume`, `app_db_data` 등)으로 자유롭게 변경할 수 있으며, 변경 시에는 서비스 내부의 `volumes` 매핑 항목(`- 식별자:컨테이너경로`)의 이름도 함께 동일하게 맞춰주면 된다.

이 설정을 선언하면 도커 엔진은 호스트 컴퓨터 내부의 전용 데이터 관리 경로(리눅스 기준 `/var/lib/docker/volumes/프로젝트명_postgres_data/_data`)에 실제 데이터 저장 공간을 자동으로 할당하고 관리한다.

> **추가 설명 — 윈도우(Docker Desktop)에서는 경로가 안 보인다**: Docker Desktop은 WSL2 안의 리눅스 가상 머신에서 도커 엔진을 돌리기 때문에, 위 경로는 윈도우 탐색기의 C 드라이브가 아니라 그 가상 머신 안에 있다. 볼륨 위치는 `docker volume inspect 프로젝트명_postgres_data`의 `Mountpoint`로 확인한다.

> 🎓 **newlec 쌤의 코멘트**
>
> 여기서 '프로젝트명'이란 기본적으로 `docker-compose.yml` 파일이 위치한 디렉터리(폴더) 이름이 사용된다. 예를 들어 `docker-compose.yml`이 `ncafe` 폴더에 있다면 프로젝트명은 자동으로 `ncafe`가 되고, 볼륨 이름은 `ncafe_postgres_data`가 된다.
>
> 그런데 만약에 폴더명과 다른 프로젝트 이름을 쓰고 싶다면 `.env` 파일에 `COMPOSE_PROJECT_NAME` 변수를 지정할 수 있다. 해당 변수값이 프로젝트명이 된다.

> 원문 바로잡기 — 원문은 "디렉토리는 ncafe 이며 자동으로 security 가 프로젝트명이 된다"로 적혀 있는데, 폴더 이름이 그대로 프로젝트명이 된다는 앞 문장과 맞지 않는다. 원문 그림에서 `docker-compose.yml`이 있던 폴더 이름이 프로젝트명이 된다고 보면 된다. 위 코멘트는 그 규칙에 맞춰 고친 것이다.

> **추가 설명 — 프로젝트명을 정하는 방법 세 가지**:
>
> ```bash
> # 1) .env 파일 (docker-compose.yml과 같은 폴더)
> COMPOSE_PROJECT_NAME=team-a
>
> # 2) 명령 옵션
> docker compose -p team-a up -d
> ```
>
> ```yaml
> # 3) docker-compose.yml 최상단의 name 항목
> name: team-a
> services:
>   ...
> ```
>
> 이름은 소문자·숫자·`-`·`_`만 쓸 수 있다. 폴더명에 대문자가 있으면 소문자로 바뀐다.

### 2-1. 도커 허브에 있는 컨테이너를 컴포즈에 등록하기

도커 허브에 올라와 있는 중앙 저장소의 공용 이미지를 그대로 사용할 때는 `image` 속성을 사용한다. 데이터베이스처럼 이미 내가 원하는 데이터베이스가 설치된 도커 이미지가 있을 때는 도커 파일을 작성할 필요없이 공식 이미지를 활용하는 것이 일반적이다.

`docker-compose.yml` 파일 내에 서비스 이름(예: `postgres-db`)을 정의하고, 도커 허브의 이미지 이름과 태그(버전)를 적어주면 컴포즈가 실행 시 자동으로 해당 이미지를 다운로드하여 컨테이너로 구동한다. 여기서 정의한 서비스 이름은 컴포즈 내부 네트워크에서 컨테이너의 도메인 네임(호스트명) 역할을 하므로, 다른 컨테이너에서 이 컴퓨터를 찾아갈 때 통신용 이름으로 사용된다.

```yaml
services:
  postgres-db:
    image: postgres:16
    container_name: my-postgres
    environment:
      POSTGRES_DB: mydatabase
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: mypassword
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

각 설정 속성의 역할은 다음과 같다.

- **`postgres-db` (서비스 이름)**: 도커 컴포즈 가상 네트워크 안에서 해당 컨테이너를 식별하는 컴퓨터 이름(호스트명)이 된다. 사용자가 원하는 이름으로 자유롭게 지정할 수 있으며, 네트워크 내부의 다른 컨테이너들은 이 지정한 이름을 통해 데이터베이스에 접근한다.
- **`image`**: 도커 허브에서 불러올 공식 이미지와 버전(`postgres:16`)을 지정한다.
- **`container_name`**: 실행될 컨테이너의 이름을 고정(`my-postgres`)하여 관리하기 쉽게 만든다.
- **`environment`**: 컨테이너 내부 환경 변수를 설정한다. 데이터베이스 이름(`POSTGRES_DB`), 계정명(`POSTGRES_USER`), 비밀번호(`POSTGRES_PASSWORD`)를 전달한다.

> **추가 설명 — 서비스 이름과 `container_name`은 다르다**: 컨테이너끼리 찾아갈 때 쓰는 주소는 **서비스 이름**(`postgres-db`)이다. `container_name`(`my-postgres`)은 `docker ps`나 `docker logs my-postgres`에서 보이는 이름일 뿐이다(같은 네트워크에서는 이 이름으로도 접근은 된다). `container_name`을 빼면 컴포즈가 `프로젝트명-서비스명-1`(예: `ncafe-postgres-db-1`)로 자동으로 붙인다.

> 💡 **여러 팀이 같은 서버를 공유할 때의 충돌 문제**
>
> 위 예시처럼 `postgres_data`라는 이름으로 명명된 볼륨(Named Volume)을 사용하면, 도커 컴포즈는 본래 지정한 볼륨 이름 앞에 프로젝트 폴더 이름(기본 프로젝트명)을 접두어로 붙여 최종 볼륨 이름을 생성한다(예: `projectA_postgres_data`). 즉, 볼륨 이름 자체가 프로젝트 이름이 되는 것은 아니며, 지정한 볼륨 이름 앞에 프로젝트명이 조합된 형태로 생성된다. 따라서 폴더명이나 프로젝트명이 다르면 호스트 서버 상에서 서로 다른 볼륨 공간으로 분리되므로 기본적으로 데이터 덮어쓰기 등의 충돌 문제가 발생하지 않는다.
>
> 하지만 볼륨명이나 프로젝트명이 동일하다면? 물론 그것을 피해야 하겠지만 프로젝트가 수업시간에 다룬 동일 프로젝트라서 폴더명을 바꿀 수가 없다면 다음처럼 마운트 디렉토리를 직접 지정해서 사용할 수도 있다.
>
> 하지만 볼륨 이름이나 프로젝트 명 또는 `.env` 파일을 이용한 설정으로 충돌을 피하는 방법이 더 바람직하다.
>
> 예시 (바인드 마운트 사용):
>
> ```yaml
> services:
>   postgres-db:
>     volumes:
>       - /home/team-a/postgres_data:/var/lib/postgresql/data
> ```

> **추가 설명 — 같은 서버에서 겹치는 것은 볼륨만이 아니다**:
>
> | 겹치는 것 | 증상 | 피하는 방법 |
> |---|---|---|
> | 볼륨 이름 | 두 팀이 같은 DB 데이터를 함께 쓰게 된다 | 프로젝트명을 다르게(`.env`, `-p`, `name:`) |
> | `container_name` | 두 번째로 올리는 쪽이 `container name ... is already in use` 오류 | `container_name`을 빼거나 팀마다 다르게 |
> | 호스트 포트(`ports` 왼쪽) | `port is already allocated` 오류 | 왼쪽 번호를 팀마다 다르게(`"8081:8080"`) |
>
> 프로젝트명만 바꾸면 볼륨·네트워크·자동 컨테이너 이름은 저절로 갈라지지만, **직접 고정한 `container_name`과 호스트 포트는 그대로 겹친다**는 점에 주의한다.
>
> 바인드 마운트(`/경로:컨테이너경로`)와 이름 있는 볼륨(`이름:컨테이너경로`)의 차이는 앞이 `/`나 `./`로 시작하는 **경로**인지, 그냥 **이름**인지다. 바인드 마운트는 최하단 `volumes:`에 선언하지 않는다.

> 🎓 **newlec 쌤의 코멘트**
>
> 이때 `POSTGRES_DB`, `POSTGRES_USER`와 같은 변수 이름은 사용자가 임의로 만드는 것이 아니라, 사용할 도커 이미지(여기서는 PostgreSQL 공식 이미지)의 개발자가 미리 정해놓은 규격이다. 따라서 반드시 해당 이미지에서 지정한 환경 변수 이름을 정확히 사용해야 컨테이너가 이를 인식하여 초기 데이터베이스와 계정을 올바르게 생성한다.
>
> 그렇다면 이 환경변수 이름을 사용자 입장에서 어떻게 알 수 있을까? 가장 확실한 방법은 도커 허브(Docker Hub)의 공식 이미지 설명 페이지를 확인하는 것이다. 도커 허브에서 검색한 이미지 페이지의 **Environment Variables** 항목을 보면 사용할 수 있는 변수명과 설명이 상세히 적혀 있다. 또한, 이미 존재하는 이미지의 환경변수 목록을 터미널에서 직접 확인하고 싶다면 `docker inspect <이미지명>` 명령어를 사용해 이미지에 설정된 기본 환경변수 정보를 살펴볼 수도 있다.

> 원문 바로잡기 — `docker inspect postgres:16`의 `Config.Env`에 나오는 것은 이미지를 만들 때 **이미 값이 정해진** 환경 변수(`PATH`, `PG_VERSION`, `PGDATA` 등)뿐이다. `POSTGRES_USER`, `POSTGRES_PASSWORD`처럼 사용자가 넣어 주기를 기다리는 변수는 이미지 안의 시작 스크립트가 읽는 것이라 여기에 나오지 않는다. 쓸 수 있는 변수 목록은 도커 허브 설명 페이지에서 확인한다.
>
> ```bash
> docker inspect postgres:16 --format '{{json .Config.Env}}'
> # ["PATH=...","GOSU_VERSION=...","LANG=en_US.utf8","PG_MAJOR=16","PG_VERSION=16.x","PGDATA=/var/lib/postgresql/data"]
> ```

> **추가 설명 — 초기화는 처음 한 번만 된다**: `POSTGRES_DB`·`POSTGRES_USER`·`POSTGRES_PASSWORD`는 **데이터 폴더가 비어 있을 때**, 즉 볼륨이 처음 만들어질 때만 적용된다. 볼륨에 데이터가 남아 있는 상태에서 비밀번호를 바꾸고 다시 올리면 바뀐 값이 반영되지 않아 `password authentication failed` 오류가 난다. 개발 중이라 데이터가 필요 없다면 `docker compose down -v`로 볼륨까지 지우고 다시 올린다.

- **`ports`**: 호스트 컴퓨터와 컨테이너의 포트를 연결한다. `"외부포트:내부포트"` 형식으로, 여기서는 내 컴퓨터의 5432 포트 접속(외부포트)을 컨테이너의 5432 포트(내부포트)로 전달한다.

> **추가 설명 — DB의 `ports`는 꼭 필요한가**: 백엔드 컨테이너는 내부 네트워크에서 `postgres-db:5432`로 접속하므로 DB에 `ports`가 없어도 된다. `"5432:5432"`는 내 컴퓨터의 DBeaver·pgAdmin 같은 도구로 DB를 들여다보고 싶을 때만 필요하다. 1-1절의 "보안성 향상"이 바로 이것으로, 운영 서버에서는 DB의 `ports`를 빼서 외부에서 DB로 직접 들어오지 못하게 하는 경우가 많다.

### 2-2. 도커 파일을 직접 빌드한 컨테이너를 컴포즈에 등록하기

직접 개발한 애플리케이션이나 고유한 설정이 포함된 컨테이너는 소스 코드와 Dockerfile을 바탕으로 이미지를 생성해야 한다. 이 경우에는 `image` 대신 `build` 속성을 사용해 Dockerfile의 위치를 지정한다.

`build: .` 설정을 사용하면 컴포즈가 지정된 경로(여기서는 현재 디렉터리)의 Dockerfile을 읽어 들여 이미지를 자동으로 빌드한 뒤 컨테이너를 띄운다.

`ports` 설정의 경우, 호스트 컴퓨터의 외부 포트와 컨테이너 내부 포트를 연결한다. 백엔드 서비스는 컴포즈 내부 네트워크 통신뿐만 아니라 외부 클라이언트(브라우저나 API 요청)나 프론트엔드와 직접 통신해야 하므로 포트를 외부로 노출해야 한다.

단, 여러 사용자가 동일한 호스트 컴퓨터를 공유하는 환경에서는 8080과 같은 기본 포트가 이미 사용 중이거나 충돌할 수 있다. 이 경우 호스트의 외부 포트를 8081, 18080 등 사용 중이지 않은 다른 포트로 변경하여 `"- 외부포트:내부포트"`(예: `"8081:8080"`) 형태로 매핑하면 충돌 없이 외부 접속 경로를 확보할 수 있다.

```yaml
services:
  backend-app:
    build: .
    container_name: my-backend
    ports:
      - "8080:8080"
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres-db:5432/mydatabase
      SPRING_DATASOURCE_USERNAME: myuser
      SPRING_DATASOURCE_PASSWORD: mypassword
    depends_on:
      - postgres-db
```

> **추가 설명 — `build`와 `image`를 같이 쓰면**: `build: .`만 쓰면 빌드된 이미지 이름이 `프로젝트명-backend-app`으로 자동으로 붙는다. `image: my-backend:1.0`을 함께 적으면 빌드한 이미지에 그 이름이 붙는다. Dockerfile 이름이나 위치가 다르면 아래처럼 나눠 적는다.
>
> ```yaml
> build:
>   context: ./backend        # 빌드에 쓸 폴더
>   dockerfile: Dockerfile.prod
> ```

`environment` 섹션에서 지정하는 DB 연결 정보(`SPRING_DATASOURCE_URL` 등)는 컴포즈가 자동으로 DB를 연결해 주는 설정이 아니라, 스프링 부트 애플리케이션에 외부 환경 변수로 값을 주입하는 역할을 한다. 스프링 부트는 기본적으로 `application.properties`나 `application.yml` 파일에서 `${SPRING_DATASOURCE_URL}` 형태의 환경 변수를 참조하도록 설정되어 있어야 이 값을 인식하여 데이터베이스에 접속한다.

만약 백엔드 코드의 설정 파일(`application.yml`)에서 환경 변수를 바인딩하도록 작성되어 있지 않거나 해당 변수를 사용하지 않는다면, 도커 컴포즈의 `environment`에 아무리 올바른 주소를 적어두어도 백엔드 앱은 데이터베이스를 찾지 못하고 연결 오류를 발생시킨다. 따라서 컴포즈에 환경 변수를 정의하기 전에 백엔드 애플리케이션 측에서 이 환경 변수들을 받아 쓰도록 미리 구현되어 있는지 반드시 확인해야 한다.

> 원문 바로잡기 — 스프링 부트는 `${SPRING_DATASOURCE_URL}` 자리표시자를 적어 두지 않아도 이 환경 변수를 **자동으로** 읽는다. **느슨한 바인딩(relaxed binding)** 규칙에 따라 환경 변수 `SPRING_DATASOURCE_URL`은 속성 `spring.datasource.url`로 해석되고(대문자→소문자, `_`→`.`), 환경 변수는 `application.yml`보다 우선순위가 높아서 yml에 `localhost` 주소가 적혀 있어도 덮어쓴다. 그래서 `application.yml`에 아래처럼 로컬 값을 적어 두어도 컨테이너에서는 컴포즈가 준 값으로 접속한다.
>
> ```yaml
> spring:
>   datasource:
>     url: jdbc:postgresql://localhost:5432/mydatabase   # 로컬 실행용. 컨테이너에서는 환경 변수가 덮어씀
>     username: myuser
>     password: mypassword
> ```
>
> 실제로 확인해야 할 것은 바인딩 코드가 아니라 다음 두 가지다.
>
> | 확인할 것 | 이유 |
> |---|---|
> | `build.gradle`에 PostgreSQL 드라이버(`runtimeOnly 'org.postgresql:postgresql'`)가 있는가 | 드라이버가 없으면 주소가 맞아도 접속하지 못한다 |
> | 변수 이름이 속성 이름과 정확히 대응하는가 | `SPRING_DATASOURCE_URL`처럼 정해진 규칙이 아니라 `DB_URL` 같은 임의 이름을 쓸 때만 yml에 `url: ${DB_URL}`처럼 직접 연결해야 한다 |

### 설정을 구성하는 주요 요소

- **`services`**: 작동시킬 상자(컨테이너)들의 목록이다. 여기서는 `postgres-db`와 `backend-app` 두 개를 선언한다.
- **`image`**: 도커 허브에서 다운로드받아 사용할 이미지를 지정한다. 데이터베이스는 공식 `postgres:16` 이미지를 사용한다.
- **`build`**: 직접 만든 Dockerfile을 이용해 이미지를 빌드하라는 뜻이다. 점(`.`)은 현재 위치의 Dockerfile을 사용함을 의미한다.
- **`environment`**: 컨테이너 내부에서 사용할 환경 변수를 적는다. 데이터베이스 이름, 계정 정보, 그리고 스프링 부트가 DB에 접속할 주소를 넘겨준다.
- **`depends_on`**: 실행 순서를 정한다. 백엔드 앱은 데이터베이스가 먼저 준비되어야 하므로 `postgres-db`가 구동된 뒤에 실행되도록 설정한다.

> **추가 설명 — `depends_on`은 "준비 완료"까지 기다리지 않는다**: 기본 `depends_on`은 DB **컨테이너가 시작된 것**만 확인하고 바로 백엔드를 띄운다. PostgreSQL은 컨테이너가 뜬 뒤에도 초기화에 몇 초가 걸리므로, 그 사이 스프링 부트가 먼저 접속을 시도하면 `Connection refused`로 실패할 수 있다. DB가 실제로 접속을 받을 수 있을 때까지 기다리게 하려면 `healthcheck`와 `condition`을 함께 쓴다.
>
> ```yaml
> services:
>   postgres-db:
>     image: postgres:16
>     healthcheck:
>       test: ["CMD-SHELL", "pg_isready -U myuser -d mydatabase"]
>       interval: 5s
>       timeout: 3s
>       retries: 10
>
>   backend-app:
>     build: .
>     depends_on:
>       postgres-db:
>         condition: service_healthy   # 헬스체크를 통과한 뒤에 시작
> ```

## 3. 한 줄의 명령어로 한꺼번에 실행하고 관리하기

설계도 작성이 끝났다면 터미널을 열어 명령어 한 줄만 입력하면 된다.

### 컨테이너 묶음 실행하기

프로젝트 폴더 위치에서 아래 명령어를 입력한다.

```bash
docker compose up -d
```

이 명령어를 실행하면 도커 컴포즈가 `docker-compose.yml` 파일을 읽어 들인다. 먼저 PostgreSQL 이미지를 받아와 컨테이너를 띄우고, 이어서 백엔드 앱의 Dockerfile을 빌드하여 컨테이너로 만든 뒤 두 상자를 자동으로 연결한다.

- **`-d` 옵션**은 컨테이너들을 백그라운드(뒷전)에서 조용히 실행하도록 만드는 옵션이다. 이 옵션을 주면 터미널 창을 닫아도 상자들이 계속해서 돌아간다.

> **추가 설명 — `-d` 없이 실행하면**: 모든 컨테이너의 로그가 터미널에 섞여서 계속 출력되고, 터미널이 그 상태로 묶인다. 이때 `Ctrl+C`를 누르면 컨테이너들이 정지된다. 처음 띄울 때 오류를 바로 보고 싶다면 `-d` 없이 실행해 보는 것도 방법이다.

> **추가 설명 — `docker compose`와 `docker-compose`**: 하이픈이 있는 `docker-compose`는 예전 V1 도구(별도 설치 프로그램)이고, 지금은 도커에 내장된 V2 명령 `docker compose`(띄어쓰기)를 쓴다. 옛 자료에서 `docker-compose up`을 보면 같은 뜻으로 읽으면 된다.

### 실행 상태 확인하기

현재 상자들이 잘 돌아가는지 확인하고 싶다면 아래 명령어를 사용한다.

```bash
docker compose ps
```

이 명령을 통해 `my-postgres`와 `my-backend` 상자가 모두 정상 작동(Up) 중인지 한눈에 살펴볼 수 있다.

### 컨테이너 묶음 전체 종료하기

작업을 마치고 실행 중인 모든 상자를 안전하게 끄고 싶을 때는 다음 명령어를 입력한다.

```bash
docker compose down
```

이 명령 한 줄로 백엔드와 데이터베이스 컨테이너가 순서대로 안전하게 정지되고 삭제된다.

> 원문 바로잡기 — "순서대로"는 실행 순서가 아니라 그 **역순**이다. `depends_on`에 따라 백엔드를 먼저 정지하고 DB를 나중에 정지한다. 또 `down`은 컨테이너와 **네트워크**를 지우지만 이름 있는 볼륨은 남긴다. 그래서 다시 `up` 하면 DB 데이터가 그대로 있다. 볼륨까지 지우려면 `docker compose down -v`를 쓴다.

## 4. 데이터베이스 연결 시 주의할 점

도커 컴포즈 환경에서 백엔드와 데이터베이스를 연결할 때는 몇 가지 중요한 규칙을 지켜야 한다.

### 컨테이너 사이의 주소 찾기 (네트워크 이름 사용)

내 컴퓨터에서 스프링 부트를 실행할 때는 보통 DB 주소로 `localhost:5432`를 사용한다. 하지만 도커 컨테이너 안으로 들어가면 `localhost`는 자기 자신 상자만을 의미하게 된다.

도커 컴포즈는 같은 파일 안에 적힌 상자들을 하나의 비밀 네트워크로 자동 묶어준다. 따라서 백엔드 앱이 데이터베이스 상자를 찾아가려면 `localhost` 대신 컴포즈 파일에 적은 데이터베이스 서비스 이름(`postgres-db`)을 주소로 써야 한다.

```bash
# 잘못된 주소 설정 (컨테이너 내부에서 자기 자신을 찾음)
jdbc:postgresql://localhost:5432/mydatabase

# 올바른 주소 설정 (도커 컴포즈 서비스 이름 이용)
jdbc:postgresql://postgres-db:5432/mydatabase
```

> **추가 설명 — 주소의 포트는 "컨테이너 포트"다**: 컨테이너끼리 통신할 때는 `ports`를 거치지 않는다. DB를 `"15432:5432"`로 공개했더라도 백엔드는 여전히 `postgres-db:5432`로 접속한다. 왼쪽 번호(15432)는 **호스트에서** DB에 들어올 때만 쓰인다.
>
> | 어디서 접속하나 | 주소 |
> |---|---|
> | 같은 컴포즈 안의 백엔드 컨테이너 | `postgres-db:5432` (서비스 이름 + 컨테이너 포트) |
> | 내 컴퓨터의 DBeaver, IDE에서 실행한 스프링 부트 | `localhost:15432` (localhost + 호스트 포트) |

### 데이터 손실을 막는 볼륨(Volumes) 설정

도커 상자는 꺼지거나 삭제되면 그 안에서 일어났던 일들이 전부 사라지는 특징이 있다. 만약 데이터베이스 상자가 꺼졌을 때 회원 정보나 게시글이 전부 날아간다면 큰문제가 된다.

> 원문 바로잡기 — 컨테이너를 **끄는 것**(`docker compose stop`, `docker stop`)만으로는 데이터가 사라지지 않는다. 컨테이너 안의 변경 내용은 컨테이너의 쓰기 레이어에 남아 있어서 다시 `start` 하면 그대로 있다. 데이터가 사라지는 것은 컨테이너를 **삭제**할 때(`docker compose down`, `docker rm`)다. 새 버전 배포나 `down`/`up`을 할 때마다 컨테이너는 지워지고 새로 만들어지므로, 지켜야 할 데이터는 볼륨에 둔다.

이를 막기 위해 상자 내부의 저장소와 내 진짜 컴퓨터의 저장소를 끈으로 연결해 두는 작업이 필요한데, 이를 **볼륨(Volume)**이라고 부른다.

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
```

이렇게 설정해 두면 PostgreSQL이 상자 안 `/var/lib/postgresql/data` 폴더에 쌓는 실제 데이터가 내 컴퓨터의 `postgres_data` 공간에 안전하게 계속 저장된다. 따라서 `docker compose down`으로 상자를 완전히 삭제했다가 나중에 다시 띄워도 기존 데이터가 그대로 남아있게 된다.

> **추가 설명 — 볼륨 확인·삭제 명령**:
>
> | 명령 | 하는 일 |
> |---|---|
> | `docker volume ls` | 볼륨 목록 (`ncafe_postgres_data` 같은 이름이 보인다) |
> | `docker volume inspect ncafe_postgres_data` | 실제 저장 위치(`Mountpoint`) 등 상세 정보 |
> | `docker compose down -v` | 컨테이너·네트워크와 함께 이 프로젝트의 볼륨도 삭제 |
> | `docker volume rm ncafe_postgres_data` | 볼륨 하나 삭제 (사용 중인 컨테이너가 없어야 함) |

### 포트 포워딩과 내부 전용 노출

`docker-compose.yml`에서 백엔드 서비스를 `ports: - "8080:8080"`으로 설정하는 것 자체가 호스트 컴퓨터의 포트와 컨테이너 내부 포트를 연결하는 **포트 포워딩(Port Forwarding)** 설정이다.

도커 컴포즈 네트워크 관점에서 포트 포워딩 동작 원리와 구성 방식은 다음과 같다.

#### 1. 외부 접속을 위한 포트 포워딩 (`ports`)

`ports` 속성은 호스트(내 컴퓨터 또는 외부 서버) 네트워크의 특정 포트로 들어오는 요청을 가상 네트워크 안의 컨테이너 포트로 전달(포워딩)한다.

- **형식**: `"호스트포트:컨테이너포트"`
- **예시**: `"8080:8080"`으로 지정하면 호스트의 8080 포트로 요청이 들어올 때 도커 엔진이 해당 요청을 컴포즈 전용 가상 네트워크를 거쳐 백엔드 컨테이너의 8080 포트로 포워딩한다.
- 호스트 쪽의 포트 번호가 이미 사용 중이라면 `"8081:8080"`처럼 호스트 포트 번호만 변경하여 포워딩할 수 있다.

```
 브라우저 ── localhost:8081 ──▶ [호스트 8081] ──포워딩──▶ [backend-app 컨테이너 8080]
                                                                │
                                                     postgres-db:5432 (내부 네트워크)
                                                                ▼
                                                    [postgres-db 컨테이너 5432]
```

> **추가 설명 — 같은 컴퓨터의 다른 기기에서만 접속을 막고 싶다면**: `"8080:8080"`은 호스트의 **모든 네트워크 주소**(`0.0.0.0`)에 포트를 열어서 같은 와이파이의 다른 기기에서도 접속할 수 있다. 내 컴퓨터에서만 접속하게 하려면 `"127.0.0.1:8080:8080"`처럼 앞에 주소를 붙인다.

#### 2. 컴포즈 내부 통신 전용 노출 (`expose`)

만약 백엔드 앱이 외부 브라우저나 클라이언트에 직접 노출될 필요가 없고, 컴포즈 가상 네트워크 내부의 다른 컨테이너(예: Nginx 리버스 프록시)를 통해서만 접근해야 한다면 호스트에 포트를 직접 개방하는 `ports` 대신 `expose` 속성을 사용할 수 있다.

```yaml
  backend-app:
    build: .
    container_name: my-backend
    expose:
      - "8080" # 호스트 포트 개방 없이 컴포즈 가상 네트워크 내부에서만 8080 포트 접근 허용
```

이 방식을 사용하면 호스트 컴퓨터의 포트를 차지하지 않고도 컴포즈 가상 네트워크 안에서만 안전하게 포트 통신을 수행할 수 있다.

> 원문 바로잡기 — `expose`가 내부 통신을 **허용해 주는** 것은 아니다. 같은 네트워크의 컨테이너끼리는 `expose`가 없어도 컨테이너 안에서 열려 있는 모든 포트로 서로 접속할 수 있다. 실제로 이 예시의 `postgres-db`에도 `expose`가 없지만 백엔드는 `postgres-db:5432`로 잘 접속한다. `expose`는 "이 서비스는 8080을 쓴다"는 **문서 표시**에 가깝고(Dockerfile의 `EXPOSE`와 같은 역할), 핵심은 **`ports`를 쓰지 않는 것**이다. `ports`가 없으면 호스트에서 들어오는 길이 없으므로 외부에 노출되지 않는다.
>
> | 설정 | 호스트·외부에서 접속 | 같은 네트워크 컨테이너에서 접속 |
> |---|---|---|
> | `ports: - "8080:8080"` | 된다 | 된다 |
> | `expose: - "8080"` | 안 된다 | 된다 |
> | 둘 다 없음 | 안 된다 | **된다** |

### 도커 컴포즈 주요 명령어 정리

도커 컴포즈 서비스를 관리할 때 자주 사용하는 핵심 명령어와 주요 옵션 목록이다. 모든 명령어는 `docker-compose.yml` 파일이 위치한 디렉터리에서 실행해야 한다.

#### 1. 서비스 실행 및 정지

- **`docker compose up`**: 정의된 모든 서비스를 빌드하고 생성하여 실행한다.
  - `-d`: 백그라운드(Detached) 모드로 실행하고 터미널을 바로 돌려준다.
  - `--build`: 이미지가 존재하더라도 Dockerfile 변경 사항을 반영하여 강제로 다시 빌드한다.
- **`docker compose down`**: 실행 중인 모든 컨테이너, 네트워크를 정지하고 삭제한다.
  - `-v` 또는 `--volumes`: 컴포즈 파일에 정의된 볼륨까지 함께 삭제한다. (데이터베이스의 데이터도 삭제되므로 주의 필요)
- **`docker compose start`**: `stop`으로 정지해 둔 기존 컨테이너들을 새로 만들지 않고 다시 실행한다.
- **`docker compose stop`**: 컨테이너를 삭제하지 않고 정지 상태로 전환한다.
- **`docker compose restart`**: 실행 중인 컨테이너들을 껐다가 다시 켠다.

> **추가 설명 — 코드를 고쳤는데 반영이 안 될 때**: `build:`로 만든 서비스는 이미지가 한 번 만들어지면 `docker compose up`만으로는 **다시 빌드하지 않는다.** 자바 코드를 고친 뒤에는 `docker compose up -d --build`로 이미지를 새로 만들어야 바뀐 코드가 컨테이너에 들어간다. `restart`는 같은 컨테이너를 다시 켜는 것이라 코드 변경도, `docker-compose.yml`의 `environment` 변경도 반영하지 않는다. yml을 고쳤다면 `docker compose up -d`를 다시 실행하면 바뀐 서비스만 새로 만들어진다.
>
> | 바꾼 것 | 반영 명령 |
> |---|---|
> | 자바 코드, Dockerfile | `docker compose up -d --build` |
> | `docker-compose.yml`(환경 변수, 포트 등) | `docker compose up -d` |
> | 아무것도 안 바꾸고 다시 켜기만 | `docker compose restart` |

#### 2. 상태 및 로그 확인

- **`docker compose ps`**: 현재 컴포즈로 관리되는 컨테이너들의 상태, 포트 매핑 정보를 확인한다.
- **`docker compose logs`**: 서비스의 출력 로그를 확인한다.
  - `-f`: 로그 출력을 실시간으로 모니터링한다. (예: `docker compose logs -f backend-app`)
- **`docker compose top`**: 각 컨테이너 내부에서 실행 중인 프로세스 목록을 보여준다.

#### 3. 유지보수 및 명령어 전달

- **`docker compose exec <서비스명> <명령어>`**: 실행 중인 특정 컨테이너 내부에서 명령어를 직접 수행한다.
  - 예: `docker compose exec postgres-db bash` (PostgreSQL 컨테이너 터미널 접속)
- **`docker compose config`**: 작성한 `docker-compose.yml` 파일의 문법적 오류를 검증하고 최종 해석된 구성을 출력한다.

> **추가 설명 — `exec`에는 서비스 이름, `docker exec`에는 컨테이너 이름**: `docker compose exec postgres-db ...`는 **서비스 이름**을, `docker exec -it my-postgres ...`는 **컨테이너 이름**을 받는다. DB 안에 바로 들어가 쿼리를 쳐 보려면 `psql`을 실행한다.
>
> ```bash
> docker compose exec postgres-db psql -U myuser -d mydatabase
> # mydatabase=# \dt        ← 테이블 목록
> # mydatabase=# \q         ← 종료
> ```

## 5. 마무리

이번 글에서는 단일 컨테이너 실행 방식의 한계를 극복하고, 도커 컴포즈(Docker Compose)를 활용해 스프링 부트 백엔드와 PostgreSQL 데이터베이스를 하나의 완성된 서비스 환경으로 구축하는 방법을 살펴보았다.

도커 컴포즈를 도입함으로써 얻을 수 있는 핵심 이점과 주의해야 할 사항은 다음과 같다.

- **환경 구축의 자동화와 단순화**: 복잡한 네트워크 설정이나 긴 도커 실행 명령어를 매번 입력할 필요 없이, `docker-compose.yml` 파일 하나로 다중 컨테이너의 빌드 및 실행 환경을 일관되게 정의할 수 있다.
- **명령어 기반의 일괄 관리**: `docker compose up -d`와 `docker compose down` 명령어를 통해 서비스 전체의 생명주기(생성·실행·정지·삭제)를 한 번에 제어할 수 있다.
- **격리된 전용 네트워크**: 자동 생성되는 컴포즈 전용 가상 네트워크 덕분에 컨테이너 안쪽 포트끼리는 충돌하지 않으며, 컨테이너끼리는 IP 주소가 아닌 서비스 이름으로 안전하게 통신한다. 단, `ports`로 호스트에 공개한 포트는 여전히 겹치지 않게 정해야 한다.
- **데이터 영속성 확보**: 컨테이너의 데이터 휘발성 문제를 해결하기 위해 볼륨(Volume)을 설정하여, 컨테이너가 삭제되고 다시 생성되어도 데이터베이스의 데이터가 유지되도록 안전장치를 마련하였다.

이처럼 도커 컴포즈는 개발 환경뿐만 아니라 테스트 및 검증 환경에서도 애플리케이션과 데이터베이스의 의존 관계를 깔끔하게 다룰 수 있도록 돕는 강력한 도구이다. 작성한 `docker-compose.yml` 파일만 전해주면 누구든, 어떤 환경에서든 동일한 실행 환경을 단 한 줄의 명령어로 손쉽게 재현할 수 있다.

> **추가 설명 — 비밀번호는 `.env`로 빼 둔다**: 위 예시처럼 비밀번호를 `docker-compose.yml`에 그대로 적으면 Git에 함께 올라간다. 같은 폴더의 `.env` 파일에 값을 두고 yml에서는 `${변수}`로 참조한 뒤, `.env`는 `.gitignore`에 넣는다. 컴포즈는 `.env`를 자동으로 읽는다.
>
> ```bash
> # .env
> DB_NAME=mydatabase
> DB_USER=myuser
> DB_PASSWORD=mypassword
> ```
>
> ```yaml
> # docker-compose.yml
> services:
>   postgres-db:
>     environment:
>       POSTGRES_DB: ${DB_NAME}
>       POSTGRES_USER: ${DB_USER}
>       POSTGRES_PASSWORD: ${DB_PASSWORD}
>   backend-app:
>     environment:
>       SPRING_DATASOURCE_URL: jdbc:postgresql://postgres-db:5432/${DB_NAME}
>       SPRING_DATASOURCE_USERNAME: ${DB_USER}
>       SPRING_DATASOURCE_PASSWORD: ${DB_PASSWORD}
> ```
>
> 여기서 `${DB_NAME}`은 **컴포즈가** yml을 읽을 때 `.env` 값으로 바꿔 넣는 것이고, 앞의 `SPRING_DATASOURCE_URL`을 스프링이 읽는 것과는 다른 단계다. 팀원에게는 값을 비운 `.env.example`을 올려 두면 어떤 변수가 필요한지 알 수 있다.
