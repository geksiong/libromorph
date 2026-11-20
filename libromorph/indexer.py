"""
libromorph.indexer: Comprehensive back-of-the-book indexing system.
Discovers indexed terms in markdown chapters, generates unique anchors,
and constructs professional alphabetical index sections for EPUB and HTML.
"""

import re
import unicodedata
from collections import defaultdict
from typing import Dict, List, Tuple, Optional


def slugify(text: str) -> str:
    """Create a URL-safe, anchor-friendly slug from text."""
    text = unicodedata.normalize('NFKD', text)
    # Allow alphanumeric, hyphens, and CJK characters
    text = re.sub(r'[^\w\s\u4e00-\u9fff\u3040-\u30ff\u3400-\u4dbf-]', '', text).strip()
    text = re.sub(r'[-\s]+', '-', text)
    return text.lower() or 'idx'


class IndexEntry:
    def __init__(self, raw_entry: str, anchor_id: str, chapter_title: str,
                 chapter_num: int, chapter_href: str, section_title: str = "",
                 chapter_label: str = ""):
        self.raw_entry = raw_entry.strip()
        self.anchor_id = anchor_id
        self.chapter_title = chapter_title
        self.chapter_num = chapter_num
        self.chapter_href = chapter_href
        self.section_title = section_title
        # Text shown for this reference in the index, e.g. "Ch. 3".
        self.chapter_label = chapter_label or f"Ch. {chapter_num}"

        # Check for hierarchical levels (e.g., "Physics!Quantum Mechanics!Entanglement")
        parts = [p.strip() for p in self.raw_entry.split('!') if p.strip()]
        self.main_term = parts[0] if parts else self.raw_entry
        self.sub_terms = parts[1:] if len(parts) > 1 else []

    @property
    def sort_key(self) -> str:
        return self.main_term.lower()

    @property
    def letter_group(self) -> str:
        first = self.main_term[0].upper()
        if 'A' <= first <= 'Z':
            return first
        if '\u4e00' <= first <= '\u9fff' or '\u3040' <= first <= '\u30ff':
            return "CJK"
        return "#"


