"""
tests/test_libromorph.py: Test suite covering filters, indexer, cover generator, and full builder.
"""

import os
import tempfile
import subprocess
import zipfile
import pytest
from libromorph.config import BookConfig
from libromorph.builder import BookBuilder
from libromorph.indexer import BookIndexer, slugify
from libromorph.cover import generate_cover_image
from libromorph import abc_render, mermaid_render, fretboard_render


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


PLAIN_QUIZ_INPUT = """
::: quiz
**Question:** Which is a capital city?

- [ ] Plain words here
- [x] Correct plain *answer*
- [ ] $x$ math first
:::
"""


@pytest.mark.parametrize("fmt", ["html", "epub3"])
def test_quiz_options_keep_leading_plain_text(fmt):
    if fmt == "html":
        res = _run_filter(PLAIN_QUIZ_INPUT)
        assert res.returncode == 0
        content = res.stdout
    else:
        with tempfile.TemporaryDirectory() as tmp:
            epub_path = os.path.join(tmp, "q.epub")
            cmd = ["pandoc", "-f", "markdown", "-t", "epub3", f"--lua-filter={FILTER_PATH}", "-o", epub_path]
            res = subprocess.run(cmd, input=PLAIN_QUIZ_INPUT, capture_output=True, text=True)
            assert res.returncode == 0
            with zipfile.ZipFile(epub_path) as z:
                content = z.read("EPUB/text/ch001.xhtml").decode("utf-8")
    assert "Plain words here" in content
    assert "Correct plain <em>answer</em>" in content
    assert "math first" in content
    for marker in ("☐", "☒", "[ ]", "[x]"):
        assert marker not in content


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


MERMAID_INPUT = """
```{.mermaid alt="A to B"}
flowchart LR
    A --> B
```
"""


def test_mermaid_filter_html():
    cmd = ["pandoc", "-f", "markdown", "-t", "html", f"--lua-filter={FILTER_PATH}"]
    res = subprocess.run(cmd, input=MERMAID_INPUT, capture_output=True, text=True)
    assert res.returncode == 0
    assert '<div class="mermaid-diagram" id="mermaid-diagram-1" role="img" aria-label="A to B">' in res.stdout
    assert '<script type="text/x-mermaid">flowchart LR\n    A --> B</script>' in res.stdout


def _mermaid_epub_chapter(env=None):
    with tempfile.TemporaryDirectory() as tmpdir:
        epub_path = os.path.join(tmpdir, "out.epub")
        cmd = ["pandoc", "-f", "markdown", "-t", "epub3", f"--lua-filter={FILTER_PATH}", "-o", epub_path]
        res = subprocess.run(cmd, input=MERMAID_INPUT, capture_output=True, text=True,
                             env=dict(os.environ, **(env or {})))
        assert res.returncode == 0
        import zipfile
        with zipfile.ZipFile(epub_path, "r") as z:
            return z.read("EPUB/text/ch001.xhtml").decode("utf-8"), z.namelist()


def test_mermaid_filter_epub_fallback():
    content, _ = _mermaid_epub_chapter()
    assert "mermaid-diagram-epub" in content
    assert '<pre class="mermaid-source">' in content
    assert "<script" not in content


def test_mermaid_filter_epub_uses_rendered_svg():
    text = mermaid_render.extract_mermaid_blocks(MERMAID_INPUT)[0]
    with tempfile.TemporaryDirectory() as svg_dir:
        with open(os.path.join(svg_dir, f"{abc_render.abc_hash(text)}-1.svg"), "w") as f:
            f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>')
        content, names = _mermaid_epub_chapter({"LIBROMORPH_MERMAID_SVG_DIR": svg_dir})
    assert 'class="mermaid-svg"' in content
    assert 'alt="A to B"' in content
    assert "mermaid-source" not in content
    assert any(name.endswith(".svg") for name in names)


def test_mermaid_renderer_resolution(monkeypatch):
    assert mermaid_render.resolve_renderer("none") is None
    with pytest.raises(mermaid_render.MermaidRenderError, match="Unknown mermaid_renderer"):
        mermaid_render.resolve_renderer("graphviz")

    monkeypatch.setattr(mermaid_render.shutil, "which", lambda name: None)
    assert "not found" in mermaid_render.check_renderer("mmdc")
    monkeypatch.setattr(mermaid_render, "check_renderer",
                        lambda name: None if name == "mmdc" else "missing")
    assert mermaid_render.resolve_renderer("auto") == "mmdc"
    with pytest.raises(mermaid_render.MermaidRenderError, match="libromorph\[diagrams\]"):
        mermaid_render.resolve_renderer("mermaid-js")


