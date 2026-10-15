---
tags: [스프링부트, AOP, 프록시, DynamicProxy, InvocationHandler, 리플렉션, 횡단관심사, 참고자료]
---

> 🔗 관련 노트: [[091_AOP와 프록시 — 곁다리 코드를 호출 흐름 밖으로 빼는 방법]] · [[089_AOP 입문 — 객체지향 위에 얹는 관점 지향과 곁다리 업무]] · [[028_AOP — 핵심 로직과 공통 부가 기능을 분리하는 관점 지향 프로그래밍 참고자료]]

# AOP의 원리와 JDK Proxy 기반 구현

## 오늘 배울 것

AOP(Aspect-Oriented Programming, 관점 지향 프로그래밍)는 **횡단 관심사를 비즈니스 로직에서 분리하여 일괄 처리**하는 프로그래밍 방식이다. 이 자료에서는 AOP가 무엇인지, 왜 필요한지, 그리고 Java의 `java.lang.reflect.Proxy`를 사용하면 실제로 코드가 어떻게 달라지는지를 살펴본다.

## 1. AOP(Aspect-Oriented Programming)는 무엇인가?

AOP는 업무를 처리하는 코드 외에 **추가적으로 결합되어야 할 코드를 쉽게 작성하기 위한 방법론**을 말한다.

### 1-1. Aspect란?

Aspect는 **바라보는 관점**을 말한다.

```
                ┌───────────────────────────┐
                │  (Aspect 코드)            │ ◀━━ 개발자
   사용자 ━━━▶  │   ┌───────────────────┐   │
                │   │   주 업무 로직     │   │ ◀━━ 운영자
                │   └───────────────────┘   │
                └───────────────────────────┘
```

사용자는 **주 업무 로직**을 요구하고, 개발자와 운영자는 그 바깥을 둘러싸는 코드를 덧붙인다.

응용 프로그램을 만들 때 가장 중요한 기능은 **고객이 원하는 기능**이다. 하지만 그런 기능을 구현하다 보면 **고객이 주문하지 않은 코드**를 포함시켜야 할 때가 있다.

예를 들어 로그 기록, 보안 확인, 처리 시간 측정 등을 위한 코드 말이다. 이런 코드는 고객이 원했던 기능, 즉 **Core Concern**이 아니다.

고객 외에 **개발자나 운영자**가 필요로 하는 기능이 추가될 수 있다. 이런 목적의 코드를 **Aspect 코드**라고 한다.

> **보충 — 용어의 쓰임**: 이 자료에서 "Aspect 코드"는 주 업무 바깥의 관점에서 덧붙는 코드 전체를 가리킨다. AspectJ나 Spring AOP 같은 도구에서 `Aspect`는 좀 더 좁게, **부가 기능 코드(Advice)와 그것을 어디에 적용할지(Pointcut)를 묶은 모듈**을 뜻한다. 스프링에서 `@Aspect`를 붙인 클래스가 그것이다.

### 1-2. AOP가 왜 필요한가?

모든 Aspect 코드는 Core Concern에 해당하는 고객의 기능에 **붙어서 기생**한다.

예를 들어 고객이 `주문()`, `결제()` 등의 기능을 요구했다면, 그것을 구현할 때 Aspect 코드가 붙여진다. 결코 독립적으로 존재하는 코드가 아니다. 고객을 위한 기능을 구현하면서, 그것의 실행 시간, 로그 등을 확인하기 위해 추가되는 코드이다.

좀 더 구체적인 예를 들어 보자.

고객이 계산기 프로그램을 만들어 달라고 했고, 성능을 우선순위에 두었다고 하자.

그러면 고객이 요구한 것은 아니지만, 그것을 구현하려면 계산 과정에서 시간을 얼마나 사용하는지 체크하는 코드가 필요할 수 있다. 이것은 고객이 요구한 기능(Core Concern)이 아니다. **개발자의 관점**에서 필요한 기능이다.

그러면 코드는 고객이 원하는 기능에 개발자에게 필요한 코드가 덧붙여진 상태로 만들어진다.

