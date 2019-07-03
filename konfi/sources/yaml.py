from typing import Any, Type

import konfi
from konfi.source import load_fields_values
from .file import register_file_loader

__all__ = ["YAML"]


@register_file_loader(".yml", ".yaml", ".json")
class YAML(konfi.SourceABC):
    """Source which loads the config from YAML files.

    Args:
        path: File path to load file from.

        ignore_not_found: When this is set to true and the config file
            couldn't be found at the given path, no error is raised and
            nothing is loaded.
    """
    _path: str
    _ignore_not_found: bool

    def __init__(self, path: str, *, ignore_not_found: bool = False, **_) -> None:
        self._path = path
        self._ignore_not_found = ignore_not_found

    def __str__(self) -> str:
        return f"YAML: {self._path!r}"

    def load_into(self, obj: Any, template: Type) -> None:
        try:
            import yaml
        except ImportError as e:
            raise ImportError("Couldn't import 'pyyaml' package. Make sure it's installed.") from e

        try:
            with open(self._path, "r") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError as e:
            if self._ignore_not_found:
                return
            else:
                raise e

        load_fields_values(obj, konfi.fields(template), data)
