import toml

import konfi

__all__ = ["TOML"]


class TOML(konfi.SourceABC):
    _path: str

    def __init__(self, path: str) -> None:
        self._path = path

    def load_into(self) -> None:
        data = toml.load(self._path)
