"""
libromorph.mermaid_render: Build-time Mermaid diagram to SVG rendering for EPUB.

Supported renderers (selected via `mermaid_renderer` in book.yaml or --mermaid-renderer):
  - mermaid-js : mermaid.js in headless Chrome/Chromium via Playwright (matches the web reader)
  - mmdc       : the mermaid-cli command-line tool (npm package @mermaid-js/mermaid-cli)
  - auto       : first available of the above, in that order
  - none       : skip rendering; EPUB shows the Mermaid source as text

Diagrams are rendered with SVG <text> labels instead of HTML <foreignObject>
labels, since most EPUB reading systems can't display foreignObject in images.
"""

import json
import os
import shutil
import subprocess
import tempfile
from typing import List, Optional

from .render_utils import (
    RenderError, check_playwright, extract_code_blocks, find_system_browser, render_in_browser, write_svgs
)


MERMAID_VERSION = "12.3.0"
MERMAID_CDN_URL = f"https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.esm.min.mjs"

RENDERERS = ["mermaid-js", "mmdc"]
RENDERER_CHOICES = ["auto", "none"] + RENDERERS

INSTALL_HINTS = {
    "mermaid-js": "pip install 'libromorph[diagrams]' (Playwright), plus Google Chrome/Chromium "
                  "or `playwright install chromium`",
    "mmdc": "npm install -g @mermaid-js/mermaid-cli",
}

# Mermaid config shared by both renderers
MERMAID_CONFIG = {
    "securityLevel": "strict",
    "htmlLabels": False,
    "flowchart": {"htmlLabels": False},
}


class MermaidRenderError(RenderError):
    pass


def extract_mermaid_blocks(markdown: str) -> List[str]:
    """Returns the text of every ```mermaid fenced block, exactly as Pandoc parses it."""
    return extract_code_blocks(markdown, "mermaid")


# ---------------------------------------------------------------------------
# Dependency checks: each returns None when usable, or a reason string
# ---------------------------------------------------------------------------

def check_renderer(name: str) -> Optional[str]:
    if name == "mermaid-js":
        return check_playwright()
    if name == "mmdc":
        return None if shutil.which("mmdc") else "'mmdc' not found on PATH"
    return f"unknown renderer '{name}'"


def resolve_renderer(choice: str) -> Optional[str]:
    """
    Maps the configured choice to a usable renderer name, or None for text fallback.
    An explicitly requested renderer with missing dependencies is an error;
    'auto' falls back to text with a warning.
    """
    choice = (choice or "auto").lower()
    if choice not in RENDERER_CHOICES:
        raise MermaidRenderError(
            f"Unknown mermaid_renderer '{choice}'. Choose from: {', '.join(RENDERER_CHOICES)}"
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
        print("[LibroMorph] Warning: no Mermaid renderer available; EPUB diagrams will be shown as text.\n"
              + "\n".join(reasons))
        return None
    reason = check_renderer(choice)
    if reason is not None:
        raise MermaidRenderError(
            f"Mermaid renderer '{choice}' is unavailable: {reason}.\n  To fix: {INSTALL_HINTS[choice]}"
        )
    return choice


# ---------------------------------------------------------------------------
# Renderers: each takes a list of Mermaid texts and returns a list of SVG lists
# ---------------------------------------------------------------------------

_MERMAID_RENDER_JS = """async ([texts, config]) => {
    const { default: mermaid } = await import("__MERMAID_URL__");
    mermaid.initialize(Object.assign({ startOnLoad: false }, config));
    const out = [];
    for (let i = 0; i < texts.length; i++) {
        try {
            const { svg } = await mermaid.render(`lm-mermaid-${i}`, texts[i]);
            out.push([svg]);
        } catch (err) {
            throw new Error(`diagram ${i + 1}: ${err && err.message ? err.message : err}`);
        }
    }
    return out;
}""".replace("__MERMAID_URL__", MERMAID_CDN_URL)


def _render_mermaid_js(texts: List[str]) -> List[List[str]]:
    try:
        # render_in_browser passes a single argument, so bundle texts with the config
        return render_in_browser([], _MERMAID_RENDER_JS, [texts, MERMAID_CONFIG])
    except RenderError as e:
        raise MermaidRenderError(f"mermaid.js failed: {e}")


def _render_mmdc(texts: List[str]) -> List[List[str]]:
    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(MERMAID_CONFIG, f)
        cmd_base = ["mmdc", "-c", config_path, "-b", "white", "-q"]
        # Prefer a system browser so Puppeteer's own Chrome download isn't required
        browser = find_system_browser()
        if browser:
            puppeteer_path = os.path.join(tmpdir, "puppeteer.json")
            with open(puppeteer_path, "w", encoding="utf-8") as f:
                json.dump({"executablePath": browser}, f)
            cmd_base += ["-p", puppeteer_path]

        for i, text in enumerate(texts):
            src = os.path.join(tmpdir, f"diagram{i}.mmd")
            out = os.path.join(tmpdir, f"diagram{i}.svg")
            with open(src, "w", encoding="utf-8") as f:
                f.write(text + "\n")
            res = subprocess.run(cmd_base + ["-i", src, "-o", out], capture_output=True, text=True)
            if res.returncode != 0 or not os.path.exists(out):
                raise MermaidRenderError(f"mmdc failed on diagram {i + 1}:\n{res.stderr or res.stdout}")
            with open(out, "r", encoding="utf-8") as f:
                results.append([f.read()])
    return results


_RENDER_FUNCS = {
    "mermaid-js": _render_mermaid_js,
    "mmdc": _render_mmdc,
}


def render_mermaid_blocks(renderer: str, texts: List[str], out_dir: str) -> int:
    """Renders unique Mermaid texts to `<out_dir>/<sha1>-1.svg`. Returns the number of diagrams rendered."""
    unique = list(dict.fromkeys(texts))
    if not unique:
        return 0
    print(f"[LibroMorph] Rendering {len(unique)} Mermaid diagram(s) to SVG with {renderer}...")
    try:
        write_svgs(out_dir, unique, _RENDER_FUNCS[renderer](unique), renderer)
    except MermaidRenderError:
        raise
    except RenderError as e:
        raise MermaidRenderError(str(e))
    return len(unique)
