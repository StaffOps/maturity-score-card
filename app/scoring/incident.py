def score_mttr(raw: dict) -> float:
    minutes = raw.get("minutes", 99999.0)
    if minutes < 60:
        return 100.0
    if minutes < 240:
        return 75.0
    if minutes < 1440:
        return 50.0
    return 25.0


def score_mttd(raw: dict) -> float:
    minutes = raw.get("minutes", 99999.0)
    if minutes < 5:
        return 100.0
    if minutes < 30:
        return 75.0
    if minutes < 120:
        return 50.0
    return 25.0
