---
tags: [자바, 컬렉션, Stream, 함수형프로그래밍, 참고자료]
---

> 🔗 관련 노트: [[007_컬렉션·제네릭 API 메서드 체이닝 뜯어보기]] · [[073_스프링 DI]] · [[001_기본형과 참조형, 박싱언박싱과 Object 배열, ArrayList]]

# Stream API — 선언형으로 컬렉션 가공하기

for문으로 컬렉션을 순회하며 처리하던 방식을 Stream API가 왜, 어떻게 대체하는지, 그리고 소스·중간 연산·최종 연산이라는 3단계 구조를 정리한다.

## 1. Stream이 왜 나왔나

기존에는 컬렉션(`List`, `Set` 등)을 다루려면 `for`문으로 하나씩 순회하면서 직접 로직을 짜야 했다.

```java
List<Menu> onSaleMenus = new ArrayList<>();
for (Menu menu : menus) {
    if (menu.getStatus().equals("on")) {
        onSaleMenus.add(menu);
    }
}
```

Stream API는 이런 "반복하면서 처리하는" 패턴을 선언적으로(뭘 원하는지만 말하면 되게) 바꿔준다.

```java
List<Menu> onSaleMenus = menus.stream()
    .filter(menu -> menu.getStatus().equals("on"))
    .toList();
```

"어떻게 반복할지"가 아니라 "뭘 걸러내고 싶은지"만 표현하는 방식이다.

## 2. Stream의 3대 핵심 특징

- **원본 데이터를 변경하지 않음(Read-Only)**: 스트림은 데이터 소스(컬렉션 등)를 읽기만 할 뿐, 원본 데이터를 수정하거나 파괴하지 않는다. 가공된 결과는 새로운 컬렉션이나 단일 값으로 생성된다.
- **일회용(Single-use)**: 스트림은 한 번 사용(최종 연산 수행)하고 나면 닫힌다. 재사용하려고 하면 `IllegalStateException`이 발생하므로, 다시 쓰려면 새 스트림을 생성해야 한다.
- **지연 연산(Lazy Evaluation)**: 중간 연산(필터링, 매핑 등)은 명시되는 즉시 수행되는 게 아니라, 최종 연산이 호출되는 시점에 한꺼번에 묶여 실행된다. `filter`, `map`을 아무리 체이닝해도, 맨 끝에 `collect()` 같은 최종 연산이 없으면 아무 일도 일어나지 않는다. 이를 통해 불필요한 연산을 최적화한다.

## 3. 연산 파이프라인 — 소스 → 중간 연산 → 최종 연산

Stream 연산은 항상 이 순서로 이루어진다.

```
[ 데이터 소스 ] ──(생성)──> [ Stream ] ──(중간 연산)──> [ Stream ] ──(최종 연산)──> [ 최종 결과 ]
 (List, Array 등)         stream()        filter(), map()          collect(), sum()
```

```java
menus.stream()                     // ① 소스: 스트림 생성
    .filter(m -> ...)              // ② 중간 연산 (여러 개 이어붙일 수 있음)
    .map(m -> ...)                 // ② 중간 연산
    .collect(Collectors.toList()); // ③ 최종 연산
```

**① 스트림 생성** — 데이터 소스로부터 스트림을 만든다.

```java
List<String> list = Arrays.asList("a", "b", "c");

// 1. 컬렉션에서 생성
Stream<String> streamFromList = list.stream();

// 2. 배열에서 생성
Stream<String> streamFromArray = Arrays.stream(new String[]{"a", "b", "c"});

// 3. 직접 생성 (Stream.of)
Stream<Integer> streamFromValues = Stream.of(1, 2, 3, 4, 5);
```

**② 중간 연산(Intermediate Operations)** — 스트림을 가공해서 또 다른 스트림을 반환한다. 메서드 체이닝으로 여러 개를 연속해서 연결할 수 있고, 지연 연산으로 동작한다.

| 메서드 | 역할 | 예시 |
|---|---|---|
| `filter(Predicate)` | 조건에 맞는 것만 남김 | `.filter(m -> m.getPrice() > 5000)` |
| `map(Function)` | 각 요소를 다른 값/타입으로 변환 | `.map(Menu::getKorName)` (Menu → String) |
| `sorted()` / `sorted(Comparator)` | 정렬 | `.sorted(Comparator.comparing(Menu::getPrice))` |
| `distinct()` | 중복 제거(`equals()` 기반) | `.distinct()` |
| `limit(n)` | 앞에서 n개만 | `.limit(10)` |
| `skip(n)` | 앞에서 n개 건너뜀 | `.skip(5)` |
| `flatMap(Function)` | 중첩 구조(예: `List<List<T>>`)를 단일 스트림으로 평탄화 | — |

**③ 최종 연산(Terminal Operations)** — 파이프라인의 마지막에서 실제 연산을 수행하고 결과값(List, Map, long, Optional 등)을 반환한다. 최종 연산이 호출되면 스트림은 닫힌다.

| 메서드 | 역할 |
|---|---|
| `collect(Collectors.toList())` / `.toList()` | 리스트로 모음 |
| `collect(Collectors.toMap(k, v))` | 맵으로 모음 |
| `forEach(Consumer)` | 각 요소에 대해 동작 실행(반환값 없음) |
| `count()`, `sum()`, `average()` | 개수·합계·평균 집계 |
| `reduce(BinaryOperator)` | 요소들을 하나씩 누적해 단일 결과값으로 줄임 |
| `anyMatch()`, `allMatch()`, `noneMatch()` | 조건 만족 여부(boolean) |
| `findFirst()`, `findAny()` | 조건에 맞는 요소 하나를 `Optional`로 반환 |

