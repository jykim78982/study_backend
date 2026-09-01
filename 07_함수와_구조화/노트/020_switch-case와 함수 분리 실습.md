---
title: switch-case와 함수 분리 실습
date: 2026-08-02
tags: [java, 함수, switch, 리턴값, ScoresApp]
---

> 🔗 관련 노트: [[018_구조적 프로그래밍과 함수]] · [[017_클래스 배열과 참조 공유]]

## 1. 실습 코드

### 변경 전

```java
class ScoresApp {

    public static void main(String[] args) throws java.io.IOException {

        Scanner scan = new Scanner(System.in, "MS949");

        int isRun = 1;
        String name;
        int score1 = 0;
        int score2 = 0;
        int score3 = 0;

        EXIT: while (isRun == 1) {

            System.out.println("성적관리 프로그램 메뉴");
            System.out.println("1. 성적입력");
            System.out.println("2. 성적출력");
            System.out.println("3. 저장");
            System.out.println("4. 로드");
            System.out.println("5. 종료");
            int menu = Integer.parseInt(scan.nextLine());

            switch (menu) {
                case 1: {

                    System.out.print("name: ");
                    name = scan.nextLine();
                    System.out.println(name);

                    do {
                    System.out.print("score1:");
                    score1 = Integer.parseInt(scan.nextLine());
                    }
                    while (score1 < 0 || 100 < score1);

                    do {
                    System.out.print("score2:");
                    score2 = Integer.parseInt(scan.nextLine());
                    }
                    while (score2 < 0 || 100 < score2);

                    do {
                    System.out.print("score3:");
                    score3 = Integer.parseInt(scan.nextLine());
                    }
                    while (score3 < 0 || 100 < score3);
                }

                break;

                case 2: {
                    int total;
                    float avg;

                    total = score1 + score2 + score3;
                    avg = total / 3.0f;

                    System.out.println("성적을 출력합니다.");

                    System.out.printf("score1:%d\n", score1);
                    System.out.printf("score2:%d\n", score2);
                    System.out.printf("score3:%d\n", score3);
                    System.out.printf("총점:%d\n", total);
                    System.out.printf("평균:%.2f\n", avg);
                }

                break;

                case 3: {
                    java.io.FileOutputStream fos = new java.io.FileOutputStream("records.csv");
                    java.io.PrintStream ps = new java.io.PrintStream(fos);

                    ps.printf("%d,%d,%d\n", score1, score2, score3);

                    ps.close();
                    fos.close();
                }

                break;

                case 4: {
                    java.io.FileInputStream fis = new java.io.FileInputStream("records.csv");
                    java.util.Scanner fileScan = new java.util.Scanner(fis);

                    fileScan.useDelimiter(",|\\r\\n|\\n");

                    if (fileScan.hasNextInt()) {
                        score1 = fileScan.nextInt();
                        score2 = fileScan.nextInt();
                        score3 = fileScan.nextInt();
                        System.out.println("[알림] records.csv 파일에서 성적을 성공적으로 불러왔습니다.");
                    }

                    fileScan.close();
                    fis.close();
                }

                break;

                case 5: {
                    boolean invalid;
                    do {
                        System.out.print("종료하시겠습니까? (0: 종료, 1: 계속): ");
                        isRun = Integer.parseInt(scan.nextLine());

                        invalid = (isRun < 0 || 1 < isRun);

                        if (invalid) {
                            System.out.println("유효하지 않은 값을 입력하였습니다. 다시 입력해주세요.");
                        }
                    }
                    while (invalid);
                }
                break;

                default: {
                    System.out.println("1,2,3,4 중에서 선택하십시오");
                }
            }
        }

        System.out.println("종료합니다");

    }
}
```

이 코드는 `case 1`, `case 2`, `case 4` 안에 입력·계산·출력 로직이 그대로 풀어져 있다. 아래는 그 로직들을 함수로 뽑아낸 결과다.

### 변경 후

