# Handoff

Last updated: 2026-11-23 · Backstage docs-standard rollout · branch `main`

## State

maturity-score-card is a stateless FastAPI service that turns build, ship and run signals into a
0-100 score per app, team and area, with 15 metrics in three scorecards, PostgreSQL state and a
Prometheus `/metrics` endpoint (see the
[README](https://github.com/StaffOps/maturity-score-card/blob/main/README.md)). The Backstage catalog
marks the service and its API `experimental`. There are no tags or releases, and the repo has no
deploy manifests: it runs through the `example/` Docker Compose stack. The latest `test` runs on
`main` (2026-11-18) succeed, including the OpenAPI drift check. The last feature, the OpenAPI spec
and Backstage API entity, landed on 2026-11-18. No work is in progress.

## Done

- OpenAPI spec, Backstage API entity and drift check ([`5e92b73`](https://github.com/StaffOps/maturity-score-card/commit/5e92b73))
- Backstage catalog, tags and TechDocs ([`120e138`](https://github.com/StaffOps/maturity-score-card/commit/120e138), [`ff04720`](https://github.com/StaffOps/maturity-score-card/commit/ff04720))
- Roadmap and two draft specs ([`a967e59`](https://github.com/StaffOps/maturity-score-card/commit/a967e59), [`a264000`](https://github.com/StaffOps/maturity-score-card/commit/a264000))
- `project_repo` per metric ([`c110c6e`](https://github.com/StaffOps/maturity-score-card/commit/c110c6e))
- Example stack on Prometheus; Schema V2 dashboard pushed through the resource API ([`22a091f`](https://github.com/StaffOps/maturity-score-card/commit/22a091f), [`012df48`](https://github.com/StaffOps/maturity-score-card/commit/012df48))

## In progress

- No open pull requests or issues. Both specs are `draft` and not started
  ([specs/README.md](https://github.com/StaffOps/maturity-score-card/blob/main/specs/README.md)).

## Next steps

From the [roadmap](https://github.com/StaffOps/maturity-score-card/blob/main/docs/site/roadmap.md):

1. Weights as a single source of truth (phase 0 of both specs).
2. Vulnerability remediation time: `first_seen` / `resolved_at` on problems and a
   `vuln_remediation_time` metric (`specs/vulnerability-remediation/`).
3. Direct Prometheus ingestion for `sla`, `mttr` and `mttd` (`specs/prometheus-ingestion/`).

## Decisions

No ADRs. Decisions with rationale live in the specs and in the roadmap's "Scored vs shown" and
"Not planned" sections (deploy/rollback success and production 5xx rate stay dashboard panels, not
scored metrics).

## Risks and open questions

- No deployment: the catalog has no deploy annotations and the repo no manifests, so the service only
  runs locally (open question whether it is meant to be deployed).
- The MkDocs site builds from `docs/site`, so this handoff is outside the site and the TechDocs build.

## How to verify

```bash
gh run list -R StaffOps/maturity-score-card -L 5
docker run --rm -v "$PWD:/app" -w /app python:3.12-slim sh -c \
  "pip install -q -r requirements-dev.txt && pytest"
cd example && docker compose up --build -d && curl -s localhost:8080/metrics | head
```
