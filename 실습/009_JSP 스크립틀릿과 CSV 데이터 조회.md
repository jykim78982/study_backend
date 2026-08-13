---
tags: [JSP, 스크립틀릿, 서블릿, 실습]
날짜: 2026-08-13
---

> 🔗 관련 노트: [[034_웹 애플리케이션과 JSP]] · [[033_어노테이션 기반 매핑과 RTTI(리플렉션)]]

# JSP 스크립틀릿과 CSV 데이터 조회

[[034_웹 애플리케이션과 JSP]]에서 재스퍼(Jasper)가 `.jsp`를 서블릿으로 변환해준다는 걸 다뤘다. 이번 실습에서는 그 JSP 안에 자바 로직을 직접 끼워 넣어서, **DB 대신 CSV 파일에 저장된 메뉴 데이터를 자바 코드로 읽어와 화면에 출력**해본다.

## 1. 핵심 개념

- **스크립틀릿 `<% ... %>`**: JSP 안에서 자바 로직(파일 읽기, 파싱, 조건문, 반복문 등)을 수행하는 블록. 여기 들어간 코드는 브라우저에 그대로 출력되지 않는다.
- **표현식 `<%= ... %>`**: 자바 변수나 연산 결과를 HTML 위치에 직접 출력하는 블록. `out.print(...)`를 대신 써주는 것과 같다.
- **ClassLoader로 리소스 읽기**: `C:\...` 같은 절대 경로 대신, 실행 시점의 클래스패스를 기준으로 리소스 파일을 찾는 방법. 배포 환경이 달라져도(내 PC든 서버든) 항상 같은 방식으로 파일을 찾을 수 있다.

## 2. 전체 동작 흐름

브라우저가 `detail.jsp?id=1`을 요청했을 때 실제로 벌어지는 과정을 정리하면 다음과 같다.

```
[1. 브라우저] ---(URL: detail.jsp?id=1 요청)---> [2. 톰캣 서블릿 엔진]
                                                          │
[5. HTML 화면 출력] <--(변환된 HTML 응답)-- [4. JSP 스크립틀릿 실행] <──┘
                                                  │
                                       (ClassLoader로 파일 접근)
                                                  ▼
                                    [3. target/classes/data/menus.csv]
```

1. **요청 수신**: 브라우저가 `id=1`이라는 파라미터를 가지고 `detail.jsp`를 호출한다.
2. **JSP 변환 & 실행**: 톰캣 내부의 재스퍼가 `detail.jsp`를 서블릿 자바 파일(`_jsp.java`)로 변환하고 실행한다.
3. **데이터 읽기**: 자바의 `ClassLoader`를 통해 빌드 폴더에 위치한 `menus.csv`의 입력 스트림을 연다.
4. **파싱 및 객체화**: CSV를 한 줄씩 읽어 `id=1`인 데이터를 찾아 `Menu` 객체로 만든다.
5. **HTML 생성 및 응답**: `Menu` 객체에 담긴 정보(이름, 가격, 이미지 등)를 HTML 태그 사이에 채워 완성된 문서로 만든 뒤 브라우저에 돌려준다.

## 3. 디렉토리 구조

```
src/
└── main/
    ├── java/
    │   └── com/example/entity/
    │       └── Menu.java
    ├── resources/
    │   └── data/
    │       └── menus.csv
    └── webapp/
        └── admin/menus/
            ├── detail.jsp
            └── list.jsp
```

## 4. 왜 `src/main/resources/`에 CSV를 두는가

`src/main/java/`와 `src/main/resources/`는 Maven이 미리 정해둔(예약된) 디렉토리다. 굳이 다른 위치로 바꿀 이유가 없다.

- `src/main/java/*`: **컴파일해야 하는** 소스 코드. 저장되면 컴파일되어 `target/classes/*`로 이동한다.
- `src/main/resources/*`: **컴파일 대상이 아닌** 리소스 파일. 코드를 실행할 때 컴파일 없이 그대로 `target/classes/*`로 복사된다.

`menus.csv`는 자바 소스가 아니라 데이터 파일이므로, `src/main/java/`가 아니라 `src/main/resources/`에 둬야 올바르다. 빌드 전/후를 비교하면:

