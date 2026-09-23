---
tags: [리눅스, WSL, VSCode, Java, 개발환경]
---

> 🔗 관련 노트: [[006_컴퓨터와 리눅스의 역사]] · [[007_플랫폼 개념과 Java 기초 문법]] · [[001_리눅스 파일 시스템 실습]]

# WSL2 기반 VSCode 개발 환경 구축 및 자바 프로젝트 실습

## 1. 가상머신이란 무엇인가

가상머신(Virtual Machine, VM)은 물리적 컴퓨터(호스트) 위에 소프트웨어적으로 또 다른 컴퓨터(게스트)를 만들어 실행하는 기술입니다.

가상머신을 구현하기 위해서 물리 하드웨어와 가상 머신을 연결해 주는 중간 관리자 역할을 하는 특수한 소프트웨어가 사용되는데 그런 소프트웨어를 하이퍼바이저(Hypervisor)라고 합니다.

Microsoft는 Hyper-V 기반의 경량 가상머신 환경(Hypervisor)을 가지고 있으며 그것을 이용해서 리눅스를 사용할 수 있는 Windows Subsystem for Linux 2(WSL 2)를 제공하고 있습니다.

기존 WSL 1이 Windows 커널을 흉내 냈다면, WSL 2는 실제 Linux 커널을 Hyper-V 가상머신에서 실행하여 호환성과 성능을 높였습니다.

```
물리적 PC (Windows 11)
  └─ 설치됨 → Hyper-V (하이퍼바이저)
                └─ 실행 중 → WSL 2 (가상 머신)
                                └─ 기반 → Linux Kernel (Ubuntu 24.04)
```

## 2. 네트워크 기초

WSL 2는 독립된 가상 머신이기 때문에, Windows(호스트)와 WSL(게스트) 사이에는 네트워크가 필요합니다.

- **IP 주소**: 네트워크에서 각 기기를 식별하는 고유한 번호입니다.
- **서브넷(Subnet)**: IP 주소를 논리적으로 묶어 놓은 그룹입니다. 같은 서브넷에 있는 기기들은 서로 직접 통신할 수 있습니다.
- **라우팅(Routing)**: 데이터가 목적지까지 가는 경로를 결정하는 과정입니다.
- **호스트와 게스트의 연결 구조**: Windows와 WSL 2는 내부적으로 브리지(Bridge) 또는 NAT(네트워크 주소 변환) 방식을 통해 연결됩니다. Windows에서는 `vEthernet (WSL 2)`라는 가상 네트워크 어댑터가 생성되며, 이를 통해 Windows와 WSL VM이 같은 네트워크 환경에서 통신합니다.

```
Windows Host                    WSL 2 VM
Windows App                     Linux App
    ↕                               ↕
vEthernet (WSL 2) Adapter  ↔  eth0 Interface
```

## 3. WSL 설치

Windows 11에서 WSL 2를 설치하는 과정입니다.

1. **가상화 활성화 확인**: BIOS에서 CPU 가상화(Intel VT-x 또는 AMD-V)가 켜져 있는지 확인합니다.
2. **관리자 권한으로 PowerShell 실행**:

   ```
   wsl --install
   ```

3. **재부팅**: 설치 후 시스템 재부팅이 필요합니다.
4. **초기 설정**: 재부팅 후 자동으로 Ubuntu 24.04가 실행되며, UNIX 사용자 계정과 비밀번호를 설정합니다.
5. **설치 확인**:

   ```
   wsl --list --verbose
   ```

   VERSION 컬럼에 `2`가 표시되면 WSL 2로 설치된 것입니다.

## 4. WSL 접속과 네트워크 구조

`wsl` 명령어를 입력하면 Windows 콘솔에서 Ubuntu 셸로 전환됩니다. 이는 단순히 명령어 해석기가 바뀌는 것이 아니라, Hyper-V 가상 머신에 로그인하는 것과 동일한 원리입니다.

