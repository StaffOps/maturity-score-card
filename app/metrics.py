from prometheus_client import CollectorRegistry, Gauge, generate_latest
from app.database import get_all_scores, get_all_problems


def build_metrics() -> bytes:
    registry = CollectorRegistry()

    score_labels = ["area", "team", "app", "env", "scorecard", "metric"]
    g_score      = Gauge("maturity_score",      "Computed maturity score (0-100)",        score_labels,             registry=registry)
    g_applicable = Gauge("maturity_applicable", "1 if metric was evaluated in pipeline",  score_labels,             registry=registry)
    g_weight     = Gauge("maturity_weight",     "Metric weight within its scorecard",      score_labels,             registry=registry)
    g_raw        = Gauge("maturity_raw",        "Raw input value",                         score_labels + ["field"], registry=registry)

    for area, team, app, env, scorecard, metric, score, weight, raw in get_all_scores():
        lv = [area, team, app, env, scorecard, metric]
        g_score.labels(*lv).set(score)
        g_applicable.labels(*lv).set(1)
        g_weight.labels(*lv).set(weight)
        if raw:
            for field, value in raw.items():
                if isinstance(value, bool):
                    g_raw.labels(*lv, field).set(1.0 if value else 0.0)
                elif isinstance(value, (int, float)):
                    g_raw.labels(*lv, field).set(float(value))

    prob_labels = ["area", "team", "app", "env", "problem_type", "severity"]
    g_prob = Gauge("maturity_problem_count", "Number of open problems (0 = clean)", prob_labels, registry=registry)

    for area, team, app, env, problem_type, severity, count in get_all_problems():
        g_prob.labels(area, team, app, env, problem_type, severity).set(count)

    return generate_latest(registry)
