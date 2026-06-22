"""Keyless web/news search (ddgs) and RSS/Atom ingestion (feedparser).

Heavy deps are imported lazily so the pipeline/report modules (and the test) import without
requiring them.
"""

import re
from urllib.parse import quote_plus

from .models import Source

# Each platform's own search results page (research §1, tier 1).
SEARCH_URLS = {
    "x": "https://x.com/search?q={q}",
    "reddit": "https://www.reddit.com/search/?q={q}",
    "youtube": "https://www.youtube.com/results?search_query={q}",
    "facebook": "https://www.facebook.com/search/posts?q={q}",
    "linkedin": "https://www.linkedin.com/search/results/content/?keywords={q}",
    "tiktok": "https://www.tiktok.com/search?q={q}",
    "news": "https://news.google.com/search?q={q}",
}
# Domains for the keyless `site:` web-search fallback (research §1, tier 3).
SITE_DOMAINS = {
    "x": "x.com", "reddit": "reddit.com", "youtube": "youtube.com",
    "facebook": "facebook.com", "linkedin": "linkedin.com",
    "tiktok": "tiktok.com", "news": "news.google.com",
}
# Freshness hints appended when a recency window is active, only where well-supported (T016).
_FRESH_PARAMS = {"x": "&f=live", "reddit": "&sort=new"}


def search_url(platform: str, query: str, fresh: bool = False) -> str:
    """Build a platform's in-site search URL; append a freshness hint when `fresh`."""
    url = SEARCH_URLS[platform].format(q=quote_plus(query))
    if fresh:
        url += _FRESH_PARAMS.get(platform, "")
    return url


def site_query(platform: str, terms: list[str]) -> str:
    """`site:<domain> <terms>` for the keyless web-search fallback."""
    domain = SITE_DOMAINS.get(platform, platform)
    return f"site:{domain} " + " ".join(terms)


def recency_timelimit(days: int) -> str | None:
    """Map a recency window in days to ddgs' native timelimit code, or None for no filter."""
    if days <= 0:
        return None
    if days <= 1:
        return "d"
    if days <= 7:
        return "w"
    if days <= 31:
        return "m"
    return "y"


def web_search(query: str, max_results: int = 10, timelimit: str | None = None) -> list[tuple[str, str]]:
    """Return [(title, url), ...] from DuckDuckGo. Empty list on failure.

    `timelimit` is ddgs' native date filter (`d`/`w`/`m`/`y`), or None for no window.
    """
    try:
        from ddgs import DDGS  # current package name
    except ImportError:  # pragma: no cover - fallback for older installs
        from duckduckgo_search import DDGS

    results: list[tuple[str, str]] = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results, timelimit=timelimit):
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