```java
public class CalculatorImpl implements Calculator {
    private int x;
    private int y;

    public CalculatorImpl(int x, int y){
        this.x = x;
        this.y = y;
    }

    @Override
    public int add(){
        // 덧붙여진 상단 코드
        long start = System.currentTimeMillis();

        //-- 업무로직(Core Concern)--------------------------
        // 일부러 시간이 오래 걸리게 하는 시뮬레이션 코드
        try {
            // 시뮬레이션: 실제 계산보다 오래 걸리는 것처럼 보이게 하기 위해 랜덤한 슬립을 삽입
            Thread.sleep((long) (Math.random() * 1000));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        int result = x + y;

        // -----------------------------------------------
        // 덧붙여진 하단 코드
        long end = System.currentTimeMillis();
        System.out.println("add() 소요 시간: " + (end - start) + "ms");
        return result;
    }

    @Override
    public int sub(){
        // 덧붙여진 상단 코드
        long start = System.currentTimeMillis();

        //-- 업무로직(Core Concern)--------------------------
        // 일부러 시간이 오래 걸리게 하는 시뮬레이션 코드
        try {
            Thread.sleep((long) (Math.random() * 1000));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        int result = x - y;

        // -----------------------------------------------
        // 덧붙여진 하단 코드
        long end = System.currentTimeMillis();
        System.out.println("sub() 소요 시간: " + (end - start) + "ms");
        return result;
    }
}
```

> 원본 자료에서는 `add()`의 하단 코드도 `"sub() 소요 시간"`을 출력한다. `sub()`의 코드를 복사해 붙여 넣으면서 메서드 이름을 고치지 않은 것이다. 위에서는 `"add() 소요 시간"`으로 고쳤다. 공교롭게도 이 실수 자체가 **같은 코드를 메서드마다 복사해 넣을 때 생기는 문제**를 그대로 보여준다. 2-2의 프록시 방식에서는 `method.getName()`으로 이름을 자동으로 넣기 때문에 이런 실수가 생기지 않는다.

> **보충 — `Thread.currentThread().interrupt()`를 쓰는 이유**: `Thread.sleep()` 중에 다른 스레드가 이 스레드를 중단(interrupt)시키면 `InterruptedException`이 발생하고, 그 순간 스레드의 "중단됨" 표시가 지워진다. `catch`에서 아무것도 하지 않으면 중단 요청이 사라져 버리므로, `interrupt()`를 다시 호출해 표시를 되살려 두는 것이 관례다.

문제는 이렇게 덧붙여진 코드는 **제품을 납품할 때는 모두 지워야 한다**는 점이다.

그래서 이런 종류의 코드 블록을 **쉽게 붙이고 쉽게 떼어낼 수 있는 방법**이 필요하게 되었고, 그 방법론이 바로 AOP이다.

> **보충 — 지우지 않는 Aspect 코드도 있다**: 처리 시간 측정처럼 테스트용으로 잠깐 붙이는 코드도 있지만, 트랜잭션 처리나 보안 확인처럼 **운영 중에도 계속 있어야 하는** Aspect 코드도 있다. 이런 코드도 모든 메서드에 같은 코드가 반복된다는 문제는 똑같다. AOP는 "쉽게 떼어내기"뿐 아니라 **반복되는 코드를 한 곳에 모아 관리하는 것**에도 목적이 있다. 스프링의 `@Transactional`이 그 예다.

### 1-3. Cross Cutting Concern이란?

앞에서 Aspect는 관점이라고 했다. 고객의 관점으로 만들어진 코드는 **Core Concern**이라고 한다. 반면에 고객의 관심이 아닌 **다른 사람의 관점으로 추가된 코드**, 즉 Aspect 코드를 **Cross Cutting Concern**이라고 한다.

```
   실행 흐름 (위 → 아래)
        │
  ┌─────▼──────────────────┐
  │ ━━━━━━━━━━━━━━━━━━━━━━ │ ← Aspect 코드 (start 기록)   ┐
  │                        │                               │ 흐름을 가로질러(Cross)
  │     업무 로직          │ ← Core Concern                │ 잘라낸다(Cutting)
  │        │               │                               │
  │ ━━━━━━━▼━━━━━━━━━━━━━━ │ ← Aspect 코드 (end 기록·출력) ┘
  └────────────────────────┘
```

