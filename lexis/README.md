# LEXIS — Intelligent Web Digest Engine

Transform any URL(s) into a styled 3-section intelligence artifact:

| Section | Content |
|---|---|
| **01 Annotated Source** | Original text with AI-highlighted spans (hover for reasoning) |
| **02 Concept Graph** | Force-directed graph of extracted concepts and relationships |
| **03 Intelligence Dossier** | Key findings, knowledge gaps, learning path, analogies, verdict |

---

## Setup

```bash
# 1. Create virtualenv
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env
# Edit .env — add your Firecrawl and Anthropic keys
```

**API Keys:**
- **Firecrawl** — [firecrawl.dev](https://firecrawl.dev) (free tier: 500 pages/month)
- **Anthropic** — [console.anthropic.com](https://console.anthropic.com) (~$0.05–0.15 per analysis)

---

## Usage

```bash
# Analyze a single URL (crawls child pages automatically)
python lexis.py https://example.com

# Analyze a specific URL without crawling
python lexis.py https://example.com --no-crawl

# Analyze multiple unrelated URLs
python lexis.py https://site-a.com https://site-b.com

# Custom output filename
python lexis.py https://example.com --output my_report.html

# Dry run (no API calls, mock data — good for testing the UI)
python lexis.py https://example.com --dry-run
```

Output is a self-contained `.html` file — open it in any browser.

---

## Architecture

```
URL(s)
  │
  ▼ [Stage 1] pipeline/extract.py
  │   Firecrawl /crawl or /scrape → markdown per page
  │
  ▼ [Stage 2] pipeline/merge.py
  │   Semantic dedup (sentence-transformers) + chunking
  │
  ├──▶ [Stage 3a] pipeline/highlight.py
  │     Claude → JSON highlight spans per chunk
  │
  └──▶ [Stage 3b] pipeline/graph.py
        Claude → JSON concept graph (nodes + edges)
  │
  ▼ [Stage 4] pipeline/synthesize.py
  │   Claude → Intelligence dossier JSON
  │
  ▼ [Stage 5] renderer/render.py
      Inject all JSON into renderer/template.html → output.html
```

---

## Project Structure

```
lexis/
├── lexis.py              # CLI entry point
├── config.py             # Settings from .env
├── requirements.txt
├── .env.example
├── pipeline/
│   ├── extract.py        # Firecrawl extraction
│   ├── merge.py          # Dedup + chunking
│   ├── highlight.py      # Claude highlight call
│   ├── graph.py          # Claude graph call
│   └── synthesize.py     # Claude dossier synthesis
└── renderer/
    ├── render.py          # Template injection
    └── template.html      # Styled 3-section output shell
```

---

## Roadmap

- [x] **Phase 1** — Single URL → dossier output (MVP)
- [ ] **Phase 2** — Multi-source merge with cross-page graph
- [ ] **Phase 3** — Section 3 modes: `timeline`, `quiz`, `vs`
- [ ] **Phase 4** — Personalization: fine-tune highlight ranker on your accept/reject history (Colab)
