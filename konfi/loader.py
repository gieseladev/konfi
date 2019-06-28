import inspect
from typing import List, Type, TypeVar, Union

from .source import SourceABC
from .template import is_template

__all__ = ["Loader"]

TT = TypeVar("TT")


class Loader:
    _sources: List[SourceABC]

    def __init__(self) -> None:
        self._sources = []

    def set_sources(self, *sources: SourceABC) -> None:
        self._sources = list(sources)

    def load(self, template: Union[Type[TT], TT]) -> TT:
        if not self._sources:
            # TODO raise something?
            raise

        if not is_template(template):
            # TODO raise something else
            raise

        if inspect.isclass(template):
            obj = object.__new__(template)
        else:
            obj = template
            template = type(template)

        for source in self._sources:
            # TODO add more details to exception
            source.load_into(obj, template)

        # TODO call post load hook or something

        return obj
