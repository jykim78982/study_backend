---
tags: [Docker, PostgreSQL, 데이터베이스, 배포, 실습]
---

> 🔗 관련 노트: [[041_Docker 설치 — WSL Ubuntu 환경 실습]] · [[042_Docker 실습 — 컨테이너 라이프사이클과 내부 구조 탐구]]

# Docker로 팀 공용 PostgreSQL 개발 DB 만들기

**대상**: `docker run`, `docker ps`, `docker exec` 명령은 알고, 팀원들이 함께 쓸 개발용 PostgreSQL을 Docker로 올리고 싶은 사람

**목표**: Docker 컨테이너로 PostgreSQL을 기동하고, `ncafe` 사용자로 `ncafedb`에 접속해 테이블을 만들 수 있는 환경을 만든다

**완성물**: Docker 호스트 IP로 접속 가능한 PostgreSQL 컨테이너, `ncafe` 사용자, `ncafedb` 데이터베이스, `public` 스키마의 `products` 테이블

**준비물**

- Docker Desktop(Windows/Mac) 또는 Docker가 설치된 리눅스 호스트
- 로컬 개발용이라면 아무 준비물 없음
- 운영서버용이라면: 클라우드 서버에 Docker가 설치되어 있어야 한다. 운영서버에 올릴 때는 포트 번호가 기존 서비스와 충돌하지 않도록 사전에 할당받은 포트 번호를 써야 한다. 이 글에서는 예시로 5432 포트를 쓰지만, 운영서버라면 안내받은 포트로 치환한다.

## 1. 컨테이너 기동

`docker run` 명령으로 PostgreSQL 컨테이너를 기동한다. 볼륨 마운트와 환경변수를 함께 설정해야 데이터가 안전하게 유지되고 초기 설정이 가능하다.

```bash
docker run -d \
  --name postgres-team \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres123 \
  -e POSTGRES_DB=ncafedb \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:16
```

> Windows/Mac은 Docker Desktop을 사용하므로 위 명령이 그대로 동작한다. Linux에서 `sudo` 없이 실행되지 않으면 `sudo`를 붙여 실행한다.

**명령 설명**

- `-d`: 백그라운드 실행
- `--name postgres-team`: 컨테이너 이름
- `-e POSTGRES_USER=postgres`: 초기 슈퍼유저
- `-e POSTGRES_PASSWORD=postgres123`: 초기 비밀번호
- `-e POSTGRES_DB=ncafedb`: 초기 데이터베이스(선택 사항, 7단계에서 다시 만들 수도 있지만 미리 만들어두면 편함)
- `-v postgres_data:/var/lib/postgresql/data`: 볼륨 마운트 (2단계에서 자세히 설명)
- `-p 5432:5432`: 포트 매핑 (호스트 5432 → 컨테이너 5432)

**✅ 확인**

```bash
docker ps
```

- `postgres-team` 컨테이너가 `Up` 상태로 보인다.
- PORTS 컬럼에 `0.0.0.0:5432->5432/tcp`가 보인다.

**🎓 코멘트**: `-e`로 환경변수를 넘겨주면 PostgreSQL이 첫 기동 시 초기 설정을 자동으로 수행한다. `POSTGRES_USER`와 `POSTGRES_PASSWORD`는 필수이고, `POSTGRES_DB`는 선택 사항이다. `-v`로 볼륨을 마운트하는 이유는 2단계에서 자세히 설명한다. 이 단계에서는 "데이터가 컨테이너 안에만 있으면 삭제 시 사라진다"는 점만 기억하면 된다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `port is already allocated` | 5432 포트가 이미 사용 중 | `lsof -i :5432`(Mac) 또는 `netstat -tlnp \| grep 5432`(Linux)로 확인 후 다른 포트로 변경 또는 기존 프로세스 종료 |
| 컨테이너가 바로 종료됨 | 이미지가 잘못되었거나 볼륨 권한 문제 | `docker logs postgres-team`으로 에러 로그 확인 |

**📝 핵심**: `docker run`으로 컨테이너를 기동할 때 `-e`로 환경변수, `-v`로 볼륨, `-p`로 포트를 설정한다. 컨테이너 이름은 `--name`으로 지정하면 나중에 관리가 편하다.

## 2. 볼륨 마운트로 데이터 보존하기

컨테이너는 격리된 환경이므로, 컨테이너 내부에 저장된 데이터는 컨테이너가 삭제되면 함께 사라진다. 그 문제를 해결하기 위해 볼륨 마운트 방식으로 호스트 컴퓨터의 저장소를 도커 컨테이너에 마운트해서 해결한다.

