"""BR4 - Domain Service.

Payout = delivery's total net weight x the price board's price per kg for
that coffee type on the delivery date, rounded to whole shillings.

The rule needs the Delivery (weight, type, date) and the PriceBoard
(cooperative pricing policy). Neither owns the other, so the calculation
sits in a stateless domain service instead of on Delivery.
"""
from datetime import date
from typing import Protocol

from domain.coffee_type import CoffeeType
from domain.delivery import Delivery
from domain.errors import PriceNotAvailable
from domain.money import Money


class PriceBoard(Protocol):
    """What the domain needs from a price source. Infrastructure supplies
    the concrete board, so the domain does not depend on it."""

    def price_per_kg(self, coffee_type: CoffeeType, on: date) -> Money | None: ...


class PayoutCalculator:
    def calculate(self, delivery: Delivery, board: PriceBoard) -> Money:
        price = board.price_per_kg(delivery.coffee_type, delivery.delivery_date)
        if price is None:
            raise PriceNotAvailable(
                f"BR4: no {delivery.coffee_type.value} price set for "
                f"{delivery.delivery_date.isoformat()}")
        return Money(round(delivery.total_net_kg() * price.ugx))
