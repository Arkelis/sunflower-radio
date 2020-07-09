# This file is part of sunflower package. radio

import json
from enum import Enum
from typing import Any, Dict, Optional

from pydantic.dataclasses import dataclass as pydantic_dataclass


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
    WAITING_FOR_NEXT = "Transition"


# Dataclasses

@pydantic_dataclass
class StationInfo:
    name: str
    website: Optional[str] = ""


@pydantic_dataclass
class Broadcast:
    title: str
    type: BroadcastType
    station: StationInfo
    thumbnail_src: str
    link: Optional[str] = ""
    show_title: Optional[str] = ""
    show_link: Optional[str] = ""
    summary: Optional[str] = ""
    parent_show_title: Optional[str] = ""
    parent_show_link: Optional[str] = ""

    @classmethod
    def waiting_for_next(cls, station: "Station", next_station_name: str):
        """Factory method for broadcast just waiting for next station"""
        return cls(
            title=f"Dans un instant : {next_station_name}.",
            type=BroadcastType.WAITING_FOR_NEXT,
            station=station.station_info,
            thumbnail_src=station.station_thumbnail,
        )


@pydantic_dataclass
class Step:
    start: int
    end: int
    broadcast: Broadcast

    @classmethod
    def waiting_for_next(cls, start: int, end: int, station: "Station", next_station_name: str):
        return cls(start, end, Broadcast.waiting_for_next(station, next_station_name))


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
            mapping["type"] = BroadcastType(type_)
            break
    return mapping