**볼륨(Volume)이란?** Docker가 호스트 OS 레벨에서 직접 관리하는 영구 저장소다. 컨테이너의 생명주기와 독립적으로 존재하므로, 컨테이너를 삭제하더라도 볼륨에 저장된 데이터는 그대로 남아있다.

```bash
docker volume ls
```

**볼륨의 역할**

- 컨테이너 내부 경로: `/var/lib/postgresql/data` (PostgreSQL 데이터 저장 위치)
- Docker 볼륨: `postgres_data` (호스트 OS가 관리하는 저장소)
- 연결: `-v postgres_data:/var/lib/postgresql/data`로 컨테이너의 데이터 디렉토리를 볼륨에 연결

**✅ 확인**

- `docker volume ls`에 `postgres_data`가 보인다.
- 컨테이너를 삭제해도 볼륨은 남아있다.

**🎓 코멘트**: 컨테이너는 "가벼운 가상머신"이 아니라 "격리된 프로세스"다. 컨테이너를 삭제하면 그 안에 있는 파일도 함께 사라진다. 하지만 볼륨은 Docker가 호스트 OS 레벨에서 관리하는 저장소이므로, 컨테이너가 아무리 삭제되어도 볼륨은 남아있다. 그래서 팀 공용 DB는 반드시 볼륨에 마운트해야 한다 — 컨테이너를 재기동하거나 업그레이드할 때 데이터가 사라지지 않기 때문이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| 컨테이너 삭제 후 데이터가 사라짐 | 볼륨 없이 컨테이너 내부에 저장 | `-v` 옵션으로 볼륨 마운트 후 재기동 |
| 볼륨이 보이지 않음 | `docker volume ls`를 다른 컨텍스트에서 실행 | Docker Desktop의 컨텍스트 확인 |

**📝 핵심**: 컨테이너 삭제 시 내부 데이터는 사라지지만, 볼륨은 남아있다. 팀 공용 DB는 반드시 볼륨에 마운트해야 데이터가 안전하게 유지된다.

## 3. PostgreSQL 접속하기

PostgreSQL에 접속하는 방법은 두 가지다. 컨테이너가 있는 호스트 컴퓨터에서라면 `localhost`로 접속하는 방법과, Docker 호스트 IP로 접속하는 방법이다.

**로컬 접속(localhost)**

```bash
psql -h localhost -p 5432 -U postgres -d ncafedb
```

비밀번호: `postgres123`

> 포트 매핑을 `5433:5432`로 설정했다면, 호스트의 5433 포트로 접속해야 한다(기본값 5432로는 접속이 안 됨).

**Docker 호스트 IP로 접속**

팀원들이 원격으로 접속하려면 Docker 호스트의 IP를 사용해야 한다.

```bash
# Mac
ifconfig | grep "inet " | grep -v 127.0.0.1
# Windows
ipconfig | findstr "IPv4"
# Linux
hostname -I
```

예를 들어 Docker 호스트 IP가 `192.168.1.100`이라면:

```bash
psql -h 192.168.1.100 -U postgres -d ncafedb
```

> 운영서버는 공개 IP 또는 내부 IP를 사용해야 하며, 방화벽 설정이 필요할 수 있다. 원격 접속이 가능하도록 하려면 `pg_hba.conf` 파일에서 `ncafe` 사용자와 해당 IP 대역에 대한 접속 허용 규칙(host 엔트리)이 별도로 설정되어 있어야 한다.

**`pg_hba.conf` 설정 방법**

1. 도커 컨테이너 환경이므로 호스트 파일 시스템이 아닌 컨테이너 내부의 파일을 수정해야 한다. 먼저 컨테이너 셸로 진입한다.

   ```bash
   docker exec -it postgres-team bash
   ```

2. 진입한 컨테이너 터미널에서 `pg_hba.conf` 파일을 편집한다.

   ```bash
   nano /var/lib/postgresql/data/pg_hba.conf
   ```

3. 파일 하단에 host 엔트리를 추가한다.

   ```
   # TYPE  DATABASE        USER            ADDRESS                 METHOD
   host    ncafedb         ncafe           0.0.0.0/0               md5
   ```

   - `0.0.0.0/0`: 모든 IP 주소에서 접속을 허용한다. 보안이 중요하면 특정 IP 대역(예: `192.168.1.0/24`)으로 제한한다.
   - `md5`: 비밀번호 인증을 사용한다.

