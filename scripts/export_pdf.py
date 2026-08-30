#!/usr/bin/env python3
"""Export Markdown files to PDF without flattening headings/tables."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from markdown_pdf import MarkdownPdf, Section

# PyMuPDF cannot resolve GFM anchors with accents (e.g. #1-présentation).
# PDF bookmarks still come from headings via toc_level.
INTERNAL_LINK = re.compile(r"\[([^\]]+)\]\(#[^)]+\)")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSS = ROOT / "docs" / "pdf-style.css"
DEFAULT_OUT_DIR = ROOT / "docs" / "pdf"


def first_heading(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Document"


def export_one(src: Path, dest: Path, css: str) -> None:
    markdown = INTERNAL_LINK.sub(r"\1", src.read_text(encoding="utf-8"))
    dest.parent.mkdir(parents=True, exist_ok=True)

    pdf = MarkdownPdf(toc_level=2)
    pdf.meta["title"] = first_heading(markdown)
    pdf.meta["author"] = "1oo9"
    pdf.meta["producer"] = "nh-cdc-proj / markdown-pdf"
    pdf.add_section(
        Section(markdown, paper_size="A4", toc=True),
        user_css=css,
    )
    pdf.save(str(dest))


def iter_sources(paths: list[str]) -> list[Path]:
    if paths:
        return [Path(p).resolve() for p in paths]
    return sorted(p for p in (ROOT / "docs").glob("*.md") if p.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description="Export .md files to PDF.")
    parser.add_argument("paths", nargs="*", help="Markdown files (default: docs/*.md)")
    parser.add_argument(
        "-o",
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help="Output directory (default: docs/pdf)",
    )
    parser.add_argument(
        "--css",
        default=str(DEFAULT_CSS),
        help="CSS file used for print layout",
    )
    args = parser.parse_args()

    css_path = Path(args.css)
    if not css_path.is_file():
        print(f"CSS not found: {css_path}", file=sys.stderr)
        return 1
    css = css_path.read_text(encoding="utf-8")

    sources = iter_sources(args.paths)
    if not sources:
        print("No markdown files to export.", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir)
    for src in sources:
        if not src.is_file():
            print(f"Skip (missing): {src}", file=sys.stderr)
            return 1
        dest = out_dir / (src.stem + ".pdf")
        export_one(src, dest, css)
        print(f"{src} -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
