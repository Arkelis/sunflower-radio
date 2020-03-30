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
from sunflower.utils import RedisMixin, Song, CardMetadata, MetadataType, MetadataEncoder, as_metadata_type

CHANNELS = dict()

class Channel(RedisMixin):
    def __init__(self, endpoint, stations, timetable=None):
        """Channel constructor.

        Parameters:
        - endpoint: string
        - stations: list of Station subclasses
        - timetable: dict
        """
        assert endpoint in settings.CHANNELS, "{} not mentionned in settings.CHANNELS".format(endpoint)

        super().__init__()

        self.endpoint = endpoint
        self.stations = stations
        self.timetable = timetable

        if len(self.stations) > 1:
            assert self.timetable is not None, "You must provide a timetable."

        self.backup_songs = []
        self.redis_metadata_key = "sunflower:" + self.endpoint + ":metadata"
        self.redis_info_key = "sunflower:" + self.endpoint + ":info"

        CHANNELS[self.endpoint] = self

    def get_station_info(self, time_):
        """Get info of station playing at given time.

        time_ must be datetime.time() instance.
        """
        MonkeyPatch.patch_fromisoformat()

        # fisrt, select weekday
        week_day = datetime.now().weekday()
        for t in self.timetable:
            # breakpoint()
            if week_day in t:
                key = t
                break
        else:
            raise RuntimeError("Jour de la semaine non supporté.")

        for t in self.timetable[key][::-1]:
            start, end = map(time.fromisoformat, t[:2])
            if time_ < start:
                continue
            station = t[2]
            return start, end, station
        else:
            raise RuntimeError("Aucune station programmée à cet horaire.")

    @property
    def current_station(self):
        """Return Station object currently on air."""
        if len(self.stations) == 1:
            CurrentStationClass = self.stations[0]
        else:
            CurrentStationClass = self.get_station_info(datetime.now().time())[2]
        return CurrentStationClass()

    def get_from_redis(self, key):
        """Get a key from Redis and return it as loaded json.

        If key is empty, return None.
        """
        stored_data = super().get_from_redis(key)
        if stored_data is None:
            return None
        return json.loads(stored_data.decode(), object_hook=as_metadata_type)

    def publish_to_redis(self, metadata):
        channel = self.endpoint
        return super().publish_to_redis(channel, metadata)

    @property
    def current_broadcast_metadata(self):
        """Retrieve metadata stored in Redis as a dict."""
        return self.get_from_redis(self.redis_metadata_key)

    @current_broadcast_metadata.setter
    def current_broadcast_metadata(self, metadata):
        """Store metadata in Redis."""
        self._redis.set(self.redis_metadata_key, json.dumps(metadata, cls=MetadataEncoder))

    @property
    def current_broadcast_info(self) -> CardMetadata:
        """Retrieve card info stored in Redis as a dict."""
        redis_data = self.get_from_redis(self.redis_info_key)
        if redis_data is None:
            return CardMetadata("", "", "", "", "")
        return CardMetadata(**redis_data)

    @current_broadcast_info.setter
    def current_broadcast_info(self, info: CardMetadata):
        """Store card info in Redis."""
        self._redis.set(self.redis_info_key, json.dumps(info._asdict(), cls=MetadataEncoder))
    
    @property
    def neutral_card_metadata(self) -> CardMetadata:
        return CardMetadata(
            current_thumbnail=self.current_station.station_thumbnail,
            current_station=self.current_station.station_name,
            current_broadcast_title="Vous écoutez {}".format(self.current_station.station_name),
            current_show_title="",
            current_broadcast_summary="",
        )

    def get_current_broadcast_info(self, metadata) -> CardMetadata:
        """Return data for displaying broadcast info in player.

        This is for data display in player client. This method uses format_info()
        method of currently broadcasted station.
        """
        if metadata["type"] == MetadataType.NONE:
            return self.neutral_card_metadata
        if metadata.get("error") is not None:
            return CardMetadata(
                current_thumbnail=self.current_station.station_thumbnail,
                current_station=self.current_station.station_name,
                current_broadcast_title="Métadonnées indisponibles",
                current_show_title="Métadonnées indisponibles",
                current_broadcast_summary="Les métadonnées n'ont pas pu être récupérées : le serveur de la station demandée a mis trop de temps à répondre.",
            )
        return self.current_station.format_info(metadata)

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
        if metadata["type"] == MetadataType.ADS:
            self.logger.info("Ads detected.")
            if not self.backup_songs:
                self.logger.info("Backup songs list must be generated.")
                self.backup_songs = self._parse_songs(settings.BACKUP_SONGS_GLOB_PATTERN)
            backup_song = self.backup_songs.pop(0)

            # tell liquidsoap to play backup song
            session = telnetlib.Telnet("localhost", 1234)
            session.write("{}_custom_songs.push {}\n".format(self.endpoint, backup_song.path).encode())
            session.close()
            
            type_ = MetadataType.MUSIC
            station = metadata["station"]
            thumbnail = self.current_station.station_thumbnail
 
            # and update metadata
            metadata = {
                "artist": backup_song[1],
                "title": backup_song[2],
                "end": int(datetime.now().timestamp()) + backup_song[3],
                "type": type_,
                "station": station,
                "thumbnail_src": thumbnail,
            }
            info = CardMetadata(
                current_thumbnail=thumbnail,
                current_station=station,
                current_broadcast_title=backup_song[1] + " • " + backup_song[2],
                current_show_title=type_,
                current_broadcast_summary="Publicité en cours sur RTL 2. Dans un instant, retour sur la station.",
            )
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
        assert hasattr(self, "logger"), "You must provide a logger to call process_radio() method."
        metadata = self.get_current_broadcast_metadata()
        info = self.get_current_broadcast_info(metadata)
        metadata, info = self._handle_advertising(metadata, info)
        if info.current_broadcast_title != self.current_broadcast_info.current_broadcast_title:
            self.current_broadcast_metadata = metadata
            self.current_broadcast_info = info
            self.publish_to_redis("updated")
        else:
            self.publish_to_redis("unchanged")
    
    def get_liquidsoap_config(self):
        """Renvoie une chaîne de caractères à écrire dans le fichier de configuration liquidsoap."""

        used_stations = set()

        # indication nom de la chaîne
        string = "##### " + str(self.endpoint) + " channel #####\n\n"

        # définition des horaires des radios
        if len(self.stations) > 1:
            timetable_to_write = "# timetable\n{}_timetable = switch(track_sensitive=false, [\n".format(self.endpoint)
            for days, timetable in self.timetable.items():
                formated_weekday = (
                    ("(" + " or ".join("{}w".format(wd+1) for wd in days) + ") and")
                    if len(days) > 1
                    else "{}w and".format(days[0]+1)
                )
                for start, end, station in timetable:
                    used_stations.add(station)
                    if start.count(":") != 1 or end.count(":") != 1:
                        raise RuntimeError("Time format must be HH:MM.")
                    formated_start = start.replace(":", "h")
                    formated_end = end.replace(":", "h")
                    formated_name = station.station_name.lower().replace(" ", "")
                    line = "    ({{ {} {}-{} }}, {}),\n".format(formated_weekday, formated_start, formated_end, formated_name)
                    timetable_to_write += line
            timetable_to_write += "])\n\n"
        else:
            used_stations = self.stations
            timetable_to_write = ""
        
        # écriture de l'emploi du temps
        string += timetable_to_write
        
        # output
        fallback = str(self.endpoint) + "_timetable" if timetable_to_write else self.stations[0].station_name.lower().replace(" ", "")
        string += str(self.endpoint) + "_radio = fallback([" + fallback + ", default])\n"    
        string += str(self.endpoint) + '_radio = fallback(track_sensitive=false, [request.queue(id="' + str(self.endpoint) + '_custom_songs"), ' + str(self.endpoint) + '_radio])\n\n'
        string += "# output\n"
        string += "output.icecast(%vorbis(quality=0.6),\n"
        string += '    host="localhost", port=3333, password="Arkelis77",\n'
        string += '    mount="{0}", {0}_radio)\n\n'.format(self.endpoint)

        return used_stations, string


