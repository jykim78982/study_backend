---
tags: [스프링부트, 트랜잭션, ACID, JDBC, EJB, 참고자료]
---

> 🔗 관련 노트: [[084_트랜잭션 — 작업 단위, ACID, 그리고 스프링 @Transactional이 필요한 이유]] · [[트랜잭션 ACID 오답노트]] · [[082_JPQL과 @Query — 쿼리 메서드 이름 대신 쿼리를 직접 쓰기]]

# 트랜잭션과 트랜잭션 처리의 이해 — JDBC에서 EJB, 스프링까지

## 1. 트랜잭션의 개념과 ACID

트랜잭션(Transaction)은 **하나의 업무 단위**를 말한다. 업무 단위라고 말하면 어렵게 느껴질 수 있는데, 우리가 사용하는 3계층 아키텍처에서 서비스가 가지는 함수 하나하나가 업무 단위이다. 이 업무 단위가 트랜잭션이다.

그렇다면 트랜잭션은 단순히 업무 단위를 말하는 것일까?

그렇다. 트랜잭션이라는 용어의 사전적인 의미는 "매매", "거래", "업무", "처리" 등을 말한다. 서비스 계층은 사용자가 원하는 하나의 처리 단위이며, 업무 단위이며, 거래 단위이다.

> 정확히는 서비스의 **공개(public) 업무 메서드**가 업무 단위다. 서비스 안에서 계산이나 검증만 하는 작은 `private` 도우미 메서드는 업무 단위의 일부일 뿐, 그 자체가 하나의 트랜잭션은 아니다.

그렇다면 단순히 트랜잭션은 업무를 처리하는 것을 말하는 것 같은데, "트랜잭션 처리"는 또 무슨 말인가?

### 1-1. 트랜잭션 처리

트랜잭션 처리, 즉 트랜잭션을 처리한다는 말은 **하나의 업무가 일부만 처리되는 일이 발생하지 않게 한다**는 것이다.

```
[Controller]  RefundController.refund(...)
      │
[Service]     RefundService.refund(...)          ← 업무 단위(트랜잭션)
      │
      ├─ PaymentRepository.findById(...)
      ├─ RefundRepository.save(...)
      ├─ PaymentRepository.save(...)
      └─ OrderRepository.save(...)
      │
[DB]          payments / refunds / orders
```

위 계층에서 서비스 계층을 보면 환불(`refund(...)`)이라는 업무가 보인다. 이 업무는 대략 다음과 같은 순서로 처리된다.

1. **원거래 결제 데이터 조회**: `결제Repository.findById(..)`
2. **환불 가능 여부 검증**: `if ...`
3. **환불 이력 저장**: `환불Repository.save(...)`
4. **결제 상태 업데이트**: `결제Repository.save(...)`
5. **주문 상태 업데이트**: `주문Repository.save(...)`

물론 이것을 처리할 때는 위 그림처럼 다양한 리포지토리를 이용해야 한다.

```java
public void refund(Long paymentId) {
    Payment payment = paymentRepository.findById(paymentId).orElseThrow(); // 1
    if (!payment.isRefundable()) throw new IllegalStateException("환불 불가");  // 2
    refundRepository.save(new Refund(payment));                            // 3
    payment.markRefunded();
    paymentRepository.save(payment);                                       // 4
    Order order = payment.getOrder();
    order.markCanceled();
    orderRepository.save(order);                                           // 5 ← 여기서 오류가 나면?
}
```

그런데 그중에서 하나의 함수 호출에서 오류가 발생하면 어떻게 될까? 예를 들어 5번에서 오류가 나면, 환불 이력은 저장되고 결제 상태도 "환불됨"으로 바뀌었는데 주문은 그대로 "완료" 상태로 남는다. 환불이 완전하게 처리되지 못하고 **깨지는** 것이다.

환불 처리는 모든 과정이 완료되거나, 아니면 원래대로 돌려놓아야 한다. 그렇게 해야 업무가 제대로 처리된 것이다. 이렇게 업무 단위가 일부만 성공하지 않도록, 모든 처리가 완료되거나 오류가 발생해 처리가 불가능하면 원래대로 돌려놓도록 하는 것을 **"트랜잭션 처리"**라고 한다.

