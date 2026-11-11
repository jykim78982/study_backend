---
tags: [Menu, MenuResponse, BFF, RouteHandler, MenuCatalog, MenuService, 실습]
---

> 🔗 관련 노트: [[055_스프링 시큐리티의 401·403 응답을 JSON으로 통일하기 — ErrorResponse, EntryPoint, AccessDeniedHandler]] · [[053_Refresh Token으로 조용히 갱신하기 — 재발급 API, RefreshTokenStore, proxy 문지기]] · [[052_Next.js 쿠키 기반 인증과 미들웨어 권한 제어 코드]] · [[051_로그인 API 작업 코드 — AuthController, AuthService, DTO, In-Memory User, MenuController]]

# 메뉴 API — 목업을 걷어내고 스프링 MenuResponse를 Next.js BFF로 연결

> **첨부 파일 안내**
> - 이 내용은 `ncafe-lesson-08-auth-error-response` 프로젝트에 함께 적용되어 있다. (401·403 JSON 통일 이후 이어서 적용)
>
> 참고 프로젝트 경로: `ncafe-lesson-08-auth-error-response`

이전 노트([[055_스프링 시큐리티의 401·403 응답을 JSON으로 통일하기 — ErrorResponse, EntryPoint, AccessDeniedHandler]])에서는 스프링이 실패를 401/403과 공통 `ErrorResponse`로 대답하게 만들었다. 로그인, 재발급, 로그아웃, 문지기, 에러 응답까지 인증의 뼈대는 모두 갖춰졌다.

그런데 정작 화면에 보이는 메뉴 데이터는 아직 가짜 목업이다. `/menus` 페이지는 `app/_mocks/menus.ts`의 배열을 읽고, `app/api/menus/route.tsx`에도 다른 목업 배열이 하나 더 있다. 스프링 쪽 `MenuController`는 지금까지 토큰 테스트용으로 문자열 세 개를 돌려주는 장난감이었고, 05 노트에서 만들어 둔 `MenuResponse` DTO는 아직 아무 데서도 쓰이지 않는다.

```java
// 지금의 MenuController — 토큰이 통하는지 보려고 만든 임시 응답
@GetMapping("/menus")
public List<String> getMenuList() {
    return List.of("아메리카노", "카페라떼", "바닐라라떼");
}
```

이번 노트는 메뉴 목록 하나를 끝에서 끝까지 진짜 데이터로 바꾸는 작업이다. 데이터가 스프링 안에 있고, Next.js 서버를 거쳐, 브라우저의 카탈로그 화면에 그려지는 흐름을 완성한다. 인증은 이미 되어 있으므로 이번에는 "데이터를 어디에 두고 어떤 길로 가져오느냐"에만 집중한다.

이번 노트에서는 다음 순서로 진행한다.

1. 데이터가 어떤 길로 브라우저에 오는지 정한다 (Route Handler, BFF)
2. 스프링에 엔티티 → 리포지토리 → 서비스 → 컨트롤러 계층을 만든다
3. 메뉴 목록 API를 공개 API로 연다
4. Postman으로 확인한다
5. Next.js의 Route Handler 목업을 스프링 호출로 바꾼다
6. 카탈로그의 API 파일에서 목업을 걷어낸다
7. 훅과 화면에 에러 상태를 더한다
8. 브라우저에서 확인한다

---

## 1. 데이터는 어떤 길로 오는가

06 노트에서 정한 원칙이 있다. 브라우저는 스프링을 직접 부르지 않는다. 브라우저 → Next.js 서버 → 스프링 순서로만 간다(BFF). 토큰이 HttpOnly 쿠키에 있어서 브라우저 자바스크립트가 읽을 수 없고, 스프링 주소도 브라우저에 노출하지 않는다는 이유였다.

지금까지 스프링을 부른 곳은 두 종류였다.

| 부른 곳 | 종류 | 예 |
|---|---|---|
| Server Action | 서버 | `loginAction.ts`, `logoutAction.ts` |
| 서버 컴포넌트 | 서버 | `BackendCheck.tsx` → `backendCheckApi.ts` |

둘 다 서버에서 실행되므로 `cookies()`로 토큰을 읽어 `backendFetch()`로 넘길 수 있었다.

그런데 메뉴 카탈로그(`MenuCatalog.tsx`)는 클라이언트 컴포넌트다. 검색어를 치고, 카테고리 탭을 누르고, 정렬을 바꾸면 그때그때 목록을 다시 받아야 한다. 이런 상호작용은 브라우저에서 일어나므로 서버 컴포넌트로 바꿀 수 없다. 클라이언트 컴포넌트가 스프링 데이터를 받으려면 Next.js 서버에 창구가 하나 필요하다.

그 창구가 Route Handler다. `app/api/menus/route.ts`에 `GET` 함수를 두면 브라우저가 `/api/menus`를 fetch할 때 Next.js 서버에서 그 함수가 실행된다. 서버이므로 `backendFetch()`를 그대로 쓸 수 있다.

```
브라우저                      Next.js 서버                        스프링
MenuCatalog (클라이언트)       app/api/menus/route.ts             MenuController
  fetch("/api/menus?q=라떼") ─▶  GET(request)                     GET /api/menus?q=라떼
                                 backendFetch("/api/menus?q=…") ─▶  MenuService → MenuRepository
                              ◀─ Response.json(body)            ◀─  List<MenuResponse>
```

재미있는 점은 `app/api/menus/route.tsx`가 이미 있다는 것이다. 프로젝트 초기에 만든 목업 Route Handler다. 안에 있는 배열을 지우고 스프링 호출로 바꾸면 된다. 경로가 같으니 브라우저 쪽 코드는 `fetch("/api/menus")`를 그대로 쓴다.

---

## 2. 백엔드 — 계층 나누기

지금까지 백엔드에는 `controller`, `service`, `dto`, `security`, `config` 패키지가 있었다. 이번에 데이터를 담는 층이 둘 추가된다. `entity`(데이터 한 건의 모양)와 `repository`(데이터를 꺼내 주는 곳)다.

```
controller/MenuController   ← HTTP 요청·응답
service/MenuService         ← 필터·정렬 규칙
repository/MenuRepository   ← 데이터 보관 (지금은 메모리, 다음 노트에서 DB)
entity/Menu                 ← 메뉴 한 건
dto/menu/MenuResponse       ← 밖으로 내보내는 모양
```

