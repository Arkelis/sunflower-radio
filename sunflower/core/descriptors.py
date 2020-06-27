from json import JSONEncoder
from typing import Callable, Type

from sunflower.core.repositories import RedisRepository, Repository
from sunflower.core.types import NotifyChangeStatus


class PersistentAttribute:
    """Descriptor for attributes stored in external persistence system.

    For the moment, only Redis persistent attributes are implemented.

    Owner class or object must have two mandatory attributes:

    - `data_type`: the type of the object to which data belongs to (for example station or channel)
    - `endpoint`: a string identifying the object (for Channel objects it is also the endpoint for webapp)

    You can provide an boolean argument for notifying changes:

    - `notify_change`: if stored data is changed, this attribute will publish to a Redis channel with obj.endpoint name.
      If data is changed, the message will be NotifyChangeStatus.UPDATED = 1, else NotifyChangeStatus.UNCHANGED = 0
      If this attribute is set to None, it will only notify UNCHANGED.

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

    def __init__(self, key: str = "", doc: str = "",
                 json_encoder_cls: Type[JSONEncoder] = None, object_hook: Callable = None,
                 repository_cls: Type[Repository] = RedisRepository, expiration_delay: int = None,
                 notify_change: bool = False,
                 pre_set_hook: Callable = lambda self, x: x, post_get_hook: Callable = lambda self, x: x):
        super().__init__()
        self.repository = repository_cls()
        self.key = key
        self.__doc__ = doc
        self.json_encoder_cls = json_encoder_cls
        self.object_hook = object_hook
        self.expiration_delay = expiration_delay
        self.notify_change = notify_change
        self.pre_set_hook_func = pre_set_hook
        self.post_get_hook_func = post_get_hook
        self._cache = None

    def __set_name__(self, owner, name):
        self.name = name
        if not self.__doc__:
            self.__doc__ = f"{self.name} persistent attribute."
        
    def __get__(self, obj, owner):
        """Get data from Redis, and return self.post_get_hook_func(data)."""
        if obj is None:
            return self
        data = self._cache = self.repository.retrieve(f"sunflower:{obj.data_type}:{obj.endpoint}:{self.key}", self.object_hook)
        return self.post_get_hook_func(obj, data)

    def __set__(self, obj, value):
        """Pass value to self.pre_set_hook_func() and store the result in Redis database.

        data = self.pre_set_hook_func(obj, value) must be serializable.
        if value is None, notify unchanged or do nothing.
        """
        data = self.pre_set_hook_func(obj, value) if value is not None else value
        if self._cache == data or data is None:
            if self.notify_change:
                self.repository.publish(obj.endpoint, NotifyChangeStatus.UNCHANGED.value)
            return
        self.repository.persist(f"sunflower:{obj.data_type}:{obj.endpoint}:{self.key}", data, self.json_encoder_cls, self.expiration_delay)
        self._cache = data
        if self.notify_change:
            self.repository.publish(obj.endpoint, NotifyChangeStatus.UPDATED.value)

    def __delete__(self, obj):
        raise AttributeError(f"Can't delete attribute 'f{self.name}'. " 
                             f"It expires {self.expiration_delay} seconds after its last assignment.")

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
        return type(self)(
            self.key, self.__doc__, self.json_encoder_cls, self.object_hook, type(self.repository), self.expiration_delay,
            self.notify_change, pre_set_hook_func, self.post_get_hook_func
        )
    
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
        return type(self)(
            self.key, self.__doc__, self.json_encoder_cls, self.object_hook, type(self.repository), self.expiration_delay,
            self.notify_change, self.pre_set_hook_func, post_get_hook_func
        )
