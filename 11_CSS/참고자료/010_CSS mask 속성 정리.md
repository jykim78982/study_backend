---
tags: [웹, CSS, mask, 참고자료]
---

> 🔗 관련 노트: [[050_플렉스박스 아이템 속성과 박스 사이징]] · [[051_CSS — 배경 이미지·컬러·마스크·인라인 박스·포지션]] · [[020_구글 아이콘 사용법과 CSS 아이콘 라이브러리 실습]]

# CSS mask 속성 정리

`mask`는 이미지나 그라데이션을 마스크(가리개)로 사용해 요소의 특정 부분을 숨기거나 드러내는 속성이다. 포토샵의 레이어 마스크(Layer Mask)와 동일한 원리로 작동한다.

## 1. 기본 원리 — 투명도 기반

마스크로 지정한 이미지의 투명도(알파 채널)를 기준으로 원본 요소의 표시 여부가 결정된다.

- 불투명한 영역(`opacity: 1` / 검은색 등): 해당 위치의 원본 요소가 그대로 보인다.
- 투명한 영역(`opacity: 0`): 해당 위치의 원본 요소가 숨겨진다(투명해진다).
- 반투명한 영역: 해당 위치의 원본 요소도 반투명하게 보인다.

## 2. 세부 속성 — background 속성과 매우 유사

```css
.masked-element {
  /* 마스크 이미지 지정 */
  mask-image: url('star-shape.svg');

  /* 마스크 반복 여부 */
  mask-repeat: no-repeat;

  /* 마스크 위치 */
  mask-position: center;

  /* 마스크 크기 (contain, cover, px 등) */
  mask-size: contain;
}
```

축약형(shorthand)으로도 작성할 수 있다.

```css
.masked-element {
  mask: url('star-shape.svg') no-repeat center / contain;
}
```

## 3. 실무 대표 활용 예시

### ① 그라데이션으로 자연스럽게 페이드아웃 처리

이미지나 텍스트의 끝부분을 부드럽게 투명하게 만들고 싶을 때 `linear-gradient`를 마스크 이미지로 활용한다.

```css
.fade-banner {
  /* 위쪽은 불투명(보임), 아래쪽으로 갈수록 투명(숨겨짐) */
  mask-image: linear-gradient(to bottom, black 50%, transparent 100%);
}
```

### ② SVG 모양으로 요소 자르기

`clip-path`보다 정교하게, 이미지의 아웃라인(별 모양, 하트 모양 등) 형태로 사진이나 동영상을 깎아낼 때 사용한다.

```css
.profile-img {
  mask-image: url('heart.svg');
  mask-size: cover;
}
```

## 4. 크로스 브라우저 호환성 주의사항

대부분의 현대 브라우저가 `mask` 속성을 지원하지만, 구형 버전이나 특정 환경에서는 `-webkit-` 접두사를 붙여야 정상 작동한다. 호환성을 위해 두 가지 모두 작성하는 것이 좋다.

```css
.element {
  -webkit-mask-image: url('mask.png');
  mask-image: url('mask.png');
}
```
