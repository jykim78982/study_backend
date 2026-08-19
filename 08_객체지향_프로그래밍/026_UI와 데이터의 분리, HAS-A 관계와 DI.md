---
tags: [자바, 객체지향, HAS-A, DI, 게터세터]
날짜: 2026-08-06
---

> 🔗 관련 노트: [[023_전역변수와 캡슐화, 객체지향의 역할 개념]] · [[024_구조화에서 객체지향으로]] · [[025_오버로드, 생성자, 캡슐 은닉화]]

# UI와 데이터의 분리, HAS-A 관계와 DI

## 1. 왜 UI와 데이터를 분리해야 하는가

`System.out.println`/`printf`는 콘솔(CUI) 프로그램에서만 의미가 있다. 같은 데이터를 윈도우(GUI) 프로그램으로 보여주려면 `JLabel`, `JTextBox` 같은 완전히 다른 방식으로 출력·입력해야 한다.

```java
// CUI: 콘솔에 출력
System.out.println("아메리카노");

// GUI: 윈도우 창에 라벨로 출력
JFrame frame = new JFrame();
frame.add(new JLabel("아메리카노"));
```

데이터는 콘솔이든 윈도우든 웹이든 동일하지만, **입출력 방식(껍데기)은 환경마다 달라진다.** 그런데 지금까지의 `Exam`처럼 데이터 관리(`kor`, `eng`, `math`, `total()`, `avg()`)와 콘솔 입출력(`input()`, `print()`)을 한 클래스에 결합해두면, 웹이나 윈도우 환경에서 이 클래스를 쓰려는 순간 콘솔 전용 기능까지 딸려온다 — **쓰지 않는 기능을 억지로 짊어지게 되는 것**이다.

그래서 데이터를 순수하게 관리하는 역할과, 그 데이터를 특정 환경에 맞게 입출력하는 역할(껍데기)을 분리해야 한다. 이번 실습(`step4_relation`)에서는 이 분리를 `Exam`(데이터)과 `ExamConsole`(콘솔 입출력)로 나눠서 구현했다.

## 2. 부품과 제품 — 누가 누구를 이용하는가

분리된 두 캡슐을 다시 엮어서 써야 하는데, 이때 **이용하는 쪽**과 **이용당하는 쪽**을 구분한다.

- 이용하는 쪽 = **클라이언트**이자 **제품**
- 이용당하는 쪽 = **서버**이자 **부품**

`ExamConsole`이 `Exam`의 서비스(`getKor()`, `total()` 등)를 갖다 쓰는 구조이므로, `Exam`이 부품(서버), `ExamConsole`이 제품(클라이언트)이다.

## 3. 게터/세터가 필요한 이유

이전에 필드를 `private`으로 감싸 캡슐을 은닉했다. 문제는 은닉된 필드를 **다른 캡슐에서 전혀 읽거나 쓸 수 없게 되는 것**이다. `exam.kor`처럼 직접 접근하는 건 캡슐을 깨는 행위이므로 금지된다.

대신 "값을 가져오는" 것과 "값을 대입하는" 것도 각각 하나의 서비스로 요청해야 한다.

- `int kor = exam.getKor();` → "국어 점수를 줘" → `exam.getKor()`
- `exam.kor = kor;` → "kor 값을 설정해줘" → `exam.setKor(kor)`

```java
// Exam 클래스 안의 메서드
public int getKor() {
    return kor;
}

public void setKor(int kor) {
    this.kor = kor;
}
```

불편해 보이지만, `private`으로 막아둔 캡슐을 절대 깨지 않으면서 값을 주고받는 유일하게 올바른 방식이다. `kor`, `eng`, `math` 세 필드 각각에 게터/세터를 만들어야 한다.

## 4. 계산은 데이터를 가진 쪽의 책임 — "극도의 이기주의"

`total`(합계), `avg`(평균) 계산은 입출력을 담당하는 콘솔의 일이 아니다. 국어·영어·수학을 더하는 건 입출력과 무관한, **데이터를 가진 `Exam`의 책임**이다.

```java
public int total() {
    return kor + eng + math;
}

public double avg() {
    return total() / 3.0;
}
```

