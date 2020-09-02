import functools
from datetime import date, datetime, time, timedelta
from logging import Logger
from typing import Dict, Iterable, List, Optional, Type

from pydantic import ValidationError

from sunflower import settings
from sunflower.core.bases.stations import Station
from sunflower.core.custom_types import (Broadcast, MetadataEncoder, Step, as_metadata_type)
from sunflower.core.descriptors import PersistentAttribute
from sunflower.core.liquidsoap import open_telnet_session
from sunflower.handlers import Handler


class Channel:
    """Channel.

    Channel object contains and manages stations. It triggers station metadata updates
    thanks to its timetable and its process() method. The latter is called by Scheduler
    object (see scheduler module). Data is persisted to Redis and retrieved by web server
    thanks to view object (see ChannelView in types module).
    """

    data_type = "channel"

    def __init__(self, endpoint, timetable, handlers=()):
        """Channel constructor.

        Parameters:
        - endpoint: string
        - timetable: dict
        - handler: list of classes that can alter metadata and card metadata at channel level after fetching.
        """
        assert endpoint in settings.CHANNELS, f"{endpoint} not mentioned in settings.CHANNELS"
        self.endpoint: str = endpoint
        self.timetable: dict = timetable
        self.handlers: Iterable[Handler] = [handler_cls(self) for handler_cls in handlers]
        self._liquidsoap_station: str = ""
        self._schedule_day: date = date(1970, 1, 1)
        self._last_pull = datetime.today()
        self.long_pull_interval = 10 # seconds between long pulls
        if len(self.stations) == 1:
            self._current_station_instance: Optional[Station] = self.stations[0]()
            self._following_station_instance: Optional[Station] = None
        else:
            self.current_station_start = datetime.now()
            self.current_station_end = datetime.now()
            self._current_station_instance: Optional[Station] = None
            self._following_station_instance: Optional[Station] = None

    @functools.cached_property
    def stations(self) -> tuple:
        """Cached property returning list of stations used by channel."""
        stations = set()
        for l in self.timetable.values():
            for t in l:
                stations.add(t[2])
        return tuple(stations)

    def get_station_info(self, dt: datetime):
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

        asked_time = dt.time()

        # fisrt, select weekday
        week_day = dt.weekday()
        for t in self.timetable:
            if week_day in t:
                key = t
                break
        else:
            raise RuntimeError("Jour de la semaine non supporté.")

        getting_following = False
        asked_station_cls: Optional[Type[Station]] = None
        following_station_cls: Optional[Type[Station]] = None

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
                asked_station_start = datetime.combine(dt.date(), start)
                asked_station_end = datetime.combine(dt.date(), end)
                if asked_station_end < asked_station_start: # cas de minuit
                    asked_station_end += timedelta(hours=24)
                getting_following = True
            else:
                # si on cherche la suivante, on enregistre uniquement la classe
                following_station_cls = t[2]
                break

        # si après avoir parcouru le bon jour on n'a rien trouvé : on lève une erreur
        if asked_station_cls is None:
            raise RuntimeError("Aucune station programmée à cet horaire.")

        # dans le cas où la station courante était le dernier créneau de la journée,
        # on cherche la station suivante dans le premier créneau de la journée suivante.
        if following_station_cls is None:
            week_day = (dt + timedelta(hours=24)).weekday()
            for t in self.timetable:
                if week_day in t:
                    for e in self.timetable[t]:
                        if (station := e[2]) != asked_station_cls:
                            following_station_cls = station
                            break
                    break
            else:
                raise RuntimeError("Jour de la semaine non supporté pour la station suivante : {}. Jours dispos : {}".format(week_day, self.timetable.keys()))

        return asked_station_start, asked_station_end, asked_station_cls, following_station_cls

    def _update_station_instances(self):
        """Update current-station-related attributes.

        - current_station_end
        - current_station_start
        - _current_station_instance (hidden, use 'current_station' property instead to access it)
        - _following_station_instance (hidden, use 'following_station' property instead to access it)
        """

        if len(self.stations) == 1:
            # If only one station, skip.
            return

        if datetime.now() > self.current_station_end or self._current_station_instance is None:
            new_start, new_end, CurrentStationClass, FollowingStationClass = self.get_station_info(datetime.now())
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
    def next_station(self) -> Station:
        """Return next Station object to be on air."""
        self._update_station_instances()
        return self._following_station_instance

    def _post_get_hook_step(self, data: dict):
        try:
            return Step(**data)
        except (TypeError, ValidationError) as err:
            return None

    def _pre_set_hook_step(self, value: Optional[Step]):
        if value is None:
            return value
        return value.dict()

    current_step = PersistentAttribute(
        "current",
        "Current broadcast data",
        MetadataEncoder,
        as_metadata_type,
        notify_change=True,
        post_get_hook=_post_get_hook_step,
        pre_set_hook=_pre_set_hook_step,
    )
    next_step = PersistentAttribute(
        "next",
        "Next broadcast data",
        MetadataEncoder,
        as_metadata_type,
        post_get_hook=_post_get_hook_step,
        pre_set_hook=_pre_set_hook_step,
    )
    schedule = PersistentAttribute("schedule", "Schedule", MetadataEncoder, as_metadata_type)

    @schedule.post_get_hook
    def schedule(self, data: List[Dict]):
        return [Step(**step_data) for step_data in data]

    @schedule.pre_set_hook
    def schedule(self, value: List[Step]):
        return [step.dict() for step in value]

    def get_current_step(self, logger: Logger, now: datetime) -> Step:
        """Get metadata of current broadcasted programm for current station.

        Param: current_metadata: current metadata stored in Redis
        
        This is for pure json data exposure. This method uses get_metadata() method
        of currently broadcasted station. Station can use current metadata for example
        to do partial updates.
        """
        return self.current_station.get_step(logger, now, self)

    def get_next_step(self, logger: Logger, start: datetime, current_broadcast: Broadcast) -> Step:
        station = [
            self.current_station, # current station if start > self.current_station_end == False
            self.next_station, # next station if start > self.current_station_end == True
        ][start > self.current_station_end]
        next_step = station.get_step(logger, start, self, for_schedule=True)
        while next_step.broadcast == current_broadcast:
            next_step = station.get_step(logger, datetime.fromtimestamp(next_step.end), self, for_schedule=True)
        return next_step

    def get_schedule(self, logger: Logger) -> List[Step]:
        """Get list of steps which is the schedule of current day"""
        today = datetime.today()
        schedule: List[Step] = []
        for t, L in self.timetable.items():
            if today.weekday() not in t:
                continue
            for start, end, station_cls in L: # type: str, str, Type[Station]
                start_dt = datetime.combine(today, time.fromisoformat(start))
                end_dt = datetime.combine(today, time.fromisoformat(end))
                end_timestamp = int(end_dt.timestamp())
                # cas de minuit
                if end_dt < start_dt:
                    end_dt = end_dt + timedelta(days=1)
                # on stocke dans une variable la fin provisoire des programme
                tmp_end = start_dt
                while tmp_end < end_dt:
                    new_step = station_cls().get_step(logger, tmp_end, self, for_schedule=True)
                    if new_step.end == new_step.start:
                        new_step.end = int(end_dt.timestamp())
                    if new_step.end > end_timestamp:
                        new_step.end = end_timestamp
                        if new_step.end - new_step.start < 300:
                            break
                    schedule.append(new_step)
                    # on met à jour la fin provisoire
                    tmp_end = datetime.fromtimestamp(new_step.end)
        return schedule

    def update_stream_metadata(self, broadcast: Broadcast, logger: Logger):
        """Send stream metadata to liquidsoap."""
        new_stream_metadata = self.current_station.format_stream_metadata(broadcast)
        if new_stream_metadata is None:
            logger.debug(f"channel={self.endpoint} StreamMetadata is empty")
            return
        with open_telnet_session(logger=logger) as session:
            metadata_string = f'title="{new_stream_metadata.title}",artist="{new_stream_metadata.artist}"'
            session.write(f'{self.endpoint}.insert {metadata_string}\n'.encode())
        logger.debug(f"channel={self.endpoint} {new_stream_metadata} sent to liquidsoap")

    def process(self, logger: Logger, now: datetime, **context):
        """If needed, update metadata.

        - Check if metadata needs to be updated
        - Get metadata and card info with stations methods
        - Apply changes operated by handlers
        - Update metadata in Redis
        - If needed, send SSE and update card info in Redis.

        If card info changed and need to be updated in client, return True.
        Else return False.
        """
        # update schedule if needed
        if now.date() != self._schedule_day:
            logger.info(f"channel={self.endpoint} Updating schedule...")
            self.schedule = self.get_schedule(logger)
            logger.info(f"channel={self.endpoint} Schedule updated!")
            self._schedule_day = now.date()
        # make sure current station is used by liquidsoap
        if (current_station_name := self.current_station.formatted_station_name) != self._liquidsoap_station:
            with open_telnet_session() as session:
                session.write(f'var.set {current_station_name}_on_{self.endpoint} = true\n'.encode())
                if self._liquidsoap_station:
                    session.read_until(b"\n")
                    session.write(f'var.set {self._liquidsoap_station}_on_{self.endpoint} = false\n'.encode())
            self._liquidsoap_station = current_station_name
        # first retrieve current step
        current_step = self.current_step
        # check if we must retrieve new metadata
        if (
            current_step is not None
            and not self.current_station.long_pull
            and now.timestamp() < current_step.end
            and current_step.broadcast.station.name == self.current_station.name
        ) or (
            self.current_station.long_pull
            and (now - self._last_pull).seconds < self.long_pull_interval
        ):
            self.current_step = None # notify unchanged
            return
        self._last_pull = now
        # get current info and new metadata and info
        current_step = self.get_current_step(logger, now)
        self.next_step = self.get_next_step(logger, datetime.fromtimestamp(current_step.end), current_step.broadcast)
        # apply handlers if needed
        for handler in self.handlers:
            current_step = handler.process(current_step, logger, now)
        # update metadata and info if needed
        self.current_step = current_step
        # update stream metadata
        self.update_stream_metadata(current_step.broadcast, logger)
        logger.debug(f"channel={self.endpoint} station={self.current_station.formatted_station_name} Metadata was updated.")

    def get_liquidsoap_config(self):
        """Renvoie une chaîne de caractères à écrire dans le fichier de configuration liquidsoap."""

        # définition des horaires des radios
        if len(self.stations) > 1:
            source_str = f"# {self.endpoint} channel\n"
            for station in self.stations:
                station_name = station.formatted_station_name
                source_str += f'{station_name}_on_{self.endpoint} = interactive.bool("{station_name}_on_{self.endpoint}", false)\n'
            source_str += f'{self.endpoint}_radio = switch(track_sensitive=false, [\n'
            for station in self.stations:
                station_name = station.formatted_station_name
                source_str += f'    ({station_name}_on_{self.endpoint}, {station_name}),\n'
            source_str += "])\n"
        else:
            source_str = ""

        # output
        fallback = str(self.endpoint) + "_radio" if source_str else self.stations[0].formatted_station_name
        source_str += str(self.endpoint) + "_radio = fallback(track_sensitive=false, [" + fallback + ", default])\n"
        source_str += str(self.endpoint) + '_radio = fallback(track_sensitive=false, [request.queue(id="' + str(self.endpoint) + '_custom_songs"), ' + str(self.endpoint) + '_radio])\n'
        source_str += f'{self.endpoint}_radio = server.insert_metadata(id="{self.endpoint}", {self.endpoint}_radio)\n\n'

        output_str = "output.icecast(%vorbis(quality=0.6),\n"
        output_str += '    host="localhost", port=3333, password="Arkelis77",\n'
        output_str += '    mount="{0}", {0}_radio)\n\n'.format(self.endpoint)

        return source_str, output_str
