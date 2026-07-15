"""
LEXIS — pipeline/merge.py
Stage 2: Deduplication + chunking across multiple extracted pages.

Steps:
1. Compute sentence-transformer embeddings for each page.
2. Drop near-duplicate pages (cosine similarity > threshold).
3. Chunk remaining pages into ~800-token segments with overlap.
4. Return a flat list of Chunk objects with source metadata.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from rich.console import Console

import config
from pipeline.extract import ExtractedPage

console = Console()


@dataclass
class Chunk:
    id: str
    text: str
    source_url: str
    page_title: str
    chunk_index: int


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def _word_chunks(text: str, size: int, overlap: int) -> list[str]:
    """Split text into word-count-approximate chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += size - overlap
    return chunks


def merge(pages: list[ExtractedPage]) -> list[Chunk]:
    """
    Dedup pages by semantic similarity, then chunk each unique page.

    Returns a flat list of Chunk objects ready for the highlight/graph calls.
    """
    if not pages:
        return []

    console.print(f"\n[cyan]Merge:[/cyan] deduplicating {len(pages)} pages…")

    # Lazy-import sentence-transformers so startup is fast if only one page
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        model = SentenceTransformer("all-MiniLM-L6-v2")
        texts = [p.markdown[:2000] for p in pages]  # Only use first 2000 chars for speed
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

        kept_indices: list[int] = []
        for i, emb in enumerate(embeddings):
            is_dup = False
            for j in kept_indices:
                if _cosine_similarity(emb, embeddings[j]) > config.DEDUP_THRESHOLD:
                    console.print(f"  [dim]↳ Skipping duplicate: {pages[i].url}[/dim]")
                    is_dup = True
                    break
            if not is_dup:
                kept_indices.append(i)

    except ImportError:
        console.print("  [yellow]sentence-transformers not installed — skipping dedup[/yellow]")
        kept_indices = list(range(len(pages)))

    unique_pages = [pages[i] for i in kept_indices]
    console.print(f"  [green]✓ {len(unique_pages)} unique pages after dedup[/green]")

    # Chunk each page
    chunks: list[Chunk] = []
    for page in unique_pages:
        raw_chunks = _word_chunks(
            page.markdown,
            size=config.CHUNK_SIZE_TOKENS,
            overlap=config.CHUNK_OVERLAP_TOKENS,
        )
        for idx, chunk_text in enumerate(raw_chunks):
            if len(chunk_text.strip()) < 50:
                continue
            chunks.append(
                Chunk(
                    id=str(uuid.uuid4())[:8],
                    text=chunk_text,
                    source_url=page.url,
                    page_title=page.title,
                    chunk_index=idx,
                )
            )

    console.print(f"  [green]✓ {len(chunks)} chunks ready[/green]")
    return chunks
