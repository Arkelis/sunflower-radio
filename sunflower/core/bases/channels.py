from datetime import datetime, time

from backports.datetime_fromisoformat import MonkeyPatch

from sunflower import settings
from sunflower.core.mixins import RedisMixin
from sunflower.core.types import (CardMetadata, MetadataEncoder, MetadataType,
                                  as_metadata_type)

CHANNELS = dict()


class Channel(RedisMixin):
    def __init__(self, endpoint, timetable, handlers=[]):
        """Channel constructor.

        Parameters:
        - endpoint: string
        - stations: list of Station subclasses
        - timetable: dict
        - handler: list of classes that can alter metadata and card metadata at channel level after fetching.
        """
        assert endpoint in settings.CHANNELS, "{} not mentionned in settings.CHANNELS".format(endpoint)

        super().__init__()

        self.endpoint = endpoint
        self.timetable = timetable
        self.handlers = [Handler(self) for Handler in handlers]

        self.redis_metadata_key = "sunflower:" + self.endpoint + ":metadata"
        self.redis_info_key = "sunflower:" + self.endpoint + ":info"

        CHANNELS[self.endpoint] = self

    @property
    def stations(self) -> set:
        """Cached property returning list of stations used by channel."""
        stations = set()
        for l in self.timetable.values():
            for t in l:
                stations.add(t[2])
        stations = self.__dict__["stations"] = tuple(stations)
        return stations

    def get_station_info(self, time_, following=False):
        """Get info of station playing at given time.

        Parameters:
        - time_ must be datetime.time instance.
        - if following=True, return next station and not current station.

        Return (start, end, station_cls):
        - start: datetime.time object
        - end: datetime.time object
        - station_cls: Station class
        """
        MonkeyPatch.patch_fromisoformat()

        # fisrt, select weekday
        week_day = datetime.now().weekday()
        for t in self.timetable:
            if week_day in t:
                key = t
                break
        else:
            raise RuntimeError("Jour de la semaine non supporté.")
        
        station_cls = self.timetable[key][0][2]
        for t in self.timetable[key][::-1]:
            # on parcourt la table en partant de la fin
            start, end = map(time.fromisoformat, t[:2])

            # tant qu'on est avant le démarrage de la plage courante, on continue
            # tout en gardant en mémoire la station
            if time_ < start:
                station_cls = t[2]
                continue

            # si on veut la station courante on la sélectionne
            if not following:
                station_cls = t[2]
            # sinon on renvoie celle encore en mémoire (la suivante puisqu'on parcourt
            # la table à l'envers)
            
            return start, end, station_cls
        else:
            raise RuntimeError("Aucune station programmée à cet horaire.")

    def _get_station_instance(self, time_, following):
        if len(self.stations) == 1:
            return self.stations[0]()
        
        CurrentStationClass = self.get_station_info(time_, following)[2]
        return CurrentStationClass()

    @property
    def current_station(self):
        """Return Station object currently on air."""
        return self._get_station_instance(datetime.now().time(), following=False)
    
    @property
    def following_station(self):
        """Return next Station object to be on air."""
        return self._get_station_instance(datetime.now().time(), following=True)

    def get_from_redis(self, key, object_hook=as_metadata_type):
        return super().get_from_redis(key, object_hook)

    def set_to_redis(self, key, value, json_encoder_cls=MetadataEncoder):
        super().set_to_redis(key, value, json_encoder_cls)

    def publish_to_redis(self, metadata):
        return super().publish_to_redis(self.endpoint, metadata)

    @property
    def current_broadcast_metadata(self):
        """Retrieve metadata stored in Redis as a dict."""
        return self.get_from_redis(self.redis_metadata_key)

    @current_broadcast_metadata.setter
    def current_broadcast_metadata(self, metadata):
        """Store metadata in Redis."""
        self.set_to_redis(self.redis_metadata_key, metadata)

    @property
    def current_broadcast_info(self) -> CardMetadata:
        """Retrieve card info stored in Redis as a dict."""
        redis_data = self.get_from_redis(self.redis_info_key)
        if redis_data is None:
            return CardMetadata("", "", "", "", "")
        return CardMetadata(**redis_data)

    @current_broadcast_info.setter
    def current_broadcast_info(self, info: CardMetadata):
        """Store card info in Redis."""
        self.set_to_redis(self.redis_info_key, info._asdict())
    
    @property
    def neutral_card_metadata(self) -> CardMetadata:
        return CardMetadata(
            current_thumbnail=self.current_station.station_thumbnail,
            current_station=self.current_station.station_name,
            current_broadcast_title="Vous écoutez {}".format(self.current_station.station_name),
            current_show_title="",
            current_broadcast_summary="",
        )
    
    @property
    def waiting_following_card_metadata(self) -> CardMetadata:
        return CardMetadata(
            current_thumbnail=self.current_station.station_thumbnail,
            current_station=self.current_station.station_name,
            current_broadcast_title="Dans un instant : {}".format(self.following_station.station_name),
            current_show_title="",
            current_broadcast_summary="",
        )

    def get_current_broadcast_info(self, metadata) -> CardMetadata:
        """Return data for displaying broadcast info in player.

        This is for data display in player client. This method uses format_info()
        method of currently broadcasted station.
        """
        metadata_type = metadata["type"]
        if metadata_type in (MetadataType.NONE, MetadataType.ERROR):
            return self.neutral_card_metadata
        if metadata_type == MetadataType.WAITING_FOLLOWING:
            return self.waiting_following_card_metadata
        return self.current_station.format_info(metadata)

    def get_current_broadcast_metadata(self):
        """Get metadata of current broadcasted programm for current station.

        This is for pure json data exposure. This method uses get_metadata() method
        of currently broadcasted station.
        """
        metadata = self.current_station.get_metadata()
        metadata.update({"station": self.current_station.station_name})
        return metadata

    def process(self, logger, **kwargs):
        """If needed, update metadata.

        1. If current station is not a simple http stream, call station.process() method.
        2. Check if metadata needs to be updated
        3. Get metadata and card info with stations methods
        4. Apply changements operated by handlers
        5. Update metadata in Redis
        6. If needed, send SSE and update card info in Redis.

        If card info changed and need to be updated in client, return True.
        Else return False.
        """

        if (
            self.current_broadcast_metadata is not None
            and datetime.now().timestamp() < self.current_broadcast_metadata["end"]
            and self.current_broadcast_metadata["station"] == self.current_station.station_name
        ):
            self.publish_to_redis("unchanged")
            return False


        metadata = self.get_current_broadcast_metadata()
        info = self.get_current_broadcast_info(metadata)

        for handler in self.handlers:
            metadata, info = handler.process(metadata, info, logger)
        
        self.current_broadcast_metadata = metadata
        if info == self.current_broadcast_info:
            self.publish_to_redis("unchanged")
            return False
        self.current_broadcast_info = info
        self.publish_to_redis("updated")
        return True
    
    def get_liquidsoap_config(self):
        """Renvoie une chaîne de caractères à écrire dans le fichier de configuration liquidsoap."""

        # indication nom de la chaîne
        string = "##### " + str(self.endpoint) + " channel #####\n\n"

        # définition des horaires des radios
        if len(self.stations) > 1:
            timetable_to_write = "# timetable\n{}_timetable = switch(track_sensitive=false, [\n".format(self.endpoint)
            for days, timetable in self.timetable.items():
                formated_weekday = (
                    ("(" + " or ".join("{}w".format(wd+1) for wd in days) + ") and")
                    if len(days) > 1
                    else "{}w and".format(days[0]+1)
                )
                for start, end, station in timetable:
                    if start.count(":") != 1 or end.count(":") != 1:
                        raise RuntimeError("Time format must be HH:MM.")
                    formated_start = start.replace(":", "h")
                    formated_end = end.replace(":", "h")
                    formated_name = station.station_name.lower().replace(" ", "")
                    line = "    ({{ {} {}-{} }}, {}),\n".format(formated_weekday, formated_start, formated_end, formated_name)
                    timetable_to_write += line
            timetable_to_write += "])\n\n"
        else:
            timetable_to_write = ""
        
        # écriture de l'emploi du temps
        string += timetable_to_write
        
        # output
        fallback = str(self.endpoint) + "_timetable" if timetable_to_write else self.stations[0].station_name.lower().replace(" ", "")
        string += str(self.endpoint) + "_radio = fallback([" + fallback + ", default])\n"    
        string += str(self.endpoint) + '_radio = fallback(track_sensitive=false, [request.queue(id="' + str(self.endpoint) + '_custom_songs"), ' + str(self.endpoint) + '_radio])\n\n'
        string += "# output\n"
        string += "output.icecast(%vorbis(quality=0.6),\n"
        string += '    host="localhost", port=3333, password="Arkelis77",\n'
        string += '    mount="{0}", {0}_radio)\n\n'.format(self.endpoint)

        return string
