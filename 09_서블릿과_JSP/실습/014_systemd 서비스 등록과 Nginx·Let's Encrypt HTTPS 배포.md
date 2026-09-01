---
tags: [리눅스, systemd, nginx, 리버스프록시, HTTPS, LetsEncrypt, certbot, 배포]
---

> 🔗 관련 노트: [[002_Nginx 리버스 프록시로 80번 포트 서비스하기]] · [[012_servlet 실습 — 서블릿·JSP·리포지토리·JDBC 연동]]

# systemd 서비스 등록과 Nginx·Let's Encrypt HTTPS 배포

`mvn exec:java`로 직접 띄운 서비스를 systemd에 등록해 데몬화하고, Nginx 리버스 프록시와 Let's Encrypt로 도메인·HTTPS까지 붙이는 배포 실습. 도메인 예시는 `jy.example.com`으로 표기한다.

## 1. systemd로 데몬화하는 이유

- `&`로 백그라운드 실행하면 터미널 세션이 끊기는 순간(SSH 접속 종료 등) 프로세스가 함께 죽을 위험이 있고, 서버가 재부팅되면 수동으로 다시 실행해야 한다.
- systemd는 우분투의 표준 서비스 관리자다. 여기에 서비스로 등록하면 **터미널을 닫아도 계속 떠 있고, 서버가 재부팅돼도 자동으로 다시 시작**된다.

## 2. 서비스 등록 사전 정보 확인

```bash
which mvn        # mvn 실행 파일의 절대 경로 확인(보통 /usr/bin/mvn)
whoami           # 현재 로그인된 사용자 계정명 확인
echo $HOME       # 홈 디렉터리 경로 확인
```

- systemd 유닛 파일에는 실행 파일 경로·계정·작업 디렉터리를 **절대 경로로 정확히** 적어야 하므로, 서비스 파일을 쓰기 전에 이 세 값을 먼저 확인해둔다.

## 3. systemd 유닛 파일 작성

```bash
sudo nano /etc/systemd/system/webapp.service
```

- `/etc/systemd/system/` 아래에 `.service` 확장자로 파일을 만들면 systemd가 이를 서비스 유닛으로 인식한다.
- 여러 사람이 같은 서버(또는 같은 실습 환경)를 공유하는 상황이라면 서비스 이름이 겹치지 않도록 `webapp-본인아이디.service`처럼 구분해서 만든다.

```ini
[Unit]
Description=NCafe Embedded Tomcat Web Application
After=network.target

[Service]
Type=simple
User=본인계정
WorkingDirectory=/home/본인계정/www/my-webapp
ExecStart=/usr/bin/mvn exec:java -Dexec.mainClass="com.example.App" -Dexec.arguments="5001"
Restart=always
RestartSec=10
StandardOutput=append:/home/본인계정/www/my-webapp/app.log
StandardError=append:/home/본인계정/www/my-webapp/app.log

[Install]
WantedBy=multi-user.target
```

각 지시어의 의미:

- **`After=network.target`**: 네트워크가 붙은 뒤에 이 서비스를 시작하라는 뜻이다. 서버 앱은 대부분 네트워크가 있어야 의미가 있으므로 붙여준다.
- **`Type=simple`**: `ExecStart`로 지정한 프로세스가 곧 서비스 본체라는 뜻이다. 별도로 데몬화(fork)하지 않는 일반적인 실행형 프로세스에 쓰는 기본 타입이다.
- **`User=본인계정`**: 이 서비스를 어떤 계정 권한으로 실행할지 지정한다. `root`가 아니라 실제 파일 소유자 계정으로 지정해야 프로젝트 디렉터리 접근 권한 문제가 없다.
- **`WorkingDirectory`**: `ExecStart` 명령이 실행될 때의 현재 작업 디렉터리다. Maven 프로젝트 루트(`pom.xml`이 있는 위치)를 지정해야 `mvn` 명령이 제대로 동작한다.
- **`ExecStart`**: 실제로 실행할 명령이다. `mvn exec:java`로 `com.example.App`의 `main()`을 실행하면서, `-Dexec.arguments="5001"`로 포트 번호를 인자로 넘긴다.
- **`Restart=always` / `RestartSec=10`**: 프로세스가 어떤 이유로든 죽으면 10초 뒤 자동으로 재시작한다. 서버 프로세스가 예외로 죽어도 서비스가 끊기지 않게 해주는 핵심 설정이다.
- **`StandardOutput` / `StandardError`**: 표준 출력·에러를 각각 지정한 로그 파일에 **append(이어쓰기)** 방식으로 저장한다. `journalctl`로도 볼 수 있지만, 별도 파일로 남기면 `tail -f`로 실시간 확인하기 편하다.
- **`WantedBy=multi-user.target`**: 시스템이 멀티유저 모드(일반적인 서버 부팅 상태)로 올라올 때 이 서비스가 함께 시작되도록 등록하는 타깃이다. `enable` 했을 때 이 타깃에 연결된다.

## 4. 서비스 등록 및 실행

