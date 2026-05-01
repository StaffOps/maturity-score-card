def score_bool(raw: dict) -> float:
    return 100.0 if raw.get("enabled", False) else 0.0


def score_unit_coverage(raw: dict) -> float:
    pct = raw.get("percentage", 0.0)
    if pct >= 80:
        return 100.0
    if pct >= 60:
        return 50 + (pct - 60) / 20 * 50
    if pct >= 40:
        return 10 + (pct - 40) / 20 * 40
    return 0.0


def score_integration_coverage(raw: dict) -> float:
    pct = raw.get("percentage", 0.0)
    if pct >= 60:
        return 100.0
    if pct >= 40:
        return 50 + (pct - 40) / 20 * 50
    if pct >= 20:
        return 10 + (pct - 20) / 20 * 40
    return 0.0


def score_stress_test(raw: dict) -> float:
    error_rate = raw.get("error_rate", 1.0)  # 0.0–1.0
    p95_ms = raw.get("p95_ms", 9999.0)
    checks_pct = raw.get("checks_pct", 0.0)  # 0–100

    if error_rate < 0.001:
        error_pts = 40
    elif error_rate < 0.01:
        error_pts = 20
    else:
        error_pts = 0

    if p95_ms < 500:
        latency_pts = 35
    elif p95_ms < 1000:
        latency_pts = 20
    elif p95_ms < 2000:
        latency_pts = 10
    else:
        latency_pts = 0

    if checks_pct >= 95:
        checks_pts = 25
    elif checks_pct >= 80:
        checks_pts = 15
    elif checks_pct >= 60:
        checks_pts = 5
    else:
        checks_pts = 0

    return float(error_pts + latency_pts + checks_pts)
