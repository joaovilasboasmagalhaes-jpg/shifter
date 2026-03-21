from datetime import date

import pytest

try:
    from loader.loader import _parse_import_dates, _parse_shift_types
    from model.config import Config
    from model.shift_type import ShiftBreakType, ShiftWorkType
except ModuleNotFoundError:
    from src.loader.loader import _parse_import_dates, _parse_shift_types
    from src.model.config import Config
    from src.model.shift_type import ShiftBreakType, ShiftWorkType


def test_parse_import_dates_accepts_date_and_datetime():
    raw_dates = [10, 11]

    parsed = _parse_import_dates(raw_dates, 2026, 2)

    assert parsed == [date(2026, 2, 10), date(2026, 2, 11)]


def test_parse_import_dates_parses_integer_days_using_year_month():
    raw_dates = [1, 15, 28]

    parsed = _parse_import_dates(raw_dates, 2026, 2)

    assert parsed == [date(2026, 2, 1), date(2026, 2, 15), date(2026, 2, 28)]


def test_parse_import_dates_rejects_invalid_day():
    with pytest.raises(ValueError):
        _parse_import_dates([31], 2026, 2)


def test_parse_import_dates_rejects_unsupported_value_type():
    with pytest.raises(ValueError):
        _parse_import_dates(["x"], 2026, 2)


def test_parse_shift_types_preserves_matrix_structure():
    raw_shifts = [["M", "A"], ["N", "V"]]

    parsed = _parse_shift_types(raw_shifts)

    assert parsed == [
        [ShiftWorkType.MORNING, ShiftWorkType.AFTERNOON],
        [ShiftWorkType.NIGHT, ShiftBreakType.VACATION],
    ]


def test_parse_shift_types_raises_on_unknown_label_with_position():
    with pytest.raises(ValueError, match="row 0, column 1"):
        _parse_shift_types([["M", "UNKNOWN"]])


def test_parse_shift_types_uses_config_overrides():
    Config.reset()
    Config.set_data(
        {
            "import": {
                "date": {"row": True, "index": 1, "header": True},
                "worker": {"row": False, "index": 1, "header": True},
                "year": 2026,
                "month": 2,
                "shift_types": {
                    "morning": "M",
                    "afternoon": "T",
                    "night": "N",
                    "vacation": "FE",
                    "day_off": "F",
                },
            }
        }
    )

    raw_shifts = [["M", "T"], ["N", "FE"]]
    parsed = _parse_shift_types(raw_shifts)

    assert parsed == [
        [ShiftWorkType.MORNING, ShiftWorkType.AFTERNOON],
        [ShiftWorkType.NIGHT, ShiftBreakType.VACATION],
    ]
    Config.reset()
