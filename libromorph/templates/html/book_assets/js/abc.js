/**
 * abc.js: Renders ABC music notation blocks using abcjs.
 *
 * Finds all .abc-score containers, reads the ABC source from the embedded
 * <script type="text/vnd.abc"> element, and renders sheet music SVGs into
 * the .abc-render target div.
 */

(function () {
  "use strict";

  // Wait for abcjs to be available (loaded async from CDN)
  function waitForAbcjs(callback, attempts) {
    attempts = attempts || 0;
    if (typeof ABCJS !== "undefined") {
      callback();
    } else if (attempts < 50) {
      setTimeout(function () { waitForAbcjs(callback, attempts + 1); }, 100);
    } else {
      // abcjs never loaded — show the raw source as fallback
      document.querySelectorAll(".abc-score").forEach(function (container) {
        var toggle = container.querySelector(".abc-source-toggle");
        if (toggle) toggle.open = true;
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var scoreContainers = document.querySelectorAll(".abc-score");
    if (scoreContainers.length === 0) return;

    waitForAbcjs(function () {
      scoreContainers.forEach(function (container) {
        var scriptEl = container.querySelector('script[type="text/vnd.abc"]');
        var renderEl = container.querySelector(".abc-render");
        if (!scriptEl || !renderEl) return;

        // Undo the "</" escaping the Lua filter applies inside the <script>
        var abcText = scriptEl.textContent.replace(/<\\\//g, "</");

        try {
          ABCJS.renderAbc(renderEl, abcText, {
            responsive: "resize",
            staffwidth: 700,
            paddingtop: 10,
            paddingbottom: 10,
            add_classes: true
          });
          renderEl.classList.add("abc-rendered");
        } catch (err) {
          console.error("[LibroMorph] ABC render error:", err);
          renderEl.innerHTML = '<p class="abc-error">⚠ Could not render ABC notation.</p>';
          // Fall back to showing the source
          var toggle = container.querySelector(".abc-source-toggle");
          if (toggle) toggle.open = true;
        }
      });
    });
  });
})();
