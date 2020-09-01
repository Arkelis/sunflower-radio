# This file is part of sunflower package. radio
# This module contains Scheduler class.

import traceback
from datetime import datetime
from time import sleep
from typing import Any, Dict, List, Set, Union

from sunflower.core.bases import Channel, Station


class Scheduler:

    def __init__(self, channels, logger):
        self.channels: List[Channel] = channels
        self.logger = logger
        # get stations
        self.stations: Set[Station] = {station_cls() for channel in channels for station_cls in channel.stations}
        # get objects to process at each iteration
        objects_to_process: List[Union[Channel, Station]] = []
        # add channels to objects to process
        objects_to_process.extend(self.channels)
        # add stations with process() method to objects to process
        for station in self.stations:
            if hasattr(station, "process"):
                objects_to_process.append(station)
        self.objects_to_process = objects_to_process

    @property
    def context(self) -> Dict[str, Any]:
        """Return context dict containing data needed for channels and station to process.
        
        Current defined keys:
        
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
        channels_using: Dict[Station, List[Channel]] = {
            station: [channel for channel in self.channels if channel.current_station is station]
            for station in self.stations
        }
        channels_using_next: Dict[Station, List[Channel]] = {
            station: [channel for channel in self.channels
                      if (channel.current_station_end - now).seconds < 10
                      if channel.next_station is station]
            for station in self.stations
        }
        return {
            "channels_using": channels_using,
            "channels_using_next": channels_using_next,
            "now": now,
        }

    def run(self):
        """Keep data for radio client up to date."""
        try:
            # loop
            while True:
                sleep(4)
                context = self.context
                for obj in self.objects_to_process:
                    try:
                        obj.process(self.logger, **context)
                    except Exception as err:
                        self.logger.error("Une erreur est survenue pendant la mise à jour des données: {}.".format(err))
                        self.logger.error(traceback.format_exc())
        except Exception as err:
            self.logger.error("Erreur fatale")
            self.logger.error(traceback.format_exc())
