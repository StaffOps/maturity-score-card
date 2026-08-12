# Specs

Each spec is three files, following the staff-level spec process: `requirements.md` (what and
why, with acceptance criteria), `design.md` (how, with rationale and failure modes), and
`tasks.md` (ordered implementation phases).

| Spec | Status | Summary |
|---|---|---|
| [`vulnerability-remediation`](vulnerability-remediation/) | draft | `first_seen` / `resolved_at` on `problems`, plus a `vuln_remediation_time` metric in `security`. The data does not exist today and no dashboard can recover it |
| [`prometheus-ingestion`](prometheus-ingestion/) | draft | The service queries Prometheus directly for `sla`/`mttr`/`mttd` instead of waiting for a scheduled job to push them |

The user-facing view of the same work is [`docs/site/roadmap.md`](../docs/site/roadmap.md),
which also records what was deliberately **not** built and why.

## Conventions

- Mark uncertainty inline with `[TO CONFIRM: ...]` or `[ASSUMPTION]` rather than guessing
- Every non-obvious decision carries a rationale — six months later the "why" is the part
  nobody can reconstruct
- Acceptance criteria are written so they can become assertions
- Counter-examples ("the endpoint must NOT ...") are as load-bearing as the requirements
- Specs are revised when decisions change. A spec describing discarded work is worse than no
  spec — see the revision note at the top of `vulnerability-remediation/requirements.md`
