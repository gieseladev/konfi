"""Built-in converters."""

import enum
import inspect
from typing import Any, Iterable, List, TypeVar, cast

from . import typeinspect
from .converter import ComplexConverterABC, ConversionError, convert_value, register_converter

T = TypeVar("T")

# add built-in primitive values
for const_converter in {
    bool,
    int, float, complex,
    str, bytes,
}:
    register_converter(const_converter)(const_converter)


# <-- simple converters ------------------------------------------------------->

@register_converter(None, type(None))
def none_converter(_: Any) -> None:
    """Converts all values to `None`."""
    return None


@register_converter(Any)
def any_convert(val: Any) -> Any:
    """Returns value as is."""
    return val


@register_converter(Iterable)
def iterable_converter(value: Any) -> Iterable:
    """Converts the value to an iterable.

    Non-iterable values are wrapped in a tuple.

    Even though strings are iterable, this converter does not treat them as such
    to be consistent with the user's expectations.
    """
    if isinstance(value, Iterable) and not isinstance(value, (str,)):
        return value
    else:
        # yes it looks weird, but this is a tuple
        return value,


@register_converter(List, list)
def list_converter(value: Any) -> List:
    """Converts a value to a list by first converting it to an iterable."""
    return list(convert_value(value, Iterable))


# <-- complex converters ------------------------------------------------------>

@register_converter()
class IterableConverter(ComplexConverterABC):
    def can_convert(self, target: type) -> bool:
        pass

    def convert(self, value: Any, target: type) -> Iterable[T]:
        # TODO find iter type
        iter_type = None

        final_list = []

        it = convert_value(value, Iterable)
        for i, sub_value in enumerate(it):
            v = convert_value(sub_value, iter_type)
            final_list.append(v)

        return final_list


@register_converter()
class TupleConverter(ComplexConverterABC):
    """Converter for typed tuples."""

    def can_convert(self, target: type) -> bool:
        return typeinspect.is_tuple(target)

    def convert(self, value: Any, target: type) -> tuple:
        values = convert_value(value, list)

        types, n = typeinspect.resolve_tuple(target)
        if n is None:
            typ = types[0]
            return tuple(convert_value(val, typ) for val in values)
        elif n != len(values):
            raise ConversionError(f"Can't convert {values!r} to {n}-tuple, lengths don't match")
        else:
            return tuple(convert_value(val, typ) for val, typ in zip(values, types))


@register_converter()
class EnumConverter(ComplexConverterABC):
    """Converter for converting values to `enum.Enum`.

    The converter prefers a perfect name match, if that fails it tries
    to use a perfect value match.
    If that also fails and the value is a string, the first case-insensitive
    match on either the name or the value of a filed is returned.
    """

    def can_convert(self, target: type) -> bool:
        return inspect.isclass(target) and issubclass(target, enum.Enum)

    def convert(self, value: Any, target: enum.EnumMeta) -> enum.Enum:
        try:
            return target[value]
        except KeyError:
            pass

        try:
            return target(value)
        except (ValueError, TypeError):
            pass

        if isinstance(value, str):
            value_lower = value.lower()
            for enum_field in target:
                enum_field = cast(enum.Enum, enum_field)

                if value_lower == enum_field.name.lower():
                    return enum_field

                field_val = enum_field.value
                if isinstance(field_val, str) and field_val.lower() == value_lower:
                    return enum_field

        raise ConversionError(f"{value!r} isn't in enum {target.__qualname__!r}")
