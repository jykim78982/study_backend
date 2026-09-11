---
tags: [자바, 추상클래스, 캡슐화, protected, 템플릿메소드]
---

> 🔗 관련 노트: [[030_다형성과 추상 클래스, Object]] · [[029_오버라이드와 super, 생성자 체이닝]] · [[023_전역변수와 캡슐화, 객체지향의 역할 개념]]

# 추상 클래스의 존재 이유와 protected

## 1. 추상 클래스는 분석해서 나온 클래스인가?

업무를 분석하다 보면 자연스럽게 등장하는 클래스가 있고, 그렇지 않은 클래스도 있다.

- **분석에서 나온 클래스**: `Line`, `Circle`, `Rect` — 실제로 그려야 할 대상이니 업무 분석 과정에서 자연스럽게 드러난다
- **분석에서 나온 게 아닌 클래스**: `Shape` — "선을 그려주세요", "원을 그려주세요"라는 요구는 있어도 "Shape를 그려주세요"라는 요구는 없다

**즉 추상 클래스는 업무 분석의 결과물이 아니라, 구체화된 자식 클래스들을 일괄 관리하기 위해 나중에 필요에 의해 만들어내는 부가적인 클래스다.** 공통 자료형(공통 코드를 모아 놓을 공간)이 필요해서 생겨난다.

## 2. 추상 클래스는 객체화될 수 없다

```java
Shape s = new Shape(); // 이렇게 쓰면 안 된다
```

추상 클래스는 오로지 **자식 클래스를 통해서만** 객체화될 수 있다. 그런데 클래스 형태로 눈에 보이기 때문에 사람들이 자꾸 직접 `new`로 만들려고 한다.

이걸 막는 키워드가 **`abstract`**다.

```java
abstract class Shape { ... }
```

클래스 앞에 `abstract`를 붙이면, 그 클래스를 직접 `new`로 객체화하려는 순간 **컴파일러가 막아준다**(컴파일 오류). `abstract` 키워드가 없어도 개념적으로는 추상 클래스일 수 있지만, 그 경우 컴파일러가 막아주지 않으므로 실수로 객체화하는 걸 방지하려면 `abstract`를 붙여야 한다.

## 3. 추상화란 무엇인가 — 다시 정리

**추상화**란:

- 여러 타입의 객체를 **일괄 관리**하기 위해 묶는 것
- 일괄 관리가 가능하도록, 구체화된 객체들의 **공통 자료형**을 만드는 것
- 공통 자료형을 만들다 보면 부수적으로 **중복 코드를 한곳에 모으는 효과**(집중화)도 생긴다.

## 4. `Object`도 일괄 관리용인데, 왜 또 추상 클래스를 만드나?

`Object`는 자바 세상에서 사용하는 추상화의 끝판왕이다. `Object` 역시 **일괄 관리를 위한 목적**으로 만들어진 게 맞다.

그럼 "일괄 관리"라는 문제는 `Object` 하나로 이미 해결된 것 아닌가? 왜 굳이 `Shape` 같은 걸 또 만드는가?

**이유: 형변환이 번거롭기 때문이다.**

```java
Object[] list = new Object[3];
list[0] = new String("hello");
list[1] = new Circle();
list[2] = new Line();

if (list[1] instanceof Circle) {
    ((Circle) list[1]).draw();
} else if (list[1] instanceof Line) {
    ((Line) list[1]).draw();
}
// ... 형식이 늘어날수록 분기도 계속 늘어난다
```

`Object`로 꺼낸 객체를 실제로 쓰려면:

1. 지금 꺼낸 게 무슨 형인지 알아야 하고 (`instanceof`로 "너 이 형식이야?" 확인)
2. 형식을 조건문으로 하나하나 비교해야 하고
3. 잘못 캐스팅하면 형변환 오류가 터진다

