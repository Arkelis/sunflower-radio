# This file is part of sunflower package. radio

import json
from typing import NamedTuple
from enum import Enum
from typing import Any, Dict, Tuple, Optional, Union
from sunflower.core.mixins import RedisMixin
from dataclasses import dataclass

# Types

class MetadataType(Enum):
    MUSIC = "Track"
    PROGRAMME = "Programme"
    NONE = ""
    ADS = "Ads"
    ERROR = "Error"
    WAITING_FOR_FOLLOWING = "Transition"

MetadataDict = Dict[str, Union[str, MetadataType]]

# Custom named tuples

class Song(NamedTuple):
    path: str
    artist: str
    album: str
    title: str
    length: float

class CardMetadata(NamedTuple):
    current_thumbnail: str
    current_station: str
    current_broadcast_title: str
    current_show_title: str
    current_broadcast_summary: str

# Views objects (not in web meaning but more in dict_view meaning)

class BaseView(RedisMixin):
    """Object referencing Redis-stored data of an object of given type.
    
    All or almost all attributes are fetched dynamically with calls to
    Redis database. Views are used by the server for getting stored data
    of Channel and Station objects without having to deal with these big
    objects. Instead, it uses these view objects which are only exposing
    Redis-stored data.
    """
    __slots__ = ()
    fields: Tuple[str, ...] = ()

    def __getattr__(self, name):
        raise AttributeError(
            f"'{name}' attribute is not readable. "
            "Only following attributes are readable: " + ", ".join(self.fields) + "."
        )
    
    def __repr__(self):
        attrs = ", ".join(f"{name}={getattr(self, name)}" for name in self.__slots__ + self.fields)
        return f"<{type(self).__name__}({attrs})>"


class ChannelView(BaseView):
    """Object referencing stored data of a Channel object.
    
    A ChannelView object contains only the endpoint of a given
    channel. Other attributes are dynamically got from Redis:
    - metadata is fetched from sunflower:channel:{endpoint}:metadata key
    - info is fetched from sunflower:channel:{endpoint}:info key

    Final attribues are defined:
    - fields: dynamic attributes that can be accessed
    - endpoint: endpoint of the corresponding Channel object

    Any other attribute access will result in a AttributeError.
    """

    __slots__= ("endpoint",)
    fields = ("metadata", "info")

    def __init__(self, endpoint):
        super().__init__()
        self.endpoint = endpoint

    def __getattr__(self, name):
        if name in self.fields:
            return self.get_from_redis(f"sunflower:channel:{self.endpoint}:{name}", object_hook=as_metadata_type)
        return super().__getattr__(name)


class StationView(BaseView):
    """Object referencing stored data of a Channel object.
    
    A StatioObject object contains only the endpoint of a given
    dynamic station. 'data' attribute is fetched from Redis.
    'endpoint' attribute is also readable.
    """

    __slots__= ("endpoint",)
    fields = ("data",)

    def __init__(self, endpoint):
        super().__init__()
        self.endpoint = endpoint

    def __getattr__(self, name):
        if name in self.fields:
            return self.get_from_redis(f"sunflower:station:{self.endpoint}:{name}")
        return super().__getattr__(name)


# MetadataType utils for json (de)serialization

class MetadataEncoder(json.JSONEncoder):
    """Subclass of json.JSONEncoder supporting MetadataType serialization."""
    def default(self, obj):
        if isinstance(obj, MetadataType):
            return obj.value
        return json.JSONEncoder.default(self, obj)

def as_metadata_type(mapping: Dict[str, Any]) -> Dict[str, Any]:
    """object_hook for supporting MetadataType at json deserialization."""
    type_ = mapping.get("type")
    if type_ is None:
        return mapping
    for member in MetadataType:
        if type_ == member.value:
            mapping["type"] = MetadataType(type_)
            break
    return mapping
