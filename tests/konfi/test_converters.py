import enum

import konfi
from konfi import converter


def test_enum_converters():
    class MyEnum(enum.Enum):
        A = "a"
        BC = "test"
        TRYHARD = 5

    assert konfi.has_converter(MyEnum)
    assert converter.convert_value("A", MyEnum) == MyEnum.A
    assert converter.convert_value("test", MyEnum) == MyEnum.BC
    assert converter.convert_value(5, MyEnum) == MyEnum.TRYHARD