그 이유는 위 그림에서 보듯이, Aspect 코드는 업무 로직(Core Concern)의 위쪽이나 아래쪽, 또는 위·아래 양쪽에 위치하며, **붙이거나 떼어낼 수 있는** 코드여야 하기 때문이다. 이때 잘라내는 코드는 실행 흐름(위에서 아래)을 기준으로 보면 **가로(Cross) 방향으로 잘라내야** 하는 코드라는 것을 알 수 있다. AOP에서 Aspect 코드는 이렇게 크로스 방향으로 잘라내는(Cross Cutting) 기능(Concern)을 말하기 때문에 **Cross Cutting Concern**이라고 한다.

> **보충 — 다른 이름들**: Core Concern은 **핵심 관심사·핵심 기능**, Cross Cutting Concern은 **횡단 관심사·부가 기능·공통 기능**이라고도 한다. "횡단(橫斷)"이 바로 "가로로 자른다"는 뜻이다. 여러 클래스와 메서드를 **가로질러** 똑같이 필요한 관심사라는 의미도 함께 담고 있다.

## 2. AOP에서 Aspect를 구현하는 방법은?

AOP를 적용하면 비즈니스 로직에 Aspect 코드를 함께 담지 않는다. 이 코드를 분리해서, Aspect 코드를 Cross로 Cutting해 **한 번만 작성**하고, 그것으로 이전과 동일한 효과를 낼 수 있도록 만든다.

```
                    ┌─── Proxy ──────────────┐          ┌─── 실제 객체 ───────┐
                    │ ━━━━━ (start 기록) ━━━ │          │                     │
  기능 호출  ━━━━━▶ │          │             │ ━━━━━━▶  │   업무 로직 (add)   │
             ◀━━━━━ │          ▼             │ ◀━━━━━━  │                     │
                    │ ━━━━━ (end 기록) ━━━━━ │          │   업무 로직 (sub)   │
                    └────────────────────────┘          └─────────────────────┘
                     Cross-cutting Concern                  Core Concern
```

업무 로직 위·아래에 있던 Aspect 코드를 Cross-cutting해서, 그 코드를 **Proxy 클래스**에 담는다.

여기서 **Proxy**란 업무 로직을 가진 객체를 **흉내 내는 대리자 객체**를 말한다. 위 그림에서 호출자와 실제 객체 사이에서, 자신이 실제 객체인 것처럼 가운데서 **호출을 낚아채는** 객체가 Proxy 객체이다.

사전적으로 Proxy란 "대리"를 의미하는 용어이지만, 실제로는 무엇인가를 **속인다**는 느낌도 같이 있다.

사실 프록시라는 용어는 다양한 곳에서 사용하는 범용적인 용어이다. 예를 들어 "웹 프록시 서버"라고 한다면, 남이 볼 때는 실제 웹 서버처럼 보이지만 사실은 캐싱이나 보안을 위한 목적으로 전면에서 실제 웹 서버를 숨기는 대리자 역할을 하는 서버를 말한다. 이처럼 프록시라고 하는 것은 **원래를 숨기고 그것을 대신하는 대리자**를 말한다.

이런 구조를 가지게 되면, 업무 로직을 호출하는 호출자에게 **실제 객체(target)를 주지 않고 대리자(proxy)를 주입**시키고, 대리자를 통해서 실제 객체를 사용하게 한다. 그러면 proxy에 있는 Aspect 코드를 거쳐서 실행되기 때문에, **실행 순서는 Aspect 코드가 업무 로직과 함께 있을 때의 실행 순서와 같아진다.**

```
[AOP 이전]  호출자 → target.add() { start → 업무 로직 → end }
[AOP 이후]  호출자 → proxy.add()  { start → target.add() { 업무 로직 } → end }
                                         실행 순서는 똑같다
```

