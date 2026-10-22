---
tags: [Docker, 컨테이너, WSL, Ubuntu, 실습]
---

> 🔗 관련 노트: [[077_도커란 무엇인가 — 가상 머신과의 차이, 이미지·컨테이너·엔진]] · [[021_Docker — 배포를 위한 경량 가상화 참고자료]] · [[041_Docker 설치 — WSL Ubuntu 환경 실습]]

# Docker 실습 — 컨테이너 라이프사이클과 내부 구조 탐구

**대상**: Docker를 설치했고, 이미지와 컨테이너의 개념을 아는 사람

**목표**: 이미지 검색·조회부터 컨테이너 실행·내부 진입·종료·삭제까지 전체 라이프사이클을 명령어로 직접 경험하고, 컨테이너의 레이어 파일 시스템 구조를 이해한다

**완성물**: `my-ubuntu`라는 이름의 컨테이너를 실행해 내부에 진입·관찰한 뒤, 정상적으로 종료 및 삭제까지 마친 상태

## 1. 실습 준비: 이미지 탐색

도커를 설치한 후, 가장 먼저 할 일은 사용할 수 있는 이미지들을 확인하는 것이다. 도커 허브(Docker Hub)에는 수만 개의 공개 이미지가 존재한다.

**이미지 검색**

`docker search` 명령어를 사용하여 특정 키워드로 이미지를 검색할 수 있다.

```bash
# ubuntu 이미지가 있는지 검색
docker search ubuntu
```

> 참고: `permission denied while trying to connect to the docker API at unix:///var/run/docker.sock` 오류가 발생하면, 현재 사용자가 Docker 데몬에 접근할 수 있는 권한이 없다는 뜻이다. `sudo`를 붙여 실행하거나, 현재 사용자를 docker 그룹에 추가하여 권한을 부여해야 한다.
>
> ```bash
> sudo usermod -aG docker $USER
> ```
>
> 명령어 실행 후 권한이 적용되도록 터미널을 재시작하거나 `newgrp docker`를 실행해야 한다.

출력 결과에서 IMAGE NAME, DESCRIPTION, STARS, OFFICIAL 컬럼을 확인한다. OFFICIAL이 true인 이미지는 Docker 공식 인증 이미지이므로 신뢰도가 높다.

**이미지 정보 확인**

특정 이미지의 상세 정보(레이어 구조, 크기, 태그 등)를 확인하려면 `docker image inspect`를 사용할 수 있다.

```bash
# ubuntu:latest 이미지의 메타데이터 확인
docker image inspect ubuntu:latest
```

> 참고: `No such image: ubuntu:latest` 오류가 발생하면, 로컬에 해당 이미지가 존재하지 않는다는 뜻이다. `docker pull` 명령어로 이미지를 먼저 다운로드한 후 다시 실행해야 한다.
>
> ```bash
> docker pull ubuntu:latest
> ```

## 2. 컨테이너 실행 (Up)

이미지를 실제 실행 가능한 컨테이너로 만들기 위해 `docker run` 명령어를 사용한다.

`docker run` 명령어를 이용해서 `ubuntu:latest` 이미지를 다운로드 받고, 그것을 실행시켜서 생성된 컨테이너(도커 상의 가상 운영체제)에 이름을 `my-ubuntu`라고 부여하는 방법을 실습한다.

**기본 실행**

```bash
# ubuntu:latest 이미지를 기반으로 컨테이너를 생성 및 실행
# -it: 인터랙티브 모드(Terminal)와 표준 입력 연결
# --rm: 컨테이너가 종료되면 자동으로 삭제
# -d: 백그라운드(Detached)로 실행
# --name: 컨테이너에 "my-ubuntu"라는 이름을 부여하여 식별 및 관리 용이하게 함
docker run -it --rm -d --name my-ubuntu ubuntu:latest
```

