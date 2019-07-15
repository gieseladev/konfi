from typing import Any, Type

import konfi
from konfi.converter import CT


def test_unregister_converter():
    class SentinelA: ...

    class SentinelB: ...

    class SentinelC: ...

    @konfi.register_converter(SentinelA, SentinelB, SentinelC)
    def func_conv():
        pass

    assert konfi.has_converter(SentinelA)
    konfi.unregister_converter(func_conv, SentinelA)

    assert not konfi.has_converter(SentinelA)
    assert konfi.has_converter(SentinelB)
    assert konfi.has_converter(SentinelC)

    konfi.unregister_converter(func_conv)
    assert not konfi.has_converter(SentinelB)
    assert not konfi.has_converter(SentinelC)


def test_unregister_complex_converter():
    class SentinelA: ...

    @konfi.register_converter()
    class Complex(konfi.ComplexConverterABC):
        def can_convert(self, target: type) -> bool:
            return target is SentinelA

        def convert(self, value: Any, target: Type[CT]) -> CT:
            pass

    assert konfi.has_converter(SentinelA)
    konfi.unregister_converter(Complex)
    assert not konfi.has_converter(SentinelA)
