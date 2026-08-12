# Roadmap

What is shipped, what is specified, and what is deliberately not being built.

Specs live in [`specs/`](https://github.com/StaffOps/maturity-score-card/tree/main/specs) in
the repository. Nothing below is implemented yet unless marked **Shipped**.

## Status at a glance

| Item | Status | Spec |
|---|---|---|
| 15 scored metrics across three scorecards | **Shipped** | — |
| Problem tracking with Slack alerts | **Shipped** | — |
| `project_repo` attribution per metric | **Shipped** | — |
| Vulnerability remediation time | **Specified** | [`vulnerability-remediation`](https://github.com/StaffOps/maturity-score-card/tree/main/specs/vulnerability-remediation) |
| Direct Prometheus ingestion | **Specified** | [`prometheus-ingestion`](https://github.com/StaffOps/maturity-score-card/tree/main/specs/prometheus-ingestion) |
| Weights single source of truth | **Specified** | phase 0 of both specs |
| Deploy / rollback success | **Dashboard only** — see [below](#scored-vs-shown) | — |
| Production 5xx rate | **Dashboard only** — see [below](#scored-vs-shown) | — |

---

## Vulnerability remediation time

**Problem:** the service records *what* is broken but not *for how long*. The `problems` table
holds a mutable `count` and an `updated_at` overwritten on every scan — no `first_seen`, no
`resolved_at`. Time-to-remediate is not recoverable, from the database or from Prometheus.

**Plan:** add lifecycle timestamps maintained by state transition, and a
`vuln_remediation_time` metric in `security` scored on the oldest open finding weighted by
severity — so a three-month-old critical cannot be offset by closing ten easy mediums.

The four existing `security` weights are scaled by 0.80 rather than reassigned, which leaves
every app not reporting the new metric scoring exactly what it scores today.

## Direct Prometheus ingestion

**Problem:** `sla`, `mttr` and `mttd` describe production behaviour that is already in
Prometheus, but the service only learns about it if somebody writes and maintains a scheduled
job to push it. Every adopter rebuilds that job, each choosing its own window and its own
definition of availability — which makes scores incomparable across teams.

**Plan:** the service queries Prometheus directly on a schedule. One query per metric returning
one series per app, mapped onto existing metrics by label. Scoring still happens in Python, so
thresholds stay in one place.

!!! warning "`mttr` and `mttd` from Prometheus are proxies"
    Alert firing duration is not incident duration — it starts *after* detection and often
    ends *after* recovery. The alert's `for:` clause is only a floor on detection delay, and
    the real gap between failure onset and detection is invisible to Prometheus.

    The shipped config enables `sla` and leaves `mttr`/`mttd` commented out. If you have
    incident tooling, keep pushing those from it — it knows when the incident actually started.

Push does not go away. Coverage, scans and the boolean practice checks are not in Prometheus
and stay pushed.

## Weights: one source of truth

`app/weights.py` and `example/prometheus/rules/maturity.yml` both hardcode the scorecard
weights, with a comment asking for manual synchronisation and nothing detecting drift.

A wrong `total_score` from a missed update produces no error and no missing series — it just
quietly reports the wrong number. A test asserting the two agree is phase 0 of both specs
above, before anything touches a weight.

---

## Scored vs shown

Some signals are better as a Grafana panel than as part of the score. Appearing on a dashboard
and counting toward the maturity number are different things, and the distinction is
deliberate:

- To **count**, a signal must pass through a scoring function, take a weight inside its
  scorecard, and aggregate into team and area scores.
- To be **shown**, it only has to exist in Prometheus.

| Signal | Decision | Why |
|---|---|---|
| Deploy success rate | Panel | Reads the GitOps controller's own metrics directly. Scoring it would mean an events table, a rolling window, a nightly recompute and a weight rebalance — a large amount of machinery before anyone has looked at the numbers |
| Rollback success rate | Panel | Same. Worth scoring later once real data exists to calibrate thresholds against |
| Production 5xx rate | Panel | Where the availability SLI is request-success based, this is `1 − sla`. Scoring both counts availability twice inside one scorecard |

Deploy and rollback success are candidates for scoring in a later phase. The order — panel
first, score once calibrated — is intentional: thresholds picked before seeing real
distributions tend to be wrong, and a wrong threshold in a scored metric is worse than no
metric, because it looks authoritative.

## Not planned

| Item | Why not |
|---|---|
| Per-environment weight overrides | No demand yet, and it makes cross-environment comparison meaningless |
| Backfilling problem history | The data was never recorded; any backfill would be invention |
| Scoring in PromQL recording rules | Would put thresholds in the rules file *and* in Python — the same drift problem the weights already have |
| Replacing push entirely | Coverage, scans and practice checks have no Prometheus representation |