지금은 DB가 없으니 "굳이 이렇게 나눠야 하나" 싶을 수 있다. 하지만 다음 노트에서 `MenuRepository`만 JPA로 바꾸면 나머지 층은 손대지 않아도 된다. 지금 나눠 두는 것은 그 교체를 위한 준비다.

### 1) Menu 엔티티

프론트엔드 목업의 `Menu` 타입을 그대로 자바로 옮긴다. 카탈로그 카드가 쓰는 필드만 담고, 상세 페이지용 `story`와 `options`는 아직 넣지 않는다.

```java
package com.ncafe.backend.entity;

import java.time.LocalDate;
import java.util.List;

import lombok.Builder;
import lombok.Data;

/**
 * 메뉴 한 건. 아직 DB가 없으므로 평범한 자바 객체다.
 * 다음 노트에서 JPA 엔티티(@Entity)로 바뀌고, 데이터는 테이블로 옮겨 간다.
 */
@Data
@Builder
public class Menu {
    private Long id;
    private String slug;          // URL 에 쓰는 식별자 (/menus/{slug})
    private String name;
    private String englishName;
    private int price;
    private String categorySlug;  // coffee, non-coffee, tea, dessert, coworker-set
    private String description;
    private List<String> tags;
    private String emoji;
    private String tone;          // 카드 배경색 이름 (espresso, latte, matcha ...)
    private boolean soldOut;
    private boolean signature;
    private int likes;
    private int calories;
    private LocalDate createdAt;
}
```

- `slug`: URL에 쓰는 식별자다. `/menus/refactor-latte`처럼 사람이 읽을 수 있는 주소를 만들기 위한 것으로, 숫자 `id`와 별개로 둔다.
- `categorySlug`: 카테고리는 아직 프론트엔드 목업(`_mocks/categories.ts`)에 남아 있다. 백엔드 메뉴가 들고 있는 slug와 프론트 카테고리의 slug가 같아야 탭 필터가 맞아떨어진다.
- `tone`: 카드 배경색 이름이다. 프론트는 `Tone` 유니언 타입이지만 백엔드에서는 문자열로 둔다.
- `createdAt`은 `LocalDate`다. Jackson이 `"2026-01-12"` 형식의 문자열로 내보낸다.

### 2) MenuRepository — 메모리 저장소

프론트엔드 `_mocks/menus.ts`에 있던 13개 메뉴를 그대로 자바로 옮긴다. 길지만 데이터가 프론트에서 백엔드로 자리를 옮기는 것이 이번 노트의 핵심이므로 전부 옮긴다.

