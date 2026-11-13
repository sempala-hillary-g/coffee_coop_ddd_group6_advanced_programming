"""BR5 follow-up: Credit Farmer Account (second use case).

Handles DeliveryGraded. It loads Aggregate B and asks it to accept the
credit. The handler does not check the account's rules itself;
FarmerAccount.credit() does, so Aggregate B enforces its own rule.
"""
from dataclasses import dataclass

from application.repositories import FarmerAccountRepository
from domain.errors import DomainError
from domain.events import DeliveryGraded


@dataclass(frozen=True)
class CreditOutcome:
    credited: bool
    reason: str


class CreditFarmerOnDeliveryGraded:
    def __init__(self, accounts: FarmerAccountRepository):
        self._accounts = accounts

    def handle(self, event: DeliveryGraded) -> CreditOutcome:
        account = self._accounts.get(event.farmer_id)
        if account is None:
            return CreditOutcome(False, f"Farmer {event.farmer_id} not found")
        try:
            account.credit(event.delivery_id, event.payout)
        except DomainError as error:
            return CreditOutcome(False, str(error))
        self._accounts.save(account)
        return CreditOutcome(True, f"Credited {event.payout} to {account.farmer_id}")
