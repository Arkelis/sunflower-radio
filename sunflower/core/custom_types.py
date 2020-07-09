# This file is part of sunflower package. radio

import json
from collections import namedtuple
from enum import Enum
from typing import Any, Dict, NamedTuple, Optional, Tuple, Union

from pydantic import AnyHttpUrl
from pydantic.dataclasses import dataclass as pydantic_dataclass

from sunflower.core.repositories import RedisRepository


# Enums

class NotifyChangeStatus(Enum):
    UNCHANGED = 0
    UPDATED = 1


class BroadcastType(Enum):
    MUSIC = "Track"
    PROGRAMME = "Programme"
    NONE = ""
    ADS = "Ads"
    ERROR = "Error"
    WAITING_FOR_FOLLOWING = "Transition"


# Dataclasses

@pydantic_dataclass
class StationInfo:
    name: str
    website: Optional[AnyHttpUrl]
    endpoint: Optional[str]


@pydantic_dataclass
class Broadcast:
    title: str
    type: BroadcastType
    link: Optional[AnyHttpUrl]
    show_title: str
    show_link: Optional[AnyHttpUrl]
    summary: Optional[str]
    thumbnail_src: AnyHttpUrl
    station: StationInfo
    parent_show_title: Optional[str]
    parent_show_link: Optional[AnyHttpUrl]


@pydantic_dataclass
class Step:
    start: int
    end: int
    broadcast: Broadcast


@pydantic_dataclass
class Song:
    path: str
    artist: str
    album: str
    title: str
    length: float


@pydantic_dataclass
class StreamMetadata:
    title: str
    artist: str
    album: str = ""


# BroadcastType utils for json (de)serialization

class MetadataEncoder(json.JSONEncoder):
    """Subclass of json.JSONEncoder supporting BroadcastType serialization."""
    def default(self, obj):
        if isinstance(obj, BroadcastType):
            return obj.value
        return json.JSONEncoder.default(self, obj)


def as_metadata_type(mapping: Dict[str, Any]) -> Dict[str, Any]:
    """object_hook for supporting BroadcastType at json deserialization."""
    type_ = mapping.get("type")
    if type_ is None:
        return mapping
    for member in BroadcastType:
        if type_ == member.value:
            mapping["type"] = MetadataType(type_)
            break
    return mapping
