from unittest import mock

import konfi


def test_env_source():
    @konfi.template()
    class SubConf:
        b: int
        d_e: float

    @konfi.template()
    class Conf:
        a: str
        with_underscore: str
        sub: SubConf

    with mock.patch("konfi.sources.env.os") as mocked_os:
        mocked_os.environ = {
            "P_A": "\"test\"",
            "P_WITHUNDERSCORE": "\"value\"",
            "P_SUB_B": "5",
            "P_SUB_DE": "3.5",
        }
        konfi.set_sources(konfi.Env("P_"))
        c: Conf = konfi.load(Conf)

    assert c.a == "test"
    assert c.with_underscore == "value"
    assert c.sub.b == 5
    assert c.sub.d_e == 3.5
