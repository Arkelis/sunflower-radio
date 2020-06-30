# This file is part of sunflower package. radio

import json
from collections import namedtuple
from enum import Enum
from typing import Any, Dict, NamedTuple, Tuple, Union

from sunflower.core.repositories import RedisRepository

# Types

ChannelView = StationView = namedtuple("ViewObject", ["data_type", "endpoint"])


class NotifyChangeStatus(Enum):
    UNCHANGED = 0
    UPDATED = 1


class MetadataType(Enum):
    MUSIC = "Track"
    PROGRAMME = "Programme"
    NONE = ""
    ADS = "Ads"
    ERROR = "Error"
    WAITING_FOR_FOLLOWING = "Transition"


MetadataDict = Dict[str, Union[str, int, MetadataType]]


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


class StreamMetadata(NamedTuple):
    title: str
    artist: str
    album: str = ""


# Views objects (not in web meaning but more in dict_view meaning)

class BaseView(RedisRepository):
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
