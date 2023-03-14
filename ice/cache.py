"""
Decorator for caching function results to disk
"""
import asyncio
import functools
import inspect
from pathlib import Path

from ice.settings import CACHE_DIR
from ice.sqlite_shelf import SQLiteShelf


def diskcache(cache_dir: Path = CACHE_DIR):
    def get_cache(func):
        cache_file = (cache_dir / func.__name__).as_posix() + ".sqlite"
        return SQLiteShelf(cache_file, "diskcache")

    def get_cache_key(func, *args, **kwargs):
        return repr(inspect.getcallargs(func, *args, **kwargs))

    def decorator(func):
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            key = get_cache_key(func, *args, **kwargs)
            cache = get_cache(func)
            if key in cache:
                return cache[key]
            result = func(*args, **kwargs)
            cache[key] = result
            return result

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            key = get_cache_key(func, *args, **kwargs)
            cache = get_cache(func)
            if key in cache:
                return cache[key]
            cache.close()
            # close connection while waiting for async function so we don't have a bunch of connections open simultaneously

            result = await func(*args, **kwargs)

            cache = get_cache(func)
            cache[key] = result
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper

        return sync_wrapper

    return decorator
