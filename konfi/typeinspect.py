from typing import Any, Optional, Tuple, _GenericAlias

TypeTuple = Tuple[type, ...]
NoneType = type(None)


def get_origin(typ: type) -> Optional[type]:
    if isinstance(typ, _GenericAlias):
        return typ.__origin__

    return None


def is_optional(typ: type) -> bool:
    if typ is None:
        return True
    elif is_union_type(typ):
        pass
    else:
        return False


def is_union_type(typ: type) -> bool:
    pass


def resolve_union(typ: type) -> TypeTuple:
    pass


def resolve_tuple(typ: type) -> Tuple[TypeTuple, int]:
    pass


def resolve_list(typ: type) -> type:
    pass


def get_type(obj: Any) -> type:
    pass


def has_type(obj: Any, typ: type) -> bool:
    pass
