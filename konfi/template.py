import inspect
from typing import Any, Dict, Optional, Tuple

from .converter import has_converter
from .field import Field, UnboundField, upgrade_unbound

__all__ = ["template", "is_template",
           "fields", "get_field"]

_FIELDS_ATTR = "__template_fields__"


def _make_fields(cls: type) -> Dict[str, Field]:
    cls_fields: Dict[str, Field] = {}

    cls_annotations = cls.__dict__.get("__annotations__", {})
    for attr, typ in cls_annotations.items():
        if not has_converter(typ):
            # TODO raise
            raise Exception

        try:
            value = getattr(cls, attr)
        except AttributeError:
            cls_fields[attr] = Field(attribute=attr, value_type=typ)
            continue

        if isinstance(value, UnboundField):
            field = upgrade_unbound(value, attribute=attr, value_type=typ)
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


def _get_fields(obj: Any) -> Dict[str, Field]:
    try:
        return getattr(obj, _FIELDS_ATTR)
    except AttributeError:
        raise TypeError("must be called with a template")


def fields(obj: Any) -> Tuple[Field, ...]:
    return tuple(_get_fields(obj).values())


def get_field(obj: Any, attr: str) -> Optional[Field]:
    return _get_fields(obj).get(attr)
