"""Runtime introspection for typings."""

import inspect
from typing import Any, Generic, Optional, Tuple, Type, TypeVar, Union, _GenericAlias

TypeTuple = Tuple[type, ...]
TypeTuple.__doc__ = \
    """Variadic tuple containing types."""

NoneType = type(None)


def get_origin(typ: type) -> Optional[type]:
    if isinstance(typ, _GenericAlias):
        return typ.__origin__

    return None


def get_type_args(typ: type) -> TypeTuple:
    if isinstance(typ, _GenericAlias):
        return typ.__args__

    return ()


def is_any(typ: type) -> bool:
    # TODO typevar
    return typ is Any


def is_union(typ: type) -> bool:
    return get_origin(typ) is Union


def is_tuple(typ: type) -> bool:
    return typ is Tuple \
           or get_origin(typ) is tuple \
           or is_generic(typ) and issubclass(typ, tuple)


def is_typevar(typ: type) -> bool:
    return isinstance(typ, TypeVar)


def is_generic(typ: type) -> bool:
    # TODO maybe exclude tuple, union and so on
    return inspect.isclass(typ) and issubclass(typ, Generic)


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


def resolve_item_type(typ: type) -> type:
    pass


def _has_union_type(obj: Any, union: Union) -> bool:
    return any(has_type(obj, typ) for typ in get_type_args(union))


def _has_tuple_type(obj: Any, tup: Type[Tuple]) -> bool:
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


def has_type(obj: Any, typ: type) -> bool:
    if is_any(typ):
        return True

    if is_union(typ):
        return _has_union_type(obj, typ)

    if is_tuple(typ):
        return _has_tuple_type(obj, typ)

    # TODO handle generic containers

    # TODO this doesn't feel safe
    return isinstance(obj, typ)
