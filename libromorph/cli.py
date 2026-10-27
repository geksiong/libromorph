"""
libromorph.cli: Command-line interface for the LibroMorph publishing toolkit.
"""

import argparse
import sys
import os
import shutil

from .config import BookConfig
from .builder import BookBuilder, BuildError
from .server import run_preview_server
from .abc_render import RENDERER_CHOICES as ABC_RENDERER_CHOICES
from .mermaid_render import RENDERER_CHOICES as MERMAID_RENDERER_CHOICES


THEMES = {
    "classic-novel": "Literary Fiction, Elegant Serif, First-line Indents, Dropcaps, Fleurons",
    "technical": "Computer Science, Math, Admonition Boxes, Code Highlighting, Ragged-right",
    "cjk-vertical": "Japanese Light Novels, Chinese Classics, Vertical-RL, Tate-chu-yoko, Ruby Furigana",
    "modern-minimal": "Nordic / Swiss Minimalist Non-Fiction, Generous Spacing, Clean Typography",
    "fantasy-vintage": "Antique Grimoires, Illuminated Dropcaps, Parchment Tones, Ornate Dividers",
}


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="libromorph",
        description="Transform folders of Markdown files into beautiful EPUBs and HTML websites using Pandoc."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: build
    build_parser = subparsers.add_parser("build", help="Build an EPUB and/or HTML website from a markdown folder.")
    build_parser.add_argument("book_dir", nargs="?", default=".", help="Path to markdown book folder (default: current directory)")
    build_parser.add_argument("-o", "--output-dir", help="Output directory (default: <book_dir>/dist)")
    build_parser.add_argument("-f", "--format", choices=["all", "epub", "html"], default="all", help="Output format (default: all)")
    build_parser.add_argument("-t", "--theme", choices=list(THEMES.keys()), help="Genre style theme")
    build_parser.add_argument("--vertical", action="store_true", help="Enable vertical writing mode (vertical-rl) for CJK text")
    build_parser.add_argument("--horizontal", action="store_true", help="Force horizontal writing mode")
    build_parser.add_argument("--cover", help="Path to custom cover image file")
    build_parser.add_argument("--title", help="Override book title")
    build_parser.add_argument("--author", help="Override author name")
    build_parser.add_argument("--lang", help="Override book language code (e.g. en, ja, zh)")
    build_parser.add_argument("--no-toc", action="store_true", help="Disable Table of Contents")
    build_parser.add_argument("--no-index", action="store_true", help="Disable automatic alphabetical Index generation")
    build_parser.add_argument("--abc-renderer", choices=ABC_RENDERER_CHOICES,
                              help="Engine for rendering ABC music scores to SVG in EPUB (default: auto)")
    build_parser.add_argument("--mermaid-renderer", choices=MERMAID_RENDERER_CHOICES,
                              help="Engine for rendering Mermaid diagrams to SVG in EPUB (default: auto)")

    # Command: init
    init_parser = subparsers.add_parser("init", help="Initialize a new book project or scaffold a demo book.")
    init_parser.add_argument("directory", nargs="?", default="my-book", help="Destination folder name")
    init_parser.add_argument("--demo", action="store_true", default=True, help="Scaffold a complete demo book with all features")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Preview the generated HTML book website in your browser.")
    serve_parser.add_argument("path", nargs="?", default="dist/html", help="Path to HTML output folder or book folder (default: dist/html)")
    serve_parser.add_argument("-p", "--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    serve_parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")

    # Command: list-themes
    subparsers.add_parser("list-themes", help="List available built-in genre themes.")

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "list-themes":
        print("\nAvailable Built-in Genre Themes:")
        print("=" * 65)
        for name, desc in THEMES.items():
            print(f"  • {name:<18} : {desc}")
        print("=" * 65)
        print("Usage: libromorph build . --theme <theme-name>\n")
        return

    if args.command == "init":
        target_dir = os.path.abspath(args.directory)
        package_demo = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo-book")
        if not os.path.exists(package_demo):
            # check sibling directory
            package_demo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "demo-book")
            package_demo = os.path.abspath(package_demo)

        if os.path.exists(target_dir) and os.listdir(target_dir):
            print(f"Error: Target directory '{target_dir}' already exists and is not empty.")
            sys.exit(1)

        print(f"[LibroMorph] Scaffolding demo book into '{target_dir}'...")
        if os.path.exists(package_demo):
            shutil.copytree(package_demo, target_dir, dirs_exist_ok=True)
            print("✓ Scaffolded complete multi-feature demo book!")
            print(f"\nNext steps:\n  cd {args.directory}\n  libromorph build\n  libromorph serve\n")
        else:
            print("Demo book assets not found in package. Creating minimal template...")
            os.makedirs(target_dir, exist_ok=True)
        return

    if args.command == "serve":
        serve_path = os.path.abspath(args.path)
        if os.path.isdir(serve_path):
            # check if user passed book dir instead of dist/html
            dist_html = os.path.join(serve_path, "dist", "html")
            if os.path.exists(dist_html):
                serve_path = dist_html
            elif os.path.exists(os.path.join(serve_path, "index.html")):
                pass
        run_preview_server(serve_path, port=args.port, open_browser=not args.no_browser)
        return

    if args.command == "build":
        book_dir = os.path.abspath(args.book_dir)
        if not os.path.isdir(book_dir):
            print(f"Error: '{book_dir}' is not a directory.")
            sys.exit(1)

        # Build overrides from CLI flags
        overrides = {}
        if args.theme:
            overrides["theme"] = args.theme
        if args.vertical:
            overrides["vertical_layout"] = True
        elif args.horizontal:
            overrides["vertical_layout"] = False
        if args.cover:
            overrides["cover"] = args.cover
        if args.title:
            overrides["title"] = args.title
        if args.author:
            overrides["author"] = args.author
        if args.lang:
            overrides["language"] = args.lang
        if args.no_toc:
            overrides["toc_enabled"] = False
        if args.no_index:
            overrides["index_enabled"] = False
        if args.abc_renderer:
            overrides["abc_renderer"] = args.abc_renderer
        if args.mermaid_renderer:
            overrides["mermaid_renderer"] = args.mermaid_renderer

        try:
            config = BookConfig.load(book_dir, overrides=overrides)
            builder = BookBuilder(config=config, output_dir=args.output_dir)
            print(f"\n========================================================")
            print(f"  LibroMorph Publishing Tool")
            print(f"  Book Title : {config.title}")
            print(f"  Author     : {config.author}")
            print(f"  Genre Theme: {config.theme}")
            print(f"  Vertical   : {'Yes (vertical-rl)' if config.vertical_layout else 'No (horizontal)'}")
            print(f"  Chapters   : {len(config.chapters)} chapters detected")
            print(f"========================================================\n")

            results = builder.build(target_format=args.format)

            print(f"\n✓ Build completed successfully!")
            if "epub" in results:
                print(f"  • EPUB Document : {results['epub']}")
            if "html" in results:
                print(f"  • HTML Website  : {results['html']}")
                print(f"\nTo preview in your browser:\n  libromorph serve {results['html']}\n")
        except BuildError as e:
            print(f"\n[LibroMorph Error] {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"\n[Unexpected Error] {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
