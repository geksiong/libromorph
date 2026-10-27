"""
libromorph.abc_render: Build-time ABC music notation to SVG rendering for EPUB.

Supported renderers (selected via `abc_renderer` in book.yaml or --abc-renderer):
  - abcjs   : abcjs in headless Chrome/Chromium via Playwright (matches the web reader)
  - abcm2ps : the abcm2ps command-line engraver
  - abc2svg : the abc2svg command-line tool (npm package, needs a JS interpreter)
  - auto    : first available of the above, in that order
  - none    : skip rendering; EPUB shows the ABC source as text
"""

import glob
import os
import re
import shutil
import subprocess
import tempfile
from typing import List, Optional

from .render_utils import (
    RenderError, check_playwright, content_hash, extract_code_blocks, render_in_browser, write_svgs
)


ABCJS_VERSION = "6.7.1"
ABCJS_CDN_URL = f"https://cdn.jsdelivr.net/npm/abcjs@{ABCJS_VERSION}/dist/abcjs-basic-min.js"

RENDERERS = ["abcjs", "abcm2ps", "abc2svg"]
RENDERER_CHOICES = ["auto", "none"] + RENDERERS

INSTALL_HINTS = {
    "abcjs": "pip install 'libromorph[music]' (Playwright), plus Google Chrome/Chromium "
             "or `playwright install chromium`",
    "abcm2ps": "install abcm2ps (e.g. `apt install abcm2ps` or `brew install abcm2ps`)",
    "abc2svg": "npm install -g abc2svg (also needs node, qjs or another JS interpreter on PATH)",
}


class AbcRenderError(RenderError):
    pass


def abc_hash(abc_text: str) -> str:
    return content_hash(abc_text)


def extract_abc_blocks(markdown: str) -> List[str]:
    """Returns the text of every ```abc fenced block, exactly as Pandoc parses it."""
    return extract_code_blocks(markdown, "abc")


# ---------------------------------------------------------------------------
# Dependency checks: each returns None when usable, or a reason string
# ---------------------------------------------------------------------------

def check_renderer(name: str) -> Optional[str]:
    if name == "abcjs":
        return check_playwright()
    if name == "abcm2ps":
        return None if shutil.which("abcm2ps") else "'abcm2ps' not found on PATH"
    if name == "abc2svg":
        if not shutil.which("abc2svg"):
            return "'abc2svg' not found on PATH"
        if not any(shutil.which(js) for js in ["node", "qjs", "js128", "js115", "js102", "d8"]):
            return "no JavaScript interpreter (node, qjs, ...) found on PATH for abc2svg"
        return None
    return f"unknown renderer '{name}'"


def resolve_renderer(choice: str) -> Optional[str]:
    """
    Maps the configured choice to a usable renderer name, or None for text fallback.
    An explicitly requested renderer with missing dependencies is an error;
    'auto' falls back to text with a warning.
    """
    choice = (choice or "auto").lower()
    if choice not in RENDERER_CHOICES:
        raise AbcRenderError(
            f"Unknown abc_renderer '{choice}'. Choose from: {', '.join(RENDERER_CHOICES)}"
        )
    if choice == "none":
        return None
    if choice == "auto":
        reasons = []
        for name in RENDERERS:
            reason = check_renderer(name)
            if reason is None:
                return name
            reasons.append(f"  - {name}: {reason}")
        print("[LibroMorph] Warning: no ABC renderer available; EPUB scores will be shown as text.\n"
              + "\n".join(reasons))
        return None
    reason = check_renderer(choice)
    if reason is not None:
        raise AbcRenderError(
            f"ABC renderer '{choice}' is unavailable: {reason}.\n  To fix: {INSTALL_HINTS[choice]}"
        )
    return choice


# ---------------------------------------------------------------------------
# Renderers: each takes a list of ABC texts and returns a list of SVG lists
# ---------------------------------------------------------------------------

_SVG_RE = re.compile(r"<svg\b.*?</svg>", re.S)

_ABCJS_RENDER_JS = """(texts) => texts.map((abc) => {
    const div = document.createElement("div");
    document.body.appendChild(div);
    ABCJS.renderAbc(div, abc, {
        staffwidth: 700, paddingtop: 10, paddingbottom: 10, add_classes: true
    });
    const out = Array.from(div.querySelectorAll("svg")).map((svg) => {
        const box = svg.getBoundingClientRect();
        if (!svg.getAttribute("viewBox")) {
            svg.setAttribute("viewBox", `0 0 ${box.width} ${box.height}`);
        }
        svg.setAttribute("width", box.width);
        svg.setAttribute("height", box.height);
        return new XMLSerializer().serializeToString(svg);
    });
    div.remove();
    return out;
})"""


def _render_abcjs(texts: List[str]) -> List[List[str]]:
    try:
        return render_in_browser(ABCJS_CDN_URL, _ABCJS_RENDER_JS, texts)
    except RenderError as e:
        raise AbcRenderError(f"abcjs failed: {e}")


def _render_abcm2ps(texts: List[str]) -> List[List[str]]:
    results = []
    for abc in texts:
        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(tmpdir, "score.abc")
            with open(src, "w", encoding="utf-8") as f:
                f.write(abc + "\n")
            # -g: one SVG file per tune; files are named out001.svg, out002.svg, ...
            res = subprocess.run(["abcm2ps", "-g", "-O", os.path.join(tmpdir, "out.svg"), src],
                                 capture_output=True, text=True)
            svg_files = sorted(glob.glob(os.path.join(tmpdir, "out*.svg")))
            if res.returncode != 0 or not svg_files:
                raise AbcRenderError(f"abcm2ps failed:\n{res.stderr or res.stdout}")
            svgs = []
            for path in svg_files:
                with open(path, "r", encoding="utf-8") as f:
                    svgs.append(f.read())
            results.append(svgs)
    return results


def _render_abc2svg(texts: List[str]) -> List[List[str]]:
    results = []
    for abc in texts:
        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(tmpdir, "score.abc")
            with open(src, "w", encoding="utf-8") as f:
                f.write(abc + "\n")
            # abc2svg writes an HTML page containing one <svg> per tune block
            res = subprocess.run(["abc2svg", src], capture_output=True, text=True)
            svgs = _SVG_RE.findall(res.stdout)
            if res.returncode != 0 or not svgs:
                raise AbcRenderError(f"abc2svg failed:\n{res.stderr or res.stdout}")
            results.append(svgs)
    return results


_RENDER_FUNCS = {
    "abcjs": _render_abcjs,
    "abcm2ps": _render_abcm2ps,
    "abc2svg": _render_abc2svg,
}


def render_abc_blocks(renderer: str, texts: List[str], out_dir: str) -> int:
    """Renders unique ABC texts to `<out_dir>/<sha1>-<n>.svg`. Returns the number of scores rendered."""
    unique = list(dict.fromkeys(texts))
    if not unique:
        return 0
    print(f"[LibroMorph] Rendering {len(unique)} ABC score(s) to SVG with {renderer}...")
    try:
        write_svgs(out_dir, unique, _RENDER_FUNCS[renderer](unique), renderer)
    except AbcRenderError:
        raise
    except RenderError as e:
        raise AbcRenderError(str(e))
    return len(unique)
