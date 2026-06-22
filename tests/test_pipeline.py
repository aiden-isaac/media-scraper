"""Stub-LLM pipeline check (constitution Principle V). No network or browser needed.

Run directly:  python tests/test_pipeline.py
Or with pytest: python -m pytest tests/test_pipeline.py
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from media_scraper import pipeline, report, state  # noqa: E402
from media_scraper.models import Config, ResearchPlan, Source, SourceAnalysis  # noqa: E402


class StubLLM:
    """The orchestrator calls analyze(source); we steer its subject off source.title."""

    def __init__(self, brands=None):
        self.brands = brands or []

    def plan(self, topic):
        return ResearchPlan(topic=topic, sub_questions=["What is X?"], search_queries=["X overview"])

    def analyze(self, source):
        if self.brands:
            subject = source.title if source.title in self.brands else "other"
        else:
            subject = ""
        return SourceAnalysis(
            url=source.url,
            claims=["claim one"],
            sentiment="positive",
            credibility=4,
            credibility_rationale="reputable outlet",
            subject=subject,
        )

    def synthesize(self, topic, plan, analyzed):
        return "## Summary\nA short summary.\n\n## Key Findings\n- finding one"


def _cfg(tmp, **kw):
    cfg = Config(
        base_url="http://x",
        model="stub",
        api_key="k",
        output_dir=Path(tmp) / "reports",
        user_data_dir=Path(tmp) / "profile",
        max_sources=10,
        max_chars_per_source=8000,
        **kw,
    )
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    return cfg


def test_pipeline_produces_report_and_survives_failed_source():
    with tempfile.TemporaryDirectory() as tmp:
        cfg = _cfg(tmp)

        def gather(_plan, _seen):
            return [
                Source(url="http://a.example", title="A", text="usable content", status="ok"),
                Source(url="http://b.example", title="B", status="fetch_error", error="boom"),
                # walled social source that never resolved a login (US2 path, FR/SC)
                Source(url="http://x.com/post", title="walled", kind="social", status="login_skipped"),
            ]

        path = pipeline.run("Test Topic", cfg, StubLLM(), gather, state_dir=str(Path(tmp) / ".state"))
        text = path.read_text(encoding="utf-8")

        # Required sections always present (SC-002)
        for header in ("## Summary & Key Findings", "## Per-Source Analysis", "## Sources", "## Steps Taken"):
            assert header in text, f"missing section: {header}"

        # The good source is analyzed; the failed source survives in the appendix (FR-013/SC-004)
        assert "http://a.example" in text
        assert "positive" in text
        assert "4/5" in text
        assert "http://b.example" in text
        assert "## Appendix: Skipped or Failed Sources" in text
        # Walled-but-unresolved social source stays login_skipped in the appendix (US2)
        assert "http://x.com/post" in text
        assert "login_skipped" in text


def test_competitive_sentiment_tally_covers_all_brands():
    brands = ["Brand A", "Brand B"]
    with tempfile.TemporaryDirectory() as tmp:
        cfg = _cfg(tmp, brand="Brand A", competitors=["Brand B"])

        def gather(_plan, _seen):
            return [
                Source(url="http://1", title="Brand A", text="a1", status="ok"),
                Source(url="http://2", title="Brand A", text="a2", status="ok"),
                Source(url="http://3", title="Brand B", text="b1", status="ok"),
            ]

        path = pipeline.run("brief", cfg, StubLLM(brands), gather, brand="Brand A", state_dir=str(Path(tmp) / ".state"))
        text = path.read_text(encoding="utf-8")

        assert "## Competitive Sentiment" in text
        # Per-brand tally: A has 2 positive mentions, B has 1; both brands appear (SC-001)
        assert "| Brand A | 2 | 0 | 0 | 2 | 4.0 |" in text
        assert "| Brand B | 1 | 0 | 0 | 1 | 4.0 |" in text


def test_dedup_skips_already_seen_url():
    with tempfile.TemporaryDirectory() as tmp:
        cfg = _cfg(tmp)
        state_dir = str(Path(tmp) / ".state")
        slug = report._slug("Test Topic")
        state.save_seen(slug, {"http://seen.example"}, state_dir)

        def gather(_plan, _seen):
            return [
                Source(url="http://seen.example", title="S", text="old", status="ok"),
                Source(url="http://new.example", title="N", text="fresh", status="ok"),
            ]

        path = pipeline.run("Test Topic", cfg, StubLLM(), gather, state_dir=state_dir)
        text = path.read_text(encoding="utf-8")

        assert "http://seen.example" not in text  # already reported -> skipped
        assert "http://new.example" in text
        assert "http://new.example" in state.load_seen(slug, state_dir)  # state grew


if __name__ == "__main__":
    test_pipeline_produces_report_and_survives_failed_source()
    test_competitive_sentiment_tally_covers_all_brands()
    test_dedup_skips_already_seen_url()
    print("ok")
