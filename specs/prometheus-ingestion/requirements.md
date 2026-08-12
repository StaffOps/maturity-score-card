# Requirements — Direct Prometheus Ingestion

**Status:** draft · **Metrics affected:** `sla`, `mttr`, `mttd` · **Breaking:** no

## Problem

Three of the four `reliability` metrics describe production behaviour, and production
behaviour is already in Prometheus. Yet the service only learns about it if somebody writes
and maintains a scheduled job that runs a PromQL query and POSTs the result.

That job is unowned infrastructure. Every organisation adopting the service has to rebuild it,
each one choosing its own window and its own definition of availability, which makes scores
incomparable across teams — the exact thing a maturity score exists to enable.

The service should query the Prometheus it already depends on.

## Scope

In scope:

- A configured Prometheus endpoint the service queries on a schedule
- Declarative query configuration mapping PromQL results onto existing metrics
- Ingestion of `sla`, `mttr`, `mttd`, and any other metric expressible as a single query
- Explicit precedence between pulled and pushed values

Out of scope:

- Replacing push. Coverage, scans and boolean practices stay pushed; they are not in Prometheus
- Any new scored metric — this changes *how* existing metrics arrive, not *what* is scored
- Querying anything other than a Prometheus-compatible `/api/v1/query` endpoint
- Alerting on ingestion failures beyond exposing the metrics to alert on

## Requirements

### R1 — One query per metric, not one per app

A query returns **one series per application**, identified by labels. The service must not
issue one request per app.

```yaml
# example/prometheus-ingest.yml
prometheus:
  url: http://prometheus:9090
  timeout_seconds: 30

identity: [area, team, app, env]   # labels that must be present on every result series

metrics:
  - metric: sla
    scorecard: reliability
    raw_field: availability_pct
    query: |
      100 * (
        sum by (area, team, app, env) (rate(http_requests_total{code!~"5.."}[30d]))
        /
        sum by (area, team, app, env) (rate(http_requests_total[30d]))
      )
```

Acceptance criteria:

- 125 apps × 3 metrics is **3 HTTP requests**, not 375
- A result series missing any `identity` label is skipped and logged with the series' labels —
  never guessed at, never defaulted
- Two series resolving to the same identity tuple is a **configuration error**: skip both, log
  loudly. Silently taking the first would produce a score nobody can explain
- `NaN` and `+Inf` results are skipped, not written. A ratio over an empty denominator is
  "no data", not zero

### R2 — Prometheus being unavailable must never change a score

Acceptance criteria:

- A failed query leaves existing `metric_scores` rows untouched — it must not write, delete,
  or zero anything
- Partial success is honoured: if two of three queries succeed, those two are written
- Failure is visible as a metric, not only a log line (see R5)

Counter-example — the run must NOT:

- delete a metric row because a query returned no series. "No data" and "the app is gone" are
  different, and only the operator can tell them apart

### R3 — Pulled and pushed values must not fight

A metric configured for pull is owned by pull.

Acceptance criteria:

- `POST /score` for a metric present in the ingest config returns **409** with a message naming
  the config file
- Removing a metric from the config restores push for it on the next reload
- The response body says which source owns the metric, so a confused pipeline author gets the
  answer from the error rather than from reading the service's source

Rationale: last-write-wins between two sources produces a score that flips depending on
scrape timing. An explicit owner is worse ergonomics and far better debuggability.

### R4 — Fidelity is documented per metric, honestly

Not every metric derives from Prometheus equally well, and pretending otherwise produces
confident wrong numbers.

| Metric | Derivable | Fidelity | Typical source |
|---|---|---|---|
| `sla` | Yes | **Exact**, if the SLI is request-success based | request counters |
| `error_rate` | Yes | **Exact** | request counters |
| `mttr` | Approximately | **Proxy** — alert firing duration is not incident duration | `ALERTS` |
| `mttd` | Barely | **Weak proxy** — the alert's `for:` is a floor on detection delay; the real gap between failure onset and detection is unobservable to Prometheus | `ALERTS` |
| `vuln_remediation_time` | No | — | lives in the `problems` table |
| coverage, scans, practices | No | — | pipeline-only by nature |

Acceptance criteria:

- The shipped example config includes `sla` and leaves `mttr`/`mttd` **commented out**, with
  the proxy caveat inline
- Documentation states plainly that organisations with incident tooling should keep pushing
  `mttr`/`mttd` from that tooling, which knows when the incident actually started

### R5 — The run is observable

| Signal | Purpose |
|---|---|
| `maturity_ingest_last_success_timestamp{metric}` | Alert when a metric stops arriving |
| `maturity_ingest_series_total{metric}` | Sudden drop means a relabel broke the query |
| `maturity_ingest_errors_total{metric,reason}` | `timeout` / `bad_identity` / `duplicate_identity` / `non_finite` |

Acceptance criteria:

- A query that silently starts returning zero series is detectable — this is the most likely
  real failure, and it looks identical to "nothing to report" without the series counter

## Non-functional

| Concern | Requirement |
|---|---|
| Interval | Configurable, default 15 min. Availability over 30 days does not move fast enough to justify more |
| Timeout | Per query, default 30s; a slow query must not stall the others |
| Statelessness | Config is read-only and mounted; the service stays stateless |
| Dependencies | `httpx` is already a dependency (used by Slack). No new package |

## Open decisions

| # | Question | Recommendation |
|---|---|---|
| 1 | In-process scheduler or separate container? | See [design](design.md#scheduling) — leaning separate, to protect statelessness |
| 2 | Authentication to Prometheus? | Bearer token from env; the demo stack needs none `[TO CONFIRM: is mTLS needed in your environment?]` |
| 3 | Should config reload without restart? | No. Restart is cheap and a watcher is a failure mode for little gain |
