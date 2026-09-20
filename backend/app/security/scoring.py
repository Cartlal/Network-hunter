SEVERITY_PENALTY = {"critical": 40, "high": 25, "medium": 10, "low": 5}


def compute_score(severities: list[str]) -> int:
    """Start at 100, subtract a fixed penalty per active, unacknowledged
    finding, floor at 0. Pure/no I/O so it's cheap to unit test directly -
    see backend/tests/test_security_scoring.py."""
    score = 100
    for severity in severities:
        score -= SEVERITY_PENALTY.get(severity, 0)
    return max(0, score)
