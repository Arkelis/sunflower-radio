from contextlib import suppress
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from logging import Logger
from telnetlib import Telnet
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type

from pydantic import ValidationError
from sunflower.core.custom_types import Broadcast
from sunflower.core.custom_types import MetadataEncoder
from sunflower.core.custom_types import Step
from sunflower.core.custom_types import UpdateInfo
from sunflower.core.custom_types import as_metadata_type
from sunflower.core.persistence import PersistenceMixin
from sunflower.core.persistence import PersistentAttribute
from sunflower.core.persistence import Repository
from sunflower.core.stations import Station
from sunflower.core.timetable import Timetable
from sunflower.handlers import Handler
from sunflower.settings import LIQUIDSOAP_TELNET_HOST
from sunflower.settings import LIQUIDSOAP_TELNET_PORT


class Channel(PersistenceMixin):
    """Channel.

    Channel object contains and manages stations. It triggers station metadata updates
    thanks to its timetable and its process() method. The latter is called by Scheduler
    object (see scheduler module). Data is persisted to Redis and retrieved by web server
    thanks to view object (see ChannelView in types module).
    """

    data_type = "channel"

    def __init__(self, id: str, repository: "Repository", timetable_dict: dict, handlers: Tuple[Type[Handler]]=()):
        """Channel constructor.

        Parameters:
        - id: string
        - timetable: dict
        - handler: list of classes that can alter metadata and card metadata at channel level after fetching.
        """
        super().__init__(repository, id)
        self.timetable = Timetable(timetable_dict)
        self.handlers: Iterable[Handler] = [handler_cls(self) for handler_cls in handlers]
        self._liquidsoap_station: str = ""
        self._schedule_day: date = date(1970, 1, 1)
        self._last_pull = datetime.today()
        self.long_pull_interval = 10  # seconds between long pulls
        if len(self.stations) == 1:
            self._current_station: Optional[Station] = self.stations[0]()
            self._following_station: Optional[Station] = None
        else:
            self.current_station_start = datetime.now()
            self.current_station_end = datetime.now()
            self._current_station: Optional[Station] = None
            self._following_station: Optional[Station] = None

    @property
    def stations(self) -> tuple:
        """Cached property returning list of stations used by channel."""
        return self.timetable.stations

    def station_at(self, dt: datetime) -> Station:
        """Return Station object currently on air."""
        return self.timetable.station_at(dt)

    def station_end_at(self, dt: datetime) -> datetime:
        """Return the time when current station will be switched"""
        return self.timetable.end_of_slot_at(dt)

    def station_after(self, dt: datetime) -> Station:
        """Return next Station object to be on air."""
        return self.timetable.station_after(dt)

    # noinspection PyMethodMayBeStatic
    def _post_get_hook_step(self, data: dict):
        try:
            return Step(**data)
        except (TypeError, ValidationError) as err:
            return Step.none()

    # noinspection PyMethodMayBeStatic
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

    def get_current_step(self, logger: Logger, now: datetime) -> UpdateInfo:
        """Get metadata of current broadcasted programm for current station.

        Param: current_metadata: current metadata stored in Redis
        
        This is for pure json data exposure. This method uses get_metadata() method
        of currently broadcasted station. Station can use current metadata for example
        to do partial updates.
        """
        return self.station_at(now).get_step(logger, now, self)

    def get_next_step(self, logger: Logger, start: datetime) -> Step:
        station = [
            self.station_at(start),  # current station if start > self.current_station_end == False
            self.station_after(start),  # next station if start > self.current_station_end == True
        ][start >= self.current_station_end]
        next_step = station.get_next_step(logger, start, self)
        if next_step.end == next_step.start:
            next_step.end = int(self.current_station_end.timestamp())
        if (next_step.is_none()) or (
            next_step.end > (self.current_station_end.timestamp() + 300)
            and next_step.broadcast.station == self.station_at(start).station_info
        ):
            next_step = self.station_after(start).get_next_step(logger, self.current_station_end, self)
        next_step.start = min(next_step.start, int(self.current_station_end.timestamp()))
        return next_step

    def get_schedule(self, logger: Logger) -> List[Step]:
        """Get list of steps which is the schedule of current day"""
        today = datetime.today()
        schedule: List[Step] = []
        for t, L in self.timetable.items():
            if today.weekday() not in t:
                continue
            for start, end, station in L:  # type: str, str, Type[Station]
                start_dt = datetime.combine(today, time.fromisoformat(start))
                end_dt = datetime.combine(today, time.fromisoformat(end))
                # cas de minuit
                if end_dt < start_dt:
                    end_dt = end_dt + timedelta(days=1)
                # on stocke dans une variable la fin provisoire des programme
                schedule += station.get_schedule(logger, start_dt, end_dt)
                # on met à jour la fin provisoire
        return schedule

    def update_stream_metadata(self, broadcast: Broadcast, logger: Logger):
        """Send stream metadata to liquidsoap."""
        new_stream_metadata = self.station_at.format_stream_metadata(broadcast)
        if new_stream_metadata is None:
            logger.debug(f"channel={self.id} StreamMetadata is empty")
            return
        with suppress(ConnectionRefusedError):
            with Telnet(LIQUIDSOAP_TELNET_HOST, LIQUIDSOAP_TELNET_PORT) as session:
                metadata_string = f'title="{new_stream_metadata.title}",artist="{new_stream_metadata.artist}"'
                session.write(f"{self.id}.insert {metadata_string}\n".encode())
        logger.debug(f"channel={self.id} {new_stream_metadata} sent to liquidsoap")

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
            logger.info(f"channel={self.id} Updating schedule...")
            self.schedule = self.get_schedule(logger)
            logger.info(f"channel={self.id} Schedule updated!")
            self._schedule_day = now.date()
        # make sure current station is used by liquidsoap
        if (current_station_name := self.station_at.formatted_station_name) != self._liquidsoap_station:
            with suppress(ConnectionRefusedError):
                with Telnet(LIQUIDSOAP_TELNET_HOST, LIQUIDSOAP_TELNET_PORT) as session:
                    session.write(f"var.set {current_station_name}_on_{self.id} = true\n".encode())
                    if self._liquidsoap_station:
                        session.read_until(b"\n")
                        session.write(f"var.set {self._liquidsoap_station}_on_{self.id} = false\n".encode())
            self._liquidsoap_station = current_station_name
        # first retrieve current step
        current_step = self.current_step
        # check if we must retrieve new metadata
        if (
            current_step is not None
            and not self.station_at.long_pull
            and now.timestamp() < current_step.end
            and current_step.broadcast.station.name == self.station_at.name
        ) or (self.station_at.long_pull and (now - self._last_pull).seconds < self.long_pull_interval):
            self.current_step = None  # notify unchanged
            return
        self._last_pull = now
        # get current info and new metadata and info
        should_notify, current_step = self.get_current_step(logger, now)
        if not should_notify:
            return
        self.next_step = self.get_next_step(logger, datetime.fromtimestamp(current_step.end))
        # apply handlers if needed
        for handler in self.handlers:
            current_step = handler.process(current_step, logger, now)
        # update metadata and info if needed
        self.current_step = current_step
        # update stream metadata
        self.update_stream_metadata(current_step.broadcast, logger)
        logger.debug(
            f"channel={self.id} station={self.station_at.formatted_station_name} Metadata was updated."
        )

    def get_liquidsoap_config(self):
        """Renvoie une chaîne de caractères à écrire dans le fichier de configuration liquidsoap."""

        # définition des horaires des radios
        if len(self.stations) > 1:
            source_str = f"# {self.id} channel\n"
            for station in self.stations:
                station_name = station.formatted_station_name
                source_str += f'{station_name}_on_{self.id} = interactive.bool("{station_name}_on_{self.id}", false)\n'
            source_str += f"{self.id}_radio = switch(track_sensitive=false, [\n"
            for station in self.stations:
                station_name = station.formatted_station_name
                source_str += f"    ({station_name}_on_{self.id}, {station_name}),\n"
            source_str += "])\n"
        else:
            source_str = ""

        # output
        fallback = str(self.id) + "_radio" if source_str else self.stations[0].formatted_station_name
        source_str += str(self.id) + "_radio = fallback(track_sensitive=false, [" + fallback + ", default])\n"
        source_str += (
            str(self.id)
            + '_radio = fallback(track_sensitive=false, [request.queue(id="'
            + str(self.id)
            + '_custom_songs"), '
            + str(self.id)
            + "_radio])\n"
        )
        source_str += (f'{self.id}_radio = server.insert_metadata(id="{self.id}", '
                       f'drop_metadata({self.id}_radio))\n\n')

        output_str = "output.icecast(%vorbis(quality=0.6),\n"
        output_str += '    host="localhost", port=3333, password="Arkelis77",\n'
        output_str += '    mount="{0}", {0}_radio)\n\n'.format(self.id)

        return source_str, output_str
