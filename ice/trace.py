import hashlib
import json
import opcode
import sys
import threading
import types
import inspect

from abc import ABCMeta
from contextvars import ContextVar
from functools import lru_cache
from inspect import getsource
from inspect import isclass
from inspect import isfunction
from pathlib import Path
from time import monotonic_ns
from typing import Any
from typing import cast
from typing import IO
from typing import Optional

import ulid

from structlog import get_logger

from ice.json_value import JSONValue
from ice.json_value import to_json_value
from ice.server import ensure_server_running
from ice.server import is_server_running
from ice.settings import OUGHT_ICE_DIR
from ice.settings import server_url
from ice.settings import settings
from ice.utils import get_docstring_from_code

log = get_logger()


call_id_stack: ContextVar[list[int]] = ContextVar("ids")

traces_dir = OUGHT_ICE_DIR / "traces"
traces_dir.mkdir(parents=True, exist_ok=True)


class Trace:
    """
    Manages storing trace data to disk.
    All data is stored under self.dir.
    The primary metadata is stored in self.file, named trace.jsonl.
    Potentially large values which will be lazily loaded are stored in block_*.jsonl.
    Each block file is appended to until its size exceeds BLOCK_LENGTH.
    """

    BLOCK_LENGTH = 1024**2

    def __init__(self):
        self.id = ulid.new().str
        self.dir = traces_dir / self.id
        self.dir.mkdir()
        self.file = self._open("trace")
        self.block_number = -1  # so that it starts at _open_block below
        self._open_block()
        self._lock = threading.Lock()

        # Keep an in-memory cache of recent block values (JSON strings)
        # keyed by their SHA256 hash, so equal values get the same address.
        # Apply lru_cache to the bound method to skip the self argument,
        # so instances of this class are not stored in the cache
        # and they can be garbage collected.
        self._write_block_value_cached = lru_cache(maxsize=1024)(
            self._write_block_value
        )
        # _write_block_value only takes one argument _string_hash,
        # so the potentially large values themselves don't live in memory.
        # The actual value is kept briefly in this attribute.
        self._current_block_value: str

        self._counter = 0
        call_id_stack.set([0])
        log.info(f"Trace: {self.url}")
        threading.Thread(target=self._server_and_browser).start()

    @property
    def url(self) -> str:
        return f"{server_url()}/traces/{self.id}"

    def next_counter(self) -> int:
        with self._lock:
            self._counter += 1
            return self._counter

    def _server_and_browser(self):
        is_running = None
        if settings.OUGHT_ICE_AUTO_SERVER:
            ensure_server_running()
            is_running = True

        if not settings.OUGHT_ICE_AUTO_BROWSER:
            return

        is_running = is_running or is_server_running()
        if not is_running:
            return

        import webbrowser

        log.info("Opening trace in browser, set OUGHT_ICE_AUTO_BROWSER=0 to disable.")
        webbrowser.open(self.url)

    def _open(self, name: str) -> IO[str]:
        return open(self.dir / f"{name}.jsonl", "a")

    def _open_block(self):
        self.block_number += 1
        self.block_file = self._open(f"block_{self.block_number}")
        self.block_length = 0
        self.block_lineno = 0

    def add_to_block(self, value) -> tuple[int, int]:
        """
        Write the value x to the current block file as a single JSON line.
        """
        string = _encode_json(value)
        string_hash = hashlib.sha256(string.encode("utf8")).digest()
        with self._lock:
            self._current_block_value = string
            return self._write_block_value_cached(string_hash)

    def _write_block_value(self, _string_hash: bytes) -> tuple[int, int]:
        address = (self.block_number, self.block_lineno)
        s = self._current_block_value
        self.block_file.write(s)
        self.block_length += len(s)
        if self.block_length > self.BLOCK_LENGTH:
            self.block_file.write("end\n")
            self.block_file.close()
            self._open_block()
        else:
            self.block_file.flush()
            self.block_lineno += 1
        return address


trace_var: ContextVar[Optional[Trace]] = ContextVar("trace", default=None)


def enable_trace():
    trace_var.set(Trace())
    sys.settrace(tracefunc)


def trace_enabled():
    return trace_var.get() is not None


def emit(value):
    if trc := trace_var.get():
        trc.file.write(_encode_json(value))
        trc.file.flush()


def emit_block(x) -> tuple[int, int]:
    if trc := trace_var.get():
        return trc.add_to_block(x)
    else:
        return 0, 0


def current_call_id() -> int:
    stack = call_id_stack.get()
    if stack:
        return stack[-1]


def add_fields(**fields: str):
    if trace_enabled():
        emit({current_call_id(): {"fields": fields}})


def _encode_json(x) -> str:
    # Note that sort_keys=True here could improve caching,
    # but it might make the output less readable.
    return json.dumps(to_json_value(x), separators=(",", ":")) + "\n"


# To add records to the trace, use the following code:
#
#     recorder(k1=v1, k2=v2)
#
# You can pass it any JSON-serializable keyword arguments.


class Recorder:
    def __call__(self, **kwargs):
        trc = trace_var.get()
        assert trc is not None
        emit({current_call_id(): {"records": {trc.next_counter(): emit_block(kwargs)}}})

    def __repr__(self):
        # So this can be used in `diskcache()` functions
        # The diskcache implementation should probably not
        # depend on calling __repr__ but that
        # seems like a larger refactor
        return "ice.trace._Recorder"


