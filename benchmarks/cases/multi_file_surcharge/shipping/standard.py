"""Standard shipping price."""


def standard_total(amount: float, surcharge_percent: float) -> float:
    return amount + amount * surcharge_percent
