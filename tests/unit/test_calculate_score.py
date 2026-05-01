import pytest
from app.scoring import calculate_score
from app.models import ScoreRequest


def make_request(scorecard: str, metric: str, raw: dict) -> ScoreRequest:
    return ScoreRequest(
        area="financial", team="payments", app="payments-api",
        env="dev", scorecard=scorecard, metric=metric, raw=raw,
    )


class TestCalculateScore:
    def test_all_metrics_resolve(self):
        cases = [
            ("security",    "image_scan",           {"critical": 0, "high": 0, "medium": 0}),
            ("security",    "secret_scan",           {"found": False}),
            ("security",    "sast",                  {"critical": 0, "high": 0, "medium": 0}),
            ("security",    "dast",                  {"high": 0, "medium": 0}),
            ("application", "libs_secrets",          {"enabled": True}),
            ("application", "libs_observability",    {"enabled": True}),
            ("application", "unique_db_user",        {"enabled": True}),
            ("application", "health_check",          {"enabled": True}),
            ("application", "unit_coverage",         {"percentage": 80}),
            ("application", "integration_coverage",  {"percentage": 60}),
            ("application", "stress_test",           {"error_rate": 0.0, "p95_ms": 400, "checks_pct": 100}),
            ("reliability", "sla",                   {"availability_pct": 99.9}),
            ("reliability", "change_failure_rate",   {"rate_pct": 3}),
            ("reliability", "mttr",                  {"minutes": 30}),
            ("reliability", "mttd",                  {"minutes": 4}),
        ]
        for scorecard, metric, raw in cases:
            score = calculate_score(make_request(scorecard, metric, raw))
            assert 0.0 <= score <= 100.0, f"{metric} returned {score}"

    def test_unknown_metric_raises(self):
        with pytest.raises(ValueError, match="unknown metric"):
            calculate_score(make_request("security", "nonexistent_metric", {}))