4. 파일을 저장한 후 PostgreSQL을 재시작한다.

   - 방법 1 (컨테이너 내부에서 프로세스만 재시작): 컨테이너 셸에서 `service postgresql restart` 또는 `pg_ctl restart -D /var/lib/postgresql/data`
   - 방법 2 (컨테이너 자체 재시작): 컨테이너 셸을 `exit`한 뒤, 호스트 터미널에서 `docker restart postgres-team`

**✅ 확인**

- `psql` 프롬프트가 나타난다(`ncafedb=#`).
- 로컬과 호스트 IP 두 가지 방법으로 모두 접속이 가능하다.

**🎓 코멘트**: 로컬에서는 `localhost`가 가장 편하다. 하지만 팀원들이 각자의 컴퓨터에서 접속하려면 Docker 호스트의 IP를 사용해야 한다. Docker 컨테이너는 호스트의 네트워크 인터페이스에 포트가 매핑되므로, 호스트 IP로 접속하면 컨테이너 내부의 PostgreSQL로 연결된다. 운영서버는 방화벽 설정이 필요할 수 있으므로, 포트가 외부로 열려 있는지 확인해야 한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `could not connect to server: Connection refused` | 포트가 열려 있지 않거나 방화벽 차단 | `docker ps`로 포트 매핑 확인, 방화벽 설정 확인 |
| `password authentication failed` | 비밀번호가 틀림 | `postgres123`이 맞는지 확인 |

**📝 핵심**: 로컬에서는 `localhost`, 원격에서는 Docker 호스트 IP로 접속한다. 운영서버는 방화벽 설정이 필요할 수 있다.

## 4. 컨테이너 내부에서 직접 접속하기

`docker exec` 명령을 사용하면 컨테이너 내부로 직접 들어가서 `psql`을 실행할 수 있다. 로컬에 `psql` 클라이언트가 설치되어 있지 않은 경우에도 유용하다.

```bash
docker exec -it postgres-team psql -U postgres
```

**✅ 확인**

- `psql` 프롬프트가 나타난다(`postgres=#`).
- 컨테이너 내부에서 PostgreSQL에 접속한 상태다.

**🎓 코멘트**: `docker exec`는 컨테이너 내부에서 명령을 실행하는 방법이다. `-it`는 인터랙티브 모드와 터미널 할당을 의미한다. 이 방법은 로컬에 `psql` 클라이언트가 설치되어 있지 않아도 컨테이너 내부의 `psql`을 사용할 수 있게 해준다. 팀원들이 로컬에 PostgreSQL 클라이언트를 설치하지 않아도, Docker 호스트에서 `docker exec`로 접속할 수 있다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `OCI runtime exec failed` | 컨테이너가 실행 중이 아님 | `docker ps`로 컨테이너 상태 확인, 필요 시 `docker start postgres-team` |

**📝 핵심**: `docker exec -it`로 컨테이너 내부에서 명령을 실행할 수 있다. 로컬에 `psql` 클라이언트가 없어도 이 방법으로 접속할 수 있다.

## 5. 팀 전용 사용자와 데이터베이스 만들기

**사용자 생성**

`psql` 프롬프트에서:

```sql
CREATE USER ncafe WITH PASSWORD 'ncafe123';
```

**✅ 확인**: `CREATE ROLE` 메시지가 출력된다.

**🎓 코멘트**: PostgreSQL의 사용자는 "역할(role)"이라고도 한다. `CREATE USER`는 `CREATE ROLE`의 별칭이다. 비밀번호는 `WITH PASSWORD`로 설정한다. 이 사용자는 나중에 `ncafedb`에 접속할 때 사용된다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `role "ncafe" already exists` | 이미 존재하는 사용자 | `DROP USER ncafe;` 후 재실행 또는 기존 사용자 사용 |

**데이터베이스 생성**

`docker run` 시 `POSTGRES_DB=ncafedb` 환경변수로 이미 초기 생성되었을 수 있지만, 명시적으로 생성 명령을 실행하는 것이 상태 확인에 더 확실하다.

```sql
CREATE DATABASE ncafedb;
```

> 1단계에서 `POSTGRES_DB=ncafedb`를 설정했다면 이미 존재하므로 `database "ncafedb" already exists` 에러가 날 수 있다. 에러가 나면 무시하고 다음 단계로 진행한다.

**✅ 확인**: `CREATE DATABASE` 메시지가 출력되거나, 이미 존재한다는 에러가 나면 이미 존재하는 것이다.

**🎓 코멘트**: 데이터베이스는 PostgreSQL의 최상위 컨테이너다. 하나의 PostgreSQL 인스턴스 안에 여러 데이터베이스를 가질 수 있다. `ncafedb`는 팀 프로젝트의 개발용 데이터베이스다.

