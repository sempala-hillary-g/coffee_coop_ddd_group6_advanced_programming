"""Interface layer: a minimal interactive command-line entry point.

This is the composition root. It creates the concrete infrastructure,
injects it into the application service and lets the user try the
business rules with their own values.

The interface holds no business rules. Every check happens in the domain
or application layer; this file only reads input, calls them, and prints
what they report.

The two use cases are Grade Delivery (menu option 1, through
GradeDeliveryService) and Credit Farmer Account (triggered by the
DeliveryGraded event). The other menu options are a test harness for
setting up data; they call the aggregates directly, which still enforce
their own rules.

Run interactively:      python -m interface.main
Run the scripted demo:  python -m interface.main --demo
"""
import sys
from datetime import date

from application.credit_farmer_handler import CreditFarmerOnDeliveryGraded
from application.dtos import GradeDeliveryInput
from application.event_dispatcher import EventDispatcher
from application.grade_delivery_service import GradeDeliveryService
from domain.coffee_type import CoffeeType
from domain.delivery import Delivery
from domain.errors import DomainError
from domain.events import DeliveryGraded
from domain.farmer_account import AccountStatus, FarmerAccount
from domain.money import Money
from domain.payout_calculator import PayoutCalculator
from domain.weight import Weight
from infrastructure.in_memory_price_board import InMemoryPriceBoard
from infrastructure.in_memory_repositories import (
    InMemoryDeliveryRepository,
    InMemoryFarmerAccountRepository,
)


# ---------------------------------------------------------------- wiring

def build_service():
    deliveries = InMemoryDeliveryRepository()
    accounts = InMemoryFarmerAccountRepository()
    board = InMemoryPriceBoard()

    dispatcher = EventDispatcher()
    dispatcher.register(DeliveryGraded, CreditFarmerOnDeliveryGraded(accounts))

    # Dependency injection: concrete implementations are passed in here
    service = GradeDeliveryService(deliveries, accounts, board,
                                   PayoutCalculator(), dispatcher)
    return service, deliveries, accounts, board


def seed(deliveries, accounts, board, on: date):
    """Sample data so every rule can be tried without typing setup first.
    Only Robusta has a price, so grading an Arabica delivery shows BR4."""
    board.set_price(CoffeeType.ROBUSTA, on, Money(12_000))
    accounts.save(FarmerAccount("F001", "Nakato Sarah"))
    accounts.save(FarmerAccount("F002", "Okello James", AccountStatus.SUSPENDED))
    for delivery_id, farmer_id in (("D001", "F001"), ("D002", "F002")):
        delivery = Delivery(delivery_id, farmer_id, CoffeeType.ROBUSTA, on)
        delivery.add_bag(1, Weight(50))
        delivery.add_bag(2, Weight(48.5))
        deliveries.save(delivery)


# ---------------------------------------------------------------- input helpers

def ask(prompt: str) -> str:
    return input(f"  {prompt}: ").strip()


def ask_float(prompt: str) -> float | None:
    raw = ask(prompt)
    try:
        return float(raw)
    except ValueError:
        print(f"  '{raw}' is not a number.")
        return None


def ask_int(prompt: str) -> int | None:
    raw = ask(prompt)
    try:
        return int(raw)
    except ValueError:
        print(f"  '{raw}' is not a whole number.")
        return None


def ask_coffee_type() -> CoffeeType | None:
    raw = ask("Coffee type (A = Arabica, R = Robusta)").upper()
    return {"A": CoffeeType.ARABICA, "R": CoffeeType.ROBUSTA}.get(raw) or _bad(raw)


def _bad(raw):
    print(f"  '{raw}' is not a valid choice.")
    return None


def rejected(error: DomainError):
    print(f"  REJECTED  {error}")


# ---------------------------------------------------------------- menu actions

def grade_delivery(service, accounts, deliveries):
    delivery_id = ask("Delivery ID")
    moisture = ask_float("Moisture reading %")
    if moisture is None:
        return
    result = service.execute(GradeDeliveryInput(delivery_id, moisture))

    print(f"  Status:          {result.status}")
    if result.payout_ugx is not None:
        print(f"  Payout:          {Money(result.payout_ugx)}")
    print(f"  Farmer credited: {'Yes' if result.farmer_credited else 'No'}")
    print(f"  Message:         {result.message}")

    delivery = deliveries.get(delivery_id)
    if delivery and result.status == "Graded":
        account = accounts.get(delivery.farmer_id)
        print(f"  {account.farmer_id} balance now {account.balance}")


