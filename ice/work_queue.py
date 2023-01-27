import asyncio
import logging
import uuid

from collections.abc import Callable
from collections.abc import Coroutine
from typing import Any
from typing import Dict
from typing import List
from typing import TypeVar


class WorkQueue:
    """An unbounded queue of async tasks. Has a maximum concurrency level."""

    def __init__(self, max_concurrency: int):
        # TODO dunder these?
        self.max_concurrency = max_concurrency
        self.workers: List[asyncio.Task] = []
        self.results: Dict[uuid.UUID, Any] = {}
        self.is_running = False

    def _generate_new_task_uuid(self) -> uuid.UUID:
        u = uuid.uuid4()
        while u in self.results:
            u = uuid.uuid4()
        return u

    T = TypeVar("T")

    async def do(self, f: Callable[[T], Coroutine[Any, Any, Any]], arg: T):
        """returns when the task is done"""
        if not self.is_running:
            self.start()
        u = self._generate_new_task_uuid()
        cv = asyncio.Condition()
        await self.queue.put((u, cv, f, arg))
        async with cv:
            await cv.wait()
        result = self.results[u]
        del self.results[u]
        if isinstance(
            result, Exception
        ):  # TODO is this the right way to do this? what about a wrapper class? (because their code might *generate* an exception
            # without them intending to raise it)
            raise result
        return result

    def start(self):
        if self.is_running:
            raise RuntimeError("already running")
        # TODO use anyio for this instead of asyncio? :)
        self.queue: asyncio.Queue = asyncio.Queue()
        self.workers = []  # TODO probably ehh
        for _ in range(self.max_concurrency):
            t = asyncio.create_task(self._work())

            def callback(x):
                self.is_running = False

            t.add_done_callback(callback)
            self.workers.append(t)
        self.is_running = True

    async def stop(self):
        # TODO is this really 'force stop'?
        for worker in self.workers:
            worker.cancel()
        self.is_running = False

    async def _work(self):
        while True:
            uuid, cv, f, arg = await self.queue.get()
            try:
                task = f(arg)
                logging.debug(f"about to await with {arg}")
                self.results[uuid] = await task
                logging.debug(f"got result for {arg}")
            except Exception as e:
                self.results[uuid] = e
            finally:
                async with cv:
                    cv.notify_all()
