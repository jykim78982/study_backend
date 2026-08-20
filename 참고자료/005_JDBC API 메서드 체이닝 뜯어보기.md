---
tags: [자바, JDBC, PostgreSQL, 메서드체이닝]
날짜: 2026-08-20
---

> 🔗 관련 노트: [[038_JDBC API와 리포지토리 분리]]

# JDBC API 메서드 체이닝 뜯어보기

`038` 노트에서 다룬 `JdbcMenuRepository`에 나온 JDBC 호출들을, 한 단계씩 무엇을 반환하고 무엇을 하는지 뜯어서 정리한다.

## 1. 드라이버 등록소에서 연결 얻기

```java
Connection conn = DriverManager.getConnection(URL, "<user>", "<password>");
```

- **`DriverManager`**: 특정 객체가 아니라, JDBC 드라이버들을 관리하는 **정적(static) 등록소**다. `pom.xml`에 추가한 PostgreSQL 드라이버가 이미 여기에 등록되어 있다.
- **`.getConnection(URL, "<user>", "<password>")`**: 등록된 드라이버 중에서 `URL`(`jdbc:postgresql://...`)에 맞는 드라이버를 찾아, 그 드라이버로 실제 DB에 접속을 시도한다. 인자 세 개는 순서대로 **접속 주소, 계정, 비밀번호**다.
- **반환값 `Connection`**: 접속에 성공하면 돌려주는 **연결 객체**. 이후의 모든 SQL 작업은 이 `conn` 하나를 시작점으로 삼는다.

## 2. 연결에서 SQL 실행 도구 얻고 바로 실행하기

```java
Statement st = conn.createStatement();
ResultSet rs = st.executeQuery(sql);
```

- **`conn.createStatement()`**: `Connection`에게 "SQL을 실행할 도구를 하나 만들어줘"라고 요청한다. 반환값은 **`Statement`** — 아직 아무 SQL도 실행하지 않은, 실행 준비만 된 도구다.
- **`st.executeQuery(sql)`**: 그 도구로 `sql` 문자열(`SELECT ...`)을 실제로 서버에 보내 실행한다. 조회(`SELECT`) 전용 메서드라서, 결과가 항상 **`ResultSet`**(결과집합)으로 돌아온다.
- 이 둘을 한 줄로 합쳐서 `ResultSet rs = conn.createStatement().executeQuery(sql);`처럼 체이닝해서 쓸 수도 있다 — 중간에 `Statement`를 따로 참조할 필요가 없을 때 자주 쓰는 형태다.

## 3. 결과집합에서 커서를 옮기며 값 꺼내기

```java
rs.next();
String korName = rs.getString("kor_name");
```

- **`rs.next()`**: `ResultSet`의 커서를 한 칸 아래로 옮긴다. 옮길 다음 행이 있으면 `true`, 더 이상 행이 없으면(EOF) `false`를 반환한다 — 그래서 실전 코드에서는 보통 `while (rs.next()) { ... }`처럼 반복문 조건으로 쓴다.
- **`rs.getString("kor_name")`**: `next()`로 이동한 **현재 커서 위치의 행**에서, `kor_name`이라는 **컬럼명**을 지정해 그 값을 `String`으로 꺼낸다. 컬럼명은 SQL의 `SELECT` 목록에 쓴 이름을 그대로 써야 한다.
- 즉 `rs.next()`가 "행을 하나 가리키게 만드는 동작"이고, `rs.getString(...)`은 "그 행에서 특정 칸의 값을 읽는 동작"으로, 역할이 분리되어 있다.

## 4. 체이닝이 아닌 개별 선언·문장도 뜯어보기

체이닝은 "반환값에 바로 점을 찍어 이어 부르는" 형태고, 아래는 그렇지 않은 평범한 문장들이다. 별거 아닌 것처럼 보여도 각자 명확한 역할이 있다.

```java
List<Menu> menus = new ArrayList<>();
```

- **`List<Menu>`**: 왼쪽의 **선언 타입**이다. 이 변수로는 `List` 인터페이스가 제공하는 기능(`add`, `get`, `size` 등)만 쓰겠다고 미리 약속하는 것 — 실제 구현체가 무엇인지는 이 시점엔 감춰둔다.
- **`new ArrayList<>()`**: 오른쪽의 **실제 생성**이다. 메모리에 진짜로 만들어지는 객체는 `ArrayList`이고, `<>`(다이아몬드 연산자)는 왼쪽에 이미 `<Menu>`가 적혀 있으니 타입을 다시 안 써도 컴파일러가 알아서 `Menu`로 채워준다는 뜻이다.
- **`menus`**: 이렇게 만들어진 `ArrayList` 객체의 주소를 가리키는 변수 이름. 이 시점의 `menus`는 **빈 리스트**를 가리킨다(`findAll()`이 결국 실패해도 빈 리스트를 반환하는 이유이기도 하다).

```java
String URL = "jdbc:postgresql://<host>:5432/<dbname>";
```

- 문자열 하나이지만 내부에 형식이 정해져 있다. `jdbc:postgresql:` 부분은 "이 문자열은 JDBC 연결 정보이고, PostgreSQL용으로 해석해라"는 프로토콜 표시다.
- `//<host>:5432`는 접속할 **서버 주소와 포트**(PostgreSQL 기본 포트가 5432)다.
- `/<dbname>`은 그 서버 안에서 접속할 **DB 이름**을 지정한다.
- 이 문자열 자체는 아무 동작도 하지 않는다 — 뒤에서 `DriverManager.getConnection(URL, ...)`이 이 문자열을 **해석해서** 실제 접속을 시도할 때 비로소 의미를 갖는다.

```java
try {
    // ...
} catch (SQLException e) {
    e.printStackTrace();
}
```

- **`try { ... }`**: DB 연결·SQL 실행처럼 **실패할 가능성이 있는 코드**를 감싼다. 네트워크 문제, 잘못된 계정, SQL 문법 오류 등으로 언제든 예외가 날 수 있는 구간이기 때문이다.
- **`catch (SQLException e)`**: `try` 블록 안에서 **`SQLException` 계열의 예외**가 발생했을 때만 이 블록이 실행된다. `e`는 예외에 대한 정보(어떤 문제였는지)를 담은 객체다.
- **`e.printStackTrace()`**: 그 예외가 어디서, 어떤 순서로 발생했는지를 콘솔에 출력한다. 사용자에게 보여줄 화면이 아니라, 개발자가 원인을 추적하기 위한 디버깅용 출력이다.

```java
System.out.println(conn.isClosed());
```

- **`conn.isClosed()`**: 지금 이 `Connection` 객체가 닫혀 있는지를 `true`/`false`로 알려준다. 연결을 만든 직후라면 아직 안 닫혔을 테니 `false`가 나온다.
- **`System.out.println(...)`**: 그 결과값을 콘솔에 한 줄 출력한다. `038` 노트의 예제 코드는 이 두 호출로 "연결이 열려 있다가, `conn.close()` 이후에는 닫혔다"는 걸 눈으로 확인시켜준다.