recorder = Recorder()

_trace_conditions = []
trace_when = _trace_conditions.append

_traced_files = set()
trace_when(lambda code: code.co_filename in _traced_files)
trace_file = _traced_files.add

_traced_folders = []
trace_when(lambda code: any(code.co_filename.startswith(f) for f in _traced_folders))


def trace_folder(folder: str | Path):
    _traced_folders.append(str(folder).rstrip("/") + "/")


_traced_file_ranges = []


@trace_when
def _trace_range(code):
    filename = code.co_filename
    lineno = code.co_firstlineno
    return any(
        filename == f and start <= lineno <= end
        for f, start, end in _traced_file_ranges
    )


def trace(fn):
    if isclass(fn) or isfunction(fn):
        try:
            lines, start = inspect.getsourcelines(fn)
        except Exception:
            return fn
        end = start + len(lines)
        filename = inspect.getsourcefile(fn)
        _traced_file_ranges.append((filename, start, end))

    return fn


_dont_trace_codes = set()


def dont_trace(fn: types.FunctionType):
    _dont_trace_codes.add(fn.__code__)
    return fn


@lru_cache(maxsize=None)
def should_trace(code: types.CodeType) -> bool:
    if (
        code.co_name.startswith("<")
        or code in _dont_trace_codes
        or not (code.co_flags & inspect.CO_COROUTINE & ~inspect.CO_ASYNC_GENERATOR)
    ):
        return False

    return any(cond(code) for cond in _trace_conditions)


def tracefunc(frame: types.FrameType, event: str, arg):
    if event not in ("call", "return"):
        return

    code = frame.f_code
    if not should_trace(code):
        return

    if event == "call":
        if frame.f_lasti != -1:
            return

        trc = trace_var.get()
        assert trc is not None
        id = trc.next_counter()
        stack = call_id_stack.get()
        call_id_stack.set(stack + [id])

        arg_dict = frame.f_locals
        arg_dict_json = to_json_value(arg_dict)
        call_event = dict(
            parent=stack[-1],
            start=monotonic_ns(),
            name=code.co_name,
            shortArgs=get_strings(arg_dict_json),
            func=emit_block(func_info(code)),
            args=emit_block(arg_dict_json),
        )
        self = arg_dict.get("self")
        if self:
            call_event["cls"] = self.__class__.__name__

        emit({id: call_event})
    else:
        code_byte = code.co_code[frame.f_lasti]
        opname = opcode.opname[code_byte]
        if opname != "RETURN_VALUE" and arg is not None or opname == "LOAD_CONST":
            return

        result_json = to_json_value(arg)
        *stack, call_id = call_id_stack.get()
        call_id_stack.set(stack)

        emit(
            {
                call_id: dict(
                    result=emit_block(result_json),
                    shortResult=get_strings(result_json),
                    end=monotonic_ns(),
                )
            }
        )
        if len(stack) <= 1:
            # We're at the top of the stack, so we're done with this trace.
            # trace_var.set(None)  # TODO this currently breaks regression testing
            sys.settrace(None)
            return

    return tracefunc


def to_json_serializable(self):
    namespace = dict(class_name=self.__class__.__name__)
    for attr in dir(self):
        if not attr.startswith("_"):
            value = getattr(self, attr)
            if isinstance(value, (bool, int, float, str)):
                namespace[attr] = value

    return namespace


class TracedABCMeta(ABCMeta):
    def __new__(mcls, name, bases, namespace):
        return trace(
            super().__new__(
                mcls,
                name,
                bases,
                namespace,
            )
        )


class TracedABC(metaclass=TracedABCMeta):
    dict = to_json_serializable


# TODO this and the functions it calls needs to be replaced with a better system
#   for summarising args and return values
def get_strings(value: JSONValue) -> list[str]:
    """
    Represent the given value as a short list of short strings
    that can be stored directly in the central trace file and loaded eagerly in the UI.
    """
    if isinstance(value, dict) and "value" in value:
        value = value["value"]

    if isinstance(value, dict):
        value = {k: v for k, v in value.items() if k not in ("self", "record")}

    result = _get_first_descendant(value)

    if isinstance(result, tuple):
        result = list(result)
    if not (isinstance(result, list) and result):
        # if result in (None, (), "", [], {}):
        # but without breaking due to truth-testing of pandas dataframes
        if any(
            isinstance(result, type(x)) and result == x
            for x in cast(tuple[Any], (None, (), "", [], {}))
        ):
            result = "()"
        result = [str(result)]

    result = _get_short_list(result)
    result = [_get_short_string(v) for v in result]
    return result


def _get_short_string(string, max_length=35) -> str:
    return string[:max_length].strip() + "..." if len(string) > max_length else string


def _get_short_list(lst: list, max_length=3) -> list:
    return lst[:max_length] + ["..."] if len(lst) > max_length else lst


def _get_first_descendant(value: JSONValue) -> Any:
    if isinstance(value, dict) and value:
        first, *_ = value.values()
        return _get_first_descendant(first)
    elif isinstance(value, list) and value:
        if isinstance(value[0], str):
            return [v for v in value if isinstance(v, str)]
        return _get_first_descendant(value[0])
    else:
        return value


@lru_cache()
def func_info(code: types.CodeType) -> dict:
    return dict(
        doc=get_docstring_from_code(code),
        source=getsource(code),
    )
