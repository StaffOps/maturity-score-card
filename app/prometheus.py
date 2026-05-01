import logging
from app.models import ScoreRequest
from app.weights import WEIGHTS
from app.database import upsert_score

logger = logging.getLogger(__name__)


def push_metrics(request: ScoreRequest, score: float) -> None:
    weight = WEIGHTS.get(request.scorecard, {}).get("metrics", {}).get(request.metric, 0.0)
    try:
        upsert_score(
            request.area, request.team, request.app, request.env,
            request.scorecard, request.metric, score, weight, request.raw,
        )
    except Exception:
        logger.exception("failed to save score to database")
