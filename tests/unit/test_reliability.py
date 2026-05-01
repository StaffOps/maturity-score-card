from app.scoring.reliability import score_sla, score_change_failure_rate


class TestSLA:
    def test_above_99_5(self):
        assert score_sla({"availability_pct": 99.95}) == 100.0
        assert score_sla({"availability_pct": 99.5}) == 100.0

    def test_between_99_and_99_5(self):
        assert score_sla({"availability_pct": 99.49}) == 75.0
        assert score_sla({"availability_pct": 99.0}) == 75.0

    def test_between_98_and_99(self):
        assert score_sla({"availability_pct": 98.99}) == 50.0
        assert score_sla({"availability_pct": 98.0}) == 50.0

    def test_proportional_below_98(self):
        # (97.5 - 95) / 3 * 50 = 41.666...
        result = score_sla({"availability_pct": 97.5})
        assert round(result, 2) == 41.67

    def test_zero_at_95(self):
        assert score_sla({"availability_pct": 95.0}) == 0.0

    def test_clamps_at_zero_below_95(self):
        assert score_sla({"availability_pct": 90.0}) == 0.0
        assert score_sla({"availability_pct": 0.0}) == 0.0

    def test_missing_key(self):
        assert score_sla({}) == 0.0


class TestChangeFailureRate:
    def test_elite_below_5(self):
        assert score_change_failure_rate({"rate_pct": 2}) == 100.0
        assert score_change_failure_rate({"rate_pct": 4.99}) == 100.0

    def test_high_5_to_10(self):
        assert score_change_failure_rate({"rate_pct": 5}) == 75.0
        assert score_change_failure_rate({"rate_pct": 9.99}) == 75.0

    def test_medium_10_to_15(self):
        assert score_change_failure_rate({"rate_pct": 10}) == 50.0
        assert score_change_failure_rate({"rate_pct": 14.99}) == 50.0

    def test_low_above_15(self):
        assert score_change_failure_rate({"rate_pct": 15}) == 25.0
        assert score_change_failure_rate({"rate_pct": 100}) == 25.0

    def test_default_is_worst(self):
        assert score_change_failure_rate({}) == 25.0
