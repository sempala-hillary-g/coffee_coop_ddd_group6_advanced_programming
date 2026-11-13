"""BR1 - Value rule.

A moisture reading must be between 8.0% and 13.0% inclusive for coffee
to be accepted. Below 8% the beans are over-dried and brittle; above 13%
they are too wet to store safely.

MoistureReading is a Value Object: it has no identity of its own. Two
readings of 12.5% are interchangeable, so equality is by value and the
object is immutable (frozen).
"""
from dataclasses import dataclass

from domain.errors import InvalidMoistureReading

MIN_MOISTURE_PERCENT = 8.0
MAX_MOISTURE_PERCENT = 13.0


@dataclass(frozen=True)
class MoistureReading:
    percent: float

    def __post_init__(self):
        if not (MIN_MOISTURE_PERCENT <= self.percent <= MAX_MOISTURE_PERCENT):
            raise InvalidMoistureReading(
                f"BR1: moisture {self.percent}% is outside the accepted range "
                f"{MIN_MOISTURE_PERCENT}% to {MAX_MOISTURE_PERCENT}%"
            )