## 4. 메서드 참조 (`Class::method`)

람다식을 줄여 쓰는 문법이다.

```java
.map(menu -> menu.getKorName())   // 람다식
.map(Menu::getKorName)            // 메서드 참조 (같은 뜻, 더 짧음)
```

`Category::getId`도 `c -> c.getId()`와 완전히 동일하다.

## 5. for문 vs Stream 비교 예시

목표: 짝수만 걸러내어, 각 숫자를 2배로 곱한 뒤, 그 결과를 리스트로 변환하기.

**❌ 기존 명령형(imperative) `for`문 방식**

```java
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);
List<Integer> result = new ArrayList<>();

for (Integer num : numbers) {
    if (num % 2 == 0) { // 필터링
        result.add(num * 2); // 변환 후 추가
    }
}
```

**✅ Stream API(선언형) 방식**

```java
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);

List<Integer> result = numbers.stream()
    .filter(n -> n % 2 == 0)       // 짝수 추출
    .map(n -> n * 2)               // 2배 변환
    .collect(Collectors.toList()); // 리스트로 집계
```

코드가 무엇을 수행하는지(What to do)가 직관적으로 읽히고, 임시 변수(`result`)에 조건 분기를 직접 채워 넣는 부분이 줄어들어 깔끔해진다.

## 6. 실제 프로젝트 예시 — `DfMenuService`에서 쓴 코드

```java
Map<Long, String> categoryNameMap = categoryRepository.findAllWithMenuCount()
        .stream()                                                        // ① List<Category> → Stream<Category>
        .collect(Collectors.toMap(Category::getId, Category::getName));  // ③ 최종 연산: Map으로 모으기
```

이 경우 중간 연산 없이 바로 최종 연산(`collect`)으로 간다 — Category 리스트를 "id → name" 맵으로 바로 변환하는 것뿐이라 중간 가공이 필요 없었던 것이다.

만약 여기에 중간 연산을 추가한다면(예: 이름이 있는 카테고리만, 이름 오름차순으로):

```java
Map<Long, String> categoryNameMap = categories.stream()
        .filter(c -> c.getName() != null)                     // 중간 연산
        .sorted(Comparator.comparing(Category::getName))      // 중간 연산
        .collect(Collectors.toMap(Category::getId, Category::getName)); // 최종 연산
```

## 7. 병렬 스트림(Parallel Stream) — 참고

Stream API는 데이터 연산을 멀티 스레드로 손쉽게 분산 처리할 수 있는 `parallelStream()`도 제공한다(내부적으로 Java의 `ForkJoinPool` 활용).

```java
List<String> list = Arrays.asList("a", "b", "c", "d", "e");

// 멀티스레드로 병렬 처리
list.parallelStream()
    .forEach(item -> {
        System.out.println(Thread.currentThread().getName() + " - " + item);
    });
```

**주의**: 데이터 양이 적거나 단순 연산일 때는 스레드 분기·합병 오버헤드로 인해 오히려 일반 `stream()`보다 느릴 수 있다. 대용량 데이터 처리, 독립적인 단순 계산 작업일 때만 신중하게 사용하는 것이 좋다.

## 8. 언제 쓰고 언제 안 쓰는 게 좋은가

- **좋은 경우**: 필터링·변환·집계처럼 "데이터를 다른 형태로 가공"할 때 — 코드가 짧아지고 의도가 명확해진다.
- **주의할 경우**: 로직이 복잡해지거나(여러 단계 조건 분기 등), 디버깅하며 중간값을 찍어봐야 할 때는 오히려 `for`문이 더 읽기 쉬울 수 있다. Stream은 중간에 브레이크포인트를 찍기가 상대적으로 불편하다.
- 3계층 구조에서는 주로 **Service 계층**에서 Repository가 가져온 Entity 리스트를 DTO로 변환하거나, Map으로 재구성할 때 자주 쓰인다.

## 9. 정리

| 개념 | 핵심 |
|---|---|
| Stream의 목적 | "어떻게 반복할지"가 아니라 "무엇을 원하는지"를 선언적으로 표현 |
| 3대 특징 | 원본 불변(Read-Only), 일회용(Single-use), 지연 연산(Lazy) |
| 파이프라인 | 소스(생성) → 중간 연산(변형, 체이닝 가능) → 최종 연산(소비, 결과 반환) |
| 중간 연산 | `filter`, `map`, `sorted`, `distinct`, `limit`, `skip`, `flatMap` — 스트림을 반환, 지연 실행 |
| 최종 연산 | `collect`, `forEach`, `count`, `reduce`, `anyMatch`, `findFirst` 등 — 호출돼야 실제로 실행됨 |
| 메서드 참조 | `Class::method`는 람다식(`obj -> obj.method()`)의 축약형 |
| 실무 위치 | Service 계층에서 Entity → DTO 변환, Map 재구성 등에 자주 사용 |

핵심은 한 문장으로 요약된다 — **중간 연산을 아무리 쌓아도 최종 연산이 없으면 아무 일도 일어나지 않는다.** Stream을 읽을 때는 항상 "이 체인의 최종 연산이 무엇인가"부터 찾는 것이 전체 흐름을 이해하는 지름길이다.
