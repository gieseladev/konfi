import dataclasses

import konfi


def test_is_template_like():
    @konfi.template()
    class Templ:
        a: int

    @dataclasses.dataclass()
    class Data:
        b: int

    assert konfi.is_template_like(Templ)
    assert konfi.is_template_like(Data)
