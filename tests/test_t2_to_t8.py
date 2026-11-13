"""T2 to T8. T1 (BR1) lives in test_t1_moisture_reading.py as the TDD example."""
import pytest

from application.dtos import GradeDeliveryInput
from domain.coffee_type import CoffeeType
from domain.delivery import DeliveryStatus
from domain.errors import (
    BagLimitExceeded,
    DeliveryAlreadyGraded,
    PriceNotAvailable,
)
from domain.events import DeliveryGraded
from domain.farmer_account import AccountStatus, FarmerAccount
from domain.moisture_reading import MoistureReading
from domain.money import Money
from domain.payout_calculator import PayoutCalculator
from domain.weight import Weight
from tests.conftest import make_delivery


def test_t2_br2_graded_delivery_cannot_be_graded_again():
    # Rejection case
    delivery = make_delivery()
    delivery.grade(MoistureReading(12.0), Money(1_000))

    with pytest.raises(DeliveryAlreadyGraded):
        delivery.grade(MoistureReading(11.0), Money(2_000))

    assert delivery.status is DeliveryStatus.GRADED
    assert delivery.payout == Money(1_000)          # first grading untouched


def test_t3_br3_delivery_rejects_an_eleventh_bag():
    # Rejection case; 10 bags is the boundary that is still allowed
    delivery = make_delivery(bag_weights=[30] * 10)
    assert len(delivery.bags) == 10

    with pytest.raises(BagLimitExceeded):
        delivery.add_bag(11, Weight(30))

    assert len(delivery.bags) == 10


def test_t4_br4_payout_is_net_weight_times_daily_price(world):
    delivery = make_delivery(bag_weights=(50, 50, 50))       # 150 kg Robusta

    payout = PayoutCalculator().calculate(delivery, world.board)
    assert payout == Money(1_800_000)                        # 150 x 12,000

    # No Arabica price is set for that day, so no payout can be calculated
    arabica = make_delivery(delivery_id="D009", coffee_type=CoffeeType.ARABICA)
    with pytest.raises(PriceNotAvailable):
        PayoutCalculator().calculate(arabica, world.board)


def test_t5_br5_grading_records_delivery_graded_event():
    delivery = make_delivery(delivery_id="D005", farmer_id="F005")
    delivery.grade(MoistureReading(12.0), Money(600_000))

    events = delivery.pull_events()
    assert events == [DeliveryGraded("D005", "F005", Money(600_000))]
    assert delivery.pull_events() == []              # events are dispatched once


def test_t6_br6_unknown_delivery_is_rejected_and_nothing_changes(world):
    # Rejection case
    world.accounts.save(FarmerAccount("F001", "Nakato Sarah"))

    result = world.service.execute(GradeDeliveryInput("D404", 12.0))

    assert result.status == "NotFound"
    assert result.farmer_credited is False
    assert world.deliveries.get("D404") is None
    assert world.accounts.get("F001").balance == Money.zero()


def test_t7_main_use_case_grades_delivery_and_credits_active_farmer(world):
    world.accounts.save(FarmerAccount("F001", "Nakato Sarah"))
    world.deliveries.save(make_delivery("D001", "F001", bag_weights=(50, 50, 50)))

    result = world.service.execute(GradeDeliveryInput("D001", 12.5))

    # Output DTO
    assert result.status == "Graded"
    assert result.payout_ugx == 1_800_000
    assert result.farmer_credited is True
    # Aggregate A changed
    assert world.deliveries.get("D001").status is DeliveryStatus.GRADED
    # Event handled and Aggregate B changed
    account = world.accounts.get("F001")
    assert account.balance == Money(1_800_000)
    assert account.has_credited("D001")


def test_t8_suspended_account_rejects_the_follow_up_credit(world):
    world.accounts.save(
        FarmerAccount("F002", "Okello James", AccountStatus.SUSPENDED))
    world.deliveries.save(make_delivery("D002", "F002", bag_weights=(50, 50, 50)))

    result = world.service.execute(GradeDeliveryInput("D002", 12.5))

    # Returned outcome: graded, but not credited, with the reason
    assert result.status == "Graded"
    assert result.payout_ugx == 1_800_000
    assert result.farmer_credited is False
    assert "suspended" in result.message
    # Final state: Delivery is graded, Aggregate B unchanged
    assert world.deliveries.get("D002").status is DeliveryStatus.GRADED
    account = world.accounts.get("F002")
    assert account.balance == Money.zero()
    assert not account.has_credited("D002")
