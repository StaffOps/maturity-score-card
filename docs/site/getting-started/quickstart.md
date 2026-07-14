# Quickstart

The `example/` directory contains a full local environment with VictoriaMetrics, vmalert, Grafana, and PostgreSQL.

```bash
git clone https://github.com/StaffOps/maturity-score-card
cd maturity-score-card/example

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

## `example/` contents

| Path | Description |
|---|---|
| `docker-compose.yml` | Full local stack (API, PostgreSQL, VictoriaMetrics, vmalert, Grafana) |
| `prometheus/rules/` | vmalert recording rules |
| `prometheus/scrape.yml` | VictoriaMetrics scrape config |
| `grafana/` | Provisioned datasource and dashboard |
| `mock.sh` | Populates all areas/teams/apps with varied scores and problems |
| `mock_warehouse.sh` | Warehouse team sample data with quality evolution snapshots |
| `mock_problems.sh` | Simulates a scan round: resolves existing problems, opens new ones |
