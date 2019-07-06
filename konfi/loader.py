import inspect
from typing import List, Type, TypeVar, Union

from .source import SourceABC
from .templ import create_object_from_template, ensure_complete, is_template_like

__all__ = ["SourceError", "Loader"]

TT = TypeVar("TT")


class SourceError(Exception):
    """Exception raised when a source fails to load the config.

    Attributes:
        source (SourceABC): Source that tried to load the config.
        template (type): Template that was to be loaded.
        error (Exception): Original error that was raised.
            This is provided for convenience.
    """
    source: SourceABC
    template: type

    error: Exception

    def __init__(self, source: SourceABC, template: type, error: Exception) -> None:
        self.source = source
        self.template = template
        self.error = error

    def __str__(self) -> str:
        return f"couldn't load {self.template.__qualname__!r} from {self.source}"


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

        Args:
            template: Template to load from the sources.
                If this is already an instance of the template, then
                the config is loaded into the instance.

        Raises:
            ValueError: If no sources are set.
            TypeError: If the given template isn't template-like.
            SourceError: If one of the sources fails to load the config.
        """

        if not self._sources:
            raise ValueError("No sources are set")

        if not is_template_like(template):
            raise TypeError(f"Template must be template-like, not {template!r}")

        if inspect.isclass(template):
            obj = create_object_from_template(template)
        else:
            obj = template
            template = type(template)

        for source in self._sources:
            try:
                source.load_into(obj, template)
            except Exception as e:
                raise SourceError(source, template, e) from e

        ensure_complete(obj, template)

        # TODO add hooks to the entire process

        return obj
