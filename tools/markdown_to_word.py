"""Convert a limited Markdown document into a Word-compatible .docx file.

This converter targets the report markdown files used in this project. It
supports headings, paragraphs, bullet lists, ordered lists, tables, and inline
code spans by converting Markdown to HTML and embedding that HTML into a docx
package through altChunk.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


INLINE_CODE_RE = re.compile(r"`([^`]+)`")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
ORDERED_LIST_RE = re.compile(r"^(\d+)\.\s+(.*)$")
UNORDERED_LIST_RE = re.compile(r"^-\s+(.*)$")
TABLE_SEPARATOR_RE = re.compile(r"^\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?$")


def inline_to_html(text: str) -> str:
    """Convert inline markdown used in the reports into HTML."""

    def replace_code(match: re.Match[str]) -> str:
        return f"<code>{html.escape(match.group(1))}</code>"

    escaped = html.escape(text, quote=False)
    return INLINE_CODE_RE.sub(replace_code, escaped)


def parse_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def markdown_to_html(markdown_text: str, title: str) -> str:
    """Convert the limited markdown subset used by the reports into HTML."""
    lines = markdown_text.splitlines()
    blocks: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        heading_match = HEADING_RE.match(stripped)
        if heading_match:
            level = min(len(heading_match.group(1)), 6)
            content = inline_to_html(heading_match.group(2).strip())
            blocks.append(f"<h{level}>{content}</h{level}>")
            index += 1
            continue

        if "|" in stripped and index + 1 < len(lines):
            separator = lines[index + 1].strip()
            if TABLE_SEPARATOR_RE.match(separator):
                headers = [inline_to_html(cell) for cell in parse_table_row(stripped)]
                rows: list[list[str]] = []
                index += 2
                while index < len(lines):
                    candidate = lines[index].strip()
                    if not candidate or "|" not in candidate:
                        break
                    rows.append([inline_to_html(cell) for cell in parse_table_row(candidate)])
                    index += 1

                header_html = "".join(f"<th>{cell}</th>" for cell in headers)
                body_rows = []
                for row in rows:
                    body_rows.append(
                        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
                    )
                blocks.append(
                    "<table>"
                    f"<thead><tr>{header_html}</tr></thead>"
                    f"<tbody>{''.join(body_rows)}</tbody>"
                    "</table>"
                )
                continue

        unordered_match = UNORDERED_LIST_RE.match(stripped)
        if unordered_match:
            items = []
            while index < len(lines):
                candidate = lines[index].strip()
                match = UNORDERED_LIST_RE.match(candidate)
                if not match:
                    break
                items.append(f"<li>{inline_to_html(match.group(1).strip())}</li>")
                index += 1
            blocks.append(f"<ul>{''.join(items)}</ul>")
            continue

        ordered_match = ORDERED_LIST_RE.match(stripped)
        if ordered_match:
            items = []
            while index < len(lines):
                candidate = lines[index].strip()
                match = ORDERED_LIST_RE.match(candidate)
                if not match:
                    break
                items.append(f"<li>{inline_to_html(match.group(2).strip())}</li>")
                index += 1
            blocks.append(f"<ol>{''.join(items)}</ol>")
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate:
                break
            if HEADING_RE.match(candidate):
                break
            if UNORDERED_LIST_RE.match(candidate):
                break
            if ORDERED_LIST_RE.match(candidate):
                break
            if "|" in candidate and index + 1 < len(lines) and TABLE_SEPARATOR_RE.match(
                lines[index + 1].strip()
            ):
                break
            paragraph_lines.append(candidate)
            index += 1
        blocks.append(f"<p>{inline_to_html(' '.join(paragraph_lines))}</p>")

    styles = """
body {
  font-family: Cambria, "Times New Roman", serif;
  font-size: 12pt;
  line-height: 1.5;
  color: #111111;
  margin: 24pt 28pt;
}
h1, h2, h3, h4, h5, h6 {
  font-family: Calibri, Arial, sans-serif;
  color: #1f497d;
  margin-top: 18pt;
  margin-bottom: 8pt;
}
h1 { font-size: 20pt; }
h2 { font-size: 16pt; }
h3 { font-size: 13pt; }
p { margin: 0 0 8pt 0; text-align: justify; }
ul, ol { margin-top: 0; margin-bottom: 8pt; }
li { margin-bottom: 4pt; }
code {
  font-family: Consolas, "Courier New", monospace;
  font-size: 10.5pt;
  background: #f1f1f1;
  padding: 1pt 3pt;
}
table {
  border-collapse: collapse;
  width: 100%;
  margin: 8pt 0 12pt 0;
}
th, td {
  border: 1px solid #666666;
  padding: 6pt;
  vertical-align: top;
}
th {
  background: #e9eff7;
  font-family: Calibri, Arial, sans-serif;
}
"""

    return (
        "<!DOCTYPE html>"
        "<html>"
        "<head>"
        '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'
        f"<title>{html.escape(title)}</title>"
        f"<style>{styles}</style>"
        "</head>"
        "<body>"
        + "".join(blocks)
        + "</body></html>"
    )


def build_docx(output_path: Path, html_text: str, title: str) -> None:
    """Write a minimal .docx package that embeds HTML via altChunk."""
    timestamp = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="html" ContentType="text/html"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""

    package_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""

    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    <w:altChunk r:id="htmlChunk"/>
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
"""

    document_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="htmlChunk" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/aFChunk" Target="afchunk.html"/>
</Relationships>
"""

    core_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                   xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:dcterms="http://purl.org/dc/terms/"
                   xmlns:dcmitype="http://purl.org/dc/dcmitype/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>{escape(title)}</dc:title>
  <dc:creator>OpenAI Codex</dc:creator>
  <cp:lastModifiedBy>OpenAI Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:modified>
</cp:coreProperties>
"""

    app_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
            xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Office Word</Application>
</Properties>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", package_rels)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/_rels/document.xml.rels", document_rels)
        archive.writestr("word/afchunk.html", html_text)
        archive.writestr("docProps/core.xml", core_xml)
        archive.writestr("docProps/app.xml", app_xml)


def convert_file(input_path: Path, output_path: Path) -> None:
    markdown_text = input_path.read_text(encoding="utf-8")
    title = input_path.stem
    html_text = markdown_to_html(markdown_text, title=title)
    build_docx(output_path, html_text=html_text, title=title)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="input markdown file")
    parser.add_argument("output", type=Path, help="output .docx file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    convert_file(args.input.resolve(), args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