- **vEthernet (WSL 2)**: Windows의 '네트워크 연결'에서 볼 수 있는 가상 어댑터입니다. 이 어댑터가 없으면 WSL 2가 정상적으로 네트워크를 사용할 수 없습니다.
- **통신 방식**: Windows의 `localhost`와 WSL의 `localhost`는 서로 다릅니다. WSL에서 Windows의 서비스를 호출하려면 WSL의 IP 주소나 `localhost`를 사용해야 하며, Windows에서 WSL의 서비스를 호출하려면 WSL의 IP 주소를 사용해야 합니다. (WSL 2는 기본적으로 NAT 모드이므로, 포트 포워딩 설정이 필요할 수 있습니다.)

## 5. WSL에 JDK 설치

WSL(Ubuntu) 환경에 Java 개발 키트를 설치합니다.

```bash
# 패키지 목록 업데이트
sudo apt update

# OpenJDK 17 (또는 최신 LTS 버전) 설치
sudo apt install openjdk-17-jdk -y

# 설치 확인
java -version
javac -version
```

**주의**: Windows에 설치된 JDK와 WSL에 설치된 JDK는 별개입니다. WSL 터미널에서 `java`를 실행하면 WSL 내부의 JDK가 사용됩니다.

## 6. VSCode에서 WSL 연결

VSCode를 사용하여 WSL 내부의 파일을 편집하고 터미널을 사용하는 방법을 설정합니다.

1. **Remote - WSL 확장 설치**: VSCode에서 `Ctrl+Shift+X`로 확장 프로그램 마켓플레이스를 엽니다. `Remote - WSL`을 검색하여 설치합니다.
2. **WSL 터미널에서 VSCode 실행**: WSL 터미널(Ubuntu)을 엽니다. 원하는 작업 디렉토리로 이동합니다.

   ```bash
   mkdir -p ~/java-project && cd ~/java-project
   ```

   `code .` 명령어를 실행합니다.

   ```bash
   code .
   ```

VSCode가 열리며, 상태바 왼쪽에 `(WSL: Ubuntu-24.04)`와 같은 텍스트가 표시되어야 합니다. 이는 VSCode가 WSL 환경에서 실행되고 있음을 의미합니다.

## 7. 간단한 자바 프로젝트 생성

WSL 파일시스템(`/home/username/java-project`)에서 자바 프로젝트를 생성하고 실행합니다.

1. **소스 파일 생성**: VSCode에서 `Main.java` 파일을 생성하고 아래 코드를 입력합니다.

   ```java
   public class Main {
       public static void main(String[] args) {
           System.out.println("Hello, WSL 2 & VSCode!");
           System.out.println("Java Version: " + System.getProperty("java.version"));
       }
   }
   ```

2. **컴파일**: VSCode의 터미널(`Ctrl+~`)에서 다음 명령어를 실행합니다.

   ```bash
   javac Main.java
   ```

   `Main.class` 파일이 생성됩니다.

3. **실행**:

   ```bash
   java Main
   ```

   콘솔에 "Hello, WSL 2 & VSCode!"와 Java 버전 정보가 출력됩니다.

## 8. 마무리 및 체크포인트

**파일시스템 차이 주의**:

- WSL 파일시스템: `/home/username/...` (Linux 경로)
- Windows에서 접근: `\\wsl$\Ubuntu-24.04\home\username\...`
- Windows 파일시스템: `C:\Users\username\...`
- WSL에서 접근: `/mnt/c/Users/username/...`

**권장**: 성능과 파일 권한 문제를 피하기 위해, 자바 프로젝트는 반드시 WSL 파일시스템(`/home/...`)에 생성하고, VSCode를 WSL 모드로 연결해 작업하세요. Windows 파일시스템(`/mnt/c/...`)에서 빌드 도구를 실행하면 파일 시스템 오버헤드로 인해 성능이 저하될 수 있습니다.
