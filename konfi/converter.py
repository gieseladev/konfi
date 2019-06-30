import abc
import functools
import inspect
import logging
from typing import Any, Callable, Generic, Iterable, List, MutableMapping, Optional, Type, TypeVar, Union

from . import typeinspect

__all__ = ["ConverterABC", "ConverterFunc", "ConverterType", "ComplexConverterABC",
           "is_converter_type", "is_complex_converter",
           "register_converter", "get_converters", "has_converter",
           "ConversionError", "convert_value"]

log = logging.getLogger(__name__)

CT = TypeVar("CT")


class ConverterABC(abc.ABC, Generic[CT]):
    """Converter which converts a value to a type.

    Usually a normal converter only converts to one specific type, or a group
    of closely related types.
    """

    @abc.abstractmethod
    def convert(self, value: Any, target: Type[CT]) -> CT:
        """Convert the given value to the target type.

        Args:
            value: Value to convert.
            target: Type to convert the value to.

        Raises:
            Exception: When the conversion failed.

        Returns:
            Converted value.
        """
        ...


ConverterFunc = Callable[[Any], CT]
ConverterFunc.__doc__ = \
    """Callable which converts the given value to a type."""

ConverterType = Union[ConverterABC, Type[ConverterABC], ConverterFunc]
ConverterType.__doc__ = \
    """Type of a converter.
    """


class ComplexConverterABC(ConverterABC[Any], abc.ABC):
    """

    Notes:
        Unlike `ConverterABC` converters, the complex converter will be converted
        to a singleton instance upon registration.
    """

    @abc.abstractmethod
    def can_convert(self, target: type) -> bool:
        ...


def is_converter_type(obj: Any) -> bool:
    """Check if the object is a converter (`ConverterType`)."""
    if isinstance(obj, ConverterABC) or inspect.isclass(obj) and issubclass(obj, ConverterABC):
        return True

    # TODO check signature
    return callable(obj)


def is_complex_converter(obj: Any) -> bool:
    """Check if the object is a complex converter.`"""
    return isinstance(obj, ComplexConverterABC) or inspect.isclass(obj) and issubclass(obj, ComplexConverterABC)


_CONVERTERS: MutableMapping[Type, List[ConverterType]] = {}
_COMPLEX_CONVERTERS: List[ComplexConverterABC] = []


def register_converter(*types: Type):
    """Decorator which registers the underlying type as a converter.

    This can either be a converter function (`ConverterFunc`), a `ConverterABC`
    class or an instance thereof.
    If the converter is a class, it is instantiated only when the conversion
    takes place. The constructor will be called without any arguments.
    There is an exception for `ComplexConverterABC` classes, as they are
    instantiated upon registration.

    Args:
        *types: Types which the converter converts to.
            This is ignored if the converter is a complex converter, but
            required otherwise.

    Raises:
        TypeError: If the decorated object isn't a converter type.
        ValueError: If no types are provided but the converter
            isn't a complex converter.
    """

    def decorator(target: ConverterType):
        if not is_converter_type(target):
            raise TypeError("decorated object must be a converter.")

        if is_complex_converter(target):
            if inspect.isclass(target):
                try:
                    target = target()
                except Exception as e:
                    raise ValueError(f"Couldn't create instance of complex converter {target!r}") from e

            _COMPLEX_CONVERTERS.append(target)
        else:
            if not types:
                raise ValueError("at least one target type must be provided for non-complex converters")

            for typ in types:
                cs = _CONVERTERS.setdefault(typ, [])
                cs.append(target)

        return target

    return decorator


# TODO unregister_converter

def get_converters(target: Type) -> Iterable[ConverterType]:
    """Get the converters for the given target type.

    Complex converters are only returned if no other converter could be found,
    The converters are ordered in the reverse order of their registration.
    """
    # iterate in reverse because we want custom converters to override built-ins
    try:
        converters = _CONVERTERS[target]
    except KeyError:
        converters = [c for c in _COMPLEX_CONVERTERS if c.can_convert(target)]

    return reversed(converters)


def has_converter(target: Type) -> bool:
    """Check whether the given target type has a converter."""
    try:
        next(iter(get_converters(target)))
    except StopIteration:
        return False
    else:
        return True


class ConversionError(Exception):
    """Exception raised if a conversion failed."""
    ...


def _call_converter(conv: ConverterType, value: Any, target: Type) -> Any:
    if inspect.isclass(conv) and issubclass(conv, ConverterABC):
        try:
            conv = conv()
        except Exception as e:
            raise ConversionError(f"Couldn't create an instance of the converter {conv}") from e

    if isinstance(conv, ConverterABC):
        converter_func = functools.partial(conv.convert, value, target)
    elif callable(conv):
        converter_func = functools.partial(conv, value)
    else:
        raise TypeError(f"Converter must be a converter type, not {conv!r}")

    try:
        return converter_func()
    except ConversionError as e:
        raise e
    except Exception as e:
        # TODO use some sort of "friendly_name" function to get {target}
        raise ConversionError(f"Couldn't convert {value!r} to {target} using {conv}") from e


def convert_value(value: Any, target: Type) -> Any:
    """Convert the value to the given type.

    If no converter was found but the target type is a class,
    a conversion using the constructor is attempted.

    If the value already has the target type, it is returned even if no
    converters are found.

    Raises:
        ConversionError: If the conversion failed.
    """
    converters = get_converters(target)

    last_exception: Optional[Exception] = None
    for c in converters:
        try:
            converted = _call_converter(c, value, target)
        except ConversionError as e:
            last_exception = e
        else:
            return converted

    # if we already have the correct type then just move on
    if typeinspect.has_type(value, target):
        return value

    # no converter found
    if last_exception is None:
        if inspect.isclass(target):
            log.debug("no converters found, trying constructor")
            try:
                return target(value)
            except Exception as e:
                raise ConversionError(f"No converter found and couldn't use {target!r} directly") from e

        raise ConversionError(f"No converter found for {target!r}")

    raise last_exception
