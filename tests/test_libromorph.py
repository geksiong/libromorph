"""
tests/test_libromorph.py: Test suite covering filters, indexer, cover generator, and full builder.
"""

import os
import tempfile
import subprocess
import pytest
from libromorph.config import BookConfig
from libromorph.builder import BookBuilder
from libromorph.indexer import BookIndexer, slugify
from libromorph.cover import generate_cover_image
from libromorph import abc_render


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_DIR = os.path.join(ROOT_DIR, "demo-book")
FILTER_PATH = os.path.join(ROOT_DIR, "libromorph", "filters", "libro_filter.lua")


def test_slugify():
    assert slugify("Quantum Mechanics") == "quantum-mechanics"
    assert slugify("Schrödinger, Erwin") == "schrodinger-erwin"
    assert slugify("夏目漱石") == "夏目漱石"


def test_ruby_filter():
    md_input = "Here is {漢字|かんじ} and [東京]{.ruby ruby=\"とうきょう\"}."
    cmd = ["pandoc", "-f", "markdown", "-t", "html", f"--lua-filter={FILTER_PATH}"]
    res = subprocess.run(cmd, input=md_input, capture_output=True, text=True)
    assert res.returncode == 0
    assert "<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>" in res.stdout
    assert "<ruby>東京<rp>(</rp><rt>とうきょう</rt><rp>)</rp></ruby>" in res.stdout


def test_tcy_filter():
    md_input = "Number {tcy:42} and [2026]{.tcy}."
    cmd = ["pandoc", "-f", "markdown", "-t", "html", f"--lua-filter={FILTER_PATH}"]
    res = subprocess.run(cmd, input=md_input, capture_output=True, text=True)
    assert res.returncode == 0
    assert '<span class="tcy">42</span>' in res.stdout
    assert '<span class="tcy">2026</span>' in res.stdout


def test_quiz_filter_html():
    md_input = """
::: quiz
**Question:** What is $E$?

- [ ] $mc$
- [x] $mc^2$
- [ ] $mc^3$

*Explanation:* Mass-energy equivalence.
:::
"""
    cmd = ["pandoc", "-f", "markdown", "-t", "html", f"--lua-filter={FILTER_PATH}"]
    res = subprocess.run(cmd, input=md_input, capture_output=True, text=True)
    assert res.returncode == 0
    assert 'class="quiz-card interactive-quiz"' in res.stdout
    assert 'data-correct="false"' in res.stdout
    assert 'data-correct="true"' in res.stdout
    assert "Mass-energy equivalence" in res.stdout


def test_quiz_filter_epub():
    md_input = """
::: quiz
**Question:** What is $E$?

- [ ] $mc$
- [x] $mc^2$

*Explanation:* Einstein's equation.
:::
"""
    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp_epub:
        tmp_path = tmp_epub.name

    try:
        cmd = ["pandoc", "-f", "markdown", "-t", "epub3", f"--lua-filter={FILTER_PATH}", "-o", tmp_path]
        res = subprocess.run(cmd, input=md_input, capture_output=True, text=True)
        assert res.returncode == 0
        import zipfile
        with zipfile.ZipFile(tmp_path, "r") as z:
            ch1_content = z.read("EPUB/text/ch001.xhtml").decode("utf-8")
            assert "is-correct-option" in ch1_content
            assert "quiz-reveal" in ch1_content
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


ABC_INPUT = """
```abc
X:1
T:Twinkle "Little" Star
M:4/4
L:1/4
K:C
C C G G | A A G2 |
```
"""


def test_abc_filter_html():
    cmd = ["pandoc", "-f", "markdown", "-t", "html", f"--lua-filter={FILTER_PATH}"]
    res = subprocess.run(cmd, input=ABC_INPUT, capture_output=True, text=True)
    assert res.returncode == 0
    assert '<div class="abc-score" id="abc-score-1" data-title="Twinkle &quot;Little&quot; Star">' in res.stdout
    assert '<script type="text/vnd.abc">' in res.stdout
    assert "C C G G | A A G2 |" in res.stdout
    assert 'class="abc-source-toggle"' in res.stdout


