import asyncio
import logging
import uuid
from collections.abc import Callable, Coroutine
from typing import Any, Dict, List, TypeVar

import anyio


class WorkQueue:
    """An unbounded queue of async tasks. Has a maximum concurrency level."""

    def __init__(self, max_concurrency: int):
        # TODO dunder these?
        self.max_concurrency = max_concurrency
        self.queue: asyncio.Queue = asyncio.Queue()  # TODO why not use a regular queue?
        self.workers: List[asyncio.Task] = []
        self.results: Dict[uuid.UUID, Any] = {}
        # TODO must we store the asyncio loop?
        self.is_running = False
        # TODo what if we kept the loop around to help w/ gc...
        self.loop = None

    def _generate_new_task_uuid(self) -> uuid.UUID:
        u = uuid.uuid4()
        while u in self.results:
            u = uuid.uuid4()
        return u

    T = TypeVar("T")

    async def do(self, f: Callable[[T], Coroutine[Any, Any, Any]], arg: T):
        """returns when the task is done"""
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

    """
        task_result = self.results[u]  # TODO dunder?
        del self.results[u]
        # TODO maybe better error handling here
        # TODO check for cancelling
        match task_result.exception():
            case None: return task_result.result()
            case e: raise e"""

    def start(self):
        if self.is_running:
            raise RuntimeError("already running")
        self.workers = []  # TODO probably ehh
        for _ in range(self.max_concurrency):
            t = asyncio.create_task(self._work())

            def callback(x):
                import traceback

                traceback.print_stack()
                logging.debug(f"worker done: {x}")

            t.add_done_callback(callback)
            self.workers.append(t)
        self.is_running = True
        self.loop = asyncio.get_running_loop()

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