이런 방식으로 Aspect를 개발하는 방법론이 AOP이다. 이 방법론에는 반드시 **Proxy**라는 역할이 필요하다.

> **보충 — Proxy가 유일한 방법은 아니다**: 원본 자료는 "Proxy라는 역할이 필수"라고 설명하는데, 이것은 **Spring AOP**와 이 자료의 JDK Proxy 방식에 해당하는 이야기다. AOP를 구현하는 방식은 크게 두 가지다.
>
> | 방식 | 원리 | 대표 도구 |
> |---|---|---|
> | **프록시 방식** (런타임) | 실행 중에 대리 객체를 만들어 호출을 가로챈다. 원본 클래스는 그대로다 | JDK Dynamic Proxy, CGLIB, **Spring AOP** |
> | **위빙 방식** (컴파일·클래스 로딩 시점) | Aspect 코드를 원본 클래스의 바이트코드 안에 **직접 끼워 넣는다** | **AspectJ** |
>
> 위빙 방식은 프록시가 없으므로 같은 클래스 안에서 자기 메서드를 호출할 때도 Aspect가 적용되는 등 더 강력하지만, 별도의 컴파일러나 설정이 필요하다. 스프링은 간편한 프록시 방식을 기본으로 쓴다.

### 2-1. AOP를 사용하지 않던 시절의 코드

AOP를 적용하지 않은 상태에서는 시간 측정 코드가 각 메서드 안에 직접 포함된다. 아래는 `Calculator` 인터페이스와 `CalculatorImpl` 구현 클래스의 예시이다.

```java
public interface Calculator {
    int add();
    int sub();
}
```

```java
public class CalculatorImpl implements Calculator {
    private int x;
    private int y;

    public CalculatorImpl(int x, int y){
        this.x = x;
        this.y = y;
    }

    @Override
    public int add(){
        // 덧붙여진 상단 코드
        long start = System.currentTimeMillis();

        //-- 업무로직(Core Concern)--------------------------
        try {
            Thread.sleep((long) (Math.random() * 1000));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        int result = x + y;

        // -----------------------------------------------
        // 덧붙여진 하단 코드
        long end = System.currentTimeMillis();
        System.out.println("add() 소요 시간: " + (end - start) + "ms");
        return result;
    }

    @Override
    public int sub(){
        // 덧붙여진 상단 코드
        long start = System.currentTimeMillis();

        //-- 업무로직(Core Concern)--------------------------
        try {
            Thread.sleep((long) (Math.random() * 1000));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        int result = x - y;

        // -----------------------------------------------
        // 덧붙여진 하단 코드
        long end = System.currentTimeMillis();
        System.out.println("sub() 소요 시간: " + (end - start) + "ms");
        return result;
    }
}
```

위 코드에서 `add()`와 `sub()` 메서드 모두에 시간 측정 로직이 **중복**되어 있다. 문제는 이 코드가 테스트가 끝나면 모두 지워야 할 코드이며, 또 나중에 필요하면 다시 붙여 넣어야 할 코드일 수도 있다는 점이다.

> **보충 — 왜 인터페이스가 있어야 하나**: 2-2에서 쓰는 JDK 동적 프록시는 **인터페이스를 흉내 내는** 방식이라, 원본 클래스가 반드시 인터페이스를 구현하고 있어야 한다. 그래서 계산기의 기능을 `Calculator` 인터페이스로 먼저 약속해 두었다. 사용하는 쪽도 `CalculatorImpl`이 아니라 `Calculator` 타입으로 참조해야, 원본 대신 프록시를 넣어도 코드가 그대로 동작한다.

### 2-2. AOP를 적용한 후의 코드

AOP를 적용하면 시간 측정 로직은 `CalculatorImpl`에서 분리되어 `CalculatorPfProxy`라는 프록시 클래스로 이동한다. `CalculatorPfProxy`는 `java.lang.reflect.Proxy`와 `InvocationHandler`를 사용하여 **동적 프록시**를 생성한다.

먼저 `CalculatorImpl`에서는 시간 측정 코드를 걷어내 **업무 로직만** 남긴다.

