"""Orchestrates plan -> gather -> analyze -> synthesize.

`run` takes a `gather` callable so it can be driven in tests without a real browser.
"""

from pathlib import Path
from typing import Callable

from . import report, sources
from .models import Config, ResearchPlan, Source

LogFn = Callable[..., None]


class NoSourcesError(Exception):
    """The plan produced nothing to gather (CLI exit code 3)."""


def _noop(*_args, **_kwargs) -> None:
    pass


def gather_sources(plan: ResearchPlan, cfg: Config, browser, log: LogFn = _noop) -> list[Source]:
    """Real gatherer: web/news search + page fetch, RSS, and gated/social pages."""
    out: list[Source] = []
    cap = cfg.max_sources

    for query in plan.search_queries:
        if len(out) >= cap:
            break
        try:
            results = sources.web_search(query, cfg.max_sources)
        except Exception as exc:  # search backend hiccup — skip this query, keep going
            log("gather", f"search failed for {query!r}: {exc}")
            results = []
        for title, url in results:
            if len(out) >= cap:
                break
            log("gather", f"fetch {url}")
            out.append(browser.fetch_page(url, kind="web", title=title))

    for feed in plan.rss_feeds:
        if len(out) >= cap:
            break
        try:
            out.extend(sources.fetch_rss(feed, cfg.max_sources, cfg.max_chars_per_source))
        except Exception as exc:
            log("gather", f"rss failed for {feed!r}: {exc}")

    for site in plan.target_sites:
        if len(out) >= cap:
            break
        url = site if site.startswith("http") else f"https://{site}"
        log("gather", f"fetch (gated) {url}")
        out.append(browser.fetch_page(url, kind="social", title=site))

    return out[:cap]


def run(topic: str, cfg: Config, llm, gather: Callable[[ResearchPlan], list[Source]], log: LogFn = _noop) -> Path:
    log("plan", f"Planning research for: {topic[:80]}")
    plan = llm.plan(topic)
    if not plan.has_sources:
        raise NoSourcesError("The model produced no searchable sources for this topic.")

    log("gather", "Gathering sources…")
    all_sources = gather(plan)
    usable = [s for s in all_sources if s.status == "ok" and s.text.strip()]
    log("gather", f"Gathered {len(all_sources)} sources ({len(usable)} usable).")

    log("analyze", f"Analyzing {len(usable)} sources…")
    analyzed = [(s, llm.analyze(s)) for s in usable]

    log("synthesize", "Writing report…")
    body = llm.synthesize(topic, plan, analyzed)

    path = report.write_report(topic, plan, all_sources, analyzed, body, cfg)
    log("synthesize", f"Report written: {path}")
    return path
