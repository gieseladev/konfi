"""Built-in converters."""

import enum
import functools
import inspect
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Set, Tuple, TypeVar, cast

from . import typeinspect
from .converter import ComplexConverterABC, ConversionError, convert_value, register_converter

T = TypeVar("T")

# <-- converter groups -------------------------------------------------------->

# primitive types
for conv in (
        bool,
        int, float, complex,
        str, bytes,
):
    register_converter(conv)(conv)

del conv


def _make_converter(cls: Callable):
    @functools.wraps(cls)
    def converter(val: Any):
        val = convert_value(val, Iterable)
        if not isinstance(val, cls):
            val = cls(val)

        return val

    return converter


# iterable types
for convs in (
        (Tuple, tuple),
        (List, list),
        (Set, set),

        (Mapping, MutableMapping, Dict, dict),
):
    cls = cast(Callable, convs[-1])
    register_converter(*convs)(_make_converter(cls))

del convs


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


# <-- complex converters ------------------------------------------------------>

@register_converter()
class UnionConverter(ComplexConverterABC):
    """Converter for union types.

    First checks if value is already in the union and if it's not it then
    tries to convert to the values from first to last.
    """

    def can_convert(self, target: type) -> bool:
        return typeinspect.is_union(target)

    def convert(self, value: Any, target: type) -> Any:
        if typeinspect.has_type(value, target):
            return value

        types = typeinspect.get_type_args(target)
        last_exception: Optional[Exception] = None

        for typ in types:
            try:
                return convert_value(value, typ)
            except ConversionError as e:
                if last_exception is not None:
                    last_exception.__cause__ = e

                last_exception = e

        raise last_exception


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


# TODO Template-like converter

# TODO make sure we don't end up recursing on the same converter

@register_converter()
class IterableConverter(ComplexConverterABC):
    def can_convert(self, target: type) -> bool:
        return typeinspect.is_generic_iterable(target) \
               and not typeinspect.is_tuple(target) \
               and not typeinspect.is_generic_mapping(target)

    def convert(self, value: Any, target: type) -> Iterable[T]:
        container_type = typeinspect.get_origin(target)
        item_type = typeinspect.get_type_args(target)[0]

        final_list = []

        it = convert_value(value, Iterable)
        for i, sub_value in enumerate(it):
            try:
                v = convert_value(sub_value, item_type)
            except ConversionError as e:
                # TODO typeinspect.friendly_name
                raise ConversionError(f"couldn't convert value at index {i} ({sub_value!r}) to {item_type}") from e

            final_list.append(v)

        if container_type is not None:
            final_list = convert_value(final_list, container_type)

        return final_list


@register_converter()
class MappingConverter(ComplexConverterABC):
    def can_convert(self, target: type) -> bool:
        return typeinspect.is_generic_mapping(target)

    def convert(self, value: Any, target: type) -> Iterable[T]:
        container_type = typeinspect.get_origin(target)
        key_type, value_type = typeinspect.get_type_args(target)

        final_map = {}

        mapping = convert_value(value, Mapping)
        for key, value in mapping.items():
            try:
                k = convert_value(key, key_type)
            except ConversionError as e:
                # TODO typeinspect.friendly_name
                raise ConversionError(f"couldn't convert key {key!r} to {key_type}") from e

            try:
                v = convert_value(value, value_type)
            except ConversionError as e:
                # TODO typeinspect.friendly_name
                raise ConversionError(f"couldn't convert value of {key!r} ({value!r}) to {value_type}") from e

            final_map[k] = v

        if container_type is not None:
            final_map = convert_value(final_map, container_type)

        return final_map


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
