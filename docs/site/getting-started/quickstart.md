# Quickstart

The `example/` directory contains a full local environment with Prometheus, Grafana, and PostgreSQL.

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

Grafana is available at [http://localhost:3000](http://localhost:3000) (admin / admin) and Prometheus at [http://localhost:9090](http://localhost:9090).

The dashboard uses Grafana's Dashboard Schema V2, which the file provisioner rejects. The `grafana-dashboard-loader` service pushes it through the resource API instead, so it appears a few seconds after Grafana starts.

## `example/` contents

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
