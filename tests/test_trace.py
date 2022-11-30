from ice import trace
import pytest


@pytest.mark.anyio
async def test_trace_blocks():
    trace.enable_trace()
    current_trace = trace.trace_var.get()
    assert trace.trace_enabled()
    assert current_trace

    long = "a" * trace.Trace.BLOCK_LENGTH
    assert trace.emit_block("foo") == [0, 0]
    assert trace.emit_block("bar") == [0, 1]
    assert trace.emit_block(long) == [0, 2]
    assert trace.emit_block("baz") == [1, 0]
    assert trace.emit_block("quux") == [1, 1]

    assert (current_trace.dir / "block_0.jsonl").read_text() == f'"foo"\n"bar"\n"{long}"\nend'
