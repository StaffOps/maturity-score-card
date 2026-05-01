import pytest
from app.scoring.security import score_image_scan, score_secret_scan, score_sast, score_dast


class TestImageScan:
    def test_perfect(self):
        assert score_image_scan({"critical": 0, "high": 0, "medium": 0}) == 100.0

    def test_only_medium(self):
        assert score_image_scan({"critical": 0, "high": 0, "medium": 1}) == 97.0

    def test_mixed(self):
        # 100 - (1*25) - (2*10) - (5*3) = 100 - 25 - 20 - 15 = 40
        assert score_image_scan({"critical": 1, "high": 2, "medium": 5}) == 40.0

    def test_clamps_at_zero(self):
        assert score_image_scan({"critical": 10, "high": 10, "medium": 10}) == 0.0

    def test_empty_raw(self):
        assert score_image_scan({}) == 100.0

    def test_single_critical(self):
        assert score_image_scan({"critical": 1}) == 75.0

    def test_four_criticals_zeroes_out(self):
        assert score_image_scan({"critical": 4}) == 0.0


class TestSecretScan:
    def test_no_secrets(self):
        assert score_secret_scan({"found": False}) == 100.0

    def test_secrets_found(self):
        assert score_secret_scan({"found": True}) == 0.0

    def test_default_no_secrets(self):
        assert score_secret_scan({}) == 100.0


class TestSAST:
    def test_perfect(self):
        assert score_sast({"critical": 0, "high": 0, "medium": 0}) == 100.0

    def test_mixed(self):
        assert score_sast({"critical": 1, "high": 2, "medium": 5}) == 40.0

    def test_clamps_at_zero(self):
        assert score_sast({"critical": 10, "high": 10, "medium": 10}) == 0.0

    def test_empty_raw(self):
        assert score_sast({}) == 100.0


class TestDAST:
    def test_perfect(self):
        assert score_dast({"high": 0, "medium": 0}) == 100.0

    def test_one_high(self):
        assert score_dast({"high": 1, "medium": 0}) == 80.0

    def test_mixed(self):
        # 100 - (2*20) - (4*5) = 100 - 40 - 20 = 40
        assert score_dast({"high": 2, "medium": 4}) == 40.0

    def test_clamps_at_zero(self):
        assert score_dast({"high": 10, "medium": 10}) == 0.0

    def test_empty_raw(self):
        assert score_dast({}) == 100.0
