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
  var MERMAID_SRC = "https://cdn.jsdelivr.net/npm/mermaid@12.3.0/dist/mermaid.esm.min.mjs";

  var renderCount = 0;
  var currentTheme = null;

  function themeForPage() {
    return document.documentElement.getAttribute("data-color-mode") === "dark" ? "redux-dark-color" : null;
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

  async function renderAll(containers, mermaid) {
    var theme = themeForPage();
    currentTheme = theme;
    var config = {
      startOnLoad: false,
      securityLevel: "strict",
      htmlLabels: false,
      flowchart: { htmlLabels: false }
    };
    if (theme) config.theme = theme;
    mermaid.initialize(config);

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

    import(MERMAID_SRC).then(function (module) {
      var mermaid = module.default;
      renderAll(containers, mermaid);

      // Re-render with the matching mermaid theme when the color mode changes
      new MutationObserver(function () {
        if (themeForPage() !== currentTheme) renderAll(containers, mermaid);
      }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-color-mode"] });
    }).catch(function () {
      // mermaid.js never loaded — show the raw source as fallback
      containers.forEach(function (container) {
        var renderEl = container.querySelector(".mermaid-render");
        var text = diagramSource(container);
        if (renderEl && text !== null) showSource(renderEl, text);
      });
    });
  });
})();
