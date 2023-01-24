import asyncio
import logging

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
        await queue.stop()

    asyncio.run(run())


if __name__ == "__main__":
    # TODO take this out? it helped me :)
    # TODO why does collecting (in pytest) take so long? (it doesn't always... not sure what's up)
    test_work_queue()

# TODO also add a test that lambdas that raise exceptions are handled properly (which is to say,
# we can still handle more work... i think we can test this by raising more exceptions than we have
# workers, and then checking that we can still handle more work)