- 개발할 때(`src/`): `src/main/java/com/example/entity/Menu.java`, `src/main/resources/data/menus.csv`
- 빌드 후(`target/`): `target/classes/com/example/entity/Menu.class`(자바는 컴파일됨), `target/classes/data/menus.csv`(resources의 파일은 컴파일 없이 그대로 복사됨)

### 파일이 실제로 이동하는 경로

```
src/main/resources/data/menus.csv     ← 원본 (개발자가 편집하는 파일)
        ↓ mvn compile (resources 플러그인이 복사)
target/classes/data/menus.csv         ← 빌드 산출물
        ↓ App.java 의 addPreResources 로 마운트
/WEB-INF/classes/data/menus.csv       ← 톰캣이 보는 가상 경로
        ↓ WebappClassLoader 가 WEB-INF/classes 를 클래스패스 루트로 취급
"data/menus.csv"                      ← 코드에서 쓰는 이름
```

[[033_어노테이션 기반 매핑과 RTTI(리플렉션)]]에서 다룬 `App.java`의 `DirResourceSet` 매핑(`target/classes` → `/WEB-INF/classes`)이 여기서도 그대로 쓰인다.

### ClassLoader를 쓰는 이유 — 경로 독립성

코드에 `C:\Users\...\project\...`처럼 이 컴퓨터에만 있는 절대 경로를 박아넣으면, 프로젝트를 다른 컴퓨터나 리눅스 서버로 옮기는 순간 그 경로가 없어서 실행이 터진다. 하지만 아래처럼 쓰면:

```java
request.getServletContext().getClassLoader().getResourceAsStream("data/menus.csv")
```

톰캣이 실행되는 서버 환경의 **클래스패스 루트**(`target/classes/` 또는 `WEB-INF/classes/`)를 기준으로 파일을 찾는다. 컴퓨터 환경이 바뀌어도 `"data/menus.csv"`라는 상대 이름만으로 항상 같은 방식으로 파일 위치를 찾을 수 있다.

## 5. Menu 엔티티

`workspace2/maven_servlet_project/src/main/java/com/example/entity/Menu.java`

```java
package com.example.entity;

public class Menu {
    private int id;
    private String korName;
    private String engName;
    private String imgSrc;
    private String description;
    private String categoryName;
    private int price;

    public Menu() {
    }

    public Menu(int id, String korName, String engName, String imgSrc, String description, String categoryName,
            int price) {
        this.id = id;
        this.korName = korName;
        this.engName = engName;
        this.imgSrc = imgSrc;
        this.description = description;
        this.categoryName = categoryName;
        this.price = price;
    }

    // getter / setter 생략
}
```

CSV의 한 줄(`1,아메리카노,Americano,...`)을 파싱해서 이 `Menu` 객체 하나로 만드는 게 이번 실습의 핵심 작업이다.

## 6. I/O 스트림 3단계 체이닝

파일의 0과 1(바이트) 데이터를 사람이 읽을 수 있는 한 줄의 텍스트로 바꾸기 위해, 스트림 3개를 체인처럼 연결해서 쓴다.

```java
try (InputStream is = request.getServletContext().getClassLoader().getResourceAsStream("data/menus.csv");
     InputStreamReader isr = new InputStreamReader(is, StandardCharsets.UTF_8);
     BufferedReader reader = new BufferedReader(isr)) { ... }
```

**1단계 `InputStream` (바이트 스트림)**
`getResourceAsStream()`의 결과물. 컴퓨터가 다루는 가장 기본 단위인 바이트로 데이터를 읽는다. 이 단계에서는 한글이든 영문이든 전부 숫자(바이트)로만 보인다.

**2단계 `InputStreamReader` (문자 변환 스트림)**
바이트 → 문자(char)로 바꿔주는 다리 역할. `StandardCharsets.UTF_8`을 지정해서, 한글처럼 2~3바이트로 묶인 바이트 데이터를 깨지지 않는 정상적인 문자로 조립해준다.

**3단계 `BufferedReader` (보조 스트림 & 버퍼)**
문자를 한 글자씩 읽으면 느리다. 메모리 버퍼에 데이터를 큼직하게 담아두고, `readLine()`으로 "줄바꿈(`\n`)이 나올 때까지 한 줄을 한 번에 읽는" 기능을 제공한다. CSV는 줄 단위로 데이터가 나뉘므로 이 클래스가 필수적이다.