즉 `Object`로 묶어버리면 참조는 일괄로 가능해도, **기능을 쓰려는 순간 다시 형식을 따지는 부담**이 생긴다. 그래서 기능을 실제로 써야 하는 상황이라면 `Object`는 쓰기 어렵다.

## 5. 공통 자료형(`Shape`)을 만들면 형변환 없이 쓸 수 있다

참조 타입을 `Shape`로 선언해서 쓰면, `Shape`가 `draw()`를 이미 공통으로 갖고 있기 때문에 형변환 없이 곧바로 `draw()`를 호출할 수 있다.

```java
Shape line = new Line();
line.draw();

Shape circle = new Circle();
circle.draw();

Shape rect = new Rect();
rect.draw();
```

이렇게 따로따로 다뤄도 각자 잘 동작한다. 하지만 도형이 몇 개가 될지 모르고, 여러 개를 순서대로 관리해야 한다면 매번 변수를 따로 선언해서 개별 호출하는 방식은 감당이 안 된다. 이럴 때는 `Shape` 타입 하나로 여러 도형을 배열에 묶어서 일괄 관리하면 된다 — 이때도 참조 타입이 이미 `Shape`이므로 형변환은 여전히 필요 없다.

여기서 흔한 오해: "그럼 `Line`, `Circle`, `Rect`가 전부 같은 기능을 가져야 하는 거 아니야?"

**아니다.** 일괄 관리를 한다는 건 모든 객체가 완전히 똑같은 기능을 가지라는 뜻이 아니라, **같은 기능(예: `draw()`)에 대해서만 일괄로 관리하겠다**는 뜻이다. 아래처럼 **배열 하나로 묶어서 일괄 관리**한다.

```java
Shape[] shapes = new Shape[3];
shapes[0] = new Line();
shapes[1] = new Circle();
shapes[2] = new Rect();

for (int i = 0; i < shapes.length; i++) {
    Shape s = shapes[i]; // 매 바퀴마다 원소 하나를 s에 대입
    s.draw();
}

// 위 for문과 완전히 같은 동작을 하는 축약형(향상된 for문)
// for (Shape s : shapes) {
//     s.draw(); // draw()라는 공통 기능만 일괄 호출
// }
```

여기서 헷갈리기 쉬운 부분이 있다. `for (Shape s : shapes)`의 `s`는 어디까지나 **참조 타입**이 `Shape`일 뿐이지, `s`가 가리키는 **실제 객체**가 `Shape` 자신인 건 아니다. `Shape`는 `abstract`이므로 애초에 `Shape` 그 자체의 객체는 존재할 수 없다 — `shapes` 배열에 들어갈 수 있는 건 `new Line()`, `new Circle()`, `new Rect()`처럼 항상 **구체화된 자식 객체**뿐이다.

즉 반복문을 한 바퀴 돌 때마다 `s`가 가리키는 실제 객체는 계속 바뀐다. 첫 번째 바퀴에서 `s`는 `Line` 객체를 가리키고 있으므로 `s.draw()`는 `Line.draw()`가 실행되고, 두 번째 바퀴에서는 `Circle` 객체를 가리키므로 `Circle.draw()`가 실행되는 식이다. `s`라는 참조 변수 하나로 서로 다른 세 개의 객체를 순서대로 다루면서도, 그때그때 **실제 객체(`s`가 가리키는 진짜 자식)에 맞는 `draw()`가 실행**된다 — 이전에 다룬 "참조형보다 객체형(실제 객체)이 우선한다"는 다형성 규칙이 여기서 그대로 적용되는 것이다.

정리하면 다음 둘은 전혀 다른 이야기다.

- `Shape s = new Shape();` → **금지**. 추상 클래스인 `Shape` 자신을 직접 객체화하려는 시도다
- `Shape s = new Circle();`처럼 자식 객체를 `Shape` 타입으로 참조하는 것 → **정상**. 참조만 `Shape`로 일괄화했을 뿐, 실제 객체는 항상 구체적인 자식이다

