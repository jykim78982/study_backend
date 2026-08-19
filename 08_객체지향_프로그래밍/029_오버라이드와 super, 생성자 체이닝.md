---
tags: [자바, 오버라이드, super, 생성자, 상속, 어노테이션]
날짜: 2026-08-06
---

> 🔗 관련 노트: [[028_프로젝트 구성과 클래스패스, IS-A 상속의 등장]] · [[025_오버로드, 생성자, 캡슐 은닉화]]

# 오버라이드와 super, 생성자 체이닝

## 1. `exam.total()`을 부를 때 실제로 무슨 일이 일어나는가

`MyExam`은 `total()`을 구현한 적이 없는데도, `exam.total()`을 부르면 마치 자기가 서비스하는 것처럼 동작한다. 이건 착각하기 쉬운 지점이다 — **엄밀히 말하면 그건 `MyExam`이 만든 게 아니라, `MyExam`의 틀(부모 클래스 `Exam`)이 구현해준 것**이다.

만약 상속(IS-A, 틀로 쓰는 방식)이 아니라 **부품(HAS-A)으로 `Exam`을 가지고 있었다면** 얘기가 다르다.

```java
exam.get부품().total();
```

이렇게 쓰면 "이 `total()`은 내가 가진 부품이 제공하는 기능"이라는 게 코드에 명확히 드러난다. 하지만 상속으로 쓰면, **사용하는 사람 입장에서는 `total()`을 자식이 구현했는지 부모가 구현했는지 알 방법이 없다.** 자식 클래스가 구현했든 부모 클래스가 구현했든 똑같이 `exam.total()`로 호출되고, 자식이 구현한 것처럼 자연스럽게 쓰이기 때문이다.

## 2. 오버라이드가 등장하는 진짜 이유 — "바른 순서로" 이해하기

1. 부모(`Exam`)가 제공하는 `total()`을 그대로 쓰고 있었다
2. 그런데 `com`(컴퓨터 과목)이 추가되면서 문제가 생겼다 — `Exam`이 제공하는 `total()`은 국영수만 더할 뿐, `com`은 전혀 모른다
3. `Exam`의 소스 코드를 고치면 되지 않느냐고 생각할 수 있지만, **불가능하다** — `Exam`은 라이브러리로 배포된 것이라 내가 손댈 수 없고, 애초에 `Exam`은 국영수만 아는 게 정상이다(컴퓨터 과목까지 알아야 할 이유가 없다)
4. 그래서 **`Exam`을 확장해서 쓰는 쪽(`MyExam`)이 알아서 고쳐 써야 한다** — 이걸 위해 부모가 준 것을 자식이 덮어써버리는 게 **오버라이드**다

즉 오버라이드는 "부모가 주는 서비스를 쓰다가, 그게 지금 내 상황에 안 맞아서 내가 덮어써버려야 했다"는 필요에서 나온 개념이다.

**참고**: 오버로드(Overload)와 오버라이드(Override)는 이름이 비슷해서 자주 비교되지만, **태생이 완전히 다른 별개의 개념**이다 — 오버로드는 같은 캡슐 안에서 인자로 메소드를 구분하는 것(이전 노트 참고), 오버라이드는 부모가 준 걸 자식이 덮어쓰는 것이다.

## 3. 오버라이드 여부를 어떻게 알아볼 수 있는가 — 어노테이션(`@`)

`total()`처럼 부모 걸 덮어쓴 함수가 있는가 하면, `help()`처럼 **자식이 새로 추가한 자체 서비스 함수**도 있을 수 있다. 문제는 겉보기엔 둘 다 똑같은 인스턴스 메소드라서, **객체를 들여다볼 때 이게 오버라이드 함수인지 자체 서비스 함수인지 구분이 안 된다**는 것이다. 매번 부모 클래스를 뒤져서 같은 시그니처가 있는지 대조해봐야 알 수 있다면 너무 번거롭다.

자바에는 객체나 클래스를 통해 **그 클래스 정보를 코드로 읽어들이는 방법**이 있다(`getDeclaredMethods()` 등 — 클래스가 직접 선언한 메소드만 가져올 수 있다). 라이브러리를 만들 때 이런 정보를 활용해 "이 메소드가 오버라이드된 것인지"를 조건 처리하고 싶을 수 있는데, 그러려면 코드 자체에 "이건 오버라이드다"라는 표식이 남아있어야 한다.

이 표식이 바로 `@Override`다. `//` 같은 일반 주석은 **사람이 읽으라고** 남기는 것이지만, `@`로 시작하는 **어노테이션**은 **런타임에 코드가 읽어들일 수 있는, 실행 중에 해석 가능한 주석(메타데이터)**이다. `@Override`는 "이 메소드는 부모의 것을 덮어쓴 것이다"라는 안내문 역할을 한다.

