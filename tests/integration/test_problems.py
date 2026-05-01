import pytest

BASE = {
    "area": "financial", "team": "payments", "app": "payments-infra",
    "env": "dev", "slack_channel": "#payments-security",
}


class TestProblemScanResult:
    def test_clean_scan_not_notified(self, client):
        r = client.post("/problem/scan-result", json={
            **BASE, "problem_type": "secret_in_terraform",
            "severity": "critical", "count": 0, "details": [],
        })
        assert r.status_code == 200
        assert r.json()["count"] == 0
        assert r.json()["notified"] is False

    def test_problem_found_is_notified(self, client):
        r = client.post("/problem/scan-result", json={
            **BASE, "problem_type": "secret_in_terraform",
            "severity": "critical", "count": 2,
            "details": [{"file": "infra/main.tf", "line": 42, "description": "AWS_SECRET_KEY"}],
        })
        assert r.status_code == 200
        assert r.json()["count"] == 2
        assert r.json()["notified"] is True

    def test_helmchart_secret(self, client):
        r = client.post("/problem/scan-result", json={
            **BASE, "problem_type": "secret_in_helmchart",
            "severity": "high", "count": 1,
            "details": [{"file": "helm/values.yaml", "line": 15, "description": "DB_PASSWORD"}],
        })
        assert r.status_code == 200
        assert r.json()["notified"] is True

    def test_response_contains_labels(self, client):
        r = client.post("/problem/scan-result", json={
            **BASE, "problem_type": "secret_in_terraform",
            "severity": "high", "count": 1, "details": [],
        })
        body = r.json()
        assert body["area"] == "financial"
        assert body["team"] == "payments"
        assert body["app"] == "payments-infra"
        assert body["problem_type"] == "secret_in_terraform"

    def test_details_are_optional(self, client):
        r = client.post("/problem/scan-result", json={
            **BASE, "problem_type": "secret_in_terraform",
            "severity": "medium", "count": 1,
        })
        assert r.status_code == 200

    def test_missing_required_field_returns_422(self, client):
        r = client.post("/problem/scan-result", json={
            "area": "financial", "team": "payments",
            "problem_type": "secret_in_terraform", "count": 1,
        })
        assert r.status_code == 422

    def test_all_severities_accepted(self, client):
        for severity in ["critical", "high", "medium"]:
            r = client.post("/problem/scan-result", json={
                **BASE, "problem_type": "secret_in_terraform",
                "severity": severity, "count": 0, "details": [],
            })
            assert r.status_code == 200, f"failed for severity={severity}"

    def test_pipeline_url_is_optional(self, client):
        r = client.post("/problem/scan-result", json={
            **BASE, "problem_type": "secret_in_helmchart",
            "severity": "critical", "count": 1, "details": [],
            "pipeline_url": "https://gitlab.com/org/repo/-/pipelines/123",
        })
        assert r.status_code == 200