## 6. `Object`를 쓰는 게 좋은가, 피해야 하는가?

경우에 따라 다르다.

- **기능은 쓰지 않고 참조(보관)만 하는 관리**라면 `Object`로 충분하고 오히려 좋은 방법이다
- **기능을 실제로 호출해서 써야 한다면** `Object`는 지양하고, 필요한 범위로 좁힌 전용 추상 클래스를 쓰는 게 낫다

## 7. `Shape s = new Shape(); s.draw();` — 두 가지가 동시에 잘못됐다

```java
Shape s = new Shape();
s.draw();
```

이 두 줄은 각각 다른 이유로 잘못됐다.

- **1번째 줄**: 추상 클래스를 직접 객체화했다 (앞서 2장에서 다룬 문제)
- **2번째 줄**: 구현이 없는 공통 메소드를 호출했다

`Shape`의 `draw()`는 애초에 "쓰라고" 만든 게 아니라 **"자식이 구현하라고" 비워둔 자리**다. 그래서 `draw()` 자체도 직접 호출하지 못하게 막아야 한다.

**해결책**

1. `Line`, `Circle`, `Rect`가 `extends Shape`로 부모-자식 관계를 맺는다 — 객체는 자식으로 만들지만, 참조는 `Shape`로 해서 일괄 관리한다
2. 클래스에 `abstract`를 붙여 `Shape` 객체 생성 자체를 막는다
3. `draw()` 메소드 앞에도 `abstract`를 붙이고 중괄호(구현부)를 아예 지워서, 직접 호출도 불가능하게 만든다

```java
public abstract class Shape {
    // 자식이 구현하게 한다.
    public abstract void draw();
}
```

**주의**: 클래스 안에 `abstract` 메소드가 하나라도 있으면, 그 클래스도 **반드시 `abstract`로 지정해야 한다.** 메소드만 골라서 못 쓰게 하고 클래스는 일반 클래스로 두는 건 불가능하다 — 직접 쓰면 안 되는 메소드가 있는 클래스라면, 그 클래스 자체가 이미 추상 클래스일 수밖에 없기 때문이다.

## 8. `protected` — 자식에게만 공개하는 보호 모드

`Shape`의 실제 필드는 이렇게 되어 있다.

```java
public abstract class Shape {
    private int x;
    private int y;

    public abstract void draw();
}
```

그런데 자식 클래스들은 `x`, `y`를 직접 쓰려고 한다.

```java
public class Circle extends Shape {
    private int radius;

    public void draw() {
        // x, y가 private이라 여기서 직접 접근하면 컴파일 오류
        System.out.printf("원을 (%d, %d)에 (%d)크기로 그리기", x, y, radius);
    }
}
```

`x`, `y`가 `private`이면 자식도 접근할 수 없다. 이때 등장하는 게 **`protected`**다.

- `protected`는 외부 클래스 입장에서는 `private`처럼 막혀 있다
- 하지만 **자식 클래스에게는 `public`처럼 공개**된다
- 즉 수직 방향(부모→자식)으로만 열어주는 보호 모드다

**그럼 그냥 `x`, `y`도 `protected`로 열어주면 되지 않나?**

- 자식들에게 필드를 직접 공개하면, 나중에 문제가 생겼을 때 그게 자식 어디에서 건드린 건지 추적하기 어려워진다
- 그래서 필드는 여전히 `private`으로 감추고, **게터/세터**를 통해서만 접근하게 하는 편이 안전하다

**"속성을 바꿀 일이 있나?"**

- 필드 이름 자체를 바꾸는 일은 드물다
- 하지만 `x`, `y`처럼 흩어진 값을 나중에 `Point` 객체 하나로 묶어 정리하는 것("방 정리")처럼, 객체가 복잡해지면 **내부 구조를 재구성하는 일은 흔하다**
- 이때 게터/세터만 그대로 유지한 채 내부 구현만 바꾸면, 외부(자식 포함)에는 영향이 없다 — 내부 구조가 어떻게 바뀌든 외부는 게터/세터라는 창구만 보고 있으면 되기 때문이다