트랜잭션의 성질은 **ACID**로 요약된다.

- **원자성(Atomicity)**: 트랜잭션 내의 모든 작업이 모두 성공하거나, 하나라도 실패하면 전체가 실행되지 않은 상태로 취급된다.
- **일관성(Consistency)**: 트랜잭션 실행 전후로 데이터베이스가 일관된 상태(무결성 제약 조건 등)를 유지한다.
- **독립성(Isolation)**: 동시에 실행되는 트랜잭션이 서로의 중간 결과를 참조하지 않도록 격리된다.
- **영속성(Durability)**: 트랜잭션이 커밋된 후에는 시스템 장애가 발생해도 변경 사항이 손실되지 않는다.

> Isolation은 **격리성**, Durability는 **지속성**이라고도 번역한다. 시험이나 자료마다 용어가 섞여 나오므로 둘 다 알아두면 된다. 영속성은 JPA의 "영속성 컨텍스트"와 단어가 같지만 뜻은 다르다(커밋된 데이터가 사라지지 않는다는 성질).

"트랜잭션을 처리한다"는 말은 단순히 데이터를 수정하는 것을 넘어, **데이터베이스 연결(Connection)을 관리하고, 작업의 시작과 끝을 명시적으로 제어하며, 예외 발생 시 롤백을 수행하는** 일련의 과정을 의미한다.

## 2. JDBC API를 이용한 트랜잭션 처리

트랜잭션 처리가 어려운 것은 아니다. DBMS나 JDBC API를 이용할 때는 그것을 위한 장치가 모두 준비되어 있다.

예를 들어 JDBC API를 이용한 코드를 보면, 연결 객체를 만든 후에 여러 작업을 모두 처리하고, 모든 작업이 성공하면 `commit`하고 실패하면 `rollback`하도록 하는 기능이 있다.

```java
Connection conn = null;
try {
    conn = dataSource.getConnection();
    conn.setAutoCommit(false); // 트랜잭션 시작

    // 1. 계좌 A에서 100만원 출금
    PreparedStatement stmt1 = conn.prepareStatement("UPDATE account SET balance = balance - ? WHERE id = ?");
    stmt1.setInt(1, 1000000);
    stmt1.setString(2, "A");
    stmt1.executeUpdate();

    // 2. 계좌 B에 100만원 입금
    PreparedStatement stmt2 = conn.prepareStatement("UPDATE account SET balance = balance + ? WHERE id = ?");
    stmt2.setInt(1, 1000000);
    stmt2.setString(2, "B");
    stmt2.executeUpdate();

    conn.commit(); // 트랜잭션 커밋
} catch (Exception e) {
    if (conn != null) {
        try {
            conn.rollback(); // 트랜잭션 롤백
        } catch (SQLException ex) {
            // 롤백 실패 처리
        }
    }
    throw e;
} finally {
    if (conn != null) {
        try {
            conn.setAutoCommit(true); // 원래 상태로 복원
            conn.close(); // 연결 반환
        } catch (SQLException e) {
            // 연결 닫기 실패 처리
        }
    }
}
```

> **코드 읽기 보충**
> - `setAutoCommit(false)`: JDBC는 기본이 **자동 커밋**이라 SQL 한 문장마다 바로 확정된다. 이를 끄는 것이 곧 트랜잭션 시작이다.
> - `finally`에서 `setAutoCommit(true)`로 되돌리는 이유: 실무에서는 `dataSource`가 **커넥션 풀**(HikariCP 등)이라서 `close()`가 연결을 끊는 게 아니라 **풀에 반납**한다. 자동 커밋을 꺼둔 채로 반납하면, 그 커넥션을 다음에 빌려 간 코드가 의도치 않게 수동 커밋 상태로 동작할 수 있다.
> - 출금만 되고 입금 전에 오류가 나도, `rollback()` 덕분에 A의 잔액은 원래대로 돌아간다.

