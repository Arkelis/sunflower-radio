# This file is part of sunflower package. radio
# This module contains core functions.
import asyncio
from concurrent.futures import ThreadPoolExecutor


def run_coroutine_synchronously(coroutine_function, *args, **kwargs):
    """Run coroutine syncronously.

    Try to run asyncio.run. If it fails, run the coroutine in a
    ThreadPoolExecutor.
    """

    if not asyncio.iscoroutinefunction(coroutine_function):
        raise TypeError('"coroutine_function" must be a coroutine_function.')
    try:
        coro = coroutine_function(*args, **kwargs)
        result = asyncio.run(coro)
        return result
    except:
        coro = coroutine_function(*args, **kwargs)
        with ThreadPoolExecutor() as executor:
            result = executor.submit(asyncio.run, coro).result()
            return result
