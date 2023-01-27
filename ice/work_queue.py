import asyncio
import logging
import uuid

from collections.abc import Callable
from collections.abc import Coroutine
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import TypeVar


@dataclass
class TaskResult:
    value: Any
    should_raise: bool


class WorkQueue:
    """An unbounded queue of async tasks. Has a maximum concurrency level."""

    def __init__(self, max_concurrency: int):
        self._max_concurrency = max_concurrency
        self._workers: Dict[uuid.UUID, asyncio.Task] = {}
        self._results: Dict[uuid.UUID, TaskResult] = {}
        self._is_running = False

    def _generate_new_task_uuid(self) -> uuid.UUID:
        u = uuid.uuid4()
        while u in self._results:
            u = uuid.uuid4()
        return u

    T = TypeVar("T")

    async def do(self, f: Callable[[T], Coroutine[Any, Any, Any]], arg: T):
        """returns when the task is done"""
        if not self._is_running:
            self.start()
        u = self._generate_new_task_uuid()
        cv = asyncio.Condition()
        await self._queue.put((u, cv, f, arg))
        async with cv:
            await cv.wait()
        result = self._results[u]
        del self._results[u]
        if result.should_raise:
            raise result.value
        return result.value

    def _spawn_worker(self):
        t = asyncio.create_task(self._work())
        u = uuid.uuid4()
        t.set_name(u)

        def callback(x):
            logging.error(f"worker died: {x}. restarting this worker")
            del self._workers[u]
            self._spawn_worker()

        t.add_done_callback(callback)
        # TODO assert new uuid
        self._workers[u] = t

    def start(self):
        if self._is_running:
            raise RuntimeError("already running")
        # TODO should maybe declare this as a class variable
        self._queue: asyncio.Queue = asyncio.Queue()

        for _ in range(self._max_concurrency):
            self._spawn_worker()

            # TODO add some error handling in a legit way

            # TODO i didn't see any way to do what i want to do with anyio... in particular, spawning tasks and just letting them work

        self._is_running = True

    async def stop(self):
        for key in self._workers:
            self._workers[key].cancel()
        self._workers = {}
        self._is_running = False

    async def _work(self):
        while True:
            uuid, cv, f, arg = await self._queue.get()
            try:
                task = f(arg)
                logging.debug(f"about to await with {arg}")
                x = await task
                self._results[uuid] = TaskResult(value=x, should_raise=False)
                logging.debug(f"got result for {arg}")
            except Exception as e:
                tr = TaskResult(value=e, should_raise=True)
                self._results[uuid] = tr
            finally:
                async with cv:
                    cv.notify_all()
