"""BR5 - Domain Event.

Raised by Aggregate A (Delivery) once grading succeeds. The handler uses
it to request a credit on Aggregate B (FarmerAccount).
"""
from dataclasses import dataclass

from domain.money import Money


@dataclass(frozen=True)
class DeliveryGraded:
    delivery_id: str
    farmer_id: str
    payout: Money
