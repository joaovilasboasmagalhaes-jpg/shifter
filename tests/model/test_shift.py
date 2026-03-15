from datetime import date

from src.model.shift import Shift
from src.model.shift_type import ShiftBreakType, ShiftWorkType
from src.model.worker import Worker


def test_shift_representation():
    w = Worker(name="Bob")
    s = Shift(shift_type=ShiftWorkType.MORNING, date=date(2026, 3, 14), worker=w)
    assert s.to_string() == "Morning on 2026-03-14 - Bob"
    assert str(s) == s.to_string()


def test_shift_with_break():
    w = Worker(name="Carol")
    s = Shift(shift_type=ShiftBreakType.VACATION, date=date(2026, 3, 15), worker=w)
    assert str(s) == "Vacation on 2026-03-15 - Carol"
