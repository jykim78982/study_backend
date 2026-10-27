# Docker Compose 오답노트

### 1. depends_on으로 보장되는 것

**문제**: Compose의 `depends_on` 설정으로 보장되는 것은 무엇인가?

1. 의존 서비스의 완전한 준비(예: DB가 연결 가능 상태)까지 대기한다.
2. 서비스의 생성 순서를 선언적으로 지정하여 먼저 시작하도록 하는 것이다.
3. 서비스 간 네트워크 격리를 해제한다.
4. 의존 서비스의 포트 매핑을 자동으로 설정한다.

**정답: 2번**

**`depends_on`은 "켜지는 순서"만 정한다**

```yaml
services:
  backend-app:
    build: .
    depends_on:
      - postgres-db
```

이 설정은 Compose에게 "`postgres-db` 컨테이너를 **먼저 시작**한 다음에 `backend-app`을 시작하라"고 알려 주는 것이다. Compose가 확인하는 것은 DB **컨테이너가 시작되었는가**까지이고, 그 안의 PostgreSQL이 접속을 받을 준비가 되었는지는 보지 않는다.

**1번이 틀린 이유 — 가장 흔한 오해**

컨테이너가 "시작됨"과 서비스가 "준비됨"은 다르다.

```
시간 ──────────────────────────────────────────────────────────▶

postgres-db  [컨테이너 시작] ─ 초기화 중 (수 초) ─▶ [접속 받을 준비 완료]
                    │
                    └─ depends_on 은 여기까지만 확인
                         │
backend-app              [컨테이너 시작] ─ 스프링 기동 ─ DB 접속 시도 ✗ Connection refused
```

DB 엔진이 부팅을 마치기 전에 스프링 부트가 접속을 시도하면 `Connection refused`로 기동에 실패한다. 즉 `depends_on`만으로는 **완전한 준비를 보장하지 않는다.**

**준비 완료까지 기다리게 하려면 — healthcheck + condition**

```yaml
services:
  postgres-db:
    image: postgres:17
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myuser -d mydatabase"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend-app:
    build: .
    depends_on:
      postgres-db:
        condition: service_healthy   # 헬스체크를 통과한 뒤에 시작
```

`condition`에 쓸 수 있는 값은 세 가지다.

| 값 | 기다리는 시점 | 쓰는 곳 |
|---|---|---|
| `service_started` (기본값) | 컨테이너가 **시작**되면 | 짧은 목록 형식(`- postgres-db`)과 같다 |
| `service_healthy` | `healthcheck`가 **healthy**가 되면 | DB처럼 준비 시간이 필요한 서비스 |
| `service_completed_successfully` | 컨테이너가 **정상 종료**(exit 0)되면 | DB 마이그레이션처럼 한 번 실행하고 끝나는 작업 |

`service_healthy`를 쓰려면 의존 대상 서비스에 반드시 `healthcheck`가 있어야 한다.

**나머지 보기가 틀린 이유**

| 보기 | 실제 |
|---|---|
| 3. 네트워크 격리를 해제 | 같은 Compose 파일의 서비스는 처음부터 **같은 기본 네트워크**(`프로젝트명_default`)에 들어 있어서 서비스 이름으로 서로 통신한다. 해제할 격리가 없고, `depends_on`은 네트워크와 무관하다 |
| 4. 포트 매핑을 자동 설정 | 포트 매핑은 각 서비스의 `ports`에 직접 적어야 한다. 또 컨테이너끼리 통신할 때는 포트 매핑이 아예 필요 없다(`postgres-db:5432`로 바로 접속) |

> **헷갈리기 쉬운 점 — `depends_on`이 하는 일은 순서 하나가 아니다**: 시작 순서 외에도 몇 가지가 따라온다. 모두 "의존 관계"에서 나오는 것이고, 준비 상태 보장은 여전히 `condition`이 맡는다.
>
> | 상황 | `depends_on`의 영향 |
> |---|---|
> | `docker compose up -d` | 의존 대상(DB)을 먼저 시작 |
> | `docker compose down` / `stop` | **역순**으로 정지 (백엔드 먼저, DB 나중) |
> | `docker compose up -d backend-app` | 백엔드만 지정해도 의존 대상인 DB까지 **같이 시작** |

> **추가 설명 — 그래도 앱 쪽 대비가 필요한 이유**: `service_healthy`는 **처음 시작할 때**만 기다려 준다. 운영 중에 DB가 재시작되면 백엔드는 연결이 끊긴 채 계속 돈다. 그래서 운영에서는 `restart: always`로 실패한 컨테이너가 다시 켜지게 하고, 스프링 쪽 커넥션 풀(HikariCP)이 끊긴 연결을 다시 맺도록 두는 등 **앱도 DB가 잠시 없을 수 있다고 가정**하고 만든다.

**정리**: `depends_on`은 서비스의 **시작 순서**만 보장한다. 의존 서비스가 실제로 요청을 받을 수 있는 상태까지 기다리게 하려면 `healthcheck`와 `condition: service_healthy`를 함께 써야 한다.
