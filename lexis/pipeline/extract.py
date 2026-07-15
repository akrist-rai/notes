"""
LEXIS — pipeline/extract.py
Stage 1: URL → clean markdown per page using Firecrawl.

Supports:
- Single URL (scrape mode)
- Root URL with crawl depth (discover all child pages)
- List of unrelated URLs (scrape each individually)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from firecrawl import FirecrawlApp
from rich.console import Console

import config

console = Console()


@dataclass
class ExtractedPage:
    url: str
    title: str
    markdown: str
    description: str = ""
    og_image: str = ""


def _scrape_single(app: FirecrawlApp, url: str) -> Optional[ExtractedPage]:
    """Scrape one URL and return an ExtractedPage."""
    try:
        result = app.scrape_url(url, params={"formats": ["markdown"]})
        metadata = result.get("metadata", {})
        return ExtractedPage(
            url=url,
            title=metadata.get("title", url),
            markdown=result.get("markdown", ""),
            description=metadata.get("description", ""),
            og_image=metadata.get("ogImage", ""),
        )
    except Exception as exc:
        console.print(f"[red]  ✗ Failed to scrape {url}: {exc}[/red]")
        return None


def extract(urls: list[str], crawl: bool = True) -> list[ExtractedPage]:
    """
    Given a list of URLs, extract clean markdown from each.

    Args:
        urls: List of URLs to process.
        crawl: If True and only one URL provided, use Firecrawl /crawl to
               discover child pages up to config.CRAWL_DEPTH and config.MAX_PAGES.
               If multiple URLs provided, always scrape each individually.

    Returns:
        List of ExtractedPage objects (may be empty if all fail).
    """
    app = FirecrawlApp(api_key=config.FIRECRAWL_API_KEY)
    pages: list[ExtractedPage] = []

    if crawl and len(urls) == 1:
        root = urls[0]
        console.print(f"\n[cyan]↳ Crawling[/cyan] {root} (depth={config.CRAWL_DEPTH}, max={config.MAX_PAGES})")

        try:
            crawl_result = app.crawl_url(
                root,
                params={
                    "limit": config.MAX_PAGES,
                    "maxDepth": config.CRAWL_DEPTH,
                    "scrapeOptions": {"formats": ["markdown"]},
                },
                poll_interval=3,
            )
            raw_pages = crawl_result.get("data", [])
            console.print(f"[green]  ✓ Found {len(raw_pages)} pages[/green]")

            for p in raw_pages:
                metadata = p.get("metadata", {})
                pages.append(
                    ExtractedPage(
                        url=metadata.get("sourceURL", root),
                        title=metadata.get("title", "Untitled"),
                        markdown=p.get("markdown", ""),
                        description=metadata.get("description", ""),
                        og_image=metadata.get("ogImage", ""),
                    )
                )
        except Exception as exc:
            console.print(f"[red]  Crawl failed ({exc}), falling back to single-page scrape[/red]")
            page = _scrape_single(app, root)
            if page:
                pages.append(page)

    else:
        for url in urls:
            console.print(f"[cyan]↳ Scraping[/cyan] {url}")
            page = _scrape_single(app, url)
            if page:
                pages.append(page)
                console.print(f"[green]  ✓ {len(page.markdown)} chars[/green]")

    # Filter out near-empty pages
    pages = [p for p in pages if len(p.markdown.strip()) > 100]
    console.print(f"\n[bold green]Extraction complete:[/bold green] {len(pages)} usable pages")
    return pages
