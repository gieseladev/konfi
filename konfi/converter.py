import abc
import functools
import inspect
import itertools
from typing import Any, Callable, Generic, Iterable, List, MutableMapping, Optional, Type, TypeVar, Union

from . import typeinspect

__all__ = ["ConverterABC", "ConverterFunc", "ConverterType", "ComplexConverterABC",
           "is_converter_type", "is_complex_converter",
           "register_converter", "get_converters", "has_converter",
           "convert_value"]

CT = TypeVar("CT")


class ConverterABC(abc.ABC, Generic[CT]):
    @abc.abstractmethod
    def convert(self, value: Any, target: Type[CT]) -> CT:
        ...


ConverterFunc = Callable[[Any], CT]

ConverterType = Union[ConverterABC, Type[ConverterABC], ConverterFunc]


class ComplexConverterABC(ConverterABC, abc.ABC):
    """

    Notes:
        Unlike `ConverterABC` converters, the complex converter will be converted
        to a singleton instance upon registration.
    """

    @abc.abstractmethod
    def can_convert(self, target: Type[CT]) -> bool:
        ...


def is_converter_type(obj: Any) -> bool:
    if isinstance(obj, ConverterABC) or inspect.isclass(obj) and issubclass(obj, ConverterABC):
        return True

    # TODO check signature
    return callable(obj)


def is_complex_converter(obj: Any) -> bool:
    return isinstance(obj, ComplexConverterABC) or inspect.isclass(obj) and issubclass(obj, ComplexConverterABC)


_CONVERTERS: MutableMapping[Type, List[ConverterType]] = {}
_COMPLEX_CONVERTERS: List[ComplexConverterABC] = []


def register_converter(*types: Type):
    def decorator(target: ConverterType):
        if not is_converter_type(target):
            raise TypeError("decorated object must be a converter.")

        if is_complex_converter(target):
            if inspect.isclass(target):
                try:
                    target = target()
                except Exception:
                    # TODO raise
                    raise

            _COMPLEX_CONVERTERS.append(target)
        else:
            if not types:
                raise ValueError("at least one target type must be provided for non-complex converters")

            for typ in types:
                cs = _CONVERTERS.setdefault(typ, [])
                cs.append(target)

    return decorator


# TODO unregister_converter


def _call_converter(conv: ConverterType, value: Any, target: Type) -> Any:
    if inspect.isclass(conv) and issubclass(conv, ConverterABC):
        try:
            conv = conv()
        except Exception:
            # TODO raise
            raise

    if isinstance(conv, ConverterABC):
        converter_func = functools.partial(conv.convert, value, target)
    elif callable(conv):
        converter_func = functools.partial(conv, value)
    else:
        # TODO raise
        raise Exception

    try:
        return converter_func()
    except Exception:
        # TODO raise
        raise


def get_converters(target: Type) -> Iterable[ConverterType]:
    # iterate in reverse because we want custom converters to override built-ins
    try:
        converters = _CONVERTERS[target]
    except KeyError:
        converters = [c for c in _COMPLEX_CONVERTERS if c.can_convert(target)]

    return reversed(converters)


def has_converter(target: Type) -> bool:
    try:
        next(iter(get_converters(target)))
    except StopIteration:
        return False
    else:
        return True


def convert_value(value: Any, target: Type) -> Any:
    # TODO move this further down to avoid unnecessarily checking the types?
    if typeinspect.has_type(value, target):
        return value

    converters = get_converters(target)

    # add target if it's a "constructor"
    if inspect.isclass(target):
        converters = itertools.chain(converters, target)

    last_exception: Optional[Exception] = None
    for c in converters:
        try:
            converted = _call_converter(c, value, target)
        except Exception as e:
            # TODO only catch conversion exception
            last_exception = e
        else:
            return converted

    if last_exception is None:
        # TODO raise
        raise Exception

    # can't be None unless there are no converters which we're already checking
    raise last_exception
