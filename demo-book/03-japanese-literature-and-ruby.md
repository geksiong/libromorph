# Japanese Literature & Ruby Furigana

[J]{.dropcap}apanese literary writing frequently employs [furigana]{.index entry="Japanese!Furigana"} (振仮名)—small phonetic ruby characters placed alongside or above kanji logographs to guide pronunciation, clarify archaic vocabulary, or convey poetic double meanings.

LibroMorph introduces clean markdown notation for authoring ruby text:
- **Shorthand Syntax**: `{漢字|かんじ}`
- **Span Syntax**: `[漢字]{.ruby ruby="かんじ"}`
- **Standard HTML**: `<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>`

All three variations automatically compile to W3C-compliant `<ruby>` markup with semantic `<rp>` parentheses fallbacks for non-ruby e-readers.

## Classic Masterpieces with Furigana

### 1. Natsume Sōseki: *I Am a Cat*

The famous opening lines of [Natsume Sōseki]{.index entry="Literature!Natsume Sōseki"} (夏目漱石)'s masterpiece, published in the Meiji era ({tcy:38}th year of Meiji, [1905]{.tcy}):

> {吾輩|わがはい}は{猫|ねこ}である。{名前|なまえ}は[未だ]{ruby="まだ"}無い。
> どこで{生|う}れたかとんと{見当|けんとう}がつかぬ。
> 何でも{薄暗|うすぐら}いじめじめした{所|ところ}で{微|かす}かに泣いていた事だけは{記憶|きおく}している。

### 2. Akutagawa Ryūnosuke: *In a Grove*

From [Akutagawa Ryūnosuke]{.index entry="Literature!Akutagawa Ryūnosuke"} (芥川龍之介)'s gripping psychological tale *Yabu no Naka* ({藪|やぶ}の{中|なか}):

> {旅法師|たびほうし}の{物語|ものがたり}。
> 「あの{死骸|しがい}を{見付|みつ}けましたのは、{昨夜|ゆうべ}の{暮|く}れ{方|がた}でございます。
> {関山|せきやま}から{山科|やましな}へ{越|こ}える{道|みち}の{途中|とちゅう}で、{草|くさ}の{中|なか}に{倒|たお}れていたのでございます。」

### 3. Matsuo Bashō's Iconic Haiku

The legendary haiku by [Matsuo Bashō]{.index entry="Literature!Matsuo Bashō"} ({松尾|まつお}{芭蕉|ばしょう}):

> {古池|ふるいけ}や  
> {蛙|かわず}{飛|と}びこむ  
> {水|みず}の{音|おと}

## Tate-chū-yoko (縦中横) for Numbers & Symbols

In East Asian vertical typography, Western numbers and abbreviations inside vertical columns are rotated upright using [tate-chū-yoko]{.index entry="Japanese!Tate-chū-yoko"}:

- `{tcy:42}` renders as {tcy:42}
- `[99]{.tcy}` renders as [99]{.tcy}
- `{tcy:!?}` renders as {tcy:!?}

When viewing this chapter or toggling to **Vertical Mode** (via the top navigation button `⇅ Switch to Vertical`), notice how the ruby annotations gracefully shift to the right side of each kanji column, and the numbers remain upright.

::: tip
**Ruby Alignment Tip**: LibroMorph's stylesheets automatically align ruby annotations evenly across base kanji characters, preserving elegant typographic balance regardless of font size.
:::

## Comprehension Check: Furigana and Literature

::: quiz
**Question 2:** In the opening sentence of Natsume Sōseki's *I Am a Cat*, what is the reading of the archaic first-person pronoun `{吾輩|わがはい}`?

- [ ] わたし (Watashi)
- [ ] ぼく (Boku)
- [x] わがはい (Wagahai)
- [ ] おれ (Ore)

*Explanation:* 「吾輩」 is pronounced *wagahai*, an elevated, slightly pompous pronoun used humorously by the feline protagonist.
:::
