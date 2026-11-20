/* Fenced fretboard.js diagrams. The same render function is used by the EPUB builder. */
(function () {
  'use strict';

  function render(target, source) {
    const spec = JSON.parse(source);
    if (!spec || typeof spec !== 'object' || Array.isArray(spec)) {
      throw new Error('Expected a JSON object');
    }
    if (!spec.scale && !Array.isArray(spec.dots)) {
      throw new Error('Provide scale or dots');
    }
    const tuning = spec.tuning || ['E2', 'A2', 'D3', 'G3', 'B3', 'E4'];
    if (!Array.isArray(tuning) || tuning.length < 2 || tuning.length > 12) {
      throw new Error('tuning must contain 2 to 12 strings, low to high');
    }
    const fretCount = spec.fretCount == null ? 15 : Number(spec.fretCount);
    if (!Number.isInteger(fretCount) || fretCount < 1 || fretCount > 35) {
      throw new Error('fretCount must be between 1 and 35');
    }
    const fg = getComputedStyle(target).color || '#222';
    // The SVG is scaled to the column width (often ~450px on e-readers), so
    // fretboard.js's 960px default made labels ~5px tall. Size the drawing to
    // the fret count and scale text and dots with it, so they stay ~12px
    // when the board is shown 450px wide.
    const width = Math.max(600, fretCount * 50);
    const k = width / 600;
    const options = {
      el: target,
      tuning: tuning,
      stringCount: tuning.length,
      fretCount: fretCount,
      width: width,
      height: Math.round(32 * k) * (tuning.length - 1),
      dotSize: 26 * k,
      dotTextSize: 17 * k,
      dotStrokeWidth: 2 * k,
      topPadding: 28 * k,
      bottomPadding: 15 * k,
      leftPadding: 32 * k,
      rightPadding: 24 * k,
      fretNumbersHeight: 40 * k,
      fretNumbersMargin: 24 * k,
      stringColor: fg,
      fretColor: fg,
      nutColor: fg,
      fretNumbersColor: fg,
      dotStrokeColor: fg,
      dotFill: '#fff',
      dotText: function (dot) { return dot.label == null ? '' : String(dot.label); }
    };
    const board = new window.fretboard.Fretboard(options);
    if (spec.scale) {
      if (typeof spec.scale.root !== 'string' || typeof spec.scale.type !== 'string') {
        throw new Error('scale requires root and type');
      }
      board.renderScale(spec.scale);
      board.style({ filter: { interval: '1P' }, fill: '#b91c1c' });
    } else {
      spec.dots.forEach(function (dot) {
        if (!Number.isInteger(dot.string) || dot.string < 1 || dot.string > tuning.length ||
            !Number.isInteger(dot.fret) || dot.fret < 0 || dot.fret > fretCount) {
          throw new Error('Each dot needs a valid string and fret');
        }
      });
      board.setDots(spec.dots).render();
    }
    const svg = target.querySelector('svg');
    if (svg) {
      const fretNumbers = svg.querySelector('.fret-numbers');
      if (fretNumbers) fretNumbers.setAttribute('font-size', 16 * k);
      svg.setAttribute('role', 'img');
      svg.setAttribute('aria-label', spec.title || 'Fretboard diagram');
      const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
      title.textContent = spec.title || 'Fretboard diagram';
      svg.prepend(title);
    }
    return board;
  }

  window.LibroMorphFretboards = { render: render };
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.lm-fretboard').forEach(function (el) {
      try {
        render(el.querySelector('.lm-fretboard-render'), el.querySelector('script[type="application/json"]').textContent);
      } catch (error) {
        const message = document.createElement('p');
        message.className = 'lm-fretboard-error';
        message.textContent = 'Could not draw fretboard: ' + error.message;
        el.prepend(message);
      }
    });
    document.querySelectorAll('.lm-fretdrom').forEach(function (el) {
      try {
        const source = el.querySelector('script[type="fretdrom"]').textContent;
        const render = document.createElement('div');
        render.innerHTML = window.FretDrom.renderSVG(source);
        el.prepend(render);
      } catch (error) {
        const message = document.createElement('p');
        message.className = 'lm-fretboard-error';
        message.textContent = 'Could not draw Fretdrom diagram: ' + error.message;
        el.prepend(message);
      }
    });
  });
}());
