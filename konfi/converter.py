import abc
import functools
import inspect
import logging
from typing import Any, Callable, Generic, Iterable, List, MutableMapping, Optional, Set, Type, TypeVar, Union, \
    overload, Tuple

from . import typeinspect

__all__ = ["ConverterABC", "ConverterFunc", "ConverterType", "ComplexConverterABC",
           "is_converter_type", "is_complex_converter",
           "register_converter", "unregister_converter",
           "get_converters", "has_converter",
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

    # we could check the signature too, but at some point we just have to
    # trust the user
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
            isn't a complex converter or vice versa.
    """

    def decorator(target: ConverterType):
        if not is_converter_type(target):
            raise TypeError("decorated object must be a converter.")

        if is_complex_converter(target):
            if types:
                raise ValueError("no types can be given for complex converters, use the can_convert method instead.")

            if inspect.isclass(target):
                try:
                    target_inst = target()
                except Exception as e:
                    raise ValueError(f"Couldn't create instance of complex converter {target!r}") from e
            else:
                target_inst = target

            _COMPLEX_CONVERTERS.append(target_inst)
        else:
            if not types:
                raise ValueError("at least one target type must be provided for non-complex converters")

            for typ in types:
                cs = _CONVERTERS.setdefault(typ, [])
                cs.append(target)

        _clear_converter_cache()
        return target

    return decorator


def unregister_converter(conv: ConverterType, *types: type) -> None:
    """Unregister the given converter from the given types.

    Args:
        conv: Converter to unregister
        *types: Types to unregister converter from. If empty, the converter
            is unregistered from all types.

    Raises:
        TypeError: If the given converter is a complex converter and types
            are given.
    """
    if is_complex_converter(conv):
        if types:
            raise TypeError("can't unregister a complex converter from specific types")

        if inspect.isclass(conv):
            for _conv in reversed(_COMPLEX_CONVERTERS):
                if type(_conv) is conv:
                    conv = _conv
                    break
            else:
                return

        try:
            _COMPLEX_CONVERTERS.remove(conv)
        except ValueError:
            return
    else:
        if not types:
            types = _CONVERTERS.keys()

        for typ in types:
            try:
                converters = _CONVERTERS[typ]
            except KeyError:
                continue

            try:
                converters.remove(conv)
            except ValueError:
                pass

    _clear_converter_cache()


@functools.lru_cache(maxsize=None)
def _get_complex_converters(target: Type) -> Tuple[ComplexConverterABC]:
    return tuple(c for c in reversed(_COMPLEX_CONVERTERS) if c.can_convert(target))


def get_converters(target: Type) -> Iterable[ConverterType]:
    """Get the converters for the given target type.

    Complex converters are only returned if no other converter could be found,
    The converters are ordered in the reverse order of their registration.
    """
    # iterate in reverse because we want custom converters to override built-ins
    try:
        return tuple(reversed(_CONVERTERS[target]))
    except KeyError:
        return _get_complex_converters(target)


def _clear_converter_cache() -> None:
    _get_complex_converters.cache_clear()


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
        raise ConversionError(f"Couldn't convert {value!r} to "
                              f"{typeinspect.friendly_name(target)} using {conv}") from e


T = TypeVar("T")


@overload
def convert_value(value: Any, target: Type[T], *, exclude_converters: Set[ConverterType] = None) -> T: ...


@overload
def convert_value(value: Any, target: type, *, exclude_converters: Set[ConverterType] = None) -> Any: ...


def convert_value(value: Any, target: Type[T], *, exclude_converters: Set[ConverterType] = None) -> T:
    """Convert the value to the given type.

    If no converter was found but the target type is a class,
    a conversion using the constructor is attempted.

    If the value already has the target type, it is returned even if no
    converters are found.

    Args:
        value: Value to convert
        target: Target type to convert to.

        exclude_converters: Set of converter types to exclude.
            Note that this only excludes the converters from this call,
            if a converter further down the line calls this function the
            exclusion no longer applies.

    Raises:
        ConversionError: If the conversion failed.
    """
    converters = get_converters(target)

    last_exception: Optional[Exception] = None
    for c in converters:
        if exclude_converters and c in exclude_converters:
            continue

        try:
            converted = _call_converter(c, value, target)
        except ConversionError as e:
            if last_exception is not None:
                e.__cause__ = last_exception

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