def test_abc_filter_epub():
    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp_epub:
        tmp_path = tmp_epub.name

    try:
        cmd = ["pandoc", "-f", "markdown", "-t", "epub3", f"--lua-filter={FILTER_PATH}", "-o", tmp_path]
        res = subprocess.run(cmd, input=ABC_INPUT, capture_output=True, text=True)
        assert res.returncode == 0
        import zipfile
        with zipfile.ZipFile(tmp_path, "r") as z:
            ch1_content = z.read("EPUB/text/ch001.xhtml").decode("utf-8")
            assert "abc-score-epub" in ch1_content
            assert "<script" not in ch1_content
            assert "C C G G | A A G2 |" in ch1_content
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_abc_filter_epub_uses_rendered_svg():
    abc_text = abc_render.extract_abc_blocks(ABC_INPUT)[0]
    with tempfile.TemporaryDirectory() as tmpdir:
        svg_dir = os.path.join(tmpdir, "abc-svg")
        os.makedirs(svg_dir)
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>'
        with open(os.path.join(svg_dir, f"{abc_render.abc_hash(abc_text)}-1.svg"), "w") as f:
            f.write(svg)

        epub_path = os.path.join(tmpdir, "out.epub")
        cmd = ["pandoc", "-f", "markdown", "-t", "epub3", f"--lua-filter={FILTER_PATH}", "-o", epub_path]
        env = dict(os.environ, LIBROMORPH_ABC_SVG_DIR=svg_dir)
        res = subprocess.run(cmd, input=ABC_INPUT, capture_output=True, text=True, env=env)
        assert res.returncode == 0
        import zipfile
        with zipfile.ZipFile(epub_path, "r") as z:
            ch1_content = z.read("EPUB/text/ch001.xhtml").decode("utf-8")
            assert 'class="abc-svg"' in ch1_content
            assert "abc-source" not in ch1_content
            assert any(name.endswith(".svg") for name in z.namelist())


def test_abc_renderer_resolution(monkeypatch):
    assert abc_render.resolve_renderer("none") is None
    with pytest.raises(abc_render.AbcRenderError, match="Unknown abc_renderer"):
        abc_render.resolve_renderer("lilypond")

    # Simulate missing tools: explicit choice errors, auto falls back to text
    monkeypatch.setattr(abc_render.shutil, "which", lambda name: None)
    monkeypatch.setattr(abc_render, "check_renderer",
                        lambda name: None if name == "abc2svg" else "missing")
    assert abc_render.resolve_renderer("auto") == "abc2svg"
    with pytest.raises(abc_render.AbcRenderError, match="abcm2ps"):
        abc_render.resolve_renderer("abcm2ps")
    monkeypatch.setattr(abc_render, "check_renderer", lambda name: "missing")
    assert abc_render.resolve_renderer("auto") is None


def test_abcm2ps_check_requires_binary(monkeypatch):
    monkeypatch.setattr(abc_render.shutil, "which", lambda name: None)
    assert "not found" in abc_render.check_renderer("abcm2ps")
    assert "not found" in abc_render.check_renderer("abc2svg")


def test_callout_filter():
    md_input = """
::: note
Important observation here.
:::
"""
    cmd = ["pandoc", "-f", "markdown", "-t", "html", f"--lua-filter={FILTER_PATH}"]
    res = subprocess.run(cmd, input=md_input, capture_output=True, text=True)
    assert res.returncode == 0
    assert 'class="callout callout-note"' in res.stdout
    assert "Important observation here." in res.stdout


def test_indexer_extraction():
    indexer = BookIndexer()
    md = "Exploring [Quantum Entanglement]{.index entry=\"Quantum!Entanglement\"} and [Gravity]{.index}."
    transformed, discovered = indexer.process_chapter_markdown(
        markdown=md,
        chapter_num=1,
        chapter_title="Intro",
        chapter_href="ch01.html"
    )
    assert len(discovered) == 2
    assert discovered[0].main_term == "Quantum"
    assert discovered[0].sub_terms == ["Entanglement"]
    assert discovered[1].main_term == "Gravity"

    # Test markdown index rendering for EPUB and HTML
    epub_idx = indexer.render_markdown_index(for_epub=True)
    html_idx = indexer.render_markdown_index(for_epub=False)

    assert "# Index" in epub_idx
    assert "ch01.html#idx-" in html_idx


def test_cover_generation():
    with tempfile.TemporaryDirectory() as tmpdir:
        cover_path = os.path.join(tmpdir, "cover.png")
        generate_cover_image(
            output_path=cover_path,
            title="Test Book",
            subtitle="Testing Covers",
            author="Test Author",
            theme="classic-novel"
        )
        assert os.path.exists(cover_path)
        assert os.path.getsize(cover_path) > 1000


def test_full_demo_book_build():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = BookConfig.load(DEMO_DIR)
        builder = BookBuilder(config=config, output_dir=tmpdir)
        results = builder.build(target_format="all")

        assert "epub" in results
        assert "html" in results
        assert os.path.exists(results["epub"])
        assert os.path.isdir(results["html"])
        assert os.path.exists(os.path.join(results["html"], "index.html"))
        assert os.path.exists(os.path.join(results["html"], "book-index.html"))
        assert os.path.exists(os.path.join(results["html"], "assets", "js", "abc.js"))
