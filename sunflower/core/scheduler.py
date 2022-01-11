# This file is part of sunflower package. radio
# This module contains Scheduler class.
import asyncio
import time
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Set

from sunflower.core.channel import Channel
from sunflower.core.custom_types import NotifyChangeStatus
from sunflower.core.persistence import PersistenceMixin
from sunflower.core.persistence import PersistentAttributesObject
from sunflower.core.stations import Station


def is_not_none(x):
    return x is not None


class Scheduler(PersistenceMixin):
    def __init__(self, channels, repository, logger):
        self.repository = repository
        self.channels: List[Channel] = channels
        self.logger = logger
        # get stations
        self.stations: Set[Station] = {
            station
            for channel in channels
            for station in channel.stations}
        self.managed_stations = {
            station
            for station in self.stations
            if isinstance(station, PersistentAttributesObject)}

    async def _retrieve_context(self) -> Dict[str, Any]:
        """Return context dict containing data needed for channels and station to process.
        
        Current defined keys:
        - now
        - channels:
          - name:
            - current
            - next
            - schedule
        -stations:
          - name:
            - key
        - `channels_using` (Dict[Station, List[Channel]]): 
            a dict containing key=station, value=list of channels objects where station is currently
            on air on these channels. This key allows station to know on which channels they
            are currently used.
        - `channels_using_next` (Dict[Station, List[Channel]]):
            a dict containing key=station, value=list of channels objects where station will be on air on these
            channels in less than 10 seconds. This key allows station to know on which channels they will
            be used.
        - `now`: datetime object representing current timestamp.
        """
        now = datetime.now()

        channels_data = {}
        for channel in self.channels:
            channel_data = {}
            for key in channel.__keys__:
                channel_data[key] = await self.retrieve_from_repository(channel, key)
            channels_data[channel.__id__] = channel_data

        stations_data = {}
        for station in self.managed_stations:
            station_data = {}
            for key in station.__keys__:
                station_data[key] = await self.retrieve_from_repository(station, key)
            stations_data[station.__id__] = station_data

        return {
            "channels": channels_data,
            "stations": stations_data,
            "now": now}

    async def _persist_context(self, context):
        for processed_obj in (*context["stations"].values(), *context["channels"].values()):
            for key, val in processed_obj.items():
                await self.persist_to_repository(processed_obj, key, val)
            await self.publish_to_repository(processed_obj, "updates", NotifyChangeStatus.UPDATED.value)

    async def run(self):
        """Keep metadata up to date and persist them.

        First update managed stations context. It is necessary if used by a channel.
        Next update channels context. This may be used newly updated stations context.
        """
        while True:
            time.sleep(4)

            # retrive context from persistence repo
            context = await self._retrieve_context()

            # first process stations and update context
            # will be used by channels
            stations_updates = dict(filter(is_not_none,
                await asyncio.gather(
                    *(obj.process(self.logger, **context)
                      for obj in self.managed_stations))))
            for station_id in stations_updates.keys():
                context["stations"][station_id] = stations_updates[station_id]

            # next process channels and update context
            channels_updates = dict(filter(is_not_none,
                await asyncio.gather(
                    *(obj.process(self.logger, **context)
                      for obj in self.channels))))
            for channel_id in channels_updates.keys():
                context["channels"][channel_id] = channels_updates[channel_id]

            # then persist context
            await self._persist_context(context)
