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

---

## Running Tests

```bash
pytest -v tests/test_libromorph.py
```
