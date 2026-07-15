"""
LEXIS — pipeline/synthesize.py
Stage 4: Claude synthesis call → Section 3 (Dossier mode).

Receives highlights + graph + original pages → generates a structured
intelligence dossier JSON that drives the styled Section 3 HTML output.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import anthropic
from rich.console import Console

import config
from pipeline.highlight import Highlight
from pipeline.graph import ConceptGraph
from pipeline.extract import ExtractedPage

console = Console()

DOSSIER_SYSTEM = """You are LEXIS, an intelligence synthesis engine.
You have analyzed a set of web sources and extracted highlights and a concept graph.
Your job: synthesize this into a structured intelligence dossier.

OUTPUT a JSON object with these fields:

{
  "subject": "the main topic in 5 words or fewer",
  "classification": "OPEN SOURCE INTELLIGENCE",
  "threat_level": "LOW | MEDIUM | HIGH | CRITICAL",
  "executive_summary": "3–4 sentence synthesis of what these sources are actually about",
  "key_findings": [
    { "finding": "one clear finding", "confidence": "HIGH | MEDIUM | LOW", "implication": "why it matters" }
  ],
  "knowledge_gaps": ["list of things the sources DON'T explain that a learner would need"],
  "recommended_learning_path": [
    { "step": 1, "topic": "concept to study first", "reason": "why this builds foundation" }
  ],
  "analogies": [
    { "concept": "technical concept", "analogy": "plain-language analogy that makes it stick" }
  ],
  "threat_surface": "A single paragraph on risks, pitfalls, or misuse potential IF APPLICABLE. Null if not a security/risk topic.",
  "verdict": "One punchy sentence: the single most important thing to take away from all of this."
}

Return valid JSON only. No markdown fences. No commentary."""


@dataclass
class DossierFinding:
    finding: str
    confidence: str
    implication: str


@dataclass
class LearningStep:
    step: int
    topic: str
    reason: str


@dataclass
class Analogy:
    concept: str
    analogy: str


@dataclass
class Dossier:
    subject: str
    classification: str
    threat_level: str
    executive_summary: str
    key_findings: list[DossierFinding]
    knowledge_gaps: list[str]
    recommended_learning_path: list[LearningStep]
    analogies: list[Analogy]
    threat_surface: str | None
    verdict: str

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "classification": self.classification,
            "threat_level": self.threat_level,
            "executive_summary": self.executive_summary,
            "key_findings": [
                {"finding": f.finding, "confidence": f.confidence, "implication": f.implication}
                for f in self.key_findings
            ],
            "knowledge_gaps": self.knowledge_gaps,
            "recommended_learning_path": [
                {"step": s.step, "topic": s.topic, "reason": s.reason}
                for s in self.recommended_learning_path
            ],
            "analogies": [{"concept": a.concept, "analogy": a.analogy} for a in self.analogies],
            "threat_surface": self.threat_surface,
            "verdict": self.verdict,
        }


def synthesize(
    pages: list[ExtractedPage],
    highlights: list[Highlight],
    graph: ConceptGraph,
) -> Dossier:
    """Generate a dossier from the full analysis output."""
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    console.print(f"\n[cyan]Synthesis:[/cyan] generating intelligence dossier…")

    # Build a condensed summary for the synthesis call
    highlight_summary = "\n".join(
        f"[{h.importance.upper()}] {h.text} (reason: {h.reason})"
        for h in highlights[:30]  # Cap at 30 most important
    )

    graph_summary = f"Key concepts: {', '.join(n.label for n in graph.nodes[:15])}"

    source_summary = f"Sources analyzed: {len(pages)} pages\n" + "\n".join(
        f"  - {p.title} ({p.url})" for p in pages
    )

    payload = f"""{source_summary}

KEY HIGHLIGHTS EXTRACTED:
{highlight_summary}

CONCEPT GRAPH OVERVIEW:
{graph_summary}
Relationships: {len(graph.edges)} connections identified."""

    try:
        response = client.messages.create(
            model=config.LEXIS_MODEL,
            max_tokens=3000,
            system=DOSSIER_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": f"Synthesize the following analysis into an intelligence dossier:\n\n{payload}",
                }
            ],
        )

        raw = response.content[0].text.strip()
        data = json.loads(raw)

        dossier = Dossier(
            subject=data.get("subject", "Unknown Subject"),
            classification=data.get("classification", "OPEN SOURCE INTELLIGENCE"),
            threat_level=data.get("threat_level", "LOW"),
            executive_summary=data.get("executive_summary", ""),
            key_findings=[
                DossierFinding(
                    finding=f["finding"],
                    confidence=f.get("confidence", "MEDIUM"),
                    implication=f.get("implication", ""),
                )
                for f in data.get("key_findings", [])
            ],
            knowledge_gaps=data.get("knowledge_gaps", []),
            recommended_learning_path=[
                LearningStep(step=s["step"], topic=s["topic"], reason=s.get("reason", ""))
                for s in data.get("recommended_learning_path", [])
            ],
            analogies=[
                Analogy(concept=a["concept"], analogy=a["analogy"])
                for a in data.get("analogies", [])
            ],
            threat_surface=data.get("threat_surface"),
            verdict=data.get("verdict", ""),
        )

        console.print(f"  [green]✓ Dossier generated: {dossier.subject}[/green]")
        return dossier

    except json.JSONDecodeError as exc:
        console.print(f"  [red]✗ Dossier JSON parse error: {exc}[/red]")
        return _fallback_dossier()
    except Exception as exc:
        console.print(f"  [red]✗ Dossier API error: {exc}[/red]")
        return _fallback_dossier()


def _fallback_dossier() -> Dossier:
    return Dossier(
        subject="Unknown",
        classification="OPEN SOURCE INTELLIGENCE",
        threat_level="LOW",
        executive_summary="Synthesis failed — see highlights and graph for raw analysis.",
        key_findings=[],
        knowledge_gaps=[],
        recommended_learning_path=[],
        analogies=[],
        threat_surface=None,
        verdict="Review the raw highlights above.",
    )
