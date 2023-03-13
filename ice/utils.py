import itertools
import os
import subprocess
import threading as td
import time
from collections import defaultdict
from collections.abc import Awaitable
from collections.abc import Callable
from collections.abc import Coroutine
from collections.abc import Iterable
from collections.abc import Sequence
from enum import Enum
from functools import cache
from random import Random
from typing import Any
from typing import Generic
from typing import Optional
from typing import TypeVar
from typing import Union

import anyio
import tqdm
import ulid
from more_itertools import windowed
from structlog.stdlib import get_logger
from transformers import GPT2TokenizerFast

log = get_logger()


def make_id() -> str:
    """Return a lexicographically sortable unique ID."""
    if hasattr(ulid, "new"):
        # Use the ulid-py version if python-ulid has been clobbered.
        return ulid.new().str
    # Otherwise use the python-ulid version.
    return str(ulid.ULID())


def _merge(recurse, path: list, base: dict, nxt: dict) -> dict:
    for k, v in nxt.items():
        if k not in base:
            base[k] = v
        else:
            base[k] = recurse(recurse, path + [k], base[k], v)
    return base


def deep_merge(base, nxt):
    """
    Performs a *limited* deep merge of nxt into base.
    Type differences are overriden by nxt.
    Lists are extended, but elements are not changed or recursed into.
    Sets are unioned but not recursed into.
    """

    def merge_strategy(
        merge_strategy,
        path: list,
        base,
        nxt,
    ):
        if not (isinstance(base, type(nxt)) or isinstance(nxt, type(base))):
            return nxt
        elif isinstance(nxt, dict):
            return _merge(merge_strategy, path, base, nxt)
        elif isinstance(nxt, list) or isinstance(nxt, tuple):
            return base + nxt
        elif isinstance(nxt, set):
            return base | nxt
        return nxt

    return merge_strategy(merge_strategy, [], base, nxt)


InputType_co = TypeVar("InputType_co", covariant=True)
ReturnType_co = TypeVar("ReturnType_co", covariant=True)


# inspired by http://bluebirdjs.com/docs/api/promise.map.html
async def map_async(
    input_list: Sequence[InputType_co],
    fn: Callable[[InputType_co], Coroutine[Any, Any, ReturnType_co]],
    max_concurrency: Optional[int] = None,
    semaphore: Optional[anyio.Semaphore] = None,
    show_progress_bar: bool = False,
) -> list[ReturnType_co]:
    result_boxes: list[list[ReturnType_co]] = [[] for _ in input_list]

    if not semaphore:
        semaphore = anyio.Semaphore(max_concurrency or len(input_list))

    if show_progress_bar:
        progress_bar = tqdm.tqdm(total=len(input_list))

    async def box_result(
        input: Any, result_box: list[ReturnType_co], semaphore: anyio.Semaphore
    ) -> None:
        async with semaphore:
            result = await fn(input)
        result_box.extend([result])

        if show_progress_bar:
            progress_bar.update(1)

    async with anyio.create_task_group() as tg:
        for i in range(len(input_list)):
            tg.start_soon(box_result, input_list[i], result_boxes[i], semaphore)

    if show_progress_bar:
        progress_bar.close()

    return [result_box[0] for result_box in result_boxes]


async def filter_async(
    iterable: Iterable[InputType_co],
    fn: Callable[[InputType_co], Coroutine[Any, Any, bool]],
    max_concurrency: Optional[int] = None,
    show_progress_bar: bool = False,
) -> list[InputType_co]:
    iterable_list = list(iterable)
    values = await map_async(
        iterable_list,
        fn,
        max_concurrency=max_concurrency,
        show_progress_bar=show_progress_bar,
    )
    return [item for item, value in zip(iterable_list, values) if value]


T = TypeVar("T")
S = TypeVar("S")


