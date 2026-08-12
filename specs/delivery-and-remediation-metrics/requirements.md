# Requirements — Delivery and Remediation Metrics

**Status:** draft · **Scorecard affected:** `reliability` · **Breaking:** no (see [R6](#r6-existing-scores-must-not-move))

## Problem

The service scores fifteen metrics but cannot answer four questions the organisation
actually asks:

1. *Do our deploys work?* — `change_failure_rate` captures the share that break something,
   but nothing records deploy volume or success count.
2. *Do our rollbacks work?* — completely untracked. A team that rolls back successfully and
   one whose rollbacks fail score identically.
3. *How fast do we fix vulnerabilities?* — findings are recorded, but the schema keeps only a
   mutable `count` and an `updated_at` that is overwritten on every scan. There is no
   `first_seen` and no `resolved_at`, so time-to-remediate is not computable.
4. *How much does the app actually fail in production?* — `stress_test.error_rate` measures
   synthetic load, not real traffic.

Without (3) in particular, the `problems` subsystem can say *what* is broken but never *for
how long* — which is the number that drives remediation SLAs.

## Scope

In scope:

- Three new `reliability` metrics: `deploy_success_rate`, `rollback_success_rate`,
  `error_rate`
- One new metric derived from problem state: `vuln_remediation_time`
- Deploy/rollback event ingestion and windowed aggregation
- `problems` lifecycle timestamps
- Removing the duplicated scorecard weights between `app/weights.py` and the recording rules

Out of scope:

- Changing the weight of `reliability` itself (stays 40%) or of any other scorecard
- Backfilling history for events or problems that predate the migration
- Per-environment weight overrides
- Any new Grafana panel — dashboards follow once the metrics exist

## Requirements

### R1 — Deploy and rollback events are ingested individually

The service accepts one request per deploy or rollback attempt and aggregates them itself,
rather than receiving a pre-computed ratio.

```
POST /event/deploy
{
  "area": "financial", "team": "payments", "app": "payments-api", "env": "prod",
  "kind": "deploy",              // deploy | rollback
  "result": "success",           // success | failure
  "occurred_at": "2026-08-12T14:03:11Z",   // optional, defaults to now()
  "pipeline_id": "ci-9271",
  "project_repo": "financial/payments-api"
}
```

Acceptance criteria:

- `kind` outside `{deploy, rollback}` and `result` outside `{success, failure}` return `400`
- `occurred_at` in the future by more than 5 minutes returns `400` (clock-skew guard)
- Two identical requests create two events — deploys are genuinely repeatable, so there is no
  dedupe key. Callers needing idempotency must supply `pipeline_id` and dedupe upstream
  `[TO CONFIRM: is pipeline retry double-counting an accepted risk?]`
- Response returns the recomputed rate so the caller can log it

Counter-examples — the endpoint must NOT:

- accept a ratio (`{"rate_pct": 96}`) — that is what this requirement replaces
- reject an event because the app has never been scored before
- fail the request if the recompute fails; ingestion and scoring are separated (see R2)

### R2 — Rates are computed over a rolling window

`deploy_success_rate` and `rollback_success_rate` are `successes / total × 100` over a rolling
window, default **30 days**, configurable per deployment via `EVENT_WINDOW_DAYS`.

Acceptance criteria:

- The rate is recomputed and upserted into `metric_scores` on every ingestion
- A nightly job recomputes every app so a rate cannot go stale when deploys stop
- **Empty window → the metric row is deleted**, not scored zero. An app that has not deployed
  in 30 days is not a 0% success rate; weight redistribution must exclude it entirely
- A window containing only rollbacks yields `rollback_success_rate` but no
  `deploy_success_rate`, and vice versa

Worked example — 30-day window, app with 24 deploys (23 success) and 2 rollbacks (1 success):

| Metric | Computation | Raw score |
|---|---|---|
| `deploy_success_rate` | 23/24 × 100 = 95.83% | see [design](design.md#scoring-curves) |
| `rollback_success_rate` | 1/2 × 100 = 50% | see design |

### R3 — Problems record their own lifecycle

`problems` gains `first_seen` and `resolved_at`, maintained by state transition rather than
overwritten on every scan.

| Transition | Trigger | `first_seen` | `resolved_at` |
|---|---|---|---|
| absent → open | first scan with `count > 0` | set to `now()` | `NULL` |
| open → open | scan with `count > 0`, any count | **unchanged** | `NULL` |
| open → resolved | scan reports `count = 0` | unchanged | set to `now()` |
| resolved → open | regression: scan reports `count > 0` again | **reset to `now()`** | cleared to `NULL` |

Acceptance criteria:

- A scan that changes nothing must not move `first_seen`
- `resolved_at` is never in the past relative to `first_seen`
- A finding that regresses starts a **new** remediation clock — the old duration is not
  extended, because the team did fix it once
- Existing rows migrate with `first_seen = updated_at` and `resolved_at = updated_at` where
  `count = 0`. This is approximate for pre-existing data and is
  [accepted as lossy](design.md#migration)

### R4 — `vuln_remediation_time` scores how long findings stay open

A `reliability` metric derived from problem state, submitted by a scheduled job rather than a
pipeline.

```json
{"metric": "vuln_remediation_time", "raw": {"p50_hours": 18.5, "open_critical_hours": 4}}
```

Acceptance criteria:

- Scored on the age of *currently open* findings, not resolved ones — a team with a
  three-month-old open critical must not be rewarded for having fixed ten easy findings fast
- An app with no open findings scores 100
- Weighted toward severity: an open `critical` dominates open `medium`s

### R5 — `error_rate` scores real production failures

Share of production requests failing, distinct from `stress_test.error_rate`.

```json
{"metric": "error_rate", "raw": {"rate_pct": 0.12, "window_hours": 24}}
```

Acceptance criteria:

- Sourced from a scheduled query against Prometheus, not a pipeline
- Documented explicitly as *not* the same signal as `sla`: a service can be 100% available by
  probe and still return 5xx to a subset of users

### R6 — Existing scores must not move

Adding metrics to `reliability` must leave every app that does not report them scoring
**exactly** what it scores today.

This is achievable because the scorecard score is a ratio, so scaling the existing four
weights by a constant cancels out. It is *not* achievable by reassigning them.

| Metric | Today | After | Relative share (unchanged) |
|---|---|---|---|
| `sla` | 0.20 | 0.1300 | 20% |
| `change_failure_rate` | 0.30 | 0.1950 | 30% |
| `mttr` | 0.25 | 0.1625 | 25% |
| `mttd` | 0.25 | 0.1625 | 25% |
| `deploy_success_rate` | — | 0.1500 | new |
| `rollback_success_rate` | — | 0.1000 | new |
| `error_rate` | — | 0.1000 | new |

Acceptance criteria:

- A regression test asserts that an app reporting only the original four metrics produces a
  byte-identical `scorecard_score` before and after the change
- Weights within each scorecard sum to 1.0, enforced by a test — currently nothing checks this

### R7 — Scorecard weights have one source of truth

`app/weights.py` and `example/prometheus/rules/maturity.yml` both hardcode `0.35 / 0.25 /
0.40`, with a comment instructing manual synchronisation. Nothing detects drift, and this
change is the first that would trigger it.

Acceptance criteria:

- Either the rules are generated from `weights.py`, or a test fails when the two disagree
- The test must fail loudly on a weight change with no rules update — a silently wrong
  `total_score` is the exact failure mode being prevented

## Non-functional

| Concern | Requirement |
|---|---|
| Ingestion latency | `POST /event/deploy` p95 < 100 ms; recompute must not block the response if it exceeds this |
| Event volume | `[ASSUMPTION]` ~10³–10⁴ events/day across 125 apps. Revisit indexing above 10⁵ |
| Retention | Events older than `2 × EVENT_WINDOW_DAYS` are pruned nightly |
| Backward compatibility | All schema changes additive (`ADD COLUMN IF NOT EXISTS`, `CREATE TABLE IF NOT EXISTS`), matching the existing `project_repo` migration pattern |

## Open decisions

| # | Question | Recommendation |
|---|---|---|
| 1 | Should pipeline retries double-count deploys? | Accept for now; revisit if data looks inflated |
| 2 | Is `error_rate` distinct enough from `sla` to hold its own weight? | Yes — probe-based availability misses partial 5xx |
| 3 | Should `vuln_remediation_time` also cover `problems` beyond secrets? | Yes, the table is already generic over `problem_type` |
