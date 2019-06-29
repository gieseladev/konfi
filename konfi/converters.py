import enum
from typing import Any, Iterable, List, Optional, TypeVar, cast

from .converter import ComplexConverterABC, convert_value, register_converter

T = TypeVar("T")

for const_converter in {str, int, float}:
    register_converter(const_converter)(const_converter)


@register_converter(None)
def none_converter(_: Any) -> None:
    return None


@register_converter(Iterable)
def iterable_converter(value: Any) -> Iterable:
    if isinstance(value, Iterable) and not isinstance(value, (str,)):
        return value
    else:
        return [value]


@register_converter(List, list)
def list_converter(value: Any) -> List:
    return list(convert_value(value, Iterable))


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
class EnumConverter(ComplexConverterABC):
    def can_convert(self, target: type) -> bool:
        return issubclass(target, enum.Enum)

    def convert(self, value: Any, target: enum.EnumMeta) -> enum.Enum:
        try:
            return target[value]
        except KeyError:
            pass

        first_name_match: Optional[enum.Enum] = None
        first_value_match: Optional[enum.Enum] = None

        value_lower = value.lower() if isinstance(value, str) else value

        for enum_field in target:
            enum_field = cast(enum.Enum, enum_field)

            if first_name_match is None and value_lower == enum_field.name.lower():
                first_name_match = enum_field
                break

            if first_value_match is None and value == enum_field.value:
                first_value_match = enum_field

        if first_name_match is not None:
            return first_name_match

        if first_value_match is not None:
            return first_value_match

        # TODO I dunno what to raise
        raise Exception
