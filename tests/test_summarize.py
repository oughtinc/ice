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


def test_basic():
    assert summarize(list(range(10))) == [0, 1, 2]
    assert summarize(dict(enumerate(range(100)))) == {
        0: 0,
        1: 1,
        2: 2,
        3: 3,
        4: 4,
        5: 5,
        6: 6,
        7: 7,
        8: 8,
        9: 9,
    }
    assert (
        summarize("abc" * 100)
        == "abcabcabcabcabcabcabcabcabcabcabcabcabcabcabcabc...cabcabcabcabcabcabcabcabcabcabcabcabcabcabcabcabc"
    )


def test_depth():
    assert summarize({"a": {"b": {"c": 3}}}) == {
        "a": {
            "b": {
                "c": 3,
            }
        }
    }
    assert (
        summarize(
            {
                "a": {
                    "b": {
                        "c": {
                            "d": 3,
                        }
                    }
                }
            }
        )
        == {}
    )
    assert summarize({"a": {"b": {"c": {"d": 3}, "e": 4}}}) == {
        "a": {
            "b": {
                "e": 4,
            },
        }
    }


def test_empty():
    assert summarize({"a": "b", "c": None, "d": {}, "e": [], "f": ""}) == {
        "a": "b",
    }
