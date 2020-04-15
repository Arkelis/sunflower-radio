# This is sunflower radio
# bases.py contains base classes

from datetime import datetime, timedelta

from sunflower.core.types import CardMetadata, MetadataType

STATIONS_INSTANCES = dict()

class Station:
    """Base station.

    User defined stations should inherit from this class and define following properties:
    - station_name (str)
    - station_thumbnail (str): link to station thumbnail
    - station_url (str): url to music stream

    Station classes are singletons.
    """

    def __new__(cls):
        instance_of_dict = STATIONS_INSTANCES.get(cls.__name__)
        if instance_of_dict is None:
            instance_of_dict = STATIONS_INSTANCES[cls.__name__] = super().__new__(cls)
        return instance_of_dict

    station_name = str()
    station_thumbnail = str()

    def _get_error_metadata(self, message, seconds):
        return {
            "type": MetadataType.ERROR,
            "message": message,
            "end": int((datetime.now() + timedelta(seconds=seconds)).timestamp()),
            "thumbnail_src": self.station_thumbnail,
        }

    def get_metadata(self):
        """Return mapping containing metadata about current broadcast.
        
        This is data meant to be exposed as json and used by format_info() method.
        
        Required fields:
        - type: element of MetadataType enum (see utils.py)
        - metadata fields required by format_info() method (see below)
        """

    def format_info(self, metadata) -> CardMetadata:
        """Format metadata for displaying in the card.
        
        Should return a CardMetadata namedtuple (see utils.py).
        If empty, a given key should have "" (empty string) as value, and not None.
        Don't support MetadataType.NONE case as it is done in Channel class.
        """
    
    @classmethod
    def get_liquidsoap_config(cls):
        """Return string containing liquidsoap config for this station."""
    

class DynamicStation(Station):
    """Base class for internally managed stations."""

    def process(self, logger, channels_using, **kwargs):
        pass

class URLStation(Station):
    """Base class for external stations (basically relayed stream)."""
    station_url = str()

    @classmethod
    def get_liquidsoap_config(cls):
        formated_name = cls.station_name.lower().replace(" ", "")
        return '{} = mksafe(input.http("{}"))\n'.format(formated_name, cls.station_url)