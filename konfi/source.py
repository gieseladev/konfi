import abc
from typing import Any

__all__ = ["SourceABC"]


class SourceABC(abc.ABC):
    @abc.abstractmethod
    def load_into(self, obj: Any, template: type) -> None:
        ...
