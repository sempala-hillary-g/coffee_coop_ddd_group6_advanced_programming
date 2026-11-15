"""In-memory price board: the cooperative's buying price per kg for each
coffee type on a given day. It satisfies the domain's PriceBoard protocol.

It is pricing reference data, not an aggregate, so it has no repository.
"""
from datetime import date

from domain.coffee_type import CoffeeType
from domain.money import Money


class InMemoryPriceBoard:
    def __init__(self):
        self._prices: dict[tuple[CoffeeType, date], Money] = {}

    def set_price(self, coffee_type: CoffeeType, on: date, price: Money) -> None:
        self._prices[(coffee_type, on)] = price

    def price_per_kg(self, coffee_type: CoffeeType, on: date) -> Money | None:
        return self._prices.get((coffee_type, on))
