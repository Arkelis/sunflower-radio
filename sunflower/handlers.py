import abc
import random
from contextlib import suppress
from datetime import datetime
from logging import Logger
from telnetlib import Telnet
from typing import List

from sunflower import settings
from sunflower.core.custom_types import Broadcast, BroadcastType, Song, Step
from sunflower.core.mixins import HTMLMixin
from sunflower.settings import LIQUIDSOAP_TELNET_HOST
from sunflower.utils.music import fetch_cover_and_link_on_deezer, parse_songs


class Handler(abc.ABC):
    @abc.abstractmethod
    def process(self, step: Step, logger: Logger, dt: datetime):
        return NotImplemented


class AdsHandler(Handler, HTMLMixin):
    def __init__(self, channel):
        self.channel = channel
        self.glob_pattern = settings.BACKUP_SONGS_GLOB_PATTERN
        self.backup_songs = self._parse_songs()

    def _parse_songs(self) -> List[Song]:
        new_songs = parse_songs(self.glob_pattern)
        return random.sample(new_songs, len(new_songs))

    def process(
        self,
        step: Step,
        logger: Logger,
        dt: datetime
    ) -> Step:
        """Play backup songs if advertising is detected on currently broadcasted station."""
        if step.broadcast.type != BroadcastType.ADS:
            return step
        logger.debug(f"channel={self.channel.endpoint} station={self.channel.current_station.formatted_station_name} Ads detected.")
        if not self.backup_songs:
            logger.debug(f"channel={self.channel.endpoint} Backup songs list must be generated.")
            self.backup_songs = self._parse_songs()
        backup_song = self.backup_songs.pop(0)

        # tell liquidsoap to play backup song
        with suppress(ConnectionRefusedError):
            with Telnet(LIQUIDSOAP_TELNET_HOST, LIQUIDSOAP_TELNET_HOST) as session:
                session.write(f"{self.channel.endpoint}_custom_songs.push {backup_song.path}\n".encode())

        broadcast = step.broadcast
        thumbnail, url = fetch_cover_and_link_on_deezer(
            self.channel.current_station.station_thumbnail, backup_song.artist, backup_song.album, backup_song.title
        )

        # and update metadata
        return Step(
            start=step.start,
            end=step.start + int(backup_song.length),
            broadcast=Broadcast(
                title=f"{backup_song.artist} • {backup_song.title}",
                type=BroadcastType.MUSIC,
                station=broadcast.station,
                thumbnail_src=thumbnail,
                summary=(f"Publicité en cours sur {broadcast.station.name}. En attendant, voici une chanson de la "
                         "playlist Pycolore."),
                show_title="La playlist Pycolore",
                show_link="/pycolore/playlist/",

            )
        )
