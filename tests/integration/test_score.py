import pytest

BASE = {"area": "financial", "team": "payments", "app": "payments-api", "env": "dev"}


class TestScoreEndpoint:
    def test_image_scan_perfect(self, client):
        r = client.post("/score", json={**BASE, "scorecard": "security", "metric": "image_scan",
                                        "raw": {"critical": 0, "high": 0, "medium": 0}})
        assert r.status_code == 200
        assert r.json()["score"] == 100.0

    def test_image_scan_with_vulnerabilities(self, client):
        r = client.post("/score", json={**BASE, "scorecard": "security", "metric": "image_scan",
                                        "raw": {"critical": 1, "high": 2, "medium": 5}})
        assert r.status_code == 200
        assert r.json()["score"] == 40.0

    def test_secret_scan_found(self, client):
        r = client.post("/score", json={**BASE, "scorecard": "security", "metric": "secret_scan",
                                        "raw": {"found": True}})
        assert r.status_code == 200
        assert r.json()["score"] == 0.0

    def test_secret_scan_clean(self, client):
        r = client.post("/score", json={**BASE, "scorecard": "security", "metric": "secret_scan",
                                        "raw": {"found": False}})
        assert r.status_code == 200
        assert r.json()["score"] == 100.0

    def test_health_check_enabled(self, client):
        r = client.post("/score", json={**BASE, "scorecard": "application", "metric": "health_check",
                                        "raw": {"enabled": True}})
        assert r.status_code == 200
        assert r.json()["score"] == 100.0

    def test_unit_coverage_below_threshold(self, client):
        r = client.post("/score", json={**BASE, "scorecard": "application", "metric": "unit_coverage",
                                        "raw": {"percentage": 30}})
        assert r.status_code == 200
        assert r.json()["score"] == 0.0

    def test_sla_within_target(self, client):
        r = client.post("/score", json={**BASE, "scorecard": "reliability", "metric": "sla",
                                        "raw": {"availability_pct": 99.9}})
        assert r.status_code == 200
        assert r.json()["score"] == 100.0

    def test_sla_below_target(self, client):
        r = client.post("/score", json={**BASE, "scorecard": "reliability", "metric": "sla",
                                        "raw": {"availability_pct": 97.5}})
        assert r.status_code == 200
        assert round(r.json()["score"], 2) == 41.67

    def test_response_contains_labels(self, client):
        r = client.post("/score", json={**BASE, "scorecard": "reliability", "metric": "mttr",
                                        "raw": {"minutes": 30}})
        body = r.json()
        assert body["area"] == "financial"
        assert body["team"] == "payments"
        assert body["app"] == "payments-api"
        assert body["scorecard"] == "reliability"
        assert body["metric"] == "mttr"

    def test_unknown_metric_returns_400(self, client):
        r = client.post("/score", json={**BASE, "scorecard": "security", "metric": "nonexistent",
                                        "raw": {}})
        assert r.status_code == 400
        assert "unknown metric" in r.json()["detail"]

    def test_missing_required_field_returns_422(self, client):
        r = client.post("/score", json={"app": "payments-api", "metric": "image_scan", "raw": {}})
        assert r.status_code == 422

    def test_pipeline_id_is_optional(self, client):
        r = client.post("/score", json={**BASE, "scorecard": "security", "metric": "secret_scan",
                                        "raw": {"found": False}, "pipeline_id": "ci-123"})
        assert r.status_code == 200

    def test_all_scorecards_accepted(self, client):
        cases = [
            ("security",    "secret_scan",         {"found": False}),
            ("application", "health_check",         {"enabled": True}),
            ("reliability", "sla",                  {"availability_pct": 99.9}),
            ("reliability", "mttr",                 {"minutes": 30}),
            ("reliability", "mttd",                 {"minutes": 3}),
        ]
        for scorecard, metric, raw in cases:
            r = client.post("/score", json={**BASE, "scorecard": scorecard, "metric": metric, "raw": raw})
            assert r.status_code == 200, f"failed for {scorecard}/{metric}"


class TestHealthEndpoint:
    def test_healthz(self, client):
        r = client.get("/healthz")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


class TestMetricsEndpoint:
    def test_metrics_returns_prometheus_format(self, client):
        r = client.get("/metrics")
        assert r.status_code == 200
        assert "text/plain" in r.headers["content-type"]

    def test_metrics_includes_scores_from_db(self, client):
        from unittest.mock import patch
        row = ("fin", "pay", "api", "prod", "security", "image_scan", 95.0, 0.25, {"critical": 0})
        with patch("app.metrics.get_all_scores", return_value=[row]):
            r = client.get("/metrics")
        assert "maturity_score" in r.text
        assert 'scorecard="security"' in r.text

    def test_metrics_includes_problems_from_db(self, client):
        from unittest.mock import patch
        row = ("fin", "pay", "infra", "prod", "terraform_secret", "critical", 2)
        with patch("app.metrics.get_all_problems", return_value=[row]):
            r = client.get("/metrics")
        assert "maturity_problem_count" in r.text
        assert 'severity="critical"' in r.text
