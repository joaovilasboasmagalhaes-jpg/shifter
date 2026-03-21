from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple, cast

try:
    from utils.loading import load_json_config
except ModuleNotFoundError:
    from src.utils.loading import load_json_config


@dataclass(frozen=True)
class AxisConfig:
    """Typed spreadsheet axis configuration."""

    row: bool
    index: int
    header: bool

    @classmethod
    def from_mapping(cls, data: object, *, section_name: str) -> "AxisConfig":
        if not isinstance(data, Mapping):
            raise ValueError(f"Config section '{section_name}' must contain an object")

        mapping = cast(Mapping[str, Any], data)
        index = mapping.get("index")
        if not isinstance(index, int) or index < 1:
            raise ValueError(
                f"Config section '{section_name}.index' must be an integer greater than or equal to 1"
            )

        return cls(
            row=bool(mapping.get("row", False)),
            index=index,
            header=bool(mapping.get("header", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"row": self.row, "index": self.index, "header": self.header}


@dataclass(frozen=True)
class ImportConfig:
    """Typed import configuration parsed from JSON."""

    date_axis: AxisConfig
    worker_axis: AxisConfig
    year: int
    month: int
    shift_type_labels: dict[str, str]

    @classmethod
    def from_mapping(cls, data: object) -> "ImportConfig":
        if not isinstance(data, Mapping):
            raise ValueError("Config 'import' key must contain an object")

        mapping = cast(Mapping[str, Any], data)
        year = mapping.get("year")
        month = mapping.get("month")
        shift_types = mapping.get("shift_types", {})

        if not isinstance(year, int):
            raise ValueError("Import config 'year' must be an integer")
        if not isinstance(month, int):
            raise ValueError("Import config 'month' must be an integer")
        if month < 1 or month > 12:
            raise ValueError("Import config 'month' must be between 1 and 12")
        if not isinstance(shift_types, Mapping):
            raise ValueError("Import config 'shift_types' must contain an object")

        shift_type_labels = {
            str(key): str(value)
            for key, value in cast(Mapping[object, object], shift_types).items()
        }

        return cls(
            date_axis=AxisConfig.from_mapping(
                mapping.get("date"), section_name="import.date"
            ),
            worker_axis=AxisConfig.from_mapping(
                mapping.get("worker"), section_name="import.worker"
            ),
            year=year,
            month=month,
            shift_type_labels=shift_type_labels,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date_axis.to_dict(),
            "worker": self.worker_axis.to_dict(),
            "year": self.year,
            "month": self.month,
            "shift_types": dict(self.shift_type_labels),
        }


class Config:
    """Runtime singleton that stores application configuration and helpers."""

    _instance: Optional["Config"] = None

    _data: dict[str, Any]
    _config_path: Optional[str]
    _import_settings: Optional[ImportConfig]

    def __new__(cls, *args: object, **kwargs: object) -> "Config":
        del args, kwargs
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = {}
            cls._instance._config_path = None
            cls._instance._import_settings = None
        return cls._instance

    @classmethod
    def instance(cls) -> "Config":
        """Return the unique Config instance for the current runtime."""
        return cls()

    @classmethod
    def get_instance(cls) -> "Config":
        """Return the initialized singleton or raise if it is not ready."""
        if cls._instance is None or cls._instance._import_settings is None:
            raise RuntimeError(
                "Config singleton is not initialized. "
                "Call Config.load_from_file(...) during startup first."
            )
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton state. Intended for tests."""
        cls._instance = None

    @classmethod
    def load_from_file(
        cls,
        config_path: str,
        required_root_keys: Optional[Tuple[str, ...]] = None,
    ) -> "Config":
        """Load configuration from JSON and store it in the singleton."""
        config_data = load_json_config(
            config_path, required_root_keys=required_root_keys
        )
        instance = cls.instance()
        instance._set_loaded_data(config_data, config_path)
        return instance

    @classmethod
    def set_data(cls, data: object) -> "Config":
        """Set singleton config data directly (useful for tests/bootstrap)."""
        if not isinstance(data, Mapping):
            raise ValueError("Config data must be a mapping")
        instance = cls.instance()
        instance._set_loaded_data(dict(cast(Mapping[str, Any], data)), None)
        return instance

    def _set_loaded_data(
        self, data: Mapping[str, Any], config_path: Optional[str]
    ) -> None:
        self._data = dict(data)
        self._config_path = config_path
        import_section = self._data.get("import")
        self._import_settings = (
            ImportConfig.from_mapping(import_section)
            if import_section is not None
            else None
        )

    @property
    def config_path(self) -> Optional[str]:
        return self._config_path

    @property
    def import_year(self) -> int:
        return self.import_config().year

    @property
    def import_month(self) -> int:
        return self.import_config().month

    @property
    def date_axis(self) -> AxisConfig:
        return self.import_config().date_axis

    @property
    def worker_axis(self) -> AxisConfig:
        return self.import_config().worker_axis

    @property
    def shift_type_labels(self) -> dict[str, str]:
        return dict(self.import_config().shift_type_labels)

    def to_dict(self) -> dict[str, Any]:
        """Return a shallow copy of the loaded config dictionary."""
        return self._data.copy()

    def import_config(self) -> ImportConfig:
        """Return validated import configuration section."""
        if self._import_settings is None:
            raise ValueError("Config 'import' key must contain an object")
        return self._import_settings
