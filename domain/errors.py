"""Domain errors. Each one names the business rule it protects."""


class DomainError(Exception):
    """Base class for every business-rule violation."""


# BR1 - Value rule
class InvalidMoistureReading(DomainError):
    pass


# Supporting value objects
class InvalidWeight(DomainError):
    pass


class InvalidMoney(DomainError):
    pass


# BR2 - Identity/state rule
class DeliveryAlreadyGraded(DomainError):
    pass


# BR3 - Invariant rule
class BagLimitExceeded(DomainError):
    pass


class DuplicateBag(DomainError):
    pass


class EmptyDelivery(DomainError):
    pass


# BR4 - Cross-concept rule
class PriceNotAvailable(DomainError):
    pass


# Aggregate B rule (checked when BR5 follow-up arrives)
class AccountSuspended(DomainError):
    pass


class DeliveryAlreadyCredited(DomainError):
    pass
