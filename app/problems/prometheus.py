import logging
from app.problems.models import ProblemScanResult
from app.database import upsert_problem

logger = logging.getLogger(__name__)


def push_problem_metrics(result: ProblemScanResult) -> None:
    try:
        details = [d.model_dump() if hasattr(d, "model_dump") else d for d in (result.details or [])]
        upsert_problem(
            result.area, result.team, result.app, result.env,
            result.problem_type, result.severity, result.count,
            details,
        )
    except Exception:
        logger.exception("failed to save problem to database")
