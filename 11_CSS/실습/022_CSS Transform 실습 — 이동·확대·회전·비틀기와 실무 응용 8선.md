---
tags: [웹, CSS, transform, 실습]
---

> 🔗 관련 노트: [[050_플렉스박스 아이템 속성과 박스 사이징]] · [[051_CSS — 배경 이미지·컬러·마스크·인라인 박스·포지션]]

# CSS Transform 실습 — 이동·확대·회전·비틀기와 실무 응용 8선

`publishing/css/transform/step1.html` ~ `step13.html` 실습. Part 1(기초 5단계)에서 `transform`이 가진 다섯 가지 기능을 하나씩 익히고, Part 2(실무 응용 8선)에서 실제 UI 패턴에 조합해봤다.

## Part 1. 개념 쪼개기 — 기초 5단계

### Step 1. 이동 (`translateX`, `translateY`)

`margin`으로 위치를 옮기면 옆에 있는 다른 박스까지 같이 밀려나지만, `translate`는 옆 요소에 아무런 피해를 주지 않고 나 혼자만 유령처럼 이동한다. `left`/`top`으로도 이동은 가능하지만, 그러려면 `display`·`position` 속성이 함께 얽혀서 기존 다른 스타일에 영향을 줄 수 있는 문제가 있다. `transform`의 `translate*` 속성을 쓰면 다른 속성에 영향을 주지 않으면서 이동시킬 수 있다.

```css
.box-2 {
  background: #1e90ff;
  /* 가로(X)로 30px, 세로(Y)로 -20px(위로) 이동 */
  transform: translate(30px, -20px);
  /* 원래 있었던 자리는 유지된다. */
}
```

- **체크 포인트**: 2번 파란 상자가 오른쪽 위로 튀어나왔는데도 3번 초록 상자는 밀려나지 않고 원래 자리를 지킨다. 2번 상자가 원래 있던 공간도 그대로 유지된다 — [[051_CSS — 배경 이미지·컬러·마스크·인라인 박스·포지션]]에서 다룬 `position: relative`의 "고스트 스페이스" 개념과 같은 원리다.

### Step 2. 배율 확대/축소 (`scale`)

`width`/`height`를 직접 늘리면 주변 요소들의 자리를 뺏지만, `scale`은 주변 레이아웃을 그대로 둔 채 돋보기로 보듯 렌더링 배율만 확대한다.

```css
/* 1.2배 확대 */
.scale-up { transform: scale(1.2); }
/* 0.7배 축소 */
.scale-down { transform: scale(0.7); }
```

- **체크 포인트**: 박스 안의 글자 크기(`font-size`)도 비율에 맞춰 같이 커지고 작아진다.

### Step 3. 회전 (`rotate`)

중심점을 축으로 시계 방향/반시계 방향으로 회전한다. 각도 단위는 `deg`(degree)를 쓴다.

```css
/* 시계 방향으로 45도 */
.rot-45 { transform: rotate(45deg); }
/* 마이너스는 반시계 방향으로 45도 */
.rot-minus { transform: rotate(-45deg); }
```

### Step 4. 비틀기 (`skew`)

직사각형을 대각선으로 밀어 평행사변형으로 비튼다.

```css
/* 가로축으로 기울이기 */
.skew-x { transform: skewX(-20deg); }
/* 세로축으로 기울이기 */
.skew-y { transform: skewY(15deg); }
```

### Step 5. 회전/확대의 축 바꾸기 (`transform-origin`)

기본적으로 모든 변형은 박스의 정중앙(`center`)을 기준으로 돌아가고 커진다. 이 중심축을 모서리로 옮기면 완전히 다른 동작이 나온다.

```css
/* 1. 기본값: 중앙 기준 회전 */
.origin-center {
  transform: rotate(45deg);
}
/* 2. 좌측 상단 모서리에 압정을 꽂고 회전 */
.origin-top-left {
  transform-origin: top left;
  transform: rotate(45deg);
}
```

## Part 2. 실무 응용 8선

### 응용 1. 화면 정중앙 배치 공식 (`absolute` + `translate`)

모든 자동 레이아웃은 절대로 엘리먼트를 겹치게 배치하지 않는다. 그래서 박스 위에 버튼을 겹쳐 두고 싶어도 쉽지 않다. `position: absolute`의 `left`/`top`만으로 정중앙 배치를 하려면 버튼의 너비·높이를 정확히 알아야 하고, 캡션이 바뀌면 그 수치도 같이 바꿔야 해서 유지보수가 어렵다. `left`/`top: 50%`와 `transform: translate(-50%, -50%)`를 함께 쓰면, 요소의 너비·높이를 몰라도 부모의 정중앙에 배치할 수 있다.

