# This is Sunflower Radio app.

"""Module containing radio metadata fetching related functions."""

import os
import random
import telnetlib
from abc import ABC
from time import sleep
from datetime import datetime, time, timedelta

import requests

from sunflower import settings


class Radio:

    def __init__(self):
        from sunflower.stations import _stations
        self.backup_songs = random.shuffle(settings.BACKUP_SONGS)
        self.stations = _stations
        self.current_broadcast_metadata = self.get_current_broadcast_metadata()
        self.current_broadcast_info = self.get_current_broadcast_info()

    @property
    def current_station_name(self):
        """Returning string matching current time according to TIMETABLE dict in settings."""
        assert hasattr(settings, "TIMETABLE"), "TIMETABLE not defined in settings."
        current_time = datetime.now().time()
        timetable = settings.TIMETABLE
        try:
            for t in timetable:
                station = t[2]
                start, end = map(time.fromisoformat, t[:2])
                end = time(23, 59, 59) if end == time(0, 0, 0) else end
                if start < current_time < end:
                    return station
            else:
                raise RuntimeError("Aucune station programmée à cet horaire.")
        except FileNotFoundError:
            raise RuntimeError("Vous devez créer une configuration d'horaires (fichier timetable.conf).")
    
    @property
    def current_station(self):
        try:
            return self.stations.get(self.current_station_name)()
        except TypeError as exception:
            raise RuntimeError("Station '{}' non gérée.".format(self.current_station_name)) from exception

    
    def get_current_broadcast_metadata(self):
        """Return metadata of current broadcasted programm for current station.
        
        This is for pure json data exposure.
        """
        try:
            metadata = self.current_station.get_metadata()
        except requests.exceptions.Timeout:
            metadata = {"error": "Metadata can't be fetched."}
        metadata.update({"station": self.current_station.station_name})
        return metadata
    
    def get_current_broadcast_info(self):
        """Return data for displaying broadcast info in player.
        
        This is for data display in player client.
        """
        try:
            card_info = self.current_station.format_info()
            if not card_info["current_broadcast_end"]:
                card_info["current_broadcast_end"] = int(datetime.now().timestamp() + 5) * 1000
        except requests.exceptions.Timeout:
            card_info = {
                "current_thumbnail": self.current_station.station_thumbnail,
                "current_station": self.current_station.station_name,
                "current_broadcast_title": "Métadonnées indisponibles",
                "current_show_title": "Métadonnées indisponibles",
                "current_broadcast_summary": "Les métadonnées n'ont pas pu être récupérées : le serveur de la station demandée a mis trop de temps à répondre.",
                "current_broadcast_end": False,
            }
        return card_info

    def _time_to_sleep(self):
        now = datetime.now().timestamp()
        end = self.current_broadcast_metadata["end"]
        if not end or now > end:
            return 5
        return end - now
    
    def _handle_advertising(self):
        if self.current_broadcast_metadata["type"] == "Publicités":
            if not self.backup_songs:
                self.backup_songs = random.shuffle(settings.BACKUP_SONGS)
            backup_song = self.backup_songs.pop(0)
            session = telnetlib.Telnet("localhost", 1234, 100)
            session.write(b"request.push {}".fromat(backup_song[0]))
            session.close()
            self.current_broadcast_metadata = {
                "artist": backup_song[1],
                "title": backup_song[2],
                "end": int(datetime.now().timestamp() + backup_song[3])
            }
            self.current_broadcast_info = {
                "current_thumbnail": self.current_station.station_thumbnail,
                "current_station": self.current_station.station_name,
                "current_broadcast_title": backup_song[1] + " &bull; " + backup_song[2],
                "current_show_title": "Musique",
                "current_broadcast_summary": "Publicité en cours sur RTL 2. Dans un instant, retour sur la station.",
                "current_broadcast_end": self.current_broadcast_metadata["end"],
            }

    def watch(self):
        while True:
            self.current_broadcast_metadata = self.get_current_broadcast_metadata()
            self.current_broadcast_info = self.get_current_broadcast_info()
            self._handle_advertising()
            sleep(self._time_to_sleep())
