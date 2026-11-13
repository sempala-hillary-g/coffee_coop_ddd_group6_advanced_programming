"""Input and output DTOs for the Grade Delivery use case.

Plain data only, so the interface layer never handles domain objects.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class GradeDeliveryInput:
    delivery_id: str
    moisture_percent: float


@dataclass(frozen=True)
class GradeDeliveryOutput:
    delivery_id: str
    status: str               # "Graded", "Rejected" or "NotFound"
    payout_ugx: int | None
    farmer_credited: bool
    message: str
