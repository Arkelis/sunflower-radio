"""Utilitary classes used in several parts of sunflower application."""

import functools

import edn_format
from edn_format import Keyword
from fastapi import HTTPException
from server.proxies import ChannelProxy
from server.proxies import Proxy
from sunflower.core.repository import RedisRepository
from sunflower.core.stations import REVERSE_STATIONS
# noinspection PyUnresolvedReferences
from sunflower.stations import *  # needed for view objects generation

redis_repo = RedisRepository()

# read definitions
with open("sunflower/conf.edn") as f:
    definitions = edn_format.loads(f.read())
channels_definitions = definitions[Keyword("channels")]
stations_definitions = definitions[Keyword("stations")]
channels_ids = [channel_def[Keyword("id")] for channel_def in channels_definitions]


def get_channel_or_404(channel: str):
    if channel not in channels_ids:
        raise HTTPException(404, f"Channel {channel} does not exist")
    return ChannelProxy(redis_repo, channel)


def get_station_or_404(view_function):
    """Decorator checking if station is a valid endpoint to a dynamic station."""
    @functools.wraps(view_function)
    def wrapper(station: str, *args, **kwargs):
        station_cls = REVERSE_STATIONS.get(station)
        if station_cls is None:
            raise HTTPException(404, f"Station {station} not found")
        proxy_cls = type(f"{station.capitalize()}StationProxy", (Proxy,), {"klass": station_cls, "name": station_cls.name})
        station_proxy = proxy_cls(station)
        return view_function(station_proxy, *args, **kwargs)
    return wrapper
