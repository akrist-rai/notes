"""
LEXIS — renderer/render.py
Final stage: inject all pipeline output into the HTML template
and write a self-contained .html output file.
"""
from __future__ import annotations

import json
import re
import html as html_mod
from datetime import datetime
from pathlib import Path

from pipeline.extract import ExtractedPage
from pipeline.highlight import Highlight
from pipeline.graph import ConceptGraph
from pipeline.synthesize import Dossier

TEMPLATE_PATH = Path(__file__).parent / "template.html"
CSS_PATH      = Path(__file__).parent / "style.css"
JS_PATH       = Path(__file__).parent / "main.js"


def _annotate_text(text: str, highlights: list[Highlight]) -> str:
    sorted_hl = sorted(highlights, key=lambda h: len(h.text), reverse=True)
    placeholder_map: dict[str, tuple[str, Highlight]] = {}
    result = text

    for hl in sorted_hl:
        pattern = re.compile(re.escape(hl.text[:80]), re.IGNORECASE)
        match = pattern.search(result)
        if match:
            actual = result[match.start():match.start() + len(hl.text)]
            ph = f"__LEXIS_HL_{len(placeholder_map)}__"
            placeholder_map[ph] = (actual, hl)
            result = result[:match.start()] + ph + result[match.start() + len(hl.text):]

    result = html_mod.escape(result)

    for ph, (actual, hl) in placeholder_map.items():
        mark = (
            f'<mark class="hl hl-{hl.importance}" '
            f'data-reason="{html_mod.escape(hl.reason)}" '
            f'data-importance="{hl.importance}" '
            f'data-category="{hl.category}">'
            f'{html_mod.escape(actual)}</mark>'
        )
        result = result.replace(ph, mark)

    return result


def _build_section1_html(pages: list[ExtractedPage], highlights: list[Highlight]) -> str:
    parts = []
    for page in pages:
        page_hl = [h for h in highlights if h.source_url == page.url]
        annotated = _annotate_text(page.markdown, page_hl)
        annotated = re.sub(r"^# (.+)$",    r"<h2>\1</h2>", annotated, flags=re.MULTILINE)
        annotated = re.sub(r"^## (.+)$",   r"<h3>\1</h3>", annotated, flags=re.MULTILINE)
        annotated = re.sub(r"^### (.+)$",  r"<h4>\1</h4>", annotated, flags=re.MULTILINE)
        annotated = re.sub(r"\n\n+", "</p><p>", annotated)
        annotated = f"<p>{annotated}</p>"
        parts.append(f"""
        <div class="src-block" data-url="{page.url}">
          <div class="src-header">
            <span class="src-dot"></span>
            <div>
              <div class="src-title">{page.title}</div>
              <a class="src-url" href="{page.url}" target="_blank" rel="noopener">{page.url}</a>
            </div>
          </div>
          <div class="src-body">{annotated}</div>
        </div>""")
    return "\n".join(parts)


def render(
    pages: list[ExtractedPage],
    highlights: list[Highlight],
    graph: ConceptGraph,
    dossier: Dossier,
    output_path: Path,
) -> None:
    template    = TEMPLATE_PATH.read_text(encoding="utf-8")
    inline_css  = CSS_PATH.read_text(encoding="utf-8") if CSS_PATH.exists() else ""
    inline_js_r = JS_PATH.read_text(encoding="utf-8") if JS_PATH.exists() else ""

    graph_data   = json.dumps(graph.to_dict(), ensure_ascii=False)
    dossier_data = json.dumps(dossier.to_dict(), ensure_ascii=False)
    sources_data = json.dumps(
        [{"url": p.url, "title": p.title, "description": p.description} for p in pages],
        ensure_ascii=False,
    )
    section1_html = _build_section1_html(pages, highlights)
    stats = {
        "pages":        len(pages),
        "highlights":   len(highlights),
        "concepts":     len(graph.nodes),
        "relations":    len(graph.edges),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    inline_js = inline_js_r
    inline_js = inline_js.replace("__GRAPH_DATA__",   graph_data)
    inline_js = inline_js.replace("__DOSSIER_DATA__", dossier_data)
    inline_js = inline_js.replace("__STATS_JSON__",   json.dumps(stats))
    inline_js = inline_js.replace("__SOURCES_DATA__", sources_data)

    result = template
    result = result.replace("{{INLINE_CSS}}",    inline_css)
    result = result.replace("{{INLINE_JS}}",     inline_js)
    result = result.replace("{{SECTION1_HTML}}", section1_html)
    result = result.replace("{{SUBJECT}}",       dossier.subject.upper())
    result = result.replace("{{THREAT_LEVEL}}",  dossier.threat_level)
    result = result.replace("{{PAGE_COUNT}}",    str(len(pages)))
    result = result.replace("{{GENERATED_AT}}",  stats["generated_at"])

    output_path.write_text(result, encoding="utf-8")
    print(f"\n✅ Output written to: {output_path}")
    print(f"   Open in browser: file://{output_path.resolve()}")
