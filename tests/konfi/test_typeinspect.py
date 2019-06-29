from typing import Any, Optional, Tuple, Union

from konfi import typeinspect


def test_is_union() -> None:
    assert typeinspect.is_union(Union[int, str])
    assert typeinspect.is_union(Optional[int])


def test_is_optional() -> None:
    assert typeinspect.is_optional(Optional[Any])
    assert typeinspect.is_optional(Union[int, str, Union[float, None]])


def test_resolve_tuple() -> None:
    assert typeinspect.resolve_tuple(Tuple[int, int]) == ((int, int), 2)
    assert typeinspect.resolve_tuple(Tuple[int, ...]) == ((int,), None)


def test_has_type() -> None:
    assert typeinspect.has_type((1, "a"), Tuple[int, str])
    assert typeinspect.has_type((1, "a"), Tuple[Union[int, str], ...])
    assert typeinspect.has_type((1, 2), Tuple[int, ...])
    assert not typeinspect.has_type((1, "a"), Tuple[int, ...])
