import pytest
from parsing import parse_bool


@pytest.mark.parametrize("value", ["true", "TRUE", "1", "yes"])
def test_true_values(value: str) -> None:
    assert parse_bool(value) is True


@pytest.mark.parametrize("value", ["false", "FALSE", "0", "no"])
def test_false_values(value: str) -> None:
    assert parse_bool(value) is False


def test_unknown_value_is_rejected() -> None:
    with pytest.raises(ValueError):
        parse_bool("sometimes")
