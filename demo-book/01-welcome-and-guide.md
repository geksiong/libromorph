# Introduction to LibroMorph

[L]{.dropcap}ibroMorph is a next-generation publishing toolkit built upon the rock-solid foundations of [Pandoc]{.index entry="Pandoc"}. It bridges the divide between lightweight authoring in [Markdown]{.index entry="Markdown"} and professional, publishing-grade output in both [EPUB 3]{.index entry="EPUB!EPUB 3 Specification"} and modern, responsive static [HTML websites]{.index entry="HTML5!Static Web Reader"}.

Whether you are crafting an academic textbook filled with mathematical theorems, a serialized Japanese light novel requiring precise [furigana]{.index entry="Japanese!Furigana"} ruby annotations, or an antique fantasy grimoire, LibroMorph transforms plain text files into publication-ready digital masterworks.

::: note
**Quick Start:** This demo volume showcases every core feature enabled by LibroMorph. You can compile this entire book to both EPUB and a static website with a single command:
```bash
libromorph build demo-book
```
:::

## Key Publishing Capabilities

LibroMorph integrates the following capabilities seamlessly into Pandoc's processing pipeline:

1. **Cover Generation & Embedding**: Automatically embeds high-resolution cover graphics in EPUB manifests and generates hero cover cards for web readers.
2. **Automated Table of Contents**: Generates deep hierarchical navigation for EPUB (`nav.xhtml`, `toc.ncx`) and a responsive drawer navigation sidebar with live search filtering for web readers.
3. **Back-of-the-Book Index Creation**: Scans paragraphs for index terms, assigns stable hyperlinked anchors, and builds an alphabetical multi-level [index]{.index entry="Index!Back-of-the-Book"}.
4. **Ruby Pronunciation Annotation**: Native support for Japanese furigana and Chinese pinyin using clean `{漢字|かんじ}` shorthand and Pandoc span attributes.
5. **Vertical Writing Mode (縦書き)**: Full support for CSS `writing-mode: vertical-rl` and EPUB 3 `page-progression-direction="rtl"`, along with [tate-chū-yoko]{.index entry="Japanese!Tate-chū-yoko"} (`.tcy`) for upright numbers in vertical columns.
6. **Interactive Self-Testing Quizzes**: Dynamic client-side interactive quizzes with instant grading and explanations for web readers, alongside accessible `<details>` fallbacks for EPUB e-readers.
7. **Mathematical Typesetting**: Standards-compliant [MathML]{.index entry="Mathematics!MathML"} for EPUB 3 readers, paired with [MathJax 3]{.index entry="Mathematics!MathJax"} for crisp, responsive web formula rendering.
8. **Genre-Specific Typography Themes**: Choose between `classic-novel`, `technical`, `cjk-vertical`, `modern-minimal`, and `fantasy-vintage`.

::: tip
Try switching between color modes (Light, Dark, and Sepia) using the dropdown in the top navigation bar!
:::

In the following chapters, we will examine each of these capabilities in depth, beginning with mathematical typesetting and technical admonitions.