```bash
sudo systemctl daemon-reload    # 새로 추가/수정한 유닛 파일을 systemd가 다시 읽도록 함
sudo systemctl enable webapp.service   # 부팅 시 자동 시작되도록 등록
sudo systemctl start webapp.service    # 서비스 즉시 시작
```

- `daemon-reload`는 유닛 파일을 새로 만들거나 수정할 때마다 실행해줘야 한다 — systemd는 유닛 파일을 처음 읽은 뒤 캐시해두기 때문에, 파일을 고쳐도 `daemon-reload` 없이는 변경사항이 반영되지 않는다.
- `enable`과 `start`는 별개다. `enable`은 "부팅 시 자동 시작"만 예약하는 것이고, 지금 당장 띄우려면 `start`를 따로 해줘야 한다.

## 5. 상태 및 로그 확인

```bash
sudo systemctl status webapp.service   # active (running) 상태인지 확인
tail -f ~/www/my-webapp/app.log   # 유닛 파일에 지정한 로그 파일 실시간 확인
sudo journalctl -u webapp.service -f   # systemd 저널을 통한 실시간 로그 확인(대안)
```

## 6. 서비스 관리 명령 요약

| 작업 | 명령어 |
|---|---|
| 시작 | `sudo systemctl start webapp.service` |
| 중지 | `sudo systemctl stop webapp.service` |
| 재시작 | `sudo systemctl restart webapp.service` |
| 상태 확인 | `sudo systemctl status webapp.service` |
| 자동 시작 비활성화 | `sudo systemctl disable webapp.service` |

## 7. Nginx 리버스 프록시 — 포트 번호 없이 서비스하기

지금까지는 `http://jy.example.com:5001`처럼 **포트 번호를 붙여야만** 접속할 수 있었다. Nginx를 앞단에 두면 포트 없이 도메인만으로 접속할 수 있고, HTTPS까지 붙일 수 있다.

- **리버스 프록시**: 외부 요청을 가장 먼저 받는 서버(Nginx)가, 내부에서 실제로 동작 중인 애플리케이션(`localhost:5001`)으로 요청을 대신 전달해주는 방식이다. 자바 서블릿 코드나 톰캣 설정을 건드리지 않고도 HTTPS·포트 포워딩·로드 밸런싱을 앞단에서 적용할 수 있다.
- **Let's Encrypt**: 무료로 공인 SSL 인증서를 발급해주는 비영리 인증 기관(CA)이다. 예전에는 도메인 하나당 유료로 인증서를 사야 했지만(서브도메인을 여러 개 쓰면 그만큼 비용이 늘어서, 기업은 보통 와일드카드 인증서를 산다), Let's Encrypt 등장 이후로는 무료로 발급받을 수 있다.
- **Certbot**: Let's Encrypt 인증서의 발급·Nginx 설정 연동·주기적 갱신을 자동으로 처리해주는 공식 CLI 도구다.

**요청 흐름**:

```
[브라우저] --(HTTPS, 443)--> [Nginx] --(내부 HTTP)--> [톰캣 서비스, localhost:5001]
```

Nginx가 443 포트에서 SSL 인증서로 복호화한 뒤, 내부적으로는 평범한 HTTP로 톰캣(5001)에 요청을 넘겨준다.

## 8. Nginx 설정 파일 작성

```bash
sudo nano /etc/nginx/sites-available/jy.example.com.conf
```

- 파일명은 보통 **본인이 부여받은 도메인명**으로 짓는다(예: `jy.example.com.conf`). 여러 사람이 같은 서버를 쓰는 경우 파일명이 도메인과 일치해야 어떤 설정이 어떤 서비스인지 헷갈리지 않는다.

```nginx
server {
    listen 80;
    server_name jy.example.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

- **`listen 80`**: 아직 HTTPS 설정 전이므로 일반 HTTP 포트만 연다.
- **`server_name`**: 이 서버 블록이 어떤 도메인으로 들어온 요청을 처리할지 지정한다. Nginx는 이 값을 보고 여러 도메인(가상 호스트) 중 어느 설정을 적용할지 결정한다.
- **`proxy_pass`**: 실제 요청을 넘길 내부 주소다. 톰캣이 5001 포트로 떠 있으므로 `http://127.0.0.1:5001`로 넘긴다.
- **`proxy_set_header`** 4줄: 클라이언트의 실제 IP·원래 요청 정보를 톰캣(서블릿 컨테이너)에게 그대로 전달하기 위한 헤더들이다. Nginx를 거치면 톰캣 입장에서는 모든 요청이 "Nginx가 보낸 요청"처럼 보이는데, 이 헤더들이 없으면 실제 클라이언트 IP·원래 프로토콜(http/https) 정보를 잃어버린다.

## 9. 설정 활성화 — `sites-enabled` 심볼릭 링크

`sites-available`에 설정 파일을 만드는 것만으로는 적용되지 않는다. `sites-enabled` 디렉터리에 **심볼릭 링크**를 만들어야 Nginx가 실제로 그 설정을 사용한다 — 링크가 없으면 "설정은 있지만 적용은 하지 마라"는 뜻으로 취급된다.

