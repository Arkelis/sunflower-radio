import random
from datetime import datetime
from logging import Logger
from typing import Tuple

from sunflower import settings
from sunflower.core.custom_types import CardMetadata, MetadataDict, MetadataType
from sunflower.core.liquidsoap import open_telnet_session
from sunflower.core.mixins import HTMLMixin
from sunflower.utils.deezer import fetch_cover_and_link_on_deezer, parse_songs


class AdsHandler(HTMLMixin):
    def __init__(self, channel):
        self.metadata: MetadataDict = {}
        self.info: CardMetadata = CardMetadata("", "", "", "", "")
        self.channel = channel
        self.glob_pattern = settings.BACKUP_SONGS_GLOB_PATTERN
        self.backup_songs = self._parse_songs()
        self.ads_on_air = False

    def _parse_songs(self):
        new_songs = parse_songs(self.glob_pattern)
        return random.sample(new_songs, len(new_songs))

    def process(
        self,
        metadata: MetadataDict,
        info: CardMetadata,
        logger: Logger,
        dt: datetime
    ) -> Tuple[MetadataDict, CardMetadata]:
        """Play backup songs if advertising is detected on currently broadcasted station."""
        if metadata["type"] != MetadataType.ADS:
            if self.ads_on_air:
                self.ads_on_air = False
                self.metadata = {}
                self.info = CardMetadata("", "", "", "", "")
                with open_telnet_session() as session:
                    session.write(f'{self.channel.endpoint}.skip')
            return metadata, info
        if self.ads_on_air:
            return self.metadata, self.info
        self.ads_on_air = True
        logger.debug(f"channel={self.channel.endpoint} station={self.channel.current_station.formatted_station_name} Ads detected.")
        if not self.backup_songs:
            logger.debug(f"channel={self.channel.endpoint} Backup songs list must be generated.")
            self.backup_songs = self._parse_songs()
        backup_song = self.backup_songs.pop(0)

        # tell liquidsoap to play backup song
        with open_telnet_session(logger=logger) as session:
            session.write(f"{self.channel.endpoint}_custom_songs.push {backup_song.path}\n".encode())

        station = metadata["station"]
        thumbnail, url = fetch_cover_and_link_on_deezer(
            self.channel.current_station.station_thumbnail, backup_song.artist, backup_song.album, backup_song.title
        )

        # and update metadata
        metadata = self.metadata = {
            "artist": backup_song.artist,
            "title": backup_song.title,
            "end": 0,
            "type": MetadataType.MUSIC,
            "station": station,
            "thumbnail_src": thumbnail,
        }
        info = self.info = CardMetadata(
            current_thumbnail=thumbnail,
            current_station=self.channel.current_station.html_formatted_station_name,
            current_broadcast_title=self._format_html_anchor_element(url, backup_song.artist + " • " + backup_song.title),
            current_show_title="Musique",
            current_broadcast_summary="Publicité en cours sur {}. Dans un instant, retour sur la station.".format(station),
        )
        return metadata, info
