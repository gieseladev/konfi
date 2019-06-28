import ast
import os
import re
from typing import Any, Callable, Iterable, List, Mapping, Pattern, Type, Union

import yaml

import konfi
from konfi import converter

__all__ = ["Env",
           "Decoder", "ResolvableDecoder", "resolve_decoder",
           "NameBuilder", "build_env_name"]

unportable_chars_pattern: Pattern = re.compile(r"^\d|[^a-z0-9]", re.IGNORECASE)

Decoder = Callable[[str], Any]
Decoder.__doc__ = \
    """Callable which decodes the value of an environment variable."""

decoders: Mapping[str, Decoder] = {
    "raw": str,
    "python": ast.literal_eval,
    "yaml": yaml.safe_load,
}

ResolvableDecoder = Union[str, Decoder]


def resolve_decoder(decoder: ResolvableDecoder) -> Decoder:
    """Resolve the given decoder name or check if it's a decoder function.

    Args:
        decoder: Decoder to resolve

    Raises:
        KeyError: Decoder name was given, but doesn't exist
        TypeError: Invalid type was given

    Returns:
        Decoder
    """
    if isinstance(decoder, str):
        try:
            return decoders[decoder.lower()]
        except KeyError:
            raise KeyError(f"No existing decoder {decoder!r}")

    if callable(decoder):
        return decoder
    else:
        raise TypeError(f"Decoder must be a function or the name of a built-in decoder")


NameBuilder = Callable[[List[str]], str]
NameBuilder.__doc__ = \
    """A callable which converts a path to the name of the corresponding 
    environment variable."""


def build_env_name(path: Iterable[str]) -> str:
    """Create the name of an environment variable for the given path."""
    return "_".join(unportable_chars_pattern.sub("", part) for part in path)


class Env(konfi.SourceABC):
    _prefix: str
    _decoder: Decoder
    _name_builder: NameBuilder

    def __init__(self, prefix: str = "", *,
                 decoder: ResolvableDecoder = "python",
                 name_builder: NameBuilder = build_env_name,
                 ):
        self._prefix = prefix
        self._decoder = resolve_decoder(decoder)
        self._name_builder = name_builder

    def get_env_name(self, path: List[str]) -> str:
        """Combine prefix and name builder result."""
        return f"{self._prefix}{self._name_builder(path)}"

    def load_path(self, path: List[str], parent: Any, field: konfi.Field) -> None:
        key = self.get_env_name(path)
        try:
            raw_value = os.environ[key]
        except KeyError:
            return

        try:
            value = self._decoder(raw_value)
        except Exception:
            # TODO le raise
            raise

        converter.set_value(parent, field, value)

    def load_into(self, obj: Any, template: Type) -> None:
        pass
