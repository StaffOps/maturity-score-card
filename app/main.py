from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST
from app.models import ScoreRequest
from app.scoring import calculate_score
from app.prometheus import push_metrics
from app.problems.router import router as problems_router
from app.database import init_db
from app.metrics import build_metrics

app = FastAPI(title="Maturity Score API", version="0.1.0")
app.include_router(problems_router)


@app.on_event("startup")
def startup():
    init_db()


@app.post("/score")
def submit_score(payload: ScoreRequest):
    try:
        score = calculate_score(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    push_metrics(payload, score)

    return {
        "area": payload.area,
        "team": payload.team,
        "app": payload.app,
        "env": payload.env,
        "scorecard": payload.scorecard,
        "metric": payload.metric,
        "score": round(score, 2),
    }


@app.get("/metrics")
def metrics():
    return Response(content=build_metrics(), media_type=CONTENT_TYPE_LATEST)


@app.get("/healthz")
def health():
    return {"status": "ok"}