```java
package com.ncafe.backend.repository;

import java.time.LocalDate;
import java.util.List;

import org.springframework.stereotype.Repository;

import com.ncafe.backend.entity.Menu;

/**
 * 메뉴 저장소. 지금은 메모리에 고정된 목록을 들고 있다.
 *
 * 프론트엔드 목업(_mocks/menus.ts)에 있던 데이터를 그대로 옮겨 왔다.
 * 데이터가 "프론트 안"에서 "백엔드 안"으로 자리를 옮긴 것이 이번 노트의 핵심이고,
 * 다음 노트에서 이 클래스는 JPA 리포지토리로 교체된다.
 */
@Repository
public class MenuRepository {

    private final List<Menu> menus = List.of(
        Menu.builder().id(1L).slug("hello-world-americano").name("헬로 월드 아메리카노").englishName("Hello World Americano")
            .price(4200).categorySlug("coffee")
            .description("모든 시작은 여기서. 에티오피아 예가체프 베이스의 깔끔한 산미.")
            .tags(List.of("시그니처", "싱글 오리진", "집중")).emoji("☕").tone("espresso")
            .soldOut(false).signature(true).likes(328).calories(10).createdAt(LocalDate.of(2026, 1, 12)).build(),
        Menu.builder().id(2L).slug("refactor-latte").name("리팩터 라떼").englishName("Refactor Latte")
            .price(5200).categorySlug("coffee")
            .description("구조는 그대로, 맛은 더 부드럽게. 저온 스티밍 우유와 다크 로스트.")
            .tags(List.of("시그니처", "부드러움")).emoji("🥛").tone("latte")
            .soldOut(false).signature(true).likes(412).calories(180).createdAt(LocalDate.of(2026, 1, 12)).build(),
        Menu.builder().id(3L).slug("deploy-cold-brew").name("디플로이 콜드브루").englishName("Deploy Cold Brew")
            .price(5500).categorySlug("coffee")
            .description("18시간 추출. 배포 전날 밤처럼 길게 기다린 맛.")
            .tags(List.of("콜드브루", "묵직함")).emoji("🧊").tone("mocha")
            .soldOut(false).signature(false).likes(201).calories(15).createdAt(LocalDate.of(2026, 2, 3)).build(),
        Menu.builder().id(4L).slug("null-pointer-flat-white").name("널 포인터 플랫화이트").englishName("Null Pointer Flat White")
            .price(5000).categorySlug("coffee")
            .description("우유 거품은 거의 없이(null), 에스프레소의 존재감만 또렷하게.")
            .tags(List.of("진함", "더블샷")).emoji("🫖").tone("espresso")
            .soldOut(true).signature(false).likes(96).calories(120).createdAt(LocalDate.of(2026, 2, 20)).build(),
        Menu.builder().id(5L).slug("merge-conflict-mocha").name("머지 컨플릭트 모카").englishName("Merge Conflict Mocha")
            .price(5800).categorySlug("coffee")
            .description("다크 초콜릿과 화이트 초콜릿이 충돌하는 두 겹 모카.")
            .tags(List.of("초콜릿", "달콤")).emoji("🍫").tone("mocha")
            .soldOut(false).signature(false).likes(275).calories(320).createdAt(LocalDate.of(2026, 3, 1)).build(),
        Menu.builder().id(6L).slug("idle-matcha-latte").name("아이들 말차 라떼").englishName("Idle Matcha Latte")
            .price(5600).categorySlug("non-coffee")
            .description("카페인 걱정 없이 느긋하게. 우지 말차와 오트 밀크.")
            .tags(List.of("말차", "비건 옵션")).emoji("🍵").tone("matcha")
            .soldOut(false).signature(true).likes(389).calories(160).createdAt(LocalDate.of(2026, 3, 10)).build(),
        Menu.builder().id(7L).slug("sandbox-strawberry-milk").name("샌드박스 딸기 우유").englishName("Sandbox Strawberry Milk")
            .price(5400).categorySlug("non-coffee")
            .description("실패해도 괜찮은 공간처럼 편안한, 생딸기 콩포트 우유.")
            .tags(List.of("생과일", "인기")).emoji("🍓").tone("berry")
            .soldOut(false).signature(false).likes(302).calories(240).createdAt(LocalDate.of(2026, 3, 18)).build(),
        Menu.builder().id(8L).slug("async-earl-grey").name("어싱크 얼그레이").englishName("Async Earl Grey")
            .price(4800).categorySlug("tea")
            .description("기다리는 동안 다른 일을 하세요. 4분 우림 베르가못 홍차.")
            .tags(List.of("홍차", "향긋함")).emoji("🫖").tone("citrus")
            .soldOut(false).signature(false).likes(154).calories(5).createdAt(LocalDate.of(2026, 4, 2)).build(),
        Menu.builder().id(9L).slug("hotfix-lemon-ade").name("핫픽스 레몬에이드").englishName("Hotfix Lemon Ade")
            .price(5300).categorySlug("tea")
            .description("급할 때 바로 효과. 생레몬 두 개를 통째로 짠 탄산 에이드.")
            .tags(List.of("탄산", "리프레시")).emoji("🍋").tone("citrus")
            .soldOut(false).signature(false).likes(221).calories(140).createdAt(LocalDate.of(2026, 4, 15)).build(),
        Menu.builder().id(10L).slug("commit-cheesecake").name("커밋 치즈케이크").englishName("Commit Cheesecake")
            .price(6500).categorySlug("dessert")
            .description("하나 끝냈으면 저장할 시간. 바스크 스타일의 꾸덕한 치즈케이크.")
            .tags(List.of("디저트", "베스트")).emoji("🍰").tone("latte")
            .soldOut(false).signature(true).likes(468).calories(410).createdAt(LocalDate.of(2026, 1, 12)).build(),
        Menu.builder().id(11L).slug("stack-overflow-brownie").name("스택 오버플로 브라우니").englishName("Stack Overflow Brownie")
            .price(4800).categorySlug("dessert")
            .description("층층이 쌓다가 넘칠 만큼 올린 피칸 브라우니.")
            .tags(List.of("초콜릿", "견과")).emoji("🍫").tone("mocha")
            .soldOut(false).signature(false).likes(187).calories(380).createdAt(LocalDate.of(2026, 5, 4)).build(),
        Menu.builder().id(12L).slug("pair-programming-set").name("페어 프로그래밍 세트").englishName("Pair Programming Set")
            .price(16800).categorySlug("coworker-set")
            .description("둘이 함께. 샌드위치 2종 + 아메리카노 2잔. 한 명은 운전, 한 명은 네비.")
            .tags(List.of("2인", "식사", "할인")).emoji("🥪").tone("mint")
            .soldOut(false).signature(true).likes(256).calories(980).createdAt(LocalDate.of(2026, 5, 20)).build(),
        Menu.builder().id(13L).slug("all-nighter-box").name("올나이터 박스").englishName("All-nighter Box")
            .price(12500).categorySlug("coworker-set")
            .description("밤샘 작업용. 콜드브루 1L + 에너지바 3개 + 견과믹스.")
            .tags(List.of("밤샘", "테이크아웃")).emoji("🌙").tone("espresso")
            .soldOut(false).signature(false).likes(143).calories(760).createdAt(LocalDate.of(2026, 6, 1)).build()
    );

    public List<Menu> findAll() {
        return menus;
    }
}

```

- `@Repository`: `@Service`, `@Component`와 같은 빈 등록 애너테이션이다. "데이터를 꺼내 주는 역할"이라는 뜻만 더해진다. 다음 노트에서 이 클래스를 지우고 `JpaRepository`를 상속한 인터페이스로 바꿀 때, 서비스는 `findAll()`을 그대로 부른다.
- `List.of(...)`는 불변 리스트다. 지금은 조회만 하므로 충분하다.

### 3) MenuResponse — 응답 전용 모양

05 노트에서 만들어 두었던 `MenuResponse`를 실제 필드로 채운다. 기존의 `category`, `onSale` 같은 임시 필드는 버리고 엔티티와 맞춘다.

```java
package com.ncafe.backend.dto.menu;

import java.time.LocalDate;
import java.util.List;

import com.ncafe.backend.entity.Menu;

import lombok.Builder;
import lombok.Data;

/**
 * GET /api/menus 가 내려주는 메뉴 한 건의 모양.
 *
 * 엔티티(Menu)를 그대로 내보내지 않고 응답 전용 객체로 한 번 옮긴다.
 * 지금은 필드가 거의 같지만, 나중에 엔티티에 원가·재고처럼 손님에게 보이면 안 되는 컬럼이 생겨도
 * 응답 모양은 여기서 통제할 수 있다.
 */
@Data
@Builder
public class MenuResponse {
    private Long id;
    private String slug;
    private String name;
    private String englishName;
    private int price;
    private String categorySlug;
    private String description;
    private List<String> tags;
    private String emoji;
    private String tone;
    private boolean soldOut;
    private boolean signature;
    private int likes;
    private int calories;
    private LocalDate createdAt;

    public static MenuResponse from(Menu menu) {
        return MenuResponse.builder()
                .id(menu.getId())
                .slug(menu.getSlug())
                .name(menu.getName())
                .englishName(menu.getEnglishName())
                .price(menu.getPrice())
                .categorySlug(menu.getCategorySlug())
                .description(menu.getDescription())
                .tags(menu.getTags())
                .emoji(menu.getEmoji())
                .tone(menu.getTone())
                .soldOut(menu.isSoldOut())
                .signature(menu.isSignature())
                .likes(menu.getLikes())
                .calories(menu.getCalories())
                .createdAt(menu.getCreatedAt())
                .build();
    }
}
```

