import asyncio
import logging
import uuid

from collections.abc import Callable
from typing import Any
from typing import Dict
from typing import List
from typing import TypeVar

logging.basicConfig(level=logging.DEBUG)


class WorkQueue:
    """An unbounded queue of async tasks. Has a maximum concurrency level."""

    def __init__(self, max_concurrency: int):
        self.max_concurrency = max_concurrency
        self.queue: asyncio.Queue = asyncio.Queue()  # TODO why not use a regular queue?
        self.workers: List[asyncio.Task] = []
        self.results: Dict[uuid.UUID, Any] = {}
        self.loop = asyncio.get_event_loop()

    T = TypeVar("T")

    async def do(self, f: Callable[[T], asyncio.Task], arg: T):
        """returns when the task is done"""
        import uuid

        u = uuid.uuid4()  # TODO assert u not in self.results
        cv = asyncio.Condition()
        await self.queue.put((u, cv, f, arg))
        async with cv:
            await cv.wait()
        result = self.results[u]
        del self.results[u]
        if isinstance(result, Exception):
            raise result
        return result

    """
        task_result = self.results[u]  # TODO dunder?
        del self.results[u]
        # TODO maybe better error handling here
        # TODO check for cancelling
        match task_result.exception():
            case None: return task_result.result()
            case e: raise e"""

    def start(self):
        for _ in range(self.max_concurrency):
            self.workers.append(self.loop.create_task(self._work()))

    async def stop(self):
        # TODO is this really 'force stop'?
        for worker in self.workers:
            worker.cancel()

    async def _work(self):
        while True:
            uuid, cv, f, arg = await self.queue.get()
            try:
                task = f(arg)
                logging.debug(f"about to await with {arg}")
                await task
                logging.debug(f"got result for {arg}")
                self.results[uuid] = task
            except Exception as e:
                self.results[uuid] = e
            finally:
                async with cv:
                    cv.notify_all()


MAX_CONCURRENCY = 2
MAX_TIME_TO_SLEEP = 1

n_current_accessing = 0


async def task(time_to_sleep: float):
    global n_current_accessing
    n_current_accessing += 1
    assert n_current_accessing <= MAX_CONCURRENCY - 1  # TODO properly handle errors
    # TODO also add another test that asserts that we raise an error if we try to access more than MAX_CONCURRENCY
    result = await asyncio.sleep(time_to_sleep, result=time_to_sleep)
    n_current_accessing -= 1
    return result
    # return await asyncio.sleep(time_to_sleep, result=time_to_sleep)


def f(time_to_sleep: float) -> asyncio.Task:
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(lambda loop, context: print(context))
    t = loop.create_task(task(time_to_sleep))
    t.set_name(f"task {time_to_sleep}")
    return t


def test_work_queue():
    async def run():
        queue = WorkQueue(max_concurrency=MAX_CONCURRENCY)
        queue.start()
        enqueued = []
        times = range(MAX_CONCURRENCY * 2, 0, -1)
        for time_to_sleep in times:
            enqueued += [queue.do(f, time_to_sleep)]
        results = []
        for x in asyncio.as_completed(enqueued):
            results += [await x]
        assert set(results) == set(times)
        await queue.stop()

    asyncio.run(run())


if __name__ == "__main__":
    # TODO take this out? it helped me :)
    # TODO why does collecting (in pytest) take so long? (it doesn't always... not sure what's up)
    test_work_queue()