```css
.parent {
  position: relative;
  width: 350px;
  height: 250px;
  background: #dfe4ea;
  border-radius: 8px;
}
.child {
  position: absolute;
  top: 50%;
  left: 50%;
  /*
    top/left 50%는 박스의 '좌상단 모서리'를 중앙에 놓습니다.
    자신의 크기의 절반(-50%)만큼 되돌려야 박스의 '중심'이 중앙에 옵니다.
  */
  transform: translate(-50%, -50%);

  background: #2f3542;
  color: white;
  padding: 16px 24px;
  border-radius: 6px;
}
```

- **원리**: `top/left: 50%`는 요소의 **좌상단 모서리**를 부모의 정중앙에 놓는다. 여기서 자신의 크기 절반만큼(`-50%`)을 `translate`로 되돌려야, 요소의 **중심**이 정중앙에 오게 된다. `translate`의 퍼센트 값은 요소 자기 자신의 크기 기준이라, 너비·높이를 몰라도(또는 내용이 바뀌어 크기가 달라져도) 항상 정확히 중앙에 맞는다.

### 응용 2. 닫기(X) 버튼 아이콘 만들기 (회전의 결합)

막대기 2개를 45도씩 반대로 회전시켜 X 모양을 만든다.

```css
.close-btn {
  width: 40px;
  height: 40px;
  background: #747d8c;
  position: relative;
  border: none;
  border-radius: 50%;
  cursor: pointer;
}
/* X를 구성하는 두 개의 가상 막대기 */
.close-btn::before,
.close-btn::after {
  content: "";
  position: absolute;
  top: 18px;
  left: 8px;
  width: 24px;
  height: 4px;
  background: white;
  border-radius: 2px;
}
/* 하나는 시계방향 45도, 하나는 반시계방향 45도 */
.close-btn::before { transform: rotate(45deg); }
.close-btn::after  { transform: rotate(-45deg); }
```

- 가상 요소(`::before`/`::after`)로 막대기를 만든 뒤 각각 반대 방향으로 회전시켜 겹치면 X자가 완성된다. 이미지 파일 없이 순수 CSS만으로 아이콘을 만든다는 점에서 [[020_구글 아이콘 사용법과 CSS 아이콘 라이브러리 실습]]의 `::before` 활용과 같은 맥락이다.

### 응용 3. 아코디언 드롭다운 화살표 회전

클릭(또는 호버)했을 때 펼쳐지는 메뉴의 화살표 애니메이션이다.

```css
.arrow {
  display: inline-block;
  transition: transform 0.3s ease; /* 회전할 때 애니메이션 */
}
/* 마우스를 올리면 180도 뒤집힘 */
.menu-item:hover .arrow {
  transform: rotate(180deg);
}
```

- `transition`을 함께 걸어두면 `rotate` 값이 순간적으로 바뀌는 게 아니라 부드럽게 회전하는 것처럼 보인다.

### 응용 4. 스피드 레이싱 스타일 '기울어진 버튼'

`skew`로 배경만 기울이고, 텍스트는 반대로 돌려 반듯하게 유지하는 기법이다.

```css
.speed-btn {
  padding: 12px 28px;
  background: #ff4757;
  border: none;
  cursor: pointer;
  /* 버튼 박스 전체를 왼쪽으로 -20도 기울임 */
  transform: skewX(-20deg);
}
.speed-btn span {
  display: inline-block;
  color: white;
  font-weight: bold;
  font-size: 16px;
  /*
    글자까지 찌그러지는 것을 막기 위해
    글자만 반대로 +20도 세워줌
  */
  transform: skewX(20deg);
}
```

- **핵심**: 부모(`.speed-btn`)와 자식(`span`)에 **서로 반대 부호의 `skewX`**를 각각 걸면, 부모가 기울어진 만큼 자식이 다시 반대로 기울어서 상쇄된다 — 버튼 배경은 사선으로 각지고 그 안의 글자는 똑바로 서 있는 결과가 나온다.

### 응용 5. 이커머스 썸네일 '확대 돋보기 뷰' (`overflow: hidden` + `scale`)

쇼핑몰 상품 목록에서 마우스를 올렸을 때 사진 프레임은 유지되면서 안의 이미지만 부드럽게 확대되는 패턴이다.

