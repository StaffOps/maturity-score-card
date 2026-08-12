# maturity-score-card

**A single 0–100 number for how well an application is built, shipped, and run.**

Test coverage lives in one tool, vulnerabilities in another, availability in a dashboard, incident response in a spreadsheet. This service collects those signals wherever they already exist, scores each on the same 0–100 scale, and rolls them up per app, per team, and per area.

It is not a CI/CD scorecard — pipelines are one source of signal among several, and the heaviest scorecard measures what happens *after* deploy:

| Dimension | Scorecard | Weight | Answers |
|---|---|---|---|
| **Build** | `application` | 25% | Is it tested? Instrumented? Does it hold up under load? |
| **Ship** | `security` | 35% | What did we catch before it reached production? |
| **Run** | `reliability` | 40% | Does it stay up? How fast do we notice and recover? |

Fifteen metrics ship in the box, covering SLA/availability, change failure rate, MTTD/MTTR, image and source vulnerability scanning, secret detection, unit and integration coverage, and load-test behaviour. Anything expressible as a number at the end of a job, a query, or a report can feed it — a pipeline step, a nightly cron against Prometheus, a scheduled scan, a manual audit.

Findings that need fixing (not just scoring) go to `POST /problem/scan-result`, which keeps them with file and line detail until a later scan reports zero, and alerts Slack when something new appears.

See **[Scorecards](docs/site/scorecards.md)** for every metric's payload and thresholds, and the **[Roadmap](docs/site/roadmap.md)** for what is specified next, what is deliberately a dashboard panel rather than a scored metric, and what is not planned.

A stateless FastAPI service; all state lives in PostgreSQL. Metrics are scraped by Prometheus and visualized in Grafana.

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
          GET /metrics  ◄──── Prometheus scrapes every 15s
               │
               ▼
          Prometheus  ──── evaluates PromQL recording rules
               │
               ▼
            Grafana
```

## Stack

| Service | Role |
|---|---|
| FastAPI | REST API — scoring + problem intake |
| PostgreSQL | State store — latest score and problem count per app |
| Prometheus | Time series database — scrapes `/metrics` and evaluates recording rules |
| Grafana | Dashboards |

## Quick start

The `example/` directory contains a full local environment with Prometheus, Grafana, and PostgreSQL.

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

Grafana is available at [http://localhost:3000](http://localhost:3000) (admin / admin) and Prometheus at [http://localhost:9090](http://localhost:9090).

The dashboard uses Grafana's Dashboard Schema V2, which the file provisioner rejects. The `grafana-dashboard-loader` service pushes it through the resource API instead, so it appears a few seconds after Grafana starts.

### example/ contents

| Path | Description |
|---|---|
| `docker-compose.yml` | Full local stack (API, PostgreSQL, Prometheus, Grafana) |
| `prometheus/prometheus.yml` | Prometheus scrape config and rule file discovery |
| `prometheus/rules/` | PromQL recording rules |
| `grafana/provisioning/` | Provisioned Prometheus datasource |
| `grafana/dashboards/maturity.json` | Dashboard (Schema V2, 3 tabs) — source of truth |
| `grafana/push-dashboard.py` | Pushes the V2 dashboard via the Grafana resource API |
| `mock.sh` | Populates all areas/teams/apps with varied scores and problems |
| `mock_warehouse.sh` | Warehouse team sample data with quality evolution snapshots |
| `mock_problems.sh` | Simulates a scan round: resolves existing problems, opens new ones |

## Scorecards and weights

| Scorecard | Weight | Metrics |
|---|---|---|
| `security` | 35% | `image_scan` (25%), `secret_scan` (25%), `sast` (25%), `dast` (25%) |
| `application` | 25% | `libs_secrets` (15%), `libs_observability` (15%), `unique_db_user` (10%), `health_check` (10%), `unit_coverage` (20%), `integration_coverage` (20%), `stress_test` (10%) |
| `reliability` | 40% | `sla` (20%), `change_failure_rate` (30%), `mttr` (25%), `mttd` (25%) |

Weights redistribute automatically among metrics that actually ran — just omit a metric to exclude it from the calculation. A scorecard is the weighted average of the metrics that reported (`Σ(score × weight) / Σ(weight)`), so a service with no DAST is judged on what it does run rather than penalised for the gap.

Team and area scores are plain averages, one level at a time — apps into teams, teams into areas — so a 40-service team does not swamp a 3-service one.

Full payloads and thresholds per metric: **[docs/site/scorecards.md](docs/site/scorecards.md)**.

## Data sources

Values can come from anywhere that produces a number:

| Source | Typical metrics |
|---|---|
| CI/CD pipeline step | `unit_coverage`, `integration_coverage`, `image_scan`, `sast`, `secret_scan` |
| Scheduled job against Prometheus/Grafana | `sla`, `mttd`, `mttr`, `change_failure_rate` |
| Load-test stage or nightly run | `stress_test` |
| Scanner or manual audit | `dast`, the boolean practice checks |

Submitting a metric that is not registered in `SCORERS` returns `400 unknown metric`.

## Pipeline integration

See **[docs/site/reference/pipeline-integration.md](docs/site/reference/pipeline-integration.md)** for one curl example per metric, including scoring rules, partial evaluation patterns, and GitHub Actions / GitLab CI snippets.

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
  "pipeline_id": "ci-456",
  "project_repo": "org/payments-api"
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

Prometheus-format metrics endpoint scraped by Prometheus.

### `GET /healthz`

Health check.

## Exposed metrics

| Metric | Description | Labels |
|---|---|---|
| `maturity_score` | Computed score (0–100) | area, team, app, env, scorecard, metric, project_repo |
| `maturity_applicable` | 1 if metric ran in this pipeline | area, team, app, env, scorecard, metric, project_repo |
| `maturity_weight` | Metric weight within its scorecard | area, team, app, env, scorecard, metric, project_repo |
| `maturity_raw` | Raw input value per field | area, team, app, env, scorecard, metric, project_repo, field |
| `maturity_problem_count` | Open problems (0 = clean) | area, team, app, env, problem_type, severity |
| `maturity_project_info` | Source repo of an app, always `1` — join target for `group_left` | area, team, app, env, project_repo |

## Recording rules (PromQL)

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
