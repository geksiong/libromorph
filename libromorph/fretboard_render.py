"""Render fretboard.js and Fretdrom fenced blocks to SVG for EPUB."""

import os
import shutil
import subprocess
import tempfile

from .render_utils import RenderError, check_playwright, extract_code_blocks, render_in_browser, write_svgs


ASSETS = os.path.join(os.path.dirname(__file__), "templates", "html", "book_assets", "js")


def extract_fretboard_blocks(markdown):
    return extract_code_blocks(markdown, "fretboard")


def extract_fretdrom_blocks(markdown):
    return extract_code_blocks(markdown, "fretdrom")


def resolve_fretboard_renderer(choice):
    if choice == "none":
        return None
    if choice not in ("auto", "fretboard-js"):
        raise RenderError("Unknown fretboard_renderer '%s'. Choose auto, fretboard-js or none" % choice)
    reason = check_playwright()
    if reason:
        if choice == "auto":
            print("[LibroMorph] Warning: no fretboard.js EPUB renderer: %s" % reason)
            return None
        raise RenderError("fretboard.js renderer is unavailable: %s" % reason)
    return "fretboard-js"


def resolve_fretdrom_renderer(choice):
    if choice == "none":
        return None
    if choice not in ("auto", "fretdrom"):
        raise RenderError("Unknown fretdrom_renderer '%s'. Choose auto, fretdrom or none" % choice)
    if not shutil.which("fretdrom"):
        if choice == "auto":
            print("[LibroMorph] Warning: fretdrom CLI unavailable; EPUB diagrams will show source")
            return None
        raise RenderError("fretdrom CLI unavailable; install with `npm install -g fretdrom`")
    return "fretdrom"


def render_fretboard_blocks(renderer, texts, out_dir):
    unique = list(dict.fromkeys(texts))
    scripts = [os.path.join(ASSETS, "vendor", "fretboard.umd.js"),
               os.path.join(ASSETS, "fretboard-init.js")]
    js = """(texts) => texts.map((source, i) => {
      const target = document.createElement('div');
      document.body.appendChild(target);
      window.LibroMorphFretboards.render(target, source);
      const svg = target.querySelector('svg');
      if (!svg) throw new Error(`fretboard ${i + 1} produced no SVG`);
      const box = svg.getBoundingClientRect();
      if (!svg.getAttribute('viewBox')) svg.setAttribute('viewBox', `0 0 ${box.width} ${box.height}`);
      svg.setAttribute('width', box.width);
      svg.setAttribute('height', box.height);
      const result = new XMLSerializer().serializeToString(svg);
      target.remove();
      return [result];
    })"""
    try:
        write_svgs(out_dir, unique, render_in_browser(scripts, js, unique), renderer)
    except RenderError as e:
        raise RenderError("fretboard.js failed: %s" % e)
    return len(unique)


def render_fretdrom_blocks(renderer, texts, out_dir):
    unique = list(dict.fromkeys(texts))
    results = []
    with tempfile.TemporaryDirectory() as temp_dir:
        for i, source in enumerate(unique):
            path = os.path.join(temp_dir, "diagram-%d.json5" % i)
            with open(path, "w", encoding="utf-8") as stream:
                stream.write(source)
            process = subprocess.run(["fretdrom", "--input", path], capture_output=True, text=True)
            if process.returncode or "<svg" not in process.stdout:
                raise RenderError("fretdrom failed on diagram %d: %s" %
                                  (i + 1, process.stderr or process.stdout))
            results.append([process.stdout])
    write_svgs(out_dir, unique, results, renderer)
    return len(unique)
