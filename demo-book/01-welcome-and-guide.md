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
9. **Music Notation**: Fenced `abc` code blocks in [ABC notation]{.index entry="Music!ABC Notation"} are engraved as sheet music in web readers and shown as notation in EPUB:

```abc
X:1
T:Ode to Joy
M:4/4
L:1/4
K:D
F F G A | A G F E | D D E F | F3/2 E/ E2 |
```

10. **Diagrams**: Fenced `mermaid` code blocks are drawn as [Mermaid]{.index entry="Diagrams!Mermaid"} diagrams, such as this overview of the LibroMorph build pipeline:

```{.mermaid alt="LibroMorph build pipeline: Markdown chapters flow through the indexer and Pandoc with the Lua filter into EPUB and HTML outputs"}
flowchart LR
    md[Markdown chapters] --> idx[Indexer]
    idx --> pandoc[Pandoc + Lua filter]
    pandoc --> epub[EPUB 3]
    pandoc --> html[HTML web reader]
    svg[SVG renderers] -.-> epub
```

11. **Chord Diagrams**: Fenced `chord` code blocks draw [chord diagrams]{.index entry="Music!Chord Diagrams"} for guitar, ukulele and other fretted instruments, with fingerings and barres:

```chord
C    x32010  fingers=x32010
G    320003  fingers=210003
Am   x02210  fingers=x02310
F    133211  fingers=134211
```

::: tip
Try switching between color modes (Light, Dark, and Sepia) using the dropdown in the top navigation bar!
:::

In the following chapters, we will examine each of these capabilities in depth, beginning with mathematical typesetting and technical admonitions.
