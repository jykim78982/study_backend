---
tags: [요약, ORM, JPA, SpringDataJPA, JPQL, 연관관계, 엔티티]
---

# ORM과 JPA 요약

같은 데이터를 담는 두 구조, **객체(자바)** 와 **테이블(DB)** 사이를 매핑하는 것이 ORM이고, 그 자바 표준이 JPA다. SQL을 직접 쓰는 대신 엔티티와 리포지토리 메서드로 데이터를 다룬다.

## 1. 한눈에 보기

| 주제 | 핵심 |
|---|---|
| ORM | 객체와 테이블 두 구조를 매핑한다. 자동화는 늘 있어 왔다 |
| JPA | ORM의 통일된 설정 표준. 구현체는 Hibernate |
| 엔티티 중심 | 엔티티만 보고 개발한다는 오브젝트 DB 관점 |
| Spring Data JPA | 인터페이스만 만들면 구현체를 스프링이 만들어 준다 |
| `JpaRepository` | `save`, `findById`, `findAll`, `deleteById` 등을 물려받는다 |
| 쿼리 메서드 | 메서드 이름으로 쿼리를 정의한다 (`findByNameContaining`) |
| 엔티티 매핑 | `@Entity`, `@Table`, `@Id`, `@Column` |
| 연관관계 | `@ManyToOne`, `@OneToMany`, `@OneToOne`. JOIN을 객체로 표현한다 |
| 복합키 | `@EmbeddedId` 또는 `@IdClass` |
| JPQL / `@Query` | 쿼리 메서드 이름이 길어질 때 쿼리를 직접 쓴다. 대상이 테이블이 아니라 엔티티다 |
| 파라미터 바인딩 | `:이름`과 `@Param` |
| 수정 쿼리 | `@Modifying` + `@Query` (`updatePrice` 예제) |

## 2. 개념 정리

### 2-1. 구현하지 않은 리포지토리는 누가 만드나

```java
public interface MenuRepository extends JpaRepository<Menu, Long> {
    List<Menu> findByNameContaining(String keyword);   // 이름만으로 쿼리가 만들어진다
}
```

인터페이스만 정의하면 스프링 데이터 JPA가 구현체를 만들어 빈으로 등록한다.

### 2-2. 연관관계 매핑

| 관계 | 어노테이션 |
|---|---|
| 다대일 | 다(多) 쪽에 `@ManyToOne` |
| 일대다 | 일(一) 쪽에 `@OneToMany` |
| 일대일 | `@OneToOne` |

- 쿼리 메서드에서도 연관된 엔티티의 필드로 조인한다.

### 2-3. 쿼리 메서드가 감당이 안 될 때

| 수단 | 용도 |
|---|---|
| JPQL / `@Query` | 정적인 복잡한 쿼리 |
| Criteria API, QueryDSL | 동적 쿼리 |
| 네이티브 쿼리 | DB 고유 기능 |

**기본은 쿼리 메서드, 예외는 `@Query`.** 동적 쿼리가 필요하면 JPQL의 한계 때문에 다른 도구를 쓴다.

### 2-4. 설계 관점

- **날것 API와 화면용 API는 다르다.** JPA로 엔티티를 쉽게 꺼낼 수 있어도, 화면에 필요한 모양은 별도로 설계한다.
- 컨벤션은 기계가 코드를 만들어도 지켜야 한다. 사람이 읽고 유지하기 때문이다.

## 3. 자주 헷갈리는 것

- **JPA vs ORM vs Hibernate:** ORM은 개념, JPA는 표준 명세, Hibernate는 구현체.
- **JPQL은 SQL이 아니다.** 테이블이 아니라 엔티티와 필드 이름을 쓴다.
- LIKE 검색은 키워드의 특수문자(`%`, `_`) 처리를 신경 써야 한다.
- 일부 기본 메서드는 버전에 따라 이름이 바뀌었다.

## 4. 이 카테고리의 실습, 오답노트, 참고자료

- 실습: MenuRepository로 첫 API 만들기, JPA 기본 메서드와 Postman으로 CRUD 완성
- 오답노트: JPA 리포지토리와 조회 도구, JPA 엔티티 상속 매핑, ORM 개념과 엔티티 매핑
- 참고자료: ORM 개념과 주요 프레임워크, Spring Data JPA 쿼리 메서드, JPQL, JPQL의 한계와 동적 쿼리
