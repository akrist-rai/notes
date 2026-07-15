"""
LEXIS — config.py
Loads environment variables and exposes typed settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
LEXIS_MODEL: str = os.getenv("LEXIS_MODEL", "claude-3-5-sonnet-20241022")
CRAWL_DEPTH: int = int(os.getenv("LEXIS_CRAWL_DEPTH", "2"))
MAX_PAGES: int = int(os.getenv("LEXIS_MAX_PAGES", "10"))

# Chunk settings
CHUNK_SIZE_TOKENS: int = 800
CHUNK_OVERLAP_TOKENS: int = 100

# Dedup similarity threshold (0-1). Pages above this are considered duplicates.
DEDUP_THRESHOLD: float = 0.88

def validate() -> None:
    errors = []
    if not FIRECRAWL_API_KEY or FIRECRAWL_API_KEY == "your_firecrawl_key_here":
        errors.append("FIRECRAWL_API_KEY is not set. Add it to .env")
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your_anthropic_key_here":
        errors.append("ANTHROPIC_API_KEY is not set. Add it to .env")
    if errors:
        raise EnvironmentError("\n".join(errors))
