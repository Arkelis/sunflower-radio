import json
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Callable
from typing import Optional
from typing import Type

import aredis


class Repository(ABC):
    @abstractmethod
    async def retrieve(self, key: str, object_hook: Optional[Callable] = None):
        ...

    @abstractmethod
    async def persist(self, key: str, value: Any, json_encoder_cls: Optional[Type[json.JSONEncoder]] = None):
        ...

    @abstractmethod
    async def publish(self, channel: str, data: str):
        ...


class RedisRepository(Repository):
    """Provide a method to access data from redis database.

    Define REDIS_KEYS containing keys the application has right
    to access.
    """
    __slots__ = ("_redis",)

    def __init__(self, *args, **kwargs):
        self._redis = aredis.StrictRedis()

    async def retrieve(self, key: str, object_hook: Optional[Callable] = None):
        """Get value for given key from Redis.

        Data got from Redis is loaded from json with given object_hook.
        If no data is found, return None.
        """
        raw_data = await self._redis.get(key)
        if raw_data is None:
            return None
        return json.loads(raw_data.decode(), object_hook=object_hook)

    async def persist(self, key: str, value: Any, json_encoder_cls: Optional[Type[json.JSONEncoder]] = None):
        """Set new value for given key in Redis.

        value is dumped as json with given json_encoder_cls.
        """
        json_data = json.dumps(value, cls=json_encoder_cls)
        return await self._redis.set(key, json_data)

    async def publish(self, channel: str, data: str):
        """publish a message to a redis channel.

        Parameters:
        - channel (str): pubsub channel name
        - data (str): data to publish

        channel in redis is prefixed with 'sunflower:'.
        """
        await self._redis.publish(channel, data)
