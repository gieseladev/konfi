from typing import Any

import toml

import konfi
from konfi.source import load_fields_values
from .file import register_file_loader

__all__ = ["TOML"]


@register_file_loader(".toml")
class TOML(konfi.SourceABC):
    _path: str

    def __init__(self, path: str, **_) -> None:
        self._path = path

    def load_into(self, obj: Any, template: type) -> None:
        try:
            data = toml.load(self._path)
        except Exception:
            # TODO add detailllllz
            raise

        load_fields_values(obj, konfi.fields(template), data)