class BookIndexer:
    def __init__(self):
        self.entries: List[IndexEntry] = []
        self._anchor_counts: Dict[str, int] = defaultdict(int)

    def generate_anchor_id(self, term: str) -> str:
        slug = slugify(term)[:30]
        self._anchor_counts[slug] += 1
        return f"idx-{slug}-{self._anchor_counts[slug]}"

    def process_chapter_markdown(self, markdown: str, chapter_num: int,
                                 chapter_title: str, chapter_href: str,
                                 chapter_label: str = "") -> Tuple[str, List[IndexEntry]]:
        """
        Parses index tags in the markdown, injects HTML anchors with IDs,
        and returns the transformed markdown and discovered IndexEntry list.

        Supported syntax:
        1. [visible text]{.index entry="Index Entry" id="optional-id"}
        2. [visible text]{.index} (indexes 'visible text')
        3. {index: "Index Entry"} (invisible index marker)
        """
        discovered = []
        current_section = chapter_title

        lines = markdown.splitlines()
        new_lines = []

        for line in lines:
            # Track current section header if any
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                current_section = header_match.group(2).strip()

            # Pattern 1: [visible text]{.index ...} or [visible text]{class="index" ...}
            # Handles optional attributes entry="..." and id="..."
            def replace_span_index(match):
                text = match.group(1)
                attrs_str = match.group(2)

                # Extract entry attribute
                entry_match = re.search(r'entry=["\']([^"\']+)["\']', attrs_str) or \
                              re.search(r'index-entry=["\']([^"\']+)["\']', attrs_str)
                entry_val = entry_match.group(1) if entry_match else text

                # Extract or generate id
                id_match = re.search(r'#([\w-]+)', attrs_str) or re.search(r'id=["\']([^"\']+)["\']', attrs_str)
                if id_match:
                    anchor_id = id_match.group(1)
                else:
                    anchor_id = self.generate_anchor_id(entry_val)

                entry_obj = IndexEntry(
                    raw_entry=entry_val,
                    anchor_id=anchor_id,
                    chapter_title=chapter_title,
                    chapter_num=chapter_num,
                    chapter_href=chapter_href,
                    section_title=current_section,
                    chapter_label=chapter_label
                )
                discovered.append(entry_obj)
                self.entries.append(entry_obj)

                return f'<span id="{anchor_id}" class="index-term" data-entry="{entry_val}">{text}</span>'

            # Regex for span indexing: [text]{.index ...}
            span_pattern = re.compile(r'\[([^\]]+)\]\{([^\}]*\.index[^\}]*)\}')
            line = span_pattern.sub(replace_span_index, line)

            # Pattern 2: {index: "term"} or {index: term} (invisible marker)
            def replace_curly_index(match):
                raw_term = match.group(1).strip()
                if (raw_term.startswith('"') and raw_term.endswith('"')) or \
                   (raw_term.startswith("'") and raw_term.endswith("'")):
                    raw_term = raw_term[1:-1].strip()

                anchor_id = self.generate_anchor_id(raw_term)
                entry_obj = IndexEntry(
                    raw_entry=raw_term,
                    anchor_id=anchor_id,
                    chapter_title=chapter_title,
                    chapter_num=chapter_num,
                    chapter_href=chapter_href,
                    section_title=current_section,
                    chapter_label=chapter_label
                )
                discovered.append(entry_obj)
                self.entries.append(entry_obj)

                return f'<span id="{anchor_id}" class="index-anchor" data-entry="{raw_term}"></span>'

            curly_pattern = re.compile(r'\{index:\s*([^{}]+)\}')
            line = curly_pattern.sub(replace_curly_index, line)

            new_lines.append(line)

        return "\n".join(new_lines), discovered

    def build_index_data(self) -> Dict[str, Dict]:
        """
        Organizes all discovered entries into a structured dictionary:
        {
          "A": {
             "Atom": { "refs": [...], "subs": {} }
          },
          "Q": {
             "Quantum Mechanics": {
                "refs": [...],
                "subs": {
                   "Entanglement": { "refs": [...] },
                   "Superposition": { "refs": [...] }
                }
             }
          }
        }
        """
        grouped = defaultdict(lambda: defaultdict(lambda: {"refs": [], "subs": defaultdict(list)}))

        for entry in self.entries:
            letter = entry.letter_group
            main = entry.main_term

            if entry.sub_terms:
                sub = " > ".join(entry.sub_terms)
                grouped[letter][main]["subs"][sub].append(entry)
            else:
                grouped[letter][main]["refs"].append(entry)

        # Sort letter groups and term names
        sorted_groups = {}
        for letter in sorted(grouped.keys()):
            terms_dict = grouped[letter]
            sorted_terms = {}
            for term in sorted(terms_dict.keys(), key=lambda s: s.lower()):
                term_data = terms_dict[term]
                # Deduplicate references per chapter/anchor
                sorted_terms[term] = {
                    "refs": term_data["refs"],
                    "subs": {s: term_data["subs"][s] for s in sorted(term_data["subs"].keys(), key=lambda x: x.lower())}
                }
            sorted_groups[letter] = sorted_terms

        return sorted_groups

    def render_markdown_index(self, for_epub: bool = True) -> str:
        """
        Renders the aggregated index into a publication-standard Markdown document.
        If for_epub is True, links are markdown links `[Ch. X](#anchor)` which
        Pandoc automatically resolves to cross-chapter files `ch00X.xhtml#anchor`.
        If False (multi-page HTML), links are `<chapter_href>#<anchor_id>`.
        """
        if not self.entries:
            return ""

        grouped = self.build_index_data()
        lines = [
            "# Index {.unnumbered .index-page}",
            "",
            '<div class="book-index-container">',
            ""
        ]

        # Jump navigation bar for letters
        jump_letters = [f"[{ltr}](#idx-letter-{ltr})" for ltr in grouped.keys()]
        lines.append(f'<div class="index-quick-nav">Jump to: {" · ".join(jump_letters)}</div>')
        lines.append("")

        for letter, terms in grouped.items():
            lines.append(f'## {letter} {{#idx-letter-{letter} .index-letter-heading}}')
            lines.append('<ul class="index-list">')

            for term, data in terms.items():
                ref_links = []
                for entry in data["refs"]:
                    loc_text = entry.chapter_label
                    if entry.section_title and entry.section_title != entry.chapter_title:
                        # Clean section title
                        clean_sec = entry.section_title.replace('"', '').replace("'", "")
                        loc_text += f" ({clean_sec})"

                    if for_epub:
                        ref_links.append(f'[{loc_text}](#{entry.anchor_id}){{.index-ref-link}}')
                    else:
                        ref_links.append(f'<a href="{entry.chapter_href}#{entry.anchor_id}" class="index-ref-link">{loc_text}</a>')

                refs_str = f' — {", ".join(ref_links)}' if ref_links else ''
                lines.append(f'  <li class="index-item"><strong class="index-term-name">{term}</strong>{refs_str}')

                # Handle sub-terms
                if data["subs"]:
                    lines.append('    <ul class="index-sublist">')
                    for sub, sub_entries in data["subs"].items():
                        sub_ref_links = []
                        for entry in sub_entries:
                            loc_text = entry.chapter_label
                            if entry.section_title and entry.section_title != entry.chapter_title:
                                clean_sec = entry.section_title.replace('"', '').replace("'", "")
                                loc_text += f" ({clean_sec})"

                            if for_epub:
                                sub_ref_links.append(f'[{loc_text}](#{entry.anchor_id}){{.index-ref-link}}')
                            else:
                                sub_ref_links.append(f'<a href="{entry.chapter_href}#{entry.anchor_id}" class="index-ref-link">{loc_text}</a>')

                        sub_refs_str = f' — {", ".join(sub_ref_links)}' if sub_ref_links else ''
                        lines.append(f'      <li class="index-subitem"><span class="index-subterm-name">{sub}</span>{sub_refs_str}</li>')
                    lines.append('    </ul>')

                lines.append('  </li>')

            lines.append('</ul>')
            lines.append("")

        lines.append('</div>')
        return "\n".join(lines)
