---
tags: [요약, Docker, Dockerfile, Compose, 배포, 컨테이너]
---

# Docker와 배포 요약

개발 환경과 운영 환경이 달라서 생기는 문제를 **컨테이너**로 해결한다. 이미지로 환경을 통째로 묶고, Compose로 여러 컨테이너를 한 번에 실행한다.

## 1. 한눈에 보기

| 주제 | 핵심 |
|---|---|
| 문제의 배경 | 내 컴퓨터에서는 되는데 서버에서는 안 된다 |
| 가상 머신 | OS 전체를 가상화한다. 무겁다 |
| 도커 | 호스트 커널을 공유하는 경량 실행 환경. 읽기 전용 파일은 공유한다 |
| 핵심 용어 | 이미지(실행 준비 완료), 컨테이너(실행 인스턴스), 엔진 |
| 기술 원리 | 네임스페이스(격리), cgroup(자원 제한), 유니온 파일 시스템(레이어) |
| 용도 | 작업 환경이 아니라 **배포·실행 환경** |
| 왜 리눅스, WSL | 도구와 서버 대부분이 리눅스 태생이고 도커는 리눅스 네이티브다 |
| Dockerfile | 설치 정보(요리법). `FROM` → `WORKDIR` → `COPY` → `ENTRYPOINT` |
| 빌드와 실행 | `docker build -t 이름:태그 .` → `docker run` |
| 포트 포워딩 | `-p 호스트:컨테이너` |
| 멀티 스테이지 빌드 | JDK 컨테이너에서 빌드하고, JRE 컨테이너에는 결과 JAR만 넣는다 |
| Docker Compose | 여러 컨테이너를 한 파일로 묶어 순서대로 올리고 내린다 |

## 2. 개념 정리

### 2-1. Dockerfile → 이미지 → 컨테이너

```
Dockerfile --build--> 이미지 --run--> 컨테이너
(설치 정보)          (실행 준비 완료)   (실행 중인 인스턴스)
```

- GitHub에는 Dockerfile만 올린다.
- 멈춘 컨테이너는 이미지가 아니다. 실행했던 상태가 남아 있다.
- 지켜야 할 데이터는 **볼륨**으로 컨테이너 밖에 둔다.

### 2-2. 스프링 부트 Dockerfile 예 (멀티 스테이지)

```dockerfile
FROM eclipse-temurin:21-jdk AS build
WORKDIR /app
COPY . .
RUN ./gradlew bootJar

FROM eclipse-temurin:21-jre
COPY --from=build /app/build/libs/*.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
```

- 베이스 이미지는 공식 이미지이고, 개발 환경과 같은 JDK 배포본(Temurin)으로, 태그로 버전을 고정한다.

### 2-3. Docker Compose

```yaml
services:
  backend:
    build: ./backend
    ports: ["8080:8080"]        # 왼쪽이 밖, 오른쪽이 컨테이너
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres-db:5432/ncafedb
    depends_on: [postgres-db]
  postgres-db:
    image: postgres:16
    volumes: [dbdata:/var/lib/postgresql/data]
volumes:
  dbdata:
```

- Compose는 **격리된 가상 네트워크**를 만든다. 그 안에서는 **서비스 이름**으로 서로를 찾는다 (`postgres-db:5432`).
- 밖으로 열 것만 `ports`로 연다. 브라우저가 쓸 수 없는 DB는 열지 않는다.
- `environment`로 넘긴 `SPRING_DATASOURCE_*`는 `application.yml`보다 **우선**한다. 비밀 정보는 `.env`로 뺀다.
- `depends_on`은 시작 순서만 보장한다. 준비까지 기다리려면 healthcheck.
- 명령: `docker compose up -d`, `down`, `logs`.

### 2-4. 실행 구성 (풀스택)

```
브라우저 → Nginx → Next.js → Spring Boot → PostgreSQL     (모두 Compose 네트워크 안)
```

## 3. 자주 헷갈리는 것

- **Dockerfile vs Compose 파일:** Dockerfile은 컴퓨터(이미지)를 만드는 요리법, Compose는 네트워크에 어떤 컨테이너를 어떻게 띄울지 정한다.
- **`ports`와 `volumes`:** 오른쪽이 컨테이너, 왼쪽이 바깥. 충돌을 신경 쓸 곳은 왼쪽.
- **컨테이너는 격리된 네트워크**라서 포트를 열어야 밖에서 접근된다.
- 공용 서버에서는 팀별로 볼륨과 포트를 나눠야 충돌하지 않는다.

## 4. 이 카테고리의 실습, 오답노트, 참고자료

- 실습: WSL Ubuntu에 도커 설치, 컨테이너 라이프사이클과 내부 구조, 팀 공용 PostgreSQL 개발 DB, 멀티 컨테이너 풀스택 환경(Docker Compose 완성)
- 오답노트: Docker Compose, Dockerfile 멀티 스테이지 빌드
- 참고자료: 배포를 위한 경량 가상화, 유니온 파일 시스템(OverlayFS), Java 21 스프링 부트 앱의 도커 이미지 배포, 도커 컴포즈로 스프링 부트와 PostgreSQL 구동, Nginx·Next.js·Spring Boot·PostgreSQL 컴포즈 구축기, CI/CD와 테스트 서버 배포