객체지향을 잘하려면 **극도로 이기적이어야 한다** — 아무리 사소한 연산이라도 자기 책임이 아니면 끌어안지 않고, 그 데이터를 가진 객체에게 넘겨야 한다. `ExamConsole`은 이제 `total`, `avg`를 직접 계산하지 않고 `exam.total()`, `exam.avg()`를 불러서 결과만 받아 쓴다.

## 5. HAS-A 관계 — Composition vs Association

`ExamConsole`이 `Exam`을 필드로 갖고 있는 것은 `kor`, `eng`, `math`처럼 단순한 값 속성을 갖는 것과는 다르다. 객체와 객체 사이의 관계이기 때문에 **"HAS-A 관계"**라고 부른다. `ExamConsole`이 `Exam`을 가지고 있음으로써 그 기능(게터/세터, `total()`, `avg()`)을 사용할 수 있게 된다.

문제는 `ExamConsole`이 자기 생성자 안에서 직접 `new Exam()`을 만들어버리면, `ExamConsole`과 그 `Exam`이 하나로 딱 붙어버려서 **다른 `Exam` 데이터를 바꿔 끼울 수 없다.** 새 `Exam` 데이터를 출력하고 싶을 때마다 `ExamConsole`을 통째로 새로 만들어야 하는 불편함이 생긴다.

이걸 해결하려면, `ExamConsole`이 `Exam`을 직접 만들지 않고 **`null`로 갖고 있다가, 외부에서 만들어진 `Exam`을 대입(주입)받아 쓰게** 하면 된다. HAS-A 관계를 만드는 방법은 두 가지다.

| 방식 | 설명 | 코드 |
|---|---|---|
| **Composition Has-A** | 자기가 직접 `new`로 생성해서 가짐 | `public ExamConsole() { this.exam = new Exam(); }` |
| **Association Has-A** | 외부에서 만든 객체를 받아서 가짐(생성자 또는 setter) | `public ExamConsole(Exam exam) { this.exam = exam; }` |

Association Has-A를 쓰면, 하나의 `ExamConsole`에 원하는 `Exam` 데이터를 갈아 끼우면서 재사용할 수 있다 — `exam`을 세팅하면 `exam`이 출력되고, `exam1`을 세팅하면 `exam1`이 출력되는 식으로, 출력 로직 하나가 다양한 데이터에 재사용된다.

> 참고: `has a`로 부품을 갖는 관계는 넓게 보면 "has a 상속"이라 부르기도 하지만, 보통 "상속"이라는 말은 잘 쓰지 않는다. 나중에 나올 **is-a 상속**이 진짜 기본형 상속이기 때문이다.

## 6. DI(Dependency Injection) — 부품을 결합하는 것

Association Has-A로 외부에서 만든 객체를 대입해주는 작업 자체를 가리키는 용어가 있다.

- 부품 = **Dependency**(의존성)
- 결합 = **Injection**(주입)
- 합쳐서 **DI(Dependency Injection)**

방식은 두 가지다.

- **Constructor Injection**: 생성자 인자로 부품을 넘겨받음 — `new ExamConsole(exam)`
- **Setter Injection**: setter로 나중에 부품을 넘겨받음 — `console.setExam(exam)`

**`ExamConsole` 쪽 — exam을 넘겨받는 통로를 정의**

```java
public ExamConsole(Exam exam) {
    this.exam = exam;
}
```

**Constructor Association Has-A** — 생성자 인자로 `exam`을 받아서, 객체가 만들어지는 그 순간 바로 채워 넣는다.

```java
public ExamConsole() {

}
public void setExam(Exam exam) {
    this.exam = exam;
}
```

**Setter Association Has-A** — 무인자 생성자로 `exam`이 `null`인 채로 먼저 만들고, 나중에 `setExam()`을 불러서 채워 넣는다.

`ExamConsole` 입장에서는 아직 `exam`이 채워지지 않았을 뿐, "누군가 나중에 `Exam`을 넣어줄 것"이라는 통로 두 개만 미리 마련해둔 상태다. 생성자로 받을지, setter로 받을지는 `ExamConsole` 스스로 정하지 않는다 — 어떤 방식으로 `exam`이 들어오든 받아줄 수 있게 문만 열어두고, 실제로 값을 채워 넣는 결정은 이 코드를 사용하는 쪽(App)에게 넘긴다.

**객체를 생성하는 시점에 `exam`을 어떻게 받는가**

