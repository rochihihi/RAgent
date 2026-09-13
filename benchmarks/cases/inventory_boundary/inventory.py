"""Inventory state transitions."""


class Inventory:
    def __init__(self, stock: int) -> None:
        self.stock = stock

    def reserve(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if quantity >= self.stock:
            raise ValueError("insufficient stock")
        self.stock -= quantity
