"""Utilitary classes used in several parts of sunflower application."""

import json
from collections import namedtuple
from enum import Enum
import functools

from flask import abort
import redis

from sunflower import settings

# Mixins

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

# Custom views

def get_channel_or_404(view_function):
    @functools.wraps(view_function)
    def wrapper(channel):
        if channel not in settings.CHANNELS:
            abort(404)
        from sunflower.channels import CHANNELS
        return view_function(channel=CHANNELS[channel])
    return wrapper

# Custom datamodel

Song = namedtuple("Song", ["path", "artist", "title", "length"])
CardMetadata = namedtuple("CardMetadata", ["current_thumbnail",
                                           "current_station",
                                           "current_broadcast_title",
                                           "current_show_title",
                                           "current_broadcast_summary",])

# Available metadata types

class MetadataType(Enum):
    MUSIC = "Musique"
    PROGRAMME = "Emission"
    NONE = ""
    ADS = "Publicité"
    ERROR = "Erreur"

class MetadataEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, MetadataType):
            return obj.value
        return json.JSONEncoder.default(self, obj)

def as_metadata_type(mapping):
    type_ = mapping.get("type")
    if type_ is None:
        return mapping
    for member in MetadataType:
        if type_ != member.value:
            continue
        mapping["type"] = MetadataType(type_)
        break
    return mapping