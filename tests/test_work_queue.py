import asyncio
import logging

from collections.abc import Coroutine
from typing import Any

import pytest

from ice.work_queue import WorkQueue

logging.basicConfig(level=logging.DEBUG)

MAX_CONCURRENCY = 2

n_current_accessing = 0


async def task(time_to_sleep: float):
    global n_current_accessing
    n_current_accessing += 1
    assert n_current_accessing <= MAX_CONCURRENCY
    # TODO also add another test that asserts that we raise an error if we try to access more than MAX_CONCURRENCY
    result = await asyncio.sleep(time_to_sleep, result=time_to_sleep)
    n_current_accessing -= 1
    return result


def f(time_to_sleep: float) -> Coroutine[Any, Any, Any]:
    return task(time_to_sleep)


queue = WorkQueue(max_concurrency=MAX_CONCURRENCY)


async def run():
    enqueued = []
    # no need to sleep too long; 0.1 is a scaling factor
    # we have to convert to a list because we need to iterate over it twice
    times = list(map(lambda x: 0.1 * x, range(MAX_CONCURRENCY * 2, 0, -1)))
    for time_to_sleep in times:
        enqueued += [queue.do(f, time_to_sleep)]
    results = []
    for x in asyncio.as_completed(enqueued):
        results += [await x]
    logging.debug(f"results: {results}")
    logging.debug(f"times: {times}")
    assert set(results) == set(times)
    print(
        f"are workers cancelled? {[w.cancelled() for _, w in queue._workers.items()]}"
    )


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def wq(anyio_backend):
    wq = WorkQueue(max_concurrency=MAX_CONCURRENCY)
    yield wq
    await wq.stop()


@pytest.mark.anyio
async def test_a(wq):
    # TODO shrug we have to do this dance for mypy- probably can fix it
    before = wq._is_running
    wq.start()
    after = wq._is_running
    assert [before, after] == [False, True]
    workers_not_cancelled = [not w.cancelled() for _, w in wq._workers.items()]
    assert workers_not_cancelled
    # TODO what about restarting the workers when they are cancelled?


@pytest.mark.anyio
async def test_b(wq):
    before = wq._is_running
    after = wq._is_running
    assert [before, after] == [True, True]
    workers_not_cancelled = [not w.cancelled() for _, w in wq._workers.items()]
    assert workers_not_cancelled
    assert 5 == await wq.do(f=lambda x: asyncio.sleep(0, x), arg=5)


@pytest.mark.anyio
async def test_can_handle_work_after_exceptions(wq):
    async def f(should_raise):
        if should_raise:
            raise Exception("oops")
        else:
            return 5

    for _ in range(MAX_CONCURRENCY * 10):
        assert 5 == await wq.do(f=f, arg=False)
    try:
        await wq.do(f=f, arg=True)
        assert False, "should have raised an exception"
    except Exception:
        pass

    for _, w in wq._workers.items():
        assert not w.cancelled()
    assert 5 == await wq.do(f=f, arg=False)
