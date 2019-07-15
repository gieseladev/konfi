import dataclasses
import functools
import inspect
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, get_type_hints, overload

from . import typeinspect
from .converter import has_converter
from .field import Field, MISSING, NoDefaultValue, UnboundField, upgrade_unbound
from .source import FieldError, MultiPathError, PathError

__all__ = ["template", "is_template", "is_template_like",
           "fields", "get_field",
           "create_object_from_template",
           "ensure_complete"]

_FIELDS_ATTR = "__template_fields__"


def _make_fields(cls: type, *, template_bases_only: bool = True) -> Dict[str, Field]:
    cls_fields: Dict[str, Field] = {}

    if template_bases_only:
        for base in cls.__mro__[:0:-1]:
            try:
                _fields = getattr(base, _FIELDS_ATTR)
            except AttributeError:
                continue

            for attr, _field in _fields.items():
                cls_fields[attr] = _field

        cls_annotations = typeinspect.get_class_type_hints_strict(cls)
    else:
        cls_annotations = get_type_hints(cls)

    for attr, typ in cls_annotations.items():
        try:
            value = getattr(cls, attr)
        except AttributeError:
            cls_fields[attr] = Field(attribute=attr, value_type=typ)
            continue

        if isinstance(value, UnboundField):
            field = upgrade_unbound(value, attribute=attr, value_type=typ)

            # replace field with the default if possible, otherwise remove
            if value.default_value is MISSING:
                delattr(cls, attr)
            else:
                setattr(cls, attr, value.default_value)

        else:
            field = Field(attribute=attr, value_type=typ, default_value=value)

        if not (field.converter is not None
                or is_template_like(typ)
                or has_converter(typ)):
            raise TypeError(f"Field {attr!r} doesn't have a converter.")

        cls_fields[attr] = field

    return cls_fields


def _make_template(cls: type, *, template_bases_only: bool = True):
    _fields = _make_fields(cls, template_bases_only=template_bases_only)
    setattr(cls, _FIELDS_ATTR, _fields)


def template(*, template_bases_only: bool = True):
    """Decorator to convert the given class to a template.

    This parses the decorated class into a template which can be used to
    load the config.
    The fields are loaded from the annotations from the class. If an attribute
    has a value it is used as the default value, unless it's an unbound field
    (see `konfi.field`) which is used directly and the class variable is
    replaced.

    Args:
        template_bases_only: If set to `True` (default) only fields from
            bases which are themselves templates are added to the template.
            If `False`, all annotations from all bases are considered as being
            part of the class itself.

    Raises:
        ValueError: If the decorated object isn't a class.
        TypeError: If one of the fields has an invalid type.
    """

    def decorator(cls: type):
        if not inspect.isclass(cls):
            raise ValueError("decorator must be applied to a class")

        _make_template(cls, template_bases_only=template_bases_only)
        return cls

    return decorator


def is_template(obj: Any) -> bool:
    """Check whether the given object is a template instance or class."""
    return hasattr(obj, _FIELDS_ATTR)


def is_template_like(obj: Any) -> bool:
    """Check whether the given object is template-like.

    Currently this includes templates and dataclasses.
    """
    return is_template(obj) or dataclasses.is_dataclass(obj)


def _field_from_dataclass_field(f: dataclasses.Field) -> Field:
    default_value = f.default
    if default_value is dataclasses.MISSING:
        default_value = MISSING

    default_factory = f.default_factory
    if default_factory is dataclasses.MISSING:
        default_factory = None

    return Field(attribute=f.name, key=f.name,
                 value_type=f.type,
                 default_value=default_value, default_factory=default_factory)


@functools.lru_cache(64)
def _fields_from_dataclass(obj: Any) -> Dict[str, Field]:
    data_fields: Tuple[dataclasses.Field, ...] = dataclasses.fields(obj)
    return {f.name: _field_from_dataclass_field(f) for f in data_fields}


def _get_fields(obj: Any) -> Dict[str, Field]:
    try:
        return getattr(obj, _FIELDS_ATTR)
    except AttributeError:
        if dataclasses.is_dataclass(obj):
            return _fields_from_dataclass(obj)

        raise TypeError("must be called with a template")


def fields(obj: Any) -> Tuple[Field, ...]:
    """Get the fields of a template-like instance or class.

    Raises:
        TypeError: If the given object isn't template-like.

    Returns:
        A tuple containing all fields of the template.
    """
    return tuple(_get_fields(obj).values())


def get_field(obj: Any, attr: str) -> Optional[Field]:
    """Get the field for an attribute from a template-like  instance or class.

    Raises:
        TypeError: If the given object isn't template-like.

    Returns:
        The field for the attribute or `None` if no such field exists.
    """
    return _get_fields(obj).get(attr)


T = TypeVar("T")


@overload
def create_object_from_template(templ: type) -> Any: ...


@overload
def create_object_from_template(templ: Type[T]) -> T: ...


def create_object_from_template(templ: Type[T]) -> T:
    """Create an empty object for the given template.

    Args:
        templ: Template-like object to create an instance for.

    Returns:
        New object which is an instance of the template.
    """
    return object.__new__(templ)


def ensure_complete(obj: Any, templ: type) -> None:
    """Check whether the given object contains all fields of the template.

    Sub-templates are checked recursively. If a field doesn't have a value but
    the field has a default value, the default value is assigned.
    No type checking is performed.

    Raises:
        TypeError: If the given template isn't template-like.
        PathError: If there's an error with one of the fields.
            `FieldError` is raised when a value is missing.
            If there are multiple errors, a `MultiPathError` exception
            is raised.
    """
    path_errors: List[PathError] = []

    for f in fields(templ):
        try:
            val = getattr(obj, f.attribute)
        except AttributeError:
            try:
                default_val = f.get_default()
            except NoDefaultValue:
                e = FieldError([f.key], f, "required value missing")
                path_errors.append(e)
            else:
                setattr(obj, f.attribute, default_val)

            continue

        if is_template_like(f.value_type):
            try:
                ensure_complete(val, f.value_type)
            except PathError as e:
                e.backtrace_path(f.key)
                path_errors.append(e)

    if len(path_errors) == 1:
        raise path_errors[0]
    elif path_errors:
        raise MultiPathError([], path_errors, f"{templ.__qualname__!r} is incomplete")