```bash
sudo ln -s /etc/nginx/sites-available/jy.example.com.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
# 기본 디폴트 설정과의 충돌 방지
sudo nginx -t
# 문법 오류 없는지 검사("syntax is ok" 확인)
sudo systemctl reload nginx
```

- `nginx -t`는 설정을 실제로 적용하기 전에 문법 오류를 미리 잡아주는 검사 단계다. 이 단계를 건너뛰고 바로 반영하면, 오타 하나로 Nginx 전체가 죽어버릴 수 있다.
- 같은 서버를 다른 사람들과 함께 쓰는 환경이라면 `restart` 대신 `reload`를 쓰는 게 안전하다 — `restart`는 nginx 프로세스를 완전히 껐다 켜서 그 순간 다른 사람의 연결까지 끊길 수 있지만, `reload`는 기존 연결을 유지한 채 새 설정만 반영한다.

## 10. Certbot으로 SSL 인증서 발급 및 HTTPS 자동 구성

```bash
sudo certbot --nginx -d jy.example.com
```

- `--nginx` 플러그인은 Nginx 설정 파일을 직접 읽고 **자동으로 수정**한다 — `listen 443 ssl;`과 인증서 경로(`ssl_certificate` 등)를 기존 `server` 블록에 추가하고, HTTP(80) 요청을 HTTPS로 리다이렉트하는 블록도 새로 만들어준다.
- 그 도메인에 **처음으로** 인증서를 발급하는 경우 아래 순서로 콘솔 입력을 요구한다.
  1. **이메일 주소 입력**: 인증서 만료 경고·비상 알림을 받을 이메일.
  2. **이용 약관 동의**: `Y` 입력.
  3. **이메일 정보 공유 여부**: `N`(또는 `Y`) 선택 — Let's Encrypt 재단의 뉴스레터 수신 여부다.
  4. **HTTPS 리다이렉트 여부**: HTTP로 접속했을 때 자동으로 HTTPS로 전환할지 묻는다 — 보통 `2`(Redirect)를 선택한다.
- 다만 이 네 가지 질문은 **Let's Encrypt 계정 등록(이메일·약관 동의)이 서버 단위로 이미 끝나 있거나, 그 도메인에 인증서가 이미 존재하는 경우**에는 건너뛴다. 이미 인증서가 있으면 대신 "1: 기존 인증서 재설치 / 2: 갱신 및 재발급" 중 하나를 고르라는 프롬프트가 뜬다.

## 11. 인증서 자동 갱신 검증

Let's Encrypt 인증서의 유효 기간은 90일이고, certbot이 systemd 타이머로 백그라운드에서 자동 갱신을 수행한다. 실제로 만료되기 전에 갱신이 잘 되는지 **모의 실행(dry-run)**으로 미리 확인할 수 있다.

```bash
sudo certbot renew --dry-run
```

- `Congratulations, all simulated renewals succeeded` 메시지가 뜨면 자동 갱신 구성이 정상이라는 뜻이다.

## 12. 최종 접속 검증

```bash
sudo systemctl status webapp.service   # 내부 톰캣 서비스가 살아있는지
sudo systemctl status nginx           # Nginx가 살아있는지
```

- 브라우저에서 포트 번호 없이 `https://jy.example.com/admin/menus/list`처럼 접속해, 주소창에 자물쇠 아이콘(보안 연결)이 뜨고 페이지가 정상 렌더링되는지 확인한다.

## 13. certbot이 설정을 잘못 건드릴 때 — 리다이렉트 무한 루프

certbot `--nginx`가 기존 `listen 80` 블록에 `listen 443 ssl`을 추가하는 과정에서, 원래 80 전용으로 있어야 할 `if ($host = ...) { return 301 https://$host$request_uri; }` 리다이렉트 구문이 **443도 처리하는 블록에도 중복으로 남는 경우**가 있다.

- 이렇게 되면 443(HTTPS)으로 들어온 요청이 같은 블록의 리다이렉트 조건에 걸려 다시 `https://...`로 301을 내려보내고, 브라우저는 그 응답을 받아 또 같은 주소로 요청하는 식으로 **자기 자신에게 무한 리다이렉트**를 반복한다 — 브라우저에는 `ERR_TOO_MANY_REDIRECTS`로 나타난다.
- 확인 방법: `sudo nginx -T`로 전체 설정을 출력해, `listen 443 ssl`이 있는 블록 안에 불필요한 `if ($host = ...) return 301 https://...` 구문이 남아있는지 본다. 있다면 그 부분만 지우고(80 전용 블록에 있는 동일 구문은 그대로 둔다) `nginx -t`로 문법 확인 후 `reload`한다.
- `reload`는 `restart`와 달리 기존 연결을 끊지 않고 새 워커 프로세스로 무중단 전환하므로, 다른 사람이 접속 중이어도 안전하게 적용할 수 있다.
