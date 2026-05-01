import os
import logging
import httpx
from app.problems.models import ProblemScanResult

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
logger = logging.getLogger(__name__)

_SEVERITY_EMOJI = {"critical": "🔴", "high": "🟠", "medium": "🟡"}

_PROBLEM_LABELS = {
    "secret_in_terraform": "Secret em Terraform",
    "secret_in_helmchart": "Secret em HelmChart",
}


def send_slack_alert(result: ProblemScanResult) -> None:
    if not SLACK_BOT_TOKEN:
        logger.warning("SLACK_BOT_TOKEN not set, skipping slack notification")
        return

    emoji = _SEVERITY_EMOJI.get(result.severity, "⚠️")
    label = _PROBLEM_LABELS.get(result.problem_type, result.problem_type)

    detail_lines = "\n".join(
        f"• `{d.file}`{f' (linha {d.line})' if d.line else ''}{f': {d.description}' if d.description else ''}"
        for d in result.details[:10]
    )

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{emoji} {label} detectado"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Área:*\n{result.area}"},
                {"type": "mrkdwn", "text": f"*Time:*\n{result.team}"},
                {"type": "mrkdwn", "text": f"*App:*\n{result.app}"},
                {"type": "mrkdwn", "text": f"*Env:*\n{result.env}"},
                {"type": "mrkdwn", "text": f"*Severidade:*\n{result.severity.upper()}"},
                {"type": "mrkdwn", "text": f"*Ocorrências:*\n{result.count}"},
            ],
        },
    ]

    if detail_lines:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Detalhes:*\n{detail_lines}"},
        })

    if result.pipeline_url:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Pipeline:* {result.pipeline_url}"},
        })

    try:
        response = httpx.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
            json={"channel": result.slack_channel, "blocks": blocks},
            timeout=5.0,
        )
        data = response.json()
        if not data.get("ok"):
            logger.error("slack api error: %s", data.get("error"))
    except Exception:
        logger.exception("failed to send slack notification")