위 코드처럼 JDBC로 트랜잭션을 처리하는 기능은 이미 있다. 그런데 이것이 어려워지는 것은 코드를 **3계층으로 나누었기 때문**이다.

## 3. 계층화와 트랜잭션의 충돌

애플리케이션을 계층화하면 트랜잭션 처리가 더 어려워진다. 일반적인 계층 구조는 다음과 같다.

- **프레젠테이션 계층**: HTTP 요청을 처리하고 서비스 계층을 호출한다.
- **서비스 계층**: 비즈니스 로직을 처리하고 리포지토리 계층을 호출한다.
- **리포지토리/데이터 접근 계층**: 데이터베이스와 통신한다.

JDBC API를 직접 사용할 때와 달리, 서비스 계층에서 리포지토리 계층을 이용하면 트랜잭션을 처리할 수가 없다.

```java
// 서비스 계층
public void 계좌이체(...) {
    accountRepository.withdraw("A", 1000000); // 내부에서 연결을 열고, 실행하고, 닫는다
    accountRepository.deposit("B", 1000000);  // 또 다른 연결에서 실행된다
}
```

각 함수가 각각 연결을 생성하고 종료하면서 **각각 커밋**될 것이기 때문이다. `deposit`에서 오류가 나도 `withdraw`는 이미 확정된 뒤라 되돌릴 수 없다.

```java
// 서비스 계층
public void 계좌이체() throws SQLException {
    Connection conn = dataSource.getConnection();
    conn.setAutoCommit(false);
    try {
        accountRepository.withdraw(conn, "A", 1000000); // 연결을 전달
        accountRepository.deposit(conn, "B", 1000000);  // 연결을 전달
        conn.commit();
    } catch (Exception e) {
        conn.rollback();
        throw e;                                        // 실패를 호출한 쪽에 알린다
    } finally {
        conn.setAutoCommit(true);
        conn.close();
    }
}
```

물론 모든 리포지토리 메서드에 연결 객체를 넘겨주게 해서, 서비스 계층이 그 연결을 관리하면서 커밋을 하나로 묶을 수는 있다. 하지만 이 방식은 다음과 같은 문제를 가지게 된다.

- **연결 객체의 전파**: 데이터베이스 연결 객체를 서비스 계층에서 리포지토리 계층으로, 다시 DAO로까지 전달해야 한다.
- **계층 간 결합도 증가**: 리포지토리 계층이 특정 연결 객체를 받아야 하므로 재사용성이 떨어진다. 또 서비스 계층이 `Connection`, `SQLException` 같은 **JDBC 기술에 직접 의존**하게 되어, 나중에 JPA로 바꾸면 서비스 코드까지 고쳐야 한다.
- **트랜잭션 범위 관리의 어려움**: 여러 리포지토리 메서드가 같은 트랜잭션에 참여하도록 보장하는 것이 복잡해진다.
- **반복 코드**: 업무 메서드마다 `getConnection` → `setAutoCommit(false)` → `commit`/`rollback` → `close`라는 같은 틀이 반복되고, 정작 비즈니스 로직은 그 사이에 묻힌다.

결국 **"계층화를 포기할 것인가, 아니면 트랜잭션을 포기할 것인가"**라는 딜레마에 직면하게 된다. 사실 둘 다 포기할 수 없는 것들이기 때문에, Java EE 플랫폼에서는 **EJB 컨테이너**를 선보였다.

## 4. EJB의 트랜잭션 처리

EJB(Enterprise JavaBeans)는 이러한 문제를 해결하기 위해 **컨테이너 관리형 트랜잭션**(CMT, Container-Managed Transaction)을 도입했다. EJB 컨테이너는 데이터베이스 연결을 관리하고, 트랜잭션의 시작과 커밋, 롤백을 자동으로 처리한다.

개발자는 EJB 빈(Bean)에 트랜잭션 속성을 지정하기만 하면 된다.

```java
@Stateless
public class AccountServiceBean {

    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public void transfer(String from, String to, int amount) {
        // 비즈니스 로직
        // 트랜잭션 시작, 커밋, 롤백은 컨테이너가 자동 처리
    }
}
```

