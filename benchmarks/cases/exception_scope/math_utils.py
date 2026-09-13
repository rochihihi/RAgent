"""Defensive arithmetic helpers."""


def safe_divide(numerator: float, denominator: float) -> float:
    try:
        return numerator / denominator
    except Exception:
        return 0.0
