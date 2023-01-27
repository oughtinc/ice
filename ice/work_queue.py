import asyncio
import logging
import uuid

from collections.abc import Callable
from collections.abc import Coroutine
from typing import Any
from typing import Dict
from typing import TypeVar


class WorkQueue:
    """An unbounded queue of async tasks. Has a maximum concurrency level."""

    def __init__(self, max_concurrency: int):
        # TODO dunder these?
        self.max_concurrency = max_concurrency
        self.workers: Dict[uuid.UUID, asyncio.Task] = {}
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

    def _spawn_worker(self):
        t = asyncio.create_task(self._work())
        u = uuid.uuid4()
        t.set_name(u)

        def callback(x):
            logging.error(f"worker died: {x}. restarting this worker")
            del self.workers[u]
            self._spawn_worker()

        t.add_done_callback(callback)
        # TODO assert new uuid
        self.workers[u] = t

    def start(self):
        if self.is_running:
            raise RuntimeError("already running")
        self.queue: asyncio.Queue = asyncio.Queue()

        for _ in range(self.max_concurrency):
            self._spawn_worker()

            # TODO add some error handling in a legit way

            # TODO i didn't see any way to do what i want to do with anyio... in particular, spawning tasks and just letting them work

        self.is_running = True

    async def stop(self):
        # TODO is this really 'force stop'?
        for key in self.workers:
            self.workers[key].cancel()
        self.workers = {}
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
