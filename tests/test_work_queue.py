import asyncio


class WorkQueue:
    """An unbounded queue of async tasks. Has a maximum concurrency level."""

    def __init__(self, max_concurrency: int):
        self.max_concurrency = max_concurrency
        self.queue: asyncio.Queue = asyncio.Queue()  # TODO why not use a regular queue?

    async def put(self, task: asyncio.Task):
        """returns when the task is done"""
        cv = asyncio.Condition()
        await self.queue.put((task, cv))
        async with cv:
            await cv.wait()
        # TODO maybe better error handling here
        return task.result()

    def start(self):
        for _ in range(self.max_concurrency):
            asyncio.create_task(self._work())

    async def _work(self):
        while True:
            task, cv = await self.queue.get()
            await asyncio.create_task(self.run_task(task))
            async with cv:
                cv.notify_all()

    async def run_task(self, task: asyncio.Task):
        print("running")
        await task
        print("done with task")


def test_work_queue():
    async def task():
        await asyncio.sleep(0.1)
        return 1

    async def run():
        queue = WorkQueue(max_concurrency=2)
        queue.start()
        enqueued = []
        for _ in range(3):
            print("putting")
            # TODO make these tasks run in parallel
            t = asyncio.create_task(task())
            enqueued += [queue.put(t)]  # it's not really "put", it's "run"
        all = await asyncio.gather(*enqueued)
        print(all)
        assert all == [1, 1, 1]

    asyncio.run(run())


if __name__ == "__main__":
    test_work_queue()
