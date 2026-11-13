"""Repository abstractions, one per aggregate root in the workflow.

The application layer owns these interfaces. Infrastructure implements
them, so the dependency points inwards.
"""
from abc import ABC, abstractmethod

from domain.delivery import Delivery
from domain.farmer_account import FarmerAccount


class DeliveryRepository(ABC):
    @abstractmethod
    def get(self, delivery_id: str) -> Delivery | None: ...

    @abstractmethod
    def all(self) -> list[Delivery]: ...

    @abstractmethod
    def save(self, delivery: Delivery) -> None: ...


class FarmerAccountRepository(ABC):
    @abstractmethod
    def get(self, farmer_id: str) -> FarmerAccount | None: ...

    @abstractmethod
    def all(self) -> list[FarmerAccount]: ...

    @abstractmethod
    def save(self, account: FarmerAccount) -> None: ...
