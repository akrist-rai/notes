"""
LEXIS — renderer/render.py
Final stage: inject all pipeline output into the HTML template
and write a self-contained .html output file.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

from pipeline.extract import ExtractedPage
from pipeline.highlight import Highlight
from pipeline.graph import ConceptGraph
from pipeline.synthesize import Dossier

TEMPLATE_PATH = Path(__file__).parent / "template.html"


def _annotate_text(text: str, highlights: list[Highlight]) -> str:
    """
    Inject <mark> spans into the source text for Section 1.
    Handles overlapping spans by processing longest first.
    Returns HTML-safe annotated string.
    """
    # Sort highlights by text length descending to handle overlaps
    sorted_hl = sorted(highlights, key=lambda h: len(h.text), reverse=True)

    # We'll use a placeholder approach to avoid double-replacement
    placeholder_map: dict[str, tuple[str, Highlight]] = {}
    result = text

    for hl in sorted_hl:
        escaped_search = re.escape(hl.text[:120])  # Match on first 120 chars
        pattern = re.compile(escaped_search[:80], re.IGNORECASE)
        match = pattern.search(result)
        if match:
            actual_text = result[match.start():match.start() + len(hl.text)]
            placeholder = f"__LEXIS_HL_{len(placeholder_map)}__"
            placeholder_map[placeholder] = (actual_text, hl)
            result = result[:match.start()] + placeholder + result[match.start() + len(hl.text):]

    # HTML-escape the non-highlighted text
    import html
    result = html.escape(result)

    # Replace placeholders with actual mark spans
    for placeholder, (actual_text, hl) in placeholder_map.items():
        escaped_placeholder = re.escape(placeholder)
        mark = (
            f'<mark class="hl hl-{hl.importance} hl-{hl.category}" '
            f'data-reason="{html.escape(hl.reason)}" '
            f'data-importance="{hl.importance}" '
            f'data-category="{hl.category}">'
            f'{html.escape(actual_text)}</mark>'
        )
        result = result.replace(placeholder, mark)

    return result


def _build_section1_html(pages: list[ExtractedPage], highlights: list[Highlight]) -> str:
    """Build the annotated source reader HTML for Section 1."""
    parts = []
    for page in pages:
        page_highlights = [h for h in highlights if h.source_url == page.url]
        annotated = _annotate_text(page.markdown, page_highlights)
        # Convert markdown-style headers to HTML (basic)
        annotated = re.sub(r"^#{1} (.+)$", r"<h2>\1</h2>", annotated, flags=re.MULTILINE)
        annotated = re.sub(r"^#{2} (.+)$", r"<h3>\1</h3>", annotated, flags=re.MULTILINE)
        annotated = re.sub(r"^#{3,} (.+)$", r"<h4>\1</h4>", annotated, flags=re.MULTILINE)
        # Convert double newlines to paragraphs
        annotated = re.sub(r"\n\n+", "</p><p>", annotated)
        annotated = f"<p>{annotated}</p>"

        parts.append(f"""
        <div class="source-page" data-url="{page.url}">
          <div class="source-header">
            <span class="source-icon">⬡</span>
            <div>
              <div class="source-title">{page.title}</div>
              <a class="source-url" href="{page.url}" target="_blank">{page.url}</a>
            </div>
          </div>
          <div class="source-body">{annotated}</div>
        </div>""")

    return "\n".join(parts)


def render(
    pages: list[ExtractedPage],
    highlights: list[Highlight],
    graph: ConceptGraph,
    dossier: Dossier,
    output_path: Path,
) -> None:
    """
    Render the complete LEXIS output page and write to output_path.
    """
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Build data payloads
    graph_data = json.dumps(graph.to_dict(), ensure_ascii=False)
    dossier_data = json.dumps(dossier.to_dict(), ensure_ascii=False)

    highlight_data = json.dumps(
        [
            {
                "text": h.text[:80] + "…" if len(h.text) > 80 else h.text,
                "importance": h.importance,
                "category": h.category,
                "reason": h.reason,
                "source_url": h.source_url,
                "page_title": h.page_title,
            }
            for h in highlights
        ],
        ensure_ascii=False,
    )

    sources_data = json.dumps(
        [{"url": p.url, "title": p.title, "description": p.description} for p in pages],
        ensure_ascii=False,
    )

    section1_html = _build_section1_html(pages, highlights)

    # Stats
    stats = {
        "pages": len(pages),
        "highlights": len(highlights),
        "concepts": len(graph.nodes),
        "relations": len(graph.edges),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    # Inject into template
    result = template
    result = result.replace("{{SECTION1_HTML}}", section1_html)
    result = result.replace("{{GRAPH_DATA}}", graph_data)
    result = result.replace("{{DOSSIER_DATA}}", dossier_data)
    result = result.replace("{{HIGHLIGHTS_DATA}}", highlight_data)
    result = result.replace("{{SOURCES_DATA}}", sources_data)
    result = result.replace("{{STATS_JSON}}", json.dumps(stats))
    result = result.replace("{{SUBJECT}}", dossier.subject.upper())
    result = result.replace("{{THREAT_LEVEL}}", dossier.threat_level)
    result = result.replace("{{PAGE_COUNT}}", str(len(pages)))
    result = result.replace("{{GENERATED_AT}}", stats["generated_at"])

    output_path.write_text(result, encoding="utf-8")
    print(f"\n✅ Output written to: {output_path}")
    print(f"   Open in browser: file://{output_path.resolve()}")
