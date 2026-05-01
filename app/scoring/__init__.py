from app.models import ScoreRequest
from app.scoring.security import score_image_scan, score_secret_scan, score_sast, score_dast
from app.scoring.application import score_bool, score_unit_coverage, score_integration_coverage, score_stress_test
from app.scoring.reliability import score_sla, score_change_failure_rate
from app.scoring.incident import score_mttr, score_mttd

SCORERS: dict = {
    # security
    "image_scan": score_image_scan,
    "secret_scan": score_secret_scan,
    "sast": score_sast,
    "dast": score_dast,
    # application
    "libs_secrets": score_bool,
    "libs_observability": score_bool,
    "unique_db_user": score_bool,
    "health_check": score_bool,
    "unit_coverage": score_unit_coverage,
    "integration_coverage": score_integration_coverage,
    "stress_test": score_stress_test,
    # reliability
    "sla": score_sla,
    "change_failure_rate": score_change_failure_rate,
    # incident
    "mttr": score_mttr,
    "mttd": score_mttd,
}


def calculate_score(request: ScoreRequest) -> float:
    scorer = SCORERS.get(request.metric)
    if scorer is None:
        raise ValueError(f"unknown metric: {request.metric}")
    return scorer(request.raw)
