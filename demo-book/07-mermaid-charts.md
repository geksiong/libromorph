# Mermaid Charts

Fenced `mermaid` blocks turn plain text into diagrams. The web reader draws them in the current color theme; the EPUB build embeds SVG images when a Mermaid renderer is available. These examples show three chart types with different uses.

## Flowchart: The Build Pipeline

A [flowchart]{.index entry="Diagrams!Flowcharts"} shows the main steps and output paths. The dashed arrow indicates that pre-rendered SVG assets are included in EPUB.

```{.mermaid alt="LibroMorph build pipeline: Markdown chapters go through the indexer and Pandoc to EPUB and HTML; SVG assets are included in EPUB"}
flowchart LR
    md[Markdown chapters] --> idx[Indexer]
    idx --> pandoc[Pandoc + Lua filter]
    pandoc --> epub[EPUB 3]
    pandoc --> html[HTML web reader]
    svg[SVG renderers] -.-> epub
```

## Sequence Diagram: Building a Chapter

A [sequence diagram]{.index entry="Diagrams!Sequence Diagrams"} makes the order of interactions explicit, including the reply from Pandoc to LibroMorph.

```{.mermaid alt="Sequence diagram: the author starts a build, LibroMorph asks Pandoc to convert a chapter, and the reader receives the output"}
sequenceDiagram
    participant Author
    participant LibroMorph
    participant Pandoc
    participant Reader
    Author->>LibroMorph: Start build
    LibroMorph->>Pandoc: Convert chapter
    Pandoc-->>LibroMorph: Return document
    LibroMorph-->>Reader: Publish HTML or EPUB
```

## State Diagram: Editorial Workflow

A [state diagram]{.index entry="Diagrams!State Diagrams"} captures the allowed paths through a review process. The revision arrow returns a chapter to Draft.

```{.mermaid alt="State diagram: a draft moves to review, may return for revision, or is approved and published"}
stateDiagram-v2
    [*] --> Draft
    Draft --> Review: Submit
    Review --> Draft: Revise
    Review --> Published: Approve
    Published --> [*]
```

## Built-in Themes and Looks

Mermaid 12 gives the flowchart, sequence, and state diagrams above its new `redux-color` theme and `neo` look by default. A diagram can choose another built-in appearance in its frontmatter. These samples use the same small process so the differences are easy to see. Their light backgrounds keep the fixed themes readable when the web reader is in dark mode.

::: {.mermaid-theme-gallery}

### Neo theme

```{.mermaid alt="Two-step process using Mermaid's neo theme and neo look"}
---
config:
  theme: neo
  look: neo
---
flowchart LR
    Draft --> Published
```

### Forest theme, hand-drawn look

```{.mermaid alt="Two-step process using Mermaid's forest theme and hand-drawn look"}
---
config:
  theme: forest
  look: handDrawn
---
flowchart LR
    Draft --> Published
```

### Neutral theme, classic look

```{.mermaid alt="Two-step process using Mermaid's neutral theme and classic look"}
---
config:
  theme: neutral
  look: classic
---
flowchart LR
    Draft --> Published
```

:::
