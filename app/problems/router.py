from fastapi import APIRouter
from app.problems.models import ProblemScanResult
from app.problems.prometheus import push_problem_metrics
from app.problems.slack import send_slack_alert

router = APIRouter(prefix="/problem", tags=["problems"])


@router.post("/scan-result")
def submit_scan_result(payload: ProblemScanResult):
    push_problem_metrics(payload)

    notified = False
    if payload.count > 0:
        send_slack_alert(payload)
        notified = True

    return {
        "area": payload.area,
        "team": payload.team,
        "app": payload.app,
        "problem_type": payload.problem_type,
        "count": payload.count,
        "notified": notified,
    }
