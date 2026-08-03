---
title: 함수 매개변수 전달 방식 (Code1 vs Code2)
date: 2026-08-03
tags: [java, 함수, 배열, 참조, call-by-value, 메모리]
---

## 1. 두 코드 비교

### Code1.java — 값 변수를 넘기는 경우

```java
public class Code1 {
    public static void main(String[] args) {
        int x, y, sum = 0;

        x = 3;
        y = 4;

        add(x, y, sum);
        printSum(sum);
    }

    public static int add(int x, int y, int sum) {
        return sum = x + y;
    }

    public static void printSum(int sum) {
        System.out.printf("sum is %d\n", sum);
    }
}
```

### Code2.java — 배열을 넘기는 경우

```java
public class Code2 {
    public static void main(String[] args) {
        int[] nums = new int[3];

        nums[0] = 3;
        nums[1] = 4;

        add(nums);
        printSum(nums[2]);
    }

    public static void add(int[] nums) {
        nums[2] = nums[0] + nums[1];
    }

    public static void printSum(int sum) {
        System.out.printf("sum is %d\n", sum);
    }
}
```

두 코드 모두 "두 값을 더한다"는 목적은 같은데, `add` 함수의 리턴 타입이 다르다. Code1은 `int`를 리턴하고 Code2는 `void`다. 이 차이가 왜 생기는지가 이 노트의 핵심이다.

## 2. 메모리 구조로 보기

### Code1 — x, y, sum은 스택에 있는 독립된 값

```
[ main의 스택 ]              [ add의 스택 ]
 x   = 3                      x   = 3   (복사본)
 y   = 4         --넘길 때-->  y   = 4   (복사본)
 sum = 0    (호출 후에도 그대로)  sum = 0   (복사본, 함수 안에서 7로 바뀜)
```

`add(x, y, sum)`을 호출하면, `main`의 `x, y, sum` 값이 **그대로 복사**되어서 `add`만의 새로운 스택 공간에 담긴다. `add` 안에서 `sum = x + y`로 `sum`을 바꿔도, 그건 `add`의 스택에 있는 복사본이 바뀌는 것이지 `main`의 `sum`과는 완전히 별개다. `add`가 끝나면 이 복사본은 사라진다.

그래서 계산 결과를 `main`으로 가져오려면 반드시 `return`으로 값을 돌려받아야 한다. (참고로 지금 코드는 `add(x, y, sum);`이라고만 하고 리턴값을 안 받고 있어서, 실제로는 `sum`이 `main`에 반영되지 않는 오류가 있다. `sum = add(x, y, sum);`처럼 받아야 정상 동작한다.)

### Code2 — nums는 힙에 있는 배열을 가리키는 참조

```
[ main의 스택 ]                    [ 힙 ]
 nums ----참조(주소)----> ┌───────────────┐
                          │ nums[0] = 3   │
                          │ nums[1] = 4   │
                          │ nums[2] = 0   │
                          └───────────────┘

add(nums) 호출 시:

[ main의 스택 ]        [ add의 스택 ]           [ 힙 ]
 nums ---주소---->      nums ---같은 주소--->   ┌───────────────┐
                                               │ nums[0] = 3   │
                                               │ nums[1] = 4   │
                                               │ nums[2] = 0→7 │ ← add에서 직접 수정
                                               └───────────────┘
```

`add(nums)`를 호출하면 `nums`가 담고 있는 **주소값**이 복사되어 `add`의 매개변수에 들어간다. 하지만 이 주소가 가리키는 대상, 즉 힙에 있는 배열 객체는 `main`과 `add`가 **동일한 것 하나**를 같이 보고 있는 것이다. 그래서 `add` 안에서 `nums[2] = nums[0] + nums[1]`을 실행하면, 그건 복사본이 아니라 원본 배열의 3번째 칸을 직접 수정하는 것이다.

`add`가 끝난 뒤 `main`으로 돌아와서 `nums[2]`를 확인하면 이미 7로 바뀌어 있다. 그래서 `add`는 `void`여도 되고, `return` 없이도 결과가 호출한 쪽에 반영된다.

## 3. 왜 이런 차이가 생기는가

자바는 항상 **값을 복사해서 전달한다** (call by value). 다만 무엇이 복사되느냐가 다르다.

- 기본 타입(`int`, `boolean` 등): 그 값 자체가 복사된다. → 복사본을 바꿔도 원본은 안 바뀜.
- 배열/객체(`int[]`, `Exam` 등): 그 객체를 가리키는 **참조(주소)**가 복사된다. → 주소는 복사되지만 가리키는 실체(힙의 객체)는 하나뿐이라, 그 실체 내부를 수정하면 양쪽 다 같은 변화를 본다.

즉 "값을 복사하느냐 참조를 복사하느냐"가 아니라, 자바는 **항상 값을 복사**하는데 그 "값"이 원시 타입이면 데이터 자체이고, 배열/객체 타입이면 주소라는 점이 다른 것이다.

## 4. 정리 표

| | Code1 (`x, y, sum`) | Code2 (`nums[0], nums[1], nums[2]`) |
|---|---|---|
| 변수의 저장 위치 | 스택 (독립된 값) | 힙의 배열 객체 내부 |
| 함수에 넘길 때 복사되는 것 | 값 자체 | 배열을 가리키는 주소(참조) |
| 함수 안에서 수정 시 | 복사본만 바뀜, 원본 불변 | 원본이 직접 바뀜 (같은 힙 공간 공유) |
| 결과를 호출부로 가져오려면 | `return` 필요 | `return` 불필요 |
| `add`의 리턴 타입 | `int` (계산 결과를 돌려줘야 함) | `void` (이미 원본이 바뀌어 있음) |

## 🔗 관련 노트

- [[015_배열과 참조, 메모리 구조]]
- [[018_구조적 프로그래밍과 함수]]
- [[020_switch-case와 함수 분리 실습]]
