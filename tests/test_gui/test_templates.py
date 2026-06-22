"""Tests for HTML template rendering."""


class TestIndexPage:
    """Test the home page (index.html)."""

    def test_index_page_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_index_contains_topic_form(self, client):
        resp = client.get("/")
        html = resp.text
        assert 'id="topic"' in html or 'name="topic"' in html
        assert "Start Research" in html
        assert "Research Topic" in html

    def test_index_contains_progress_section(self, client):
        resp = client.get("/")
        html = resp.text
        assert "planning" in html.lower() or "phase" in html.lower()


class TestConfigPage:
    """Test the configuration page (config.html)."""

    def test_config_page_returns_200(self, client):
        resp = client.get("/config")
        assert resp.status_code == 200

    def test_config_page_shows_fields(self, client):
        resp = client.get("/config")
        html = resp.text
        assert "base_url" in html or "LLM Endpoint" in html
        assert "model" in html.lower() or "Model" in html
        assert "output_dir" in html or "Output" in html
        assert "headless" in html.lower() or "Headless" in html

    def test_api_key_is_masked_in_page(self, client):
        resp = client.get("/config")
        html = resp.text
        # API key value should never appear in HTML
        assert "sk-test-key-12345" not in html
        assert "test-key" not in html


class TestReportsPage:
    """Test the reports listing page (reports.html)."""

    def test_reports_page_returns_200(self, client):
        resp = client.get("/reports")
        assert resp.status_code == 200

    def test_reports_shows_empty_message_when_no_reports(self, client):
        resp = client.get("/reports")
        html = resp.text
        assert "no reports" in html.lower() or "No reports" in html


class TestReportViewer:
    """Test the report viewer page (report.html)."""

    def test_report_viewer_404_for_missing_file(self, client):
        resp = client.get("/report/nonexistent-file.md")
        assert resp.status_code == 404

    def test_report_viewer_rejects_path_traversal(self, client):
        resp = client.get("/report/../../etc/passwd.md")
        assert resp.status_code == 404

    def test_report_viewer_rejects_slash_in_filename(self, client):
        resp = client.get("/report/foo/bar.md")
        assert resp.status_code == 404


class TestBaseTemplate:
    """Test base.html template structure."""

    def test_navbar_present(self, client):
        resp = client.get("/")
        html = resp.text
        assert "Media Scraper" in html
        assert "Home" in html
        assert "Settings" in html
        assert "Reports" in html

    def test_css_is_linked(self, client):
        resp = client.get("/")
        html = resp.text
        assert "/static/style.css" in html

    def test_version_shown(self, client):
        resp = client.get("/")
        html = resp.text
        assert "0.1.0" in html
