from datetime import datetime, time, timedelta
import functools
from logging import Logger

from sunflower import settings
from sunflower.core.bases.stations import Station
from sunflower.core.mixins import RedisMixin
from sunflower.core.descriptors import PersistentAttribute
from sunflower.core.types import (CardMetadata, MetadataEncoder, MetadataType,
                                  as_metadata_type, MetadataDict)


class Channel(RedisMixin):
    """Channel.

    Channel object contains and manages stations. It triggers station metadata updates
    thanks to its timetable and its process() method. The latter is called by Scheduler
    object (see scheduler module). Data is persisted to Redis and retrieved by web server
    thanks to view object (see ChannelView in types module).
    """

    data_type = "channel"
    
    def __init__(self, endpoint, timetable, handlers=[]):
        """Channel constructor.

        Parameters:
        - endpoint: string
        - timetable: dict
        - handler: list of classes that can alter metadata and card metadata at channel level after fetching.
        """
        assert endpoint in settings.CHANNELS, "{} not mentionned in settings.CHANNELS".format(endpoint)

        super().__init__()

        self.endpoint = endpoint
        self.timetable = timetable
        self.handlers = [Handler(self) for Handler in handlers]
        
        if len(self.stations) == 1:
            self._current_station_instance = self.stations[0]()
            self._following_station_instance = None
        else:
            self.current_station_start = datetime.now()
            self.current_station_end = datetime.now()
            self._current_station_instance = None
            self._following_station_instance = None

        self.redis_metadata_key = "sunflower:channel:" + self.endpoint + ":metadata"
        self.redis_info_key = "sunflower:channel:" + self.endpoint + ":info"

    @functools.cached_property
    def stations(self) -> tuple:
        """Cached property returning list of stations used by channel."""
        stations = set()
        for l in self.timetable.values():
            for t in l:
                stations.add(t[2])
        return tuple(stations)

    def get_station_info(self, datetime_obj, following=False):
        """Get info of station playing at given time.

        Parameters:
        - date_time must be datetime.datetime instance.
        - if following=True, return next station and not current station.

        Return (start, end, station_cls):
        - start: datetime.time object
        - end: datetime.time object
        - station_cls: Station class
        - following_station_cls: Station class
        """

        asked_time = datetime_obj.time()

        # fisrt, select weekday
        week_day = datetime_obj.weekday()
        for t in self.timetable:
            if week_day in t:
                key = t
                break
        else:
            raise RuntimeError("Jour de la semaine non supporté.")
        
        getting_following = False
        asked_station_cls = None
        following_station_cls = None

        index_of_last_element = len(self.timetable[key]) - 1
        for (i, t) in enumerate(self.timetable[key]):
            start, end = map(time.fromisoformat, t[:2])

            # tant que l'horaire demandé est situé après la fin de la plage,
            # on va à la plage suivante ; si on est sur le dernier élément
            # on le prend
            if asked_time > end and i != index_of_last_element:
                continue
            
            # cas où end > asked_time, càd on se situe dans la bonne plage
            # on sélectionne la plage courante
            if not getting_following:
                # dans le cas où on cherche la station courante, on enregistre les infos voulues
                asked_station_cls = t[2]
                asked_station_start = datetime.combine(datetime_obj.date(), start)
                asked_station_end = datetime.combine(datetime_obj.date(), end)
                if asked_station_end < asked_station_start: # cas de minuit
                    asked_station_end += timedelta(hours=24)
                getting_following = True
            else:
                # si on cherche la suivante, on enregistre uniquement la classe
                following_station_cls = t[2]
        
        # si après avoir parcouru le bon jour on n'a rien trouvé : on lève une erreur
        if asked_station_cls is None:
            raise RuntimeError("Aucune station programmée à cet horaire.")

        # dans le cas où la station courante était le dernier créneau de la journée,
        # on cherche la station suivante dans le premier créneau de la journée suivante.
        if following_station_cls is None:
            week_day = (datetime_obj + timedelta(hours=24)).weekday()
            for t in self.timetable:
                if week_day in t:
                    following_station_cls = self.timetable[t][0][2]
                    break
            else:
                raise RuntimeError("Jour de la semaine non supporté pour la station suivante : {}. Jours dispos : {}".format(week_day, self.timetable.keys()))
            
        return asked_station_start, asked_station_end, asked_station_cls, following_station_cls

    def _update_station_instances(self):
        """Update current-station-related attributes.

        - current_station_end
        - current_station_start
        - _current_station_instance (hidden, use 'current_station' property instead to acces it)
        - _following_station_instance (hidden, use 'ollowing_station' property instead to acces it)
        """

        if len(self.stations) == 1:
            # If only one station, skip.
            return
        
        if datetime.now() > self.current_station_end or self._current_station_instance is None:
            new_start, new_end, CurrentStationClass, FollowingStationClass = self.get_station_info(datetime.now(), following=True)
            self.current_station_end = new_end
            self.current_station_start = new_start
            self._current_station_instance = CurrentStationClass()
            self._following_station_instance = FollowingStationClass()

    @property
    def current_station(self) -> Station:
        """Return Station object currently on air."""
        self._update_station_instances()
        return self._current_station_instance
    
    @property
    def following_station(self) -> Station:
        """Return next Station object to be on air."""
        self._update_station_instances()
        return self._following_station_instance

    current_broadcast_metadata = PersistentAttribute("metadata", MetadataEncoder, as_metadata_type)
    current_broadcast_info = PersistentAttribute("info") # private as it is wrapped by current_broadcast_info property

    def publish_to_redis(self, metadata):
        return super().publish_to_redis(self.endpoint, metadata)

    @current_broadcast_info.post_get_hook
    def current_broadcast_info(self, redis_data) -> CardMetadata:
        """Retrieve card info stored in Redis as a dict."""
        if redis_data is None:
            return CardMetadata("", "", "", "", "")
        return CardMetadata(**redis_data)

    @current_broadcast_info.pre_set_hook
    def current_broadcast_info(self, info: CardMetadata):
        """Store card info in Redis."""
        return info._asdict()
    
    @property
    def neutral_card_metadata(self) -> CardMetadata:
        return CardMetadata(
            current_thumbnail=self.current_station.station_thumbnail,
            current_station=self.current_station.html_formated_station_name,
            current_broadcast_title=self.current_station.station_slogan or "Vous écoutez {}".format(self.current_station.station_name),
            current_show_title="",
            current_broadcast_summary="",
        )
    
    @property
    def waiting_for_following_card_metadata(self) -> CardMetadata:
        return CardMetadata(
            current_thumbnail=self.current_station.station_thumbnail,
            current_station=self.current_station.html_formated_station_name,
            current_broadcast_title="Dans un instant : {}".format(self.following_station.station_name),
            current_show_title="",
            current_broadcast_summary="",
        )

    def get_current_broadcast_info(self, current_info: CardMetadata, metadata: MetadataDict, logger: Logger) -> CardMetadata:
        """Return data for displaying broadcast info in player.

        This is for data display in player client. This method uses format_info()
        method of currently broadcasted station.
        """
        metadata_type = metadata["type"]
        if metadata_type in (MetadataType.NONE, MetadataType.ERROR):
            return self.neutral_card_metadata
        if metadata_type == MetadataType.WAITING_FOR_FOLLOWING:
            return self.waiting_for_following_card_metadata
        return self.current_station.format_info(current_info, metadata, logger)

    def get_current_broadcast_metadata(self, current_metadata, logger: Logger, dt: datetime):
        """Get metadata of current broadcasted programm for current station.

        Param: current_metadata: current metadata stored in Redis
        
        This is for pure json data exposure. This method uses get_metadata() method
        of currently broadcasted station. Station can use current metadata for example
        to do partial updates.
        """
        if current_metadata is None:
            current_metadata = {}
        return self.current_station.get_metadata(current_metadata, logger, dt)

    def process(self, logger: Logger, now: datetime, **kwargs):
        """If needed, update metadata.

        - Check if metadata needs to be updated
        - Get metadata and card info with stations methods
        - Apply changements operated by handlers
        - Update metadata in Redis
        - If needed, send SSE and update card info in Redis.

        If card info changed and need to be updated in client, return True.
        Else return False.
        """

        current_metadata = self.current_broadcast_metadata

        if (
            current_metadata is not None
            and now.timestamp() < current_metadata["end"]
            and current_metadata["station"] == self.current_station.station_name
        ):
            self.publish_to_redis("unchanged")
            return False

        current_info = self.current_broadcast_info

        metadata = self.get_current_broadcast_metadata(current_metadata, logger, now)
        info = self.get_current_broadcast_info(current_info, metadata, logger)

        for handler in self.handlers:
            metadata, info = handler.process(metadata, info, logger, now)
        
        self.current_broadcast_metadata = metadata
        if info == self.current_broadcast_info:
            self.publish_to_redis("unchanged")
            return False
        self.current_broadcast_info = info
        self.publish_to_redis("updated")
        logger.debug(f"channel={self.endpoint} station={self.current_station.formated_station_name} Metadata was updated.")
        return True
    
    def get_liquidsoap_config(self):
        """Renvoie une chaîne de caractères à écrire dans le fichier de configuration liquidsoap."""

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
                    line = "    ({{ {} {}-{} }}, {}),\n".format(formated_weekday, formated_start, formated_end, station.formated_station_name)
                    timetable_to_write += line
            timetable_to_write += "])\n\n"
        else:
            timetable_to_write = ""
        
        # output
        fallback = str(self.endpoint) + "_timetable" if timetable_to_write else self.stations[0].formated_station_name
        timetable_to_write += str(self.endpoint) + "_radio = fallback([" + fallback + ", default])\n"    
        timetable_to_write += str(self.endpoint) + '_radio = fallback(track_sensitive=false, [request.queue(id="' + str(self.endpoint) + '_custom_songs"), ' + str(self.endpoint) + '_radio])\n\n'

        output_to_write = "output.icecast(%vorbis(quality=0.6),\n"
        output_to_write += '    host="localhost", port=3333, password="Arkelis77",\n'
        output_to_write += '    mount="{0}", {0}_radio)\n\n'.format(self.endpoint)

        return timetable_to_write, output_to_write
