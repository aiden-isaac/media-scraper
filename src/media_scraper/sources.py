"""Keyless web/news search (ddgs) and RSS/Atom ingestion (feedparser).

Heavy deps are imported lazily so the pipeline/report modules (and the test) import without
requiring them.
"""

import re

from .models import Source


def web_search(query: str, max_results: int = 10) -> list[tuple[str, str]]:
    """Return [(title, url), ...] from DuckDuckGo. Empty list on failure."""
    try:
        from ddgs import DDGS  # current package name
    except ImportError:  # pragma: no cover - fallback for older installs
        from duckduckgo_search import DDGS

    results: list[tuple[str, str]] = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            url = r.get("href") or r.get("url") or ""
            title = r.get("title") or ""
            if url:
                results.append((title, url))
    return results


def fetch_rss(feed_url: str, max_entries: int = 10, max_chars: int = 8000) -> list[Source]:
    """Parse an RSS/Atom feed into Sources (summary text, HTML stripped, truncated)."""
    import feedparser

    parsed = feedparser.parse(feed_url)
    out: list[Source] = []
    for entry in parsed.entries[:max_entries]:
        title = getattr(entry, "title", "")
        link = getattr(entry, "link", feed_url)
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
        text = re.sub(r"<[^>]+>", " ", summary)
        text = re.sub(r"\s+", " ", text).strip()[:max_chars]
        out.append(
            Source(
                url=link,
                title=title,
                kind="rss",
                text=text,
                status="ok" if text else "fetch_error",
                error=None if text else "empty feed entry",
            )
        )
    return out