## 7. 상세 조회 — `detail.jsp`

`workspace2/maven_servlet_project/src/main/webapp/admin/menus/detail.jsp` (요청 파라미터로 넘어온 `id`에 해당하는 메뉴 하나만 찾는 실제 구현)

```jsp
<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ page import="java.io.InputStream"%>
<%@ page import="java.io.InputStreamReader"%>
<%@ page import="java.io.BufferedReader"%>
<%@ page import="java.nio.charset.StandardCharsets"%>
<%@ page import="com.example.entity.Menu"%>

<%
    String idParam = request.getParameter("id");
    int targetId = -1;
    if (idParam != null && !idParam.isEmpty()) {
        try {
            targetId = Integer.parseInt(idParam);
        } catch (NumberFormatException e) {
            targetId = -1;
        }
    }
    Menu menu = null;

    // 1. ClassLoader를 이용해 CSV 파일 읽기
    if (targetId != -1) {
        try (InputStream is = request.getServletContext().getClassLoader().getResourceAsStream("data/menus.csv")) {
            if (is != null) {
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
                    String line;
                    boolean isFirstLine = true;

                    while ((line = reader.readLine()) != null) {
                        if (isFirstLine) {
                            isFirstLine = false; // CSV 헤더(컬럼명) 건너뛰기
                            continue;
                        }

                        // 데이터 줄을 만나면 파싱
                        String[] tokens = line.split(",");
                        if (tokens.length >= 7) {
                            int id = Integer.parseInt(tokens[0].trim());

                            if (id == targetId) {
                                String korName = tokens[1].trim();
                                String engName = tokens[2].trim();
                                String imgSrc = tokens[3].trim();
                                String description = tokens[4].trim();
                                String categoryName = tokens[5].trim();
                                int price = Integer.parseInt(tokens[6].trim());

                                menu = new Menu(id, korName, engName, imgSrc, description, categoryName, price);
                                break; // 원하는 메뉴를 찾았으니 더 읽을 필요 없다
                            }
                        }
                    }
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
%>

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>메뉴 상세 정보</title>
</head>
<body>
    <h1>메뉴 상세 페이지 (기본)</h1>
    <hr>

    <% if (menu != null) { %>
        <div>
            <img src="<%= menu.getImgSrc() %>" alt="<%= menu.getKorName() %>" width="200"><br>
            <p><strong>ID:</strong> <%= menu.getId() %></p>
            <p><strong>한글명:</strong> <%= menu.getKorName() %></p>
            <p><strong>영문명:</strong> <%= menu.getEngName() %></p>
            <p><strong>카테고리:</strong> <%= menu.getCategoryName() %></p>
            <p><strong>가격:</strong> <%= menu.getPrice() %>원</p>
            <p><strong>설명:</strong> <%= menu.getDescription() %></p>
        </div>
    <% } else { %>
        <p>메뉴 데이터를 불러올 수 없습니다.</p>
    <% } %>
</body>
</html>
```

### ① 요청 파라미터 추출 및 안전한 정수 변환

```java
String idParam = request.getParameter("id"); // URL의 ?id=1 에서 "1"을 추출 (문자열 타입)
int targetId = -1; // 찾고자 하는 메뉴 ID (초기값 -1)

if (idParam != null && !idParam.isEmpty()) {
    try {
        targetId = Integer.parseInt(idParam); // "1" -> 숫자 1로 변환
    } catch (NumberFormatException e) {
        targetId = -1; // "abc" 같은 이상한 값이 들어오면 에러 방지를 위해 -1 유지
    }
}
```

`request.getParameter()`는 항상 문자열(String)로 값을 가져온다. 이걸 숫자 비교에 쓰려면 `Integer.parseInt()`로 `int`로 바꿔줘야 한다.

### ② CSV 파일 한 줄씩 읽기 및 헤더 스킵

```java
String line;
boolean isFirstLine = true; // 첫 줄 감지용 플래그

while ((line = reader.readLine()) != null) {
    if (isFirstLine) {
        isFirstLine = false; // 첫 줄을 읽었으니 플래그를 꺼줌
        continue; // 헤더("id,korName,engName...") 줄은 건너뛰고 다음 줄(진짜 데이터)로 이동
    }
    ...
```

