> 🔗 관련 노트: [[033_어노테이션 기반 매핑과 RTTI(리플렉션)]] · [[032_톰캣과 서블릿, 생명주기와 빌드 도구]]

# [실습 8] 인코딩과 Content-Type, 데이터 출력 방식

`maven_servlet_project`의 `step1` 패키지에 있는 예제들(`Ex1`~`Ex6`)로 진행한 실습. 서블릿이 브라우저에 응답을 돌려줄 때 **인코딩**과 **Content-Type**을 왜 명시해야 하는지, 그리고 데이터를 화면에 내보내는 대표적인 두 가지 방식(HTML / JSON)을 다룬다.

## 1. 한글이 `??????`로 깨지는 문제

인코딩 설정을 아무것도 하지 않은 채로 한글을 응답에 담아 보내면, 브라우저 화면에 `??????`처럼 깨져서 나온다.

**왜 이런 일이 생기는가**

- 서버가 응답을 보낼 때 **아무 힌트도 주지 않으면**, 브라우저는 자기 나름의 기본값으로 그 문서를 읽는다 — 한글 사용자 환경이라면 브라우저는 흔히 "이 문서는 EUC-KR이겠거니" 하고 읽어들인다
- 그런데 우리 서버 코드는 (버전에 따라 다르지만) 기본적으로 **UTF-8**로 인코딩해서 문자를 바이트로 바꿔 보낸다
- **보낸 쪽의 인코딩 방식과, 받는 쪽이 추정한 인코딩 방식이 서로 다르면** 글자가 깨진다

즉 해결책은 "브라우저야, 나는 이 문서를 UTF-8로 보내고 있어"라고 **명시적으로 알려주는 것**이다.

```java
resp.setContentType("text/html; charset=UTF-8");
```

`maven_servlet_project`의 `Ex1EncodingServlet`이 이 실험을 위한 서블릿이다.

```java
@WebServlet("/encoding")
public class Ex1EncodingServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        // [실습 A] 아래 인코딩 설정을 주석 처리한 상태로 먼저 실행해봅니다.
        resp.setContentType("text/html; charset=EUC-KR");

        PrintWriter out = resp.getWriter();

        // 1. print() vs println() (HTML 상에서는 줄바꿈을 위해 <br> 태그가 필요함)
        out.println("Hello ");
        out.println("Servlet! ");
        out.println("<br>");

        // 2. printf()를 통한 서식 지정 출력
        out.printf("국어: %d점, 평균: %.2f점<br>", 90, 88.6666);

        // 3. 한글 출력 검증
        out.println("한글 인코딩 테스트: 정상 출력 완료 <br>");

        out.println("줄바꿈 <br> 테스트");
    }
}
```

이 서블릿으로 세 가지 상태를 순서대로 비교해보면 인코딩 불일치의 정체가 뚜렷해진다.

1. `setContentType(...)` 자체를 주석 처리 — 아무 힌트도 없어서 브라우저가 임의로 추정 → 깨짐
2. `charset=EUC-KR`로 명시 — 우리는 실제로 UTF-8로 문자를 내보내고 있는데 "EUC-KR이다"라고 거짓 힌트를 줌 → 여전히 깨짐
3. `charset=UTF-8`로 명시 — 실제 인코딩과 알려준 힌트가 일치 → 정상 출력

## 2. 브라우저 개발자 도구로 응답 헤더 확인하기

브라우저 개발자 도구의 **네트워크(Network) 탭**을 열면, 내가 요청한 문서에 대한 **응답(Response)**과 그 **헤더(Header)** 정보를 확인할 수 있다. 헤더를 "Raw" 형태로 보면 `키: 값` 형식으로 나열된 걸 볼 수 있다.

이 헤더에는 이 문서가 언제 만들어졌는지, 크기는 얼마인지, HTTP 버전은 무엇인지, 연결은 어떻게 유지되는지, 캐시 유효기간은 얼마인지, 그리고 **어떤 방식으로 압축·인코딩되어 있는지**까지 담겨 있다.

- 인코딩 설정을 아예 안 했을 때: 응답 헤더에 문서 포맷이나 인코딩 정보가 **전혀 없다** — 그래서 브라우저가 자기 판단으로 기본값을 쓰게 된다
- `resp.setContentType("text/html; charset=UTF-8")`을 설정했을 때: 응답 헤더의 `Content-Type`에 `text/html; charset=UTF-8`이 실제로 찍히는 걸 확인할 수 있다

보낸 쪽(서버)과 받는 쪽(브라우저)이 이 헤더를 통해 같은 인코딩으로 서로 맞춰지면, 그제서야 정상적으로 문서를 읽을 수 있게 된다.

## 3. `text/plain`과 `text/html`의 차이 — 태그가 명령어로 읽히는가

