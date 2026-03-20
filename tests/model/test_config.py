import json
from pathlib import Path
from typing import Any

import pytest

from src.model.config import AxisConfig, Config, ImportConfig


def test_config_is_singleton_instance():
    Config.reset()

    first = Config.instance()
    second = Config.instance()

    assert first is second


def test_config_get_instance_raises_when_not_initialized():
    Config.reset()

    with pytest.raises(RuntimeError, match="not initialized"):
        Config.get_instance()


def test_config_get_instance_returns_loaded_singleton(tmp_path: Path):
    Config.reset()
    config_path = tmp_path / "config.json"
    config_payload: dict[str, Any] = {
        "import": {
            "date": {"row": True, "index": 2, "header": True},
            "worker": {"row": False, "index": 2, "header": True},
            "year": 2026,
            "month": 2,
            "shift_types": {"morning": "M"},
        }
    }
    config_path.write_text(json.dumps(config_payload), encoding="utf-8")

    loaded = Config.load_from_file(str(config_path), required_root_keys=("import",))
    retrieved = Config.get_instance()

    assert retrieved is loaded


def test_config_load_from_file_stores_data_and_path(tmp_path: Path):
    Config.reset()
    config_path = tmp_path / "config.json"
    config_payload: dict[str, Any] = {
        "import": {
            "date": {"row": True, "index": 2, "header": True},
            "worker": {"row": False, "index": 2, "header": True},
            "year": 2026,
            "month": 2,
            "shift_types": {"morning": "M"},
        }
    }
    config_path.write_text(json.dumps(config_payload), encoding="utf-8")

    config = Config.load_from_file(str(config_path), required_root_keys=("import",))

    assert config.config_path == str(config_path)
    assert config.to_dict() == config_payload
    assert config.import_config() == ImportConfig(
        date_axis=AxisConfig(row=True, index=2, header=True),
        worker_axis=AxisConfig(row=False, index=2, header=True),
        year=2026,
        month=2,
        shift_type_labels={"morning": "M"},
    )


def test_config_exposes_typed_import_values(tmp_path: Path):
    Config.reset()
    config_path = tmp_path / "config.json"
    config_payload: dict[str, Any] = {
        "import": {
            "date": {"row": True, "index": 2, "header": True},
            "worker": {"row": False, "index": 3, "header": False},
            "year": 2027,
            "month": 11,
            "shift_types": {"night": "N"},
        }
    }
    config_path.write_text(json.dumps(config_payload), encoding="utf-8")

    config = Config.load_from_file(str(config_path), required_root_keys=("import",))

    assert config.import_year == 2027
    assert config.import_month == 11
    assert config.date_axis == AxisConfig(row=True, index=2, header=True)
    assert config.worker_axis == AxisConfig(row=False, index=3, header=False)
    assert config.shift_type_labels == {"night": "N"}


def test_config_require_section_raises_when_section_is_not_object():
    Config.reset()
    with pytest.raises(ValueError, match="Config 'import' key must contain an object"):
        Config.set_data({"import": "not-an-object"})