- `new ExamConsole(exam)`처럼 인자를 주면, 생성자(`ExamConsole(Exam exam)`)가 실행되면서 그 자리에서 바로 `this.exam = exam;`이 이루어진다 — 생성과 동시에 `exam`이 채워진 상태로 태어난다
- `new ExamConsole()`처럼 인자 없이 만들면, `ExamConsole(Exam exam)`이라는 오버로드 생성자가 이미 있기 때문에 이 무인자 생성자는 **직접 추가로 정의해둬야만** 존재한다 — 그 몸통이 비어있으면 `exam`은 대입해주는 코드가 없으니 참조 형식의 기본값인 `null`로 남은 채로 태어난다

즉 객체가 태어나는 그 순간의 상태(`exam`이 채워져 있는지, `null`인지)는 **어떤 생성자를 호출했는지**에 따라 갈리고, `null`로 태어난 경우에만 이후에 `setExam()`으로 값을 채워 넣어야 한다.

**`Exam`을 넘겨주는 쪽(App) — 실제로 DI가 일어나는 지점**

```java
// Constructor Injection
ExamConsole console = new ExamConsole(exam);
// 객체를 생성하는 시점에 exam을 넘겨받는다

// Setter Injection
ExamConsole console = new ExamConsole();
// 생성 시점에는 exam이 null 상태
console.setExam(exam);
// 이후에 exam을 넘겨받는다
```

> 예문: "exam을 console 객체에 DI 해줘야 하지 않을까요?" / "exam을 console 객체에 constructor injection 해주세요."

## 7. 종합 코드 — step4_relation

**`Exam` — 데이터 + 계산 서비스만 가진 순수한 부품**

```java
public class Exam {
    private int kor;
    private int eng;
    private int math;

    public Exam() {
        this(50, 50, 50);
    }

    public Exam(int kor, int eng, int math) {
        this.kor = kor;
        this.eng = eng;
        this.math = math;
    }

    public int getKor() { return kor; }
    public void setKor(int kor) { this.kor = kor; }
    public int getEng() { return eng; }
    public void setEng(int eng) { this.eng = eng; }
    public int getMath() { return math; }
    public void setMath(int math) { this.math = math; }

    public int total() {
        return kor + eng + math;
    }

    public double avg() {
        return total() / 3.0;
    }
}
```

**`ExamConsole` — 콘솔 입출력만 담당하고, `Exam`을 Association Has-A로 갖는 제품**

```java
public class ExamConsole {

    private Exam exam;

    // Constructor Association Has-A
    public ExamConsole(Exam exam) {
        this.exam = exam;
    }

    // Setter Association Has-A
    public void setExam(Exam exam) {
        this.exam = exam;
    }

    public void print(boolean hasBorder) {
        int kor = exam.getKor();
        int eng = exam.getEng();
        int math = exam.getMath();
        int total = exam.total();
        double avg = exam.avg();

        System.out.println("[성적출력]");
        System.out.printf("kor : %d\n", kor);
        System.out.printf("eng : %d\n", eng);
        System.out.printf("math : %d\n", math);
        System.out.printf("total : %d\n", total);
        System.out.printf("avg : %.1f\n", avg);

        if (hasBorder)
            System.out.println("--------------------------------");
    }

    public void input() {
        Scanner scan = new Scanner(System.in);

        System.out.print("kor:");
        int kor = Integer.parseInt(scan.nextLine());
        System.out.print("eng:");
        int eng = Integer.parseInt(scan.nextLine());
        System.out.print("math:");
        int math = Integer.parseInt(scan.nextLine());

        exam.setKor(kor);
        exam.setEng(eng);
        exam.setMath(math);
    }
}
```

**`App` — DI로 부품을 조립하는 조립부**

```java
Exam exam = new Exam();

// Constructor Injection
ExamConsole console = new ExamConsole(exam);

// Setter Injection (같은 exam을 다시 세팅해도 되고, 다른 exam으로 갈아 끼워도 됨)
console.setExam(exam);
```

`Exam`은 데이터와 계산만 책임지고, `ExamConsole`은 콘솔 입출력만 책임진다. 나중에 GUI 버전이 필요하면 `Exam`은 그대로 두고 `ExamConsole` 대신 `ExamWindow` 같은 새 클라이언트를 만들어 같은 `Exam`을 DI해주기만 하면 된다 — 이것이 UI와 데이터를 분리해서 얻는 재사용성이다.

