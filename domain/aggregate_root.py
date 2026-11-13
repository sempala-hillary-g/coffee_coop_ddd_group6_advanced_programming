"""Layer Supertype for the domain layer.

Both aggregate roots (Delivery and FarmerAccount) extend this class so
the event-recording behaviour is written once instead of in each root.
"""


class AggregateRoot:
    def __init__(self):
        self._pending_events = []

    def record_event(self, event) -> None:
        self._pending_events.append(event)

    def pull_events(self) -> list:
        """Return recorded events and clear them, so each is dispatched once."""
        events, self._pending_events = self._pending_events, []
        return events