from sunflower.stations import FranceCulture, FranceInfo, FranceInter, FranceMusique, RTL2

tournesol = Channel(
    endpoint="tournesol",
    stations=(FranceCulture, FranceInter, FranceMusique, FranceInfo, RTL2),
    timetable={
        # (weekday1, weekday2, ...)
        (0, 1, 2, 3, 4): [
            # (start, end, station_name),
            ("00:00", "06:00", RTL2),
            ("06:00", "07:00", FranceInfo),
            ("07:00", "09:00", FranceInter),
            ("09:00", "12:30", RTL2),
            ("12:30", "14:30", FranceInter),
            ("14:30", "18:00", RTL2),
            ("18:00", "20:00", FranceInter),
            ("20:00", "21:00", FranceInfo),
            ("21:00", "00:00", RTL2),
        ],
        (5,): [
            ("00:00", "06:00", RTL2),
            ("06:00", "07:00", FranceInfo),
            ("07:00", "09:00", FranceInter),
            ("09:00", "11:00", RTL2),
            ("11:00", "14:00", FranceInter),
            ("14:00", "16:00", RTL2),
            ("16:00", "17:00", FranceCulture),
            ("17:00", "20:00", RTL2),
            ("20:00", "21:00", FranceInfo),
            ("21:00", "00:00", RTL2),
        ],
        (6,): [
            ("00:00", "06:00", RTL2),
            ("06:00", "07:00", FranceInfo),
            ("07:00", "09:00", FranceInter),
            ("09:00", "12:00", RTL2),
            ("12:00", "14:00", FranceInter),
            ("14:00", "16:00", RTL2),
            ("16:00", "18:00", FranceMusique),
            ("18:00", "19:00", RTL2),
            ("19:00", "21:00", FranceInter),
            ("21:00", "00:00", RTL2),
        ]
    },
)

music = Channel("music", (RTL2,))

def write_liquidsoap_config():
    with open("test.liq", "w") as f:
        # config de base (pas de log, activation server telnet, source par défaut)
        f.write("#! /usr/bin/env liquidsoap\n\n")
        f.write("# log file\n")
        f.write('set("log.file", false)\n\n')
        f.write("# activate telnet server\n")
        f.write('set("server.telnet", true)\n\n')
        f.write('# default source\n')
        f.write('default = single("~/radio/franceinfo-long.ogg")\n\n')
        f.write('# streams\n')

        # configuration des chaînes
        # initialisation
        all_channels_string = ""
        used_stations = set()

        # on récupère les infos de chaque chaîne
        for channel in CHANNELS.values():
            stations_used_by_channel, channel_string = channel.get_liquidsoap_config()
            used_stations.update(stations_used_by_channel)
            all_channels_string += channel_string
        
        # on commence par énumérer toutes les stations utilisées
        for station in used_stations:
            url = station.station_url
            formated_name = station.station_name.lower().replace(" ", "")
            f.write('{} = mksafe(input.http("{}"))\n'.format(formated_name, url))
        
        # puis on écrit les output
        f.write("\n" + all_channels_string)
