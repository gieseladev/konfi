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


def test_template_mro():
    class NonTemplate:
        a: str

    @konfi.template()
    class Template:
        b: int
        c: int

    @konfi.template()
    class Normal(NonTemplate, Template):
        d: str

    assert tuple(field.attribute for field in konfi.fields(Normal)) == ("b", "c", "d")

    @konfi.template(template_bases_only=False)
    class Inherit(NonTemplate, Template):
        c: str

    assert set(field.attribute for field in konfi.fields(Inherit)) == {"b", "c", "a"}