def test_normalize_svg_sizes_percentage_width():
    from libromorph.render_utils import normalize_svg
    svg = normalize_svg('<svg width="100%" viewBox="0 0 320 120" xmlns="http://www.w3.org/2000/svg"></svg>')
    assert 'width="320"' in svg and 'height="120"' in svg and "100%" not in svg


CHORD_INPUT = """
```chord
F:  133211  fingers=134211
Am  2000
D   x,x,0,14,15,14 base=13
```
"""


def _run_filter(md, fmt="html"):
    cmd = ["pandoc", "-f", "markdown", "-t", fmt, f"--lua-filter={FILTER_PATH}"]
    return subprocess.run(cmd, input=md, capture_output=True, text=True)


def test_chord_filter_html():
    res = _run_filter(CHORD_INPUT)
    assert res.returncode == 0
    out = res.stdout
    assert '<div class="chord-diagrams" id="chord-diagrams-1">' in out
    assert out.count('<div class="chord-diagram">') == 3
    assert 'aria-label="F chord: 1 3 3 2 1 1"' in out
    assert 'aria-label="Am chord: 2 0 0 0"' in out
    # F: barre for finger 1 across all six strings, nut drawn (base fret 1)
    assert 'rx="6.5"' in out
    assert ">1</text>" in out and ">4</text>" in out
    # D: explicit base fret is labelled
    assert ">13fr</text>" in out
    assert 'stroke="currentColor"' in out


def test_chord_filter_error_shows_source():
    res = _run_filter("```chords\nG 3200z3\n```\n")
    assert res.returncode == 0
    assert "chord-diagrams-error" in res.stdout
    assert "invalid fret" in res.stdout
    assert "G 3200z3" in res.stdout
    assert "invalid fret" in res.stderr

    res = _run_filter("```chord\nC x32010 fingers=x3201\n```\n")
    assert "fingers has 5 entries but there are 6 strings" in res.stdout


def test_chord_filter_epub():
    with tempfile.TemporaryDirectory() as tmpdir:
        epub_path = os.path.join(tmpdir, "out.epub")
        cmd = ["pandoc", "-f", "markdown", "-t", "epub3", f"--lua-filter={FILTER_PATH}", "-o", epub_path]
        res = subprocess.run(cmd, input=CHORD_INPUT, capture_output=True, text=True)
        assert res.returncode == 0
        import zipfile
        with zipfile.ZipFile(epub_path, "r") as z:
            content = z.read("EPUB/text/ch001.xhtml").decode("utf-8")
            svgs = [z.read(n).decode("utf-8") for n in z.namelist() if n.endswith(".svg")]
    assert "chord-diagrams-epub" in content
    assert content.count('class="chord-svg"') == 3
    assert 'alt="Am chord: 2 0 0 0"' in content
    assert len(svgs) == 3
    assert all("currentColor" not in svg and 'xmlns="http://www.w3.org/2000/svg"' in svg for svg in svgs)


FRETBOARD_INPUT = '''
```{.fretboard alt="A minor pentatonic"}
{"title":"A minor pentatonic","fretCount":8,"scale":{"root":"A","type":"minor pentatonic"}}
```
```{.fretdrom alt="Riff tab"}
{name:"Riff",tab:[{name:"e",wave:"03.."},{name:"B",wave:"...."}]}
```
'''


def test_fret_diagram_filter_html():
    res = _run_filter(FRETBOARD_INPUT)
    assert res.returncode == 0
    assert 'class="lm-fret-diagram lm-fretboard"' in res.stdout
    assert 'class="lm-fret-diagram lm-fretdrom"' in res.stdout
    assert '<script type="application/json">' in res.stdout
    assert '<script type="fretdrom">' in res.stdout
    assert 'aria-label="A minor pentatonic"' in res.stdout


