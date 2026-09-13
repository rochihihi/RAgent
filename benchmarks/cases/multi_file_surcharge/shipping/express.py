"""Express shipping price."""


def express_total(amount: float, surcharge_percent: float) -> float:
    fixed_express_fee = 5.0
    return amount + fixed_express_fee + amount * surcharge_percent