def record_delivery(deliveries, today: date):
    delivery_id = ask("New delivery ID")
    if deliveries.get(delivery_id):
        print(f"  Delivery {delivery_id} already exists.")
        return
    farmer_id = ask("Farmer ID")
    coffee_type = ask_coffee_type()
    if coffee_type is None:
        return
    deliveries.save(Delivery(delivery_id, farmer_id, coffee_type, today))
    print(f"  Delivery {delivery_id} recorded for {farmer_id} with no bags yet.")
    print("  (Farmer existence is checked when grading, under BR6.)")


def add_bag(deliveries):
    delivery = deliveries.get(ask("Delivery ID"))
    if delivery is None:
        print("  Delivery not found.")
        return
    number = ask_int("Bag number")
    kg = ask_float("Bag weight kg")
    if number is None or kg is None:
        return
    try:
        delivery.add_bag(number, Weight(kg))          # BR2, BR3 enforced here
    except DomainError as error:
        rejected(error)
        return
    deliveries.save(delivery)
    print(f"  Bag {number} added. {delivery.delivery_id} now has "
          f"{len(delivery.bags)} bag(s), {delivery.total_net_kg()} kg.")


def register_farmer(accounts):
    farmer_id = ask("New farmer ID")
    if accounts.get(farmer_id):
        print(f"  Farmer {farmer_id} already exists.")
        return
    name = ask("Name")
    accounts.save(FarmerAccount(farmer_id, name))
    print(f"  Farmer {farmer_id} registered as Active.")


def suspend_farmer(accounts):
    account = accounts.get(ask("Farmer ID"))
    if account is None:
        print("  Farmer not found.")
        return
    account.suspend()
    accounts.save(account)
    print(f"  {account.farmer_id} is now Suspended.")


def set_price(board, today: date):
    coffee_type = ask_coffee_type()
    if coffee_type is None:
        return
    amount = ask_int(f"Price per kg in UGX for {today.isoformat()}")
    if amount is None:
        return
    try:
        board.set_price(coffee_type, today, Money(amount))
    except DomainError as error:
        rejected(error)
        return
    print(f"  {coffee_type.value} set to {Money(amount)} per kg.")


def show_all(deliveries, accounts, board, today: date):
    print("  Farmers")
    for a in accounts.all():
        print(f"    {a.farmer_id}  {a.name:<16} {a.status.value:<10} balance {a.balance}")
    print("  Deliveries")
    for d in deliveries.all():
        payout = f"payout {d.payout}" if d.payout else ""
        print(f"    {d.delivery_id}  farmer {d.farmer_id}  {d.coffee_type.value:<8} "
              f"{len(d.bags)} bag(s) {d.total_net_kg():>6} kg  {d.status.value:<9} {payout}")
    print(f"  Prices for {today.isoformat()}")
    for t in CoffeeType:
        price = board.price_per_kg(t, today)
        print(f"    {t.value:<8} {price if price else 'not set'}")


# ---------------------------------------------------------------- main loops

MENU = """
------------------------------------------------------------
 Coffee Cooperative  |  try the business rules
------------------------------------------------------------
 1  Grade a delivery          (BR1, BR2, BR3, BR4, BR5, BR6)
 2  Record a new delivery
 3  Add a bag to a delivery   (BR2, BR3)
 4  Register a farmer
 5  Suspend a farmer          (sets up the T8 case)
 6  Set today's price         (BR4)
 7  Show farmers, deliveries and prices
 0  Exit
"""


def interactive():
    service, deliveries, accounts, board = build_service()
    today = date.today()
    seed(deliveries, accounts, board, today)

    print("\nSample data loaded: F001 (Active), F002 (Suspended), "
          "D001 and D002 (98.5 kg Robusta each), Robusta at UGX 12,000/kg.")

    actions = {
        "1": lambda: grade_delivery(service, accounts, deliveries),
        "2": lambda: record_delivery(deliveries, today),
        "3": lambda: add_bag(deliveries),
        "4": lambda: register_farmer(accounts),
        "5": lambda: suspend_farmer(accounts),
        "6": lambda: set_price(board, today),
        "7": lambda: show_all(deliveries, accounts, board, today),
    }

    while True:
        print(MENU)
        try:
            choice = input("Choose: ").strip()
        except EOFError:
            break
        if choice == "0":
            break
        action = actions.get(choice)
        if action is None:
            print("  Pick a number from the menu.")
            continue
        try:
            action()
        except EOFError:
            break
    print("Goodbye.")


def scripted_demo():
    """The original fixed run, kept for the evidence file."""
    service, deliveries, accounts, board = build_service()
    today = date(2026, 11, 6)
    seed(deliveries, accounts, board, today)
    for delivery_id in ("D001", "D002"):
        print(service.execute(GradeDeliveryInput(delivery_id, 12.5)))
    print(f"F001 balance: {accounts.get('F001').balance}")
    print(f"F002 balance: {accounts.get('F002').balance}")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        scripted_demo()
    else:
        interactive()
