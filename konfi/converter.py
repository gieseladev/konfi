import abc
from typing import Any, Callable, Generic, List, MutableMapping, Optional, Type, TypeVar, Union

from .field import Field

__all__ = ["ConverterABC", "ConverterFunc", "ConverterType",
           "is_converter_type", "register_converter",
           "get_converters", "convert_value", "set_value"]

CT = TypeVar("CT")


# TODO more complex conversions like List[type]


class ConverterABC(abc.ABC, Generic[CT]):
    @abc.abstractmethod
    def convert(self, value: Any) -> CT:
        ...


ConverterFunc = Callable[[Any], CT]

ConverterType = Union[ConverterABC, Type[ConverterABC], ConverterFunc]


def is_converter_type(obj: Any) -> bool:
    if issubclass(obj, ConverterABC) or isinstance(obj, ConverterABC):
        return True

    # TODO check signature
    return callable(obj)


CONVERTERS: MutableMapping[Type, List[ConverterType]] = {}


def register_converter(typ: Type):
    def decorator(target: ConverterType):
        if not is_converter_type(target):
            raise TypeError("decorated object must be a register_converter.")

        CONVERTERS.setdefault(typ, []).insert(0, target)

    return decorator


def _call_converter(conv: ConverterType, value: Any) -> Any:
    if issubclass(conv, ConverterABC):
        try:
            conv = conv()
        except Exception:
            # TODO raise
            raise

    if isinstance(conv, ConverterABC):
        converter_func = conv.convert
    elif callable(conv):
        converter_func = conv
    else:
        # TODO raise
        raise Exception

    try:
        return converter_func(value)
    except Exception:
        # TODO raise
        raise


def get_converters(target: Type) -> List[ConverterType]:
    try:
        return CONVERTERS[target]
    except KeyError:
        return []


def convert_value(value: Any, target: Type) -> Any:
    # TODO check if value is already type target

    converters = get_converters(target)
    if not converters:
        # TODO maybe try using the target type as a register_converter (like int, str)
        # TODO raise
        raise Exception

    last_exception: Optional[Exception] = None
    for conv in converters:
        try:
            converted = _call_converter(conv, value)
        except Exception as e:
            # TODO only catch conversion exception
            last_exception = e
        else:
            return converted

    # can't be None unless there are no converters which we're already checking
    raise last_exception


def set_value(obj: Any, field: Field, value: Any) -> None:
    try:
        converted = convert_value(value, field.value_type)
    except Exception:
        # TODO only catch conversion exception
        # TODO raise
        raise

    setattr(obj, field.attribute, converted)