`draw()`처럼 모두에게 공개할 공통 서비스는 `public`이면 되지만, **자식에게만 노출해야 하는 경우**도 있다. 그 경우가 다음 장의 `onSave()`다.

## 9. 공통 로직 + 부분 위임 — `save()`와 `onSave()`

`draw()`는 자식마다 구현이 완전히 다르므로 통째로 `abstract`로 넘겼다. 그런데 **"저장" 기능**은 조금 다르다.

- 파일을 열고, 스트림을 만들고, 예외를 처리하고, 스트림을 닫는 과정은 `Line`, `Circle`, `Rect` 모두 **똑같다**
- 다만 **실제로 어떤 데이터를 저장할지**(선은 좌표 4개, 원은 좌표+반지름 등)만 자식마다 다르다

이럴 때 전체를 `abstract`로 넘겨버리면 자식들이 똑같은 파일 처리 코드를 매번 중복해서 작성하게 된다. 그래서 **공통된 부분은 `Shape`가 갖고, 차이 나는 부분만 자식에게 위임**한다.

```java
public abstract class Shape {
    private int x;
    private int y;

    // 공통된 부분은 추상 클래스가 만든다
    public void save() {
        File file = new File("file.data");
        try {
            FileOutputStream fos = new FileOutputStream(file);
            PrintStream out = new PrintStream(fos);

            // onSave를 호출하면 자식 클래스에서 오버라이드 한 메소드가 호출된다
            onSave(out);

            out.close();
            try {
                fos.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
    }

    // 자식에게 구현을 위탁하는 목적의 메소드
    // 메소드를 protected로 하면 자식만 onSave에 접근 할 수 있다
    protected void onSave(PrintStream out) {
    }
}
```

```java
public class Line extends Shape {
    private int dx;
    private int dy;

    public void onSave(PrintStream out) {
        out.printf("{%d, %d, %d, %d}\n", x, y, dx, dy);
    }
}
```

`save()`를 호출하면 파일을 열고 닫는 공통 절차는 그대로 진행되다가, 중간의 `onSave(out)` 부분에서 **실제 실행되는 건 자식이 오버라이드한 코드**다. 자식은 "무엇을 저장할지"만 채워 넣으면 되고, 파일 처리 절차 자체는 신경 쓸 필요가 없다.

## 10. `onSave`는 왜 `private`도 `public`도 아닌 `protected`인가?

**질문**: 부모의 메소드가 `private`이면, 자식이 같은 이름으로 다시 만든 게 오버라이드일까?

**아니다.** 오버라이드는 **부모가 노출하고 있는 것을 자식이 덮어쓰는 것**인데, `private`은 애초에 자식에게조차 노출되지 않는다. 그래서 자식에서 같은 이름의 메소드를 만들어도 그건 오버라이드가 아니라 **부모와 무관한 별개의 메소드**가 된다.

**그럼 오버라이드가 되게 `public`으로 하면?** — 이번엔 반대 문제가 생긴다. `onSave()`는 `save()` 내부에서만 호출되도록 의도된 메소드이지, 외부에서 직접 `shape.onSave(...)`처럼 호출하라고 만든 게 아니다. `public`으로 열면 이 의도치 않은 외부 호출을 막을 수 없다.

**그래서 `protected`가 필요하다.**

- 외부에는 노출되지 않는다 (`private`처럼)
- 자식에서는 오버라이드가 가능하다 (`public`처럼, 단 수직 방향으로만)

`draw()`처럼 누구나 호출해도 되는 진짜 "서비스"는 `public abstract`로, `onSave()`처럼 부모 내부에서만 호출되고 구현만 자식에게 위탁하는 메소드는 `protected`로 — 이렇게 접근 제어자가 메소드의 **역할과 의도**를 코드로 드러낸다.