async def reduce_async(
    fn: Callable[[T, S], Awaitable[T]], iterable: Iterable[S], initial: T
):
    current = initial
    for item in iterable:
        current = await fn(current, item)
    return current


class _Sentinel(Enum):
    token = 0


_sentinel = _Sentinel.token


def window_dropping(items: Sequence[T], n, step) -> Sequence[Sequence[T]]:
    """Windows over items, shortening n if necessary"""
    return [
        [i for i in window if i is not _sentinel]
        for window in windowed(items, n=n, step=step, fillvalue=_sentinel)
    ]


def longest_common_prefix(xs: Sequence[str]) -> str:
    if not xs:
        return ""
    prefix = xs[0]
    for x in xs[1:]:
        prefix = os.path.commonprefix([prefix, x])
    return prefix


AsyncComparator = Callable[[T, T], Awaitable[int]]


async def _nsmallest_async(
    n: int,
    items: list[T],
    cmp: AsyncComparator,
    semaphore: Optional[anyio.Semaphore],
    offset: int = 0,
    seed: int = 1,
) -> list[T]:
    n = max(0, n)
    if len(items) <= 1 or n == 0:
        return items[:n]

    pivot = items.pop(Random(seed).randrange(len(items)))

    async def get_key(item: T) -> bool:
        return await cmp(item, pivot) >= 0

    # partitions[False] contains items < pivot, partitions[True] contains items >= pivot
    partitions = defaultdict(list)
    keys = await map_async(items, get_key, semaphore=semaphore)
    for item, key in zip(items, keys):
        partitions[key].append(item)

    async def recurse(key: bool) -> tuple[bool, list[T]]:
        delta = len(partitions[False]) + 1 if key else 0
        # Represent the path to this node in the call tree as a binary number, and use
        # that as the seed.
        new_seed = 2 * seed + int(key)
        return key, await _nsmallest_async(
            n - delta, partitions[key], cmp, semaphore, offset + delta, new_seed
        )

    partitions = defaultdict(list, await map_async(list(partitions), recurse))
    return (partitions[False] + [pivot] + partitions[True])[:n]


async def nsmallest_async(
    n: int,
    items: Iterable[T],
    cmp: AsyncComparator,
    max_concurrency: Optional[int] = None,
) -> list[T]:
    semaphore = anyio.Semaphore(max_concurrency) if max_concurrency else None
    return await _nsmallest_async(n, list(items), cmp, semaphore)


def flatten(xs: Iterable[Iterable[T]]) -> list[T]:
    return list(itertools.chain(*xs))


def chunk_by(xs: list[T], n: int, f: Callable[[T], float]) -> list[list[T]]:
    """
    Split a list into chunks of size n, with the size of each element of l computed by f.
    """
    chunks = []
    current_chunk: list[T] = []
    current_chunk_size: float = 0.0
    for x in xs:
        x_size = f(x)
        if current_chunk_size + x_size > n:
            chunks.append(current_chunk)
            current_chunk = []
            current_chunk_size = 0.0
        current_chunk.append(x)
        current_chunk_size += x_size
    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def quoted(multiline_string: str) -> str:
    return "\n".join(f"> {line}" for line in multiline_string.split("\n"))


ArgT = TypeVar("ArgT")
ReturnT_co = TypeVar("ReturnT_co", covariant=True)


