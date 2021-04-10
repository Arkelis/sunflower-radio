class classproperty:
    """Create a class-accessible property.
    
    If a `Klass` class implements a classproperty named `kprop`,
    following calls are valid:

    >>> Klass.kprop
    >>> Klass().kprop

    Note that it is up to you to make the function to work on
    both class an instances. Simply make sure that you use only
    class attributes.
    """
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, obj, owner):
        return self.fget(owner)
