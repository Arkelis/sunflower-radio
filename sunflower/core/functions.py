# This file is part of sunflower package. radio
# This module contains core functions.
import asyncio
from collections import Coroutine

from sunflower.core.descriptors import PersistentAttribute


def check_obj_integrity(obj):
    """Perfom several checks in order to prevent some runtime errors."""
    
    errors = []

    # 1. If obj has PersistentAttribute attributes, check if this object
    #    has the 'data_type' and 'endpoint' attributes.

    for attr in vars(type(obj)).values():
        if not isinstance(attr, PersistentAttribute):
            continue
        if not hasattr(obj, "endpoint"):
            errors.append(f"Missing 'endpoint' attribute in {obj} which contains PersistentAttribute descriptor.")
        if not hasattr(obj, "data_type"):
            errors.append(f"Missing 'data_type' attribute in {obj} which contains PersistentAttribute descriptor.")

    return errors


def run_coroutine_synchronously(coro: Coroutine):
    """Run coroutine syncronously.

    If asyncio.get_event_loop() returns None, use asyncio.run()
    Else use loop.run_until_complete()
    """

    if not asyncio.iscoroutine(coro):
        raise TypeError('"coro" must be a coroutine.')
    try:
        event_loop = asyncio.get_event_loop()
        result = event_loop.run_until_complete(coro)
        return result
    except RuntimeError:
        result = asyncio.run(coro)
        return result
