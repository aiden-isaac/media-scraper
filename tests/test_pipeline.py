"""Stub-LLM pipeline check (constitution Principle V). No network or browser needed.

Run directly:  python tests/test_pipeline.py
Or with pytest: python -m pytest tests/test_pipeline.py
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from media_scraper import pipeline  # noqa: E402
from media_scraper.models import Config, ResearchPlan, Source, SourceAnalysis  # noqa: E402


class StubLLM:
    def plan(self, topic):
        return ResearchPlan(
            topic=topic,
            sub_questions=["What is X?"],
            search_queries=["X overview"],
        )

    def analyze(self, source):
        return SourceAnalysis(
            url=source.url,
            claims=["claim one"],
            sentiment="positive",
            credibility=4,
            credibility_rationale="reputable outlet",
        )

    def synthesize(self, topic, plan, analyzed):
        return "## Summary\nA short summary.\n\n## Key Findings\n- finding one"


def test_pipeline_produces_report_and_survives_failed_source():
    with tempfile.TemporaryDirectory() as tmp:
        cfg = Config(
            base_url="http://x",
            model="stub",
            api_key="k",
            output_dir=Path(tmp) / "reports",
            user_data_dir=Path(tmp) / "profile",
            max_sources=10,
            max_chars_per_source=8000,
        )
        cfg.output_dir.mkdir(parents=True, exist_ok=True)

        def gather(_plan):
            return [
                Source(url="http://a.example", title="A", text="usable content", status="ok"),
                Source(url="http://b.example", title="B", status="fetch_error", error="boom"),
            ]

        path = pipeline.run("Test Topic", cfg, StubLLM(), gather)
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


if __name__ == "__main__":
    test_pipeline_produces_report_and_survives_failed_source()
    print("ok")
