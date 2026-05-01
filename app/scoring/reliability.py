def score_sla(raw: dict) -> float:
    availability = raw.get("availability_pct", 0.0)
    if availability >= 99.5:
        return 100.0
    if availability >= 99.0:
        return 75.0
    if availability >= 98.0:
        return 50.0
    return max(0.0, (availability - 95) / 3 * 50)


def score_change_failure_rate(raw: dict) -> float:
    cfr = raw.get("rate_pct", 100.0)
    if cfr < 5:
        return 100.0
    if cfr < 10:
        return 75.0
    if cfr < 15:
        return 50.0
    return 25.0
