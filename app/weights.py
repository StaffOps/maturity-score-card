WEIGHTS: dict[str, dict] = {
    "security": {
        "scorecard_weight": 0.35,
        "metrics": {
            "image_scan": 0.25,
            "secret_scan": 0.25,
            "sast": 0.25,
            "dast": 0.25,
        },
    },
    "application": {
        "scorecard_weight": 0.25,
        "metrics": {
            "libs_secrets": 0.15,
            "libs_observability": 0.15,
            "unique_db_user": 0.10,
            "health_check": 0.10,
            "unit_coverage": 0.20,
            "integration_coverage": 0.20,
            "stress_test": 0.10,
        },
    },
    "reliability": {
        "scorecard_weight": 0.40,
        "metrics": {
            "sla": 0.20,
            "change_failure_rate": 0.30,
            "mttr": 0.25,
            "mttd": 0.25,
        },
    },
}
