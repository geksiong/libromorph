"""
libromorph.config: Book project configuration and metadata loader.
Reads book.yaml / book.json and scans markdown chapter files.
"""

import os
import glob
import yaml
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ChapterInfo:
    file_path: str
    filename: str
    stem: str
    number: int
    title: str
    html_filename: str


@dataclass
class BookConfig:
    book_dir: str
    title: str = "Untitled Book"
    subtitle: str = ""
    author: str = "Unknown Author"
    language: str = "en"
    date: str = ""
    description: str = ""
    rights: str = "All rights reserved"
    publisher: str = "LibroMorph"
    cover: Optional[str] = None
    theme: str = "classic-novel"
    vertical_layout: bool = False
    toc_enabled: bool = True
    toc_depth: int = 3
    index_enabled: bool = True
    index_title: str = "Index"
    math_mode: str = "auto"
    custom_css: Optional[str] = None
    abc_renderer: str = "auto"
    mermaid_renderer: str = "auto"
    chapters: List[ChapterInfo] = field(default_factory=list)

    @classmethod
    def load(cls, book_dir: str, overrides: Optional[Dict[str, Any]] = None) -> "BookConfig":
        book_dir = os.path.abspath(book_dir)
        yaml_candidates = [
            os.path.join(book_dir, "book.yaml"),
            os.path.join(book_dir, "book.yml"),
            os.path.join(book_dir, "_book.yaml"),
            os.path.join(book_dir, "metadata.yaml"),
        ]
        data: Dict[str, Any] = {}
        for path in yaml_candidates:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    loaded = yaml.safe_load(f)
                    if isinstance(loaded, dict):
                        data = loaded
                        break

        # Apply overrides from CLI
        if overrides:
            for k, v in overrides.items():
                if v is not None:
                    data[k] = v

        title = data.get("title") or os.path.basename(book_dir).replace("-", " ").title()
        subtitle = data.get("subtitle", "")
        author = data.get("author", "Unknown Author")
        if isinstance(author, list):
            author = ", ".join(str(a) for a in author)
        language = data.get("language") or data.get("lang") or "en"
        date = str(data.get("date", ""))
        description = data.get("description", "")
        rights = data.get("rights", "All rights reserved")
        publisher = data.get("publisher", "LibroMorph")
        theme = data.get("theme", "classic-novel")
        vertical_layout = bool(data.get("vertical_layout", theme == "cjk-vertical"))

        toc_conf = data.get("toc", {})
        if isinstance(toc_conf, bool):
            toc_enabled = toc_conf
            toc_depth = 3
        else:
            toc_enabled = bool(toc_conf.get("enabled", True))
            toc_depth = int(toc_conf.get("depth", 3))

        index_conf = data.get("index", {})
        if isinstance(index_conf, bool):
            index_enabled = index_conf
            index_title = "Index"
        else:
            index_enabled = bool(index_conf.get("enabled", True))
            index_title = str(index_conf.get("title", "Index"))

        math_mode = data.get("math", "auto")

        # Discover or load cover image
        cover = data.get("cover")
        if cover:
            cover_path = os.path.join(book_dir, cover) if not os.path.isabs(cover) else cover
            cover = cover_path if os.path.exists(cover_path) else None
        if not cover:
            # Check standard cover image filenames in book directory
            for ext in [".png", ".jpg", ".jpeg", ".webp"]:
                for name in ["cover", "Cover", "cover-image"]:
                    candidate = os.path.join(book_dir, f"{name}{ext}")
                    if os.path.exists(candidate):
                        cover = candidate
                        break
                if cover:
                    break

        custom_css = data.get("custom_css")
        abc_renderer = str(data.get("abc_renderer", "auto")).lower()
        mermaid_renderer = str(data.get("mermaid_renderer", "auto")).lower()

        # Discover chapters
        explicit_chapters = data.get("chapters")
        discovered_files: List[str] = []

        if explicit_chapters and isinstance(explicit_chapters, list):
            for ch in explicit_chapters:
                p = os.path.join(book_dir, ch) if not os.path.isabs(ch) else ch
                if os.path.exists(p):
                    discovered_files.append(p)
        else:
            all_md = sorted(glob.glob(os.path.join(book_dir, "*.md")))
            # Exclude readme or generated index
            for p in all_md:
                base = os.path.basename(p).lower()
                if base in ["readme.md", "summary.md", "_index.md"]:
                    continue
                discovered_files.append(p)

        chapters: List[ChapterInfo] = []
        for idx, file_path in enumerate(discovered_files, 1):
            fname = os.path.basename(file_path)
            stem = os.path.splitext(fname)[0]
            # Extract title from first H1 in file, or fallback to clean stem
            ch_title = ""
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("# ") and not line.startswith("##"):
                            ch_title = line[2:].strip()
                            break
            except Exception:
                pass
            if not ch_title:
                ch_title = stem.replace("-", " ").replace("_", " ").title()

            html_filename = f"chapter-{idx:02d}-{stem}.html"
            chapters.append(ChapterInfo(
                file_path=file_path,
                filename=fname,
                stem=stem,
                number=idx,
                title=ch_title,
                html_filename=html_filename
            ))

        return cls(
            book_dir=book_dir,
            title=title,
            subtitle=subtitle,
            author=author,
            language=language,
            date=date,
            description=description,
            rights=rights,
            publisher=publisher,
            cover=cover,
            theme=theme,
            vertical_layout=vertical_layout,
            toc_enabled=toc_enabled,
            toc_depth=toc_depth,
            index_enabled=index_enabled,
            index_title=index_title,
            math_mode=math_mode,
            custom_css=custom_css,
            abc_renderer=abc_renderer,
            mermaid_renderer=mermaid_renderer,
            chapters=chapters
        )
