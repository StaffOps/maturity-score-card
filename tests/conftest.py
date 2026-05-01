import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    with patch("app.database.init_db"), \
         patch("app.database.upsert_score"), \
         patch("app.database.upsert_problem"), \
         patch("app.metrics.get_all_scores", return_value=[]), \
         patch("app.metrics.get_all_problems", return_value=[]):
        from app.main import app
        yield TestClient(app)


@pytest.fixture(autouse=True)
def mock_external():
    """Bloqueia chamadas externas (Slack)."""
    with patch("app.problems.slack.httpx.post",
               return_value=MagicMock(json=lambda: {"ok": True})):
        yield