## 4. `total()`을 다시 구현하는 과정에서 겪는 문제들

**문제 1 — `this.kor`이 안 보인다**

```java
@Override
public int total() {
    return this.kor + this.eng + this.math + this.com; // kor, eng, math에 빨간 줄
}
```

`kor`/`eng`/`math`는 부모 `Exam`에서 `private`으로 캡슐 은닉되어 있다. **부모-자식 관계라고 해도 `private` 필드는 자식조차 직접 건드릴 수 없다** — `private`은 "이 클래스 자신 외에는 아무도 못 쓴다"는 뜻이지, "자식은 예외"가 아니다. 그래서 `this.getKor()`처럼 부모가 공개해둔 게터로 값을 가져와야 한다.

**문제 2 — 굳이 국영수를 다시 더할 필요가 있을까?**

부모의 `total()`은 이미 국영수를 더하는 로직을 갖고 있다. 굳이 자식이 그 계산을 처음부터 다시 짤 필요 없이, **부모의 계산 결과를 그대로 가져다 쓰고 `com`만 더하면** 된다.

```java
@Override
public int total() {
    return this.total() + this.com;
}
```

**문제 3 — `this.total()`을 쓰면 무한루프에 빠진다**

`this`가 가리키는 객체는 `MyExam` 인스턴스이므로, `this.total()`을 부르면 **다형성(동적 바인딩)에 의해 다시 `MyExam`이 오버라이드한 `total()`이 호출된다.** 자기 자신을 계속 호출하는 셈이라 무한루프가 된다.

**해결 — `super` 키워드**

자식 객체는 사실 **두 개의 객체가 합쳐진 형태**다. 부모 부분이 먼저 만들어지고, 그 위에 자식이 확장한 영역이 얹히는 구조다. `this`가 "현재 객체 전체"를 가리킨다면, **`super`는 그 안에 온전히 들어있는 부모 객체 부분만 가리키는 키워드**다.

```java
@Override
public int total() {
    return super.total() + this.com; // 부모의 total()을 명시적으로 호출
}
```

`super.total()`은 `Exam` 형식으로 명시적으로 부모의 `total()`을 호출하므로, `MyExam`이 오버라이드한 버전이 아니라 **진짜 부모의 원래 계산식**이 실행된다. 무한루프 없이 국영수 + 컴퓨터를 정확히 계산할 수 있다.

> 참고로, 만약 오버라이드를 아예 하지 않았다면 `total()`을 호출했을 때 자연스럽게 부모의 `total()`이 호출된다 — `MyExam` 안에는 `Exam`이 온전한 객체로 들어있으니, `Exam`의 `total()`을 참조하는 게 당연히 가능하다.

## 5. 생성자에서 국영수를 초기화하는 문제 — `super(...)`

`kor`/`eng`/`math`는 부모의 것이니, 자식 생성자 안에서 `this.kor = kor;`처럼 직접 초기화할 수 없다(역시 `private`). 그렇다고 이 값들을 초기화해줄 방법이 없는 것도 아니다 — **부모의 생성자를 그대로 호출하면 된다.**

```java
public MyExam(int kor, int eng, int math, int com) {
    super(kor, eng, math); // 부모의 생성자 호출
    this.com = com;
}
```

`super(kor, eng, math)`는 "갓 태어난 `Exam` 객체"가 자기 생성자를 호출하는 것과 같다. `this` 안에 부모가 통째로 들어있다는 걸 떠올리면, `super(...)`로 그 부모 부분을 초기화하는 게 자연스럽다.

**왜 반드시 생성자의 첫 줄이어야 하는가**

```java
public MyExam(int kor, int eng, int math, int com) {
    this.com = com;
    super(kor, eng, math);
}
```

`super(...)`를 첫 줄이 아닌 곳으로 내리면 에러가 난다. 이유는, `super(...)`를 부르기 전에 이 객체가 "갓 태어난 상태"가 아니게 되기 때문이다 — 이미 `this.com = com;`이라는 연산을 거친 객체에 부모 생성자를 나중에 갖다 붙이는 건 허용되지 않는다. **부모 부분이 먼저 완전히 만들어져야, 그 위에 자식의 초기화가 이어질 수 있다.**

> 다시 한번 강조: 생성자는 함수처럼 인자를 받고 호출되지만, **이름이 없다.** `super(kor, eng, math)`도 `kor, eng, math`라는 인자를 받아 호출되는 형태이지만, "이름 있는 함수를 부르는 것"이라고 착각하면 코드가 꼬인다.