class DynamicBatcher(Generic[ArgT, ReturnT_co]):
    # Shamelessly adapted/simplified/typed based on:
    # https://github.com/cortexlabs/nucleus/blob/master/src/cortex/cortex_internal/lib/api/utils.py
    # Apache 2.0 license
    # Copyright 2022 Cortex Labs, Inc.
    # Thanks, Cortex!
    def __init__(
        self,
        handler: Callable[[list[ArgT]], list[ReturnT_co]],
        max_batch_size: int,
        batch_interval_seconds: int,
        test_mode: bool = False,
    ):
        self.handler = handler

        self.batch_max_size = max_batch_size
        self.batch_interval_seconds = batch_interval_seconds  # measured in seconds
        self.test_mode = test_mode  # only for unit testing
        self._test_batch_lengths: list[int] = []  # only when unit testing

        self.barrier = td.Barrier(self.batch_max_size + 1)

        self.samples: dict[int, ArgT] = {}
        self.results: dict[int, Union[Exception, ReturnT_co]] = {}
        td.Thread(target=self._batch_engine, daemon=True).start()

        self.sample_id_generator = itertools.count()

    def _batch_engine(self):
        while True:
            if len(self.results) > 0:
                time.sleep(0.001)
                continue

            try:
                self.barrier.wait(self.batch_interval_seconds)
            except td.BrokenBarrierError:
                pass

            self.results = {}
            sample_ids = self._get_sample_ids(self.batch_max_size)
            try:
                if self.samples:
                    batch = self._make_batch(sample_ids)

                    results = self.handler(batch)
                    if not isinstance(results, list):
                        raise RuntimeError(
                            f"please return a list when using server side batching, got {type(results)}"
                        )

                    if self.test_mode:
                        self._test_batch_lengths.append(len(results))

                    self.results = dict(zip(sample_ids, results))
            except Exception as e:
                self.results = {sample_id: e for sample_id in sample_ids}
                log.exception("Unhandled exception in server-side batching")
            finally:
                for sample_id in sample_ids:
                    del self.samples[sample_id]
                self.barrier.reset()

    def _get_sample_ids(self, max_number: int) -> list[int]:
        if len(self.samples) <= max_number:
            return list(self.samples.keys())
        return sorted(self.samples)[:max_number]

    def _make_batch(self, sample_ids: list[int]) -> list[ArgT]:
        batched_samples: list[ArgT] = []
        for sample_id in sample_ids:
            batched_samples.append(self.samples[sample_id])

        return batched_samples

    def _enqueue_request(self, sample_id: int, kwargs: ArgT):
        """
        Enqueue sample for batch processing. This is a blocking method.
        """

        self.samples[sample_id] = kwargs
        try:
            self.barrier.wait()
        except td.BrokenBarrierError:
            pass

    def process(self, arg: ArgT) -> ReturnT_co:
        """
        Queues a request to be batched with other incoming request, waits for the response
        and returns the processed result. This is a blocking method.
        """
        sample_id = next(self.sample_id_generator)
        self._enqueue_request(sample_id, arg)
        result = self._get_result(sample_id)
        return result

    def _get_result(self, sample_id: int) -> ReturnT_co:
        """
        Return the processed result. This is a blocking method.
        """
        while sample_id not in self.results:
            time.sleep(0.001)

        result = self.results[sample_id]
        del self.results[sample_id]

        if isinstance(result, Exception):
            raise result
        else:
            return result


def truncate_by_tokens(text: str, *, max_tokens: int = 7500):
    # Full context is 8000 tokens * ~3.5 chars/token
    chars = len(text)
    max_chars = int(max_tokens * 3.5)
    if chars > max_chars:
        log.warning(
            f"Truncating from {chars} to {max_chars} characters",
        )
        text = text[:max_chars]
    return text


def window_by_tokens(text: str, *, max_tokens: int = 7000):
    chars = len(text)
    max_chars = int(max_tokens * 3.5)
    for i in range(0, chars, max_chars):
        yield text[i : i + max_chars]


K = TypeVar("K")  # key type

V = TypeVar("V")  # value type


def max_by_value(
    d: dict[K, V], *, key: Callable[[V], Any] = lambda x: x
) -> tuple[K, V]:
    return max(d.items(), key=lambda x: key(x[1]))


@cache
def make_gpt2_tokenizer() -> GPT2TokenizerFast:
    return GPT2TokenizerFast.from_pretrained("gpt2")


def n_tokens(text: str) -> int:
    return len(make_gpt2_tokenizer().tokenize(text))


def latest_commit_hash():
    return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
