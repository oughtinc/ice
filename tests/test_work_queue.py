import asyncio
import random

from typing import List


class WorkQueue:
    """An unbounded queue of async tasks. Has a maximum concurrency level."""

    def __init__(self, max_concurrency: int):
        self.max_concurrency = max_concurrency
        self.queue: asyncio.Queue = asyncio.Queue()  # TODO why not use a regular queue?
        self.workers: List[asyncio.Task] = []

    async def do(self, task: asyncio.Task):
        """returns when the task is done"""
        cv = asyncio.Condition()
        await self.queue.put((task, cv))
        async with cv:
            await cv.wait()
        # TODO maybe better error handling here
        return task.result()

    def start(self):
        for _ in range(self.max_concurrency):
            self.workers.append(asyncio.create_task(self._work()))

    async def stop(self):
        # TODO is this really 'force stop'?
        for worker in self.workers:
            worker.cancel()

    async def _work(self):
        while True:
            task, cv = await self.queue.get()
            await task
            async with cv:
                cv.notify_all()


MAX_CONCURRENCY = 2
MAX_TIME_TO_SLEEP = 3
CONSTANT_RESULT = 1


def test_work_queue():
    async def task():
        time_to_sleep = random.random() * MAX_TIME_TO_SLEEP
        print(f"sleeping for {time_to_sleep}")
        await asyncio.sleep(time_to_sleep)
        return CONSTANT_RESULT

    async def run():
        queue = WorkQueue(max_concurrency=MAX_CONCURRENCY)
        queue.start()
        enqueued = []
        for _ in range(MAX_CONCURRENCY * 2):
            t = asyncio.create_task(task())
            enqueued += [queue.do(t)]
        results = []
        for x in asyncio.as_completed(enqueued):
            results += [await x]
            print(f"got result {results[-1]}")
        assert results == [CONSTANT_RESULT] * (MAX_CONCURRENCY * 2)
        await queue.stop()

    asyncio.run(run())


if __name__ == "__main__":
    # TODO take this out? it helped me :)
    # TODO why does collecting (in pytest) take so long? (it doesn't always... not sure what's up)
    test_work_queue()
