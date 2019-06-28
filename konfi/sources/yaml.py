import yaml

import konfi

__all__ = ["YAML"]


class YAML(konfi.SourceABC):
    _path: str

    def __init__(self, path: str) -> None:
        self._path = path

    def load_into(self) -> None:
        with open(self._path, "r") as f:
            yaml.safe_load(f)
