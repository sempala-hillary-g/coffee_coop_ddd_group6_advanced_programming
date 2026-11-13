"""Aggregate A: Delivery.

Root: Delivery (identity = delivery_id).
Child entities: Bag (identity = bag number within its delivery).

BR2 (state): Received -> Graded. A graded delivery cannot be graded again
             and cannot take more bags.
BR3 (invariant): 1 to 10 bags, unique bag numbers, each bag a valid Weight.
                 A delivery with no bags cannot be graded.
"""
from dataclasses import dataclass
from datetime import date
from enum import Enum

from domain.aggregate_root import AggregateRoot
from domain.coffee_type import CoffeeType
from domain.errors import (
    BagLimitExceeded,
    DeliveryAlreadyGraded,
    DuplicateBag,
    EmptyDelivery,
)
from domain.events import DeliveryGraded
from domain.moisture_reading import MoistureReading
from domain.money import Money
from domain.weight import Weight

MAX_BAGS = 10


class DeliveryStatus(Enum):
    RECEIVED = "Received"
    GRADED = "Graded"


@dataclass
class Bag:
    """Entity inside the Delivery aggregate. Two bags can weigh the same and
    still be different bags, so identity comes from the bag number."""
    number: int
    weight: Weight


class Delivery(AggregateRoot):
    def __init__(self, delivery_id: str, farmer_id: str,
                 coffee_type: CoffeeType, delivery_date: date):
        super().__init__()
        self.delivery_id = delivery_id
        self.farmer_id = farmer_id
        self.coffee_type = coffee_type
        self.delivery_date = delivery_date
        self.status = DeliveryStatus.RECEIVED
        self._bags: list[Bag] = []
        self.moisture: MoistureReading | None = None
        self.payout: Money | None = None

    @property
    def bags(self) -> tuple:
        # Read-only view so nothing outside the root can change the bags.
        return tuple(self._bags)

    def total_net_kg(self) -> float:
        return Weight.total_kg(b.weight for b in self._bags)

    def add_bag(self, number: int, weight: Weight) -> None:
        self._ensure_not_graded()                                   # BR2
        if len(self._bags) >= MAX_BAGS:                             # BR3
            raise BagLimitExceeded(
                f"BR3: delivery {self.delivery_id} already has {MAX_BAGS} bags")
        if any(b.number == number for b in self._bags):             # BR3
            raise DuplicateBag(
                f"BR3: bag {number} is already recorded on {self.delivery_id}")
        self._bags.append(Bag(number, weight))

    def grade(self, moisture: MoistureReading, payout: Money) -> None:
        self._ensure_not_graded()                                   # BR2
        if not self._bags:                                          # BR3
            raise EmptyDelivery(
                f"BR3: delivery {self.delivery_id} has no bags to grade")
        self.moisture = moisture
        self.payout = payout
        self.status = DeliveryStatus.GRADED
        self.record_event(DeliveryGraded(self.delivery_id, self.farmer_id, payout))  # BR5

    def _ensure_not_graded(self) -> None:
        if self.status is DeliveryStatus.GRADED:
            raise DeliveryAlreadyGraded(
                f"BR2: delivery {self.delivery_id} has already been graded")
