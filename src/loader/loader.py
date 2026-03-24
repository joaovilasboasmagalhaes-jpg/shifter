import argparse
from datetime import date as Date

from src.loader.loader_xlsx import load_file as load_xlsx_file
from src.model.config import Config
from src.model.schedule import Schedule
from src.model.shift import Shift
from src.model.shift_type import ShiftType
from src.model.worker import Worker
from src.utils.date_utils import build_import_date
from src.utils.errors.error_handler import ErrorHandler as Error
from src.utils.loading import resolve_file_path, validate_existing_file_path

EXCEL = "xlsx"


def _resolve_file_type(args: argparse.Namespace) -> str:
    """Resolve and normalize file path/type from CLI arguments."""
    resolved_file_path, resolved_file_type = resolve_file_path(
        file_path=getattr(args, "file_path", ""),
        file_type=getattr(args, "file_type", None),
    )
    if not resolved_file_type:
        raise ValueError(Error.get_message("system_errors.could_not_resolve_file_type"))

    args.file_path = resolved_file_path
    return resolved_file_type

def _parse_import_dates(days: list[int], year: int, month: int) -> list[Date]:
    parsed_dates: list[Date] = []
    for idx, day in enumerate(days):
        try:
            parsed_dates.append(build_import_date(year, month, day))
        except ValueError as exc:
            raise ValueError(
                Error.get_message(
                    "errors.invalid_day_at_index",
                    day=day,
                    idx=idx,
                    year=year,
                    month=month,
                )
            ) from exc

    return parsed_dates


def _parse_shift_types(raw_shifts: list[list[object]]) -> list[list[ShiftType]]:
    """Convert raw shift short-label matrix to a ShiftType matrix."""
    parsed_shift_types: list[list[ShiftType]] = []

    for row_index, row in enumerate(raw_shifts):
        parsed_row: list[ShiftType] = []
        for col_index, cell in enumerate(row):
            try:
                parsed_row.append(ShiftType.from_short_label(str(cell)))
            except ValueError as exc:
                raise ValueError(
                    Error.get_message(
                        "system_errors.invalid_shift_label",
                        row=row_index,
                        col=col_index,
                        cell=cell,
                    )
                ) from exc
        parsed_shift_types.append(parsed_row)

    return parsed_shift_types


def _build_schedule(
    dates: list[Date], workers: list[Worker], shift_types: list[list[ShiftType]]
) -> Schedule:
    """Build a list of Shifts from the given dates, workers, and shift type matrix."""
    schedule: Schedule = Schedule(
        start_date=dates[0], end_date=dates[-1], shifts_by_worker={}
    )
    for worker, shift_type_row in zip(workers, shift_types):
        for d, shift_type in zip(dates, shift_type_row):
            schedule.add_shift(Shift(date=d, worker=worker, shift_type=shift_type))
    return schedule

def load_file(args: argparse.Namespace) -> Schedule:
    """Load shifts using parsed CLI arguments."""

    config = Config.get_instance()
    import_config = config.import_config()
    file_type = _resolve_file_type(args)
    file_path = validate_existing_file_path(args.file_path)

    raw_dates, raw_workers, raw_shifts = [], [], []

    if file_type == EXCEL:
        loaded = load_xlsx_file(file_path, import_config)
        raw_dates = loaded.get("dates", [])
        raw_workers = loaded.get("workers", [])
        raw_shifts = loaded.get("shifts", [])
    else:
        raise NotImplementedError(
            Error.get_message(
                "system_errors.unsupported_file_type", file_type=file_type
            )
        )

    shift_types = _parse_shift_types(raw_shifts)

    dates = _parse_import_dates(raw_dates, config.import_year, config.import_month)
    workers = [Worker(name=str(w)) for w in raw_workers]
    return _build_schedule(dates, workers, shift_types)

