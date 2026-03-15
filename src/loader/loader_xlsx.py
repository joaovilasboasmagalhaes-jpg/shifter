
from typing import Any, Dict, List

try:
	from common import open_excel_workbook
except ModuleNotFoundError:
	from src.common import open_excel_workbook


def _read_axis_values(sheet: Any, axis_config: Dict[str, Any]) -> List[Any]:
	"""Read values from one configured row/column axis."""
	is_row = bool(axis_config.get("row", False))
	index = axis_config.get("index")
	has_header = bool(axis_config.get("header", False))

	if not isinstance(index, int) or index < 1:
		raise ValueError("Axis index must be an integer greater than or equal to 1")

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


def load_file(file_path: str, config: Dict[str, Any]) -> Dict[str, List[Any]]:
	"""Load configured date/worker arrays from the first worksheet of an XLSX file."""
	if not isinstance(config, dict):
		raise ValueError("config must be a dictionary")

	if "date" not in config or "worker" not in config:
		raise ValueError("config must contain both 'date' and 'worker' keys")

	with open_excel_workbook(file_path, data_only=True, read_only=True) as workbook:
		sheet = workbook.active
		dates = _read_axis_values(sheet, config["date"])
		workers = _read_axis_values(sheet, config["worker"])

	return {"dates": dates, "workers": workers}