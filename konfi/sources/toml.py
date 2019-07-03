from typing import Any

import konfi
from konfi.source import load_fields_values
from .file import register_file_loader

__all__ = ["TOML"]


@register_file_loader(".toml")
class TOML(konfi.SourceABC):
    _path: str
    _ignore_not_found: bool

    def __init__(self, path: str, *, ignore_not_found: bool = False, **_) -> None:
        self._path = path
        self._ignore_not_found = ignore_not_found

    def __str__(self) -> str:
        return f"TOML: {self._path!r}"

    def load_into(self, obj: Any, template: type) -> None:
        try:
            import toml
        except ImportError as e:
            raise ImportError("Couldn't import the 'toml' package. Make sure it's installed.") from e

        try:
            data = toml.load(self._path)
        except FileNotFoundError as e:
            if self._ignore_not_found:
                return
            else:
                raise e

        load_fields_values(obj, konfi.fields(template), data)
