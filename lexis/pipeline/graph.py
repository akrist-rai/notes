"""
LEXIS — pipeline/graph.py
Stage 3b: Claude call to extract a concept graph (nodes + edges) from the corpus.

The graph is generated from the full merged text (not per-chunk) so that
cross-page relationships can be discovered.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field

import anthropic
from rich.console import Console

import config
from pipeline.merge import Chunk

console = Console()

GRAPH_SYSTEM = """You are LEXIS, an intelligent knowledge cartographer.
Your job: given a body of text (possibly from multiple web pages), extract a concept graph.

RULES:
- Nodes are meaningful concepts, entities, tools, techniques, processes, risks, or outcomes found in the text.
- Edges represent named relationships between nodes.
- Limit to the 25 most significant nodes. Quality over quantity.
- Every node ID must be a short unique slug (snake_case, no spaces).
- Source URLs should be an array of URLs where this concept appears.
- Return valid JSON only. No markdown fences, no commentary.

OUTPUT FORMAT:
{
  "nodes": [
    {
      "id": "unique_slug",
      "label": "Human Readable Name",
      "type": "entity | process | tool | technique | risk | outcome | concept",
      "weight": 0.1-1.0,
      "summary": "one sentence description",
      "source_urls": ["https://..."]
    }
  ],
  "edges": [
    {
      "source": "node_id",
      "target": "node_id",
      "relation": "uses | causes | depends_on | contrasts | example_of | mitigates | enables | part_of",
      "weight": 0.1-1.0
    }
  ]
}"""


@dataclass
class GraphNode:
    id: str
    label: str
    type: str
    weight: float
    summary: str
    source_urls: list[str] = field(default_factory=list)


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str
    weight: float


@dataclass
class ConceptGraph:
    nodes: list[GraphNode]
    edges: list[GraphEdge]

    def to_dict(self) -> dict:
        return {
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "type": n.type,
                    "weight": n.weight,
                    "summary": n.summary,
                    "source_urls": n.source_urls,
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "relation": e.relation,
                    "weight": e.weight,
                }
                for e in self.edges
            ],
        }


def build_graph(chunks: list[Chunk]) -> ConceptGraph:
    """
    Send the full corpus to Claude and extract a concept graph.
    Truncates to fit context if needed (keeps first 15k words).
    """
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # Build a condensed corpus for graph extraction (keep page boundaries)
    page_groups: dict[str, list[str]] = {}
    for chunk in chunks:
        page_groups.setdefault(chunk.source_url, []).append(chunk.text)

    corpus_parts = []
    for url, texts in page_groups.items():
        title = next((c.page_title for c in chunks if c.source_url == url), url)
        corpus_parts.append(f"=== SOURCE: {title} ({url}) ===\n" + " ".join(texts))

    full_corpus = "\n\n".join(corpus_parts)

    # Truncate to ~15k words to stay within context limits
    words = full_corpus.split()
    if len(words) > 15000:
        full_corpus = " ".join(words[:15000]) + "\n\n[...truncated for graph extraction...]"

    console.print(f"\n[cyan]Graph:[/cyan] extracting concept graph from {len(words)} words…")

    try:
        response = client.messages.create(
            model=config.LEXIS_MODEL,
            max_tokens=4000,
            system=GRAPH_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": f"Extract a concept graph from the following corpus:\n\n{full_corpus}",
                }
            ],
        )

        raw = response.content[0].text.strip()
        data = json.loads(raw)

        nodes = [
            GraphNode(
                id=n["id"],
                label=n["label"],
                type=n.get("type", "concept"),
                weight=float(n.get("weight", 0.5)),
                summary=n.get("summary", ""),
                source_urls=n.get("source_urls", []),
            )
            for n in data.get("nodes", [])
        ]

        # Validate edges — only keep edges where both nodes exist
        node_ids = {n.id for n in nodes}
        edges = [
            GraphEdge(
                source=e["source"],
                target=e["target"],
                relation=e.get("relation", "related"),
                weight=float(e.get("weight", 0.5)),
            )
            for e in data.get("edges", [])
            if e["source"] in node_ids and e["target"] in node_ids
        ]

        console.print(f"  [green]✓ {len(nodes)} nodes, {len(edges)} edges[/green]")
        return ConceptGraph(nodes=nodes, edges=edges)

    except json.JSONDecodeError as exc:
        console.print(f"  [red]✗ Graph JSON parse error: {exc}[/red]")
        return ConceptGraph(nodes=[], edges=[])
    except Exception as exc:
        console.print(f"  [red]✗ Graph API error: {exc}[/red]")
        return ConceptGraph(nodes=[], edges=[])
