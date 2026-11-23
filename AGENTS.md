# AGENTS.md

Guide for AI agents working in this repo: a stateless FastAPI service that scores applications 0-100
across build, ship and run, keeps state in PostgreSQL and exposes Prometheus metrics. Human-facing
docs: [README.md](README.md) and the MkDocs site in [docs/site/](docs/site/index.md).

## Branches

| Branch | Use |
|---|---|
| `main` | The only branch. Commits have landed directly on it so far (no pull requests). CI (`test`) runs on every branch and pull request |

## Commands

Python runs in Docker (no local SDK). The repo and CI use Python 3.12:

```bash
# Tests (pytest.ini adds coverage, fail-under 80); unit tests mock the database, no Postgres needed
docker run --rm -v "$PWD:/app" -w /app python:3.12-slim sh -c \
  "pip install -q -r requirements-dev.txt && pytest"
make openapi                                   # regenerate openapi.json (Docker)
cd example && docker compose up --build -d     # API + PostgreSQL + Prometheus + Grafana
bash example/mock.sh                           # sample data
docker run --rm -v "$PWD:/docs" -w /docs squidfunk/mkdocs-material:latest build --strict
```

## Rules

- **English only**: code comments, docs, specs, CHANGELOG and commits.
- **Conventional Commits** (`feat(api): ...`, `fix(dashboards): ...`, `docs(specs): ...`).
- **CHANGELOG** `[Unreleased]` and the affected `docs/site/` page change in the same commit as the
  code. Update [docs/handoff.md](docs/handoff.md) when you stop with work in flight.
- **API changes regenerate `openapi.json`** in the same commit; CI fails on drift.
- **Specs first**: new scoring work starts as `specs/<feature>/{requirements,design,tasks}.md`
  ([specs/README.md](specs/README.md)), and the roadmap page reflects it.
- **Secrets are never committed**: `DATABASE_URL` and the Slack webhook come from the environment.

## Pitfalls

| Pitfall | What to do |
|---|---|
| Grafana's file provisioner rejects the Schema V2 dashboard | Edit `example/grafana/dashboards/maturity.json`; `push-dashboard.py` loads it through the resource API |
| `mkdocs.yml` uses `docs_dir: docs/site`, so files directly under `docs/` (like `docs/handoff.md`) are not in the site | Link them by repo URL from the site |

## Map

| Need | Read |
|---|---|
| Scorecards, payloads, thresholds | [docs/site/scorecards.md](docs/site/scorecards.md) |
| API and metrics reference | [docs/site/reference/](docs/site/reference/api.md), [openapi.json](openapi.json) |
| What is planned and what is not | [docs/site/roadmap.md](docs/site/roadmap.md), [specs/](specs/README.md) |
| Current state | [docs/handoff.md](docs/handoff.md) |
| History | [CHANGELOG.md](CHANGELOG.md) |
