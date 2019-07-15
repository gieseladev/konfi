"""Built-in converters."""

import collections.abc as collections
import enum
import functools
import inspect
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, TypeVar, cast

from . import source, templ, typeinspect
from .converter import ComplexConverterABC, ConversionError, convert_value, has_converter, register_converter

T = TypeVar("T")


# <-- converter groups -------------------------------------------------------->

# primitive types which can be called with multiple input types to get the
# desired type.

def _register_primitive_converters(converters: Iterable[type]) -> None:
    for conv in converters:
        register_converter(conv)(conv)


_register_primitive_converters((
    bool,
    int, float, complex,
    str, bytes,
))

del _register_primitive_converters


# types which are first converted to a general type (read: interface)
# and then converted to the real type.

def _register_container_converters(converters: Iterable[Tuple[Tuple[type, ...], type]]) -> None:
    def _make_converter(cls: Callable, base_type: type):
        @functools.wraps(cls)
        def converter(val: Any):
            val = convert_value(val, base_type)
            if not isinstance(val, cls):
                val = cls(val)

            return val

        return converter

    for convs, base in converters:
        register_converter(*convs)(_make_converter(
            cast(Callable, convs[-1]),
            base,
        ))


_register_container_converters((
    ((Tuple, tuple), Iterable),
    ((List, list), Iterable),
    ((Set, set), Iterable),

    ((Dict, dict), Mapping),
))

del _register_container_converters


# <-- simple converters ------------------------------------------------------->

@register_converter(None, type(None))
def none_converter(_: Any) -> None:
    """Converts all values to `None`."""
    return None


@register_converter(Any)
def any_convert(val: Any) -> Any:
    """Returns value as is."""
    return val


@register_converter(Iterable, collections.Iterable)
def iterable_converter(value: Any) -> Iterable:
    """Converts the value to an iterable.

    Non-iterable values are wrapped in a tuple.

    Even though strings are iterable, this converter does not treat them as such
    to be consistent with the user's expectations.

    The same is true for mappings which is converted to an iterable of key,
    value tuples instead of just the keys.
    """
    if isinstance(value, Mapping):
        return value.items()

    if isinstance(value, Iterable) and not isinstance(value, (str,)):
        return value
    else:
        # yes it looks weird, but this is a tuple
        return value,


@register_converter(Mapping, collections.Mapping)
def mapping_converter(value: Any) -> Mapping:
    """Converts the value to a mapping,

    Sequences are interpreted as a mapping from index to value.
    All other value types raise a `ConversionError`.
    """
    if isinstance(value, Mapping):
        return value
    elif isinstance(value, Sequence):
        return dict(enumerate(value))
    else:
        raise ConversionError(f"can't convert {value!r} to a Mapping")


# <-- complex converters ------------------------------------------------------>

@register_converter()
class UnionConverter(ComplexConverterABC):
    """Converter for union types.

    First checks if value is already in the union and if it's not it then
    tries to convert to the values from first to last.
    """

    def can_convert(self, target: type) -> bool:
        return typeinspect.is_union(target) and all(map(has_converter, typeinspect.get_type_args(target)))

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
    """Converter for typed tuples.

    The input value is first converted to a collection, if the tuple
    type has a fixed length the input must match that, otherwise any
    length is accepted.
    """

    def can_convert(self, target: type) -> bool:
        is_tuple = typeinspect.is_tuple(target) \
                   and not typeinspect.has_free_parameters(target)

        if not is_tuple:
            return False

        container_type = typeinspect.get_origin(target)
        item_types = typeinspect.resolve_tuple(target)[0]
        return has_converter(container_type) and all(map(has_converter, item_types))

    def convert(self, value: Any, target: type) -> tuple:
        # convert to a collection
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
class IterableConverter(ComplexConverterABC):
    """Converts the value to a typed iterable.

    The value is first converted to an untyped `Iterable`.
    All items are converted to the item type and gathered in a `list`.
    The list is then converted to the container type.
    """

    def can_convert(self, target: type) -> bool:
        is_iterable = typeinspect.is_generic_iterable(target) \
                      and not typeinspect.has_free_parameters(target) \
                      and not typeinspect.is_tuple(target) \
                      and not typeinspect.is_generic_mapping(target)

        if not is_iterable:
            return False

        container_type = typeinspect.get_origin(target)
        item_type = typeinspect.get_type_args(target)[0]
        return has_converter(container_type) and has_converter(item_type)

    def convert(self, value: Any, target: type) -> Iterable[T]:
        container_type = typeinspect.get_origin(target)
        item_type = typeinspect.get_type_args(target)[0]

        final_list = []

        it = convert_value(value, Iterable)
        for i, sub_value in enumerate(it):
            try:
                v = convert_value(sub_value, item_type)
            except ConversionError as e:
                raise ConversionError(f"couldn't convert value at index {i} ({sub_value!r}) "
                                      f"to {typeinspect.friendly_name(item_type)}") from e

            final_list.append(v)

        if container_type is not None:
            final_list = convert_value(final_list, container_type, exclude_converters={self})

        return final_list


@register_converter()
class MappingConverter(ComplexConverterABC):
    """Converts the value to a mapping.

    The value is first converted to an untyped `Mapping`.
    A `dict` is which maps the keys converted to the key type to
    the values converted to the value type.
    This dict is then converted to the container type.
    """

    def can_convert(self, target: type) -> bool:
        is_mapping = typeinspect.is_generic_mapping(target) \
                     and not typeinspect.has_free_parameters(target)
        if not is_mapping:
            return False

        container_type = typeinspect.get_origin(target)
        key_type, value_type = typeinspect.get_type_args(target)

        return has_converter(container_type) \
               and has_converter(key_type) \
               and has_converter(value_type)

    def convert(self, value: Any, target: type) -> Iterable[T]:
        container_type = typeinspect.get_origin(target)
        key_type, value_type = typeinspect.get_type_args(target)

        final_map = {}

        mapping = convert_value(value, Mapping)
        for key, value in mapping.items():
            try:
                k = convert_value(key, key_type)
            except ConversionError as e:
                raise ConversionError(f"couldn't convert key {key!r} to "
                                      f"{typeinspect.friendly_name(key_type)}") from e

            try:
                v = convert_value(value, value_type)
            except ConversionError as e:
                raise ConversionError(f"couldn't convert value of {key!r} ({value!r}) "
                                      f"to {typeinspect.friendly_name(value_type)}") from e

            final_map[k] = v

        if container_type is not None:
            final_map = convert_value(final_map, container_type, exclude_converters={self})

        return final_map


@register_converter()
class TemplateConverter(ComplexConverterABC):
    """Converter which converts the value to a template-like object.

    This converter exists mainly for templates used in containers like
    `List[MyTemplate]` or `Dict[str, MyTemplate]`.

    It also requires that the value is a complete template object. This
    is why it shouldn't be used by a source.
    """

    def can_convert(self, target: type) -> bool:
        return templ.is_template_like(target)

    def convert(self, value: Any, target: type) -> Any:
        value_map = convert_value(value, Mapping)

        fields = templ.fields(target)
        obj = templ.create_object_from_template(target)
        source.load_fields_values(obj, fields, value_map)
        templ.ensure_complete(obj, target)

        return obj


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

        raise ConversionError(f"{value!r} isn't in enum {typeinspect.friendly_name(target)}")