```java
class ScoresApp {

    public static void main(String[] args) throws IOException {

        Scanner scan = new Scanner(System.in, "MS949");
        int isRun = 1;
        String name = "";
        int score1 = 0;
        int score2 = 0;
        int score3 = 0;

        while (isRun == 1) {

            System.out.println("성적관리 프로그램 메뉴");
            System.out.println("1. 성적입력");
            System.out.println("2. 성적출력");
            System.out.println("3. 저장");
            System.out.println("4. 로드");
            System.out.println("5. 종료");
            int menu = Integer.parseInt(scan.nextLine());

            switch (menu) {
                // 이름과 점수 3개를 입력받는다.
                case 1: {
                    name = inputName(scan);

                    int[] results = inputScore(scan);
                    score1 = results[0];
                    score2 = results[1];
                    score3 = results[2];
                }
                isRun = checkContinue(scan); break;

                // 총점·평균을 구해서 성적을 출력한다.
                case 2: {
                    int total = totalScores(score1, score2, score3);

                    float avg = total / 3.0f;

                    printScore(name, score1, score2, score3, total, avg);
                }
                isRun = checkContinue(scan); break;

                // 현재 이름·점수를 파일에 저장한다.
                case 3: {
                    saveScores(name, score1, score2, score3);
                }
                isRun = checkContinue(scan); break;

                // 파일에서 이름·점수를 불러온다.
                case 4: {

                    Record record = loadScores();
                    name = record.name;
                    score1 = record.score1;
                    score2 = record.score2;
                    score3 = record.score3;

                    System.out.printf("학생 이름 : %s%n성적1 : %d%n성적2 : %d%n성적3 : %d%n", name, score1, score2, score3);
                }
                // break가 없어 case 5로 이어짐 (fallthrough)

                // 종료 여부를 묻는다.
                case 5: {
                    isRun = checkContinue(scan);
                }
                break;

                // 1~5 범위를 벗어난 메뉴 입력 처리
                default: {
                    System.out.println("1,2,3,4 중에서 선택하십시오");
                }
            }
        }
        scan.close();
        System.out.println("종료합니다");
    }

    // 이름 하나를 입력받아 돌려준다.
    public static String inputName(Scanner scan) {

        System.out.print("name: ");
        String name = scan.nextLine();
        System.out.println(name);

        return name;
    }

    // 점수 3개를 각각 0~100 범위로 검증하며 입력받아 배열로 돌려준다.
    public static int[] inputScore(Scanner scan) {

        int score1, score2, score3;

        do {
            System.out.print("score1:");
            score1 = Integer.parseInt(scan.nextLine());
        }
        while (score1 < 0 || 100 < score1);

        do {
            System.out.print("score2:");
            score2 = Integer.parseInt(scan.nextLine());
        }
        while (score2 < 0 || 100 < score2);

        do {
            System.out.print("score3:");
            score3 = Integer.parseInt(scan.nextLine());
        }
        while (score3 < 0 || 100 < score3);

        return new int[]{score1, score2, score3};

    }

    // 점수 3개를 더해서 총점을 돌려준다.
    public static int totalScores(int score1, int score2, int score3) {
        int total;

        total = score1 + score2 + score3;

        return total;
    }

    // 이름·점수·총점·평균을 화면에 출력한다.
    public static void printScore(String name, int score1, int score2, int score3, int total, float avg) {
        System.out.println("성적을 출력합니다.");
        System.out.printf("학생 이름 : %s%n", name);
        System.out.printf("score1:%d\n", score1);
        System.out.printf("score2:%d\n", score2);
        System.out.printf("score3:%d\n", score3);
        System.out.printf("총점:%d\n", total);
        System.out.printf("평균:%.2f\n", avg);
    }

    // 이름·점수 3개를 records.csv 한 줄로 저장한다.
    public static void saveScores(String name, int score1, int score2, int score3) throws IOException {
        FileOutputStream fos = new FileOutputStream("records.csv");
        PrintStream ps = new PrintStream(fos);

        ps.printf("%s,%d,%d,%d\n", name, score1, score2, score3);

        ps.close();
        fos.close();
    }

    // records.csv에서 이름·점수 3개를 읽어 Record로 돌려준다.
    public static Record loadScores() throws IOException {
        FileInputStream fis = new FileInputStream("records.csv");
        Scanner fileScan = new Scanner(fis);
        fileScan.useDelimiter(",|\\r\\n|\\n");

        Record record = new Record();
        record.name = fileScan.next();

        if (fileScan.hasNextInt()) {
            record.score1 = fileScan.nextInt();
            record.score2 = fileScan.nextInt();
            record.score3 = fileScan.nextInt();
            System.out.println("[알림] records.csv 파일에서 성적을 성공적으로 불러왔습니다.");
        }

        fileScan.close();
        fis.close();

        return record;
    }

    // 계속할지(1)/종료할지(0) 유효한 값이 들어올 때까지 물어본다.
    public static int checkContinue(Scanner scan) {
        int isRun;
        boolean invalid;
        do {
            System.out.print("종료하시겠습니까? (0: 종료, 1: 계속): ");
            isRun = Integer.parseInt(scan.nextLine());

            invalid = (isRun < 0 || 1 < isRun);

            if (invalid) {
                System.out.println("유효하지 않은 값을 입력하였습니다. 다시 입력해주세요.");
            }
        }
        while (invalid);

        return isRun;
    }
}

// 이름 + 점수 3개를 한 번에 묶어 돌려주기 위한 클래스
class Record {
    String name;
    int score1;
    int score2;
    int score3;
}
```