```java
@WebServlet("/content-type")
public class Ex2ContentTypeServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        // [테스트 1] 일반 텍스트 모드 설정
        // resp.setContentType("text/plain; charset=UTF-8");

        // [테스트 2] HTML 모드 설정 (테스트 1을 주석 처리하고 아래 주석을 해제)
        resp.setContentType("text/html; charset=UTF-8");

        PrintWriter out = resp.getWriter();
        out.println("<html>");
        out.println("<body>");
        out.println("<h1>Content-Type 테스트</h1>");
        out.println("<p>브라우저가 이 태그를 어떻게 해석할까요?</p>");
        out.println("</body>");
        out.println("</html>");
    }
}
```

같은 내용을 `text/plain`으로 보내는지 `text/html`로 보내는지에 따라, 브라우저가 `<h1>`, `<p>` 같은 태그를 다루는 방식이 완전히 달라진다.

- **`text/plain`**: "이 문서에는 명령어가 포함되어 있지 않다"는 뜻이다. `<h1>` 같은 문자열이 그냥 텍스트 그대로, 태그 모양의 글자로 화면에 나온다
- **`text/html`**: HTML은 태그 자체가 전부 **명령어**다. 문서의 구조를 어떻게 표현하고, 어떤 의미를 가지는지를 태그가 설명한다. 그래서 `<h1>`이 실제로 제목처럼 렌더링된다 — 단, 이게 제대로 동작하려면 반드시 "이건 HTML 문서다"라고 Content-Type으로 먼저 알려줘야 한다

**줄바꿈(`\n`)의 동작도 달라진다.**

- 일반 텍스트로 읽는 뷰어는 `\n`을 그대로 줄바꿈으로 처리한다
- 하지만 `text/html`로 지정하면, HTML은 **태그 기반으로만** 문서를 해석한다 — `\n`은 HTML에서 명령어가 아니므로 줄바꿈으로 적용되지 않는다. HTML에서 줄을 바꾸려면 `<br>` 같은 태그를 직접 써야 한다(`Ex1EncodingServlet`에서 `println()` 뒤에도 매번 `<br>`을 따로 붙인 이유가 이것이다)

정리하면 `text/plain`은 메모장처럼 글자 그대로만 읽고, `text/html`은 태그를 명령어로 해석해서 문서 구조를 만든다.

## 4. 데이터를 출력하는 두 가지 방식 — HTML vs JSON

서블릿이 데이터를 응답으로 내보내는 방법은 크게 두 갈래로 나뉜다.

- **HTML로 포맷해서 출력** — 데이터를 이미 완성된 문서(사람이 브라우저에서 바로 보는 화면) 형태로 감싸서 준다. 서버사이드 페이지를 만들던 전통적인 방식이다
- **JSON으로 출력** — 문서가 아니라 **데이터 그 자체**만 준다. 뒤에서 배울 백엔드 API가 데이터만 주는 형태가 바로 이것이다

**서버사이드 페이지가 아직도 많이 쓰이는 이유**는 SEO(검색 엔진 최적화)다. 상품을 나열·소개하는 페이지들은 프론트엔드(자바스크립트)로 렌더링하면 오히려 기술적 난도가 올라가고 오류 가능성도 커진다. 페이지 수가 많고 관리할 게 많은 서비스일수록 서버사이드 페이지 방식을 여전히 많이 쓴다 — 그래서 실무에서는 풀스택으로 두 방식을 함께 다루게 되는 경우가 많다. (SEO 자체에 대해서는 관심 있으면 따로 찾아보면 좋다.)

## 5. HTML로 출력하기 — 값을 print문에 바로 넣지 않기

```java
@WebServlet("/object")
public class Ex3ExamObjectServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        resp.setContentType("text/html; charset=UTF-8");
        PrintWriter out = resp.getWriter();

        Exam exam = new Exam(85, 90, 78);
        int kor = exam.getKor();
        int eng = exam.getEng();
        int math = exam.getMath();
        int total = exam.total();
        double avg = exam.avg();

        out.println("<!DOCTYPE html>");
        out.println("<html><body>");
        out.println("<h2>개인 성적 성적표</h2>");
        // out.println("<p>국어: " + exam.getKor() + "점</p>");
        // out.println("<p>영어: " + exam.getEng() + "점</p>");
        // out.println("<p>수학: " + exam.getMath() + "점</p>");
        out.printf("<p>국어: %d점</p>", kor);
        out.printf("<p>영어: %d점</p>", eng);
        out.printf("<p>수학: %d점</p>", math);
        out.println("<hr>");
        out.printf("<p>총점: <strong>%d점</strong></p>", total);
        out.printf("<p>평균: <strong>%.2f점</strong></p>", avg);
        out.println("</body></html>");
    }
}
```

