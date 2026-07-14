# API Reference

## `POST /score`

Submits a metric result for a single app.

```json
{
  "area": "financial",
  "team": "payments",
  "app": "payments-api",
  "env": "prod",
  "scorecard": "security",
  "metric": "image_scan",
  "raw": {"critical": 0, "high": 1, "medium": 3},
  "pipeline_id": "ci-456",
  "project_repo": "org/payments-api"
}
```

## `POST /problem/scan-result`

Reports infrastructure secrets found by a scanner. State is persisted until the next scan sets `count` to `0`.

```json
{
  "area": "financial",
  "team": "payments",
  "app": "payments-infra",
  "env": "prod",
  "problem_type": "terraform_secret",
  "severity": "critical",
  "count": 2,
  "details": [
    {"file": "infra/main.tf", "line": 42, "description": "AWS_SECRET_KEY"}
  ],
  "slack_channel": "#payments-security"
}
```

Sends a Slack alert when `count > 0` if `SLACK_BOT_TOKEN` is set.

## `GET /metrics`

Prometheus-format metrics endpoint scraped by VictoriaMetrics.

## `GET /healthz`

Health check.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL DSN (required) |
| `SLACK_BOT_TOKEN` | — | Slack bot token for problem alerts (optional) |

Local default (docker compose): `postgresql://maturity:maturity@postgres:5432/maturity`
