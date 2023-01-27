import asyncio
import logging

import pytest

from ice.work_queue import WorkQueue

logging.basicConfig(level=logging.DEBUG)

MAX_CONCURRENCY = 5
TIME_TO_SLEEP = 0.01


class FakeResource:
    def __init__(self, limit: int):
        self._n_current_accessing = 0
        self.limit = limit

    async def access(self):
        self._n_current_accessing += 1
        assert self._n_current_accessing <= self.limit
        result = await asyncio.sleep(TIME_TO_SLEEP, result=TIME_TO_SLEEP)
        self._n_current_accessing -= 1
        return result


@pytest.mark.anyio
async def test_that_work_queue_prevents_overaccess():
    wq = WorkQueue(max_concurrency=MAX_CONCURRENCY)
    wq.start()
    fake_resource = FakeResource(limit=MAX_CONCURRENCY)
    n_tasks = 10 * MAX_CONCURRENCY
    tasks = [wq.do(lambda _: fake_resource.access(), 1) for _ in range(n_tasks)]
    results = await asyncio.gather(*tasks)
    assert results == [TIME_TO_SLEEP] * n_tasks
    await wq.stop()


@pytest.mark.anyio
async def test_that_work_queue_with_too_high_limit_raises():
    wq = WorkQueue(max_concurrency=MAX_CONCURRENCY)
    wq.start()
    fake_resource = FakeResource(limit=MAX_CONCURRENCY - 1)
    n_tasks = 10 * MAX_CONCURRENCY
    try:
        tasks = [wq.do(lambda _: fake_resource.access(), 1) for _ in range(n_tasks)]
        await asyncio.gather(*tasks)
        assert False, "should have raised an exception"
    except Exception:
        pass
    await wq.stop()


@pytest.mark.anyio
async def test_that_tasks_can_return_exceptions_without_raising():
    wq = WorkQueue(max_concurrency=MAX_CONCURRENCY)
    wq.start()
    result = await wq.do(lambda _: asyncio.sleep(0, RuntimeError("oops")), arg=1)
    assert isinstance(result, RuntimeError)
    await wq.stop()


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def wq(anyio_backend):
    wq = WorkQueue(max_concurrency=MAX_CONCURRENCY)
    yield wq
    await wq.stop()


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
