"""Shared dataclasses passed between pipeline stages (see specs .../data-model.md)."""

from dataclasses import dataclass, field
from pathlib import Path

# Allowed enum values, kept as plain strings (ponytail: no Enum class for 4 constants).
SENTIMENTS = ("positive", "neutral", "negative", "mixed")
SOURCE_KINDS = ("web", "news", "rss", "social")
SOURCE_STATUSES = ("ok", "login_skipped", "fetch_error")
PLATFORMS = ("x", "reddit", "youtube", "facebook", "linkedin", "tiktok", "news")


@dataclass
class Config:
    base_url: str
    model: str
    api_key: str
    output_dir: Path
    user_data_dir: Path
    headless: bool = False
    max_sources: int = 12
    max_chars_per_source: int = 8000
    # Competitive-intelligence brief (feature 003); empty brand = ad-hoc --topic run.
    brand: str = ""
    competitors: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    recency_days: int = 0  # 0 = no date filter

    @property
    def brands(self) -> list[str]:
        """Full competitive set: primary brand first, then competitors."""
        return [self.brand, *self.competitors] if self.brand else []


@dataclass
class ResearchPlan:
    topic: str
    sub_questions: list[str] = field(default_factory=list)
    search_queries: list[str] = field(default_factory=list)
    rss_feeds: list[str] = field(default_factory=list)
    target_sites: list[str] = field(default_factory=list)

    @property
    def has_sources(self) -> bool:
        return bool(self.search_queries or self.rss_feeds or self.target_sites)


@dataclass
class Source:
    url: str
    title: str = ""
    kind: str = "web"          # one of SOURCE_KINDS
    text: str = ""
    status: str = "ok"         # one of SOURCE_STATUSES
    error: str | None = None


@dataclass
class SourceAnalysis:
    url: str
    claims: list[str] = field(default_factory=list)
    sentiment: str = "neutral"  # one of SENTIMENTS
    credibility: int = 3        # 1..5
    credibility_rationale: str = ""
    subject: str = ""           # which brand the source concerns; "" / "other" when none
