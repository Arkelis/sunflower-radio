import abc
import random
from datetime import datetime
from logging import Logger
from typing import List

from sunflower.core.config import K
from sunflower.core.config import get_config
from sunflower.core.custom_types import Broadcast
from sunflower.core.custom_types import BroadcastType
from sunflower.core.custom_types import Song
from sunflower.core.custom_types import Step
from sunflower.core.liquidsoap import liquidsoap_telnet_session
from sunflower.utils.music import fetch_cover_and_link_on_deezer
from sunflower.utils.music import parse_songs


class Handler(abc.ABC):
    def __init__(self, channel):
        self.channel = channel

    @abc.abstractmethod
    def process(self, step: Step, logger: Logger, dt: datetime):
        return NotImplemented


class AdsHandler(Handler):
    def __init__(self, channel):
        super().__init__(channel)
        self.glob_pattern = get_config()[K("backup-songs-glob-pattern")]
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
        logger.debug(f"channel={self.channel.id} station={self.channel.station_at(dt).formatted_station_name} Ads detected.")
        if not self.backup_songs:
            logger.debug(f"channel={self.channel.id} Backup songs list must be generated.")
            self.backup_songs = self._parse_songs()
        backup_song = self.backup_songs.pop(0)

        # tell liquidsoap to play backup song
        with liquidsoap_telnet_session() as session:
            session.write(f"{self.channel.id}_custom_songs.push {backup_song.path}\n".encode())

        broadcast = step.broadcast
        thumbnail, url = fetch_cover_and_link_on_deezer(
            self.channel.station_at(dt).station_thumbnail, backup_song.artist, backup_song.album, backup_song.title
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
