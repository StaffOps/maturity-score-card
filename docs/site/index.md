# Maturity Score Card

**Stateless scoring service for CI/CD maturity metrics.**

Receives CI/CD tool results, computes a 0–100 maturity score per metric, and persists state in PostgreSQL. Metrics are scraped by VictoriaMetrics and visualized in Grafana.

---

## What it does

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

---

## Stack

| Service | Role |
|---|---|
| FastAPI | REST API — scoring + problem intake |
| PostgreSQL | State store — latest score and problem count per app |
| VictoriaMetrics | Time series database — scrapes `/metrics` |
| vmalert | Evaluates PromQL recording rules |
| Grafana | Dashboards |

---

## Key properties

- Stateless API — all state lives in PostgreSQL
- Weights redistribute automatically among metrics that actually ran
- Slack alerts on new infrastructure problems
- Ships with a full local stack (`example/`) for evaluation

[Get started →](getting-started/quickstart.md){ .md-button .md-button--primary }
[Source on GitHub →](https://github.com/StaffOps/maturity-score-card){ .md-button }
