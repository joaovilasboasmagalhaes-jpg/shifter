import argparse

try:
    from common import load_json_config, resolve_file_path, validate_existing_file_path

    from .loader_xlsx import load_file as load_xlsx_file
except ModuleNotFoundError:
    from src.common import (
        load_json_config,
        resolve_file_path,
        validate_existing_file_path,
    )
    from src.loader.loader_xlsx import load_file as load_xlsx_file


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


def load_file(args: argparse.Namespace) -> None:
    """Load shifts using parsed CLI arguments."""

    config = load_json_config(getattr(args, "config_path", ""), required_root_keys=("import",))
    file_type = _resolve_file_type(args)
    file_path = validate_existing_file_path(args.file_path)

    if file_type == EXCEL:
        load_xlsx_file(file_path, config["import"])
        return
    raise NotImplementedError(f"Unsupported file type: {file_type}")
