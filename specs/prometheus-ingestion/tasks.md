# Tasks — Direct Prometheus Ingestion

## Phase 0 — Config contract

- [ ] `app/ingest/config.py` — Pydantic models for the config file, so a malformed config
      fails at startup with a field-level error rather than mid-run [R1]
- [ ] Validation: `identity` non-empty; every metric's `scorecard`/`metric` pair exists in
      `WEIGHTS`; `raw_field` non-empty
- [ ] Reject a config naming a metric absent from `SCORERS` — catching a typo at startup beats
      discovering it 15 minutes later in a counter
- [ ] Tests for each validation failure

## Phase 1 — Query client

- [ ] `app/ingest/prometheus.py` — instant query via `httpx`, timeout, optional bearer token
      read from the env var named in config [design § Configuration]
- [ ] Parse `data.result`; return `(labels, value)` pairs
- [ ] Tests against recorded Prometheus responses: normal, empty result, `NaN`, `+Inf`,
      HTTP 500, timeout

## Phase 2 — Identity resolution

- [ ] Extract the `identity` tuple from each series' labels [R1]
- [ ] Skip + count `bad_identity` when a label is missing
- [ ] Detect duplicates within one query result; skip **both**, count `duplicate_identity`,
      log the full label sets of the colliding series [design § Duplicate identity]
- [ ] Tests, including the `instance`-leaking case that motivates the rule

## Phase 3 — Scoring and write

- [ ] Build a `ScoreRequest` per series and run it through the existing `calculate_score()` —
      no second scoring implementation [design § Why the score is computed in Python]
- [ ] Upsert via the existing `upsert_score()`
- [ ] **Never write on query failure**; partial success writes only what succeeded [R2]
- [ ] Test: a failing query leaves prior rows byte-identical

## Phase 4 — Pull ownership

- [ ] Load pull-owned metric names at startup
- [ ] `POST /score` returns 409 naming the config file for owned metrics [R3]
- [ ] Test: pushing an owned metric 409s; pushing an unowned one still works; removing it from
      config restores push

## Phase 5 — Scheduling

- [ ] `python -m app.jobs.ingest` entrypoint — one full pass, then exit
- [ ] `--loop` mode honouring `interval_minutes` for the container
- [ ] Add the container to `example/docker-compose.yml` [design § Scheduling, option B]
- [ ] Ship `example/prometheus-ingest.yml` with `sla` enabled and `mttr`/`mttd` commented out
      with the proxy caveat inline [R4]
- [ ] Verify against the demo stack: `mock.sh` data, then confirm `sla` arrives by ingestion
      rather than by push

## Phase 6 — Observability

- [ ] The four gauges/counters from [design § Observability]
- [ ] `series_total` first — it is the only detector for the silent-zero-series failure
- [ ] Example alert rules in `example/prometheus/rules/`, at least: no success in `3 ×
      interval`, and `series_total == 0` while `errors_total` is flat

## Phase 7 — Document

- [ ] `docs/site/reference/prometheus-ingestion.md` — config reference, the `label_replace`
      worked example, and the fidelity table
- [ ] State plainly that `mttr`/`mttd` from `ALERTS` are proxies and that incident tooling
      should keep pushing them [R4]
- [ ] `docs/site/reference/api.md` — document the 409
- [ ] `docs/site/index.md` — the "what it does" section says values arrive by push; add pull
- [ ] `docs/site/roadmap.md` — mark delivered

## Sequencing notes

Phases 0–3 are the whole feature; 4–7 make it safe and legible. Phase 4 can ship before
Phase 5 — 409ing on a metric nothing pulls yet is harmless and gets the contract in place.

Phase 6 is not optional polish. Without `series_total`, the most likely production failure —
a query silently returning nothing after an unrelated relabelling — is undetectable.
