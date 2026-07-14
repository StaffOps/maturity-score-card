# Metrics & Recording Rules

## Exposed metrics

| Metric | Description | Labels |
|---|---|---|
| `maturity_score` | Computed score (0–100) | area, team, app, env, scorecard, metric, project_repo |
| `maturity_applicable` | 1 if metric ran in this pipeline | area, team, app, env, scorecard, metric, project_repo |
| `maturity_weight` | Metric weight within its scorecard | area, team, app, env, scorecard, metric, project_repo |
| `maturity_raw` | Raw input value per field | area, team, app, env, scorecard, metric, project_repo, field |
| `maturity_problem_count` | Open problems (0 = clean) | area, team, app, env, problem_type, severity |

## Recording rules (vmalert)

| Metric | Description |
|---|---|
| `maturity:scorecard_score` | Weighted score per scorecard per app |
| `maturity:total_score` | Total weighted score per app |
| `maturity:team_score` | Average total score per team |
| `maturity:area_score` | Average of team scores per area |
| `maturity:team_scorecard_score` | Average scorecard score per team |
| `maturity:area_scorecard_score` | Average scorecard score per area |
| `maturity:problems_by_area` | Total open problems per area |
| `maturity:problems_by_team` | Total open problems per team |
| `maturity:apps_with_problems` | Count of apps with at least one open problem |
