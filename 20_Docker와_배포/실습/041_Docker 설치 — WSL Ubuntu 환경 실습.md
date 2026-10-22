---
tags: [Docker, WSL, Ubuntu, 설치, 실습]
---

> 🔗 관련 노트: [[077_도커란 무엇인가 — 가상 머신과의 차이, 이미지·컨테이너·엔진]] · [[021_Docker — 배포를 위한 경량 가상화 참고자료]]

# Docker 설치 — WSL Ubuntu 환경 실습

**대상**: 컨테이너와 이미지의 개념은 알지만, 도커를 아직 설치해 본 적 없는 사람

**목표**: WSL(Ubuntu) 환경에 Docker를 설치하고 `docker --version`으로 정상 설치를 확인한다

**완성물**: 터미널에 `docker --version`을 입력했을 때 `Docker version 2x.x.x`가 출력되는 상태

이 실습은 설치만 한다. 컨테이너 실행(`docker run`)은 다음 단계에서 다룬다.

도커는 리눅스 네이티브라서 윈도우에서는 가상 환경(리눅스 가상 컴퓨터 또는 WSL)이 필요하다. 여기서는 WSL 위의 Ubuntu에 직접 설치하는 방법을 쓴다. WSL 환경도 Ubuntu 기반이므로 일반 Ubuntu 설치 절차와 명령어가 동일하게 적용된다.

Ubuntu에서는 `apt`로도 설치할 수 있지만 기본 저장소의 Docker 버전이 오래된 경우가 많아, Docker 공식 저장소를 추가하고 최신 버전을 설치하는 방법을 권장한다.

## 1. 기존 Docker 패키지 제거

이미 설치된 Docker가 있으면 충돌을 방지하기 위해 제거한다.

```bash
sudo apt-get remove docker docker-engine docker.io containerd runc
```

## 2. 필수 패키지 설치

Docker 저장소와 GPG 키를 처리하는 데 필요한 도구들을 설치한다. `ca-certificates`는 HTTPS 통신 시 서버 인증서를 검증하는 데 필요하며, `curl`은 네트워크에서 파일을 내려받거나 API를 호출할 때 사용한다. `gnupg`는 GPG 키를 등록하고 서명을 검증하는 데 필요한 도구다.

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
```

## 3. Docker GPG 키 추가

Docker 공식 저장소에서 내려받은 패키지의 진위를 확인하기 위해 GPG 키를 등록한다. `keyrings` 디렉토리를 만들고, Docker GPG 키를 내려받아 `dearmor` 변환 후 권한을 설정한다.

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

## 4. Docker 저장소 추가

아래 명령을 실행하면 시스템의 아키텍처(`arch`)와 Ubuntu 버전 코드명(`VERSION_CODENAME`)을 자동으로 감지하여 Docker 공식 저장소 정보를 `/etc/apt/sources.list.d/docker.list` 파일에 등록한다. `signed-by` 옵션은 3단계에서 등록한 GPG 키를 참조하여 패키지의 서명을 검증하도록 지정하며, `sudo tee`를 사용해 루트 권한으로 파일을 생성하고 출력은 `/dev/null`로 버린다.

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

## 5. Docker CE 설치

저장소 정보를 갱신한 뒤, Docker Engine과 관련 도구를 설치한다. `docker-ce`는 컨테이너 엔진의 본체이며, `docker-ce-cli`는 터미널에서 `docker` 명령을 사용할 수 있게 해주는 클라이언트다. `containerd.io`는 컨테이너를 실제로 실행하는 런타임이며, `docker-buildx-plugin`은 이미지 빌드 기능을 확장하고, `docker-compose-plugin`은 `docker compose` 명령을 통해 여러 컨테이너를 정의하고 관리할 수 있게 한다.

```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 6. 버전 확인

```bash
docker --version
```

**✅ 확인**: 터미널에 `Docker version 27.x.x, build xxxxxxx`가 출력된다.

**🎓 코멘트**: Linux는 Docker Engine이 네이티브로 동작하므로 가상 머신이 필요 없다. 성능이 가장 빠르고 리소스 사용량이 적다. `docker-ce`는 Community Edition으로 무료다. `docker-ce-cli`는 명령어, `containerd.io`는 컨테이너 런타임이다. 다음에 `docker run`을 할 때 permission denied 에러가 나면 `sudo`를 붙이거나 현재 사용자를 docker 그룹에 추가해야 한다.

**❌ 자주 하는 실수**

| 증상 | 원인 | 해결 |
|---|---|---|
| `E: The repository ... does not have Release file` | 저장소 URL 에러 또는 네트워크 문제 | 4단계의 `echo` 명령을 다시 실행하고 `sudo apt-get update` |
| `permission denied while trying to connect to Docker daemon` | 현재 사용자가 docker 그룹에 없음 | `sudo usermod -aG docker $USER` 후 로그아웃/로그인 |
| `docker: command not found` | PATH 문제 | `sudo apt-get install -y docker-ce-cli` 재실행 |

**📝 핵심**: WSL의 Ubuntu는 일반 Ubuntu와 동일하게 Docker 공식 저장소를 추가하고 `docker-ce`를 설치해야 최신 버전을 받을 수 있다. Linux(WSL 포함)는 가상 머신 없이 네이티브로 컨테이너를 실행한다.
