import json
import threading

from abc import ABCMeta
from asyncio import create_task
from collections.abc import Callable
from contextvars import ContextVar
from functools import lru_cache
from functools import wraps
from inspect import getdoc
from inspect import getsource
from inspect import isclass
from inspect import iscoroutinefunction
from inspect import isfunction
from inspect import Parameter
from inspect import signature
from time import monotonic_ns
from typing import IO
from typing import Optional

import ulid

from structlog import get_logger

from ice.settings import OUGHT_ICE_DIR

log = get_logger()


def make_id() -> str:
    return ulid.new().str


parent_id_var: ContextVar[str] = ContextVar("id")

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
        self.id = make_id()
        self.dir = traces_dir / self.id
        self.dir.mkdir()
        self.file = self._open("trace")
        self.block_number = -1  # so that it starts at _open_block below
        self._open_block()
        self._lock = threading.Lock()
        print(f"Trace: {_url_prefix()}/traces/{self.id}")
        parent_id_var.set(self.id)

    def _open(self, name: str) -> IO[str]:
        return open(self.dir / f"{name}.jsonl", "a")

    def _open_block(self):
        self.block_number += 1
        self.block_file = self._open(f"block_{self.block_number}")
        self.block_length = 0
        self.block_lineno = 0

    def add_to_block(self, x):
        """
        Write the value x to the current block file as a single JSON line.
        """
        s = json.dumps(x, cls=JSONEncoder) + "\n"
        with self._lock:
            address = [self.block_number, self.block_lineno]
            self.block_file.write(s)
            self.block_length += len(s)
            if self.block_length > self.BLOCK_LENGTH:
                self.block_file.write("end")
                self.block_file.close()
                self._open_block()
            else:
                self.block_file.flush()
                self.block_lineno += 1
        return address


trace_var: ContextVar[Optional[Trace]] = ContextVar("trace", default=None)


def _url_prefix():
    # TODO use OUGHT_ICE_HOST/PORT
    return "http://localhost:8935"


def enable_trace():
    trace_var.set(Trace())


def trace_enabled():
    return trace_var.get() is not None


def emit(value):
    if trc := trace_var.get():
        json.dump(value, trc.file, cls=JSONEncoder)
        print(file=trc.file, flush=True)


def emit_block(x):
    if trc := trace_var.get():
        return trc.add_to_block(x)
    else:
        return 0, 0


def compress(o: object):
    if isinstance(o, dict):
        if {"paragraphs", "document_id"} <= set(o):
            return {"document_id": o["document_id"]}
        return {k: compress(v) for k, v in o.items()}
    if isinstance(o, list):
        return [compress(v) for v in o]
    return o


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, dict):
            return {repr(k): v for k, v in o.items()}
        if hasattr(o, "dict") and callable(o.dict):
            return compress(o.dict())
        if isfunction(o):
            return dict(class_name=o.__class__.__name__, name=o.__name__)
        try:
            return json.JSONEncoder.default(self, o)
        except TypeError:
            return repr(o)

    def iterencode(self, o, **kwargs):
        try:
            return super().iterencode(o, **kwargs)
        except TypeError:
            return self.default(o)


# To add records to the trace, use the following code:
#
# async def f(self, arg1, arg2, record = recorder):
#     record(k1=v1, k2=v2)
#
# You can name 'record' anything and pass it any JSON-serializable keyword arguments.
#
# You MUST set its default value to 'recorder'. This allows @trace to know where to
# inject the recorder, and it ensures that your function will work even if tracing is
# disabled.


Recorder = Callable[..., None]

recorder: Recorder = lambda **kwargs: None


def trace(fn):
    if isclass(fn):
        for key, value in fn.__dict__.items():
            if isfunction(value):
                setattr(fn, key, trace(value))
        return fn

    if not iscoroutinefunction(fn):
        return fn

    @wraps(fn)
    async def wrapper(*args, **kwargs):
        if not trace_enabled():
            return await fn(*args, **kwargs)

        @wraps(fn)
        async def inner_wrapper(*args, **kwargs):
            id = make_id()
            parent_id = parent_id_var.get()
            parent_id_var.set(id)

            sig = signature(fn)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            arg_dict = {}
            recorder_name = None
            for k, v in bound_args.arguments.items():
                p = sig.parameters[k]
                if p.default is recorder:
                    recorder_name = k
                if p.kind == Parameter.VAR_KEYWORD:
                    arg_dict.update(v)
                else:
                    arg_dict[k] = v

            call_event = dict(
                parent=parent_id,
                start=monotonic_ns(),
                name=fn.__name__,
                arg=get_strings(arg_dict),
                func=emit_block(func_info(fn)),
                args=emit_block(arg_dict),
            )
            self = arg_dict.get("self")
            if self:
                call_event["cls"] = self.__class__.__name__

            emit(
                {
                    id: call_event,
                    f"{parent_id}.children.{id}": True,
                }
            )

            if recorder_name:
                kwargs[recorder_name] = lambda **kwargs: emit(
                    {f"{id}.records.{make_id()}": emit_block(kwargs)}
                )

            result = await fn(*args, **kwargs)
            emit(
                {
                    f"{id}.result": emit_block(result),
                    f"{id}.shortResult": get_strings(result),
                    f"{id}.end": monotonic_ns(),
                }
            )
            return result

        return await create_task(inner_wrapper(*args, **kwargs))

    return wrapper


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
        return super().__new__(
            mcls,
            name,
            bases,
            {k: trace(v) for k, v in namespace.items()}
            | dict(dict=to_json_serializable),
        )


class TracedABC(metaclass=TracedABCMeta):
    ...


def get_first_descendant(value):
    if value:
        if isinstance(value, dict):
            first, *_ = value.values()
            return get_first_descendant(first)
        if isinstance(value, (list, tuple)):
            if isinstance(value[0], str):
                return [v for v in value if isinstance(v, str)]
            return get_first_descendant(value[0])
    return value


def get_strings(value) -> list[str]:
    """
    Represent the given value as a short list of short strings
    that can be stored directly in the central trace file and loaded eagerly in the UI.
    """
    if isinstance(value, dict):
        if "value" in value:
            value = value["value"]
        else:
            value = {k: v for k, v in value.items() if k not in ("self", "record")}

    result = get_first_descendant(value)

    if isinstance(result, tuple):
        result = list(result)
    if not (result and isinstance(result, list)):
        result = [f"{result or '()'}"]

    result = get_short_list(result)
    result = [get_short_string(v) for v in result]
    return result


def get_short_string(string, max_length=35) -> str:
    return string[:max_length].strip() + "..." if len(string) > max_length else string


def get_short_list(lst: list, max_length=3) -> list:
    return lst[:max_length] + ["..."] if len(lst) > max_length else lst


@lru_cache()
def func_info(fn):
    return dict(
        doc=getdoc(fn),
        source=getsource(fn),
    )