지금은 `Menu`와 `MenuResponse`의 필드가 거의 같다. 그래도 엔티티를 컨트롤러에서 직접 `return`하지 않는다. 다음 노트에서 `Menu`가 JPA 엔티티가 되면 원가, 재고, 연관 관계처럼 손님에게 보이면 안 되거나 JSON으로 바꾸기 곤란한 필드가 생긴다. 응답 모양은 DTO에서 통제한다는 습관을 지금 들인다. `from()` 정적 메서드가 변환을 한 곳에 모은다.

### 4) MenuService — 필터와 정렬

프론트엔드 목업 `menuCatalogApi.ts`의 `fetchMenus()`가 하던 일(카테고리 필터, 검색어 매칭, 정렬, 품절 뒤로 보내기)을 그대로 서버로 옮긴다.

```java
package com.ncafe.backend.service;

import java.util.Comparator;
import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import com.ncafe.backend.dto.menu.MenuResponse;
import com.ncafe.backend.entity.Menu;
import com.ncafe.backend.repository.MenuRepository;

/**
 * 메뉴 목록 조회. 프론트엔드 목업(menuCatalogApi.ts)이 하던 필터·정렬을 그대로 서버로 옮겼다.
 */
@Service
public class MenuService {

    private final MenuRepository menuRepository;

    public MenuService(MenuRepository menuRepository) {
        this.menuRepository = menuRepository;
    }

    /**
     * @param category 카테고리 slug. null 또는 "all" 이면 전체
     * @param q        검색어. 이름·영문 이름·태그에 부분 일치
     * @param sort     popular(기본) | newest | price-asc | price-desc
     */
    public List<MenuResponse> getMenus(String category, String q, String sort) {
        String keyword = StringUtils.hasText(q) ? q.trim().toLowerCase() : null;
        boolean allCategories = !StringUtils.hasText(category) || "all".equals(category);

        return menuRepository.findAll().stream()
                .filter(m -> allCategories || m.getCategorySlug().equals(category))
                .filter(m -> keyword == null || matches(m, keyword))
                .sorted(comparatorOf(sort))
                .map(MenuResponse::from)
                .toList();
    }

    private boolean matches(Menu m, String keyword) {
        if (m.getName().toLowerCase().contains(keyword)) return true;
        if (m.getEnglishName().toLowerCase().contains(keyword)) return true;
        return m.getTags().stream().anyMatch(t -> t.toLowerCase().contains(keyword));
    }

    private Comparator<Menu> comparatorOf(String sort) {
        Comparator<Menu> bySort = switch (sort == null ? "popular" : sort) {
            case "price-asc"  -> Comparator.comparingInt(Menu::getPrice);
            case "price-desc" -> Comparator.comparingInt(Menu::getPrice).reversed();
            case "newest"     -> Comparator.comparing(Menu::getCreatedAt).reversed();
            default           -> Comparator.comparingInt(Menu::getLikes).reversed();
        };
        // 품절은 어떤 정렬이든 뒤로 보낸다
        return Comparator.comparing(Menu::isSoldOut).thenComparing(bySort);
    }
}
```

- `category`가 null이거나 `"all"`이면 전체다. 프론트의 "전체" 탭은 `all`이라는 가짜 slug를 쓰므로 그것도 받아 준다.
- 검색은 이름·영문 이름·태그에 부분 일치다. "라떼"를 치면 "리팩터 라떼", "아이들 말차 라떼"가, "비건"을 치면 태그에 "비건 옵션"이 있는 메뉴가 나온다.
- 정렬 키는 프론트의 `SortKey`와 같은 문자열(`popular`, `newest`, `price-asc`, `price-desc`)이다. 모르는 값이 오면 기본인 인기순으로 처리한다. 400을 내는 대신 기본값으로 흡수한 것은, 정렬 키가 틀렸다고 목록을 안 보여줄 이유는 없기 때문이다.
- 품절은 어떤 정렬이든 뒤로 간다. `Comparator.comparing(Menu::isSoldOut)`이 false(판매 중)를 먼저 두고, 같은 그룹 안에서 `thenComparing(bySort)`로 정렬한다.
- 마지막에 `map(MenuResponse::from)`으로 엔티티를 응답 DTO로 바꿔 내보낸다. 서비스 바깥으로 엔티티가 나가지 않는다.

### 5) MenuController — `@RequestParam`

```java
package com.ncafe.backend.controller;

import java.util.List;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.ncafe.backend.dto.menu.MenuResponse;
import com.ncafe.backend.service.MenuService;

@RestController
@RequestMapping("/api")
public class MenuController {

    private final MenuService menuService;

    public MenuController(MenuService menuService) {
        this.menuService = menuService;
    }

    /**
     * GET /api/menus?category=coffee&q=라떼&sort=price-asc
     * 세 파라미터 모두 선택이다. 없으면 전체 메뉴를 인기순으로 내려준다.
     */
    @GetMapping("/menus")
    public List<MenuResponse> getMenuList(
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String sort) {

        return menuService.getMenus(category, q, sort);
    }

    @GetMapping("/admin/menus")
    public List<String> getAdminMenuList() {

        return List.of("아메리카노", "카페라떼", "바닐라라떼", "초크라떼");
    }
}
```

- `@RequestParam(required = false)`: 쿼리 스트링(`?category=coffee&q=라떼`)을 메서드 파라미터로 받는다. `required = false`가 없으면 파라미터가 빠진 요청에 400이 난다. 세 개 모두 선택이라 전부 false다. 빠진 값은 null로 들어오고, null 처리는 서비스가 한다.
- 반환 타입이 `List<MenuResponse>`다. `@RestController`라서 Jackson이 JSON 배열로 바꿔 준다.
- `/admin/menus`는 그대로 둔다. 관리자 페이지의 `BackendCheck`가 문자열 배열을 기대하고 있고, 이번 노트의 범위는 손님용 카탈로그다.

---

## 3. SecurityConfig — 메뉴 목록은 공개

지금 규칙은 `/api/auth/**`만 공개이고 나머지는 전부 `authenticated()`다. 메뉴 목록은 로그인 전 손님이 보는 화면이므로 공개해야 한다. 단, 조회(GET)만 연다. 나중에 생길 메뉴 등록·수정(POST, PUT)은 관리자 전용이어야 하므로 메서드를 명시한다.

