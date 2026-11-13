"""Supporting Value Object: a bag weight in kilograms.

Used by BR3 (each bag weighs more than 0 kg and at most 60 kg) and by
BR4 (total net weight feeds the payout). Weights have no identity;
two 50 kg weights are the same value.
"""
from dataclasses import dataclass

from domain.errors import InvalidWeight

MAX_BAG_KG = 60.0


@dataclass(frozen=True)
class Weight:
    kg: float

    def __post_init__(self):
        if self.kg <= 0:
            raise InvalidWeight(f"BR3: bag weight must be more than 0 kg, got {self.kg}")
        if self.kg > MAX_BAG_KG:
            raise InvalidWeight(
                f"BR3: bag weight must be at most {MAX_BAG_KG} kg, got {self.kg}"
            )

    @staticmethod
    def total_kg(weights) -> float:
        # A delivery total can exceed 60 kg, so it is returned as a plain
        # number rather than another bag-sized Weight.
        return sum(w.kg for w in weights)