**📝 핵심**: `CREATE USER`로 새 사용자를, `CREATE DATABASE`로 새 데이터베이스를 생성한다. 이미 존재하면 에러가 나지만 무시해도 된다.

## 6. 권한 부여하기

`ncafe` 사용자에게 `ncafedb`에 접속하고 테이블을 생성할 수 있는 권한을 부여한다.

```sql
GRANT ALL PRIVILEGES ON DATABASE ncafedb TO ncafe;
```

`ncafedb`로 전환 후 `public` 스키마에 대한 권한도 부여한다.

```sql
\c ncafedb
GRANT ALL ON SCHEMA public TO ncafe;
```

**✅ 확인**: `GRANT` 명령이 성공적으로 실행되고, `ncafe` 사용자가 `ncafedb`에 접속할 수 있다.

**🎓 코멘트**: PostgreSQL의 권한은 세 단계로 나뉜다 — 1) 데이터베이스 접속 권한, 2) 스키마 권한, 3) 테이블/뷰 등 객체 권한. `GRANT ALL PRIVILEGES ON DATABASE`는 데이터베이스에 접속할 수 있는 권한을 부여하고, `GRANT ALL ON SCHEMA public`은 `public` 스키마에서 테이블을 생성하고 기존 테이블에 접근할 수 있는 권한을 부여한다. 개발용이므로 `ALL`을 사용하는 것이 편하다. 운영용이라면 더 세분화된 권한을 설정해야 한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `permission denied for database ncafedb` | 데이터베이스 접속 권한 없음 | `GRANT ALL PRIVILEGES ON DATABASE ncafedb TO ncafe;` 실행 |
| `permission denied for schema public` | 스키마 권한 없음 | `GRANT ALL ON SCHEMA public TO ncafe;` 실행 |

**📝 핵심**: 데이터베이스 접속 권한과 스키마 권한을 별도로 부여해야 한다. 개발용은 `ALL` 권한, 운영용은 세분화된 권한을 사용한다.

## 7. ncafe 사용자로 테이블 만들고 확인하기

```bash
\q
psql -h localhost -U ncafe -d ncafedb
```

비밀번호: `ncafe123`

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

\dt
```

**✅ 확인**

- `psql` 프롬프트가 `ncafedb=#`으로 바뀐다.
- `CREATE TABLE` 명령이 성공적으로 실행된다.
- `\dt` 명령에 `products` 테이블이 목록에 보인다.

**🎓 코멘트**: 이제 `ncafe` 사용자가 `ncafedb`에 접속하고 테이블을 생성할 수 있다. 각 팀원은 `ncafe` 계정으로 접속해서 자유롭게 테이블을 생성하고 데이터를 관리할 수 있다. `SERIAL`은 자동 증가 ID를 생성하는 데이터 타입이고, `DECIMAL(10, 2)`는 소수점 둘째 자리까지의 정밀도를 가지는 숫자 타입이다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `permission denied for schema public` | 6단계에서 스키마 권한을 부여하지 않음 | `GRANT ALL ON SCHEMA public TO ncafe;`를 다시 실행 |
| `relation "products" already exists` | 이미 존재하는 테이블 | `DROP TABLE products;` 후 재실행 또는 기존 테이블 사용 |

**📝 핵심**: `ncafe` 사용자로 접속해서 테이블을 생성할 수 있다. 팀원들은 `ncafe` 계정으로 자유롭게 개발할 수 있다.

## 마무리

- 로컬과 운영서버의 Docker 설치 방식은 동일하지만, 운영서버는 포트 충돌 방지를 위해 사전에 할당된 포트를 사용해야 한다.
- `docker run`으로 PostgreSQL 컨테이너를 기동할 때 `-e`로 환경변수, `-v`로 볼륨, `-p`로 포트를 설정한다.
- 컨테이너 삭제 시 내부 데이터는 사라지지만, 볼륨은 남아있으므로 팀 공용 DB는 반드시 볼륨에 마운트해야 한다.
- 로컬에서는 `localhost`, 원격에서는 Docker 호스트 IP로 접속한다.
- `docker exec -it`로 컨테이너 내부에서 `psql`을 실행할 수 있다.
- `CREATE USER`로 `ncafe` 사용자를, `CREATE DATABASE`로 `ncafedb` 데이터베이스를 생성한다.
- `GRANT` 명령으로 데이터베이스 접속 권한과 스키마 권한을 부여한다.
- `ncafe` 사용자로 접속해서 테이블을 생성하고 확인한다.