- `--name`: 컨테이너에 고유한 이름을 지정한다. 도커는 기본적으로 랜덤한 해시 값을 컨테이너 ID로 사용하지만, `--name`을 통해 사람이 읽을 수 있는 이름(예: `my-ubuntu`)을 부여하면 `docker ps`, `docker exec`, `docker stop` 등 후속 명령어에서 컨테이너를 식별하고 관리하기 훨씬 쉬워진다.
- `-it`: `--interactive`와 `--tty`의 합성어. 터미널 세션을 유지하여 명령어를 입력할 수 있게 한다.
- `--rm`: 컨테이너가 종료된 후 자동으로 파일 시스템과 메타데이터를 삭제한다. 디스크 공간 절약에 유용하다.
- `-d`: 데몬(Daemon) 모드로 실행하여 터미널이 점유되지 않도록 한다.

**🎓 코멘트**: 컨테이너의 본질은 이미지(읽기 전용 레이어들의 스택)를 기반으로, 실행 시 생성되는 읽기/쓰기 레이어와 컨테이너 고유 메타데이터(설정, 네트워크, 볼륨 링크 등)를 결합하여 생성된 실행 가능한 인스턴스라는 것이다. 즉, 이미지는 "레시피"라면, 컨테이너는 그 레시피로 만든 "음식"에 해당한다.

**실행 중 컨테이너 확인**

```bash
# 현재 실행 중인 컨테이너 목록
docker ps

# 종료된 컨테이너까지 포함하여 전체 목록
docker ps -a
```

## 3. 컨테이너 내부 진입 (Exec)

실행 중인 컨테이너(도커 이미지를 실행한 가상의 운영체제: ubuntu linux)의 셸(Shell)에 진입하여 내부 환경을 직접 확인해 볼 수 있다. 이는 컨테이너 내부의 파일 시스템 구조나 설치된 패키지를 확인하는 데 필수적이다.

```bash
# 컨테이너 ID 또는 이름(my-ubuntu)을 지정하여 bash 셸 진입
docker exec -it my-ubuntu /bin/bash
```

- `-it`: 인터랙티브 터미널 세션 생성.
- `/bin/bash`: 진입할 셸 프로그램. Ubuntu 계열은 `/bin/bash`, Alpine 계열은 `/bin/sh`를 사용한다.

**컨테이너 내부에서의 관찰**

진입 후 다음 명령어들을 실행해 본다.

```bash
# 컨테이너 내부의 프로세스 목록 (호스트 OS의 프로세스는 보이지 않음)
ps aux

# 컨테이너 내부의 파일 시스템 루트 확인
ls -la /

# 컨테이너 내부의 호스트 이름 확인 (호스트와 다름)
hostname
```

**핵심 관찰**: 컨테이너 내부에서는 호스트 OS의 파일 시스템이나 프로세스가 보이지 않는다. 이는 네임스페이스(Namespace)에 의해 시야가 격리되어 있기 때문이다.

관찰이 끝났다면, 컨테이너 셸에서 `exit` 명령어를 입력하여 컨테이너 내부에서 빠져나와야 한다.

```bash
# 컨테이너 셸 종료
root@4992abc0786a:/# hostname
4992abc0786a
root@4992abc0786a:/# exit
newlec@book2pro360:~$
```

## 4. 컨테이너 종료 및 삭제 (Down)

실습이 끝난 후 컨테이너를 정리해야 한다.

**컨테이너 종료**

```bash
# 컨테이너를 정상 종료 (SIGTERM 신호 전송)
docker stop my-ubuntu

# 강제 종료 (SIGKILL 신호 전송, stop으로 안 될 때 사용)
docker kill my-ubuntu
```

- `docker stop`은 컨테이너에 SIGTERM 신호를 보내어 프로세스가 정상적으로 종료되도록 요청한다.
- `docker kill`은 SIGKILL 신호를 보내어 즉시 프로세스를 강제 종료시킨다.

종료 후 컨테이너의 상태가 Exited로 변경되었는지 확인해 볼 수 있다.

```bash
# 컨테이너 상태 확인 (STATUS 컬럼이 Exited로 표시되어야 함)
docker ps -a
```

**컨테이너 삭제**

```bash
# 종료된 컨테이너 삭제
docker rm my-ubuntu

# 모든 종료된 컨테이너 일괄 삭제
docker container prune
```

> 참고: 여기서 말하는 "종료된 컨테이너"는 프로세스가 더 이상 실행되지 않는 상태(Exited)를 의미한다. 컨테이너는 프로세스가 실행되는 상태(Up)일 때는 삭제할 수 없으며, 반드시 `docker stop` 등으로 프로세스를 종료한 후에야 `docker rm`으로 삭제할 수 있다.

