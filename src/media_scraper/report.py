"""Assemble the Markdown report. Required sections are always emitted (FR-008, SC-002)."""

import re
from datetime import datetime
from pathlib import Path

from .models import Config, ResearchPlan, Source, SourceAnalysis


def _slug(topic: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    return s[:50].strip("-") or "report"


def _competitive_section(cfg: Config, analyzed: list[tuple[Source, SourceAnalysis]]) -> list[str]:
    """Per-brand sentiment tally over the full competitive set (zero-rows included, SC-001)."""
    by_subject: dict[str, list[SourceAnalysis]] = {}
    for _s, a in analyzed:
        by_subject.setdefault(a.subject, []).append(a)

    out = ["## Competitive Sentiment\n"]
    out.append("_Reports only mentions new since the last run for this brief._\n")
    out.append("| Brand | Positive | Neutral | Negative | Mentions | Avg Credibility |")
    out.append("|---|---|---|---|---|---|")
    for brand in cfg.brands:
        items = by_subject.get(brand, [])
        pos = sum(1 for a in items if a.sentiment == "positive")
        neg = sum(1 for a in items if a.sentiment == "negative")
        neu = len(items) - pos - neg  # neutral + mixed under the headline neutral column
        avg = f"{sum(a.credibility for a in items) / len(items):.1f}" if items else "—"
        out.append(f"| {brand} | {pos} | {neu} | {neg} | {len(items)} | {avg} |")
    out.append("")
    return out


def write_report(
    topic: str,
    plan: ResearchPlan,
    all_sources: list[Source],
    analyzed: list[tuple[Source, SourceAnalysis]],
    body: str,
    cfg: Config,
) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = Path(cfg.output_dir) / f"{_slug(topic)}-{ts}.md"

    ok_sources = [s for s, _ in analyzed]
    failed = [s for s in all_sources if s.status != "ok"]

    out: list[str] = []
    out.append(f"# Research Report: {topic}\n")
    out.append(
        f"*Generated {datetime.now():%Y-%m-%d %H:%M} · model `{cfg.model}` · "
        f"{len(all_sources)} sources gathered, {len(analyzed)} analyzed*\n"
    )

    out.append("## Summary & Key Findings\n")
    out.append((body or "_No synthesis was produced._").strip() + "\n")

    if cfg.brand:
        out.extend(_competitive_section(cfg, analyzed))

    out.append("## Per-Source Analysis\n")
    if analyzed:
        out.append("| Source | Sentiment | Credibility | Rationale |")
        out.append("|---|---|---|---|")
        for s, a in analyzed:
            title = (s.title or s.url).replace("|", "/")
            rationale = (a.credibility_rationale or "").replace("|", "/").replace("\n", " ")
            out.append(f"| [{title}]({s.url}) | {a.sentiment} | {a.credibility}/5 | {rationale} |")
    else:
        out.append("_No sources were successfully analyzed._")
    out.append("")

    out.append("## Sources\n")
    if ok_sources:
        for s in ok_sources:
            out.append(f"- [{s.title or s.url}]({s.url}) ({s.kind})")
    else:
        out.append("_None._")
    out.append("")

    out.append("## Steps Taken\n")
    out.append(f"- Sub-questions: {', '.join(plan.sub_questions) or '—'}")
    out.append(f"- Search queries: {', '.join(plan.search_queries) or '—'}")
    out.append(f"- RSS feeds: {', '.join(plan.rss_feeds) or '—'}")
    out.append(f"- Target sites: {', '.join(plan.target_sites) or '—'}")
    out.append(
        f"- Gathered {len(all_sources)} sources; {len(analyzed)} analyzed; "
        f"{len(failed)} skipped/failed."
    )
    out.append("")

    if failed:
        out.append("## Appendix: Skipped or Failed Sources\n")
        for s in failed:
            suffix = f" ({s.error})" if s.error else ""
            out.append(f"- {s.url} — {s.status}{suffix}")
        out.append("")

    path.write_text("\n".join(out), encoding="utf-8")
    return path
