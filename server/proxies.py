from typing import Type

from sunflower.core.bases import Station, Channel
from sunflower.core.descriptors import PersistentAttribute
from sunflower.stations import PycolorePlaylistStation

class Proxy:
    klass: Type

    def __init_subclass__(cls):
        if not hasattr(cls, "klass"):
            raise TypeError("Subclasses of 'Proxy' need a 'klass' class attribute")

    def __getattr__(self, name):
        attr = getattr(self.klass, name)
        if isinstance(attr, PersistentAttribute):
            return attr.__get__(self, self.klass)
        return attr


class ChannelProxy(Proxy):
    klass = Channel

    def __init__(self, endpoint):
        self.endpoint = endpoint


class PycoloreStationProxy(Proxy):
    endpoint = "pycolore"
    klass = PycolorePlaylistStation
