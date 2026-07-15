#!/usr/bin/env python3
"""
LEXIS — lexis.py
CLI entry point.

Usage:
  python lexis.py https://example.com
  python lexis.py https://site-a.com https://site-b.com --no-crawl
  python lexis.py https://example.com --output my_report.html
"""
import sys
import click
from pathlib import Path
from rich.console import Console
from rich.rule import Rule

console = Console()


@click.command()
@click.argument("urls", nargs=-1, required=True)
@click.option("--output", "-o", default=None, help="Output HTML filename (default: auto)")
@click.option("--crawl/--no-crawl", default=True, help="Crawl child pages (single URL only)")
@click.option("--dry-run", is_flag=True, help="Run with mock data (no API calls)")
def main(urls: tuple[str, ...], output: str | None, crawl: bool, dry_run: bool) -> None:
    """
    LEXIS — Intelligent Web Digest Engine.
    Transforms URLs into a stylized 3-section intelligence artifact.
    """
    console.print(Rule("[cyan]LEXIS[/cyan] Intelligence Pipeline", style="dim"))

    # Validate config
    if not dry_run:
        import config
        try:
            config.validate()
        except EnvironmentError as e:
            console.print(f"\n[red]Configuration error:[/red] {e}")
            console.print("[dim]Copy .env.example to .env and fill in your API keys.[/dim]")
            sys.exit(1)

    url_list = list(urls)
    console.print(f"[bold]URLs:[/bold] {', '.join(url_list)}")
    console.print(f"[bold]Crawl:[/bold] {crawl} | [bold]Dry-run:[/bold] {dry_run}")

    # Output filename
    if output is None:
        from urllib.parse import urlparse
        domain = urlparse(url_list[0]).netloc.replace("www.", "").replace(".", "_")
        output = f"lexis_{domain}.html"
    output_path = Path(output)

    if dry_run:
        _run_dry(url_list, output_path)
    else:
        _run_live(url_list, crawl, output_path)


def _run_live(urls: list[str], crawl: bool, output_path: Path) -> None:
    from pipeline.extract import extract
    from pipeline.merge import merge
    from pipeline.highlight import highlight
    from pipeline.graph import build_graph
    from pipeline.synthesize import synthesize
    from renderer.render import render

    console.print(Rule("Stage 1 — Extract", style="dim"))
    pages = extract(urls, crawl=crawl)
    if not pages:
        console.print("[red]No pages extracted. Check your URLs and API key.[/red]")
        sys.exit(1)

    console.print(Rule("Stage 2 — Merge & Chunk", style="dim"))
    chunks = merge(pages)
    if not chunks:
        console.print("[red]No content after merging. Pages may be empty.[/red]")
        sys.exit(1)

    console.print(Rule("Stage 3 — Highlight + Graph (parallel)", style="dim"))
    # Run highlight and graph in parallel using threads
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        hl_future   = executor.submit(highlight, chunks)
        graph_future = executor.submit(build_graph, chunks)
        highlights  = hl_future.result()
        graph       = graph_future.result()

    console.print(Rule("Stage 4 — Synthesize", style="dim"))
    dossier = synthesize(pages, highlights, graph)

    console.print(Rule("Stage 5 — Render", style="dim"))
    render(pages, highlights, graph, dossier, output_path)


