import abc
from typing import Any, Type

__all__ = ["SourceABC"]


class SourceABC(abc.ABC):
    @abc.abstractmethod
    def load_into(self, obj: Any, template: Type) -> None:
        ...
