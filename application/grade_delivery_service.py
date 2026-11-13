"""Main use case: Grade Delivery.

The service coordinates. It looks things up (BR6), builds the value
object (BR1), asks the domain service for the payout (BR4), tells the
aggregate to grade itself (BR2, BR3, records BR5 event), saves, and
dispatches the event. It holds no business rules of its own.

Dependencies arrive through the constructor (dependency injection), so
the service never creates its own repositories or price board.
"""
from application.dtos import GradeDeliveryInput, GradeDeliveryOutput
from application.event_dispatcher import EventDispatcher
from application.repositories import (
    DeliveryRepository,
    FarmerAccountRepository,
)
from domain.errors import DomainError
from domain.moisture_reading import MoistureReading
from domain.payout_calculator import PayoutCalculator, PriceBoard


class GradeDeliveryService:
    def __init__(self, deliveries: DeliveryRepository,
                 accounts: FarmerAccountRepository,
                 price_board: PriceBoard,
                 calculator: PayoutCalculator,
                 dispatcher: EventDispatcher):
        self._deliveries = deliveries
        self._accounts = accounts
        self._price_board = price_board
        self._calculator = calculator
        self._dispatcher = dispatcher

    def execute(self, request: GradeDeliveryInput) -> GradeDeliveryOutput:
        # BR6: the delivery and its farmer must already exist
        delivery = self._deliveries.get(request.delivery_id)
        if delivery is None:
            return self._not_found(request.delivery_id,
                                   f"BR6: delivery {request.delivery_id} not found")
        if self._accounts.get(delivery.farmer_id) is None:
            return self._not_found(request.delivery_id,
                                   f"BR6: farmer {delivery.farmer_id} not found")

        try:
            moisture = MoistureReading(request.moisture_percent)          # BR1
            payout = self._calculator.calculate(delivery, self._price_board)  # BR4
            delivery.grade(moisture, payout)                              # BR2, BR3, BR5
        except DomainError as error:
            return GradeDeliveryOutput(request.delivery_id, "Rejected",
                                       None, False, str(error))

        self._deliveries.save(delivery)
        outcomes = self._dispatcher.dispatch(delivery.pull_events())

        credited = bool(outcomes) and all(o.credited for o in outcomes)
        message = "; ".join(o.reason for o in outcomes) or "Graded"
        return GradeDeliveryOutput(request.delivery_id, delivery.status.value,
                                   payout.ugx, credited, message)

    @staticmethod
    def _not_found(delivery_id: str, message: str) -> GradeDeliveryOutput:
        return GradeDeliveryOutput(delivery_id, "NotFound", None, False, message)
