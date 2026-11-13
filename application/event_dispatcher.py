"""Simple in-process event dispatcher.

Handlers are registered by event type. dispatch() calls each handler
straight away and returns their outcomes, so the application service can
report what happened in its output DTO.
"""
from collections import defaultdict


class EventDispatcher:
    def __init__(self):
        self._handlers = defaultdict(list)

    def register(self, event_type, handler) -> None:
        self._handlers[event_type].append(handler)

    def dispatch(self, events) -> list:
        outcomes = []
        for event in events:
            for handler in self._handlers[type(event)]:
                outcomes.append(handler.handle(event))
        return outcomes
