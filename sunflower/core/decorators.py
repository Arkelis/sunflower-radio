class cached_property:
    def __init__(self, fget):
        self.__doc__ = fget.__doc__
        self.fget = fget

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.fget.__name__] = self.fget(obj)
        return value