## 2. 여러 값을 리턴해야 할 때

### 2-1. `return a, b;`는 문법 오류

```java
return score1, score2, score3;  // 컴파일 오류
```

자바의 `return`은 값을 **하나만** 돌려줄 수 있다. 콤마로 여러 값을 나열하는 문법 자체가 없다.

### 2-2. 타입이 같으면 배열로 묶는다

`score1, score2, score3`처럼 전부 `int`라면 배열 하나로 묶어서 리턴할 수 있다.

```java
public static int[] inputScore(Scanner scan) {
    int score1, score2, score3;
    // ... 입력 로직 ...
    return new int[]{score1, score2, score3};
}
```

호출부:
```java
int[] results = inputScore(scan);
score1 = results[0];
score2 = results[1];
score3 = results[2];
```

### 2-3. 타입이 다르면 클래스로 묶는다

`name`(String)과 `score1/score2/score3`(int)처럼 타입이 섞여 있으면 배열에 못 담는다. 이럴 땐 값을 묶는 작은 클래스를 만든다.

```java
class Record {
    String name;
    int score1;
    int score2;
    int score3;
}
```

```java
public static Record loadScores() throws IOException {
    Record record = new Record();
    record.name = fileScan.next();
    record.score1 = fileScan.nextInt();
    record.score2 = fileScan.nextInt();
    record.score3 = fileScan.nextInt();
    return record;
}
```

`return total; return avg;`처럼 서로 다른 타입 두 개를 나란히 리턴하려던 시도도 같은 이유로 오류였다 — 이런 경우도 `Result` 같은 클래스로 묶거나, 애초에 함수를 `void`로 두고 내부에서 출력까지 끝내는 방식으로 단순화할 수 있다.

### 2-4. 한 파일에 클래스 여러 개

`public class`는 파일당 하나(파일명과 이름이 같아야 함)지만, `public`을 안 붙인 클래스는 같은 파일에 여러 개 넣을 수 있다. 그래서 `Record` 클래스를 `ScoresApp.java` 안에 그냥 추가해도 컴파일에 문제없다.

## 3. 함수로 뺄 때 자주 나는 오류

### 3-1. 함수 안에서 새 Scanner를 또 만듦

