"""T1 - BR1 (Value rule): a moisture reading must be between 8.0% and 13.0% inclusive.

This is the test used for the TDD example. It was written before
MoistureReading existed, run to fail, then the class was implemented.
"""
import pytest

from domain.errors import InvalidMoistureReading
from domain.moisture_reading import MoistureReading


def test_t1_br1_moisture_upper_boundary_accepted_and_just_above_rejected():
    # Boundary case: exactly 13.0% is accepted
    reading = MoistureReading(13.0)
    assert reading.percent == 13.0

    # Rejection case: 13.1% is too wet
    with pytest.raises(InvalidMoistureReading):
        MoistureReading(13.1)
