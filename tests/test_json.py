from dataclasses import dataclass

from fvalues import F
from pydantic import BaseModel

from ice.json_value import to_json_value


@dataclass
class MyDataClass:
    things: list


class MyModel(BaseModel):
    stuff: dict


def test_objects():
    assert to_json_value(MyDataClass([1, 2, 3])) == {"things": [1, 2, 3]}
    assert to_json_value(MyModel(stuff={"a": 1})) == {"stuff": {"a": 1}}
    assert to_json_value(
        MyDataClass(
            [
                MyModel(
                    stuff={
                        "foo": MyDataClass(
                            ["a", "b"],
                        ),
                        "bar": 9,
                    }
                ),
                "c",
            ]
        )
    ) == {
        "things": [
            {
                "stuff": {
                    "foo": {
                        "things": [
                            "a",
                            "b",
                        ]
                    },
                    "bar": 9,
                }
            },
            "c",
        ]
    }


def test_non_str_keys():
    assert to_json_value({"a": 1, 2: 3}) == {"a": 1, "2": 3}


def test_iterables():
    assert to_json_value([1, 2, 3]) == [1, 2, 3]
    assert to_json_value((1, 2, 3)) == [1, 2, 3]
    # Sets are unordered, so use a singleton for testing
    assert to_json_value({1}) == [1]


def test_function():
    def foo():
        pass

    assert to_json_value(foo) == {
        "class_name": "function",
        "name": "foo",
    }


def test_primitives():
    things = [1, 2.3, None, "4", True, False]
    assert to_json_value(things) == things
    for thing in things:
        assert to_json_value(thing) is thing


def test_repr():
    class Foo:
        def dict(self, x):
            # This doesn't get used because it has a parameter,
            # which leads to raising a TypeError when .dict() is called.
            return {"a": x}

        def __repr__(self):
            return "Foo"

    assert to_json_value(Foo()) == "Foo"


def test_f():
    f = F(f"hello {1 + 2} world")
    assert to_json_value(f) == {
        "__fstring__": [
            "hello ",
            {"formatted": "3", "source": "1 + 2", "value": 3},
            " world",
        ]
    }
