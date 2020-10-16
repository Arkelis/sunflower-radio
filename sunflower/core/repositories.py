import json
from abc import ABC, abstractmethod
from typing import Any, Optional, Type

import aredis

from sunflower import settings
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
        raw_data = run_coroutine_synchronously(self._redis.get(key))
        if raw_data is None:
            return None
        return json.loads(raw_data.decode(), object_hook=object_hook)

    def persist(self, key: str, value: Any, json_encoder_cls: Optional[Type[json.JSONEncoder]] = None):
        """Set new value for given key in Redis.

        value is dumped as json with given json_encoder_cls.
        """
        json_data = json.dumps(value, cls=json_encoder_cls)
        return run_coroutine_synchronously(self._redis.set(key, json_data))

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
        run_coroutine_synchronously(self._redis.publish(self.REDIS_CHANNELS[channel], data))
