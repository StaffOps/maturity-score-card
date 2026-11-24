"""Slack notification tests: message content, optional blocks and error handling."""
import logging
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.problems import slack
from app.problems.models import ProblemScanResult


def make_result(**overrides) -> ProblemScanResult:
    data = {
        "area": "financial", "team": "payments", "app": "payments-infra",
        "env": "dev", "problem_type": "secret_in_terraform",
        "severity": "critical", "count": 1, "details": [],
        "slack_channel": "#payments-security",
    }
    data.update(overrides)
    return ProblemScanResult(**data)


@pytest.fixture()
def token(monkeypatch):
    monkeypatch.setattr(slack, "SLACK_BOT_TOKEN", "test-token")


@pytest.fixture()
def post():
    with patch("app.problems.slack.httpx.post",
               return_value=MagicMock(json=lambda: {"ok": True})) as mock:
        yield mock


def sent_blocks(post) -> list[dict]:
    return post.call_args.kwargs["json"]["blocks"]


class TestNoToken:
    def test_skips_without_token(self, monkeypatch, post, caplog):
        monkeypatch.setattr(slack, "SLACK_BOT_TOKEN", None)
        with caplog.at_level(logging.WARNING):
            slack.send_slack_alert(make_result())
        post.assert_not_called()
        assert "SLACK_BOT_TOKEN not set" in caplog.text


@pytest.mark.usefixtures("token")
class TestMessage:
    def test_posts_to_channel_with_bearer_token(self, post):
        slack.send_slack_alert(make_result())
        assert post.call_args.args[0] == "https://slack.com/api/chat.postMessage"
        assert post.call_args.kwargs["headers"] == {"Authorization": "Bearer test-token"}
        assert post.call_args.kwargs["json"]["channel"] == "#payments-security"

    def test_header_uses_severity_emoji_and_label(self, post):
        slack.send_slack_alert(make_result(severity="high", problem_type="secret_in_helmchart"))
        header = sent_blocks(post)[0]["text"]["text"]
        assert header == "🟠 Secret em HelmChart detectado"

    def test_unknown_severity_and_type_fall_back(self, post):
        slack.send_slack_alert(make_result(severity="low", problem_type="open_bucket"))
        header = sent_blocks(post)[0]["text"]["text"]
        assert header == "⚠️ open_bucket detectado"

    def test_fields_include_context_and_uppercased_severity(self, post):
        slack.send_slack_alert(make_result(count=3))
        fields = [f["text"] for f in sent_blocks(post)[1]["fields"]]
        assert "*App:*\npayments-infra" in fields
        assert "*Severidade:*\nCRITICAL" in fields
        assert "*Ocorrências:*\n3" in fields

    def test_no_details_or_pipeline_sends_only_header_and_fields(self, post):
        slack.send_slack_alert(make_result())
        assert len(sent_blocks(post)) == 2

    def test_details_formatting_with_optional_parts(self, post):
        slack.send_slack_alert(make_result(details=[
            {"file": "main.tf", "line": 42, "description": "AWS_SECRET_KEY"},
            {"file": "values.yaml"},
        ]))
        text = sent_blocks(post)[2]["text"]["text"]
        assert text == ("*Detalhes:*\n"
                        "• `main.tf` (linha 42): AWS_SECRET_KEY\n"
                        "• `values.yaml`")

    def test_details_capped_at_ten(self, post):
        details = [{"file": f"f{i}.tf"} for i in range(15)]
        slack.send_slack_alert(make_result(count=15, details=details))
        text = sent_blocks(post)[2]["text"]["text"]
        assert text.count("•") == 10
        assert "f9.tf" in text and "f10.tf" not in text

    def test_pipeline_url_block(self, post):
        slack.send_slack_alert(make_result(pipeline_url="https://ci/run/1"))
        assert sent_blocks(post)[-1]["text"]["text"] == "*Pipeline:* https://ci/run/1"


@pytest.mark.usefixtures("token")
class TestErrors:
    def test_slack_api_error_is_logged(self, caplog):
        with patch("app.problems.slack.httpx.post",
                   return_value=MagicMock(json=lambda: {"ok": False, "error": "channel_not_found"})), \
             caplog.at_level(logging.ERROR):
            slack.send_slack_alert(make_result())
        assert "slack api error: channel_not_found" in caplog.text

    def test_transport_failure_does_not_raise(self, caplog):
        with patch("app.problems.slack.httpx.post", side_effect=httpx.ConnectError("down")), \
             caplog.at_level(logging.ERROR):
            slack.send_slack_alert(make_result())
        assert "failed to send slack notification" in caplog.text
