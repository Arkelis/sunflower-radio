import json
from abc import ABC
from abc import abstractmethod
from abc import abstractmethod
from abc import abstractmethod
from typing import Any
from typing import Any
from typing import Callable
from typing import Callable
from typing import Optional
from typing import Optional
from typing import Optional
from typing import Optional
from typing import Type
from typing import Type

import aredis
from sunflower.core.functions import run_coroutine_synchronously
from sunflower.core.functions import run_coroutine_synchronously
from sunflower.core.functions import run_coroutine_synchronously


class Repository(ABC):
    @abstractmethod
    def retrieve(self, key: str, object_hook: Optional[Callable] = None):
        ...

    @abstractmethod
    def persist(self, key: str, value: Any, json_encoder_cls: Optional[Type[json.JSONEncoder]] = None):
        ...

    @abstractmethod
    def publish(self, key: str, channel, data):
        ...


class RedisRepository(Repository):
    """Provide a method to access data from redis database.

    Define REDIS_KEYS containing keys the application has right
    to access.
    """
    __slots__ = ("_redis",)

    def __init__(self, *args, **kwargs):
        self._redis = aredis.StrictRedis()

    def retrieve(self, key: str, object_hook: Optional[Callable] = None):
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
        if not isinstance(data, str):
            data = json.dumps(data)
        run_coroutine_synchronously(self._redis.publish, channel, data)
