import json

from abc import ABCMeta
from asyncio import create_task
from collections.abc import Callable
from contextvars import ContextVar
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

import ulid

from structlog import get_logger

from ice.settings import OUGHT_ICE_DIR

log = get_logger()


def make_id() -> str:
    return ulid.new().str


trace_id = make_id()
parent_id_var: ContextVar[str] = ContextVar("id", default=trace_id)


trace_dir = OUGHT_ICE_DIR / "traces"
trace_dir.mkdir(parents=True, exist_ok=True)
trace_file: IO[str] | None = None


def _url_prefix():
    # TODO use OUGHT_ICE_HOST/PORT
    return "http://localhost:8935"


def enable_trace():
    global trace_file

    trace_file = (trace_dir / f"{trace_id}.jsonl").open("a")

    print(f"Trace: {_url_prefix()}/traces/{trace_id}")


def trace_enabled():
    return trace_file is not None


def emit(value):
    if trace_file:
        json.dump(value, trace_file, cls=JSONEncoder)
        print(file=trace_file, flush=True)


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

    def iterencode(self, o):
        try:
            return super().iterencode(o)
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

            emit(
                {
                    id: dict(
                        parent=parent_id,
                        start=monotonic_ns(),
                        name=fn.__name__,
                        doc=getdoc(fn),
                        args=arg_dict,
                        source=getsource(fn),
                    ),
                    f"{parent_id}.children.{id}": True,
                }
            )

            if recorder_name:
                kwargs[recorder_name] = lambda **kwargs: emit(
                    {f"{id}.records.{make_id()}": kwargs}
                )

            result = await fn(*args, **kwargs)
            emit({f"{id}.result": result, f"{id}.end": monotonic_ns()})
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