def _run_dry(urls: list[str], output_path: Path) -> None:
    """Dry run using mock data — useful for frontend development."""
    from pipeline.extract import ExtractedPage
    from pipeline.highlight import Highlight
    from pipeline.graph import ConceptGraph, GraphNode, GraphEdge
    from pipeline.synthesize import Dossier, DossierFinding, LearningStep, Analogy
    from renderer.render import render

    console.print("[yellow]⚠ DRY RUN — using mock data, no API calls[/yellow]")

    pages = [
        ExtractedPage(
            url=urls[0],
            title="Example Source Page",
            markdown="""# Introduction to the Topic

This is a sample article about a complex subject. The key insight here is that understanding the fundamentals is critical before moving on to advanced topics.

## Core Concepts

The first concept to grasp is the relationship between inputs and outputs in any system. Without this foundation, the rest becomes noise.

A second important idea: iteration beats perfection. Systems that learn from feedback loops outperform those designed in isolation.

## Risks and Considerations

One major warning: over-engineering early leads to brittle systems. Start simple, add complexity only when forced.

## Conclusion

The most important takeaway is that structured thinking applied to messy domains is itself a learnable skill.""",
            description="A sample page for dry-run testing",
        )
    ]

    highlights = [
        Highlight("understanding the fundamentals is critical", "critical", "Foundation before advanced topics", "concept", urls[0], "Example Source Page", "c1"),
        Highlight("iteration beats perfection", "high", "Feedback loops outperform isolated design", "claim", urls[0], "Example Source Page", "c2"),
        Highlight("over-engineering early leads to brittle systems", "high", "Key anti-pattern warning", "warning", urls[0], "Example Source Page", "c3"),
        Highlight("structured thinking applied to messy domains", "medium", "Meta-skill worth internalizing", "concept", urls[0], "Example Source Page", "c4"),
    ]

    graph = ConceptGraph(
        nodes=[
            GraphNode("fundamentals", "Fundamentals", "concept", 0.9, "Core foundational knowledge"),
            GraphNode("iteration", "Iteration", "process", 0.8, "Feedback-driven improvement loop"),
            GraphNode("over_engineering", "Over-Engineering", "risk", 0.7, "Premature complexity anti-pattern"),
            GraphNode("structured_thinking", "Structured Thinking", "technique", 0.85, "Applying systematic frameworks"),
            GraphNode("feedback_loops", "Feedback Loops", "process", 0.75, "Mechanisms for learning from output"),
        ],
        edges=[
            GraphEdge("fundamentals", "structured_thinking", "enables", 0.9),
            GraphEdge("structured_thinking", "iteration", "uses", 0.8),
            GraphEdge("iteration", "feedback_loops", "depends_on", 0.85),
            GraphEdge("over_engineering", "iteration", "contrasts", 0.7),
        ],
    )

    dossier = Dossier(
        subject="Structured Learning Systems",
        classification="OPEN SOURCE INTELLIGENCE",
        threat_level="LOW",
        executive_summary="The source material covers a systematic approach to learning and building within complex domains. Core themes include foundational knowledge, iterative improvement, and the dangers of premature optimization. The material advocates for feedback-driven processes over isolated design.",
        key_findings=[
            DossierFinding("Fundamentals must precede advanced concepts", "HIGH", "Skipping foundations creates compounding knowledge debt"),
            DossierFinding("Feedback loops are the primary driver of system improvement", "HIGH", "Without measurement, optimization is guesswork"),
            DossierFinding("Over-engineering is the most common early failure mode", "MEDIUM", "Premature complexity is harder to undo than to prevent"),
        ],
        knowledge_gaps=["No coverage of failure recovery strategies", "Lacks quantitative metrics for 'good enough'", "Does not address team dynamics"],
        recommended_learning_path=[
            LearningStep(1, "Core domain fundamentals", "Without this, nothing else lands"),
            LearningStep(2, "Feedback loop design", "Enables iteration to be productive rather than random"),
            LearningStep(3, "Complexity management patterns", "Prevents the over-engineering failure mode"),
        ],
        analogies=[
            Analogy("Feedback loops", "Like a thermostat — it doesn't know the perfect temperature, it just corrects when it drifts too far"),
            Analogy("Over-engineering", "Like packing 10 suitcases for a weekend trip — the weight becomes the problem, not the destination"),
        ],
        threat_surface=None,
        verdict="Master the feedback loop first — everything else is commentary.",
    )

    render(pages, highlights, graph, dossier, output_path)


if __name__ == "__main__":
    main()
