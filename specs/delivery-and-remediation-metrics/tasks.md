# Tasks — Delivery and Remediation Metrics

Ordered so that each step lands independently and the repo stays green. Requirement and design
references in brackets.

## Phase 0 — Guard rails first

Do these before touching weights. They are what makes the rest safe.

- [ ] Add `tests/unit/test_weights.py`: every scorecard's metric weights sum to 1.0, and the
      scorecard weights sum to 1.0 [R6]
- [ ] Add a test asserting `app/weights.py` agrees with the constants in
      `example/prometheus/rules/maturity.yml` — parse the YAML, extract the multipliers from
      `maturity:total_score`, compare [R7, design option B]
- [ ] Add a regression test pinning `scorecard_score` for an app reporting only the original
      four reliability metrics, so the rebalance is provably a no-op [R6]

## Phase 1 — Weight rebalance

- [ ] Scale the four existing `reliability` weights by 0.65 and register the three new metric
      weights [R6]
- [ ] Update `maturity.yml` if the scorecard-level constants changed — they should not; only
      intra-scorecard weights move
- [ ] Confirm the Phase 0 regression test still passes

At this point the weights exist but no scorer does, so submissions still 400. That is
intentional — the weights are inert until a metric reports.

## Phase 2 — Problem lifecycle

- [ ] `ALTER TABLE problems ADD COLUMN IF NOT EXISTS first_seen, resolved_at` in `init_db()`
      [R3]
- [ ] Backfill existing rows in the same migration [design § Migration]
- [ ] Rewrite `upsert_problem()` with the transition CASE logic [design § problems lifecycle]
- [ ] Tests for all four transitions, especially:
      - repeated scans of an open finding do **not** move `first_seen`
      - a regression resets `first_seen` and clears `resolved_at`
      - `count = 0` on a never-seen finding leaves `first_seen` NULL
- [ ] Expose `first_seen` / `resolved_at` on `maturity_problem_count` or as a companion info
      metric `[TO CONFIRM: which — label cardinality on timestamps is a real risk, so a
      separate maturity_problem_age_seconds gauge is probably right]`

## Phase 3 — `vuln_remediation_time`

- [ ] `get_open_problem_ages()` in `app/database.py` — open findings with severity and age
- [ ] `score_vuln_remediation_time()` in `app/scoring/incident.py` [design § scoring curves]
- [ ] Register in `SCORERS`
- [ ] Tests: no open findings → 100; one critical at 12h → 100; one critical at 30h → 75; one
      critical at 60h → 0; a fresh medium alongside an old critical → scored on the critical

## Phase 4 — Deploy events

- [ ] `CREATE TABLE deploy_events` + index in `init_db()` [design § schema]
- [ ] `app/events/models.py` — `DeployEvent` Pydantic model with the enum validation [R1]
- [ ] `app/events/router.py` — `POST /event/deploy`, including the 5-minute future guard
- [ ] `insert_deploy_event()` and `count_events_in_window()` in `app/database.py`
- [ ] Recompute-and-upsert on ingestion, in a try block separate from the insert so a
      recompute failure cannot lose the event [design § failure modes]
- [ ] `EVENT_WINDOW_DAYS` env var, default 30
- [ ] Tests: invalid `kind`/`result` → 400; future `occurred_at` → 400; ingestion succeeds when
      recompute raises

## Phase 5 — Rate scorers

- [ ] `score_deploy_success_rate()` and `score_rollback_success_rate()` in
      `app/scoring/reliability.py` [design § scoring curves]
- [ ] Register both in `SCORERS`
- [ ] Tests at every threshold boundary, plus the asymmetry: 95% scores 75 for deploys but 60
      for rollbacks

## Phase 6 — `error_rate`

- [ ] `score_error_rate()` in `app/scoring/reliability.py` [R5]
- [ ] Register in `SCORERS`
- [ ] Document the distinction from `sla` and from `stress_test.error_rate` — three
      error-rate-shaped things now exist and confusing them is the obvious failure

## Phase 7 — Nightly recompute

- [ ] Recompute-all entrypoint: `python -m app.jobs.recompute` [design § aggregation flow]
- [ ] Delete the `metric_scores` row when a window is empty, logging each deletion at INFO
      [R2, design § observability]
- [ ] Prune events older than `2 × EVENT_WINDOW_DAYS`
- [ ] `maturity_recompute_last_success_timestamp` gauge
- [ ] Add the job to `example/docker-compose.yml` so the demo stack exercises it
      `[TO CONFIRM: cron container, or an in-process scheduler? A container keeps the API
      stateless, which the project treats as a property worth protecting]`

## Phase 8 — Surface and document

- [ ] Grafana: deploy/rollback rate and remediation age panels on the reliability tab
- [ ] `docs/site/scorecards.md` — move the four signals out of "Not yet covered" into the
      reliability catalogue with their payloads and thresholds
- [ ] **Fix the existing inaccuracy**: the current text claims problem history exists. Until
      Phase 2 ships it does not, and afterwards it exists in the database rather than only in
      Prometheus retention
- [ ] `docs/site/reference/api.md` — document `POST /event/deploy`
- [ ] `docs/site/reference/pipeline-integration.md` — curl examples for the new metrics
- [ ] README metrics table — add `maturity_deploy_events_total` and the recompute gauge

## Sequencing notes

Phases 2 and 4 are independent and can run in parallel. Everything else is ordered.

Phase 0 genuinely gates Phase 1: without the agreement test, a weight change that misses the
recording rules produces a `total_score` that is silently wrong — the same class of bug as the
`project_repo` join, which stayed invisible because the series count never changed.