주석 처리된 세 줄(`exam.getKor()`을 `println` 안에 직접 문자열 이어붙이기로 쓴 부분)이 잘못 쓴 방식이다. **출력 구문(`print`/`printf`) 안에 연산식이나 메소드 호출을 바로 넣지 말고, 그 앞에서 변수로 값을 먼저 꺼내둔 뒤에 출력하는 게 좋다.** 실제 코드는 `int kor = exam.getKor();`처럼 미리 값을 변수에 담아두고, `printf`에는 그 변수만 넘긴다.

"이렇게 하면 코드량도 늘고 메모리도 더 쓰는 거 아닌가?"라는 생각이 들 수 있는데, 아니다. 지역 변수 몇 개가 늘어나는 정도는 무시할 수준이고, 그 대신 출력 코드가 **읽기 쉬워지고**, 나중에 같은 값을 여러 번 써야 할 때(총점·평균처럼) **다시 계산하거나 다시 호출할 필요가 없어진다.**

## 6. 목록(리스트) 페이지 — `for`문으로 반복 출력하기

실무에서 가장 많이 만들게 되는 화면 중 하나가 **목록 페이지**다. 여러 건의 데이터를 배열/리스트로 받아서, `for`문을 돌며 각 항목을 같은 포맷으로 반복 출력한다.

```java
@WebServlet("/list")
public class Ex4ExamListServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        resp.setContentType("text/html; charset=UTF-8");
        PrintWriter out = resp.getWriter();

        Exam[] list = new Exam[] {
            new Exam(100, 95, 90),
            new Exam(70, 80, 65),
            new Exam(88, 92, 79)
        };

        out.println("<!DOCTYPE html>");
        out.println("<html><body>");
        out.println("<h2>전체 수강생 성적 목록</h2>");
        out.println("<table border='1' style='border-collapse: collapse; text-align: center;'>");
        out.println("  <tr style='background-color: #f2f2f2;'>");
        out.println("    <th>번호</th><th>국어</th><th>영어</th><th>수학</th><th>총점</th><th>평균</th>");
        out.println("  </tr>");

        for (int i = 0; i < list.length; i++) {
            Exam e = list[i];
            int kor = e.getKor();
            int eng = e.getEng();
            int math = e.getMath();
            int total = e.total();
            double avg = e.avg();
            // out.printf("  <tr><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%.1f</td></tr>",
            //         i + 1, e.getKor(), e.getEng(), e.getMath(), e.total(), e.avg());
            out.printf("  <tr><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%.1f</td></tr>",
                    i + 1, kor, eng, math, total, avg);
        }

        out.println("</table>");
        out.println("</body></html>");
    }
}
```

여기서도 5장과 같은 원칙이 반복된다 — 반복문 안에서도 `e.getKor()` 등을 `printf`에 직접 넣기보다(주석 처리된 줄), `kor`, `eng`, `math`, `total`, `avg`처럼 **매 반복마다 변수로 먼저 꺼내놓고** 그 변수들을 출력에 쓴다. 한 행(`<tr>`)을 만드는 포맷 문자열 하나를 반복문으로 여러 번 찍어내는 것이 목록 페이지의 기본 패턴이다.

## 7. (참고) JSON으로 출력하기

HTML 문서 대신 **데이터만** 응답으로 주는 방식도 실무에서 아주 많이 쓰인다. `maven_servlet_project`에는 그 맛보기로 두 단계가 준비되어 있다.

**수동으로 JSON 문자열 만들기** (`Ex5JsonBasicServlet`)

```java
resp.setContentType("application/json; charset=UTF-8");
PrintWriter out = resp.getWriter();

Exam exam = new Exam(90, 85, 95);

String json = String.format(
    "{\"kor\": %d, \"eng\": %d, \"math\": %d, \"total\": %d, \"avg\": %.2f}",
    exam.getKor(), exam.getEng(), exam.getMath(), exam.total(), exam.avg()
);

out.print(json);
```

**라이브러리(Jackson)로 자동 변환하기** (`Ex6JsonJacksonServlet`)

```java
resp.setContentType("application/json; charset=UTF-8");
PrintWriter out = resp.getWriter();

List<Exam> list = new ArrayList<>();
list.add(new Exam(90, 80, 85));
list.add(new Exam(100, 95, 90));

// Jackson ObjectMapper를 활용한 Java List -> JSON Array 자동 변환
ObjectMapper mapper = new ObjectMapper();
String jsonResult = mapper.writeValueAsString(list);

out.print(jsonResult);
```

Content-Type도 `text/html`이 아니라 **`application/json`**으로 바뀐 걸 볼 수 있다 — 이 응답은 사람이 보는 문서가 아니라 프로그램이 읽어서 쓸 데이터라는 뜻이다. 문자열을 직접 이어붙이는 방식(`Ex5`)은 필드가 몇 개 안 될 때는 간단하지만, 객체가 복잡해지거나 리스트를 다뤄야 하면 금방 번거로워진다. `Ex6`처럼 Jackson 같은 라이브러리를 쓰면 자바 객체(`List<Exam>`)를 통째로 넘기기만 해도 JSON 배열로 자동 변환해준다.

