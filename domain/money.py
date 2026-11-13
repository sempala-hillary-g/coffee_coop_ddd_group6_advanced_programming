"""Supporting Value Object: an amount in Uganda shillings.

UGX has no subunit in everyday use, so amounts are whole shillings and
never negative. Payouts (BR4) and account balances (Aggregate B) use it,
which stops a float like 1799999.9999 from reaching a farmer's balance.
"""
from dataclasses import dataclass

from domain.errors import InvalidMoney


@dataclass(frozen=True)
class Money:
    ugx: int

    def __post_init__(self):
        if not isinstance(self.ugx, int) or isinstance(self.ugx, bool):
            raise InvalidMoney(f"Money must be whole shillings, got {self.ugx!r}")
        if self.ugx < 0:
            raise InvalidMoney(f"Money cannot be negative, got {self.ugx}")

    @staticmethod
    def zero() -> "Money":
        return Money(0)

    def __add__(self, other: "Money") -> "Money":
        return Money(self.ugx + other.ugx)

    def __str__(self) -> str:
        return f"UGX {self.ugx:,}"
