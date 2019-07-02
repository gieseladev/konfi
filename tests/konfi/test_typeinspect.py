from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, Union

import pytest

from konfi import typeinspect


def test_get_origin():
    assert typeinspect.get_origin(List[str]) is list
    assert typeinspect.get_origin(Dict[str, int]) is dict


def test_has_origin():
    assert typeinspect.has_origin(List[str], list)
    assert typeinspect.has_origin(List[str], List)
    assert typeinspect.has_origin(List[str], Iterable)

    assert typeinspect.has_origin(Dict[str, int], Iterable)
    assert typeinspect.has_origin(Dict[str, int], Mapping)
    assert typeinspect.has_origin(Dict[str, int], dict)
    assert typeinspect.has_origin(Dict[str, int], Dict)


def test_get_type_args():
    assert typeinspect.get_type_args(List[str]) == (str,)
    assert typeinspect.get_type_args(Dict[str, int]) == (str, int)
    assert typeinspect.get_type_args(Union[str, int]) == (str, int)
    assert typeinspect.get_type_args(Tuple[str, ...]) == (str, Ellipsis)


def test_is_any():
    assert typeinspect.is_any(Any)


def test_is_union() -> None:
    assert typeinspect.is_union(Union[int, str])
    assert typeinspect.is_union(Optional[int])


def test_is_tuple():
    assert typeinspect.is_tuple(Tuple[str, int])
    assert not typeinspect.is_tuple(Union[str, int])


def test_is_typevar():
    # TODO urgh
    pass


def test_is_generic():
    assert typeinspect.is_generic(List[str])
    assert typeinspect.is_generic(Dict[str, int])
    assert typeinspect.is_generic(Dict)


def test_is_optional() -> None:
    assert typeinspect.is_optional(Optional[Any])
    assert typeinspect.is_optional(Union[int, str, Union[float, None]])


def test_resolve_tuple() -> None:
    assert typeinspect.resolve_tuple(Tuple[int, int]) == ((int, int), 2)
    assert typeinspect.resolve_tuple(Tuple[int, ...]) == ((int,), None)


def test_has_type_special() -> None:
    assert not typeinspect.has_type((1, "a"), Tuple[int, ...])


TESTS = [
    (("lol",), Any),
    ((1, "a"), Tuple[int, str]),
    ((1, "a"), Tuple[Union[int, str], ...]),
    ((1, 2), Tuple[int, ...]),
    (["1", "string", "3"], List[str]),
    ([1, "string", 3], List[Union[int, str]]),
]


@pytest.mark.parametrize("val,typ", TESTS)
def test_has_type(val: Any, typ: type):
    assert typeinspect.has_type(val, typ)