```css
.card {
  width: 260px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  cursor: pointer;
  background: white;
}

/* 이미지의 바깥 틀: 넘치는 이미지를 숨김 */
.img-wrap {
  width: 100%;
  height: 180px;
  overflow: hidden;
}

.img-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  /* 복귀할 때도 부드럽게 애니메이션 적용 */
  transition: transform 0.4s ease;
}

/* 카드를 호버했을 때 내부 이미지 확대 */
.card:hover .img-wrap img {
  transform: scale(1.15);
}

.info {
  padding: 16px;
  font-family: sans-serif;
}
.info h4 { margin: 0 0 6px 0; }
.info p { margin: 0; color: #888; font-size: 14px; }
```

- **체크 포인트**: `:hover`를 `img`가 아닌 부모인 `.card`에 걸어서, 카드의 텍스트 영역에 마우스가 닿아도 이미지가 함께 확대된다.
- **원리**: `.img-wrap`에 `overflow: hidden`을 줘서 틀 크기는 고정한 채, 그 안의 `img`만 `scale(1.15)`로 확대한다. 이미지가 틀보다 커지면서 넘치는 부분은 `overflow: hidden`이 잘라내므로, 바깥 카드 프레임은 전혀 흔들리지 않고 사진만 확대되는 것처럼 보인다.
- 실습 파일에는 대안으로 `.card`(전체)에 `transition`과 `:hover { transform: scale(1.15) }`를 거는 코드가 주석으로 남아 있다. 이렇게 하면 이미지뿐 아니라 카드 전체(그림자·텍스트 포함)가 통째로 커지는데, 이는 원하는 "사진 틀은 고정, 사진만 확대" 효과와는 다른 결과다 — 왜 굳이 `.img-wrap` 안쪽 `img`에만 `scale`을 걸어야 하는지를 비교해보려고 일부러 남겨둔 대조군으로 보인다.

### 응용 6. 3D 입체 푸시 버튼 (`:hover` + `:active`)

마우스를 올리면 떠오르고, 꾹 누르면(`:active`) 물리적으로 쑥 들어가는 게임기 버튼 효과다.

```css
.push-btn {
  padding: 16px 36px;
  font-size: 18px;
  font-weight: bold;
  color: white;
  background-color: #2ed573;
  border: none;
  border-radius: 12px;
  cursor: pointer;

  /* 아래쪽 그림자를 두껍게 깔아 3D 입체 블록 생성 */
  box-shadow: 0 8px 0 #26af5f, 0 15px 20px rgba(0,0,0,0.15);
  transition: transform 0.5s ease, box-shadow 0.5s ease;
}

/* 1. 호버 시: 위로 살짝 뜸 */
.push-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 0 #26af5f, 0 20px 25px rgba(0,0,0,0.2);
}

/* 2. 클릭 중(마우스 누름)일 때: 바닥까지 쑥 눌려 들어감 */
.push-btn:active {
  transform: translateY(6px);
  /* 누른 만큼 그림자 높이를 줄임 (10px -> 2px) */
  box-shadow: 0 2px 0 #26af5f, 0 5px 10px rgba(0,0,0,0.1);
}
```

- **체크 포인트**: `translateY`로 요소를 내리는 거리와 `box-shadow`의 Y축 두께를 동일하게 줄여서 실제 물리 버튼이 눌리는 감각을 재현한다.
- 가이드 원문은 `transition: transform 0.1s ease, box-shadow 0.1s ease;`(0.1초)였지만, 실습 코드는 **0.5초**로 늘려서 적용했다 — 애니메이션 속도를 눈으로 더 뚜렷하게 관찰하려고 일부러 느리게 설정한 것으로 보인다.

### 응용 7. 밑줄이 중앙에서 양옆으로 뻗어나가는 내비게이션 메뉴

단순 색상 변경 대신, 가상 요소(`::after`)와 `scaleX(0)`을 결합해 밑줄이 동적으로 퍼지는 인터랙션이다.

```css
.nav-link {
  position: relative;
  text-decoration: none;
  color: #2f3542;
  font-size: 18px;
  font-weight: 600;
  padding: 8px 0;
}

/* 밑줄을 가상 요소로 바닥에 배치 */
.nav-link::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background-color: #ff4757;

  /* [핵심] 가로 폭을 0으로 압축하여 숨김 */
  transform: scaleX(0);
  /* 중앙을 기준으로 좌우로 펴지도록 설정 */
  transform-origin: center;
  transition: transform 0.3s ease-out;
}

/* 마우스 오버 시 가로 배율을 1로 복원 */
.nav-link:hover::after {
  transform: scaleX(1);
}
```

