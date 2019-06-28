from typing import Tuple

from konfi import typeinspect


def test_has_type() -> None:
    assert typeinspect.has_type((1, 2), Tuple[int, int])
    assert typeinspect.has_type((1, 2), Tuple[int, ...])
