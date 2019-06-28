from typing import Any, Iterable, List, TypeVar

from .converter import ComplexConverterABC, convert_value, register_converter

T = TypeVar("T")


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
class IterableConverter(ComplexConverterABC[Iterable[T]]):
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
