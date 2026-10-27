"""
libromorph.abc_render: Build-time ABC music notation to SVG rendering for EPUB.

Supported renderers (selected via `abc_renderer` in book.yaml or --abc-renderer):
  - abcjs   : abcjs in headless Chrome/Chromium via Playwright (matches the web reader)
  - abcm2ps : the abcm2ps command-line engraver
  - abc2svg : the abc2svg command-line tool (npm package, needs a JS interpreter)
  - auto    : first available of the above, in that order
  - none    : skip rendering; EPUB shows the ABC source as text

Rendered SVGs are written as `<sha1(abc text)>-<n>.svg` so the Lua filter can
match each fenced ```abc block to its images with pandoc.utils.sha1.
"""

import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from typing import Dict, List, Optional


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

# System browsers Playwright can drive when its own Chromium isn't downloaded
SYSTEM_BROWSERS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]


class AbcRenderError(Exception):
    pass


def abc_hash(abc_text: str) -> str:
    return hashlib.sha1(abc_text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Dependency checks: each returns None when usable, or a reason string
# ---------------------------------------------------------------------------

def _find_browser(p) -> Optional[Dict[str, str]]:
    """Returns launch kwargs for an available Chromium-family browser, given a running Playwright."""
    bundled = p.chromium.executable_path
    if bundled and os.path.exists(bundled):
        return {}
    for name in SYSTEM_BROWSERS:
        path = shutil.which(name)
        if path:
            return {"executable_path": path}
    return None


def check_renderer(name: str) -> Optional[str]:
    if name == "abcjs":
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return "Python package 'playwright' is not installed"
        try:
            with sync_playwright() as p:
                launch_args = _find_browser(p)
        except Exception as e:
            return f"Playwright failed to start ({e})"
        if launch_args is None:
            return "no Chromium/Chrome browser found for Playwright"
        return None
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
# Extraction
# ---------------------------------------------------------------------------

def _walk_code_blocks(node, found: List[str]):
    if isinstance(node, dict):
        if node.get("t") == "CodeBlock":
            (_, classes, _), text = node["c"]
            if "abc" in classes:
                found.append(text)
            return
        for v in node.values():
            _walk_code_blocks(v, found)
    elif isinstance(node, list):
        for v in node:
            _walk_code_blocks(v, found)


def extract_abc_blocks(markdown: str) -> List[str]:
    """Returns the text of every ```abc fenced block, exactly as Pandoc parses it."""
    if "abc" not in markdown:
        return []
    res = subprocess.run(["pandoc", "-f", "markdown", "-t", "json"],
                         input=markdown, capture_output=True, text=True)
    if res.returncode != 0:
        raise AbcRenderError(f"Pandoc failed while scanning for ABC blocks:\n{res.stderr}")
    found: List[str] = []
    _walk_code_blocks(json.loads(res.stdout).get("blocks", []), found)
    return found


# ---------------------------------------------------------------------------
# Renderers: each takes a list of ABC texts and returns a list of SVG lists
# ---------------------------------------------------------------------------

_SVG_RE = re.compile(r"<svg\b.*?</svg>", re.S)


def _normalize_svg(svg: str) -> str:
    """Ensures a standalone SVG has an XML namespace and a viewBox so it scales as an <img>."""
    svg = re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>|<!--.*?-->", "", svg, flags=re.S).strip()
    open_tag = re.match(r"<svg\b[^>]*>", svg).group(0)
    new_tag = open_tag
    if "xmlns=" not in new_tag:
        new_tag = new_tag.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    if "viewBox" not in new_tag:
        w = re.search(r'\bwidth="([\d.]+)(?:px)?"', new_tag)
        h = re.search(r'\bheight="([\d.]+)(?:px)?"', new_tag)
        if w and h:
            new_tag = new_tag.replace("<svg", f'<svg viewBox="0 0 {w.group(1)} {h.group(1)}"', 1)
    return svg.replace(open_tag, new_tag, 1)


def _render_abcjs(texts: List[str]) -> List[List[str]]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        launch_args = _find_browser(p)
        if launch_args is None:
            raise AbcRenderError("no Chromium/Chrome browser found for Playwright")
        browser = p.chromium.launch(**launch_args)
        try:
            page = browser.new_page()
            page.set_content("<!DOCTYPE html><html><body></body></html>")
            try:
                page.add_script_tag(url=ABCJS_CDN_URL)
            except Exception as e:
                raise AbcRenderError(f"Could not load abcjs from {ABCJS_CDN_URL}: {e}")
            return page.evaluate("""(texts) => texts.map((abc) => {
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
            })""", texts)
        finally:
            browser.close()


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
    os.makedirs(out_dir, exist_ok=True)
    print(f"[LibroMorph] Rendering {len(unique)} ABC score(s) to SVG with {renderer}...")
    for abc, svgs in zip(unique, _RENDER_FUNCS[renderer](unique)):
        if not svgs:
            raise AbcRenderError(f"{renderer} produced no SVG output for score:\n{abc[:200]}")
        digest = abc_hash(abc)
        for n, svg in enumerate(svgs, 1):
            with open(os.path.join(out_dir, f"{digest}-{n}.svg"), "w", encoding="utf-8") as f:
                f.write(_normalize_svg(svg))
    return len(unique)
