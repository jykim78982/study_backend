---
tags: [자바, 기본형, 참조형, 박싱, 언박싱, 래퍼클래스, 배열, ArrayList, 제네릭]
날짜: 2026-08-15
---

> 🔗 관련 노트: [[015_배열과 참조, 메모리 구조]] · [[017_클래스 배열과 참조 공유]]

# 기본형과 참조형, 박싱/언박싱과 Object 배열, ArrayList

Workspace2에서 Boxing/Unboxing, Object 배열, 직접 만든 제네릭 리스트(`GList<T>`)를
다루면서 헷갈렸던 것들을 한 번에 정리한다. 핵심 줄기는 하나다 —
**"기본형은 원래 객체가 아닌데, 어떻게 Object 배열이나 리스트에 들어가는가?"**

## 1. 기본형 vs 참조형 — 다시 한 줄 요약

| 타입 종류 | 변수 안에 들어있는 것 | 예 |
|---|---|---|
| 기본형(primitive) 8개 | **값 그 자체** | `int`, `double`, `char`, `boolean` |
| 참조형(reference) | **주소**(실제 데이터는 힙에) | 배열, `String`, 모든 객체 |

문제는, `Object obj = ...` 처럼 **"뭐든 담을 수 있는 참조형 변수"**나
`Object[]` 배열에 **기본형 값을 넣고 싶을 때** 생긴다. 기본형은 객체가
아니라서 애초에 `Object`가 될 자격이 없다.

## 2. 래퍼(Wrapper) 클래스 — 기본형을 객체로 감싼 것

그래서 자바는 기본형 8개 하나하나에 대응하는 **객체 버전**을 만들어뒀다.

| 기본형 | 래퍼 클래스 |
|---|---|
| `int` | `Integer` |
| `double` | `Double` |
| `char` | `Character` |
| `boolean` | `Boolean` |
| ... | ... |

`Integer`는 내부에 `int` 값 하나를 필드로 갖고 있는 **평범한 클래스**다.
즉 "값 하나를 담은 상자"를 객체로 한 번 더 감싼 것 — 그래서 참조형이고,
`Object`의 자식이 될 수 있고, 컬렉션(`List` 등 참조형만 다루는 자료구조)에
들어갈 수 있다.

## 3. Boxing / Unboxing — 값을 객체로, 객체를 값으로

**Boxing**: 기본형 값 → 래퍼 객체로 포장
**Unboxing**: 래퍼 객체 → 기본형 값으로 꺼냄

### 수동(Manual) 방식

```java
int primitiveNum = 10;

// Boxing: valueOf(...)로 직접 포장
Integer boxedNum = Integer.valueOf(primitiveNum);
Object obj = boxedNum;              // 포장된 상태라 Object로 참조 가능

// Unboxing: 캐스팅 + intValue()로 직접 꺼냄
Integer castedNum = (Integer) obj;
int unboxedNum = castedNum.intValue();
```

### 자동(Auto) 방식 — 컴파일러가 대신 해줌

```java
Integer autoBoxed = 100;            // 컴파일러가 Integer.valueOf(100)으로 바꿔줌
Object obj = 200;                   // 마찬가지로 자동 Boxing

int autoUnboxed = autoBoxed;        // 컴파일러가 .intValue() 호출로 바꿔줌
int numFromObj = (Integer) obj;     // Object → Integer 캐스팅 + 자동 Unboxing
```

**Auto-boxing/Auto-unboxing은 컴파일러가 수동 방식 코드를 자동으로 끼워
넣어주는 "문법 설탕(syntactic sugar)"일 뿐**, 실행 시점에 일어나는 일은
수동 방식과 동일하다. `Integer castedNum = (Integer) obj;` 처럼 **Object에서
꺼낼 때는 반드시 원래 넣었던 타입으로 캐스팅**해야 하는 것도 그대로다.

## 4. Object 배열 — 오토박싱 덕분에 뭐든 담는 만능 배열

```java
Object[] mixedArray = new Object[3];
mixedArray[0] = "문자열(String)";   // 원래 참조형, 그대로 저장
mixedArray[1] = 10;                 // int → 자동 Boxing → Integer로 저장
mixedArray[2] = 3.14;               // double → 자동 Boxing → Double로 저장
```

`Object[]`의 각 칸에는 값이 아니라 **주소(참조)만 들어있다.**
기본형을 넣을 수 있는 것처럼 보이는 건 대입되는 순간 자동으로 Boxing되어
"래퍼 객체의 주소"로 바뀌기 때문이다. 즉 `Object[]`에는 **결국 참조만
들어간다** — 이 규칙에 예외는 없다.

```java
for (Object item : mixedArray) {
    System.out.println("타입: " + item.getClass().getSimpleName() + ", 값: " + item);
}
// 타입: String, 값: 문자열(String)
// 타입: Integer, 값: 10
// 타입: Double, 값: 3.14
```

`getClass()`로 확인해보면 `int`나 `double`이 아니라 **`Integer`, `Double`**로
찍힌다 — 배열 안에는 이미 래퍼 객체만 있다는 증거.

## 5. 흔한 함정 세 가지

### 함정 1 — 엉뚱한 타입으로 캐스팅하면 `ClassCastException`

```java
Object value = 100;               // 실제로는 Integer가 들어있음
Double doubleVal = (Double) value; // ❌ ClassCastException
```

`Object` 변수 자체는 "무슨 타입인지" 컴파일 시점엔 모른다. 실제로 들어있는
객체와 다른 타입으로 캐스팅을 시도하면 실행 시점에 예외가 터진다.

