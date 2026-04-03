from pathlib import Path

import yaml


# Custom exception for missing error messages
class ErrorMessageNotFound(KeyError):
    def __init__(self, key):
        super().__init__(f"Error message not found for key: '{key}'")


class ErrorHandler:
    _messages: dict[str, str] = {}
    _error_file = Path(__file__).parent / "errors-en.yaml"

    @classmethod
    def load_messages(cls):
        if not cls._messages:
            path = Path(cls._error_file)
            if path.suffix.lower() not in {".yaml", ".yml"}:
                raise ValueError(f"Config file must be a .yaml or .yml file: {path}")
            try:
                with path.open("r", encoding="utf-8") as config_file:
                    config_data = yaml.safe_load(config_file)
            except yaml.YAMLError as exc:
                raise ValueError(f"Invalid YAML in config file {path}: {exc}") from exc
            if not isinstance(config_data, dict):
                raise ValueError("Config YAML must contain an object at the root")
            cls._messages = config_data

    @classmethod
    def get_message(cls, key: str, default=None, **kwargs) -> str:
        if not cls._messages:
            cls.load_messages()
        keys = key.split(".")
        dicts = cls._messages
        for k in keys:
            if not isinstance(dicts, dict):
                dicts = default
                break
            dicts = dicts.get(k, default)
        if dicts is None:
            raise ErrorMessageNotFound(key)
        message = str(dicts)
        if kwargs:
            message = message.format(**kwargs)
        return message