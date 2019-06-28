import abc
import functools
import inspect
from typing import Any, Callable, Dict, Generic, Iterable, List, Mapping, MutableMapping, Optional, Type, TypeVar, Union

import konfi

__all__ = ["ConverterABC", "ConverterFunc", "ConverterType", "ComplexConverterABC",
           "is_converter_type", "is_complex_converter",
           "register_converter", "get_converters", "has_converter",
           "convert_value",
           "load_field_value", "load_template_value"]

CT = TypeVar("CT")


# TODO more complex conversions like List[type]


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
    if issubclass(obj, ConverterABC) or isinstance(obj, ConverterABC):
        return True

    # TODO check signature
    return callable(obj)


def is_complex_converter(obj: Any) -> bool:
    return issubclass(obj, ComplexConverterABC) or isinstance(obj, ComplexConverterABC)


CONVERTERS: MutableMapping[Type, List[ConverterType]] = {}
COMPLEX_CONVERTERS: List[ComplexConverterABC] = []


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

            COMPLEX_CONVERTERS.append(target)
        else:
            if not types:
                raise ValueError("at least one target type must be provided for non-complex converters")

            for typ in types:
                cs = CONVERTERS.setdefault(typ, [])
                cs.append(target)

    return decorator


# TODO unregister_converter


def _call_converter(conv: ConverterType, value: Any, target: Type) -> Any:
    if issubclass(conv, ConverterABC):
        try:
            conv = conv()
        except Exception:
            # TODO raise
            raise

    if isinstance(conv, ConverterABC):
        converter_func = functools.partial(conv.convert, value, target)
    elif callable(conv):
        converter_func = functools.partial(value)
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
        converters = CONVERTERS[target]
    except KeyError:
        converters = [c for c in COMPLEX_CONVERTERS if c.can_convert(target)]

    # add target if it's a "constructor"
    if not converters and inspect.isclass(target):
        converters.insert(0, target)

    return reversed(converters)


def has_converter(target: Type) -> bool:
    try:
        next(iter(get_converters(target)))
    except StopIteration:
        return False
    else:
        return True


def convert_value(value: Any, target: Type) -> Any:
    # TODO check if value is already type target

    converters = get_converters(target)

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
        # TODO maybe try using the target type as a converter (like int, str)
        # TODO raise
        raise Exception

    # can't be None unless there are no converters which we're already checking
    raise last_exception


def load_field_value(obj: Any, field: konfi.Field, value: Any) -> None:
    try:
        converted = convert_value(value, field.value_type)
    except Exception:
        # TODO only catch conversion exception
        # TODO raise
        raise

    setattr(obj, field.attribute, converted)


def _get_sub_obj(obj: Any, field: konfi.Field) -> Any:
    try:
        value = getattr(obj, field.attribute)
    except AttributeError:
        value = object.__new__(field.value_type)

    return value


def load_template_value(obj: Any, fields: Iterable[konfi.Field], mapping: Mapping, *,
                        ignore_unknown: bool = False) -> None:
    _field_by_keys: Dict[str, konfi.Field] = {field.key: field for field in fields}
    for key, value in mapping.items():
        try:
            field = _field_by_keys[key]
        except KeyError:
            if ignore_unknown:
                continue
            else:
                # TODO raise something
                raise Exception

        if konfi.is_template(field.value_type) and isinstance(value, Mapping):
            sub_obj = _get_sub_obj(obj, field)
            try:
                load_template_value(sub_obj, konfi.fields(sub_obj), value)
            except Exception:
                # TODO add detail
                raise
        else:
            try:
                load_field_value(obj, field, mapping)
            except Exception:
                # TODO add more detail
                raise
