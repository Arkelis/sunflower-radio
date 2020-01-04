"""Utilitary classes used in several parts of sunflower application."""

import json
from collections import namedtuple

import redis

from sunflower import settings


class RedisMixin:
    """Provide a method to access data from redis database.
    
    Define REDIS_KEYS containing keys the application has right 
    to access.
    """

    REDIS_KEYS = [
        item 
        for name in settings.CHANNELS 
        for item in ("sunflower:{}:metadata".format(name), "sunflower:{}:info".format(name))
    ]
    
    REDIS_CHANNELS = {name: "sunflower:" + name for name in settings.CHANNELS}

    def __init__(self, *args, **kwargs):
        self._redis = redis.Redis()

    def get_from_redis(self, key):
        if key not in self.REDIS_KEYS:
            raise KeyError("Only {} keys are used by this application.".format(self.REDIS_KEYS))
        return self._redis.get(key)

    def publish_to_redis(self, channel, data):
        """publish a message to a redis channel.

        Parameters:
        - channel (str): channel name
        - data (jsonable data): data to publish
        
        channel in redis is prefixed with 'sunflower:'.
        """
        assert channel in self.REDIS_CHANNELS, "Channel not defined in settings."
        self._redis.publish(self.REDIS_CHANNELS[channel], json.dumps(data))



Song = namedtuple("Song", ["path", "artist", "title", "length"])
