# This file is part of sunflower package. radio
# bases.py contains base classes

from datetime import datetime, timedelta

from sunflower.core.types import CardMetadata, MetadataType
from sunflower.core.mixins import HTMLMixin

STATIONS_INSTANCES = dict()

class Station(HTMLMixin):
    """Base station.

    User defined stations should inherit from this class and define following properties:
    - station_name (str)
    - station_thumbnail (str): link to station thumbnail

    Station classes are singletons.
    """

    def __new__(cls):
        """Create new instance or return previously created one.

        Station class is singleton, so once one instance is created,
        all other calls to this method return the one created before. At
        first instanciation, call __setup__() method.
        """
        instance_of_dict = STATIONS_INSTANCES.get(cls.__name__)
        if instance_of_dict is None:
            instance_of_dict = STATIONS_INSTANCES[cls.__name__] = super().__new__(cls)
            instance_of_dict.__setup__()
        return instance_of_dict

    station_name = str()
    station_thumbnail = str()
    station_website_url = str()

    @property
    def formated_station_name(self):
        return self.station_name.lower().replace(" ", "")

    @property
    def html_formated_station_name(self):
        return self._format_html_anchor_element(self.station_website_url, self.station_name)

    def __setup__(self):
        """Equivalent of __init__() but it is called at first instanciation only.

        Further instanciations return first created object as this class is a singleton.
        """

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

    def get_metadata(self, current_metadata, logger):
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

    def format_info(self, metadata, logger) -> CardMetadata:
        """Format metadata for displaying in the card.

        Return a CardMetadata namedtuple (see sunflower.core.types).
        If empty, a given key should have "" (empty string) as value, and not None.

        Data in returned CardMetadata must come from metadata mapping argument.

        Don't support MetadataType.NONE and MetadataType.WAITNIG_FOR_FOLLOWING cases
        as it is done in Channel class.
        """

    @classmethod
    def get_liquidsoap_config(cls):
        """Return string containing liquidsoap config for this station."""


class DynamicStation(Station):
    """Base class for internally managed stations.
    
    Must implement process() method.
    """

    def process(self, logger, channels_using, **kwargs):
        raise NotImplementedError("process() must be implemented")

class URLStation(Station):
    """Base class for external stations (basically relayed stream).
    
    URLStation object must have station_url str class attribute (audio stream url).
    URLStation object can have station_slogan attribute that can be
    used when no metadata is provided at a given time.
    """
    station_url = str()
    station_slogan = str()

    def __setup__(self):
        if self.station_url == "":
            raise ValueError("URL not specified for URLStation object.")

    @classmethod
    def get_liquidsoap_config(cls):
        formated_name = cls.station_name.lower().replace(" ", "")
        return '{} = mksafe(input.http("{}"))\n'.format(formated_name, cls.station_url)