CSV의 1번째 줄은 데이터가 아니라 컬럼명(`id,korName,engName...`)이다. 이걸 메뉴 데이터로 처리하면 에러가 나므로, `isFirstLine` 플래그로 첫 한 줄만 건너뛴다.

### ③ 데이터 분할(split) 및 일치하는 ID 탐색

```java
String[] tokens = line.split(","); // 쉼표 기준으로 쪼개서 배열로 만듦
if (tokens.length >= 7) {
    int id = Integer.parseInt(tokens[0].trim()); // 0번째 값(id)을 숫자로 변환 (공백 제거 trim)

    if (id == targetId) { // 찾던 메뉴 ID와 일치한다면!
        String korName = tokens[1].trim();
        // ... 이하 필드도 동일하게 추출

        menu = new Menu(id, korName, engName, imgSrc, description, categoryName, price);
        break; // 찾았으니 반복문(while)을 즉시 종료! 남은 데이터를 쓸데없이 안 읽는다
    }
}
```

- `split(",")`: `"1,아메리카노,Americano,..."` 문자열을 `,` 단위로 잘라 7개짜리 `String[]` 배열로 만든다.
- `trim()`: 데이터 앞뒤에 붙어 있을지 모르는 공백을 제거한다.
- `break`: 원하는 `id`를 찾았으면 파일 뒤쪽 줄을 더 읽을 필요가 없으므로 반복문을 종료해 성능을 아낀다.

### ④ 화면 출력(HTML 렌더링)

```jsp
<% if (menu != null) { %>
    <div>
        <img src="<%= menu.getImgSrc() %>" alt="<%= menu.getKorName() %>" width="200"><br>
        <p><strong>한글명:</strong> <%= menu.getKorName() %></p>
        <p><strong>가격:</strong> <%= menu.getPrice() %>원</p>
    </div>
<% } else { %>
    <p>메뉴 데이터를 불러올 수 없습니다.</p>
<% } %>
```

- `<% if (menu != null) { %>`: 메뉴를 정상적으로 찾았을 때만 HTML 태그들을 출력하도록 분기한다.
- `<%= menu.getKorName() %>`: 표현식 태그. `out.print(menu.getKorName())`으로 변환되어 서블릿 출력 스트림에 적히고, 브라우저는 그 자리에 값이 채워진 HTML을 받는다.

## 8. 목록 조회 — `list.jsp`, SSR과 CSR

`workspace2/maven_servlet_project/src/main/webapp/admin/menus/list.jsp`

```jsp
<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>메뉴 관리 - 카페 관리자</title>
<link rel="stylesheet" href="../../css/variables.css">
<link rel="stylesheet" href="list.css">
</head>
<body>
  <header class="admin-header">
    ...
  </header>

  <main class="container page">
    <section class="hero">
      ...
    </section>
    <div id="tabs" class="tabs"></div>
    <div id="menu-list" class="menu-grid"></div>
    <p id="empty-msg" class="empty-msg" style="display:none;">등록된 메뉴가 없습니다. "새 메뉴 등록"으로 추가해보세요.</p>
  </main>

  <script src="../../js/data.js"></script>
  <script src="../../js/utils.js"></script>
  <script src="list.js"></script>
</body>
</html>
```

실제 `list.jsp`는 스크립틀릿으로 메뉴를 반복 출력하지 않고, `<div id="menu-list">`를 비워둔 채 `list.js`(자바스크립트)가 브라우저에서 데이터를 채워 넣는 방식이다. 지시 블록(`<%@ page ... %>`) 한 줄만 추가된 걸 빼면 `list.html`과 거의 동일하다 — **정적 HTML을 그대로 재스퍼가 서블릿으로 변환할 수 있게 확장자만 `.jsp`로 바꾼 셈**이다. 이걸 계기로, 같은 목록 화면을 만드는 두 가지 접근을 비교해볼 수 있다.

### 방식 1) 스크립틀릿으로 직접 반복 출력 — SSR(Server Side Rendering)

`detail.jsp`와 같은 패턴을 반복문으로 확장해서, JSP 내부에서 CSV 전체를 읽고 `<tr>`을 직접 찍어낸다.

