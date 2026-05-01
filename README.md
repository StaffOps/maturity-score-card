# maturity-score-card

A stateless FastAPI service that receives CI/CD tool results, computes maturity scores (0–100) per metric, and persists state in PostgreSQL. Metrics are scraped by VictoriaMetrics and visualized in Grafana.

## Architecture

```
CI/CD step
    │
    ▼
POST /score              POST /problem/scan-result
    │                           │
    ▼                           ▼
calculate_score()        save problem state
    │                           │
    └──────────┬────────────────┘
               ▼
          PostgreSQL  ◄──── upsert (state persists until next scan)
               │
               ▼
          GET /metrics  ◄──── VictoriaMetrics scrapes every 15s
               │
               ▼
          vmalert  ──── evaluates recording rules ──► VictoriaMetrics
               │
               ▼
            Grafana
```

## Stack

| Service | Role |
|---|---|
| FastAPI | REST API — scoring + problem intake |
| PostgreSQL | State store — latest score and problem count per app |
| VictoriaMetrics | Time series database — scrapes `/metrics` |
| vmalert | Evaluates PromQL recording rules |
| Grafana | Dashboards |

## Quick start

The `example/` directory contains a full local environment with VictoriaMetrics, vmalert, Grafana, and PostgreSQL.

```bash
cd example

# Start all services (builds the API from the repo root)
docker compose up --build -d

# Submit a score
curl -X POST http://localhost:8080/score \
  -H "Content-Type: application/json" \
  -d '{
    "area": "financial",
    "team": "payments",
    "app": "payments-api",
    "env": "prod",
    "scorecard": "security",
    "metric": "image_scan",
    "raw": {"critical": 0, "high": 1, "medium": 3}
  }'

# Check exposed metrics
curl http://localhost:8080/metrics

# Populate with sample data
bash mock.sh
```

Grafana is available at [http://localhost:3000](http://localhost:3000) (admin / admin).

### example/ contents

| Path | Description |
|---|---|
| `docker-compose.yml` | Full local stack (API, PostgreSQL, VictoriaMetrics, vmalert, Grafana) |
| `prometheus/rules/` | vmalert recording rules |
| `prometheus/scrape.yml` | VictoriaMetrics scrape config |
| `grafana/` | Provisioned datasource and dashboard |
| `mock.sh` | Populates all areas/teams/apps with varied scores and problems |
| `mock_warehouse.sh` | Warehouse team sample data with quality evolution snapshots |
| `mock_problems.sh` | Simulates a scan round: resolves existing problems, opens new ones |

## Scorecards and weights

| Scorecard | Weight | Metrics |
|---|---|---|
| `security` | 35% | `image_scan` (25%), `secret_scan` (25%), `sast` (25%), `dast` (25%) |
| `application` | 25% | `libs_secrets` (15%), `libs_observability` (15%), `unique_db_user` (10%), `health_check` (10%), `unit_coverage` (20%), `integration_coverage` (20%), `stress_test` (10%) |
| `reliability` | 40% | `sla` (20%), `change_failure_rate` (30%), `mttr` (25%), `mttd` (25%) |

Weights redistribute automatically among metrics that actually ran — just omit a metric to exclude it from the calculation.

## Pipeline integration

See **[docs/pipeline-curl-examples.md](docs/pipeline-curl-examples.md)** for one curl example per metric, including scoring rules, partial evaluation patterns, and GitHub Actions / GitLab CI snippets.

## API endpoints

### `POST /score`

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
  "pipeline_id": "ci-456"
}
```

### `POST /problem/scan-result`

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

### `GET /metrics`

Prometheus-format metrics endpoint scraped by VictoriaMetrics.

### `GET /healthz`

Health check.

## Exposed metrics

| Metric | Description | Labels |
|---|---|---|
| `maturity_score` | Computed score (0–100) | area, team, app, env, scorecard, metric |
| `maturity_applicable` | 1 if metric ran in this pipeline | area, team, app, env, scorecard, metric |
| `maturity_weight` | Metric weight within its scorecard | area, team, app, env, scorecard, metric |
| `maturity_raw` | Raw input value per field | area, team, app, env, scorecard, metric, field |
| `maturity_problem_count` | Open problems (0 = clean) | area, team, app, env, problem_type, severity |

## Recording rules (vmalert)

| Metric | Description |
|---|---|
| `maturity:scorecard_score` | Weighted score per scorecard per app |
| `maturity:total_score` | Total weighted score per app |
| `maturity:team_score` | Average total score per team |
| `maturity:area_score` | Average of team scores per area |
| `maturity:team_scorecard_score` | Average scorecard score per team |
| `maturity:area_scorecard_score` | Average scorecard score per area |
| `maturity:problems_by_area` | Total open problems per area |
| `maturity:problems_by_team` | Total open problems per team |
| `maturity:apps_with_problems` | Count of apps with at least one open problem |

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL DSN (required) |
| `SLACK_BOT_TOKEN` | — | Slack bot token for problem alerts (optional) |

Local default (docker compose): `postgresql://maturity:maturity@postgres:5432/maturity`

## Adding a new metric

1. Create the scoring function in `app/scoring/<scorecard>.py`
2. Register it in `SCORERS` in `app/scoring/__init__.py`
3. Add the weight in `app/weights.py`

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Run tests
pytest

# Run locally (requires a running PostgreSQL)
DATABASE_URL=postgresql://... uvicorn app.main:app --reload --port 8080
```