def test_fret_diagram_filter_epub_embeds_svg():
    texts = (fretboard_render.extract_fretboard_blocks(FRETBOARD_INPUT),
             fretboard_render.extract_fretdrom_blocks(FRETBOARD_INPUT))
    with tempfile.TemporaryDirectory() as tmpdir:
        env = dict(os.environ)
        for kind, source in zip(("FRETBOARD", "FRETDROM"), texts):
            svg_dir = os.path.join(tmpdir, kind.lower())
            os.makedirs(svg_dir)
            with open(os.path.join(svg_dir, f"{abc_render.abc_hash(source[0])}-1.svg"), "w") as stream:
                stream.write('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>')
            env[f"LIBROMORPH_{kind}_SVG_DIR"] = svg_dir
        epub_path = os.path.join(tmpdir, "fret.epub")
        res = subprocess.run(["pandoc", "-f", "markdown", "-t", "epub3",
                              f"--lua-filter={FILTER_PATH}", "-o", epub_path],
                             input=FRETBOARD_INPUT, capture_output=True, text=True, env=env)
        assert res.returncode == 0, res.stderr
        with zipfile.ZipFile(epub_path) as archive:
            content = archive.read("EPUB/text/ch001.xhtml").decode("utf-8")
            assert content.count('class="lm-fret-diagram lm-fret-diagram-epub"') == 2
            assert len([name for name in archive.namelist() if name.endswith(".svg")]) == 2


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


def _write_book(book_dir, index_yaml, chapters):
    with open(os.path.join(book_dir, "book.yaml"), "w", encoding="utf-8") as f:
        f.write('title: "Labels"\nauthor: "Tester"\n' + index_yaml)
    for name, text in chapters:
        with open(os.path.join(book_dir, name), "w", encoding="utf-8") as f:
            f.write(text)


LABEL_CHAPTERS = [
    ("01-preface.md", "# Preface\n\nA [Pulse]{.index} here.\n"),
    ("02-harmony.md", "# 03 — Harmony\n\nA [Shell]{.index} here.\n"),
]


def test_index_chapter_labels_default_to_build_position():
    with tempfile.TemporaryDirectory() as book_dir:
        _write_book(book_dir, "", LABEL_CHAPTERS)
        config = BookConfig.load(book_dir)
        builder = BookBuilder(config=config, output_dir=os.path.join(book_dir, "dist"))
        assert config.index_chapter_labels == "number"
        assert [builder._index_chapter_label(c) for c in config.chapters] == ["Ch. 1", "Ch. 2"]


def test_index_chapter_labels_from_titles():
    with tempfile.TemporaryDirectory() as book_dir:
        _write_book(book_dir, "index:\n  chapter_labels: title\n", LABEL_CHAPTERS)
        config = BookConfig.load(book_dir)
        builder = BookBuilder(config=config, output_dir=os.path.join(book_dir, "dist"))
        assert [builder._index_chapter_label(c) for c in config.chapters] == ["Preface", "Ch. 03"]

        indexer = BookIndexer()
        for ch, (_, text) in zip(config.chapters, LABEL_CHAPTERS):
            indexer.process_chapter_markdown(
                markdown=text, chapter_num=ch.number, chapter_title=ch.title,
                chapter_href=ch.html_filename, chapter_label=builder._index_chapter_label(ch))
        rendered = indexer.render_markdown_index(for_epub=True)
        assert "[Ch. 03](#" in rendered
        assert "[Preface](#" in rendered
        assert "Ch. 2" not in rendered


def test_index_chapter_labels_rejects_unknown_value():
    with tempfile.TemporaryDirectory() as book_dir:
        _write_book(book_dir, "index:\n  chapter_labels: roman\n", LABEL_CHAPTERS)
        with pytest.raises(ValueError, match="chapter_labels"):
            BookConfig.load(book_dir)


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


def test_generated_cover_goes_to_output_not_source():
    with tempfile.TemporaryDirectory() as book_dir, tempfile.TemporaryDirectory() as out_dir:
        with open(os.path.join(book_dir, "book.yaml"), "w", encoding="utf-8") as f:
            f.write('title: "No Cover Book"\nauthor: "Tester"\nindex:\n  enabled: false\n')
        with open(os.path.join(book_dir, "01-only.md"), "w", encoding="utf-8") as f:
            f.write("# Only chapter\n\nText.\n")
        before = sorted(os.listdir(book_dir))

        config = BookConfig.load(book_dir)
        results = BookBuilder(config=config, output_dir=out_dir).build(target_format="all")

        assert sorted(os.listdir(book_dir)) == before
        assert os.path.exists(os.path.join(out_dir, "generated-cover.png"))
        assert os.path.exists(results["epub"])
        assert os.path.exists(os.path.join(results["html"], "cover.png"))


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
        assert os.path.exists(os.path.join(results["html"], "assets", "js", "mermaid-init.js"))