```java
public class CalculatorImpl implements Calculator {
    private int x;
    private int y;

    public CalculatorImpl(int x, int y){
        this.x = x;
        this.y = y;
    }

    @Override
    public int add(){
        try {
            Thread.sleep((long) (Math.random() * 1000));   // 시뮬레이션
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return x + y;
    }

    @Override
    public int sub(){
        try {
            Thread.sleep((long) (Math.random() * 1000));   // 시뮬레이션
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return x - y;
    }
}
```

> 원본 자료는 2-2에서 프록시 클래스만 보여 주고, 시간 측정 코드를 걷어낸 `CalculatorImpl`은 보여 주지 않는다. 2-1의 `CalculatorImpl`을 그대로 둔 채 프록시를 씌우면 **시간이 두 번씩 출력**되므로, 위처럼 업무 로직만 남긴 버전을 추가했다.

그리고 걷어낸 시간 측정 코드는 프록시 클래스 **한 곳**에 담는다.

```java
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

public class CalculatorPfProxy {

    public static Calculator newProxyInstance(Calculator target){
        InvocationHandler handler = new InvocationHandler() {
            @Override
            public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
                long start = System.currentTimeMillis();
                // --- 업무로직(Core Concern)을 호출하는 코드 ----------------------
                Object result = method.invoke(target, args);
                // -----------------------------------------------------------
                long end = System.currentTimeMillis();
                System.out.println(method.getName() + "() 소요 시간: " + (end - start) + "ms");
                return result;
            }
        };

        return (Calculator) Proxy.newProxyInstance(
            target.getClass().getClassLoader(),
            target.getClass().getInterfaces(),
            handler
        );
    }
}
```

`CalculatorPfProxy`의 `invoke()` 메서드는 실제 메서드 호출 **전후에** 시간 측정 로직을 수행한다. `method.invoke(target, args)`를 통해 실제 대상 객체의 메서드를 호출하고, 그 전후의 시간을 측정하여 로그를 출력한다.

> **보충 — 코드 한 줄씩 읽기**
>
> **① `InvocationHandler` — 대리자가 할 일**
>
> 프록시의 어떤 메서드가 불리든(`add`든 `sub`든) **전부 이 `invoke()` 하나로 모인다.** 그래서 시간 측정 코드를 여기 한 번만 쓰면 모든 메서드에 적용된다.
>
> | `invoke()` 매개변수 | 의미 | `calc.add()`를 불렀을 때 |
> |---|---|---|
> | `proxy` | 프록시 자기 자신 | 거의 쓰지 않는다 |
> | `method` | **어떤 메서드가 불렸는지** (리플렉션의 `Method` 객체) | `add` 메서드 정보 |
> | `args` | 그 메서드에 넘긴 인자 | 인자가 없으므로 `null` |
>
> 핵심은 `method.invoke(target, args)`다. "불린 메서드를 **진짜 객체(`target`)에게** 같은 인자로 실행해 줘"라는 뜻이다. 실제 계산은 원본이 하고, 프록시는 그 **앞뒤에서 시간만 잰다.** 반환 타입이 `Object`인 것은 어떤 메서드의 결과든 받기 위해서이며, `int` 결과는 `Integer`로 포장되어 전달된다.
>
> **② `Proxy.newProxyInstance` — 대리자 만들기**
>
> 자바가 **실행 중에 클래스를 즉석에서 만들어** 그 객체를 돌려준다. 프록시 클래스를 직접 작성하지 않아도 되는 이유다.
>
> | 인자 | 의미 |
> |---|---|
> | `target.getClass().getClassLoader()` | 새로 만든 클래스를 메모리에 올릴 클래스 로더. 원본과 같은 것을 쓴다 |
> | `target.getClass().getInterfaces()` | 흉내 낼 인터페이스 목록 → `[Calculator]`. 자바는 이 인터페이스의 메서드를 모두 갖춘 클래스를 만들고, 각 메서드가 `handler.invoke(...)`를 부르도록 채운다 |
> | `handler` | 호출되면 할 일 (①) |
>
> 결과는 `Object`로 돌아오므로 `(Calculator)`로 형 변환한다. 두 번째 인자로 `Calculator`를 흉내 내라고 했으니 안전하다.
>
> **③ 정적 팩토리 메서드 `newProxyInstance(Calculator target)`**
>
> ①과 ②를 묶어서, 원본을 넣으면 프록시를 돌려주는 공장 역할을 한다. 매개변수가 `Calculator` 인터페이스라 이 인터페이스를 구현한 계산기라면 무엇이든 감쌀 수 있다. 익명 클래스 안에서 바깥 매개변수 `target`을 그대로 쓸 수 있는 것은, `target`이 값을 바꾸지 않는(effectively final) 변수이기 때문이다.

