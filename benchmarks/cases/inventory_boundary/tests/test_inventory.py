import pytest
from inventory import Inventory


def test_can_reserve_all_remaining_stock() -> None:
    inventory = Inventory(3)
    inventory.reserve(3)
    assert inventory.stock == 0


def test_cannot_reserve_more_than_stock() -> None:
    inventory = Inventory(3)
    with pytest.raises(ValueError):
        inventory.reserve(4)
