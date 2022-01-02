# This file is part of sunflower package. radio
# bases.py contains base classes
from abc import ABC
from abc import abstractmethod
from abc import abstractproperty
from datetime import datetime
from logging import Logger
from typing import Dict
from typing import List
from typing import Optional
from typing import TYPE_CHECKING
from typing import Type

from sunflower.core import _html as html_utils
from sunflower.core.custom_types import Broadcast
from sunflower.core.custom_types import StationInfo
from sunflower.core.custom_types import Step
from sunflower.core.custom_types import StreamMetadata
from sunflower.core.custom_types import UpdateInfo
from sunflower.core.decorators import classproperty
from sunflower.core.liquidsoap import liquidsoap_telnet_session
from sunflower.core.persistence import PersistenceMixin

if TYPE_CHECKING:
    from sunflower.core.channel import Channel

REVERSE_STATIONS = {} # type: Dict[str, Type[DynamicStation]]


class Station(ABC):
    """Base station.

    User defined stations should inherit from this class and define following properties:
    - name (str)
    - station_thumbnail (str): link to station thumbnail
    - station_website_url (str): link to station website. Default: ""
    - station_slogan (str): station moto. Default: ""
    """

    name: str = abstractproperty()
    station_thumbnail: str = abstractproperty()
    station_website_url: str = ""
    station_slogan: str = ""

    # By default, station data is retrieved when current broadcast/step is ended. Sometimes, station external API is not
    # very reliable, and long pull is needed (regular retrieval instead of strategic pull). In this case, turn this
    # attribute True in child class.
    long_pull = False

    @property
    def station_info(self):
        return StationInfo(name=self.name, website=self.station_website_url)

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
        return html_utils._format_html_anchor_element(self.station_website_url, self.name)

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
        ...

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
        ...


class DynamicStation(Station, PersistenceMixin, ABC):
    """Base class for internally managed stations.
    
    Must implement process() method.
    """
    data_type = "station"
    name = property(fget=lambda self: getattr(self, "_name"))

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
    _is_onair: bool = False

    @property
    def is_onair(self) -> bool:
        return self._is_onair

    def __new__(cls):
        if cls.station_url == "":
            raise ValueError("URL not specified for URLStation object.")
        return super().__new__(cls)

    def start_liquidsoap_source(self):
        with liquidsoap_telnet_session() as session:
            session.write(f"{self.formatted_station_name}.start\n".encode())

    def stop_liquidsoap_source(self):
        with liquidsoap_telnet_session() as session:
            session.write(f"{self.formatted_station_name}.stop\n".encode())

    def process(self, logger, channels_using, channels_using_next, **kwargs):
        if any(channels_using_next[self]) or any(channels_using[self]):
            if not self._is_onair:
                self.start_liquidsoap_source()
                self._is_onair = True
        else:
            if self._is_onair:
                self.stop_liquidsoap_source()
                self._is_onair = False
