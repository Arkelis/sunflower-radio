"""Utilitary classes used in several parts of sunflower application."""

import functools

from flask import abort

from sunflower import settings
from sunflower.core.bases import Channel, REVERSE_STATIONS
from sunflower.core.types import ChannelView, StationView
# noinspection PyUnresolvedReferences
from sunflower.stations import *


# flask views decorator

def get_channel_or_404(view_function):
    @functools.wraps(view_function)
    def wrapper(channel: str):
        if channel not in settings.CHANNELS:
            abort(404)
        channel_view: ChannelView = Channel.get_view(channel)
        return view_function(channel_view)
    return wrapper


def get_station_or_404(view_function):
    """Decorator checking if station is a valid endpoint to a dynamic station."""
    @functools.wraps(view_function)
    def wrapper(station: str, *args, **kwargs):
        station_cls = REVERSE_STATIONS.get(station)
        if station_cls is None:
            abort(404)
        station_view: StationView = station_cls.get_view(station)
        return view_function(station_view, *args, **kwargs)
    return wrapper
