# This file is part of sunflower package. radio
# This module contains Scheduler class.

import traceback
from datetime import datetime
from time import sleep
from typing import Any, Dict, List

from sunflower.core.bases import Channel, DynamicStation, Station


class Scheduler:

    def __init__(self, channels, logger):
        self.channels = channels
        self.logger = logger

        # get stations
        self.stations = {Station() for channel in channels for Station in channel.stations}

        # get objects to process at each iteration
        objects_to_process = []

        # add logger to channels
        # add channels to objects to process
        for channel in self.channels:
            channel.logger = logger
            objects_to_process.append(channel)
        
        # add logger to dynamic stations
        # add dynamic stations to objects to process
        for station in self.stations:
            if isinstance(station, DynamicStation):
                station.logger = logger
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
        - `now`: datetime object representing current timestamp.
        """
        channels_using: Dict[Station, List[Channel]] = {
            station: [channel for channel in self.channels if channel.current_station is station]
            for station in self.stations
        }
        return {
            "channels_using": channels_using,
            "now": datetime.now(),
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