```java
import org.springframework.http.HttpMethod;
// ...
            .authorizeHttpRequests(auth -> auth
                // 로그인, 회원가입 등 공개 API는 토큰 없이도 접근 허용
                .requestMatchers("/api/auth/**", "/error").permitAll()
                // 메뉴 목록은 손님이 로그인 전에 보는 화면이므로 조회(GET)만 공개
                .requestMatchers(HttpMethod.GET, "/api/menus/**").permitAll()
                // 관리자만 접근 가능
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                // 그 외의 모든 요청은 인증된 사용자만 접근 가능
                .anyRequest().authenticated()
            )
```

- `requestMatchers(HttpMethod.GET, "/api/menus/**")`: 경로만 적는 두 인자 버전과 달리 메서드까지 조건에 넣는다. 같은 `/api/menus`라도 POST는 아래 `anyRequest().authenticated()`에 걸려 401이 난다.
- 규칙은 위에서부터 먼저 맞는 것이 적용된다. 공개 규칙을 `anyRequest()`보다 위에 두어야 한다.
- `/api/admin/menus`는 `/api/menus/**`에 맞지 않으므로(`/api/admin/...`으로 시작한다) 그대로 관리자 전용이다.

---

## 4. Postman으로 확인하기 (메뉴)

스프링을 재시작하고 확인한다. 요점은 토큰 없이 메뉴 데이터가 나오는가와 쿼리 파라미터가 먹는가다.

| # | 요청 | 기대 | 확인할 것 |
|---|---|---|---|
| 1 | `GET /api/menus` (헤더 없음) | 200, 13개 | 첫 항목이 좋아요 468의 "커밋 치즈케이크", 마지막이 품절인 "널 포인터 플랫화이트" |
| 2 | `GET /api/menus?category=coffee` | 200, 5개 | 모두 `categorySlug: "coffee"` |
| 3 | `GET /api/menus?q=라떼` | 200, 2개 | 리팩터 라떼, 아이들 말차 라떼 |
| 4 | `GET /api/menus?q=비건` | 200, 1개 | 태그로 매치된 아이들 말차 라떼 |
| 5 | `GET /api/menus?sort=price-asc` | 200 | 4200부터 오름차순, 품절(5000)은 맨 뒤 |
| 6 | `GET /api/menus?sort=newest` | 200 | `createdAt` 2026-06-01 이 첫 번째 |
| 7 | `GET /api/menus?category=nope` | 200, `[]` | 없는 카테고리는 빈 배열 |
| 8 | `POST /api/menus` (헤더 없음) | 401 | GET만 공개했으므로 다른 메서드는 보호 |
| 9 | `GET /api/admin/menus` (헤더 없음) | 401 | 관리자 API는 그대로 보호 |
| 10 | newlec / 123 토큰으로 `GET /api/menus` | 200 | 로그인 상태에서도 당연히 된다 |
| 11 | Bearer `abc.def.ghi`로 `GET /api/menus` | 200 | 공개 API라 위조 토큰이 있어도 거절하지 않는다 (아래 9-1 참고) |

1번 응답의 첫 항목은 이렇다.

```json
{
  "id": 10,
  "slug": "commit-cheesecake",
  "name": "커밋 치즈케이크",
  "englishName": "Commit Cheesecake",
  "price": 6500,
  "categorySlug": "dessert",
  "description": "하나 끝냈으면 저장할 시간. 바스크 스타일의 꾸덕한 치즈케이크.",
  "tags": ["디저트", "베스트"],
  "emoji": "🍰",
  "tone": "latte",
  "soldOut": false,
  "signature": true,
  "likes": 468,
  "calories": 410,
  "createdAt": "2026-01-12"
}
```

8번과 9번이 401인 것을 꼭 확인한다. "공개로 열었다"가 "/api/menus 전부를 열었다"가 아니라 GET 하나만 열었다는 뜻임을 눈으로 보는 단계다.

---

## 5. 프론트엔드 — Route Handler 목업 교체

`app/api/menus/route.tsx`를 지우고 `route.ts`로 새로 만든다. JSX가 없으니 확장자는 `.ts`다. 안에 있던 목업 배열 다섯 개와 필터 코드는 모두 사라지고, 스프링에 그대로 넘기는 코드만 남는다.

```ts
import type { NextRequest } from "next/server";
import { backendFetch, BACKEND_URL } from "@/app/_lib/auth/backend";

/**
 * GET /api/menus?category=&q=&sort=  →  스프링 GET /api/menus?...
 *
 * 브라우저(클라이언트 컴포넌트)가 스프링을 직접 부르지 않고 이 Route Handler 를 거친다(BFF).
 * - 스프링 주소(BACKEND_URL)가 브라우저에 노출되지 않고 CORS 설정도 필요 없다.
 * - 쿠키의 토큰은 backendFetch 가 Authorization 헤더로 바꿔 실어 준다.
 *   메뉴 목록은 공개 API 라 토큰이 없어도 되지만, 로그인 상태라면 그대로 전달된다.
 *
 * 전에는 여기에 목업 배열이 있었다. 이제 데이터는 스프링에만 있다.
 */
export async function GET(request: NextRequest) {
  const { search } = request.nextUrl; // "?category=coffee&q=라떼&sort=popular" 를 그대로 넘긴다

  try {
    const res = await backendFetch(`/api/menus${search}`);
    const body = await res.json();
    return Response.json(body, { status: res.status }); // 성공·실패 응답을 그대로 전달
  } catch {
    return Response.json(
      { status: 502, error: "Bad Gateway", message: `백엔드(${BACKEND_URL})에 연결할 수 없어요.`, path: "/api/menus" },
      { status: 502 },
    );
  }
}
```