```java
public static String inputName() {
    Scanner scan = new Scanner(System.in, "MS949");  // 문제
    ...
}
```

`System.in`에 대해 `Scanner`를 여러 개 만들면 버퍼링 문제가 생긴다. `main`에서 쓰던 `scan`을 매개변수로 받아서 재사용해야 한다.

```java
public static String inputName(Scanner scan) { ... }
```

### 3-2. 지역변수 확정 초기화(definite assignment) 오류

```java
String name;               // 초기값 없음
...
case 1: name = inputName(scan); break;
case 2: printScore(name, ...);   // 컴파일 오류 가능
```

`switch`는 `case 1`을 거치지 않고 바로 `case 2`로 갈 수 있기 때문에, 컴파일러가 "`name`이 확실히 초기화됐다"고 보장할 수 없다. 선언할 때 기본값을 주면 해결된다.

```java
String name = "";
```

### 3-3. 함수 시그니처(매개변수 타입)를 실제 데이터에 맞춘다

이름처럼 여러 글자를 담아야 하면 `char`가 아니라 `String`을 써야 한다.

```java
// 잘못된 예
public static void saveScores(char name, int score1, int score2, int score3)

// 올바른 예
public static void saveScores(String name, int score1, int score2, int score3)
```

### 3-4. 함수 선언에 세미콜론을 잘못 붙임

```java
public static void loadScores(); throws IOException {  // 오류
```

매개변수 괄호 뒤에 `;`이 오면 "선언만 하고 본문 없음"이 되어버려 컴파일 오류가 난다.

```java
public static void loadScores() throws IOException {
```

### 3-5. 리턴값을 받지 않고 버림

```java
case 5: {
    checkContinue(scan);   // 리턴값(0/1)을 버림 → isRun이 안 바뀜
}
```

함수 안의 지역변수(`checkContinue`의 `isRun`)와 `main`의 변수는 이름이 같아도 완전히 다른 변수다. 함수 밖에 반영하려면 반드시 리턴받아서 대입해야 한다.

```java
case 5: {
    isRun = checkContinue(scan);
}
```

## 4. switch-case의 break와 fallthrough

`break`가 없으면 다음 `case`로 그대로 이어서 실행된다(fallthrough). 예를 들어 `case 4`(로드)에서 `break`를 빼면 로드 직후 바로 `case 5`(종료 확인)까지 실행된다.

```java
case 4: {
    ...
}
// break 없음 → case 5로 흘러감

case 5: {
    isRun = checkContinue(scan);
}
break;
```

**주의**: fallthrough는 "한 단계만 건너뛰는" 게 아니라 `break`를 만날 때까지 전부 이어서 실행된다. `case 1~4`에 전부 `break`를 지우면, 메뉴에서 2번(출력)만 골라도 3번(저장)·4번(로드)까지 줄줄이 실행되어 버린다. 실습 중 이 문제로 "2번을 골랐는데 왜 로드 완료 메시지가 뜨는지" 혼란이 있었다.

**설계 정리**: "각 case 작업 후 자동으로 종료 여부를 묻는다"가 목적이라면, fallthrough로 여러 case를 잇는 것보다 각 case의 `break` 자리에 `isRun = checkContinue(scan); break;`를 공통으로 넣는 편이 의도가 명확하다.

## 5. 정리

- 리턴은 하나만 가능 → 값이 여러 개면 **같은 타입은 배열, 다른 타입은 클래스**로 묶는다.
- 함수는 외부 자원(Scanner 등)을 새로 만들지 말고 매개변수로 받아 재사용한다.
- `switch` 안에서만 초기화되는 지역변수는 선언 시 기본값을 준다.
- 함수 시그니처(매개변수 타입, 리턴 타입)는 실제 다루는 데이터에 맞춰야 하고, 바꾸면 호출부도 같이 고쳐야 한다.
- `break` 유무에 따른 fallthrough 범위를 항상 끝까지 추적해야 의도치 않은 케이스 실행을 피할 수 있다.

