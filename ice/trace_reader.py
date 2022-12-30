import json
from functools import lru_cache

from ice.trace import traces_dir


class TraceReader:
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self._block_lines_cached = lru_cache(self._block_lines)

    @property
    def dir(self):
        return traces_dir / self.trace_id

    @property
    def trace_file(self):
        return self.dir / "trace.jsonl"

    def _block_lines(self, block_num):
        block_file = self.dir / f"block_{block_num}.jsonl"
        return block_file.read_text().splitlines()

    def block_value(self, address):
        num, lineno = address
        return json.loads(self._block_lines_cached(num)[lineno])

    def raw_events(self):
        for line in self.trace_file.open():
            yield json.loads(line)

    def events_with_block_values(self):
        for event in self.raw_events():
            [[call_id, data]] = event.items()
            assert call_id.isdigit()
            if "start" in data:
                data["args"] = self.block_value(data["args"])
                data["func"] = self.block_value(data["func"])
            elif "end" in data:
                data["result"] = self.block_value(data["result"])
            elif "records" in data:
                [[record_id, record]] = data["records"].items()
                data["records"][record_id] = self.block_value(record)
            yield event