- **원리**: `::after`로 밑줄을 만들고 평소엔 `scaleX(0)`으로 가로 폭을 눌러 숨겨둔다. 호버 시 `scaleX(1)`로 복원되는데, `transform-origin: center`가 걸려 있어서 **중앙을 축으로 좌우 양쪽으로 동시에** 펴진다.
- **체크 포인트**: `transform-origin`을 `left`로 바꾸면 왼쪽에서 오른쪽으로 쓱 그어지는 밑줄로 손쉽게 변형할 수 있다.

### 응용 8. 하단에서 텍스트가 미끄러져 올라오는 '슬라이드 업 오버레이 카드'

마우스를 올리기 전에는 깔끔한 이미지 카드였다가, 호버 시 숨겨진 상세 설명이 아래에서 슬라이드 업되는 카드 UI다.

```css
.gallery-card {
  position: relative;
  width: 400px;
  height: 380px;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  font-family: sans-serif;
}

.gallery-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 아래에 숨겨둘 반투명 오버레이 정보창 */
.overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  padding: 24px;
  box-sizing: border-box;
  background: linear-gradient(to top, rgba(0,0,0,0.9), transparent);
  color: white;

  /* 박스를 자기 높이만큼 아래(100%)로 밀어 화면 밖으로 숨김 */
  transform: translateY(100%);
  transition: transform 0.35s cubic-bezier(0.25, 1, 0.5, 1);
}

/* 카드에 호버 시 원래 위치(0)로 끌어올림 */
.gallery-card:hover .overlay {
  transform: translateY(0);
}

.overlay h3 { margin: 0 0 8px 0; font-size: 20px; }
.overlay p { margin: 0; font-size: 14px; opacity: 0.85; line-height: 1.4; }
```

- **체크 포인트**: `display: none`을 쓰지 않고 `overflow: hidden`(카드 바깥틀)과 `translateY(100%)`(자기 높이만큼 아래로 밀기)를 조합했기 때문에, 숨김 상태에서 나타날 때 `display` 전환 없이 CSS `transition` 애니메이션이 매끄럽게 작동한다.
- 실습 파일의 카드 너비는 `400px`로, 가이드 원문의 `280px`보다 넓게 잡혀 있다 — 오버레이 텍스트("자연 보호구역" 안내 문구)가 좁은 카드에서 줄바꿈이 너무 잦아지는 것을 피하려고 조정한 것으로 보인다.

## 전체 요약

| 구분 | 기법 | 핵심 원리 |
|---|---|---|
| 기초 1 | `translate(x, y)` | 문서 흐름을 건드리지 않고 시각적으로만 이동, 원래 자리는 유지됨 |
| 기초 2 | `scale(n)` | 레이아웃 크기는 그대로, 렌더링 배율만 확대/축소(자식 폰트도 함께 커짐) |
| 기초 3 | `rotate(deg)` | 중심점 기준 회전, 양수는 시계 방향 |
| 기초 4 | `skewX`/`skewY(deg)` | 대각선으로 밀어 평행사변형으로 비틈 |
| 기초 5 | `transform-origin` | 변형의 기준점을 중앙이 아닌 원하는 지점으로 이동 |
| 응용 1 | `absolute` + `translate(-50%, -50%)` | 크기를 몰라도 부모 정중앙 배치 |
| 응용 2 | `rotate(±45deg)` 두 막대 | 가상 요소 회전 조합으로 X 아이콘 |
| 응용 3 | `rotate(180deg)` + `transition` | 호버 시 화살표 회전 애니메이션 |
| 응용 4 | 부모/자식 반대 부호 `skewX` | 배경만 기울이고 텍스트는 상쇄해서 반듯하게 |
| 응용 5 | `overflow: hidden` + 자식 `scale` | 틀 고정, 내부 이미지만 확대(돋보기 효과) |
| 응용 6 | `translateY` + `box-shadow` 연동 | 호버·클릭에 따라 눌리는 3D 물리 버튼 |
| 응용 7 | `scaleX(0→1)` + `transform-origin: center` | 중앙에서 양옆으로 펼쳐지는 밑줄 |
| 응용 8 | `translateY(100%→0)` + `overflow: hidden` | `display` 전환 없이 슬라이드 업 애니메이션 |
