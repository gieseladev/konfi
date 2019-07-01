import pathlib
from typing import Any, Callable, Dict, Optional

import konfi

__all__ = ["FileLoaderType",
           "register_file_loader", "has_file_loader",
           "FileLoader"]

FileLoaderType = Callable[[str], konfi.SourceABC]
FileLoaderType.__doc__ = \
    """Constructor of a konfi file source.
    
    In addition to the path, the functions must also accept various keyword 
    arguments. Specifically, it should not raise an exception if unknown keyword
    arguments are given!
    """

_FILE_LOADERS: Dict[str, FileLoaderType] = {}


def register_file_loader(*file_types: str, replace: bool = False):
    """Decorator to register a file loader.

    The decorated object must be a `FileLoaderType`.

    Args:
        *file_types: File extensions (including the dot) to assign to
            the decorated source.
        replace: Whether to replace existing file loaders if an extension
            is already registered.

    Raises:
        TypeError: If the decorated value isn't a file loader constructor
        ValueError: If one of the file types is already registered and
            `replace` isn't `True`.
    """

    def decorator(loader: FileLoaderType):
        if not callable(loader):
            raise TypeError("decorated value must be a file loader constructor")

        for file_type in file_types:
            file_type = file_type.lower()
            if file_type in _FILE_LOADERS and not replace:
                raise ValueError(f"file loader for file type {file_type!r} already exists.")

            _FILE_LOADERS[file_type] = loader

        return loader

    return decorator


def has_file_loader(ext: str) -> bool:
    """Check whether the given extension has a file loader associated.

    Args:
        ext: File extension including the leading dot.
    """
    return ext in _FILE_LOADERS


class FileLoader(konfi.SourceABC):
    """A higher order source which uses other sources under the hood.

    The source uses the file extension of the given path to determine which
    source to use. This is done by providing the `register_file_loader`
    decorator which can be used to register a `FileLoaderType` (which can be a
    `konfi.SourceABC`) for the given extensions.

    Supported extensions by the built-in sources:

    - YAML: .yml, .yaml, .json
    - TOML: .toml

    The file loader is determined as soon as the constructor is called, so if
    there is no file loader for the given extension a `ValueError` is raised
    unless `ignore_no_loader` is set to `True`.

    Args:
        path: Path of config file to load.
        ignore_no_loader: If set to `True` and no loader could be found for
            the given path, the source turns into a dummy source and doesn't
            load anything.
        ignore_not_found: If set to `True` and the wrapped source raises
            a `FileNotFoundError`, it is ignored.
        **kwargs: Keyword arguments to pass to the file loader constructor.

    Raises:
        ValueError: If no file loader was found for the given path and
            `ignore_no_loader` is `False`.
    """
    _loader: Optional[konfi.SourceABC]

    _ignore_not_found: bool
    _kwargs: Dict[str, Any]

    def __init__(self, path: str, *,
                 ignore_no_loader: bool = False,
                 ignore_not_found: bool = False,
                 **kwargs: Any) -> None:
        suffix = pathlib.Path(path).suffix.lower()
        try:
            loader_cls = _FILE_LOADERS[suffix]
        except KeyError:
            if ignore_no_loader:
                loader = None
            else:
                raise ValueError(f"No loader for file type {suffix}")
        else:
            loader = loader_cls(path, **kwargs)

        self._loader = loader

        self._ignore_not_found = ignore_not_found

    def __str__(self) -> str:
        loader = self._loader or "no loader"
        return f"FileLoader ({loader})"

    def load_into(self, obj: Any, template: type) -> None:
        if self._loader is None:
            return

        try:
            self._loader.load_into(obj, template)
        except FileNotFoundError as e:
            if self._ignore_not_found:
                return
            else:
                raise e
