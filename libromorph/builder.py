"""
libromorph.builder: Orchestrates Pandoc compilation for EPUB and HTML website targets.
Handles asset bundling, index generation, metadata injection, and theme templating.
"""

import os
import shutil
import subprocess
import tempfile
from typing import Dict, Any, Optional, List
from jinja2 import Environment, FileSystemLoader

from .config import BookConfig, ChapterInfo
from .indexer import BookIndexer
from .cover import generate_cover_image


PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
FILTERS_DIR = os.path.join(PACKAGE_DIR, "filters")
TEMPLATES_DIR = os.path.join(PACKAGE_DIR, "templates")
THEMES_DIR = os.path.join(PACKAGE_DIR, "themes")


class BuildError(Exception):
    pass


class BookBuilder:
    def __init__(self, config: BookConfig, output_dir: Optional[str] = None):
        self.config = config
        self.output_dir = os.path.abspath(output_dir or os.path.join(config.book_dir, "dist"))
        self.indexer = BookIndexer()
        self.jinja_env = Environment(
            loader=FileSystemLoader(os.path.join(TEMPLATES_DIR, "html")),
            autoescape=False
        )

    def _resolve_theme_css(self) -> str:
        """Locates the CSS stylesheet for the configured genre theme or custom path."""
        if self.config.custom_css and os.path.exists(self.config.custom_css):
            return os.path.abspath(self.config.custom_css)
        
        theme_path = os.path.join(THEMES_DIR, self.config.theme, "style.css")
        if os.path.exists(theme_path):
            return theme_path

        # Fallback to classic-novel if theme name not recognized
        fallback = os.path.join(THEMES_DIR, "classic-novel", "style.css")
        if os.path.exists(fallback):
            return fallback
        
        raise BuildError(f"Cannot resolve CSS for theme '{self.config.theme}'")

    def _ensure_cover(self) -> str:
        """Ensures a valid cover image exists, auto-generating one if missing."""
        if self.config.cover and os.path.exists(self.config.cover):
            return self.config.cover

        cover_path = os.path.join(self.config.book_dir, "cover.png")
        if not os.path.exists(cover_path):
            print(f"[LibroMorph] Generating custom typographic cover for '{self.config.title}'...")
            generate_cover_image(
                output_path=cover_path,
                title=self.config.title,
                subtitle=self.config.subtitle,
                author=self.config.author,
                theme=self.config.theme
            )
        self.config.cover = cover_path
        return cover_path

    def build(self, target_format: str = "all") -> Dict[str, str]:
        """
        Builds the book.
        target_format: 'epub', 'html', or 'all'.
        Returns a dict of output file/folder paths.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        results = {}

        if not self.config.chapters:
            raise BuildError(f"No markdown chapters found in '{self.config.book_dir}'.")

        # 1. Ensure cover image
        cover_image = self._ensure_cover()

        # 2. Preprocess chapters & collect index terms
        processed_chapters = []
        for ch in self.config.chapters:
            with open(ch.file_path, "r", encoding="utf-8") as f:
                content = f.read()

            transformed_md, _ = self.indexer.process_chapter_markdown(
                markdown=content,
                chapter_num=ch.number,
                chapter_title=ch.title,
                chapter_href=ch.html_filename
            )
            processed_chapters.append((ch, transformed_md))

        # 3. Build EPUB
        if target_format in ["all", "epub"]:
            epub_path = self._build_epub(processed_chapters, cover_image)
            results["epub"] = epub_path

        # 4. Build HTML Website
        if target_format in ["all", "html"]:
            html_dir = self._build_html_website(processed_chapters, cover_image)
            results["html"] = html_dir

        return results

    def _build_epub(self, processed_chapters: List[tuple], cover_image: str) -> str:
        """Compiles standard EPUB 3 document with Pandoc."""
        epub_filename = f"{self.config.title.lower().replace(' ', '-')}.epub"
        # Sanitize filename
        epub_filename = "".join(c for c in epub_filename if c.isalnum() or c in "-._")
        epub_out = os.path.join(self.output_dir, epub_filename)

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_files = []

            # Write preprocessed chapters
            for idx, (ch, transformed_md) in enumerate(processed_chapters):
                tmp_ch_path = os.path.join(tmpdir, f"ch_{idx:03d}_{ch.stem}.md")
                with open(tmp_ch_path, "w", encoding="utf-8") as f:
                    f.write(transformed_md)
                temp_files.append(tmp_ch_path)

            # If index is enabled, generate index markdown for EPUB (internal links)
            if self.config.index_enabled and self.indexer.entries:
                index_md = self.indexer.render_markdown_index(for_epub=True)
                if index_md:
                    tmp_idx_path = os.path.join(tmpdir, "ch_999_index.md")
                    with open(tmp_idx_path, "w", encoding="utf-8") as f:
                        f.write(index_md)
                    temp_files.append(tmp_idx_path)

            # Combine base CSS + theme CSS into a single epub stylesheet
            theme_css_path = self._resolve_theme_css()
            base_css_path = os.path.join(TEMPLATES_DIR, "html", "book_assets", "css", "base.css")
            combined_css = os.path.join(tmpdir, "epub_style.css")

            with open(combined_css, "w", encoding="utf-8") as out_css:
                if os.path.exists(base_css_path):
                    with open(base_css_path, "r", encoding="utf-8") as f:
                        out_css.write(f.read() + "\n")
                with open(theme_css_path, "r", encoding="utf-8") as f:
                    out_css.write(f.read() + "\n")

            # Prepare pandoc command
            lua_filter = os.path.join(FILTERS_DIR, "libro_filter.lua")
            cmd = [
                "pandoc",
                *temp_files,
                "-o", epub_out,
                "-t", "epub3",
                f"--css={combined_css}",
                f"--lua-filter={lua_filter}",
                f"--epub-cover-image={cover_image}",
                "--mathml",
                f"--metadata=title:{self.config.title}",
                f"--metadata=author:{self.config.author}",
                f"--metadata=lang:{self.config.language}",
            ]

            if self.config.date:
                cmd.append(f"--metadata=date:{self.config.date}")
            if self.config.rights:
                cmd.append(f"--metadata=rights:{self.config.rights}")
            if self.config.description:
                cmd.append(f"--metadata=description:{self.config.description}")

            if self.config.toc_enabled:
                cmd.extend(["--toc", f"--toc-depth={self.config.toc_depth}"])

            if self.config.vertical_layout:
                cmd.append("-Mpage-progression-direction=rtl")

            print(f"[LibroMorph] Compiling EPUB: {os.path.basename(epub_out)}...")
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                raise BuildError(f"Pandoc EPUB generation failed:\n{res.stderr}")

        return epub_out

    def _build_html_website(self, processed_chapters: List[tuple], cover_image: str) -> str:
        """Builds static responsive HTML web reader."""
        html_out_dir = os.path.join(self.output_dir, "html")
        os.makedirs(html_out_dir, exist_ok=True)

        assets_dir = os.path.join(html_out_dir, "assets")
        css_dest = os.path.join(assets_dir, "css")
        js_dest = os.path.join(assets_dir, "js")
        os.makedirs(css_dest, exist_ok=True)
        os.makedirs(js_dest, exist_ok=True)

        # Copy assets
        src_assets = os.path.join(TEMPLATES_DIR, "html", "book_assets")
        shutil.copy2(os.path.join(src_assets, "css", "base.css"), os.path.join(css_dest, "base.css"))
        shutil.copy2(os.path.join(src_assets, "css", "reader.css"), os.path.join(css_dest, "reader.css"))
        shutil.copy2(self._resolve_theme_css(), os.path.join(css_dest, "theme.css"))

        for js_file in ["quiz.js", "reader.js", "search.js"]:
            src_js = os.path.join(src_assets, "js", js_file)
            if os.path.exists(src_js):
                shutil.copy2(src_js, os.path.join(js_dest, js_file))

        # Copy book cover image
        cover_filename = ""
        if cover_image and os.path.exists(cover_image):
            cover_ext = os.path.splitext(cover_image)[1]
            cover_filename = f"cover{cover_ext}"
            shutil.copy2(cover_image, os.path.join(html_out_dir, cover_filename))

        # Copy any images directory from the book project
        book_images_dir = os.path.join(self.config.book_dir, "images")
        if os.path.exists(book_images_dir):
            dest_images = os.path.join(html_out_dir, "images")
            if os.path.exists(dest_images):
                shutil.rmtree(dest_images)
            shutil.copytree(book_images_dir, dest_images)

        lua_filter = os.path.join(FILTERS_DIR, "libro_filter.lua")
        chapter_template = self.jinja_env.get_template("chapter.html.j2")
        index_landing_template = self.jinja_env.get_template("index.html.j2")

        has_index = self.config.index_enabled and bool(self.indexer.entries)

        # Render each chapter
        total_chapters = len(processed_chapters)
        for i, (ch, transformed_md) in enumerate(processed_chapters):
            # Run pandoc to convert markdown to HTML fragment
            cmd = [
                "pandoc",
                "-f", "markdown",
                "-t", "html",
                f"--lua-filter={lua_filter}",
                "--mathjax",
            ]
            res = subprocess.run(cmd, input=transformed_md, capture_output=True, text=True)
            if res.returncode != 0:
                raise BuildError(f"Pandoc HTML chapter render failed for {ch.filename}:\n{res.stderr}")

            body_html = res.stdout
            prev_ch = processed_chapters[i - 1][0] if i > 0 else None
            next_ch = processed_chapters[i + 1][0] if i < total_chapters - 1 else None

            rendered_page = chapter_template.render(
                config=self.config,
                chapters=self.config.chapters,
                current_chapter=ch,
                prev_chapter=prev_ch,
                next_chapter=next_ch,
                content=body_html,
                has_index=has_index
            )

            with open(os.path.join(html_out_dir, ch.html_filename), "w", encoding="utf-8") as f:
                f.write(rendered_page)

        # Render Alphabetical Index page if index is enabled
        if has_index:
            index_md = self.indexer.render_markdown_index(for_epub=False)
            cmd = [
                "pandoc",
                "-f", "markdown",
                "-t", "html",
                f"--lua-filter={lua_filter}",
                "--mathjax",
            ]
            res = subprocess.run(cmd, input=index_md, capture_output=True, text=True)
            index_html_body = res.stdout if res.returncode == 0 else "<p>Index generation failed.</p>"

            idx_pseudo_ch = ChapterInfo(
                file_path="",
                filename="book-index.html",
                stem="book-index",
                number=total_chapters + 1,
                title="Alphabetical Index",
                html_filename="book-index.html"
            )
            last_ch = processed_chapters[-1][0] if processed_chapters else None
            rendered_idx = chapter_template.render(
                config=self.config,
                chapters=self.config.chapters,
                current_chapter=idx_pseudo_ch,
                prev_chapter=last_ch,
                next_chapter=None,
                content=index_html_body,
                has_index=has_index
            )
            with open(os.path.join(html_out_dir, "book-index.html"), "w", encoding="utf-8") as f:
                f.write(rendered_idx)

        # Render landing / book cover overview page
        rendered_index = index_landing_template.render(
            config=self.config,
            chapters=self.config.chapters,
            cover_filename=cover_filename,
            has_index=has_index
        )
        with open(os.path.join(html_out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(rendered_index)

        print(f"[LibroMorph] Generated HTML Website at: {html_out_dir}")
        return html_out_dir