## 6. 라이브러리로 배포해도 소스는 숨겨지지 않는다 — 디컴파일

`Exam` 클래스에 커서를 놓고 **우클릭 → Go to Definition**을 하면, `.jar`로 배포되어 원본 `.java` 파일이 없는데도 **디컴파일된 코드**가 그대로 열린다. `.class`(컴파일된 바이트코드)를 다시 사람이 읽을 수 있는 `.java` 코드로 되돌린 것이다.

"소스코드를 공개하기 싫으면 컴파일해서 배포하면 된다"는 말은 **틀렸다.** 컴파일된 `.class`/`.jar`만 배포해도, 도구를 쓰면 얼마든지 디컴파일해서 원래 코드에 가까운 형태로 다시 볼 수 있다.

## 7. 종합 코드 — workspace2/my-java-app

**부모 — `Exam`(라이브러리, `examlib`)**

```java
package com.example.examlib.entity;

public class Exam {
    private int kor;
    private int eng;
    private int math;

    public Exam() {
        this(50, 50, 50);
    }

    public Exam(int kor, int eng, int math) {
        this.init(kor, eng, math);
    }

    private void init(int kor, int eng, int math) {
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

**자식 — `MyExam`(라이브러리를 IS-A로 확장)**

```java
import com.example.examlib.entity.Exam;

public class MyExam extends Exam {

    private int com;

    public MyExam() {
        this(50, 50, 50, 50);
    }

    // 부모 클래스의 생성자를 이용
    public MyExam(int kor, int eng, int math, int com) {
        super(kor, eng, math);
        this.com = com;
    }

    public int getCom() {
        return com;
    }

    public void setCom(int com) {
        this.com = com;
    }

    @Override
    public int total() {
        return super.total() + com;
    }
}
```

**사용 — `App`**

```java
public class App {
    public static void main(String[] args) {
        MyExam exam = new MyExam(10, 10, 10, 10);

        System.out.println("총점: " + exam.total());
        System.out.println("평균: " + exam.avg());
    }
}
```

`exam.total()`은 `super.total()`(국영수 30) + `com`(10)으로 **40**이 나온다.

`exam.avg()`는 `Exam`이 물려준 `avg()`가 그대로 실행되지만, 그 내부에서 부르는 `total()`은 `MyExam`이 오버라이드한 버전이므로 40을 3으로 나눈 값이 나온다.

**비유 — 스마트폰과 업그레이드된 신형 스마트폰**

- **부모 클래스(`Exam`)**: 기본 스마트폰 설계도다. 국어/영어/수학 점수로 계산하는 "기본 총점" 기능이 들어있다.
- **자식 클래스(`MyExam`)**: 기본 스마트폰을 물려받아 컴퓨터(`com`) 과목을 추가한 "신형 스마트폰" 설계도다.
- **`App.java`**: 실제 스마트폰을 매장에서 하나 구매하는 곳이다.

```java
MyExam exam = new MyExam(...);
```

이건 "실체(알맹이)가 신형 스마트폰(`MyExam`)인 제품을 만들었다"는 뜻이다.

**`this`의 진짜 의미 — "지금 이 일을 하고 있는 진짜 나"**

`Exam` 클래스의 `avg()` 메서드 안을 보면 (정확히는 `total()`을) `this.total()`처럼 부르고 있다. 여기서 `this`는 "내가 적혀있는 설계도(클래스) 이름"을 뜻하는 게 아니라, **"지금 현재 실제로 메모리에 만들어진 객체(진짜 알맹이)"**를 가리킨다.

`App.java`에서 `exam.avg()`를 호출하면, 실체 알맹이는 신형 스마트폰(`MyExam`)이다. 비록 `avg()`라는 기능 자체는 부모(`Exam`)로부터 물려받아 실행되지만, 실행되는 순간 `avg()` 안에 있는 `this`는 **"지금 나(신형 스마트폰)"**를 바라보게 된다. 따라서 `this.total()`을 부를 때, 신형 스마트폰(`MyExam`)에서 재정의(오버라이딩)한 `total()` 기능이 우선순위로 작동한다.

**왜 이렇게 만들었을까 — 다양한 동작(다형성)**

자바는 부모가 만들어둔 `avg()`(총점 / 3.0)라는 큰 틀의 계산 공식을 자식들이 그대로 재사용하되, 만약 자식이 자기만의 총점 계산 방식(`total()`)을 덮어씌웠다면(`@Override`), 부모의 공식을 실행할 때도 **자식이 새로 만든 총점을 반영**하도록 설계되어 있다.

