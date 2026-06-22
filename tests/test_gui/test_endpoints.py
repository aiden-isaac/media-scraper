"""Tests for all /api/ endpoint routes."""

from unittest.mock import MagicMock, patch

import pytest


class TestGetConfig:
    """Test GET /api/config endpoint."""

    def test_returns_config_without_api_key(self, client):
        resp = client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "base_url" in data
        assert "model" in data
        assert "output_dir" in data
        assert "headless" in data
        assert "max_sources" in data
        assert "max_chars_per_source" in data
        assert "api_key_set" in data
        # API key value should never appear
        assert data["api_key_set"] is True
        assert "sk-test" not in str(data)

    def test_api_key_set_false_when_no_key(self, client, monkeypatch):
        monkeypatch.delenv("MEDIA_SCRAPER_API_KEY", raising=False)
        resp = client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["api_key_set"] is False


class TestUpdateConfig:
    """Test PUT /api/config endpoint."""

    def test_updates_single_field(self, client):
        resp = client.put("/api/config", json={"model": "gpt-4o-mini"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["config"]["model"] == "gpt-4o-mini"

    def test_updates_multiple_fields(self, client):
        payload = {"model": "claude-3-opus", "max_sources": 5}
        resp = client.put("/api/config", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["config"]["model"] == "claude-3-opus"
        assert data["config"]["max_sources"] == 5

    def test_rejects_api_key_in_request(self, client):
        resp = client.put("/api/config", json={"api_key": "sk-secret"})
        assert resp.status_code == 403
        assert "Cannot change API key" in resp.json()["detail"]

    def test_partial_update_keeps_other_fields(self, client):
        # Change only model, verify other fields preserved
        resp = client.put("/api/config", json={"model": "gpt-3.5-turbo"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["config"]["model"] == "gpt-3.5-turbo"
        # headless and max_sources should be unchanged from config.toml
        assert data["config"]["headless"] == False

    def test_validates_headless_is_bool(self, client):
        resp = client.put("/api/config", json={"headless": "yes"})
        assert resp.status_code == 422

    def test_validates_max_sources_is_int(self, client):
        resp = client.put("/api/config", json={"max_sources": "twelve"})
        assert resp.status_code == 422


class TestStartRun:
    """Test POST /api/run/start endpoint."""

    def test_starts_scraper_with_valid_topic(self, client):
        resp = client.post("/api/run/start", json={"topic": "test topic"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "accepted"

    def test_rejects_empty_topic(self, client):
        resp = client.post("/api/run/start", json={"topic": ""})
        assert resp.status_code == 422

    def test_rejects_whitespace_only_topic(self, client):
        resp = client.post("/api/run/start", json={"topic": "   "})
        assert resp.status_code == 422

    def test_rejects_concurrent_runs(self, client):
        # Start first run
        resp1 = client.post("/api/run/start", json={"topic": "first topic"})
        assert resp1.status_code == 201
        # Try to start second while first is running
        resp2 = client.post("/api/run/start", json={"topic": "second topic"})
        assert resp2.status_code == 409
        assert "already in progress" in resp2.json()["detail"]


class TestRunStatus:
    """Test GET /api/run/status endpoint."""

    def test_idle_status(self, client):
        resp = client.get("/api/run/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "idle"
        assert data["phase"] == "planning"
        assert data["topic"] == ""

    def test_running_status_after_start(self, client):
        client.post("/api/run/start", json={"topic": "polling test"})
        resp = client.get("/api/run/status")
        data = resp.json()
        assert data["status"] == "running"
        assert data["topic"] == "polling test"
        assert data["started_at"] is not None


class TestCancelRun:
    """Test POST /api/run/cancel endpoint."""

    def test_cancel_active_run(self, client):
        client.post("/api/run/start", json={"topic": "cancel me"})
        resp = client.post("/api/run/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "cancelled"

    def test_rejects_cancel_when_idle(self, client):
        resp = client.post("/api/run/cancel")
        assert resp.status_code == 400
        assert "No scraper run is currently active" in resp.json()["detail"]


class TestReportsEndpoints:
    """Test report listing and content endpoints."""

    def test_list_reports_empty(self, client):
        resp = client.get("/api/reports")
        assert resp.status_code == 200
        data = resp.json()
        assert data["reports"] == []
        assert data["total"] == 0

    def test_report_content_not_found(self, client):
        resp = client.get("/api/reports/nonexistent.md/content")
        assert resp.status_code == 404

    def test_report_content_rejects_path_traversal(self, client):
        resp = client.get("/api/reports/../../../etc/passwd/content")
        assert resp.status_code == 404
