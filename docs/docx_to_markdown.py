#!/usr/bin/env python3
"""
Convert a .docx document into a Markdown file.

Requires:
    pip install python-docx

Usage:
    python3 docs/docx_to_markdown.py input.docx
    python3 docs/docx_to_markdown.py input.docx -o output.md
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.document import Document as DocumentType
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph


def iter_block_items(parent: DocumentType | _Cell):
    if isinstance(parent, DocumentType):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise TypeError(f"Unsupported parent type: {type(parent)!r}")

    for child in parent_elm.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, parent)
        elif child.tag.endswith("}tbl"):
            yield Table(child, parent)


def markdown_escape(text: str) -> str:
    text = text.replace("\\", "\\\\")
    for char in ("*", "_", "[", "]", "#", "`", "|"):
        text = text.replace(char, f"\\{char}")
    return text


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def style_name(paragraph: Paragraph) -> str:
    return (paragraph.style.name if paragraph.style else "").strip()


def get_heading_level(paragraph: Paragraph) -> int | None:
    match = re.match(r"Heading\s+(\d+)$", style_name(paragraph), re.IGNORECASE)
    if not match:
        return None
    return max(1, min(6, int(match.group(1))))


def is_list_paragraph(paragraph: Paragraph) -> bool:
    name = style_name(paragraph).lower()
    return "list" in name or paragraph._p.pPr is not None and paragraph._p.pPr.numPr is not None


def list_indent_level(paragraph: Paragraph) -> int:
    ppr = paragraph._p.pPr
    if ppr is not None and ppr.ind is not None and ppr.ind.left is not None:
        return max(0, int(ppr.ind.left) // 360)
    return 0


def inline_markdown(paragraph: Paragraph) -> str:
    parts: list[str] = []

    for run in paragraph.runs:
        text = run.text
        if not text:
            continue

        text = markdown_escape(text)
        if run.bold:
            text = f"**{text}**"
        if run.italic:
            text = f"*{text}*"
        if run.font.strike:
            text = f"~~{text}~~"

        parts.append(text)

    text = "".join(parts).strip()
    return normalize_whitespace(text)


def plain_text(paragraph: Paragraph) -> str:
    return normalize_whitespace(paragraph.text)


def convert_table(table: Table) -> list[str]:
    rows = []
    for row in table.rows:
        values = []
        for cell in row.cells:
            text = normalize_whitespace(cell.text).replace("|", "\\|")
            values.append(text)
        rows.append(values)

    if not rows:
        return []
    if len(rows) == 1 and len(rows[0]) == 1:
        return [rows[0][0], ""]

    width = max(len(row) for row in rows)
    padded = [row + [""] * (width - len(row)) for row in rows]
    header = padded[0]
    separator = ["---"] * width

    lines = [
        f"| {' | '.join(header)} |",
        f"| {' | '.join(separator)} |",
    ]
    for row in padded[1:]:
        lines.append(f"| {' | '.join(row)} |")
    lines.append("")
    return lines


def convert_paragraph(paragraph: Paragraph) -> list[str]:
    text = inline_markdown(paragraph)
    if not text:
        return [""]

    heading_level = get_heading_level(paragraph)
    if heading_level is not None:
        return [f"{'#' * heading_level} {text}", ""]

    if style_name(paragraph).lower() == "title":
        return [f"# {text}", ""]

    if is_list_paragraph(paragraph):
        indent = "  " * list_indent_level(paragraph)
        return [f"{indent}- {text}"]

    return [text, ""]


def split_blocks(document: Document) -> tuple[list[Paragraph], list[Paragraph | Table]]:
    front_matter: list[Paragraph] = []
    rest: list[Paragraph | Table] = []
    in_front_matter = True

    for block in iter_block_items(document):
        if in_front_matter and isinstance(block, Paragraph):
            if get_heading_level(block) is None:
                front_matter.append(block)
                continue
            in_front_matter = False

        if in_front_matter:
            in_front_matter = False
        rest.append(block)

    return front_matter, rest


def convert_front_matter(paragraphs: list[Paragraph]) -> list[str]:
    entries = [p for p in paragraphs if plain_text(p)]
    if not entries:
        return []

    lines: list[str] = []
    if len(entries) >= 1:
        lines.extend([f"# {plain_text(entries[0])}", ""])
    if len(entries) >= 2:
        lines.extend([f"## {plain_text(entries[1])}", ""])
    if len(entries) >= 3:
        lines.extend([f"*{plain_text(entries[2])}*", ""])

    for paragraph in entries[3:]:
        lines.extend([inline_markdown(paragraph), ""])

    return lines


def convert_document(document: Document) -> str:
    lines: list[str] = []
    front_matter, blocks = split_blocks(document)
    lines.extend(convert_front_matter(front_matter))

    for block in blocks:
        if isinstance(block, Paragraph):
            lines.extend(convert_paragraph(block))
        elif isinstance(block, Table):
            if lines and lines[-1] != "":
                lines.append("")
            lines.extend(convert_table(block))

    while lines and lines[-1] == "":
        lines.pop()

    output = "\n".join(lines)
    output = re.sub(r"\n{3,}", "\n\n", output)
    return output + "\n"


def build_output_path(input_path: Path, output_path: Path | None) -> Path:
    if output_path is not None:
        return output_path
    return input_path.with_suffix(".md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a DOCX document to Markdown.")
    parser.add_argument("input", type=Path, help="Path to the input .docx file")
    parser.add_argument("-o", "--output", type=Path, help="Path to the output .md file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input.resolve()
    output_path = build_output_path(input_path, args.output).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if input_path.suffix.lower() != ".docx":
        raise ValueError("Input file must have a .docx extension")

    document = Document(str(input_path))
    markdown = convert_document(document)
    output_path.write_text(markdown, encoding="utf-8")

    print(f"Wrote Markdown to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
