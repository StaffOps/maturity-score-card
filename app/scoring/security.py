def score_image_scan(raw: dict) -> float:
    critical = raw.get("critical", 0)
    high = raw.get("high", 0)
    medium = raw.get("medium", 0)
    return max(0.0, 100 - (critical * 25) - (high * 10) - (medium * 3))


def score_secret_scan(raw: dict) -> float:
    return 0.0 if raw.get("found", False) else 100.0


def score_sast(raw: dict) -> float:
    critical = raw.get("critical", 0)
    high = raw.get("high", 0)
    medium = raw.get("medium", 0)
    return max(0.0, 100 - (critical * 25) - (high * 10) - (medium * 3))


def score_dast(raw: dict) -> float:
    high = raw.get("high", 0)
    medium = raw.get("medium", 0)
    return max(0.0, 100 - (high * 20) - (medium * 5))
