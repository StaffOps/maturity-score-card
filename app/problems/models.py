from pydantic import BaseModel


class ProblemDetail(BaseModel):
    file: str | None = None
    line: int | None = None
    description: str | None = None


class ProblemScanResult(BaseModel):
    area: str
    team: str
    app: str
    env: str
    problem_type: str   # secret_in_terraform | secret_in_helmchart | ...
    severity: str       # critical | high | medium
    count: int
    details: list[ProblemDetail] = []
    slack_channel: str  # ex: #payments-security
    pipeline_id: str | None = None
    pipeline_url: str | None = None
