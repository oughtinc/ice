import asyncio
import uuid

from collections.abc import Callable
from typing import Any
from typing import Dict
from typing import List
from typing import TypeVar


class WorkQueue:
    """An unbounded queue of async tasks. Has a maximum concurrency level."""

    def __init__(self, max_concurrency: int):
        self.max_concurrency = max_concurrency
        self.queue: asyncio.Queue = asyncio.Queue()  # TODO why not use a regular queue?
        self.workers: List[asyncio.Task] = []
        self.results: Dict[uuid.UUID, Any] = {}

    T = TypeVar("T")

    async def do(self, f: Callable[[T], asyncio.Task], arg: T):
        """returns when the task is done"""
        import uuid

        u = uuid.uuid4()  # TODO assert u not in self.results
        cv = asyncio.Condition()
        await self.queue.put((u, cv, f, arg))
        async with cv:
            await cv.wait()
        result = self.results[u]  # TODO dunder?
        del self.results[u]
        # TODO maybe better error handling here
        return result

    def start(self):
        for _ in range(self.max_concurrency):
            self.workers.append(asyncio.create_task(self._work()))

    async def stop(self):
        # TODO is this really 'force stop'?
        for worker in self.workers:
            worker.cancel()

    async def _work(self):
        while True:
            uuid, cv, f, arg = await self.queue.get()
            print(f"invoking f with {arg}")
            task = f(arg)
            result = await task
            self.results[uuid] = result
            async with cv:
                cv.notify_all()


MAX_CONCURRENCY = 2
MAX_TIME_TO_SLEEP = 3
CONSTANT_RESULT = 1


async def task(time_to_sleep: float):
    return await asyncio.sleep(time_to_sleep, result=time_to_sleep)


def f(time_to_sleep: float) -> asyncio.Task:
    t = asyncio.create_task(task(time_to_sleep))
    t.set_name(f"task {time_to_sleep}")
    return t


def test_work_queue():
    async def run():
        queue = WorkQueue(max_concurrency=MAX_CONCURRENCY)
        queue.start()
        enqueued = []
        times = range(10 + MAX_CONCURRENCY * 2, 0, -1)
        for time_to_sleep in times:
            enqueued += [queue.do(f, time_to_sleep)]
        results = []
        for x in asyncio.as_completed(enqueued):
            results += [await x]
            print(f"got result {results[-1]}")
        assert set(results) == set(times)
        await queue.stop()

    asyncio.run(run())


if __name__ == "__main__":
    # TODO take this out? it helped me :)
    # TODO why does collecting (in pytest) take so long? (it doesn't always... not sure what's up)
    test_work_queue()
