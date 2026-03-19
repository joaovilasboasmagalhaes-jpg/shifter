import argparse
from datetime import date as Date
from typing import Any

try:
    from model.worker import Worker
except ModuleNotFoundError:
    from src.model.worker import Worker

try:
    from common import (
        build_import_date,
        load_json_config,
        resolve_file_path,
        validate_existing_file_path,
    )
    from model.schedule import Schedule
    from model.shift import Shift
    from model.shift_type import ShiftType

    from .loader_xlsx import load_file as load_xlsx_file
except ModuleNotFoundError:
    from src.common import (
        build_import_date,
        load_json_config,
        resolve_file_path,
        validate_existing_file_path,
    )
    from src.loader.loader_xlsx import load_file as load_xlsx_file
    from src.model.schedule import Schedule
    from src.model.shift import Shift
    from src.model.shift_type import ShiftType


EXCEL = "xlsx"


def _resolve_file_type(args: argparse.Namespace) -> str:
    """Resolve and normalize file path/type from CLI arguments."""
    resolved_file_path, resolved_file_type = resolve_file_path(
        file_path=getattr(args, "file_path", ""),
        file_type=getattr(args, "file_type", None),
    )
    if not resolved_file_type:
        raise ValueError(
            "Could not resolve file type. Provide --file-type or use a file path with an extension."
        )

    args.file_path = resolved_file_path
    return resolved_file_type

def _parse_import_dates(days: list[int], import_config: dict[str, Any]) -> list[Date]:
    year = import_config.get("year")
    month = import_config.get("month")

    if not year or not month:
        raise ValueError(
            "Import config must contain 'year' and 'month' for parsing dates"
        )

    parsed_dates: list[Date] = []
    for idx, day in enumerate(days):
        try:
            parsed_dates.append(build_import_date(year, month, day))
        except ValueError as exc:
            raise ValueError(
                f"Invalid day '{day}' at date index {idx} for {year:04d}-{month:02d}"
            ) from exc

    return parsed_dates


def _parse_shift_types(
    raw_shifts: list[list[Any]], shift_type_config: dict[str, str] | None = None
) -> list[list[ShiftType]]:
    """Convert raw shift short-label matrix to a ShiftType matrix."""
    shift_type_config = shift_type_config or {}
    parsed_shift_types: list[list[ShiftType]] = []

    for row_index, row in enumerate(raw_shifts):
        parsed_row: list[ShiftType] = []
        for col_index, cell in enumerate(row):
            try:
                parsed_row.append(
                    ShiftType.from_short_label(str(cell), shift_type_config)
                )
            except ValueError as exc:
                raise ValueError(
                    f"Invalid shift label at row {row_index}, column {col_index}: {cell!r}"
                ) from exc
        parsed_shift_types.append(parsed_row)

    return parsed_shift_types


def _build_shedule(
    dates: list[Date], workers: list[Worker], shift_types: list[list[ShiftType]]
) -> Schedule:
    """Build a list of Shifts from the given dates, workers, and shift type matrix."""
    schedule: Schedule = Schedule(
        start_date=dates[0], end_date=dates[-1], shifts_by_worker={}
    )
    for row_index, (worker, shift_type_row) in enumerate(zip(workers, shift_types)):
        for col_index, (d, shift_type) in enumerate(zip(dates, shift_type_row)):
            schedule.add_shift(Shift(date=d, worker=worker, shift_type=shift_type))
    return schedule

def load_file(args: argparse.Namespace) -> None:
    """Load shifts using parsed CLI arguments."""

    config = load_json_config(getattr(args, "config_path", ""), required_root_keys=("import",))
    import_config: dict[str, Any] = config.get("import", {})
    if not import_config or not isinstance(import_config, dict):
        raise ValueError("Config 'import' key must contain an object")
    file_type = _resolve_file_type(args)
    file_path = validate_existing_file_path(args.file_path)

    raw_dates, raw_workers, raw_shifts = [], [], []

    if file_type == EXCEL:
        loaded = load_xlsx_file(file_path, import_config)
        raw_dates = loaded.get("dates", [])
        raw_workers = loaded.get("workers", [])
        raw_shifts = loaded.get("shifts", [])
    else:
        raise NotImplementedError(f"Unsupported file type: {file_type}")

    shift_types = _parse_shift_types(raw_shifts, import_config.get("shift_types", {}))

    dates = _parse_import_dates(raw_dates, import_config)
    workers = [Worker(name=str(w)) for w in raw_workers]
    schedule = _build_shedule(dates, workers, shift_types)

