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
    def get_cache_and_key(func, *args, **kwargs):
        cache_file = (cache_dir / func.__name__).as_posix() + ".sqlite"
        key = repr(inspect.getcallargs(func, *args, **kwargs))
        cache = SQLiteShelf(cache_file, "diskcache")
        return cache, key

    def decorator(func):
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache, key = get_cache_and_key(func, *args, **kwargs)
            if key in cache:
                return cache[key]
            result = func(*args, **kwargs)
            cache[key] = result
            return result

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache, key = get_cache_and_key(func, *args, **kwargs)
            if key in cache:
                return cache[key]
            result = await func(*args, **kwargs)
            cache[key] = result
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper

        return sync_wrapper

    return decorator