> **보충 — 예외가 나도 시간을 찍으려면**: 원본 메서드에서 예외가 나면 `method.invoke()`가 그 예외를 `InvocationTargetException`으로 **감싸서** 던지고, 아래의 시간 출력 줄은 실행되지 않는다. 예외가 나도 시간을 찍고, 호출한 쪽에는 원래 예외를 그대로 전달하려면 다음처럼 쓴다.
>
> ```java
> long start = System.currentTimeMillis();
> try {
>     return method.invoke(target, args);
> } catch (InvocationTargetException e) {
>     throw e.getCause();                           // 감싸진 원래 예외를 꺼내 다시 던진다
> } finally {
>     long end = System.currentTimeMillis();        // 정상이든 예외든 항상 실행
>     System.out.println(method.getName() + "() 소요 시간: " + (end - start) + "ms");
> }
> ```
>
> 감싼 예외를 그대로 두면, 호출한 쪽에서는 원래 예외 대신 `UndeclaredThrowableException` 같은 엉뚱한 예외를 받게 된다.

`App` 클래스에서는 `CalculatorImpl`을 직접 사용하지 않고, `CalculatorPfProxy`를 통해 프록시 객체를 받아 사용한다.

```java
public class App {

    public static void main(String[] args) {
        int result = 0;

        // Calculator calc = new CalculatorImpl(10, 7);
        Calculator calc = CalculatorPfProxy.newProxyInstance(new CalculatorImpl(10, 7));

        result = calc.add();
        System.out.printf("add result : %d\n", result);

        result = calc.sub();
        System.out.printf("sub result : %d\n", result);
    }
}
```

```
add() 소요 시간: 523ms
add result : 17
sub() 소요 시간: 87ms
sub result : 3
```

> 원본 자료의 `App`에는 `import org.springframework.beans.factory.annotation.Autowired;`가 있지만 쓰이지 않는다. 이 예제는 **순수 자바**만으로 프록시를 만드는 것이 목적이므로 스프링 import를 뺐다. 스프링 라이브러리가 없는 환경에서는 이 import 때문에 컴파일 오류가 난다.

`CalculatorPfProxy.newProxyInstance(target)`는 `Calculator` 인터페이스를 구현하는 프록시 객체를 반환한다. `calc.add()`를 호출하면, 실제로는 `CalculatorPfProxy`의 `invoke()` 메서드가 실행되어 시간 측정이 시작된 후 `CalculatorImpl`의 `add()` 메서드가 호출되고, 끝나면 소요 시간이 출력된다. 이를 통해 `CalculatorImpl`은 **순수한 비즈니스 로직만** 포함하게 되고, 시간 측정은 프록시에서 **일괄 처리**된다.

> 원본 자료는 이 부분에서 `calc.add(1, 2)`라고 설명하지만, `add()`는 매개변수 없이 객체의 상태(`x`, `y`)로 계산하므로 `calc.add()`가 맞다.

```
calc.add()
  → (자바가 만든 프록시 클래스의 add)
  → handler.invoke(proxy, add, null)
       start 기록
       method.invoke(target, null)  →  CalculatorImpl.add()  →  10 + 7 = 17
       end 기록, "add() 소요 시간: 523ms" 출력
       return 17
  → 17이 calc.add()의 결과로 돌아온다
```

