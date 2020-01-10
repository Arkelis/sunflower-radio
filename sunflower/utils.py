"""Utilitary classes used in several parts of sunflower application."""

import json
from collections import namedtuple
import functools

from flask import abort
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
        - data (jsonable data or str): data to publish
        
        channel in redis is prefixed with 'sunflower:'.
        """
        assert channel in self.REDIS_CHANNELS, "Channel not defined in settings."
        if not isinstance(data, str):
            data = json.dumps(data)
        self._redis.publish(self.REDIS_CHANNELS[channel], data)


def get_channel_or_404(view_function):
    @functools.wraps(view_function)
    def wrapper(channel):
        if channel not in settings.CHANNELS:
            abort(404)
        from sunflower.radio import Channel
        return view_function(channel=Channel(channel))
    return wrapper


Song = namedtuple("Song", ["path", "artist", "title", "length"])