- `@Stateless`: 상태를 가지지 않는 세션 빈이라는 표시.
- `REQUIRED`: 이미 진행 중인 트랜잭션이 있으면 거기에 참여하고, 없으면 새로 시작한다. 스프링 `@Transactional`의 기본 동작(전파 속성 `REQUIRED`)과 같은 개념이다.

하지만 위 코드가 보여주듯 단순한 어노테이션 한 줄로 끝나는 것은 아니다. EJB를 실제 애플리케이션에 적용하려면 아래와 같은 복잡한 설정과 인프라가 요구된다.

- **XML 설정 파일**: `ejb-jar.xml`이나 서버별 설정 파일(`sun-ejb-jar.xml`, `weblogic-ejb-jar.xml` 등)에서 빈의 종류, 트랜잭션 속성, 보안 역할 등을 상세히 정의해야 한다.
- **EJB 컨테이너 실행**: Tomcat 같은 일반 웹 서버(서블릿 컨테이너)로는 구동할 수 없으며, WildFly, GlassFish, WebLogic 등 EJB 스펙을 지원하는 애플리케이션 서버를 설치하고 실행해야 한다.
- **배포 단위 관리**: EJB 모듈은 WAR 파일에 포함되거나 별도의 EAR 파일로 패키징되어야 하며, 컨테이너가 이를 스캔하고 초기화하는 과정이 필요하다.

좀 더 구체적으로 본 단점은 다음과 같다.

- **복잡한 설정**: XML 설정 파일과 컨테이너 설정이 복잡하다.
- **무거운 구조**: EJB 컨테이너가 필요하며, 배포와 관리가 어렵다. 테스트하려 해도 컨테이너를 띄워야 해서 단위 테스트가 어렵다.
- **학습 곡선**: EJB의 생명주기, 빈 종류, 컨테이너 관리 개념 등을 이해해야 한다.
- **상업적 라이선스 비용**: WebLogic, WebSphere 등 엔터프라이즈급 EJB 서버는 라이선스 비용이 발생하여, 오픈소스 기반의 경량 프레임워크에 비해 유지보수 비용이 높아진다.

> **보충 — EJB의 시기별 차이**: 위 예시처럼 어노테이션을 쓰는 방식은 2006년 **EJB 3.0**부터다. 그 전의 **EJB 2.x**는 어노테이션 없이 홈 인터페이스·리모트 인터페이스·빈 클래스를 따로 만들고 모든 것을 XML로 설정해야 해서 훨씬 무거웠다. 스프링(2004년 1.0 출시)은 바로 이 EJB 2.x의 무게에 대한 반발로 등장했고, EJB 3.0은 오히려 스프링과 Hibernate의 영향을 받아 가벼워진 것이다.

## 5. 스프링의 트랜잭션 처리

스프링은 EJB의 장점(선언만 하면 컨테이너가 트랜잭션을 관리)을 흡수하되, 복잡성을 크게 줄인 경량 트랜잭션 관리 방식을 제공한다. 스프링은 **AOP(Aspect-Oriented Programming) 프록시** 원리를 이용하여 트랜잭션 처리 로직을 비즈니스 로직과 분리한다.

스프링에서 트랜잭션을 처리하려면 `@Transactional` 어노테이션을 서비스 빈의 메서드에 붙이는 것만으로 충분하다.

```java
@Service
public class AccountService {

    private final AccountRepository accountRepository;

    public AccountService(AccountRepository accountRepository) {   // 생성자 주입
        this.accountRepository = accountRepository;
    }

    @Transactional
    public void transfer(String from, String to, int amount) {
        accountRepository.decreaseBalance(from, amount);
        accountRepository.increaseBalance(to, amount);
        // 트랜잭션 시작, 커밋, 롤백은 스프링이 자동 처리
    }
}
```

> 원본 자료는 `@Autowired` 필드 주입을 썼는데, 스프링에서는 위처럼 **생성자 주입**이 권장된다. 필드를 `final`로 둘 수 있고, 테스트할 때 가짜 리포지토리를 넣기도 쉽다.

