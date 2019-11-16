"""Mixins used by several classes in Sunflower application."""

import redis

class RedisMixin:
    """Provide a method to access data from redis database.
    
    Define REDIS_KEYS containing keys the application has right 
    to access.
    """

    REDIS_METADATA = "sunflower:metadata"
    REDIS_KEYS = [
        REDIS_METADATA,
    ]

    def __init__(self, *args, **kwargs):
        self._redis = redis.Redis()

    def get_from_redis(self, key):
        if key not in self.REDIS_KEYS:
            raise KeyError("Only {} keys are used by this application.".format(self.REDIS_KEYS))
        return self.redis.get(key)
