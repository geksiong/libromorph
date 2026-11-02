# LibroMorph (リブロモルフ)

> A modern, Pandoc-powered publishing command-line toolkit that compiles folders of Markdown files into publication-grade **EPUB 3** ebooks and responsive **HTML websites**.

---

## Features

- 📖 **Dual-Target Compilation**: Converts a single source folder of Markdown chapters into both standalone **EPUB 3** files and interactive static **HTML book websites**.
- 🎨 **Five Genre-Specific Themes**:
  - `classic-novel`: Elegant literary serif, first-line indents, chapter header flourishes, dropcaps, fleurons (`❦`).
  - `technical`: Clean sans-serif, syntax-highlighted code blocks, admonitions (`note`, `tip`, `warning`, `theorem`), structured formula display.
  - `cjk-vertical`: Traditional East Asian layout (`writing-mode: vertical-rl`), right-to-left EPUB page turning (`page-progression-direction="rtl"`), Mincho typography.
  - `modern-minimal`: Clean Scandinavian / Swiss aesthetic, generous line-height, card-based components.
  - `fantasy-vintage`: Antique parchment tones, illuminated dropcaps, decorative borders, ornamental dividers (`❧ ❧ ❧`).
- 🖼 **Automated & Custom Ebook Covers**: Supports custom cover images (`cover.png`/`cover.jpg`) or automatically generates high-resolution typography covers matching your chosen genre theme.
- 📑 **Automatic Table of Contents (TOC)**: Deep hierarchical navigation for EPUB (`nav.xhtml` & `toc.ncx`) and responsive slide-out drawer with real-time search filtering for web readers.
- 🏷 **Back-of-the-Book Index Creation**: Discovers terms tagged in paragraphs (`[term]{.index}`, `[term]{.index entry="Parent!Child"}`), organizes them alphabetically with jump pills, and cross-references them with clickable links back to exact sections.
- 🎌 **Japanese Furigana (Ruby Text)**: Intuitive shorthand `{漢字|かんじ}` and Pandoc spans `[漢字]{.ruby ruby="かんじ"}` compiled to semantic `<ruby>` and `<rp>` fallbacks.
- ⇅ **Vertical Writing & Tate-chū-yoko**: Full support for vertical columns and upright numbers in vertical text via `{tcy:42}` and `[2026]{.tcy}`.
- 📝 **Interactive Self-Check Quizzes**: Write quizzes using simple markdown lists (`::: quiz` and `- [x]`). Generates animated interactive quiz widgets for HTML and `<details>` answer reveals for EPUB readers.
- 📐 **Mathematical Formulas**: LaTeX formulas (`$E = mc^2$` and `$$\dots$$`) rendered to standards-compliant **MathML** for EPUB 3, and interactive **MathJax 3** for web readers.
- 🎵 **ABC Music Notation**: Fenced ` ```abc ` code blocks are rendered as sheet music with [abcjs](https://www.abcjs.net) in web readers (with a "View ABC Source" toggle), and pre-rendered to SVG images for EPUB with your choice of abcjs, abcm2ps or abc2svg.
- 🔀 **Mermaid Diagrams**: Fenced ` ```mermaid ` code blocks are drawn with [Mermaid](https://mermaid.js.org) in web readers (following the light/dark color mode), and pre-rendered to SVG images for EPUB with mermaid.js or mermaid-cli.
- 🎸 **Chord Diagrams**: Fenced ` ```chord ` code blocks draw fretboard chord diagrams (guitar, ukulele or any fretted instrument) as SVG, with fingerings and barres, with no extra dependencies.

---

## Installation

Ensure you have [Pandoc](https://pandoc.org) (v2.14+ or v3.0+) and Python 3.8+ installed:

```bash
# Clone the repository
git clone https://github.com/your-username/libro-morph.git
cd libro-morph

# Install in editable mode
pip install -e . --break-system-packages
```

---

## CLI Usage

### 1. Build a Book
To compile a folder of Markdown files into both EPUB and an HTML website:

```bash
# Build default outputs (EPUB + HTML) into <book-dir>/dist
libromorph build demo-book

# Choose a specific genre theme
libromorph build demo-book --theme classic-novel

# Force vertical writing mode (vertical-rl) for Japanese/Chinese text
libromorph build demo-book --theme cjk-vertical --vertical

# Output only EPUB or only HTML
libromorph build demo-book -f epub
libromorph build demo-book -f html -o ./public
```

### 2. Preview the HTML Website
Start a local live preview server:

```bash
libromorph serve demo-book/dist/html
# or simply:
libromorph serve demo-book
```

### 3. List Available Themes
```bash
libromorph list-themes
```

### 4. Initialize a New Book Project
```bash
libromorph init my-new-book --demo
```

---

## Book Project Structure

A LibroMorph book project is simply a folder containing a `book.yaml` metadata file and Markdown chapters:

```text
my-book/
├── book.yaml          # Book metadata, theme, and settings
├── cover.png          # Optional cover image (auto-generated if omitted)
├── 01-intro.md        # Chapter 1
├── 02-mechanics.md    # Chapter 2
├── 03-poetry.md       # Chapter 3
└── images/            # Optional illustrations or media
```

### Sample `book.yaml`
```yaml
title: "The Polyglot Codex"
subtitle: "A Journey Through Mathematics and Literature"
author: "Antigravity Research Group"
language: "en"
date: "2026-10-27"
publisher: "LibroMorph Editions"
rights: "CC BY 4.0"
description: "A showcase volume demonstrating digital publishing features."
theme: "technical"     # classic-novel | technical | cjk-vertical | modern-minimal | fantasy-vintage
vertical_layout: false # set to true for traditional vertical-rl reading

toc:
  enabled: true
  depth: 3

index:
  enabled: true
  title: "Index of Subjects and Names"

abc_renderer: auto     # EPUB music scores: auto | abcjs | abcm2ps | abc2svg | none
mermaid_renderer: auto # EPUB diagrams: auto | mermaid-js | mmdc | none
```

---

## Markdown Authoring Syntax

### 1. Japanese Furigana (Ruby Text)
```markdown
{吾輩|わがはい}は{猫|ねこ}である。名前は[未だ]{ruby="まだ"}無い。
```

### 2. Tate-chū-yoko (Upright numbers in vertical text)
```markdown
Published in the {tcy:38}th year of Meiji ([1905]{.tcy}).
```

### 3. Interactive Self-Testing Quizzes
```markdown
::: quiz
**Question:** What is the fundamental unit of information in quantum computing?

- [ ] Classical bit
- [x] Qubit
- [ ] Byte
- [ ] Qutrit

*Explanation:* A qubit represents a two-state quantum-mechanical system.
:::
```

### 4. Back-of-the-Book Indexing
```markdown
# Visible term indexed under its own name
[Quantum Entanglement]{.index}

# Visible text indexed under custom term
[Albert Einstein]{.index entry="Einstein, Albert"}

# Hierarchical entry (Category > Subcategory)
[Entangled states]{.index entry="Quantum Mechanics!Entanglement"}

# Invisible index anchor
{index: "Special Relativity"}
```

### 5. Admonitions & Callouts
```markdown
::: note
This is an informational note.
:::

::: theorem
**Pythagorean Theorem**: $a^2 + b^2 = c^2$.
:::

::: tip
Helpful advice for the reader.
:::
```

### 6. Math Formulas
```markdown
Inline: $E = mc^2$ and block equations:

$$\int_{-\infty}^{+\infty} e^{-x^2} \, dx = \sqrt{\pi}$$
```

### 7. ABC Music Notation
~~~markdown
```abc
X:1
T:Ode to Joy
M:4/4
L:1/4
K:D
F F G A | A G F E | D D E F | F3/2 E/ E2 |
```
~~~
The `T:` field is used as the score's title. Add `{#my-id .abc}` attributes instead of `abc` to set a custom anchor id.

Web readers render scores in the browser with abcjs. For EPUB, scores are rendered to SVG images at build time with the engine chosen by `abc_renderer` in `book.yaml` or `--abc-renderer` on the command line:

| Renderer  | Requirements                                                                 |
|-----------|------------------------------------------------------------------------------|
| `abcjs`   | `pip install 'libromorph[music]'` plus Chrome/Chromium (or `playwright install chromium`); network access to load abcjs. Matches the web reader. |
| `abcm2ps` | `abcm2ps` on `PATH`                                                          |
| `abc2svg` | `npm install -g abc2svg` and a JS interpreter (`node`, `qjs`, ...)          |
| `auto`    | *(default)* first available of the above; falls back to text with a warning |
| `none`    | show the ABC source as text in EPUB                                         |

Dependencies are checked before rendering; an explicitly chosen renderer that is unavailable fails the build with an install hint.

### 8. Mermaid Diagrams
~~~markdown
```{.mermaid alt="Order flow: cart to checkout to confirmation"}
flowchart LR
    cart[Cart] --> checkout[Checkout] --> done[Confirmation]
```
~~~
Plain ` ```mermaid ` works too; the optional `alt` attribute provides the accessible description (default: "Diagram"). Web readers load mermaid.js only on pages that contain diagrams. For EPUB, diagrams are rendered to SVG images at build time with the engine chosen by `mermaid_renderer` in `book.yaml` or `--mermaid-renderer`:

| Renderer     | Requirements                                                              |
|--------------|---------------------------------------------------------------------------|
| `mermaid-js` | `pip install 'libromorph[diagrams]'` plus Chrome/Chromium (or `playwright install chromium`); network access to load mermaid.js. Matches the web reader. |
| `mmdc`       | `npm install -g @mermaid-js/mermaid-cli` (uses your system Chrome when available) |
| `auto`       | *(default)* first available of the above; falls back to text with a warning |
| `none`       | show the Mermaid source as text in EPUB                                  |

EPUB diagrams use plain SVG text labels (no HTML `foreignObject`) so they display in e-readers.

### 9. Chord Diagrams
~~~markdown
```chord
C    x32010  fingers=x32010
G    320003  fingers=210003
F    133211  fingers=134211
A    x,12,14,14,14,12  fingers=x,1,3,3,3,1
```
~~~
Each line defines one chord, `NAME FRETS [options]`, drawn side by side:

- **FRETS** has one entry per string, lowest string first: `x` = muted, `0` = open, a number = fret. Separate entries with commas when any fret is 10 or higher. The number of entries sets the number of strings, so `2000` draws a four-string ukulele chord.
- `fingers=` uses the same layout (`0`, `x` or `-` = no finger, `T` = thumb). Strings held by the same finger on the same fret are drawn as a barre.
- `base=N` sets the fret shown at the top of the diagram. By default it is the nut, or the lowest fretted note (labelled e.g. `5fr`) when the chord doesn't fit in the first four frets.
- `barre=N` draws a barre on fret N without needing `fingers=`.

` ```chords ` works as well. Diagrams are drawn as SVG by the Lua filter itself: inline in web readers, where they follow the light/dark color mode, and as SVG images in EPUB. A block with a syntax error is shown as source text with the error message, and the build prints a warning.

---

## Running Tests

```bash
pytest -v tests/test_libromorph.py
```