EJB와의 차이점은 다음과 같다.

- **경량성**: 별도의 애플리케이션 서버나 복잡한 XML 설정이 필요 없다. Tomcat이 내장된 스프링 부트 애플리케이션으로 그대로 실행된다.
- **단순한 설정**: `@Transactional` 한 줄로 트랜잭션 범위를 정의할 수 있다. 스프링 부트는 DB 의존성이 있으면 트랜잭션 관리자(`JpaTransactionManager` 등)와 `@Transactional` 처리 기능을 **자동으로 설정**해준다.
- **AOP 기반**: 프록시를 통해 트랜잭션 로직을 삽입하므로 비즈니스 코드는 깔끔하게 유지된다.
- **기술 독립**: 서비스 코드에 `Connection`이 등장하지 않는다. JDBC든 JPA든 같은 `@Transactional`을 쓴다.

스프링은 `@Transactional`을 통해 트랜잭션의 시작, 커밋, 롤백을 자동화하고, 데이터베이스 연결을 관리한다. 스프링이 이 기능을 어떻게 구현하는지는 다음에 AOP와 함께 자세히 살펴볼 예정이다.

### 5-1. 추가 — 3절의 "연결 전파" 문제는 어떻게 사라지나

3절에서 가장 큰 문제는 리포지토리들이 **같은 연결을 쓰게 하려면 연결 객체를 계속 넘겨야 한다**는 것이었다. 스프링은 연결을 파라미터로 넘기는 대신, **현재 실행 중인 스레드에 보관**하는 방법으로 해결한다.

```
요청 스레드 ──> [트랜잭션 프록시] 트랜잭션 시작: 커넥션을 얻어 자동 커밋 끄고 "현재 스레드"에 보관
                 │
                 ├─> AccountService.transfer()
                 │     ├─> decreaseBalance()  ── 스레드에 보관된 같은 커넥션 사용
                 │     └─> increaseBalance()  ── 스레드에 보관된 같은 커넥션 사용
                 │
                 └─ 정상 종료 → commit / 런타임 예외 → rollback, 커넥션 반납
```

웹 요청 하나는 보통 스레드 하나가 처음부터 끝까지 처리한다. 그래서 그 스레드에 커넥션을 묶어두면(`ThreadLocal`, 스프링의 `TransactionSynchronizationManager`), 리포지토리들은 파라미터 없이도 **같은 커넥션**을 꺼내 쓸 수 있다. 서비스와 리포지토리의 메서드 시그니처에 `Connection`이 등장하지 않는 이유다.

### 5-2. 추가 — @Transactional 사용 시 주의할 점

| 주의점 | 설명 |
|---|---|
| **롤백 기준** | 기본적으로 **런타임 예외(`RuntimeException`)와 `Error`**에서만 롤백한다. `IOException` 같은 체크 예외는 커밋된다. 체크 예외에도 롤백하려면 `@Transactional(rollbackFor = Exception.class)` |
| **예외를 삼키면 커밋된다** | 메서드 안에서 `try-catch`로 예외를 잡고 다시 던지지 않으면, 스프링은 실패를 모르고 커밋한다 |
| **같은 클래스 내부 호출** | 같은 클래스 안에서 `this.다른메서드()`로 부른 메서드의 `@Transactional`은 적용되지 않는다. 프록시를 거치지 않고 객체 내부에서 바로 호출되기 때문이다 |
| **public 메서드에 붙인다** | 프록시가 가로챌 수 있는 메서드에만 적용된다. `private` 메서드에 붙이면 무시된다 |
| **조회 전용** | 조회만 하는 메서드는 `@Transactional(readOnly = true)`로 표시하면 불필요한 변경 감지를 줄여 성능에 유리하다 |
| **import 주의** | `org.springframework.transaction.annotation.Transactional`(스프링)과 `jakarta.transaction.Transactional`(Jakarta EE) 두 가지가 있다. 스프링 프로젝트에서는 `readOnly`, `rollbackFor` 같은 옵션을 모두 지원하는 **스프링 쪽**을 쓴다 |
