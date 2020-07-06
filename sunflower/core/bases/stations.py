# This file is part of sunflower package. radio
# bases.py contains base classes

from datetime import datetime, timedelta
from logging import Logger
from typing import Dict, Optional

from sunflower.core.custom_types import CardMetadata, MetadataDict, MetadataType, StreamMetadata
from sunflower.core.decorators import classproperty
from sunflower.core.liquidsoap import open_telnet_session
from sunflower.core.mixins import HTMLMixin, ProvideViewMixin

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
    station_name: str = ""
    station_thumbnail: str = ""
    station_website_url: str = ""
    station_slogan: str = ""

    @classproperty
    def formatted_station_name(cls) -> str:
        """Return formatted station name.

        Formatted name means name in lower case and with all spaces removed.
        Example : "France Inter" becomes "franceinter".

        The parameter `cls` refers to the class and not to the instance.
        """
        return cls.station_name.lower().replace(" ", "")

    @property
    def html_formatted_station_name(self):
        return self._format_html_anchor_element(self.station_website_url, self.station_name)

    def _get_error_metadata(self, message, seconds):
        """Return general mapping containing a message and ERROR type.
        
        Paramaters:
        - message: error description
        - seconds: error duration
        """
        return {
            "station": self.station_name,
            "type": MetadataType.ERROR,
            "message": message,
            "end": int((datetime.now() + timedelta(seconds=seconds)).timestamp()),
            "thumbnail_src": self.station_thumbnail,
        }

    def get_metadata(self, current_metadata: MetadataDict, logger: Logger, dt: datetime):
        """Return mapping containing new metadata about current broadcast.
        
        current_metadata is metadata stored in Redis and known by
        Channel object. This method can use currant_metadata provided
        by channel for partial updates. 

        Returned data is data meant to be exposed as json and used by format_info() method.
        
        Mandatory fields in returned mapping:
        - type: element of MetadataType enum (see sunflower.core.types module);
        - end: timestamp (int) telling Channel object when to call this method for updating
        metadata;
        
        and other metadata fields required by format_info().
        """

    def format_info(self, current_info: CardMetadata, metadata: MetadataDict, logger: Logger) -> CardMetadata:
        """Format metadata for displaying in the card.

        Return a CardMetadata namedtuple (see sunflower.core.types).
        If empty, a given key should have "" (empty string) as value, and not None.

        Data in returned CardMetadata must come from metadata mapping argument.

        Don't support MetadataType.NONE and MetadataType.WAITNIG_FOR_FOLLOWING cases
        as it is done in Channel class.
        """
    
    def format_stream_metadata(self, metadata) -> Optional[StreamMetadata]:
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


class DynamicStation(Station, ProvideViewMixin):
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
    is_on: bool = False

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
            session.write(f"{self.formatted_station_name}.start")

    def stop_liquidsoap_source(self):
        with open_telnet_session() as session:
            session.write(f"{self.formatted_station_name}.stop")

    def process(self, channels_using, channels_using_next):
        if self in (*channels_using, *channels_using_next):
            if not self.is_on:
                self.start_liquidsoap_source()
        else:
            if self.is_on:
                self.stop_liquidsoap_source()
