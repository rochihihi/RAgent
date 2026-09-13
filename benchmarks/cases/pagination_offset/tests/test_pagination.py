import pytest
from pagination import paginate


def test_first_and_second_pages() -> None:
    items = [1, 2, 3, 4, 5]
    assert paginate(items, 1, 2) == [1, 2]
    assert paginate(items, 2, 2) == [3, 4]


def test_invalid_page() -> None:
    with pytest.raises(ValueError):
        paginate([1], 0, 1)
