"""Retry scheduling."""


def retry_delays(base: int, attempts: int) -> list[int]:
    if base <= 0 or attempts < 0:
        raise ValueError("base must be positive and attempts non-negative")
    return [base * 2**index for index in range(1, attempts + 1)]
