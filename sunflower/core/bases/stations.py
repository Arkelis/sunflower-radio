# This file is part of sunflower package. radio
# bases.py contains base classes

from datetime import datetime, timedelta
from logging import Logger
from typing import Dict, Optional

from sunflower.core.custom_types import Broadcast, BroadcastType, StationInfo, Step, StreamMetadata
from sunflower.core.decorators import classproperty
from sunflower.core.liquidsoap import open_telnet_session
from sunflower.core.mixins import HTMLMixin

STATIONS_INSTANCES = {} # type: Dict[StationMeta, Optional[Station]]
REVERSE_STATIONS = {} # type: Dict[str, Type[DynamicStation]]


class StationMeta(type):
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

    def _get_error_metadata(self, message, seconds):
        """Return general mapping containing a message and ERROR type.
        
        Paramaters:
        - message: error description
        - seconds: error duration
        """
        return {
            "station": self.name,
            "type": BroadcastType.ERROR,
            "message": message,
            "end": int((datetime.now() + timedelta(seconds=seconds)).timestamp()),
            "thumbnail_src": self.station_thumbnail,
        }

    def get_step(self, logger: Logger, dt: datetime, channel: "Channel", for_schedule: bool = False) -> Step:
        """Return Step object for broadcast starting at dt.

        For schedule purpose: return a Step with end=start for a step during until the end of the
        time slot.

        Parameters:

        - logger: Logger - for logging and debug purpose
        - dt: datetime which should be the beginning of broadcast
        - channel: Channel object calling this method, it can contains useful information
        - for_schedule: bool - indicates if returned step is meant to be displayed in schedule or in player
        """

    # def format_info(self, current_info: CardMetadata, metadata: MetadataDict, logger: Logger) -> CardMetadata:
    #     """Format metadata for displaying in the card.
    #
    #     Return a CardMetadata namedtuple (see sunflower.core.types).
    #     If empty, a given key should have "" (empty string) as value, and not None.
    #
    #     Data in returned CardMetadata must come from metadata mapping argument.
    #
    #     Don't support BroadcastType.NONE and BroadcastType.WAITNIG_FOR_FOLLOWING cases
    #     as it is done in Channel class.
    #     """
    
    def format_stream_metadata(self, broadcast: Broadcast) -> Optional[StreamMetadata]:
        """For sending data to liquidsoap server.

        These metadata will be attached to stream file and can be readen by
        music software reading icecast stream directly.
        
        By default, return None (no data is sent)
        Otherwise return a StreamMetadata object.
        """
        return None

    @classmethod
    def get_liquidsoap_config(cls):
        """Return string containing liquidsoap config for this station."""


class DynamicStation(Station):
    """Base class for internally managed stations.
    
    Must implement process() method.
    """
    endpoint: str = "" # for api

    def __init_subclass__(cls):
        REVERSE_STATIONS[cls.endpoint] = cls

    def process(self, logger, channels_using, now, **kwargs):
        raise NotImplementedError("process() must be implemented")


class URLStation(Station):
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
                f'mksafe(drop_metadata(input.http(id="{cls.formatted_station_name}", autostart=false, '
                f'"{cls.station_url}")))\n')

    def start_liquidsoap_source(self):
        with open_telnet_session() as session:
            session.write(f"{self.formatted_station_name}.start\n".encode())

    def stop_liquidsoap_source(self):
        with open_telnet_session() as session:
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
