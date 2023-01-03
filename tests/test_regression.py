"""
This module doesn't contain any tests directly.
The filename just starts with test_ so that pytest rewrites asserts.
Call check_trace() in another test after calling a traced function.
"""
import json
import os
import random

from contextlib import contextmanager
from pathlib import Path

from faker import Faker

from ice.trace import trace_var
from ice.trace_reader import TraceReader


def normalized_trace_events(trace_id: str):
    reader = TraceReader(trace_id)
    for event in reader.events_with_block_values():
        [[_call_id, data]] = event.items()
        if "start" in data:
            assert isinstance(data.pop("start"), int)
            assert isinstance(data.pop("func"), dict)
        elif "end" in data:
            assert isinstance(data.pop("end"), int)

        yield event


@contextmanager
def check_trace(name: str):
    """
    Check that the most recent trace matches the expected trace on disk.
    `name` is the filename under the expected_traces folder.
    Set the environment variable FIX_TESTS=1 to update the expected trace.
    """
    Faker.seed(name)
    random.seed(name)

    yield

    trc = trace_var.get()
    assert trc
    actual = list(normalized_trace_events(trc.id))
    assert actual
    path = Path(__file__).parent / "expected_traces" / f"{name}.json"
    if os.environ.get("FIX_TESTS"):
        json_dump = json.dumps(actual, indent=2, sort_keys=True)
        if len(json_dump) < 50_000:
            path.write_text(json_dump)
        elif path.exists():
            raise ValueError(
                f"Trace has become too large: {path} ({len(json_dump)} bytes)"
            )
    elif path.exists():
        expected = json.loads(path.read_text())
        assert actual == expected
