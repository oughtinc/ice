from fvalues import F

from ice.json_value import to_json_value
from ice.summarize import summarize


def test_f():
    name = "world"
    f = F(f"hello {name}")
    assert to_json_value(f) == {
        "__fstring__": [
            "hello ",
            {"source": "name", "value": "world", "formatted": "world"},
        ]
    }
    assert summarize(to_json_value(f)) == {"name": "world"}
    f += "!"
    assert summarize(to_json_value(f)) == {"f": {"name": "world"}}
