/**
 * reader.js: Controls Reader Navigation, Theme Toggle, Font Size, and Vertical Layout.
 */

(function () {
  const STORAGE_KEY_THEME = "libromorph_color_mode";
  const STORAGE_KEY_FONT = "libromorph_font_size";
  const STORAGE_KEY_LAYOUT = "libromorph_layout_mode";

  document.addEventListener("DOMContentLoaded", function () {
    initReaderControls();
    initSidebar();
  });

  function initReaderControls() {
    // 1. Color Mode (light, dark, sepia)
    const savedColor = localStorage.getItem(STORAGE_KEY_THEME) || "auto";
    setColorMode(savedColor);

    const themeSelect = document.getElementById("lm-color-select");
    if (themeSelect) {
      themeSelect.value = savedColor;
      themeSelect.addEventListener("change", (e) => {
        setColorMode(e.target.value);
      });
    }

    // 2. Font Size Adjuster
    let currentFontSize = parseInt(localStorage.getItem(STORAGE_KEY_FONT), 10) || 100;
    applyFontSize(currentFontSize);

    const btnFontInc = document.getElementById("lm-font-inc");
    const btnFontDec = document.getElementById("lm-font-dec");
    if (btnFontInc) {
      btnFontInc.addEventListener("click", () => {
        if (currentFontSize < 160) {
          currentFontSize += 10;
          applyFontSize(currentFontSize);
        }
      });
    }
    if (btnFontDec) {
      btnFontDec.addEventListener("click", () => {
        if (currentFontSize > 70) {
          currentFontSize -= 10;
          applyFontSize(currentFontSize);
        }
      });
    }

    // 3. Writing Mode: Horizontal <-> Vertical
    const layoutToggleBtn = document.getElementById("lm-toggle-layout");
    if (layoutToggleBtn) {
      const savedLayout = localStorage.getItem(STORAGE_KEY_LAYOUT);
      if (savedLayout) {
        setLayoutMode(savedLayout);
      }

      layoutToggleBtn.addEventListener("click", () => {
        const isVertical = document.body.classList.contains("mode-vertical-rl");
        const newMode = isVertical ? "horizontal" : "vertical";
        setLayoutMode(newMode);
      });
    }
  }

  function setColorMode(mode) {
    document.documentElement.setAttribute("data-color-mode", mode);
    localStorage.setItem(STORAGE_KEY_THEME, mode);
  }

  function applyFontSize(sizePercent) {
    const content = document.querySelector(".reader-content") || document.body;
    content.style.fontSize = sizePercent + "%";
    localStorage.setItem(STORAGE_KEY_FONT, sizePercent.toString());
  }

  function setLayoutMode(mode) {
    const layoutToggleBtn = document.getElementById("lm-toggle-layout");
    if (mode === "vertical") {
      document.body.classList.add("mode-vertical-rl");
      document.body.classList.remove("mode-horizontal-tb");
      if (layoutToggleBtn) {
        layoutToggleBtn.innerHTML = "⇄ Switch to Horizontal";
      }
    } else {
      document.body.classList.add("mode-horizontal-tb");
      document.body.classList.remove("mode-vertical-rl");
      if (layoutToggleBtn) {
        layoutToggleBtn.innerHTML = "⇅ Switch to Vertical";
      }
    }
    localStorage.setItem(STORAGE_KEY_LAYOUT, mode);
  }

  function initSidebar() {
    const sidebar = document.getElementById("lm-sidebar");
    const backdrop = document.getElementById("lm-backdrop");
    const openBtn = document.getElementById("lm-sidebar-open");
    const closeBtn = document.getElementById("lm-sidebar-close");

    function openNav() {
      if (sidebar) sidebar.classList.add("open");
      if (backdrop) backdrop.classList.add("open");
    }

    function closeNav() {
      if (sidebar) sidebar.classList.remove("open");
      if (backdrop) backdrop.classList.remove("open");
    }

    if (openBtn) openBtn.addEventListener("click", openNav);
    if (closeBtn) closeBtn.addEventListener("click", closeNav);
    if (backdrop) backdrop.addEventListener("click", closeNav);
  }
})();