**해결책 — `instanceof` 패턴 매칭으로 먼저 확인**

```java
if (value instanceof Integer i) {   // 맞는 타입일 때만 블록 진입, i에 바로 대입까지
    int safeInt = i;
}
```

### 함정 2 — `null`을 Unboxing하면 `NullPointerException`

```java
Integer nullableInteger = null;
int primitiveVal = nullableInteger;  // ❌ NPE
```

Auto-unboxing은 내부적으로 `nullableInteger.intValue()`를 호출하는 것과
같다. 대상이 `null`이면 **메서드를 호출할 객체 자체가 없으니** NPE가
난다. 래퍼 타입 변수를 기본형에 대입하기 전에는 항상 `null` 가능성을
의심해야 한다.

### 함정 3 — 반복문 안에서 불필요한 Auto-boxing은 성능 저하

```java
// 기본형끼리 연산 — Boxing 없음, 빠름
long sum = 0L;
for (long i = 0L; i < 1_000_000; i++) {
    sum += i;
}
```

만약 `sum`이나 `i`를 `Long`(래퍼 타입)으로 선언했다면, 매 반복마다
Boxing/Unboxing이 끼어들어 **새 래퍼 객체가 계속 생성**된다. 단순 누적
연산처럼 성능이 중요한 반복문에서는 **래퍼 타입 대신 기본형을 쓰는 게
원칙** — 래퍼 타입은 "객체가 필요한 곳"(컬렉션, 제네릭, `Object` 참조)에
쓰고, 순수 계산에는 기본형을 쓴다.

## 6. 배열 vs ArrayList — 무엇이 다른가

| | 배열(`int[]`, `Exam[]`) | `ArrayList`(`List<T>`) |
|---|---|---|
| 크기 | 생성 시점에 고정, 못 바꿈 | 자동으로 늘어남 |
| 기본형 저장 | 그대로 값 저장 가능 (`int[]`) | 불가능 — 항상 래퍼로 Boxing해서 저장 (`List<Integer>`) |
| 담을 수 있는 타입 | 선언한 타입 하나로 고정 | 제네릭으로 타입 하나로 고정하되, 내부는 `Object[]` |
| 크기 늘리기 | 새 배열 만들어서 복사(직접 구현) | `add()` 호출 시 알아서 처리 |

`List<Integer>`처럼 **기본형을 담는 것처럼 보이는 제네릭도 실제로는
Integer(래퍼)를 담는다** — 자바 제네릭은 참조형만 다룰 수 있고, `int` 같은
기본형 타입 매개변수(`List<int>`)는 애초에 문법적으로 허용되지 않는다.

## 7. ArrayList는 내부적으로 Object 배열이다

직접 제네릭 리스트를 만들어보면 `ArrayList`가 왜 "크기가 자동으로 늘어나는
`Object[]`"인지 알 수 있다.

```java
public class GList<T> {
    private Object[] objs = new Object[10];   // 내부는 결국 Object 배열
    private int size = 0;

    public void add(T menu) {
        if (objs.length <= size) {
            // 꽉 차면 더 큰 배열을 새로 만들어서 옮겨 담아야 함 (ArrayList가 실제로 하는 일)
        }
        objs[size] = menu;   // T가 뭐든 결국 Object[] 칸에 참조로 저장됨
        size++;
    }

    @SuppressWarnings("unchecked")
    public T get(int i) {
        return (T) objs[i];  // 꺼낼 땐 원래 타입(T)으로 다시 캐스팅
    }
}
```

```java
List<Menu> list = new ArrayList<>();
list.add(new Menu());
list.get(0).getKorName();
```

- `add(T menu)`로 넣을 때: `Menu` 객체의 **참조**가 `Object[]` 칸에 그대로
  들어간다 (4번 섹션의 원리와 동일 — 애초에 `Menu`도 참조형이라 Boxing 불필요).
- `get(int i)`로 꺼낼 때: `Object[]`에서 꺼낸 값을 **`T`로 캐스팅**해서
  돌려준다. 이게 바로 함정 1에서 본 캐스팅과 같은 위험을 안고 있는데,
  제네릭이 컴파일 시점에 타입을 강제해주기 때문에 실제로는 잘못된 타입이
  섞여 들어올 일이 (직접 `Object[]`를 다룰 때와 달리) 거의 없다.
- `List<Integer>`에 `int` 값을 `add(3)`처럼 넣으면, 3번 섹션의 Auto-boxing이
  먼저 일어나 `Integer`로 포장된 뒤 `Object[]` 칸에 저장된다. 즉
  `ArrayList`도 결국 **"Object 배열 + 자동 Boxing/Unboxing + 자동 크기
  늘리기"**를 합쳐놓은 것일 뿐이다.

## 8. 정리 — 헷갈리는 것들을 한 표로

| 상황 | 실제 배열/칸에 들어있는 것 |
|---|---|
| `int[] nums` | 값 그 자체 (Boxing 없음) |
| `Exam[] exams` | `Exam` 객체의 참조 |
| `Object[] mixed` (기본형 대입) | 자동 Boxing된 래퍼 객체의 참조 |
| `List<Integer> list` | 내부 `Object[]`에 자동 Boxing된 `Integer` 참조 |
| `List<Menu> list` | 내부 `Object[]`에 `Menu` 참조 (Boxing 불필요, 원래 참조형) |

결국 **"기본형이 Object 계열 어딘가에 들어가려면 반드시 래퍼로 Boxing된다"**
는 규칙 하나만 기억하면, `Object[]`든 제네릭 컬렉션이든 동작 방식이
전부 같은 원리로 설명된다.