- `request.nextUrl.search`는 `"?category=coffee&q=라떼&sort=popular"` 같은 쿼리 스트링 전체다. 하나하나 꺼내서 다시 조립하지 않고 그대로 뒤에 붙인다. 파라미터가 늘어나도 이 파일은 바뀌지 않는다.
- `backendFetch()`를 그대로 쓴다. 06 노트에서 만든 함수다. 쿠키에 토큰이 있으면 `Authorization` 헤더를 붙이고, 없으면 붙이지 않는다. 메뉴 목록은 공개 API이므로 비로그인 손님도 정상적으로 받는다.
- 상태 코드를 그대로 전달한다. `Response.json(body, { status: res.status })`. 스프링이 401이나 500을 주면 브라우저도 같은 코드를 받는다. 중간에서 200으로 바꿔 숨기지 않는다.
- 연결 자체가 실패하면 502다. 스프링이 꺼져 있을 때 `fetch`가 예외를 던진다. 이때 본문은 이전 노트의 `ErrorResponse`와 같은 모양으로 만들어 준다. 그래야 브라우저 쪽에서 "백엔드가 거절한 경우"와 "백엔드가 없는 경우"를 같은 코드로 읽을 수 있다. 502 Bad Gateway는 "중간 서버가 뒤쪽 서버에서 유효한 응답을 못 받았다"는 뜻으로, 지금 상황에 정확히 맞는 코드다.

이 파일은 서버에서 실행되므로 `backendFetch` 안의 `cookies()` 호출이 문제없이 동작한다. 클라이언트 컴포넌트가 `@/app/_lib/auth/backend`를 import하면 `next/headers` 때문에 빌드 오류가 나는데, Route Handler가 중간에 있어서 그 경계가 지켜진다.

---

## 6. 프론트엔드 — `menuCatalogApi.ts`에서 목업 걷어내기

카탈로그가 데이터를 가져오는 함수들이 모여 있는 파일이다. 메뉴 관련 함수만 바꾸고, 카테고리와 좋아요는 아직 목업으로 둔다.

```ts
import { categories } from "@/app/_mocks/categories";
import { likedMenuIds } from "@/app/_mocks/session";
import { delay } from "@/app/_mocks/delay";
import type { Category, Menu, Tone } from "@/app/_types";

export type SortKey = "popular" | "price-asc" | "price-desc" | "newest";

export type MenuQuery = {
  category: string; // 'all' | slug
  q: string;
  sort: SortKey;
};

/** 스프링 MenuResponse 와 같은 모양. 백엔드 DTO 의 필드 이름을 그대로 따른다 */
export type MenuResponse = {
  id: number;
  slug: string;
  name: string;
  englishName: string;
  price: number;
  categorySlug: string;
  description: string;
  tags: string[];
  emoji: string;
  tone: string;
  soldOut: boolean;
  signature: boolean;
  likes: number;
  calories: number;
  createdAt: string; // "2026-01-12"
};

/** API 응답 → 화면 타입. 아직 API 가 주지 않는 필드(story, options)는 빈 값으로 채운다 */
function toMenu(r: MenuResponse): Menu {
  return { ...r, tone: r.tone as Tone, story: "", options: [] };
}

/** 노출 중인 카테고리 (목업) */
export async function fetchCategories(): Promise<Category[]> {
  await delay(150);
  return categories.filter((c) => c.visible).sort((a, b) => a.order - b.order);
}

/**
 * 메뉴 목록 조회 — GET /api/menus?category=&q=&sort=
 * Next.js Route Handler(app/api/menus/route.ts)를 거쳐 스프링까지 간다. 필터·정렬은 서버가 한다.
 */
export async function fetchMenus(query: MenuQuery): Promise<Menu[]> {
  const params = new URLSearchParams();
  if (query.category !== "all") params.set("category", query.category);
  if (query.q.trim()) params.set("q", query.q.trim());
  params.set("sort", query.sort);

  const res = await fetch(`/api/menus?${params}`);
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { message?: string } | null;
    throw new Error(body?.message ?? `메뉴를 불러오지 못했어요. (HTTP ${res.status})`);
  }
  const list = (await res.json()) as MenuResponse[];
  return list.map(toMenu);
}

/** 카테고리별 메뉴 수. 전체 목록을 한 번 받아 센다 */
export async function fetchMenuCounts(): Promise<Record<string, number>> {
  const all = await fetchMenus({ category: "all", q: "", sort: "popular" });
  const counts: Record<string, number> = { all: all.length };
  for (const m of all) counts[m.categorySlug] = (counts[m.categorySlug] ?? 0) + 1;
  return counts;
}

/** 내 좋아요 목록 (목업) */
export async function fetchLikedIds(): Promise<number[]> {
  await delay(100);
  return [...likedMenuIds];
}

/** 좋아요 토글 (목업) — POST/DELETE /api/my/likes/{menuId} */
export async function toggleLike(menuId: number, liked: boolean): Promise<void> {
  await delay(120);
  const idx = likedMenuIds.indexOf(menuId);
  if (liked && idx === -1) likedMenuIds.push(menuId);
  if (!liked && idx !== -1) likedMenuIds.splice(idx, 1);
}

```

### 1) `MenuResponse` 타입 — 백엔드와 같은 모양

백엔드 `MenuResponse.java`의 필드를 그대로 TypeScript로 적는다. 필드 이름이 백엔드와 한 글자라도 다르면 `undefined`가 들어온다. 특히 `createdAt`은 백엔드에서 `LocalDate`지만 JSON으로는 `"2026-01-12"` 문자열이므로 `string`이다.

### 2) `toMenu()` — API 모양에서 화면 모양으로

화면이 쓰는 `Menu` 타입에는 `story`, `options`가 있지만 API는 아직 주지 않는다. 그 둘을 빈 값으로 채우고, `tone`은 문자열에서 `Tone` 유니언으로 단언한다. API 응답 타입과 화면 타입을 분리하고 변환을 이 한 함수에 모아 두면, 나중에 API가 `story`를 주기 시작해도 이 함수 한 줄만 바뀐다.

### 3) `fetchMenus()` — 진짜 fetch

- `URLSearchParams`로 쿼리를 조립한다. `"all"`과 빈 검색어는 보내지 않는다(백엔드가 null을 전체로 처리하므로 보내도 되지만, 주소를 깔끔하게 유지한다).
- `fetch("/api/menus?...")`: 상대 경로다. 같은 Next.js 서버의 Route Handler를 부른다. 스프링 주소는 여기 없다.
- 실패하면 `throw`한다. `res.ok`가 아니면 본문에서 `message`를 꺼내 `Error`로 던진다. 백엔드의 `ErrorResponse`든 Route Handler가 만든 502 본문이든 `message` 필드가 있으므로 같은 코드로 읽힌다. 본문이 JSON이 아닐 때를 위해 `.catch(() => null)`로 막아 둔다.
- 이전에 있던 필터·정렬 코드가 모두 사라졌다. 서버가 하기 때문이다. 목업 때는 "GET /api/menus?category=&q=&sort=" 라고 주석으로만 적어 두었던 것이 실제 호출이 되었다.

