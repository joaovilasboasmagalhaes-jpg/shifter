from src.model.shift_type import ShiftBreakType, ShiftWorkType


def test_work_shift_labels_and_hours():
    assert ShiftWorkType.NIGHT.to_string() == "Night"
    assert ShiftWorkType.NIGHT.hours_range() == (0, 8)
    assert ShiftWorkType.MORNING.to_string() == "Morning"
    assert str(ShiftWorkType.AFTERNOON) == "Afternoon"
    assert ShiftWorkType.AFTERNOON.hours_range() == (16, 24)


def test_break_shift_labels():
    assert ShiftBreakType.DAY_OFF.to_string() == "DayOff"
    assert ShiftBreakType.VACATION.to_string() == "Vacation"
