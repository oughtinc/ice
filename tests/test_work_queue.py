import asyncio
import logging

from collections.abc import Coroutine
from typing import Any

import pytest

from ice.utils import wq
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


# TODO the error is that the worker coroutines are cancelled


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
    print(f"are workers cancelled? {[w.cancelled() for w in queue.workers]}")


def test_work_queue():
    asyncio.run(run())


def test_if_workers_are_now_cancelled():
    # just call the exact same thing
    asyncio.run(run())


@pytest.mark.anyio
async def test_a():
    # TODO shrug we have to do this dance for mypy- probably can fix it
    before = wq.is_running
    wq.start()
    after = wq.is_running
    assert [before, after] == [False, True]
    workers_not_cancelled = [not w.cancelled() for w in wq.workers]
    assert workers_not_cancelled


@pytest.mark.anyio
async def test_b():
    assert wq.is_running
    workers_cancelled = [
        w.cancelled() for w in wq.workers
    ]  # TODO This is the problematic state!
    assert workers_cancelled


async def main():
    queue.start()
    await run()
    await run()
    await queue.stop()


if __name__ == "__main__":
    # TODO take this out? it helped me :)
    # TODO why does collecting (in pytest) take so long? (it doesn't always... not sure what's up)
    asyncio.run(main())
    # await queue.stop() # TODO where to put this

# TODO also add a test that lambdas that raise exceptions are handled properly (which is to say,
# we can still handle more work... i think we can test this by raising more exceptions than we have
# workers, and then checking that we can still handle more work)
