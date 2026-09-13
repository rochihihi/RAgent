from shipping import express_total, standard_total


def test_standard_percentage_surcharge() -> None:
    assert standard_total(100, 10) == 110


def test_express_percentage_surcharge() -> None:
    assert express_total(100, 10) == 115
