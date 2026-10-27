/**
 * mermaid-init.js: Renders Mermaid diagram blocks using mermaid.js.
 *
 * Finds all .mermaid-diagram containers, reads the diagram source from the
 * embedded <script type="text/x-mermaid"> element, and renders an SVG into
 * the .mermaid-render target div. mermaid.js is only loaded on pages that
 * contain diagrams, and diagrams are re-rendered when the reader switches
 * between dark and light color modes.
 */

(function () {
  "use strict";

  // Keep in sync with MERMAID_VERSION in libromorph/mermaid_render.py
  var MERMAID_SRC = "https://cdn.jsdelivr.net/npm/mermaid@11.17.2/dist/mermaid.min.js";

  var renderCount = 0;
  var currentTheme = null;

  function themeForPage() {
    return document.documentElement.getAttribute("data-color-mode") === "dark" ? "dark" : "default";
  }

  function showSource(renderEl, text) {
    renderEl.innerHTML =
      '<p class="mermaid-error">⚠ Could not render diagram.</p>' +
      '<pre class="mermaid-source"><code></code></pre>';
    renderEl.querySelector("code").textContent = text;
  }

  function diagramSource(container) {
    var scriptEl = container.querySelector('script[type="text/x-mermaid"]');
    // Undo the "</" escaping the Lua filter applies inside the <script>
    return scriptEl ? scriptEl.textContent.replace(/<\\\//g, "</") : null;
  }

  async function renderAll(containers) {
    var theme = themeForPage();
    currentTheme = theme;
    mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: theme });

    for (var i = 0; i < containers.length; i++) {
      var renderEl = containers[i].querySelector(".mermaid-render");
      var text = diagramSource(containers[i]);
      if (!renderEl || text === null) continue;

      renderCount += 1;
      var svgId = "lm-mermaid-svg-" + renderCount;
      try {
        var result = await mermaid.render(svgId, text);
        renderEl.innerHTML = result.svg;
      } catch (err) {
        console.error("[LibroMorph] Mermaid render error:", err);
        showSource(renderEl, text);
        // mermaid may leave its temporary error graphic attached to <body>
        var stray = document.getElementById("d" + svgId);
        if (stray) stray.remove();
      }
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var containers = document.querySelectorAll(".mermaid-diagram");
    if (containers.length === 0) return;

    var script = document.createElement("script");
    script.src = MERMAID_SRC;
    script.onload = function () {
      renderAll(containers);

      // Re-render with the matching mermaid theme when the color mode changes
      new MutationObserver(function () {
        if (themeForPage() !== currentTheme) renderAll(containers);
      }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-color-mode"] });
    };
    script.onerror = function () {
      // mermaid.js never loaded — show the raw source as fallback
      containers.forEach(function (container) {
        var renderEl = container.querySelector(".mermaid-render");
        var text = diagramSource(container);
        if (renderEl && text !== null) showSource(renderEl, text);
      });
    };
    document.head.appendChild(script);
  });
})();
