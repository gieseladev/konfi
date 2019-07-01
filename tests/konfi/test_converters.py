import enum
from typing import Any, Tuple, Union

import pytest

import konfi
from konfi import converter


def test_union_converter():
    assert konfi.convert_value("5", Union[str, int]) == "5"
    assert konfi.convert_value("5", Union[int, float]) == 5


def test_tuple_converter():
    assert konfi.convert_value([1, 2], Tuple[int, ...]) == (1, 2)
    assert konfi.convert_value([1, 2], Tuple[int, int]) == (1, 2)
    assert konfi.convert_value([1, "str"], Tuple[Union[int, str], ...]) == (1, "str")
    assert konfi.convert_value([1, "str"], Tuple[int, str]) == (1, "str")


def test_enum_converter():
    class MyEnum(enum.Enum):
        A = "a"
        BC = "test"
        TRYHARD = 5

    assert konfi.has_converter(MyEnum)
    assert converter.convert_value("A", MyEnum) == MyEnum.A
    assert converter.convert_value("test", MyEnum) == MyEnum.BC
    assert converter.convert_value(5, MyEnum) == MyEnum.TRYHARD


TESTS = [
    ("4", int, 4),
    ("4", float, 4.),
]


@pytest.mark.parametrize("inp,typ,expected", TESTS)
def test_converters(inp: Any, typ: type, expected: Any):
    assert konfi.convert_value(inp, typ) == expected
