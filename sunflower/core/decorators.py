import asyncio
import functools

class classproperty(property):
    """Create a class-accessible property.
    
    If a `Klass` class implements a classproperty named `kprop`,
    following calls are valid:

    >>> Klass.kprop
    >>> Klass().kprop

    Note that it is up to you to make the function to work on
    both class an instances. Simply make sure that you use only
    class attributes.
    """
    def __get__(self, obj, owner):
        return self.fget(owner)


def async_to_sync(func):
    """Make func synchrone.

    Available syntaxes

    @async_to_sync
    async def f(*args, **kwargs):
        ...

    result = async_to_sync(f)(*args, **kwargs)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if asyncio.iscoroutine(result):
            try:
                event_loop = asyncio.get_event_loop()
                result = event_loop.run_until_complete(result)
            except RuntimeError:
                result = asyncio.run(result)
            finally:
                return result
    return wrapper
