"""FastAPI test client and fixtures for GUI tests."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import tomllib
from fastapi.testclient import TestClient

from media_scraper.gui import app, run_state


@pytest.fixture(autouse=True)
def reset_run_state():
    """Reset RunState between tests."""
    run_state.status = "idle"
    run_state.phase = "planning"
    run_state.topic = ""
    run_state.report_path = None
    run_state.error_message = None
    run_state.started_at = None
    run_state.completed_at = None
    run_state.llm = None
    run_state._cancel_event.clear()
    yield
    # Cleanup after test
    run_state.status = "idle"
    run_state.phase = "planning"
    run_state.topic = ""
    run_state.report_path = None
    run_state.error_message = None
    run_state.started_at = None
    run_state.completed_at = None
    run_state.llm = None
    run_state._cancel_event.clear()


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def temp_config(tmp_path):
    """Create a temporary config.toml for testing."""
    config_data = {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "output_dir": str(tmp_path / "reports"),
        "user_data_dir": str(tmp_path / ".browser-profile"),
        "headless": False,
        "max_sources": 12,
        "max_chars_per_source": 8000,
    }
    config_file = tmp_path / "config.toml"
    lines = []
    for k, v in config_data.items():
        if isinstance(v, bool):
            rendered = "true" if v else "false"
        elif isinstance(v, (int, float)):
            rendered = str(v)
        else:
            rendered = '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'
        lines.append(f"{k} = {rendered}")
    config_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config_file


@pytest.fixture(autouse=True)
def use_temp_config(temp_config, monkeypatch):
    """Use the temp config file for all tests."""
    monkeypatch.setattr("media_scraper.gui.CONFIG_PATH", str(temp_config))
    monkeypatch.delenv("MEDIA_SCRAPER_API_KEY", raising=False)
    monkeypatch.setenv("MEDIA_SCRAPER_API_KEY", "sk-test-key-12345")


@pytest.fixture
def stub_llm():
    """Create a stub LLM for testing pipeline calls."""
    from media_scraper.models import ResearchPlan, SourceAnalysis

    llm = MagicMock()

    def mock_plan(topic):
        return ResearchPlan(
            topic=topic,
            sub_questions=[f"What is {topic}?"],
            search_queries=[topic],
            rss_feeds=[],
            target_sites=[],
        )

    def mock_analyze(source):
        return SourceAnalysis(
            url=source.url,
            claims=["Test claim"],
            sentiment="neutral",
            credibility=3,
            credibility_rationale="Standard source.",
        )

    llm.plan.side_effect = mock_plan
    llm.analyze.side_effect = mock_analyze
    llm.synthesize.return_value = "## Summary\n\nNo findings."
    return llm
