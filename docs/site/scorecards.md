# Scorecards and Weights

| Scorecard | Weight | Metrics |
|---|---|---|
| `security` | 35% | `image_scan` (25%), `secret_scan` (25%), `sast` (25%), `dast` (25%) |
| `application` | 25% | `libs_secrets` (15%), `libs_observability` (15%), `unique_db_user` (10%), `health_check` (10%), `unit_coverage` (20%), `integration_coverage` (20%), `stress_test` (10%) |
| `reliability` | 40% | `sla` (20%), `change_failure_rate` (30%), `mttr` (25%), `mttd` (25%) |

Weights redistribute automatically among metrics that actually ran — just omit a metric to exclude it from the calculation.

## Adding a new metric

1. Create the scoring function in `app/scoring/<scorecard>.py`
2. Register it in `SCORERS` in `app/scoring/__init__.py`
3. Add the weight in `app/weights.py`

See [Pipeline Integration](reference/pipeline-integration.md) for curl examples covering every metric.
