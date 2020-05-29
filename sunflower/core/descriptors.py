from sunflower.core.mixins import RedisMixin
from json import JSONEncoder
from typing import Type, Callable


class PersistentAttribute(RedisMixin):
    """Descriptor for attributes stored in external persistence system.

    For the moment, only Redis persistent attributes are implemented.

    Owner class or object must have two mandatory attributes:

    - `data_type`: the type of the object to which data belongs to (for example station or channel)
    - `endpoint`: a string identifying the object (for Channel objects it is also the endpoint for webapp)

    Hooks can be added for customizing persistence and retrievals:

    - `pre_set_hook_func()` is called before storing data in Redis database (see `__set__()` method).
    - `post_get_hook_func()` is called after retrieving data from Redis database (see `__get__()` method).

    These can be added through the constructor or with decorators. For example:

    ```
    persistent_attribute = PersistentAttribute(...)

    @persistent_attribute.pre_set_hook
    def persistent_attribute(self, value):
        # format data to be stored in Redis database
        return data
    
    @persistent_attribute.post_get_hook
    def persistent_attribute(self, data):
        # decode data
        return value
    ```
    """

    def __init__(self, redis_key: str, 
                 json_encoder_cls: Type[JSONEncoder] = None, object_hook: Callable = None,
                 expiration_delay: int = None, doc: str = "",
                 pre_set_hook: Callable = lambda self, x: x, post_get_hook: Callable = lambda self, x: x):
        """Initializer.
        
        pre_set_hook and post_get_hook can be added with decorators,
        see pre_set_hook() and post_get_hook() methods.
        """
        super().__init__()
        self.__doc__ = doc
        self.json_encoder_cls = json_encoder_cls
        self.object_hook = object_hook
        self.expiration_delay = expiration_delay
        self.redis_key = redis_key
        self.pre_set_hook_func = pre_set_hook
        self.post_get_hook_func = post_get_hook

    def __set_name__(self, owner, name):
        """Called at descriptor assignment.
        
        Check if owner is subclass of relevant types.
        Assign name.
        """

        self.name = name
        
        if not self.__doc__:
            self.__doc__ = f"{self.name} persistent attribute."
        
    def __get__(self, obj, owner):
        """Get data from Redis, and return self.post_get_hook_func(data)."""
        if obj is None:
            return self
        data = self.get_from_redis(f"sunflower:{obj.data_type}:{obj.endpoint}:{self.redis_key}", self.object_hook)
        return self.post_get_hook_func(obj, data)

    def __set__(self, obj, value):
        """Pass value to self.pre_set_hook_func() and store the result in Redis database."""
        data = self.pre_set_hook_func(obj, value)
        self.set_to_redis(f"sunflower:{obj.data_type}:{obj.endpoint}:{self.redis_key}", data, self.json_encoder_cls, self.expiration_delay)

    def __delete__(self, obj):
        raise AttributeError(f"Can't delete attribute 'f{self.name}'. It expires {self.expiration_delay} seconds after its last assignment.")

    def pre_set_hook(self, pre_set_hook_func):
        """Method for adding pre_set_hook_func() with a decorator.

        Usage:

        ```
        persistent_attribute = PersistentAttribute(...)

        @persistent_attribute.pre_set_hook
        def persistent_attribute(self, value):
            # format data to be stored in Redis database
            return data
        ```
        """
        return type(self)(self.redis_key, self.json_encoder_cls, self.object_hook, self.expiration_delay, self.__doc__, pre_set_hook_func, self.post_get_hook_func)
    
    def post_get_hook(self, post_get_hook_func):
        """Method for adding post_get_hook_func() with a decorator.

        Usage:

        ```
        persistent_attribute = PersistentAttribute(...)

        @persistent_attribute.post_get_hook
        def persistent_attribute(self, data):
            # decode data
            return value
        ```
        """
        return type(self)(self.redis_key, self.json_encoder_cls, self.object_hook, self.expiration_delay, self.__doc__, self.pre_set_hook_func, post_get_hook_func)
