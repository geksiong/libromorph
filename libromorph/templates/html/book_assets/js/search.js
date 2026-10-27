/**
 * search.js: Instant client-side search and filtering for Table of Contents and Index.
 */

document.addEventListener("DOMContentLoaded", function () {
  initLiveFilter();
});

function initLiveFilter() {
  const searchInput = document.getElementById("lm-toc-search");
  if (!searchInput) return;

  searchInput.addEventListener("input", function (e) {
    const query = e.target.value.toLowerCase().trim();
    const navItems = document.querySelectorAll(".sidebar-toc-item");

    navItems.forEach((item) => {
      const text = item.textContent.toLowerCase();
      if (!query || text.includes(query)) {
        item.style.display = "";
      } else {
        item.style.display = "none";
      }
    });
  });

  const indexSearch = document.getElementById("lm-index-search");
  if (!indexSearch) return;

  indexSearch.addEventListener("input", function (e) {
    const q = e.target.value.toLowerCase().trim();
    const indexItems = document.querySelectorAll(".index-item");
    const sections = document.querySelectorAll(".index-letter-section");

    indexItems.forEach((item) => {
      const txt = item.textContent.toLowerCase();
      if (!q || txt.includes(q)) {
        item.style.display = "";
      } else {
        item.style.display = "none";
      }
    });

    sections.forEach((sec) => {
      const visibleChildren = sec.querySelectorAll(".index-item:not([style*='display: none'])");
      if (visibleChildren.length === 0 && q) {
        sec.style.display = "none";
      } else {
        sec.style.display = "";
      }
    });
  });
}