### 4) `fetchMenuCounts()` — 비동기가 된 카운트

카테고리 탭 옆의 숫자(전체 13, 커피 5, ...)는 전에는 목업 배열을 바로 세는 동기 함수였다. 데이터가 서버로 갔으니 이것도 비동기가 된다. 전체 목록을 한 번 받아서 센다. 카운트 전용 API를 만드는 대신 가장 단순한 방법을 택했다.

---

## 7. 프론트엔드 — 훅과 화면에 에러 상태 더하기

### 1) `useMenuCatalog.ts`

```ts
"use client";

import { useEffect, useState } from "react";
import type { Category, Menu } from "@/app/_types";
import {
  fetchCategories,
  fetchLikedIds,
  fetchMenuCounts,
  fetchMenus,
  toggleLike,
  type SortKey,
} from "./menuCatalogApi";

export function useMenuCatalog() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [category, setCategory] = useState("all");
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<SortKey>("popular");
  const [menus, setMenus] = useState<Menu[]>([]);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [likedIds, setLikedIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    fetchCategories().then(setCategories);
    fetchLikedIds().then((ids) => setLikedIds(new Set(ids)));
    fetchMenuCounts().then(setCounts).catch(() => setCounts({}));
  }, [retryKey]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const timer = setTimeout(() => {
      fetchMenus({ category, q, sort })
        .then((list) => {
          if (cancelled) return;
          setMenus(list);
          setLoading(false);
        })
        .catch((e: Error) => {
          if (cancelled) return;
          setMenus([]);
          setError(e.message);
          setLoading(false);
        });
    }, q ? 200 : 0); // 검색어 디바운스
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [category, q, sort, retryKey]);

  const handleToggleLike = async (menu: Menu) => {
    const next = !likedIds.has(menu.id);
    // 낙관적 업데이트
    setLikedIds((prev) => {
      const s = new Set(prev);
      if (next) s.add(menu.id); else s.delete(menu.id);
      return s;
    });
    setMenus((prev) => prev.map((m) => (m.id === menu.id ? { ...m, likes: m.likes + (next ? 1 : -1) } : m)));
    await toggleLike(menu.id, next);
  };

  return {
    categories, category, setCategory,
    q, setQ,
    sort, setSort,
    menus, loading, error, counts,
    likedIds, handleToggleLike,
    reset: () => { setCategory("all"); setQ(""); setSort("popular"); },
    retry: () => setRetryKey((k) => k + 1),
  };
}

```

바뀐 곳은 세 가지다.

- `counts`가 상태가 되었다. 전에는 `useMemo(() => countByCategory(), [])`였다. 이제 첫 `useEffect`에서 `fetchMenuCounts()`로 받아 온다.
- `error` 상태와 `.catch()`. 목업 때는 실패할 일이 없었지만, 진짜 서버는 꺼져 있을 수도 있고 500을 낼 수도 있다. `fetchMenus()`가 던진 `Error`의 `message`를 상태에 담고 `loading`을 끈다. 이게 없으면 서버가 꺼졌을 때 화면이 "불러오는 중…"에서 영원히 멈춘다.
- `retry()`와 `retryKey`. 두 `useEffect`의 의존성에 `retryKey`를 넣어, 버튼 한 번으로 카운트와 목록을 모두 다시 받는다.

### 2) `MenuCatalog.tsx`

로딩 → 에러 → 빈 결과 → 목록 순서로 분기를 하나 추가한다. 상태 표시줄도 에러일 때는 "연결 오류"로 바꾼다.

```tsx
      <div className={styles.status} aria-live="polite">
        {c.loading ? "불러오는 중…" : c.error ? "연결 오류" : <>총 <strong>{c.menus.length}</strong>개 메뉴</>}
      </div>

      {c.loading ? (
        {/* 스켈레톤 — 그대로 */}
      ) : c.error ? (
        <div className="emptyState" role="alert">
          <span className="emoji">🔌</span>
          <strong>메뉴를 불러오지 못했어요</strong>
          <p>{c.error}</p>
          <button type="button" className="btn btnSm" onClick={c.retry}>다시 시도</button>
        </div>
      ) : c.menus.length === 0 ? (
        {/* 조건에 맞는 메뉴가 없어요 — 그대로 */}
      ) : (
        {/* 카드 그리드 — 그대로 */}
      )}
```

`role="alert"`는 스크린 리더가 에러 문장을 바로 읽어 주게 한다. `MenuCard`, `CategoryTabs`는 손대지 않는다. 데이터 출처가 바뀌어도 `Menu` 타입이 같으므로 화면 컴포넌트는 모른다.

---

## 8. 브라우저에서 확인하기

스프링(8080)과 Next.js(3000)를 모두 켜고 `http://localhost:3000/menus`를 연다.

1. 로그인하지 않은 상태에서 13개 메뉴가 보여야 한다. 공개 API다. 탭의 숫자(전체 13, 커피 5, 논커피 2, 티 & 에이드 2, 디저트 2, 코워커 세트 2)가 맞는지 본다.
2. "커피" 탭을 누르면 5개, 검색창에 "라떼"를 치면 2개로 줄어든다. 개발자 도구 Network 탭에서 `GET /api/menus?category=coffee&sort=popular` 같은 요청이 `localhost:3000`으로 가는 것을 본다. 8080은 어디에도 보이지 않는다.
3. 정렬을 "가격 낮은순"으로 바꾸면 품절인 널 포인터 플랫화이트가 가격(5,000원)과 상관없이 맨 뒤로 간다.
4. 스프링을 끄고 탭을 하나 눌러 본다. "메뉴를 불러오지 못했어요 / 백엔드(`http://localhost:8080`)에 연결할 수 없어요." 가 나오고, 스프링을 다시 켠 뒤 다시 시도를 누르면 목록이 돌아온다.
5. 로그인한 상태에서도 같은 화면이 나와야 한다. 토큰이 헤더에 실려 가지만 공개 API라 결과는 같다.

