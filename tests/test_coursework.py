"""Exactly eight automated tests, using Python's standard library."""
import unittest
from dataclasses import FrozenInstanceError
from datetime import date, timedelta

from application.dtos import GradeDeliveryInput
from application.credit_farmer_handler import CreditFarmerOnDeliveryGraded
from domain.coffee_type import CoffeeType
from domain.delivery import Delivery, DeliveryStatus
from domain.errors import (InvalidMoistureReading, InvalidWeight, DuplicateBag,
    BagLimitExceeded, EmptyDelivery, DeliveryAlreadyGraded, PriceNotAvailable)
from domain.events import DeliveryGraded
from domain.farmer_account import FarmerAccount, AccountStatus
from domain.moisture_reading import MoistureReading
from domain.money import Money
from domain.payout_calculator import PayoutCalculator
from domain.weight import Weight
from interface.main import build_service

DAY = date(2026, 11, 6)


def make_delivery(delivery_id="D001", farmer_id="F001",
                  coffee_type=CoffeeType.ROBUSTA, weights=(50, 50, 50), on=DAY):
    delivery = Delivery(delivery_id, farmer_id, coffee_type, on)
    for number, kg in enumerate(weights, 1):
        delivery.add_bag(number, Weight(kg))
    return delivery


class CourseworkTests(unittest.TestCase):
    def setUp(self):
        self.service, self.deliveries, self.accounts, self.board = build_service()
        self.board.set_price(CoffeeType.ROBUSTA, DAY, Money(12_000))

    def test_t1_br1_moisture_boundaries(self):
        for value in (8.0, 13.0):
            self.assertEqual(MoistureReading(value).percent, value)
        for value in (7.9, 13.1, float("nan")):
            with self.assertRaises(InvalidMoistureReading):
                MoistureReading(value)

    def test_t2_br2_graded_delivery_cannot_change(self):
        delivery = make_delivery()
        delivery.grade(MoistureReading(12), Money(1000))
        with self.assertRaises(DeliveryAlreadyGraded):
            delivery.grade(MoistureReading(11), Money(2000))
        with self.assertRaises(DeliveryAlreadyGraded):
            delivery.add_bag(4, Weight(30))
        with self.assertRaises(AttributeError):
            delivery.status = DeliveryStatus.RECEIVED
        with self.assertRaises(AttributeError):
            delivery.delivery_id = "D999"
        self.assertEqual(delivery.status, DeliveryStatus.GRADED)
        self.assertEqual(delivery.payout, Money(1000))

    def test_t3_br3_bag_invariants(self):
        delivery = make_delivery(weights=(30,) * 10)
        with self.assertRaises(BagLimitExceeded):
            delivery.add_bag(11, Weight(30))
        self.assertEqual(len(delivery.bags), 10)
        delivery = make_delivery(weights=(60,))
        with self.assertRaises(DuplicateBag):
            delivery.add_bag(1, Weight(30))
        with self.assertRaises(FrozenInstanceError):
            delivery.bags[0].number = 99
        for weight in (0, -1, 60.1, float("nan"), float("inf")):
            with self.assertRaises(InvalidWeight):
                Weight(weight)
        self.assertEqual(delivery.bags[0].weight, Weight(60))
        empty = make_delivery(weights=())
        with self.assertRaises(EmptyDelivery):
            empty.grade(MoistureReading(12), Money(0))
        self.assertEqual(empty.status, DeliveryStatus.RECEIVED)
        self.assertEqual(empty.pull_events(), [])

    def test_t4_br4_payout_and_daily_price(self):
        calculator = PayoutCalculator()
        self.assertEqual(calculator.calculate(make_delivery(), self.board), Money(1_800_000))
        self.board.set_price(CoffeeType.ROBUSTA, DAY + timedelta(days=1), Money(15_000))
        self.assertEqual(calculator.calculate(make_delivery(), self.board), Money(1_800_000))
        with self.assertRaises(PriceNotAvailable):
            calculator.calculate(make_delivery(coffee_type=CoffeeType.ARABICA), self.board)
        with self.assertRaises(PriceNotAvailable):
            calculator.calculate(make_delivery(on=DAY - timedelta(days=1)), self.board)

    def test_t5_br5_grading_records_event(self):
        delivery = make_delivery("D005", "F005")
        delivery.grade(MoistureReading(12), Money(600_000))
        self.assertEqual(delivery.pull_events(), [DeliveryGraded("D005", "F005", Money(600_000))])
        self.assertEqual(delivery.pull_events(), [])

    def test_t6_br6_both_lookups_required(self):
        account = FarmerAccount("F001", "Nakato Sarah")
        self.accounts.save(account)
        missing = self.service.execute(GradeDeliveryInput("D404", 12))
        self.assertEqual(missing.status, "NotFound")
        self.assertFalse(missing.farmer_credited)
        self.assertIsNone(self.deliveries.get("D404"))
        delivery = make_delivery("D002", "F404")
        self.deliveries.save(delivery)
        result = self.service.execute(GradeDeliveryInput("D002", 12))
        self.assertEqual(result.status, "NotFound")
        self.assertFalse(result.farmer_credited)
        self.assertEqual(delivery.status, DeliveryStatus.RECEIVED)
        self.assertEqual(account.balance, Money.zero())
        self.assertEqual(delivery.pull_events(), [])

    def test_t7_main_use_case_and_duplicate_credit(self):
        account = FarmerAccount("F001", "Nakato Sarah")
        self.accounts.save(account)
        self.deliveries.save(make_delivery())
        result = self.service.execute(GradeDeliveryInput("D001", 12.5))
        self.assertEqual(result.status, "Graded")
        self.assertEqual(result.payout_ugx, 1_800_000)
        self.assertTrue(result.farmer_credited)
        self.assertEqual(self.deliveries.get("D001").status, DeliveryStatus.GRADED)
        self.assertEqual(account.balance, Money(1_800_000))
        self.assertTrue(account.has_credited("D001"))
        duplicate = CreditFarmerOnDeliveryGraded(self.accounts).handle(
            DeliveryGraded("D001", "F001", Money(1_800_000)))
        self.assertFalse(duplicate.credited)
        self.assertIn("already credited", duplicate.reason)
        self.assertEqual(account.balance, Money(1_800_000))

    def test_t8_suspended_account_rejects_follow_up(self):
        account = FarmerAccount("F002", "Okello James", AccountStatus.SUSPENDED)
        self.accounts.save(account)
        self.deliveries.save(make_delivery("D002", "F002"))
        result = self.service.execute(GradeDeliveryInput("D002", 12.5))
        self.assertEqual(result.status, "Graded")
        self.assertEqual(result.payout_ugx, 1_800_000)
        self.assertFalse(result.farmer_credited)
        self.assertIn("suspended", result.message)
        self.assertEqual(self.deliveries.get("D002").status, DeliveryStatus.GRADED)
        self.assertEqual(account.balance, Money.zero())
        self.assertFalse(account.has_credited("D002"))
        self.assertEqual(account.status, AccountStatus.SUSPENDED)


if __name__ == "__main__":
    unittest.main()
