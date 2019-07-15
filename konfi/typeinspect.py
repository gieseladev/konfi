"""Runtime introspection for typings."""

import inspect
import sys
from typing import Any, Generic, Iterable, Mapping, Optional, Tuple, TypeVar, \
    Union, _GenericAlias, _eval_type, Dict, ForwardRef

TypeTuple = Tuple[type, ...]
TypeTuple.__doc__ = \
    """Variadic tuple containing types."""

NoneType = type(None)


def class_and_subclass(typ: type, cls: type) -> bool:
    return inspect.isclass(typ) and issubclass(typ, cls)


def get_origin(typ: type) -> Optional[type]:
    if isinstance(typ, _GenericAlias):
        return typ.__origin__

    return None


def has_origin(typ: type, origin: type) -> bool:
    typ_origin = get_origin(typ)
    if typ_origin is None:
        return False

    return class_and_subclass(typ_origin, origin)


def get_type_args(typ: type) -> TypeTuple:
    if isinstance(typ, _GenericAlias):
        return typ.__args__

    return ()


def get_parameters(typ: type) -> TypeTuple:
    if isinstance(typ, _GenericAlias):
        return typ.__parameters__

    return ()


def has_free_parameters(typ: type) -> bool:
    return len(get_parameters(typ)) > 0


def is_any(typ: type) -> bool:
    # TODO typevar?
    return typ is Any


def is_union(typ: type) -> bool:
    return get_origin(typ) is Union


def is_tuple(typ: type) -> bool:
    return typ is Tuple \
           or get_origin(typ) is tuple \
           or is_generic(typ) and class_and_subclass(typ, tuple)


def is_typevar(typ: type) -> bool:
    return isinstance(typ, TypeVar)


def is_generic(typ: type) -> bool:
    return class_and_subclass(typ, Generic) \
           or isinstance(typ, _GenericAlias)


def is_generic_iterable(typ: type) -> bool:
    return is_generic(typ) and has_origin(typ, Iterable)


def is_generic_mapping(typ: type) -> bool:
    return is_generic(typ) and has_origin(typ, Mapping)


def is_optional(typ: type) -> bool:
    if typ is NoneType:
        return True
    elif is_union(typ):
        return any(is_optional(t) for t in get_type_args(typ))
    # TODO typevar ?
    else:
        return False


def resolve_tuple(typ: type) -> Tuple[TypeTuple, Optional[int]]:
    args = get_type_args(typ)
    # homogeneous variadic tuple
    if len(args) == 2 and args[1] == Ellipsis:
        return (args[0],), None
    else:
        return args, len(args)


def _has_union_type(obj: Any, union: type) -> bool:
    return any(has_type(obj, typ) for typ in get_type_args(union))


def _has_tuple_type(obj: Any, tup: type) -> bool:
    if not isinstance(obj, tuple):
        return False

    types, n = resolve_tuple(tup)
    if n is None:
        typ = types[0]
        return all(has_type(val, typ) for val in obj)
    elif n != len(obj):
        return False
    else:
        return all(has_type(val, typ) for val, typ in zip(obj, types))


def _has_generic_iterable_type(obj: Any, iter_type: type) -> bool:
    container_type = get_origin(iter_type)
    if not has_type(obj, container_type):
        return False

    item_type = get_type_args(iter_type)[0]
    return all(has_type(item, item_type) for item in obj)


def _has_generic_mapping_type(obj: Any, map_type: type) -> bool:
    container_type = get_origin(map_type)
    if not has_type(obj, container_type):
        return False

    key_type, value_type = get_type_args(map_type)
    return all(has_type(key, key_type) and has_type(value, value_type) for key, value in obj.items())


def has_type(obj: Any, typ: type) -> bool:
    if is_any(typ):
        return True

    if is_union(typ):
        return _has_union_type(obj, typ)

    if is_tuple(typ):
        return _has_tuple_type(obj, typ)

    if is_generic_iterable(typ):
        return _has_generic_iterable_type(obj, typ)

    if is_generic_mapping(typ):
        return _has_generic_mapping_type(obj, typ)

    # TODO this doesn't feel safe
    return isinstance(obj, typ)


def friendly_name(typ: Any) -> str:
    if inspect.isclass(typ) and typ.__module__ == "builtins":
        return typ.__qualname__
    else:
        if is_union(typ):
            args = get_type_args(typ)
            if len(args) == 2 and args[1] is NoneType:
                return f"typing.Optional[{friendly_name(args[0])}]"

        return repr(typ)


def get_class_type_hints_strict(cls: type,
                                globalns: Mapping[str, Any] = None,
                                localns: Mapping[str, Any] = None
                                ) -> Dict[str, type]:
    if not inspect.isclass(cls):
        raise TypeError("cls needs to be a class. Use typing.get_type_hints for other types")

    if globalns is None:
        globalns = sys.modules[cls.__module__].__dict__

    ann = cls.__dict__.get("__annotations__", {})

    hints = {}

    for name, value in ann.items():
        if value is None:
            value = type(None)
        if isinstance(value, str):
            value = ForwardRef(value, is_argument=False)

        value = _eval_type(value, globalns, localns)
        hints[name] = value

    return hints
