# This file is part of sunflower package. radio
# Mixins

import json

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

    def get_from_redis(self, key, object_hook=None):
        """Get value for given key from Redis.
        
        Data got from Redis is loaded from json with given object_hook.
        If no data is found, return None.
        """
        assert key in self.REDIS_KEYS, "Only {} keys are used by this application.".format(self.REDIS_KEYS)
        raw_data = self._redis.get(key)
        if raw_data is None:
            return None
        return json.loads(raw_data.decode(), object_hook=object_hook)
    
    def set_to_redis(self, key, value, json_encoder_cls=None):
        """Set new value for given key in Redis.
        
        value is dumped as json with given json_encoder_cls.
        """
        assert key in self.REDIS_KEYS, "Only {} keys are used by this application.".format(self.REDIS_KEYS)
        json_data = json.dumps(value, cls=json_encoder_cls)
        return self._redis.set(key, json_data, ex=86400)

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
