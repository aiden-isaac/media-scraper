"""Orchestrates plan -> gather -> analyze -> synthesize.

`run` takes a `gather` callable so it can be driven in tests without a real browser.
"""

from pathlib import Path
from typing import Callable

from . import report, sources, state
from .models import Config, ResearchPlan, Source

LogFn = Callable[..., None]


class NoSourcesError(Exception):
    """The plan produced nothing to gather (CLI exit code 3)."""


def _noop(*_args, **_kwargs) -> None:
    pass


def _normalize_target_url(site: str) -> str | None:
    """A planner target site/handle → a fetchable URL, or None to skip.

    Fixes the malformed-handle bug: a bare `@handle` must never become `https://@handle`.
    """
    site = site.strip()
    if not site:
        return None
    if site.startswith(("http://", "https://")):
        return site
    if site.startswith("@"):
        # Bare social handle — default to X (the @-handle platform).
        return f"https://x.com/{site.lstrip('@')}"
    if " " not in site and "." in site:  # bare domain
        return f"https://{site}"
    return None  # free-text name, not a URL — skip rather than build a bad link


def gather_sources(
    plan: ResearchPlan, cfg: Config, browser, log: LogFn = _noop, seen: set[str] | None = None
) -> list[Source]:
    """Web/news search, in-site social search per platform × brand, RSS, and gated pages.

    Already-seen URLs are skipped before fetching. Recency (`cfg.recency_days`) narrows the
    search window. ponytail: no recursive crawl — breadth comes from query expansion across
    brand × competitors × platforms, capped by `max_sources`, not link-following.
    """
    seen = seen or set()
    out: list[Source] = []
    added: set[str] = set()
    cap = cfg.max_sources
    timelimit = sources.recency_timelimit(cfg.recency_days)
    fresh = cfg.recency_days > 0

    def add(s: Source) -> None:
        if s.url and s.url not in seen and s.url not in added:
            added.add(s.url)
            out.append(s)

    # Web/news search from the planner's (comparative) queries.
    for query in plan.search_queries:
        if len(out) >= cap:
            break
        try:
            results = sources.web_search(query, cfg.max_sources, timelimit=timelimit)
        except Exception as exc:  # search backend hiccup — skip this query, keep going
            log("gather", f"search failed for {query!r}: {exc}")
            results = []
        for title, url in results:
            if len(out) >= cap:
                break
            if url in seen:
                continue
            log("gather", f"fetch {url}")
            add(browser.fetch_page(url, kind="web", title=title))

    # In-site social search per platform × brand/competitor (research §1).
    subjects = cfg.brands or ([plan.topic] if cfg.platforms else [])
    per = max(1, cap // max(1, len(cfg.platforms) * len(subjects))) if subjects else 0
    for platform in cfg.platforms:
        for subject in subjects:
            if len(out) >= cap:
                break
            try:
                hits = browser.search_site(platform, subject, limit=per or 5, fresh=fresh)
            except Exception as exc:
                log("gather", f"search_site {platform} failed: {exc}")
                hits = []
            if hits:
                for s in hits:
                    if len(out) >= cap:
                        break
                    add(s)
                continue
            # Keyless `site:` fallback — works headless/unattended when the platform is walled.
            try:
                fb = sources.web_search(sources.site_query(platform, [subject]), per or 5, timelimit=timelimit)
            except Exception as exc:
                log("gather", f"site: fallback {platform} failed: {exc}")
                fb = []
            for title, url in fb:
                if len(out) >= cap:
                    break
                if url in seen:
                    continue
                log("gather", f"fetch (social) {url}")
                add(browser.fetch_page(url, kind="social", title=title))

    for feed in plan.rss_feeds:
        if len(out) >= cap:
            break
        try:
            for s in sources.fetch_rss(feed, cfg.max_sources, cfg.max_chars_per_source):
                add(s)
        except Exception as exc:
            log("gather", f"rss failed for {feed!r}: {exc}")

    for site in plan.target_sites:
        if len(out) >= cap:
            break
        url = _normalize_target_url(site)
        if not url:
            log("gather", f"skip unparseable target {site!r}")
            continue
        if url in seen:
            continue
        log("gather", f"fetch (gated) {url}")
        add(browser.fetch_page(url, kind="social", title=site))

    return out[:cap]


def run(
    topic: str,
    cfg: Config,
    llm,
    gather: Callable[[ResearchPlan, set[str]], list[Source]],
    log: LogFn = _noop,
    brand: str = "",
    state_dir: str = ".state",
) -> Path:
    slug = report._slug(brand or topic)
    seen = state.load_seen(slug, state_dir)

    log("plan", f"Planning research for: {topic[:80]}")
    plan = llm.plan(topic)
    if not plan.has_sources:
        raise NoSourcesError("The model produced no searchable sources for this topic.")

    log("gather", "Gathering sources…")
    all_sources = [s for s in gather(plan, seen) if s.url not in seen]  # dedup is authoritative here
    usable = [s for s in all_sources if s.status == "ok" and s.text.strip()]
    log("gather", f"Gathered {len(all_sources)} sources ({len(usable)} usable).")

    log("analyze", f"Analyzing {len(usable)} sources…")
    analyzed = [(s, llm.analyze(s)) for s in usable]

    log("synthesize", "Writing report…")
    body = llm.synthesize(topic, plan, analyzed)

    path = report.write_report(topic, plan, all_sources, analyzed, body, cfg)
    # Seen-state is written ONLY after a successful report, so a failed run doesn't suppress items.
    state.save_seen(slug, seen | {s.url for s in all_sources}, state_dir)
    log("synthesize", f"Report written: {path}")
    return path
