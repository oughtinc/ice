from ice.f import F
from ice.f import FValue
from ice.trace import _encode_json


def test_f():
    numbers = [1.23456789, 2, 3]
    ndigits = 2
    s = F(
        f"number is approximately equal to {numbers[0]:.{ndigits}f}, "
        f"rounded to {ndigits = } places."
    )
    assert s == "number is approximately equal to 1.23, rounded to ndigits = 2 places."
    assert s.parts == [
        "number is approximately equal to ",
        FValue(source="numbers[0]", value=1.23456789, formatted="1.23"),
        ", rounded to ndigits = ",
        FValue(source="ndigits", value=2, formatted="2"),
        " places.",
    ]


def test_f_json():
    name = "world"
    s = F(f"hello {name}")
    assert s == "hello world"
    assert s.parts == [
        "hello ",
        FValue(source="name", value="world", formatted="world"),
    ]
    assert _encode_json(s) == _encode_json(
        {
            "__fstring__": [
                "hello ",
                {"source": "name", "value": "world", "formatted": "world"},
            ]
        }
    )


def test_add():
    s = F("hello ") + "world"
    assert s == "hello world"
    assert s.parts == ["hello ", "world"]
    s = "hello " + F("world")
    assert s == "hello world"
    assert s.parts == ["hello ", "world"]
