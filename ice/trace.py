import hashlib
import json
import threading
from abc import ABCMeta
from asyncio import create_task
from collections.abc import Callable
from contextvars import ContextVar
from functools import lru_cache
from functools import partial
from functools import wraps
from inspect import getdoc
from inspect import getsource
from inspect import isclass
from inspect import iscoroutinefunction
from inspect import isfunction
from inspect import Parameter
from inspect import signature
from time import monotonic_ns
from typing import Any
from typing import cast
from typing import IO
from typing import Optional
from typing import Union

from structlog import get_logger

from .logging import log_lock
from ice.json_value import JSONValue
from ice.json_value import to_json_value
from ice.server import ensure_server_running
from ice.server import is_server_running
from ice.settings import OUGHT_ICE_DIR
from ice.settings import server_url
from ice.settings import settings
from ice.utils import make_id

log = get_logger()


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

        parent_id_var.set(self.id)
        log.info(f"Trace: {self.url}")
        threading.Thread(target=self._server_and_browser).start()

    @property
    def url(self) -> str:
        return f"{server_url()}/traces/{self.id}"

    def _server_and_browser(self):
        # We use this lock to prevent logging from here (which runs in a
        # background thread) from burying the input prompt in
        # [Settings.__get_and_store].
        with log_lock:
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

            log.info(
                "Opening trace in browser, set OUGHT_ICE_AUTO_BROWSER=0 to disable."
            )
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


Scalar = Union[bool, int, float, str, None]


def add_fields(**fields: Scalar):
    if trace_enabled():
        id = parent_id_var.get()
        emit({f"{id}.fields.{key}": value for key, value in fields.items()})


def _encode_json(x) -> str:
    # Note that sort_keys=True here could improve caching,
    # but it might make the output less readable.
    return json.dumps(to_json_value(x), separators=(",", ":")) + "\n"


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


class _Recorder:
    def __init__(self, id: str):
        self.id = id

    def __call__(self, **kwargs):
        emit({f"{self.id}.records.{make_id()}": emit_block(kwargs)})

    def __repr__(self):
        # So this can be used in `diskcache()` functions
        # The diskcache implementation should probably not
        # depend on calling __repr__ but that
        # seems like a larger refactor
        return "ice.trace._Recorder"


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

            arg_dict_json = to_json_value(arg_dict)
            call_event = dict(
                parent=parent_id,
                start=monotonic_ns(),
                name=fn.__name__ if hasattr(fn, "__name__") else repr(fn),
                shortArgs=get_strings(arg_dict_json),
                func=emit_block(func_info(fn)),
                args=emit_block(arg_dict_json),
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
                kwargs[recorder_name] = _Recorder(id)

            result = await fn(*args, **kwargs)
            result_json = to_json_value(result)
            emit(
                {
                    f"{id}.result": emit_block(result_json),
                    f"{id}.shortResult": get_strings(result_json),
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
def func_info(fn):
    return dict(
        doc=getdoc(fn),
        source=getsource(fn.func) if isinstance(fn, partial) else getsource(fn),
    )
