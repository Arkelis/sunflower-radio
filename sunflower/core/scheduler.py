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
from sunflower.core.persistence import PersistenceMixin
from sunflower.core.stations import DynamicStation
from sunflower.core.stations import Station


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
            if isinstance(station, DynamicStation)
                and station.keys}

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
            for key in channel.keys:
                channel_data[key] = await self.retrieve_from_repository(channel, key)
            channels_data[channel.__id__] = channel_data

        stations_data = {}
        for station in self.managed_stations:
            for key in station.keys:
                station_data[key] = await self.retrieve_from_repository(station, key)
            stations_data[station.__id__] = station_data

        return {"channels": channels_data,
                "stations": stations_data,
                "now": now}

    async def _persist_context(self, context):
        for processed_obj in (*self.channels, *self.managed_stations):
            for key in processed_obj.keys:
                await self.persist_to_repository(
                    processed_obj,
                    key,
                    context[f"{processed_obj.__data_type__}s"][processed_obj.__id__][key])

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
            stations_updates = dict(await asyncio.gather(
                *(obj.process(self.logger, **context)
                  for obj in self.managed_stations)))
            for station in self.stations:
                context[station.__id__] = stations_updates[station.__id__]

            # next process channels and update context
            channels_updates = dict(await asyncio.gather(
                *(obj.process(self.logger, **context)
                  for obj in self.channels)))
            for channel in self.channels:
                context[channel.__id__] = channels_updates[channel.__id__]

            # then persist context
            await self._persist_context(context)

    # async def _process_and_catch(self, context, obj):
    #     try:
    #         return await obj.process(self.logger, **context)
    #     except Exception as err:
    #         self.logger.error("Une erreur est survenue pendant la mise à jour des données: {}.".format(err))
    #         self.logger.error(traceback.format_exc())