**`docker stop`과 `docker rm`의 차이**

- `docker stop`: 컨테이너 내부의 프로세스를 종료하여 컨테이너의 상태를 Exited로 변경한다. 컨테이너의 메타데이터(설정, 이름, 볼륨 링크 등)와 읽기/쓰기 레이어는 디스크에 그대로 남아있어, 이후 `docker start`로 다시 실행할 수 있다.
- `docker rm`: `docker stop`으로 종료된 컨테이너의 메타데이터와 읽기/쓰기 레이어를 디스크에서 영구적으로 제거하는 작업이다. 이 명령어는 이미지가 아닌, 특정 컨테이너 인스턴스 자체를 삭제하는 것이다. 이미지는 `docker rmi` 명령어로 별도로 관리되며, 컨테이너 삭제 시 이미지는 삭제되지 않는다.
- `--rm` 옵션을 지정하여 실행한 컨테이너는 `docker stop` 후 자동으로 삭제되므로 `docker rm`이 필요 없다.
- `--rm` 없이 실행한 컨테이너는 `docker stop` 후에도 `docker ps -a`에 남아있으므로 `docker rm`으로 수동 삭제가 필요하다.

## 5. 이론: 컨테이너 파일 시스템과 레이어 구조

컨테이너가 실행될 때, 도커 데몬은 어떻게 파일 시스템을 구성하는지 이해하는 것이 중요하다.

**유니온 파일 시스템 (Union File System)**

도커 컨테이너의 파일 시스템은 유니온 파일 시스템(Union FS) 기반의 오버레이(Overlay) 파일 시스템을 사용한다.

- **읽기 전용 레이어 (Read-Only Layers)**: Dockerfile의 각 명령어(`RUN`, `COPY` 등)가 실행될 때마다 생성된 레이어다. 모든 컨테이너가 공유하며, 변경이 불가능하다. 예: `ubuntu:latest` 이미지의 OS 기본 파일, 설치된 라이브러리 등.
- **읽기/쓰기 레이어 (Read/Write Layer)**: 컨테이너가 실행될 때 생성되는 최상위 레이어다. 컨테이너 내부에서 파일을 생성, 수정, 삭제하는 모든 작업이 이 레이어에 기록된다. 컨테이너가 삭제되면 이 레이어도 함께 삭제된다.

**레이어 구조 예시**

```
[Read/Write Layer]  <- 컨테이너 실행 중 생성/수정되는 파일 (my-ubuntu 컨테이너 전용)
[Read-Only Layer 3] <- Dockerfile: RUN apt-get install -y nginx
[Read-Only Layer 2] <- Dockerfile: COPY app /app
[Read-Only Layer 1] <- Base Image: ubuntu:latest (OS 기본 파일)
```

- 읽기 요청: 가장 위 레이어부터 아래로 내려가며 파일을 찾는다.
- 쓰기 요청: 항상 최상위 Read/Write 레이어에 기록된다.
- 삭제 요청: 실제 파일은 삭제되지 않고, Read/Write 레이어에 "삭제됨"이라는 마커(Whiteout file)를 남긴다.

**왜 이렇게 설계되었는가?**

- 공유: 여러 컨테이너가 동일한 기반 이미지를 공유하므로 디스크 공간을 절약한다.
- 성능: 변경 사항만 별도의 레이어에 기록하므로, 기반 이미지의 불변성(Immutability)을 유지하면서도 빠른 실행이 가능하다.

## 6. 마무리

- 명령어 흐름: `docker search` → `docker run` → `docker exec` → `docker stop` → `docker rm` 순서로 컨테이너의 생애주기를 관리할 수 있다.
- 격리의 실체: `docker exec`로 진입하여 내부 환경을 확인했을 때, 호스트와 분리된 독립적인 파일 시스템과 프로세스 공간을 경험할 수 있다.
- 파일 시스템 구조: 컨테이너의 파일 시스템은 읽기 전용 레이어와 읽기/쓰기 레이어가 오버레이된 유니온 파일 시스템으로 구성되어 있다.
