from pydantic import BaseModel


class ScoreRequest(BaseModel):
    area: str
    team: str
    app: str
    env: str
    scorecard: str  # security | application | reliability | incident
    metric: str
    raw: dict
    pipeline_id: str | None = None
