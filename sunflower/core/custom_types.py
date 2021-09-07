# This file is part of sunflower package. radio

from enum import Enum
from typing import Any
from typing import Optional
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from sunflower.core.bases import Station


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

class StationInfo(BaseModel):
    name: str
    website: Optional[str] = ""


class Broadcast(BaseModel):
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
    metadata: Any = None  # useful for storing some payload

    @classmethod
    def waiting_for_next(cls, station: "Station", next_station_name: str) -> "Broadcast":
        """Factory method for broadcast just waiting for next station"""
        return cls(
            title=f"Dans un instant : {next_station_name}.",
            type=BroadcastType.WAITING_FOR_NEXT,
            station=station.station_info,
            thumbnail_src=station.station_thumbnail,
        )

    @classmethod
    def ads(cls, station) -> "Broadcast":
        return cls(
            title=f"Publicité",
            type=BroadcastType.ADS,
            station=station.station_info,
            thumbnail_src=station.station_thumbnail,
        )

    @classmethod
    def empty(cls, station) -> "Broadcast":
        return cls(
            title=station.station_slogan,
            type=BroadcastType.NONE,
            station=station.station_info,
            thumbnail_src=station.station_thumbnail
        )

    @classmethod
    def none(cls) -> "Broadcast":
        return cls(title="", type=BroadcastType.NONE, station=StationInfo(name=""), thumbnail_src="")


class Step(BaseModel):
    start: int
    end: int
    broadcast: Broadcast

    @classmethod
    def waiting_for_next_station(cls, start: int, end: int, station: "Station", next_station_name: str) -> "Step":
        """Generic step indicating next station."""
        return cls(start=start, end=end, broadcast=Broadcast.waiting_for_next(station, next_station_name))

    @classmethod
    def ads(cls, start: int, station: "Station") -> "Step":
        """Generic ads step."""
        return cls(start=start, end=0, broadcast=Broadcast.ads(station))

    @classmethod
    def empty(cls, start: int, station: "Station") -> "Step":
        return cls(start=start, end=0, broadcast=Broadcast.empty(station))

    @classmethod
    def empty_until(cls, start: int, end: int, station: "Station") -> "Step":
        return cls(start=start, end=end, broadcast=Broadcast.empty(station))

    @classmethod
    def none(cls) -> "Step":
        return cls(start=0, end=0, broadcast=Broadcast.none())

    def is_none(self):
        return self.broadcast == Broadcast.none()


class UpdateInfo(BaseModel):
    should_notify_update: bool
    step: Step

    def __iter__(self):
        return self.__dict__.values().__iter__()


class Song(BaseModel):
    path: str
    artist: str
    album: str
    title: str
    length: float


class StreamMetadata(BaseModel):
    title: str
    artist: str
    album: str = ""


# alias for StreamMetadata
class SongPayload(StreamMetadata):
    pass
