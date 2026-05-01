from app.scoring.incident import score_mttr, score_mttd


class TestMTTR:
    def test_elite_below_1h(self):
        assert score_mttr({"minutes": 35}) == 100.0
        assert score_mttr({"minutes": 59}) == 100.0

    def test_high_1h_to_4h(self):
        assert score_mttr({"minutes": 60}) == 75.0
        assert score_mttr({"minutes": 239}) == 75.0

    def test_medium_4h_to_24h(self):
        assert score_mttr({"minutes": 240}) == 50.0
        assert score_mttr({"minutes": 1439}) == 50.0

    def test_low_above_24h(self):
        assert score_mttr({"minutes": 1440}) == 25.0
        assert score_mttr({"minutes": 2160}) == 25.0

    def test_default_is_worst(self):
        assert score_mttr({}) == 25.0


class TestMTTD:
    def test_elite_below_5min(self):
        assert score_mttd({"minutes": 3}) == 100.0
        assert score_mttd({"minutes": 4}) == 100.0

    def test_high_5_to_30min(self):
        assert score_mttd({"minutes": 5}) == 75.0
        assert score_mttd({"minutes": 29}) == 75.0

    def test_medium_30min_to_2h(self):
        assert score_mttd({"minutes": 30}) == 50.0
        assert score_mttd({"minutes": 119}) == 50.0

    def test_low_above_2h(self):
        assert score_mttd({"minutes": 120}) == 25.0
        assert score_mttd({"minutes": 180}) == 25.0

    def test_default_is_worst(self):
        assert score_mttd({}) == 25.0
