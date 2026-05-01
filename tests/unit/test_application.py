import pytest
from app.scoring.application import score_bool, score_unit_coverage, score_integration_coverage, score_stress_test


class TestBool:
    def test_enabled_true(self):
        assert score_bool({"enabled": True}) == 100.0

    def test_enabled_false(self):
        assert score_bool({"enabled": False}) == 0.0

    def test_missing_key(self):
        assert score_bool({}) == 0.0


class TestUnitCoverage:
    def test_above_80(self):
        assert score_unit_coverage({"percentage": 88}) == 100.0

    def test_exactly_80(self):
        assert score_unit_coverage({"percentage": 80}) == 100.0

    def test_midpoint_70(self):
        # 50 + (70-60)/20*50 = 50 + 25 = 75
        assert score_unit_coverage({"percentage": 70}) == 75.0

    def test_exactly_60(self):
        assert score_unit_coverage({"percentage": 60}) == 50.0

    def test_midpoint_50(self):
        # 10 + (50-40)/20*40 = 10 + 20 = 30
        assert score_unit_coverage({"percentage": 50}) == 30.0

    def test_exactly_40(self):
        assert score_unit_coverage({"percentage": 40}) == 10.0

    def test_below_40(self):
        assert score_unit_coverage({"percentage": 39}) == 0.0
        assert score_unit_coverage({"percentage": 0}) == 0.0

    def test_missing_key(self):
        assert score_unit_coverage({}) == 0.0


class TestIntegrationCoverage:
    def test_above_60(self):
        assert score_integration_coverage({"percentage": 68}) == 100.0

    def test_exactly_60(self):
        assert score_integration_coverage({"percentage": 60}) == 100.0

    def test_midpoint_50(self):
        # 50 + (50-40)/20*50 = 50 + 25 = 75
        assert score_integration_coverage({"percentage": 50}) == 75.0

    def test_exactly_40(self):
        assert score_integration_coverage({"percentage": 40}) == 50.0

    def test_midpoint_30(self):
        # 10 + (30-20)/20*40 = 10 + 20 = 30
        assert score_integration_coverage({"percentage": 30}) == 30.0

    def test_exactly_20(self):
        assert score_integration_coverage({"percentage": 20}) == 10.0

    def test_below_20(self):
        assert score_integration_coverage({"percentage": 19}) == 0.0
        assert score_integration_coverage({"percentage": 0}) == 0.0


class TestStressTest:
    def test_excellent(self):
        assert score_stress_test({"error_rate": 0.0005, "p95_ms": 310, "checks_pct": 98}) == 100.0

    def test_good(self):
        # error_rate=0.004 → 20pts | p95=670 → 20pts | checks=91 → 15pts
        assert score_stress_test({"error_rate": 0.004, "p95_ms": 670, "checks_pct": 91}) == 55.0

    def test_medium(self):
        # error_rate=0.015 → 0pts | p95=1250 → 10pts | checks=74 → 5pts
        assert score_stress_test({"error_rate": 0.015, "p95_ms": 1250, "checks_pct": 74}) == 15.0

    def test_poor(self):
        assert score_stress_test({"error_rate": 0.04, "p95_ms": 2600, "checks_pct": 52}) == 0.0

    def test_error_rate_boundary_low(self):
        # < 0.001 → 40pts
        assert score_stress_test({"error_rate": 0.0009, "p95_ms": 499, "checks_pct": 95}) == 100.0

    def test_error_rate_boundary_high(self):
        # >= 0.01 → 0pts
        assert score_stress_test({"error_rate": 0.01, "p95_ms": 499, "checks_pct": 95}) == 60.0

    def test_latency_boundaries(self):
        assert score_stress_test({"error_rate": 0.0, "p95_ms": 499,  "checks_pct": 0}) == 75.0  # 40+35
        assert score_stress_test({"error_rate": 0.0, "p95_ms": 500,  "checks_pct": 0}) == 60.0  # 40+20
        assert score_stress_test({"error_rate": 0.0, "p95_ms": 1000, "checks_pct": 0}) == 50.0  # 40+10
        assert score_stress_test({"error_rate": 0.0, "p95_ms": 2000, "checks_pct": 0}) == 40.0  # 40+0

    def test_defaults(self):
        # error_rate=1.0 → 0 | p95=9999 → 0 | checks=0 → 0
        assert score_stress_test({}) == 0.0
