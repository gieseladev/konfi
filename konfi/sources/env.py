import ast
import os
import re
from typing import Any, Callable, Dict, Iterable, List, Pattern, Type, Union

import konfi
from konfi import source

__all__ = ["Env",
           "Decoder", "ResolvableDecoder", "resolve_decoder",
           "NameBuilder", "build_env_name"]

unportable_chars_pattern: Pattern = re.compile(r"^\s*\d+|[^a-z0-9]+", re.IGNORECASE)

Decoder = Callable[[str], Any]
Decoder.__doc__ = \
    """Callable which decodes the value of an environment variable."""

_DECODERS: Dict[str, Union[Decoder, Exception]] = {
    "raw": str,
    "python": ast.literal_eval,
}

try:
    import yaml
except ImportError as e:
    exc = ImportError("yaml decoder unavailable because pyyaml package is missing.")
    exc.__cause__ = e
    _DECODERS["yaml"] = e
else:
    _DECODERS["yaml"] = yaml.safe_load

ResolvableDecoder = Union[str, Decoder]
ResolvableDecoder.__doc__ = \
    """Either the name of a built-in decoder or a `Decoder` function."""


def resolve_decoder(decoder: ResolvableDecoder) -> Decoder:
    """Resolve the given decoder name or check if it's a decoder function.

    Args:
        decoder: Decoder to resolve

    Raises:
        KeyError: Decoder name was given, but doesn't exist
        TypeError: Invalid type was given
        Exception: If the decoder whose name was given is unavailable.
            For example if the `pyyaml` package isn't installed, an
            `ImportError` will be raised when trying to resolve the
            "yaml" decoder.
    """
    if isinstance(decoder, str):
        try:
            dec = _DECODERS[decoder.lower()]
        except KeyError:
            raise KeyError(f"No existing decoder {decoder!r}")
        else:
            if isinstance(dec, Exception):
                raise dec from None
            else:
                return dec

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
    return "_".join(unportable_chars_pattern.sub("", part) for part in path).upper()


class Env(konfi.SourceABC):
    """Source which loads the config from environment variables.

    The env source is different from most sources because it walks through the
    config template and looks for the corresponding environment variable instead
    of the other way around. This means that with the exception of template-like
    objects it's not possible to set sub values directly. For example, you can't
    update a specific key of a dictionary using an environment variable using a
    specific environment variable, only the entire value (i.e. dictionary) can
    be set.


    Args:
          prefix: Prefix to prepend to all variable names.
            This can be used to prevent name collisions and ensure
            that the variables were set with the right intent.

          decoder: Decoder used to interpret the values of the environment
              variables. There are three built-in decoders:

              - raw: Values are interpreted as strings.

              - python: Values are (safely) interpreted as if they were Python
                literals.

              - yaml: Values are interpreted as YAML. This is by far the most
                powerful and convenient decoder. For example, it doesn't require
                the use of quotation marks to escape strings.


              You can also pass your own decoder with the type `Decoder` which
              is just a function that takes a string and returns the decoded
              version.

              The default is the python decoder.

          name_builder: Function that combines the path segments of a field to
            the name of the corresponding environment variable
            (ex: ["database", "main", "url"] -> "DATABASE_MAIN_URL").

            The default is the `build_env_name` function which removes
            non-alphanumeric characters and underscores from the path segments
            as well as stripping leading numbers. The segments are then joined
            using underscores. For example ["a_b@", "1c_d"] would be turned
            into "AB_CD".
    """
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

    def __str__(self) -> str:
        return f"Environment ({self._prefix!r})"

    def get_env_name(self, path: List[str]) -> str:
        """Combine prefix and name builder result."""
        return f"{self._prefix}{self._name_builder(path)}"

    def _load_path(self, path: List[str], parent: Any, field: konfi.Field) -> None:
        key = self.get_env_name(path)
        try:
            raw_value = os.environ[key]
        except KeyError:
            return

        try:
            value = self._decoder(raw_value)
        except Exception as e:
            raise konfi.PathError(path, f"can't decode {raw_value!r}") from e

        source.load_field_value(parent, field, value)

    def load_into(self, obj: Any, template: Type) -> None:
        for qfield in source.iter_fields_recursively(obj, template):
            self._load_path(qfield.path, qfield.parent, qfield.field)