시간 측정을 빼고 싶으면 `App`에서 주석 처리된 줄(`new CalculatorImpl(10, 7)`)을 쓰면 끝이다. `CalculatorImpl`은 한 줄도 고치지 않는다.

> **보충 — 스프링에서는 이 한 줄도 안 바꾼다**: 위 예제는 `App`에서 원본을 쓸지 프록시를 쓸지 **직접 고른다.** 스프링에서는 사용하는 쪽이 `@Autowired Calculator calc`처럼 인터페이스만 주입받고, 원본을 넣을지 프록시를 넣을지는 **DI 컨테이너가 결정**한다. 그래서 사용하는 쪽 코드는 전혀 바뀌지 않는다. `@Transactional`이 붙은 서비스를 주입받으면 실제로는 이런 프록시가 들어오고, 그 프록시의 `invoke()`에 해당하는 곳에서 트랜잭션 시작 → 원본 메서드 호출 → 커밋/롤백이 일어난다.

> **보충 — Spring AOP 용어로 다시 보기**
>
> | Spring AOP 용어 | 이 예제에서 |
> |---|---|
> | **Target** (대상 객체) | `CalculatorImpl` |
> | **Proxy** | `Proxy.newProxyInstance()`가 만든 객체 |
> | **Advice** (부가 기능 코드) | `invoke()` 안의 시간 측정 코드. 앞뒤를 감싸므로 **Around** advice |
> | **Join Point** (적용 가능한 지점) | `add()`, `sub()` 메서드 호출 |
> | **Pointcut** (어디에 적용할지) | 이 예제는 `Calculator`의 **모든** 메서드. 특정 메서드만 고르려면 `invoke()`에서 `method.getName()`으로 분기한다 |

> **보충 — 인터페이스가 없는 클래스는?**: JDK 동적 프록시는 인터페이스가 없으면 쓸 수 없다. 또 `getInterfaces()`는 그 클래스가 **직접** 구현한 인터페이스만 돌려준다. 인터페이스 없이 클래스 자체를 상속해서 프록시를 만드는 라이브러리가 **CGLIB**이며, 스프링 부트는 기본적으로 CGLIB 방식을 쓴다. 그래서 스프링에서는 인터페이스가 없는 서비스 클래스에도 `@Transactional`이 동작한다. 단, 상속으로 만들기 때문에 `final` 클래스나 `final`·`private` 메서드에는 적용되지 않는다.

## 3. 학습 내용 정리

AOP는 **횡단 관심사(Cross Cutting Concern)를 비즈니스 로직(Core Concern)에서 분리하여 일괄 처리**하는 프로그래밍 방식이다. 이를 통해 로그 기록, 보안 확인, 성능 측정 등 공통 기능이 필요한 코드를 각 메서드에 중복하여 작성하지 않고, **프록시(Proxy)를 통해 중앙 집중식으로 관리**할 수 있다.

Java에서는 `java.lang.reflect.Proxy`와 `InvocationHandler`를 활용하여 **동적 프록시**를 생성함으로써 AOP를 구현할 수 있다. 이 방식은 실제 대상 객체(Target)를 호출하는 과정에서 프록시가 개입하여 필요한 전후 처리를 수행하게 함으로써, 비즈니스 로직 클래스를 순수하게 유지하면서도 부가 기능을 효과적으로 적용할 수 있게 한다.

| 구분 | AOP 이전 | AOP 이후 (JDK Proxy) |
|---|---|---|
| 시간 측정 코드 위치 | `add()`, `sub()` 안에 각각 | `CalculatorPfProxy.invoke()` 한 곳 |
| 메서드 이름 출력 | 직접 입력 (복사 실수 가능) | `method.getName()`으로 자동 |
| 측정 끄기 | 모든 메서드를 열어 삭제·주석 | `App`에서 원본 객체를 쓰면 끝 |
| `CalculatorImpl` | 업무 로직 + 측정 코드 | **업무 로직만** |
| 필요 조건 | 없음 | 원본이 **인터페이스**를 구현해야 함 |
