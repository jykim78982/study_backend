---
layout: default
title: 백엔드 스터디 노트
---

<div id="pageLayout">

<aside id="sidebar">

<h1>목록</h1>

<ul id="noteList">
  <li><a href="07-15%5F컴퓨터와%20리눅스의%20역사.html">07-15_컴퓨터와 리눅스의 역사</a></li>
  <li><a href="07-14%5F데이터베이스%20논리%20설계와%20프론트엔드.html">07-14_데이터베이스 논리 설계와 프론트엔드</a></li>
  <li><a href="07-12%5FERD%20개념%20설계.html">07-12_ERD 개념 설계</a></li>
  <li><a href="07-10%5FNginx%20리버스%20프록시로%2080번%20포트%20서비스하기.html">07-10_Nginx 리버스 프록시로 80번 포트 서비스하기</a></li>
  <li><a href="07-10%5F도메인.html">07-10_도메인</a></li>
  <li><a href="07-10%5F데이터베이스%20모델링.html">07-10_데이터베이스 모델링</a></li>
  <li><a href="07-09%5F데이터베이스.html">07-09_데이터베이스</a></li>
  <li><a href="07-08%5F리눅스%20파일%20시스템%20실습.html">07-08_리눅스 파일 시스템 실습</a></li>
</ul>

<div id="pagination" style="display:flex;align-items:center;gap:12px;margin-top:16px;">
  <button id="prevPageBtn" type="button">&lt;</button>
  <span id="pageIndicator"></span>
  <button id="nextPageBtn" type="button">&gt;</button>
</div>

</aside>

<div id="mainContent" style="min-width:0;">
  <div id="noteViewer" style="display:none;"></div>
</div>

<aside id="rightSidebar"></aside>

</div>

<script>
(function () {
  var PAGE_SIZE = 5;
  var items = Array.prototype.slice.call(document.querySelectorAll("#noteList > li"));
  var currentPage = 1;
  var totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE));

  var prevBtn = document.getElementById("prevPageBtn");
  var nextBtn = document.getElementById("nextPageBtn");
  var indicator = document.getElementById("pageIndicator");
  var viewer = document.getElementById("noteViewer");

  function render() {
    var start = (currentPage - 1) * PAGE_SIZE;
    var end = start + PAGE_SIZE;
    items.forEach(function (item, index) {
      item.style.display = index >= start && index < end ? "" : "none";
    });
    indicator.textContent = currentPage + " / " + totalPages;
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;
  }

  prevBtn.addEventListener("click", function () {
    if (currentPage > 1) {
      currentPage -= 1;
      render();
    }
  });

  nextBtn.addEventListener("click", function () {
    if (currentPage < totalPages) {
      currentPage += 1;
      render();
    }
  });

  function loadNote(link, scroll) {
    viewer.style.display = "block";
    viewer.innerHTML = "불러오는 중...";
    if (scroll) {
      viewer.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    fetch(link.getAttribute("href"))
      .then(function (res) { return res.text(); })
      .then(function (html) {
        var parsed = new DOMParser().parseFromString(html, "text/html");
        var section = parsed.querySelector("section");
        viewer.innerHTML = section ? section.innerHTML : "내용을 불러오지 못했습니다.";
      })
      .catch(function () {
        viewer.innerHTML = "내용을 불러오지 못했습니다.";
      });
  }

  items.forEach(function (item) {
    var link = item.querySelector("a");
    if (!link) return;

    link.addEventListener("click", function (event) {
      event.preventDefault();
      loadNote(link, true);
    });
  });

  render();

  var latestLink = items.length > 0 ? items[0].querySelector("a") : null;
  if (latestLink) {
    loadNote(latestLink, false);
  }
})();
</script>
