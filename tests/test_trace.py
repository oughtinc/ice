import pandas as pd
import pytest

from ice import trace


@pytest.mark.anyio
async def test_trace_blocks():
    trace.enable_trace()
    current_trace = trace.trace_var.get()
    assert trace.trace_enabled()
    assert current_trace

    long = "a" * trace.Trace.BLOCK_LENGTH
    assert trace.emit_block("foo") == (0, 0)
    assert trace.emit_block("bar") == (0, 1)
    assert trace.emit_block(long) == (0, 2)
    assert trace.emit_block("baz") == (1, 0)
    assert trace.emit_block("quux") == (1, 1)

    # Now repeat the same blocks and check caching
    assert trace.emit_block("baz") == (1, 0)
    assert trace.emit_block("bar") == (0, 1)
    assert trace.emit_block(long) == (0, 2)
    assert trace.emit_block("foo") == (0, 0)
    assert trace.emit_block("foo") == (0, 0)
    assert trace.emit_block("foo") == (0, 0)
    assert trace.emit_block(long) == (0, 2)
    assert trace.emit_block("quux") == (1, 1)

    assert (
        current_trace.dir / "block_0.jsonl"
    ).read_text() == f'"foo"\n"bar"\n"{long}"\nend\n'


def test_get_strings():
    assert trace.get_strings("foo") == ["foo"]
    assert trace.get_strings(["foo", "bar"]) == ["foo", "bar"]
    assert trace.get_strings({"foo": "bar"}) == ["bar"]

    # First descendant list of strings
    assert trace.get_strings({"foo": {"spam": ["bar", "baz"], "x": "y"}}) == [
        "bar",
        "baz",
    ]

    # Empty values that get converted to '()'
    assert trace.get_strings([]) == ["()"]
    assert trace.get_strings(()) == ["()"]
    assert trace.get_strings({}) == ["()"]
    assert trace.get_strings(None) == ["()"]
    assert trace.get_strings("") == ["()"]

    # Other falsy values are just their string representation
    assert trace.get_strings(0) == ["0"]
    assert trace.get_strings(0.0) == ["0.0"]
    assert trace.get_strings(False) == ["False"]

    # First descendant isn't a string, gets converted
    assert trace.get_strings([1, 2, 3]) == ["1"]

    # Long lists get truncated
    assert trace.get_strings(["1", "2", "3", "4", "5"]) == ["1", "2", "3", "..."]

    # Long strings get truncated
    assert trace.get_strings("a" * 100) == ["a" * 35 + "..."]

    # `value` gets extracted
    assert trace.get_strings({"a": "b", "c": "d"}) == ["b"]
    assert trace.get_strings({"value": "b", "c": "d"}) == ["b"]
    assert trace.get_strings({"a": "b", "value": "d"}) == ["d"]
    assert trace.get_strings({"a": "b", "value": {}}) == ["()"]

    # self and record are omitted
    assert trace.get_strings({"self": "foo", "record": "bar", "a": "b", "c": "d"}) == [
        "b"
    ]
    assert trace.get_strings({"self": "foo", "record": "bar"}) == ["()"]
    assert trace.get_strings(
        {
            "x": "y",
            "value": {"self": "foo", "record": "bar", "a": "b", "c": "d"},
        }
    ) == ["b"]

    # Non-strings are filtered out
    assert trace.get_strings(["a", "b", 3, None, "c"]) == ["a", "b", "c"]

    # Tuples are converted to lists
    assert trace.get_strings(("a", "b")) == ["a", "b"]

    # Nested lists are not flattened
    assert trace.get_strings([["a", "b"], ["c", "d"]]) == ["a", "b"]

    assert trace.get_strings(pd.DataFrame({"a": [1, 2, 3]})) == [
        "   a\n" "0  1\n" "1  2\n" "2  3"
    ]
