"""
libromorph.render_utils: Shared helpers for build-time rendering of fenced code
blocks (ABC music, Mermaid diagrams) to SVG images for EPUB.

Rendered SVGs are written as `<sha1(block text)>-<n>.svg` so the Lua filter can
match each fenced block to its images with pandoc.utils.sha1.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
from typing import Dict, List, Optional


# System browsers Playwright (or Puppeteer) can drive when no bundled Chromium is downloaded
SYSTEM_BROWSERS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]


class RenderError(Exception):
    pass


def content_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Browser discovery
# ---------------------------------------------------------------------------

def find_system_browser() -> Optional[str]:
    for name in SYSTEM_BROWSERS:
        path = shutil.which(name)
        if path:
            return path
    return None


def find_browser(p) -> Optional[Dict[str, str]]:
    """Returns launch kwargs for an available Chromium-family browser, given a running Playwright."""
    bundled = p.chromium.executable_path
    if bundled and os.path.exists(bundled):
        return {}
    path = find_system_browser()
    return {"executable_path": path} if path else None


def check_playwright() -> Optional[str]:
    """Returns None if Playwright and a browser are usable, or a reason string."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "Python package 'playwright' is not installed"
    try:
        with sync_playwright() as p:
            launch_args = find_browser(p)
    except Exception as e:
        return f"Playwright failed to start ({e})"
    if launch_args is None:
        return "no Chromium/Chrome browser found for Playwright"
    return None


def render_in_browser(script_url: str, js_function: str, texts: List[str]) -> List[List[str]]:
    """Loads `script_url` in headless Chromium and evaluates `js_function(texts)`."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        launch_args = find_browser(p)
        if launch_args is None:
            raise RenderError("no Chromium/Chrome browser found for Playwright")
        browser = p.chromium.launch(**launch_args)
        try:
            page = browser.new_page()
            page.set_content("<!DOCTYPE html><html><body></body></html>")
            try:
                page.add_script_tag(url=script_url)
            except Exception as e:
                raise RenderError(f"Could not load {script_url}: {e}")
            try:
                return page.evaluate(js_function, texts)
            except Exception as e:
                raise RenderError(str(e))
        finally:
            browser.close()


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def _walk_code_blocks(node, cls: str, found: List[str]):
    if isinstance(node, dict):
        if node.get("t") == "CodeBlock":
            (_, classes, _), text = node["c"]
            if cls in classes:
                found.append(text)
            return
        for v in node.values():
            _walk_code_blocks(v, cls, found)
    elif isinstance(node, list):
        for v in node:
            _walk_code_blocks(v, cls, found)


def extract_code_blocks(markdown: str, cls: str) -> List[str]:
    """Returns the text of every fenced block with class `cls`, exactly as Pandoc parses it."""
    if cls not in markdown:
        return []
    res = subprocess.run(["pandoc", "-f", "markdown", "-t", "json"],
                         input=markdown, capture_output=True, text=True)
    if res.returncode != 0:
        raise RenderError(f"Pandoc failed while scanning for {cls} blocks:\n{res.stderr}")
    found: List[str] = []
    _walk_code_blocks(json.loads(res.stdout).get("blocks", []), cls, found)
    return found


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def normalize_svg(svg: str) -> str:
    """Ensures a standalone SVG has an XML namespace, a viewBox and pixel dimensions so it scales as an <img>."""
    svg = re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>|<!--.*?-->", "", svg, flags=re.S).strip()
    open_tag = re.match(r"<svg\b[^>]*>", svg).group(0)
    new_tag = open_tag
    if "xmlns=" not in new_tag:
        new_tag = new_tag.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    w = re.search(r'\bwidth="([\d.]+)(?:px)?"', new_tag)
    h = re.search(r'\bheight="([\d.]+)(?:px)?"', new_tag)
    view_box = re.search(r'\bviewBox="[\d.-]+[ ,]+[\d.-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', new_tag)
    if "viewBox" not in new_tag and w and h:
        new_tag = new_tag.replace("<svg", f'<svg viewBox="0 0 {w.group(1)} {h.group(1)}"', 1)
    elif view_box and not (w and h):
        # e.g. Mermaid's width="100%": use intrinsic size so images aren't zero-sized
        new_tag = re.sub(r'\s(width|height)="[^"]*"', "", new_tag)
        new_tag = new_tag.replace(
            "<svg", f'<svg width="{view_box.group(1)}" height="{view_box.group(2)}"', 1)
    return svg.replace(open_tag, new_tag, 1)


def write_svgs(out_dir: str, texts: List[str], results: List[List[str]], label: str):
    os.makedirs(out_dir, exist_ok=True)
    for text, svgs in zip(texts, results):
        if not svgs:
            raise RenderError(f"{label} produced no SVG output for block:\n{text[:200]}")
        digest = content_hash(text)
        for n, svg in enumerate(svgs, 1):
            with open(os.path.join(out_dir, f"{digest}-{n}.svg"), "w", encoding="utf-8") as f:
                f.write(normalize_svg(svg))