Next.js 터미널에도 Route Handler가 지나간 흔적이 남는다.

```
GET /api/menus?category=coffee&sort=popular 200 in 34ms (next.js: 13ms, proxy.ts: 7ms, application-code: 14ms)
```

`proxy.ts`가 찍힌 것에 주목한다. 07 노트의 문지기는 `/api/menus` 요청에도 실행된다(`matcher`가 정적 파일만 제외하기 때문이다). 그래서 액세스 토큰이 만료된 채 카탈로그를 열어도, Route Handler에 닿기 전에 재발급이 끝나 `backendFetch`에는 유효한 토큰이 간다.

---

## 9. 주의할 사항과 정리 (메뉴)

### 1) 공개 API에 잘못된 토큰이 와도 거절하지 않는다

Postman 11번에서 위조 토큰을 붙여도 200이 나왔다. `JwtAuthenticationFilter`는 토큰이 무효하면 출입증을 발급하지 않고 지나갈 뿐 요청을 끊지 않는다. 그 다음 인가 단계에서 `GET /api/menus`는 `permitAll()`이므로 출입증이 없어도 통과한다. 토큰이 없는 것과 같은 취급이다. 보호된 경로였다면 같은 상황에서 401이 났을 것이다(이전 노트). "필터는 판정하지 않고, 인가 규칙이 판정한다"는 역할 분리가 그대로 지켜진다.

### 2) `required = false`의 null은 서비스가 받는다

컨트롤러에서 `category == null ? "all" : category`처럼 기본값을 넣고 싶어질 수 있다. 하지만 "비어 있으면 전체"라는 것은 업무 규칙이므로 서비스에 둔다. 컨트롤러는 HTTP에서 값을 꺼내 넘기는 일만 한다. `@RequestParam(defaultValue = "popular")`로 기본값을 애너테이션에 적는 방법도 있는데, 이번에는 "모르는 값도 인기순"이라는 규칙까지 서비스에 함께 두기 위해 null을 그대로 넘겼다.

### 3) `LocalDate`는 문자열로 나간다

Spring Boot 4(Jackson 3)는 `java.time` 타입을 기본으로 ISO 문자열(`"2026-01-12"`)로 직렬화한다. 별도 설정이 필요 없다. 프론트의 `MenuResponse.createdAt`을 `string`으로 둔 이유다. `Date` 객체가 필요하면 받는 쪽에서 `new Date(r.createdAt)`으로 바꾼다.

### 4) 상태 코드는 중간에서 바꾸지 않는다

Route Handler가 스프링 응답을 전달할 때 `status: res.status`를 꼭 넘긴다. 이걸 빼면 `Response.json()`의 기본값인 200으로 나가서, 스프링이 500을 냈는데 브라우저는 "성공"으로 받고 `list.map`에서 터진다. 에러를 삼키는 중간 서버는 디버깅을 가장 어렵게 만든다.

### 5) 아직 목업으로 남은 것

이번 노트는 카탈로그의 메뉴 목록 한 줄기만 바꿨다. 다음은 아직 `_mocks`를 읽는다.

- 카테고리 목록 (`fetchCategories`) 과 좋아요 (`fetchLikedIds`, `toggleLike`)
- 메뉴 상세 페이지 (`/menus/[slug]`), 홈의 시그니처 메뉴, 관리자 메뉴 관리

데이터가 백엔드로 갔으니 이들을 바꾸는 작업은 같은 패턴의 반복이다. 특히 상세 페이지는 `GET /api/menus/{slug}` 하나를 추가하고 `story`, `options`를 `MenuResponse`에 넣으면 된다. DB를 붙인 뒤에 하는 것이 수고가 덜하다.

### 6) 정리

| 층 | 파일 | 역할 |
|---|---|---|
| 브라우저 | `menuCatalogApi.ts` | `fetch("/api/menus?...")`, `MenuResponse` → `Menu` 변환, 실패 시 throw |
| Next.js 서버 | `app/api/menus/route.ts` | 쿼리를 그대로 스프링에 전달, 상태 코드 그대로 반환, 연결 실패 502 |
| 스프링 | `MenuController` | `@RequestParam` 세 개를 서비스로 |
| 스프링 | `MenuService` | 필터·정렬·품절 뒤로, 엔티티 → DTO |
| 스프링 | `MenuRepository` | 메뉴 13개 (메모리) |

### 7) 이번 노트에서 추가·수정된 파일

**백엔드 (추가)**

- `entity/Menu.java`
- `repository/MenuRepository.java`
- `service/MenuService.java`

**백엔드 (수정)**

- `dto/menu/MenuResponse.java` — 실제 필드로 교체, `from()`
- `controller/MenuController.java` — `MenuService` 주입, `@RequestParam`
- `config/SecurityConfig.java` — `GET /api/menus/**` 공개

**프론트엔드 (추가·삭제)**

- `app/api/menus/route.ts` — 추가 (스프링으로 전달)
- `app/api/menus/route.tsx` — 삭제 (목업)

**프론트엔드 (수정)**

- `app/menus/_components/MenuCatalog/menuCatalogApi.ts` — 메뉴 목업 제거, `MenuResponse`, `fetchMenuCounts()`
- `app/menus/_components/MenuCatalog/useMenuCatalog.ts` — counts 상태, error, retry
- `app/menus/_components/MenuCatalog/MenuCatalog.tsx` — 에러 분기

---

## 마무리

이번 노트로 메뉴 데이터가 처음으로 스프링에서 출발해 Next.js 서버를 거쳐 브라우저에 도착했다. 클라이언트 컴포넌트가 백엔드 데이터를 받는 길(Route Handler)이 생겼고, 백엔드에는 엔티티·리포지토리·서비스 계층이 자리를 잡았다. 메뉴 목록은 공개 API로, 그 외는 여전히 보호 상태다.

데이터는 아직 자바 코드 안의 `List.of(...)`에 있다. 서버를 재시작하면 그대로지만, 메뉴를 추가하려면 코드를 고쳐야 한다. 그리고 `RefreshTokenStore`는 여전히 메모리 Map이라 서버를 재시작하면 모든 사용자가 로그아웃된다. 두 문제 모두 서버 바깥의 저장소가 필요하다는 뜻이고, 그 저장소를 띄우는 것이 먼저다.
