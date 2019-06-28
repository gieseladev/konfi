from typing import Any

import toml

import konfi
from konfi.converter import load_template_value
from .file import register_file_loader

__all__ = ["TOML"]


@register_file_loader(".toml")
class TOML(konfi.SourceABC):
    _path: str

    def __init__(self, path: str) -> None:
        self._path = path

    def load_into(self, obj: Any, template: type) -> None:
        try:
            data = toml.load(self._path)
        except Exception:
            # TODO add detailllllz
            raise
        load_template_value(obj, konfi.fields(template), data)
