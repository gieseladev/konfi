import inspect
from typing import List, Type, TypeVar, Union

from .source import SourceABC
from .template import ensure_complete, is_template_like

__all__ = ["Loader"]

TT = TypeVar("TT")


class Loader:
    """Loads the config from sources."""
    _sources: List[SourceABC]

    def __init__(self) -> None:
        self._sources = []

    def set_sources(self, *sources: SourceABC) -> None:
        """Set the sources to use when loading."""
        self._sources = list(sources)

    def load(self, template: Union[Type[TT], TT]) -> TT:
        """Load the config for the given template.

        Raises:
            ValueError: If no sources are set.
            TypeError: If the given template isn't template-like.
        """

        if not self._sources:
            raise ValueError("No sources are set")

        if not is_template_like(template):
            raise TypeError(f"Template must be template-like, not {template!r}")

        if inspect.isclass(template):
            obj = object.__new__(template)
        else:
            obj = template
            template = type(template)

        for source in self._sources:
            try:
                source.load_into(obj, template)
            except Exception:
                # TODO add more details to exception
                raise

        ensure_complete(obj, template)

        # TODO add hooks to the entire process

        return obj
