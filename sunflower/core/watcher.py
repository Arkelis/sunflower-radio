# This file is part of sunflower package. radio
# This module contains Watcher class.

import traceback
from datetime import datetime
from time import sleep

from sunflower.core.mixins import RedisMixin
from sunflower.core.bases import DynamicStation

class Watcher(RedisMixin):

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
    def context(self):
        """return context dict containing data needed for channels and station to process.
        
        Current defined keys:
        - channels_using: a dict containing key=station, value=channel object where station is currently
                          on air on this channel. This key allows station to know on which channels they
                          are currently used.
        """
        channels_using = {}
        for station in self.stations:
            channels_using_station = []
            for channel in self.channels:
                if channel.current_station is station:
                    channels_using_station.append(channel)
            channels_using[station] = channels_using_station
        return {
            "channels_using": channels_using
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
