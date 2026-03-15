import pytest

from src.model.shift_type import ShiftBreakType, ShiftType, ShiftWorkType


def test_work_shift_labels_and_hours():
    assert ShiftWorkType.NIGHT.to_string() == "Night"
    assert ShiftWorkType.NIGHT.hours_range() == (0, 8)
    assert ShiftWorkType.MORNING.to_string() == "Morning"
    assert str(ShiftWorkType.AFTERNOON) == "Afternoon"
    assert repr(ShiftWorkType.AFTERNOON) == "A"
    assert ShiftWorkType.AFTERNOON.hours_range() == (16, 24)


def test_break_shift_labels():
    assert ShiftBreakType.DAY_OFF.to_string() == "DayOff"
    assert ShiftBreakType.VACATION.to_string() == "Vacation"
    assert repr(ShiftBreakType.VACATION) == "V"


def test_shift_type_from_short_label_resolves_work_and_break():
    assert ShiftType.from_short_label("M") == ShiftWorkType.MORNING
    assert ShiftType.from_short_label("V") == ShiftBreakType.VACATION


def test_shift_type_from_short_label_respects_config_overrides():
    config = {
        "morning": "M",
        "afternoon": "T",
        "night": "N",
        "vacation": "FE",
        "day off": "F",
    }
    assert ShiftType.from_short_label("T", config) == ShiftWorkType.AFTERNOON
    assert ShiftType.from_short_label("FE", config) == ShiftBreakType.VACATION


def test_shift_type_from_short_label_raises_for_unknown_label():
    with pytest.raises(ValueError):
        ShiftType.from_short_label("UNKNOWN")
