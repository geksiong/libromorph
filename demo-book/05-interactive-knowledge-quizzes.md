# Comprehensive Interactive Challenge

[E]{.dropcap}ducational research has repeatedly demonstrated that active recall through [interactive quizzes]{.index entry="Pedagogy!Interactive Quizzes"} significantly improves long-term retention compared to passive rereading.

In this concluding chapter, we present a multi-disciplinary assessment challenging your understanding of mathematics, literature, and digital publishing.

## Quiz 1: Mathematical Foundations

::: quiz
**Question 1:** What is the exact value of the Gaussian integral $\int_{-\infty}^{+\infty} e^{-x^2} \, dx$?

- [ ] $\pi$
- [x] $\sqrt{\pi}$
- [ ] $\frac{\pi}{2}$
- [ ] $2\pi$

*Explanation:* By evaluating the double integral in polar coordinates $\left(\int_{-\infty}^\infty e^{-x^2} dx\right)^2 = \int_0^{2\pi} d\theta \int_0^\infty r e^{-r^2} dr = \pi$, we obtain $\sqrt{\pi}$.
:::

## Quiz 2: EPUB Publishing Standards

::: quiz
**Question 2:** Which EPUB 3 metadata attribute directs modern e-readers to turn pages right-to-left for vertical East Asian typography?

- [ ] `writing-mode="vertical-rl"`
- [ ] `direction="rtl"`
- [x] `page-progression-direction="rtl"`
- [ ] `book-orient="vertical"`

*Explanation:* In the EPUB 3 Open Packaging Format (OPF) specification, `<spine page-progression-direction="rtl">` dictates right-to-left page turning order, essential for Japanese and Chinese vertical editions.
:::

## Quiz 3: Literature & Linguistics

::: quiz
**Question 3:** What semantic HTML5 tag is utilized by LibroMorph to provide fallbacks for ruby text in older e-readers?

- [ ] `<ruby-fallback>`
- [ ] `<alt>`
- [x] `<rp>` (Ruby Parentheses)
- [ ] `<noscript>`

*Explanation:* The `<rp>` tag encloses punctuation (such as parentheses) that is hidden by modern ruby-aware renderers but displayed by legacy readers so text appears as 「漢字(かんじ)」.
:::

## Summary of Publishing Features

| Feature | EPUB 3 Support | Web Reader Support | Syntactic Notation |
| :--- | :--- | :--- | :--- |
| **Mathematical Formulas** | Native MathML | MathJax 3 / KaTeX | `$E=mc^2$` / `$$\dots$$` |
| **Ruby Furigana** | `<ruby><rt>` tags | Responsive CSS Ruby | `{漢字\|かんじ}` |
| **Tate-chū-yoko** | CSS text-combine | CSS text-combine | `{tcy:42}` / `[42]{.tcy}` |
| **Vertical Layout** | OPF `progression="rtl"` | CSS `vertical-rl` toggle | Theme `cjk-vertical` |
| **Interactive Quizzes** | Accessible `<details>` | Real-time JS scoring | `::: quiz` fenced divs |
| **Back-of-the-Book Index**| Hyperlinked sections | Searchable index page | `[term]{.index}` |

::: note
All index terms marked in this volume have been automatically compiled into the **Alphabetical Index** chapter that follows. Check it out to see cross-references and anchors in action!
:::
