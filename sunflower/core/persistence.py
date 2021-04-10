import json
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from json.encoder import JSONEncoder
from typing import Any
from typing import Callable
from typing import Optional
from typing import Type

import aredis
from sunflower import settings
from sunflower.core.custom_types import NotifyChangeStatus
from sunflower.core.functions import run_coroutine_synchronously


class Repository(ABC):
    @abstractmethod
    def retrieve(self, *args, **kwargs):
        ...

    @abstractmethod
    def persist(self, *args, **kwargs):
        ...

    @abstractmethod
    def publish(self, *args, **kwargs):
        ...


class RedisRepository(Repository):
    """Provide a method to access data from redis database.

    Define REDIS_KEYS containing keys the application has right
    to access.
    """

    # keep a dict containing name of Redis channels for pubsub
    REDIS_CHANNELS = {name: "sunflower:channel:" + name for name in settings.CHANNELS}

    __slots__ = ("_redis",)

    def __init__(self, *args, **kwargs):
        self._redis = aredis.StrictRedis()

    def retrieve(self, key, object_hook=None):
        """Get value for given key from Redis.

        Data got from Redis is loaded from json with given object_hook.
        If no data is found, return None.
        """
        raw_data = run_coroutine_synchronously(self._redis.get, key)
        if raw_data is None:
            return None
        return json.loads(raw_data.decode(), object_hook=object_hook)

    def persist(self, key: str, value: Any, json_encoder_cls: Optional[Type[json.JSONEncoder]] = None):
        """Set new value for given key in Redis.

        value is dumped as json with given json_encoder_cls.
        """
        json_data = json.dumps(value, cls=json_encoder_cls)
        return run_coroutine_synchronously(self._redis.set, key, json_data)

    def publish(self, channel, data):
        """publish a message to a redis channel.

        Parameters:
        - channel (str): channel name
        - data (jsonable data or str): data to publish

        channel in redis is prefixed with 'sunflower:'.
        """
        assert channel in self.REDIS_CHANNELS, "Channel not defined in settings."
        if not isinstance(data, str):
            data = json.dumps(data)
        run_coroutine_synchronously(self._redis.publish, self.REDIS_CHANNELS[channel], data)


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
                 repository_cls: Type["Repository"] = None, notify_change: bool = False,
                 pre_set_hook: Callable = lambda self, x: x, post_get_hook: Callable = lambda self, x: x):
        super().__init__()
        if repository_cls is None:
            repository_cls = RedisRepository
        self.repository = repository_cls()
        self.key = key
        self.__doc__ = doc
        self.json_encoder_cls = json_encoder_cls
        self.object_hook = object_hook
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
        now = datetime.now().timestamp()
        data = self.pre_set_hook_func(obj, value) if value is not None else value
        if self._cache == data or data is None:
            if self.notify_change:
                self.repository.publish(obj.endpoint, NotifyChangeStatus.UNCHANGED.value)
            return
        self.repository.persist(f"sunflower:{obj.data_type}:{obj.endpoint}:{self.key}", data, self.json_encoder_cls)
        self._cache = data
        if self.notify_change:
            self.repository.publish(obj.endpoint, NotifyChangeStatus.UPDATED.value)

    def __delete__(self, obj):
        raise AttributeError(f"Can't delete attribute 'f{self.name}'.")

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
            self.key, self.__doc__, self.json_encoder_cls, self.object_hook, type(self.repository),
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
            self.key, self.__doc__, self.json_encoder_cls, self.object_hook, type(self.repository),
            self.notify_change, self.pre_set_hook_func, post_get_hook_func
        )
