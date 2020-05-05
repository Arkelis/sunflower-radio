class cached_property:
    def __init__(self, fget):
        self.__doc__ = fget.__doc__
        self.fget = fget

    def __get__(self, obj, owner):
        if obj is None:
            return self
        value = obj.__dict__[self.fget.__name__] = self.fget(obj)
        return value


class classproperty(property):
    """Create a class-accessible property.
    
    If a`Klass` class implements a classproperty named `kprop`,
    following calls are valid:

    >>> Klass.kprop
    >>> Klass().kprop

    Note that it is up to you to make the function to work on
    both class an instances. Simply make sure that you use only
    class attributes.
    """
    def __get__(self, obj, owner):
        return self.fget(owner)
