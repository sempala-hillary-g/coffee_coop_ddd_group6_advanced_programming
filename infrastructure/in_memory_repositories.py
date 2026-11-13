"""In-memory implementations of the repository abstractions.

Each stores whole aggregates in a dict keyed by the root's identity.
"""
from application.repositories import (
    DeliveryRepository,
    FarmerAccountRepository,
)
from domain.delivery import Delivery
from domain.farmer_account import FarmerAccount


class InMemoryDeliveryRepository(DeliveryRepository):
    """Stores Delivery aggregates (with their bags) by delivery_id."""

    def __init__(self):
        self._store: dict[str, Delivery] = {}

    def get(self, delivery_id: str) -> Delivery | None:
        return self._store.get(delivery_id)

    def all(self) -> list[Delivery]:
        return list(self._store.values())

    def save(self, delivery: Delivery) -> None:
        self._store[delivery.delivery_id] = delivery


class InMemoryFarmerAccountRepository(FarmerAccountRepository):
    """Stores FarmerAccount aggregates by farmer_id."""

    def __init__(self):
        self._store: dict[str, FarmerAccount] = {}

    def get(self, farmer_id: str) -> FarmerAccount | None:
        return self._store.get(farmer_id)

    def all(self) -> list[FarmerAccount]:
        return list(self._store.values())

    def save(self, account: FarmerAccount) -> None:
        self._store[account.farmer_id] = account
