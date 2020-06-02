import telnetlib
from datetime import datetime
import random
from typing import Tuple, Dict

from sunflower import settings
from sunflower.core.types import CardMetadata, MetadataType, MetadataDict
from sunflower.utils.functions import fetch_cover_and_link_on_deezer, parse_songs
from sunflower.core.mixins import HTMLMixin


class AdsHandler(HTMLMixin):
    def __init__(self, channel):
        self.channel = channel
        self.glob_pattern = settings.BACKUP_SONGS_GLOB_PATTERN
        self.backup_songs = self._parse_songs()

    def _parse_songs(self):
        new_songs = parse_songs(self.glob_pattern)
        return random.sample(new_songs, len(new_songs))

    def process(self, metadata, info, logger, dt: datetime) -> Tuple[MetadataDict, CardMetadata]:
        """Play backup songs if advertising is detected on currently broadcasted station."""
        if metadata["type"] == MetadataType.ADS:
            logger.debug(f"channel={self.channel.endpoint} station={self.channel.current_station.formated_station_name} Ads detected.")
            if not self.backup_songs:
                logger.debug(f"channel={self.channel.endpoint} Backup songs list must be generated.")
                self.backup_songs = self._parse_songs()
            backup_song = self.backup_songs.pop(0)

            # tell liquidsoap to play backup song
            session = telnetlib.Telnet("localhost", 1234)
            session.write("{}_custom_songs.push {}\n".format(self.channel.endpoint, backup_song.path).encode())
            session.write("exit\n".encode())
            session.close()
            
            station = metadata["station"]
            thumbnail, url = fetch_cover_and_link_on_deezer(
                self.channel.current_station.station_thumbnail, backup_song.artist, backup_song.album, backup_song.title
            )

            # and update metadata
            metadata = {
                "artist": backup_song.artist,
                "title": backup_song.title,
                "end": int(dt.timestamp() + backup_song.length),
                "type": MetadataType.MUSIC,
                "station": station,
                "thumbnail_src": thumbnail,
            }
            info = CardMetadata(
                current_thumbnail=thumbnail,
                current_station=self.channel.current_station.html_formated_station_name,
                current_broadcast_title=self._format_html_anchor_element(url, backup_song.artist + " • " + backup_song.title),
                current_show_title="Musique",
                current_broadcast_summary="Publicité en cours sur {}. Dans un instant, retour sur la station.".format(station),
            )
        return metadata, info
