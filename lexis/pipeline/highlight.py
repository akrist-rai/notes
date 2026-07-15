"""
LEXIS — pipeline/highlight.py
Stage 3a: Claude call to extract highlighted spans from chunks.

Returns a list of HighlightResult objects keyed back to their source chunk.
Each result maps spans in the original text to importance levels and categories.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

import anthropic
from rich.console import Console

import config
from pipeline.merge import Chunk

console = Console()

ImportanceLevel = Literal["critical", "high", "medium"]
CategoryType = Literal["concept", "definition", "claim", "data", "warning", "example"]

HIGHLIGHT_SYSTEM = """You are LEXIS, an intelligent content analyst.
Your job: given a passage of text extracted from a web page, identify spans that are genuinely important for a reader to understand or learn from.

RULES:
- Only highlight spans that appear VERBATIM in the source text. Do not paraphrase.
- Prefer shorter, precise spans (1–3 sentences max) over long ones.
- Mark as "critical" only the 1–2 most essential ideas per chunk.
- Return valid JSON only. No markdown fences, no commentary.

OUTPUT FORMAT:
{
  "highlights": [
    {
      "text": "exact substring from input",
      "importance": "critical | high | medium",
      "reason": "one-sentence explanation of why this matters",
      "category": "concept | definition | claim | data | warning | example"
    }
  ]
}"""


@dataclass
class Highlight:
    text: str
    importance: ImportanceLevel
    reason: str
    category: CategoryType
    source_url: str
    page_title: str
    chunk_id: str


def highlight(chunks: list[Chunk]) -> list[Highlight]:
    """
    Run highlight extraction across all chunks.
    Batches chunks to reduce API calls (up to 3 chunks per call).
    """
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    results: list[Highlight] = []

    # Batch: group chunks in sets of 3 to reduce call count
    BATCH_SIZE = 3
    batches = [chunks[i : i + BATCH_SIZE] for i in range(0, len(chunks), BATCH_SIZE)]

    console.print(f"\n[cyan]Highlight:[/cyan] processing {len(chunks)} chunks in {len(batches)} batches…")

    for batch_idx, batch in enumerate(batches):
        combined_text = "\n\n---CHUNK SEPARATOR---\n\n".join(
            f"[CHUNK {c.id} | {c.page_title}]\n{c.text}" for c in batch
        )

        try:
            response = client.messages.create(
                model=config.LEXIS_MODEL,
                max_tokens=2000,
                system=HIGHLIGHT_SYSTEM,
                messages=[
                    {
                        "role": "user",
                        "content": f"Extract important highlights from the following text:\n\n{combined_text}",
                    }
                ],
            )

            raw = response.content[0].text.strip()
            data = json.loads(raw)

            for item in data.get("highlights", []):
                # Find which chunk this highlight belongs to (by text substring match)
                source_chunk = _find_source_chunk(item["text"], batch)
                results.append(
                    Highlight(
                        text=item["text"],
                        importance=item.get("importance", "medium"),
                        reason=item.get("reason", ""),
                        category=item.get("category", "concept"),
                        source_url=source_chunk.source_url if source_chunk else batch[0].source_url,
                        page_title=source_chunk.page_title if source_chunk else batch[0].page_title,
                        chunk_id=source_chunk.id if source_chunk else batch[0].id,
                    )
                )

            console.print(f"  [green]✓ Batch {batch_idx + 1}/{len(batches)}: {len(data.get('highlights', []))} highlights[/green]")

        except json.JSONDecodeError as exc:
            console.print(f"  [red]✗ Batch {batch_idx + 1} JSON parse error: {exc}[/red]")
        except Exception as exc:
            console.print(f"  [red]✗ Batch {batch_idx + 1} API error: {exc}[/red]")

    console.print(f"  [bold green]Total highlights: {len(results)}[/bold green]")
    return results


def _find_source_chunk(text: str, chunks: list[Chunk]) -> Chunk | None:
    """Return the chunk whose text contains the given highlight span."""
    for chunk in chunks:
        if text[:60] in chunk.text:  # Match on first 60 chars for speed
            return chunk
    return None
