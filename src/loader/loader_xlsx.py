
from typing import Any

try:
    from common import open_excel_workbook, read_excel_matrix
    from model.config import AxisConfig, ImportConfig
except ModuleNotFoundError:
    from src.common import open_excel_workbook, read_excel_matrix
    from src.model.config import AxisConfig, ImportConfig


def _read_axis_values(sheet: Any, axis_config: AxisConfig) -> list[Any]:
    """Read values from one configured row/column axis."""
    is_row = axis_config.row
    index = axis_config.index
    has_header = axis_config.header

    if is_row:
        values = next(
            sheet.iter_rows(min_row=index, max_row=index, values_only=True),
            tuple(),
        )
    else:
        values = tuple(
            row[0]
            for row in sheet.iter_rows(
                min_col=index,
                max_col=index,
                values_only=True,
            )
            if row
        )
    values = [v for v in values if v is not None]

    if has_header and values:
        values = values[1:]

    return values


def load_file(file_path: str, config: ImportConfig) -> dict[str, list[Any]]:
    """Load configured date/worker arrays from the first worksheet of an XLSX file."""
    date_index = config.date_axis.index
    worker_index = config.worker_axis.index

    with open_excel_workbook(file_path, data_only=True, read_only=True) as workbook:
        sheet = workbook.active
        dates = _read_axis_values(sheet, config.date_axis)
        workers = _read_axis_values(sheet, config.worker_axis)
        shifts = read_excel_matrix(
            sheet,
            start_row=date_index + 1,
            start_col=worker_index + 1,
            row_count=len(workers),
            col_count=len(dates),
        )

    return {"dates": dates, "workers": workers, "shifts": shifts}