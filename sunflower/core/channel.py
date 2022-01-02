import itertools
import traceback
from datetime import date
from datetime import datetime
from logging import Logger
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type

from pydantic import ValidationError

from sunflower.core.config import K
from sunflower.core.custom_types import Step
from sunflower.core.custom_types import StreamMetadata
from sunflower.core.custom_types import UpdateInfo
from sunflower.core.liquidsoap import liquidsoap_telnet_session
from sunflower.core.persistence import MetadataEncoder
from sunflower.core.persistence import PersistenceMixin
from sunflower.core.persistence import PersistentAttribute
from sunflower.core.persistence import as_metadata_type
from sunflower.core.repository import Repository
from sunflower.core.stations import Station
from sunflower.core.timetable import Timetable
from sunflower.handlers import Handler


class Channel(PersistenceMixin):
    """Channel.

    Channel object contains and manages stations. It triggers station metadata updates
    thanks to its timetable and its process() method. The latter is called by Scheduler
    object (see scheduler module). Data is persisted to Redis and retrieved by web server
    thanks to view object (see ChannelView in types module).
    """

    data_type = "channel"

    def __init__(self,
                 __id: str,
                 name: str,
                 repository: "Repository",
                 timetable: Timetable,
                 handlers: Tuple[Type[Handler]] = ()):
        """Channel constructor.

        Parameters:
        - id: string
        - timetable: dict
        - handler: list of classes that can alter metadata and card metadata at channel level after fetching.
        """
        super().__init__(repository, __id)
        self.name = name
        self.timetable = timetable
        self.handlers: Iterable[Handler] = [handler_cls(self) for handler_cls in handlers]
        self._liquidsoap_station: str = ""
        self._schedule_day: date = date(1970, 1, 1)
        self._last_pull = datetime.today()
        self.long_pull_interval = 10  # seconds between long pulls

    @classmethod
    def fromconfig(cls,
                   repository: "Repository",
                   config: Dict,
                   stations_map: Dict[str, Station],
                   handlers_map: Dict[str, Type[Handler]]):
        channel_name = config[K("name")]
        channel_id = config[K("id")]
        channel_timetable = Timetable.fromconfig(config[K("timetable")], stations_map)
        channel_handlers = tuple(handlers_map[name] for name in config[K("handlers")])
        return cls(channel_id, channel_name, repository, channel_timetable, channel_handlers)

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
        try:
            return self.station_at(now).get_step(logger, now, self)
        except Exception as err:
            logger.error("Erreur lors de la récupération du step")
            logger.error(traceback.fromat_exc())
            return Step.empty(now, self.station_at(now))

    def get_next_step(self, logger: Logger, start: datetime) -> Step:
        try:
            current_station_end = self.station_end_at(dt=start)
            station = [
                self.station_at(start),  # current station if start > self.current_station_end == False
                self.station_after(start),  # next station if start > self.current_station_end == True
            ][start >= current_station_end]
            next_step = station.get_next_step(logger, start, self)
            if next_step.end == next_step.start:
                next_step.end = int(current_station_end.timestamp())
            if (next_step.is_none()) or (
                next_step.end > (current_station_end.timestamp() + 300)
                and next_step.broadcast.station == self.station_at(start).station_info
            ):
                next_step = self.station_after(start).get_next_step(logger, current_station_end, self)
            next_step.start = min(next_step.start, int(current_station_end.timestamp()))
            return next_step
        except Exception as err:
            logger.error("Erreur lors de la récupération du step")
            logger.error(traceback.fromat_exc())
            return Step.empty(now, self.station_at(now))


    def get_schedule(self, logger: Logger) -> List[Step]:
        """Get list of steps which is the schedule of current day"""
        return list(itertools.chain(*(
            slot.station.get_schedule(logger, slot.start, slot.end)
            for slot in self.timetable.resolved_timetable_of(datetime.today()))))

    def send_metadata_to_liquidsoap(self, stream_metadata: StreamMetadata, logger: Logger):
        """Send stream metadata to liquidsoap."""
        if stream_metadata is None:
            logger.debug(f"channel={self.id} StreamMetadata is empty")
            return
        with liquidsoap_telnet_session() as session:
            session.write(f'var.set {self.id}_artist = "{stream_metadata.artist}"\n'.encode())
            session.read_until(b"\n")
            session.write(f'var.set {self.id}_title = "{stream_metadata.title}"\n'.encode())
            session.read_until(b"\n")
            session.write(f'var.set {self.id}_album = "{stream_metadata.album}"\n'.encode())
            session.read_until(b"\n")
        logger.debug(f"channel={self.id} {stream_metadata} sent to liquidsoap")
        return

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
        # temporary fix waiting for new RTL2 Fix
        # try:
        #     if now.date() != self._schedule_day:
        #         logger.info(f"channel={self.id} Updating schedule...")
        #         self.schedule = self.get_schedule(logger)
        #         logger.info(f"channel={self.id} Schedule updated!")
        #         self._schedule_day = now.date()
        # except:
        #     logger.warn("Error when fetching schedule. Passing.")
        #     pass

        current_station = self.station_at(now)

        # make sure current station is used by liquidsoap
        if (current_station_name := current_station.formatted_station_name) != self._liquidsoap_station:
            with liquidsoap_telnet_session() as session:
                session.write(f"var.set {current_station_name}_on_{self.id} = true\n".encode())
                session.read_until(b"\n")
                if self._liquidsoap_station:
                    session.write(f"var.set {self._liquidsoap_station}_on_{self.id} = false\n".encode())
                    session.read_until(b"\n")
            self._liquidsoap_station = current_station_name
        # first retrieve current step
        current_step = self.current_step
        # check if we must retrieve new metadata
        if ((current_step is not None
                and not current_station.long_pull
                and now.timestamp() < current_step.end
                and current_step.broadcast.station.name == current_station.name)
            or (current_station.long_pull
                and (now - self._last_pull).seconds < self.long_pull_interval)):
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
        new_stream_metadata = current_station.format_stream_metadata(current_step.broadcast)
        self.send_metadata_to_liquidsoap(new_stream_metadata, logger)
        logger.debug(
            f"channel={self.id} "
            f"station={current_station.formatted_station_name} "
            f"Metadata was updated.")
