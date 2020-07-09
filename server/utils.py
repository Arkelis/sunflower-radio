"""Utilitary classes used in several parts of sunflower application."""

import functools

from fastapi import HTTPException
from sunflower import settings
from sunflower.core.bases import REVERSE_STATIONS
from server.proxies import ChannelProxy, Proxy
# noinspection PyUnresolvedReferences
from sunflower.stations import * # needed for view objects generation


# fastapi/starlette views decorator

def get_channel_or_404(view_function):
    @functools.wraps(view_function)
    def wrapper(channel: str, *args, **kwargs):
        if channel not in settings.CHANNELS:
            raise HTTPException(404, f"Channel {channel} not found")
        channel_proxy = ChannelProxy(channel)
        return view_function(channel_proxy, *args, **kwargs)
    return wrapper


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
