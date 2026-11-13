"""Shared test wiring. Builds the same object graph as the interface layer,
using the in-memory infrastructure, so T6 to T8 run the real use case."""
from dataclasses import dataclass
from datetime import date

import pytest

from application.credit_farmer_handler import CreditFarmerOnDeliveryGraded
from application.event_dispatcher import EventDispatcher
from application.grade_delivery_service import GradeDeliveryService
from domain.coffee_type import CoffeeType
from domain.delivery import Delivery
from domain.events import DeliveryGraded
from domain.money import Money
from domain.payout_calculator import PayoutCalculator
from domain.weight import Weight
from infrastructure.in_memory_price_board import InMemoryPriceBoard
from infrastructure.in_memory_repositories import (
    InMemoryDeliveryRepository,
    InMemoryFarmerAccountRepository,
)

DELIVERY_DATE = date(2026, 11, 6)
ROBUSTA_PRICE = Money(12_000)


@dataclass
class World:
    service: GradeDeliveryService
    deliveries: InMemoryDeliveryRepository
    accounts: InMemoryFarmerAccountRepository
    board: InMemoryPriceBoard


@pytest.fixture
def world() -> World:
    deliveries = InMemoryDeliveryRepository()
    accounts = InMemoryFarmerAccountRepository()
    board = InMemoryPriceBoard()
    board.set_price(CoffeeType.ROBUSTA, DELIVERY_DATE, ROBUSTA_PRICE)

    dispatcher = EventDispatcher()
    dispatcher.register(DeliveryGraded, CreditFarmerOnDeliveryGraded(accounts))

    service = GradeDeliveryService(deliveries, accounts, board,
                                   PayoutCalculator(), dispatcher)
    return World(service, deliveries, accounts, board)


def make_delivery(delivery_id="D001", farmer_id="F001",
                  coffee_type=CoffeeType.ROBUSTA, bag_weights=(50, 50, 50)):
    delivery = Delivery(delivery_id, farmer_id, coffee_type, DELIVERY_DATE)
    for number, kg in enumerate(bag_weights, start=1):
        delivery.add_bag(number, Weight(kg))
    return delivery
