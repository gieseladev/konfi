import pathlib
from typing import Any, Callable, Dict

import konfi

__all__ = ["FileLoaderType", "register_file_loader", "FileLoader"]

FileLoaderType = Callable[[str], konfi.SourceABC]
FileLoaderType.__doc__ = \
    """Constructor of a konfi file source."""

_FILE_LOADERS: Dict[str, FileLoaderType] = {}


def register_file_loader(*file_types: str, replace: bool = False):
    """Decorator to register a file loader.

    The decorated object must be a `FileLoaderType`.

    Args:
        *file_types: File extensions (including the dot) to assign to
            the decorated source.
        replace: Whether to replace existing file loaders if an extension
            is already registered.
    """

    def decorator(loader: FileLoaderType):
        if not callable(loader):
            raise TypeError("decorated value must be a file loader constructor")

        for file_type in file_types:
            file_type = file_type.lower()
            if file_type in _FILE_LOADERS and not replace:
                raise ValueError(f"file loader for file type {file_type!r} already exists.")

            _FILE_LOADERS[file_type] = loader

    return decorator


class FileLoader(konfi.SourceABC):
    _loader: konfi.SourceABC

    def __init__(self, path: str) -> None:
        suffix = pathlib.Path(path).suffix.lower()
        try:
            loader = _FILE_LOADERS[suffix]
        except KeyError:
            raise ValueError(f"No loader for file type {suffix}")

        self._loader = loader(path)

    def load_into(self, obj: Any, template: type) -> None:
        self._loader.load_into(obj, template)
