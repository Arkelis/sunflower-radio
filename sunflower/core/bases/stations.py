# This file is part of sunflower package. radio
# bases.py contains base classes
from abc import ABC, ABCMeta, abstractmethod
from contextlib import suppress
from datetime import datetime
from logging import Logger
from telnetlib import Telnet
from typing import Dict, List, Optional, TYPE_CHECKING, Type

from sunflower.core.custom_types import Broadcast, StationInfo, Step, StreamMetadata, UpdateInfo
from sunflower.core.decorators import classproperty
from sunflower.core.mixins import HTMLMixin
from sunflower.settings import LIQUIDSOAP_TELNET_HOST, LIQUIDSOAP_TELNET_PORT

if TYPE_CHECKING:
    from sunflower.core.bases.channels import Channel

STATIONS_INSTANCES = {} # type: Dict[StationMeta, Optional[Station]]
REVERSE_STATIONS = {} # type: Dict[str, Type[DynamicStation]]


class StationMeta(ABCMeta):
    """Station metaclass

    Station are singletons. This metaclass override Station classes instantiation mechanism:

    - first time `StationKlass()` is called, an object is created
    - the following times `StationKlass()` is called, it returns the existing instance
      (does not call `__new__()` or `__init__()`)
    """

    def __call__(cls, *args, **kwargs):
        if cls not in STATIONS_INSTANCES:
            STATIONS_INSTANCES[cls] = super().__call__(*args, **kwargs)
        return STATIONS_INSTANCES[cls]


class Station(HTMLMixin, metaclass=StationMeta):
    """Base station.

    User defined stations should inherit from this class and define following properties:
    - station_name (str)
    - station_thumbnail (str): link to station thumbnail

    Station classes are singletons.
    """

    data_type = "station"
    name: str = ""
    station_thumbnail: str = ""
    station_website_url: str = ""
    station_slogan: str = ""

    # By default, station data is retrieved when current broadcast/step is ended. Sometimes, station external API is not
    # very reliable, and long pull is needed (regular retrieval instead of strategic pull). In this case, turn this
    # attribute True in child class.
    long_pull = False

    @property
    def station_info(self):
        info = StationInfo(name=self.name)
        if self.station_website_url:
            info.website = self.station_website_url
        return info

    @classproperty
    def formatted_station_name(cls) -> str:
        """Return formatted station name.

        Formatted name means name in lower case and with all spaces removed.
        Example : "France Inter" becomes "franceinter".

        The parameter `cls` refers to the class and not to the instance.
        """
        return cls.name.lower().replace(" ", "")

    @property
    def html_formatted_station_name(self):
        return self._format_html_anchor_element(self.station_website_url, self.name)

    @abstractmethod
    def get_step(self, logger: Logger, dt: datetime, channel: "Channel") -> UpdateInfo:
        """Return UpdateInfo object for broadcast starting at dt.

        UpdateInfo object contains two attributs:
        - should_notify_update (bool): depending on this value, the Channel object will decide if it must send a server
        push to the client.
        - step (Step): the new Step object

        Parameters:

        - logger: Logger - for logging and debug purpose
        - dt: datetime which should be the beginning of broadcast
        - channel: Channel object calling this method, it can contains useful information
        - for_schedule: bool - indicates if returned step is meant to be displayed in schedule or in player
        """

    @abstractmethod
    def get_next_step(self, logger: Logger, dt: datetime, channel: "Channel") -> Step:
        ...

    @abstractmethod
    def get_schedule(self, logger: Logger, start: datetime, end: datetime) -> List[Step]:
        ...

    @abstractmethod
    def format_stream_metadata(self, broadcast: Broadcast) -> Optional[StreamMetadata]:
        """For sending data to liquidsoap server.

        These metadata will be attached to stream file and can be readen by
        music software reading icecast stream directly.
        
        By default, return None (no data is sent)
        Otherwise return a StreamMetadata object.
        """

    @classmethod
    @abstractmethod
    def get_liquidsoap_config(cls):
        """Return string containing liquidsoap config for this station."""


class DynamicStation(Station, ABC):
    """Base class for internally managed stations.
    
    Must implement process() method.
    """
    endpoint: str = "" # for api

    def __init_subclass__(cls):
        REVERSE_STATIONS[cls.endpoint] = cls

    @abstractmethod
    def process(self, logger, channels_using, channels_using_next, now, **kwargs):
        ...


class URLStation(Station, ABC):
    """Base class for external stations (basically relayed stream).
    
    URLStation object must have station_url str class attribute (audio stream url).
    URLStation object can have station_slogan attribute that can be
    used when no metadata is provided at a given time.
    """
    station_url: str = ""
    station_slogan: str = ""
    _is_on: bool = False

    @property
    def is_onair(self) -> bool:
        return self._is_on

    def __new__(cls):
        if cls.station_url == "":
            raise ValueError("URL not specified for URLStation object.")
        return super().__new__(cls)

    @classmethod
    def get_liquidsoap_config(cls):
        return (f'{cls.formatted_station_name} = '
                f'mksafe(input.http(id="{cls.formatted_station_name}", autostart=false, "{cls.station_url}"))\n')

    def start_liquidsoap_source(self):
        with suppress(ConnectionRefusedError):
            with Telnet(LIQUIDSOAP_TELNET_HOST, LIQUIDSOAP_TELNET_PORT) as session:
                session.write(f"{self.formatted_station_name}.start\n".encode())

    def stop_liquidsoap_source(self):
        with suppress(ConnectionRefusedError):
            with Telnet(LIQUIDSOAP_TELNET_HOST, LIQUIDSOAP_TELNET_PORT) as session:
                session.write(f"{self.formatted_station_name}.stop\n".encode())

    def process(self, logger, channels_using, channels_using_next, **kwargs):
        if any(channels_using_next[self]) or any(channels_using[self]):
            if not self._is_on:
                self.start_liquidsoap_source()
                self._is_on = True
        else:
            if self._is_on:
                self.stop_liquidsoap_source()
                self._is_on = False
