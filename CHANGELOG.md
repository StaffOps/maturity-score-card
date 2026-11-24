# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html),
and commit messages follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

No version has been tagged or released yet.

## [Unreleased]

### Added

- OpenAPI spec (`openapi.json`) generated from the code, a Backstage `kind: API` entity, and a CI
  check that fails when the committed spec drifts from the code (`make openapi` regenerates it).
- `project_repo` tracked per metric through an info-metric join.
- Roadmap page and two draft specs: `vulnerability-remediation` and `prometheus-ingestion`.
- MkDocs site published to GitHub Pages.
- Backstage `catalog-info.yaml`, technology tags and TechDocs.
- Initial service: `POST /score` for 15 metrics across the `security`, `application` and
  `reliability` scorecards, `POST /problem/scan-result` with Slack alerts on new problems,
  PostgreSQL state and a Prometheus `/metrics` endpoint.

### Changed

- The example stack uses Prometheus instead of VictoriaMetrics and vmalert.
- The project is framed around build, ship and run rather than as a CI/CD scorecard.

### Fixed

- The coverage gate in `pytest.ini` is 90 %, matching the org standard (it was 80 %). New unit
  tests cover the database layer and the Slack notifier; total coverage is 98 %.
- The Grafana dashboard (Schema V2) is pushed through the Grafana resource API, since the file
  provisioner rejects it.

[Unreleased]: https://github.com/StaffOps/maturity-score-card/commits/main
