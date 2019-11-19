# This is Sunflower Radio app.

"""Module containing radio metadata fetching related functions."""

import json
import random
import telnetlib
from datetime import datetime, time, timedelta
import glob

from backports.datetime_fromisoformat import MonkeyPatch
import requests
import mutagen

from sunflower import settings
from sunflower.utils import RedisMixin, Song


class Radio(RedisMixin):
    def __init__(self, logger):
        super().__init__()
        from sunflower.stations import _stations
        self.backup_songs = []
        self.stations = _stations
        self.logger = logger # see watcher.py

    @property
    def current_station_name(self):
        """Return string matching current time according to TIMETABLE dict in settings."""
        return self.get_station_info(datetime.now().time())[2]

    @staticmethod
    def get_station_info(time_):
        """Get info of station playing at given time.
        
        time_ must be datetime.time() instance.
        """
        assert hasattr(settings, "TIMETABLE"), "TIMETABLE not defined in settings."
        timetable = settings.TIMETABLE
        try:
            MonkeyPatch.patch_fromisoformat()
            for t in timetable:
                station = t[2]
                start, end = map(time.fromisoformat, t[:2])
                end = time(23, 59, 59) if end == time(0, 0, 0) else end
                if start < time_ < end:
                    return start, end, station
            else:
                raise RuntimeError("Aucune station programmée à cet horaire.")
        except FileNotFoundError:
            raise RuntimeError("Vous devez créer une configuration d'horaires (fichier timetable.conf).")

    @property
    def current_station(self):
        """Return Station object currently on air."""
        try:
            return self.stations.get(self.current_station_name)()
        except TypeError as exception:
            raise RuntimeError("Station '{}' non gérée.".format(self.current_station_name)) from exception
    
    def get_from_redis(self, key):
        """Get a key from Redis and return it as loaded json.

        If key is empty, return None.
        """
        stored_data = super().get_from_redis(key)
        if stored_data is None:
            return None
        return json.loads(stored_data.decode())
    
    @property
    def current_broadcast_metadata(self):
        """Retrieve metadata stored in Redis as a dict."""
        return self.get_from_redis(self.REDIS_METADATA)

    @current_broadcast_metadata.setter
    def current_broadcast_metadata(self, metadata):
        """Store metadata in Redis."""
        self._redis.set(self.REDIS_METADATA, json.dumps(metadata))

    @property
    def current_broadcast_info(self):
        """Retrieve card info stored in Redis as a dict."""
        return self.get_from_redis(self.REDIS_INFO)

    @current_broadcast_info.setter
    def current_broadcast_info(self, info):
        """Store card info in Redis."""
        self._redis.set(self.REDIS_INFO, json.dumps(info))


    def get_current_broadcast_info(self, metadata):
        """Return data for displaying broadcast info in player.
        
        This is for data display in player client. This method uses format_info()
        method of currently broadcasted station.
        """
        try:
            card_info = self.current_station.format_info(metadata)
            if not card_info["current_broadcast_end"]:
                card_info["current_broadcast_end"] = int(datetime.now().timestamp() + 5) * 1000
        except requests.exceptions.Timeout:
            card_info = {
                "current_thumbnail": self.current_station.station_thumbnail,
                "current_station": self.current_station.station_name,
                "current_broadcast_title": "Métadonnées indisponibles",
                "current_show_title": "Métadonnées indisponibles",
                "current_broadcast_summary": "Les métadonnées n'ont pas pu être récupérées : le serveur de la station demandée a mis trop de temps à répondre.",
                "current_broadcast_end": 0,
            }
        return card_info
    
    def get_current_broadcast_metadata(self):
        """Get metadata of current broadcasted programm for current station.
        
        This is for pure json data exposure. This method uses get_metadata() method
        of currently broadcasted station.
        """
        try:
            metadata = self.current_station.get_metadata()
        except requests.exceptions.Timeout:
            metadata = {"error": "Metadata can't be fetched.", "end": 0}
        metadata.update({"station": self.current_station.station_name})
        return metadata

    def _handle_advertising(self, metadata, info):
        """Play backup songs if advertising is detected on currently broadcasted station."""
        if metadata["type"] == "Publicités":
            self.logger.info("Ads detected.")
            if not self.backup_songs:
                self.backup_songs = self._parse_songs(settings.BACKUP_SONGS_GLOB_PATTERN)
                self.logger.debug("Backup songs list generated:", self.backup_songs)
            backup_song = self.backup_songs.pop(0)
            
            # tell liquidsoap to play backup song
            session = telnetlib.Telnet("localhost", 1234, 100)
            session.write("request.push {}\n".format(backup_song[0]).encode())
            session.close()

            # and update metadata
            metadata = {
                "artist": backup_song[1],
                "title": backup_song[2],
                "end": int(datetime.now().timestamp()) + backup_song[3],
                "type": "Musique",
            }
            info = {
                "current_thumbnail": self.current_station.station_thumbnail,
                "current_station": self.current_station.station_name,
                "current_broadcast_title": backup_song[1] + " • " + backup_song[2],
                "current_show_title": "Musique",
                "current_broadcast_summary": "Publicité en cours sur RTL 2. Dans un instant, retour sur la station.",
                "current_broadcast_end": metadata["end"] * 1000,
            }
        return metadata, info
    
    @staticmethod
    def _parse_songs(glob_pattern):
        """Parse songs matching glob_pattern and return a list of Song objects.
        
        Song object is a namedtuple defined in sunflower.utils module.
        """
        songs = []
        if not glob_pattern.endswith(".ogg"):
            raise RuntimeError("Only ogg files are supported.")
        for path in glob.iglob(glob_pattern):
            file = mutagen.File(path)
            try:
                songs.append(Song(
                    path,
                    file["artist"][0],
                    file["title"][0],
                    int(file.info.length),
                ))
            except KeyError as err:
                raise KeyError("Song file {} must have an artist and a title in metadata.".format(path)) from err
        random.shuffle(songs)
        return songs

    def process_radio(self):
        """Fetch metadata, and if needed do some treatment.
        
        Treatments:
        - play backup song if advertising is detected.
        """
        metadata = self.get_current_broadcast_metadata()
        info = self.get_current_broadcast_info(metadata)
        metadata, info = self._handle_advertising(metadata, info)
        self.current_broadcast_metadata = metadata
        self.current_broadcast_info = info

    