```jsp
<%
    Menu[] menus = new Menu[100];
    int count = 0;
    InputStream is = request.getServletContext().getClassLoader().getResourceAsStream("data/menus.csv");
    if (is != null) {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
            String line;
            boolean isFirstLine = true;
            while ((line = reader.readLine()) != null) {
                if (isFirstLine) { isFirstLine = false; continue; }
                String[] tokens = line.split(",");
                if (tokens.length >= 7) {
                    menus[count++] = new Menu(
                        Integer.parseInt(tokens[0].trim()), tokens[1].trim(), tokens[2].trim(),
                        tokens[3].trim(), tokens[4].trim(), tokens[5].trim(), Integer.parseInt(tokens[6].trim())
                    );
                }
            }
        } catch (Exception e) { e.printStackTrace(); }
    }
%>
...
<tbody>
  <% for (int i = 0; i < count; i++) { %>
    <tr>
      <td><a href="detail.jsp?id=<%= menus[i].getId() %>"><%= menus[i].getKorName() %></a></td>
      <td><%= menus[i].getCategoryName() %></td>
      <td><%= menus[i].getPrice() %>원</td>
    </tr>
  <% } %>
</tbody>
```

`<% for (...) { %>`로 반복문을 열고, 그 안에서 `<%= %>` 표현식으로 각 줄의 값을 출력한 뒤 `<% } %>`로 닫는다 — HTML 태그 사이사이에 자바 제어문이 그대로 끼어드는 게 스크립틀릿의 전형적인 모습이다.

- **장점**: 서버에서 이미 완성된 HTML을 넘겨주므로, 브라우저 화면이 처음부터 한 번에 나타난다.
- **단점**: HTML과 자바 코드가 뒤섞여서 코드가 지저분해지기 쉽다.

### 방식 2) 자바스크립트와 비동기 연동 — CSR(Client Side Rendering)

실습의 `list.jsp` 원본처럼, JSP 안에는 스크립틀릿 없이 `<div id="menu-list"></div>` 틀만 두고, `<script src="list.js"></script>`를 통해 브라우저(자바스크립트)가 데이터를 받아와 화면을 그리는 방식이다.

- **장점**: JSP는 깔끔한 HTML 구조만 유지하고, 데이터 렌더링은 클라이언트 스크립트가 맡아 역할 분담이 확실해진다.

## 9. 재스퍼가 실제로 변환한 결과 — `list_jsp.java`

톰캣이 `list.jsp`를 실행하면 `tomcat.8080/work/Tomcat/localhost/ROOT/org/apache/jsp/admin/menus/list_jsp.java`에 실제로 이런 서블릿 소스가 생성된다.

```java
// Jasper가 자동으로 만드는 변환 코드 (_jspService 메서드 내부)
public void _jspService(final HttpServletRequest request, final HttpServletResponse response)
    throws java.io.IOException, jakarta.servlet.ServletException {
    ...
    response.setContentType("text/html; charset=UTF-8");
    ...
    out.write("\r\n");
    out.write("<!DOCTYPE html>\r\n");
    out.write("<html lang=\"ko\">\r\n");
    out.write("<head>\r\n");
    out.write("<meta charset=\"UTF-8\">\r\n");
    out.write("<title>메뉴 관리 - 카페 관리자</title>\r\n");
    ...
}
```

- JSP 맨 위에 적었던 지시어(`<%@ page contentType="..." %>`)는 서블릿의 `response.setContentType(...)` 호출로 바뀌어 응답 헤더를 설정한다.
- 자바 코드가 아닌 일반 HTML 텍스트는 전부 `out.write("...")` 문장으로 포장되어, 브라우저에게 그대로 전달되는 문장이 된다.
- 우리가 적은 스크립틀릿(`<% %>`) 안의 코드만 `out.write()` 밖으로 빠져나와 진짜 자바 실행 로직으로 동작한다.

[[034_웹 애플리케이션과 JSP]]에서 다룬 것처럼, 이 변환 결과는 재스퍼가 대신 만들어주는 것이므로 사람이 직접 읽거나 수정할 필요가 없다 — 우리가 다루는 건 어디까지나 `.jsp` 원본 파일이다.

## 🔗 관련 노트

- [[034_웹 애플리케이션과 JSP]]
- [[033_어노테이션 기반 매핑과 RTTI(리플렉션)]]
