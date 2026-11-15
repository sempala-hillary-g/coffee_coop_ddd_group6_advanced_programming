"""Aggregate B: FarmerAccount.

Root: FarmerAccount (identity = farmer_id, the cooperative membership number).

Invariant protected by this root, and the rule it checks before accepting
the BR5 follow-up: a credit is accepted only if the account is Active and
that delivery has not already been credited. The balance changes only
through credit().
"""
from enum import Enum

from domain.aggregate_root import AggregateRoot
from domain.errors import AccountSuspended, DeliveryAlreadyCredited
from domain.money import Money


class AccountStatus(Enum):
    ACTIVE = "Active"
    SUSPENDED = "Suspended"


class FarmerAccount(AggregateRoot):
    def __init__(self, farmer_id: str, name: str,
                 status: AccountStatus = AccountStatus.ACTIVE):
        super().__init__()
        self._farmer_id = farmer_id
        self.name = name
        self._status = status
        self._balance = Money.zero()
        self._credited_deliveries: set[str] = set()

    @property
    def farmer_id(self):
        return self._farmer_id

    @property
    def status(self):
        return self._status

    @property
    def balance(self) -> Money:
        return self._balance

    def has_credited(self, delivery_id: str) -> bool:
        return delivery_id in self._credited_deliveries

    def suspend(self) -> None:
        self._status = AccountStatus.SUSPENDED

    def credit(self, delivery_id: str, amount: Money) -> None:
        if self.status is AccountStatus.SUSPENDED:
            raise AccountSuspended(
                f"BR5: Account {self.farmer_id} is suspended and cannot be credited")
        if delivery_id in self._credited_deliveries:
            raise DeliveryAlreadyCredited(
                f"BR5: Delivery {delivery_id} was already credited to {self.farmer_id}")
        self._balance = self._balance + amount
        self._credited_deliveries.add(delivery_id)
