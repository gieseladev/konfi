import abc
import dataclasses
import functools
from typing import Any, Dict, Iterable, Iterator, List, Mapping

import konfi

__all__ = ["SourceABC",
           "PathError", "MultiPathError",
           "FieldError",
           "QualifiedField", "iter_fields_recursively",
           "load_field_value", "load_fields_values"]


class SourceABC(abc.ABC):
    """Abstract base class of a source which can load the config."""

    @abc.abstractmethod
    def load_into(self, obj: Any, template: type) -> None:
        """Load the config into the given object according to the template.

        Raises:
            Exception: If the config couldn't be loaded.
        """
        ...


class PathError(Exception):
    """General exception in a template path.

    The path represents the config keys, which is not necessarily the same
    as the attributes.

    Attributes:
        path (List[str]): Path to the origin of the exception.
    """
    path: List[str]

    def __init__(self, path: Iterable[str], msg: str) -> None:
        super().__init__(msg)
        self.path = list(path)

    def __str__(self) -> str:
        path_str = self.path_str
        if path_str:
            path_str = f"{path_str}: "

        return f"{path_str}{super().__str__()}"

    @property
    def path_str(self) -> str:
        """Get the path as a string."""
        return ".".join(f"{path!r}" for path in self.path)

    def backtrace_path(self, part: str) -> None:
        """Add a part to the path."""
        self.path.insert(0, part)


class MultiPathError(PathError):
    """Exception grouping multiple `PathError` instances.

    Attributes:
        errors (List[PathError]): Grouped path errors.
    """
    errors: List[PathError]

    def __init__(self, path: Iterable[str], errors: Iterable[PathError], msg: str) -> None:
        super().__init__(path, msg)
        self.errors = list(errors)

    def __iter__(self) -> Iterable[PathError]:
        return iter(self.errors)

    def __str__(self) -> str:
        import textwrap
        errors_str = textwrap.indent("\n".join(map(str, self.errors)), "  ")
        return f"{super().__str__()}:\n{errors_str}"


class FieldError(PathError):
    """Exception for a particular field.

    Attributes:
        field (konfi.Field): Field which caused the exception.
    """
    field: konfi.Field

    def __init__(self, path: Iterable[str], field: konfi.Field, msg: str) -> None:
        super().__init__(path, msg)
        self.field = field


@dataclasses.dataclass()
class QualifiedField:
    """Qualified field information as returned by `iter_fields_recursively`."""
    parent: Any
    path: List[str]
    field: konfi.Field


def iter_fields_recursively(obj: Any, template: Any) -> Iterator[QualifiedField]:
    """Iterate over all fields of the template recursively.

     Yields:
          `QualifiedField` instances.
     """

    def iter_fields(parent: Any, path: List[str], fields: Iterable[konfi.Field]) -> None:
        for field in fields:
            key_path = [*path, field.key]

            if konfi.is_template_like(field.value_type):
                sub_obj = _get_sub_obj(obj, field)
                yield from iter_fields(sub_obj, key_path, konfi.fields(field.value_type))
            else:
                yield QualifiedField(parent, key_path, field)

    yield from iter_fields(obj, [], konfi.fields(template))


def load_field_value(obj: Any, field: konfi.Field, value: Any) -> None:
    """Load the given value for a field into the object.

    Raises:
        FieldError: If the value couldn't be converted to the given field
    """
    try:
        if field.converter is None:
            converted = konfi.convert_value(value, field.value_type)
        else:
            converted = konfi.converter._call_converter(field.converter, value, field.value_type)
    except konfi.ConversionError as e:
        raise FieldError([field.key], field, str(e)) from e

    setattr(obj, field.attribute, converted)


def _get_sub_obj(obj: Any, field: konfi.Field) -> Any:
    try:
        value = getattr(obj, field.attribute)
    except AttributeError:
        value = konfi.create_object_from_template(field.value_type)
        setattr(obj, field.attribute, value)

    return value


def load_fields_values(obj: Any, fields: Iterable[konfi.Field], mapping: Mapping, *,
                       ignore_unknown: bool = False) -> None:
    """Load the values for the fields from the mapping.

    This is done recursively.

    Args:
        obj: Object to load fields into
        fields: Fields to load
        mapping: Mapping to get field values from
        ignore_unknown: If `True`, excessive keys in the mapping are ignored.

    Raises:
        PathError: If there is an issue with a field.
            If multiple fields have an error, `MultiPathError` is raised.
    """
    _field_by_keys: Dict[str, konfi.Field] = {field.key: field for field in fields}

    field_errors: List[PathError] = []

    for key, value in mapping.items():
        try:
            field = _field_by_keys[key]
        except KeyError:
            if ignore_unknown:
                continue
            else:
                raise PathError([key], f"unexpected config key: {key!r}")

        if konfi.is_template_like(field.value_type) and isinstance(value, Mapping):
            sub_obj = _get_sub_obj(obj, field)
            loader = functools.partial(load_fields_values, sub_obj, konfi.fields(sub_obj), value)
        else:
            loader = functools.partial(load_field_value, obj, field, value)

        try:
            loader()
        except PathError as e:
            field_errors.append(e)
        except Exception as e:
            err = FieldError([key], field, str(e))
            err.__cause__ = e
            field_errors.append(err)

    if len(field_errors) == 1:
        raise field_errors[0]
    elif field_errors:
        raise MultiPathError((), field_errors, "")
