from typing import Any, Type

import yaml

import konfi
from konfi.converter import load_template_value
from .file import register_file_loader

__all__ = ["YAML"]


@register_file_loader(".yml", ".yaml", ".json")
class YAML(konfi.SourceABC):
    _path: str

    def __init__(self, path: str) -> None:
        self._path = path

    def load_into(self, obj: Any, template: Type) -> None:
        with open(self._path, "r") as f:
            data = yaml.safe_load(f)

        # TODO exceptions

        load_template_value(obj, konfi.fields(template), data)
