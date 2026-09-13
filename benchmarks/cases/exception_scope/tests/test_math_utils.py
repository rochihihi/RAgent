import pytest
from math_utils import safe_divide


def test_zero_division_has_fallback() -> None:
    assert safe_divide(10, 0) == 0.0


def test_type_errors_are_not_hidden() -> None:
    with pytest.raises(TypeError):
        safe_divide("10", 2)  # type: ignore[arg-type]
