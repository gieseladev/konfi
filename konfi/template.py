import dataclasses
import functools
import inspect
from typing import Any, Dict, Optional, Tuple, get_type_hints

from .converter import has_converter
from .field import Field, MISSING, NoDefaultValue, UnboundField, upgrade_unbound

__all__ = ["template", "is_template", "is_template_like",
           "fields", "get_field"]

_FIELDS_ATTR = "__template_fields__"


def _make_fields(cls: type) -> Dict[str, Field]:
    cls_fields: Dict[str, Field] = {}

    # TODO handle MRO properly
    cls_annotations = get_type_hints(cls)
    for attr, typ in cls_annotations.items():
        if not (is_template_like(typ) or has_converter(typ)):
            # TODO raise
            raise Exception

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

        cls_fields[attr] = field

    return cls_fields


def _make_template(cls: type):
    _fields = _make_fields(cls)
    setattr(cls, _FIELDS_ATTR, _fields)


def template():
    def decorator(cls: type):
        if not inspect.isclass(cls):
            raise ValueError("decorator must be applied to a class")

        _make_template(cls)
        return cls

    return decorator


def is_template(obj: Any) -> bool:
    return hasattr(obj, _FIELDS_ATTR)


def is_template_like(obj: Any) -> bool:
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
    return tuple(_get_fields(obj).values())


def get_field(obj: Any, attr: str) -> Optional[Field]:
    return _get_fields(obj).get(attr)


def ensure_complete(obj: Any, templ: type) -> None:
    for f in fields(templ):
        try:
            val = getattr(obj, f.attribute)
        except AttributeError:
            try:
                default_val = f.get_default()
            except NoDefaultValue:
                # TODO raise something
                raise

            setattr(obj, f.attribute, default_val)
            continue

        if is_template_like(f.value_type):
            try:
                ensure_complete(val, f.value_type)
            except Exception:
                # TODO add details
                raise
