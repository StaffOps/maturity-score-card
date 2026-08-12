# Scorecards and Metrics

Every metric is scored 0–100 by a pure function in `app/scoring/`. This page documents what
each one measures, the payload it expects, and the exact thresholds it applies.

| Scorecard | Weight | Metrics |
|---|---|---|
| [`reliability`](#reliability-40) | 40% | `sla` (20%), `change_failure_rate` (30%), `mttr` (25%), `mttd` (25%) |
| [`security`](#security-35) | 35% | `image_scan` (25%), `secret_scan` (25%), `sast` (25%), `dast` (25%) |
| [`application`](#application-25) | 25% | `libs_secrets` (15%), `libs_observability` (15%), `unique_db_user` (10%), `health_check` (10%), `unit_coverage` (20%), `integration_coverage` (20%), `stress_test` (10%) |

!!! info "Weights redistribute automatically"
    Metrics you never submit are excluded from the calculation instead of counting as zero.
    A scorecard's score is the weighted average of the metrics that actually reported, so a
    service with no DAST is judged on what it does run. See [Scoring model](#scoring-model).

---

## reliability (40%)

The heaviest scorecard, and the only one measuring production behaviour. Values here usually
come from a scheduled query against your monitoring stack rather than from a pipeline.

### `sla` — 20%

Availability against your SLO. Feed it whatever figure your SLI already produces; downtime is
expressed through this metric rather than reported separately.

```json
{"availability_pct": 99.82}
```

| Availability | Score |
|---|---|
| ≥ 99.5% | 100 |
| ≥ 99.0% | 75 |
| ≥ 98.0% | 50 |
| 95–98% | Linear 0 → 50 |
| < 95% | 0 |

### `change_failure_rate` — 30%

The DORA metric: share of deploys that caused a degradation requiring a fix or rollback.

```json
{"rate_pct": 4.2}
```

| Failure rate | Score |
|---|---|
| < 5% | 100 |
| < 10% | 75 |
| < 15% | 50 |
| ≥ 15% | 25 |

### `mttd` — 25%

Mean time to **detect**: incident start to the moment someone or something noticed. Scored
much more aggressively than recovery — detection is where most of the avoidable delay lives.

```json
{"minutes": 4}
```

| Detection time | Score |
|---|---|
| < 5 min | 100 |
| < 30 min | 75 |
| < 2 h | 50 |
| ≥ 2 h | 25 |

### `mttr` — 25%

Mean time to **recover**: detection to service restored.

```json
{"minutes": 45}
```

| Recovery time | Score |
|---|---|
| < 1 h | 100 |
| < 4 h | 75 |
| < 24 h | 50 |
| ≥ 24 h | 25 |

---

## security (35%)

What was caught before reaching production. All four metrics carry equal weight.

### `image_scan` — 25% · `sast` — 25%

Container image and source-code vulnerability counts. Both use the same severity-weighted
deduction, floored at zero.

```json
{"critical": 0, "high": 1, "medium": 3}
```

```
score = max(0, 100 − 25×critical − 10×high − 3×medium)
```

The example above scores **81**. A single critical costs 25 points; it takes eight mediums to
do the same damage.

### `dast` — 25%

Findings against a running instance. No critical tier — DAST criticals are rare enough in
practice that the scale starts at high.

```json
{"high": 0, "medium": 2}
```

```
score = max(0, 100 − 20×high − 5×medium)
```

### `secret_scan` — 25%

Hardcoded credentials in the repository. Binary by design: a leaked credential is not a matter
of degree.

```json
{"found": false}
```

| Found | Score |
|---|---|
| `false` | 100 |
| `true` | 0 |

!!! tip "Secrets in infrastructure code go somewhere else"
    `secret_scan` scores the application repository. Findings in Terraform or Helm belong in
    [`POST /problem/scan-result`](reference/api.md), which keeps them as a tracked worklist
    with file and line detail until they are resolved.

---

## application (25%)

How the service is built. Mostly pipeline-sourced.

### `unit_coverage` — 20% · `integration_coverage` — 20%

Both take a percentage, but on deliberately different curves — integration tests are more
expensive per point of coverage, so full marks arrive earlier.

```json
{"percentage": 84.5}
```

| Score | `unit_coverage` | `integration_coverage` |
|---|---|---|
| 100 | ≥ 80% | ≥ 60% |
| 50 → 100 | 60–80% | 40–60% |
| 10 → 50 | 40–60% | 20–40% |
| 0 | < 40% | < 20% |

Between thresholds the score interpolates linearly, so improvements show up immediately
instead of waiting for the next band.

### `stress_test` — 10%

A composite of three load-test outputs, scored independently and summed. Partial credit is the
point: fast but flaky scores differently from slow but solid.

```json
{"error_rate": 0.0004, "p95_ms": 320, "checks_pct": 98.5}
```

| Component | Max | Thresholds |
|---|---|---|
| Error rate | 40 | < 0.1% → 40 · < 1% → 20 · else 0 |
| p95 latency | 35 | < 500 ms → 35 · < 1 s → 20 · < 2 s → 10 · else 0 |
| Check pass rate | 25 | ≥ 95% → 25 · ≥ 80% → 15 · ≥ 60% → 5 · else 0 |

`error_rate` is a fraction from 0.0 to 1.0, not a percentage.

### Boolean practices — `libs_secrets` 15% · `libs_observability` 15% · `unique_db_user` 10% · `health_check` 10%

Four all-or-nothing checks for organisational standards: the shared secrets library, the shared
telemetry library, a dedicated database user rather than a shared one, and an exposed health
endpoint.

```json
{"enabled": true}
```

| `enabled` | Score |
|---|---|
| `true` | 100 |
| `false` | 0 |

---

## Scoring model

### Per scorecard

Each scorecard is the weighted average of the metrics that reported, which is what makes
partial submission safe:

```
scorecard_score = Σ(score × weight) / Σ(weight)
```

An app reporting only `image_scan` (81) and `sast` (95) scores
`(81×0.25 + 95×0.25) / (0.25 + 0.25)` = **88** for security — the absent DAST and secret scan
do not drag it down.

### Per app

```
total = security × 0.35 + application × 0.25 + reliability × 0.40
```

### Per team and per area

Team and area scores are plain averages, one level at a time — apps average into teams, teams
average into areas. Every team counts equally regardless of how many services it owns, so a
40-service team does not swamp a 3-service one.

---

## Not yet covered

These are recognised gaps rather than deliberate omissions. Submitting them today returns
`400 unknown metric` — `calculate_score()` only accepts metrics registered in `SCORERS`.

| Signal | Status | Notes |
|---|---|---|
| Deployment success rate / frequency | Not implemented | `change_failure_rate` captures the inverse for failures, but neither deploy volume nor success count is scored |
| Rollback success rate | Not implemented | Whether rollbacks actually work is untracked |
| Vulnerability remediation time | Not computable today | The `problems` table keeps a mutable `count` and an `updated_at` that is overwritten on every scan — there is no `first_seen` and no `resolved_at`, so how long a finding stayed open is not recoverable from the database. The `maturity_problem_count` series in Prometheus shows the count falling to zero, but only within its retention window |
| Production 5xx error rate | Partially covered | `stress_test.error_rate` measures errors under synthetic load, not real traffic. A production error-rate SLI currently has to be folded into `sla` |

All four are specified in
[`specs/delivery-and-remediation-metrics/`](https://github.com/StaffOps/maturity-score-card/tree/main/specs/delivery-and-remediation-metrics),
including the weight rebalance that adds them to `reliability` without moving any existing
app's score.

## Adding a metric

1. Write the scoring function in `app/scoring/<scorecard>.py` — a pure `dict → float`
2. Register it in `SCORERS` in `app/scoring/__init__.py`
3. Add its weight in `app/weights.py`

Weights within a scorecard should sum to 1.0. Nothing enforces this, but the redistribution
maths assumes it.

See [Pipeline Integration](reference/pipeline-integration.md) for a curl example per metric.
