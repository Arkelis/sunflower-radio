import random
from datetime import datetime
from datetime import timedelta
from logging import Logger
from typing import Dict
from typing import List
from typing import Optional

from sunflower.core.channel import Channel
from sunflower.core.config import K
from sunflower.core.config import get_config
from sunflower.core.custom_types import Broadcast
from sunflower.core.custom_types import BroadcastType
from sunflower.core.custom_types import Song
from sunflower.core.custom_types import SongPayload
from sunflower.core.custom_types import Step
from sunflower.core.custom_types import StreamMetadata
from sunflower.core.custom_types import UpdateInfo
from sunflower.core.liquidsoap import liquidsoap_telnet_session
from sunflower.core.persistence import PersistentAttribute
from sunflower.core.stations import DynamicStation
from sunflower.utils.music import fetch_cover_and_link_on_deezer
from sunflower.utils.music import parse_songs
from sunflower.utils.music import prevent_consecutive_artists


class PycolorePlaylistStation(DynamicStation):
    station_thumbnail = "https://www.pycolore.fr/assets/img/sunflower-dark-min.jpg"
    name = "Radio Pycolore"
    id = "pycolore"
    public_playlist = PersistentAttribute("playlist")

    @public_playlist.pre_set_hook
    def public_playlist(self, songs: List[Song]):
        """Persist public fields of song objects in current playlist in redis."""
        return [
            {"artist": song.artist, "title": song.title, "album": song.album}
            for song in songs]

    def __init__(self, repository):
        super().__init__(repository, self.id)
        self._songs_to_play: List[Song] = []
        # self._populate_songs_to_play()
        self._current_song: Optional[Song] = None
        self._current_song_end: float = 0
        self._end_of_use: datetime = datetime.now()

    def _populate_songs_to_play(self):
        new_songs = parse_songs(get_config()[K("backup-songs-glob-pattern")])
        self.public_playlist = new_songs
        self._songs_to_play += random.sample(new_songs, len(new_songs))
        self._songs_to_play = prevent_consecutive_artists(self._songs_to_play)

    def _get_next_song(self, max_length: float):
        """Get next song in current playlist.

        Check if its length is not greater than remaining time before end of use
        of this station. Set max_length to -1 if you want to skip this behaviour.
        """
        if len(self._songs_to_play) <= 5:
            self._populate_songs_to_play()
        for (i, song) in enumerate(self._songs_to_play):
            if song.length < max_length or max_length == -1:
                return self._songs_to_play.pop(i)
        return None

    @property
    def _artists(self) -> List[str]:
        """Property returning artists of the 5 next-played songs."""
        artists_list = []
        for song in self._songs_to_play:
            if song.artist not in artists_list:
                artists_list.append(song.artist)
            if len(artists_list) == 5:
                break
        return artists_list
        
    def _play(self, delay: float, max_length: float, logger: Logger, now: datetime):
        """Play next song in playlist.
        
        Call _get_next_song() for getting next song to play.
        If max_length == -1, _get_next_song does not care about max length.
        Send a request to liquidsoap telnet server telling it to play the song.
        """
        self._current_song = self._get_next_song(max_length)
        if self._current_song is None:
            self._current_song_end = now.timestamp() + max_length
            return
        logger.debug(
            f"station={self.formatted_station_name} "
            f"Playing {self._current_song.artist} "
            f"- {self._current_song.title} "
            f"({len(self._songs_to_play)} songs remaining in current list)."
        )
        self._current_song_end = (now + timedelta(seconds=self._current_song.length)).timestamp() + delay
        with liquidsoap_telnet_session() as session:
            session.write(f"{self.formatted_station_name}.push {self._current_song.path}\n".encode())

    def get_step(self, logger: Logger, dt: datetime, channel: Channel) -> UpdateInfo:
        dt_timestamp = int(dt.timestamp())
        if self._current_song is None:
            next_station_name = channel.station_after(dt).name
            next_station_start = int(channel.station_end_at(dt).timestamp())
            return UpdateInfo(
                should_notify_update=True,
                step=Step.waiting_for_next_station(dt_timestamp, next_station_start, self, next_station_name)
            )
        artists_list = tuple(self._artists)
        artists_str = ", ".join(artists_list[:-1]) + " et " + artists_list[-1]
        thumbnail_src, link = fetch_cover_and_link_on_deezer(
            self.station_thumbnail,
            self._current_song.artist,
            self._current_song.album,
            self._current_song.title
        )
        return UpdateInfo(should_notify_update=True, step=Step(
            start=dt_timestamp,
            end=int(self._current_song_end),
            broadcast=Broadcast(
                title=f"{self._current_song.artist} • {self._current_song.title}",
                link=link,
                thumbnail_src=thumbnail_src,
                station=self.station_info,
                type=BroadcastType.MUSIC,
                show_link="https://radio.pycolore.fr/pages/playlist-pycolore",
                show_title="La playlist Pycolore",
                summary=(f"Une sélection aléatoire de chansons parmi les musiques stockées sur Pycolore. À suivre : "
                         f"{artists_str}."),
                metadata=SongPayload(title=self._current_song.title,
                                     artist=self._current_song.artist,
                                     album="La Playlist Pycolore"))))

    def get_next_step(self, logger: Logger, dt: datetime, channel: "Channel") -> Step:
        if self == channel.station_at(dt):
            return Step.none()
        return Step(
            start=int(dt.timestamp()),
            end=int(dt.timestamp()),
            broadcast=Broadcast(
                title="La Playlist Pycolore",
                type=BroadcastType.PROGRAMME,
                station=self.station_info,
                thumbnail_src=self.station_thumbnail)
        )

    def get_schedule(self, logger: Logger, start: datetime, end: datetime) -> List[Step]:
        return [Step(
            start=int(start.timestamp()),
            end=int(end.timestamp()),
            broadcast=Broadcast(
                title="La Playlist Pycolore",
                type=BroadcastType.PROGRAMME,
                station=self.station_info,
                thumbnail_src=self.station_thumbnail)
        )]

    def process(self, logger: Logger, channels_using: Dict, channels_using_next: Dict, now: datetime, **kwargs):
        """Play new song if needed.
        
        Compute end of use time of this station.
        If current song is about to end, prepare and play next song.

        Call _play() to trigger next song.
        """

        # if station is not used, check if a channel will soon use it
        channels_using_self = channels_using[self]
        if not channels_using_self:
            # in case we already anticipated, return
            if self._current_song is not None:
                return
            # in this case, anticipate and launch a song
            for channel in channels_using_next[self]: # type: Channel
                delay = max((channel.station_end_at(now) - now).seconds, 0)
                max_length = -1
                self._play(delay, max_length, logger, now)
                break
            return

        # compute end of use
        for channel in channels_using_self: # type: Channel
            end_of_current_station = channel.station_end_at(now)
            if self._end_of_use < end_of_current_station:
                self._end_of_use = end_of_current_station

        if self._current_song_end - 10 < now.timestamp():
            delay = max(self._current_song_end - now.timestamp(), 0)
            max_length = (self._end_of_use - now).seconds - delay
            self._play(delay, max_length, logger, now)

    def format_stream_metadata(self, broadcast: Broadcast) -> Optional[StreamMetadata]:
        if broadcast.type != BroadcastType.MUSIC:
            return StreamMetadata(
                title=broadcast.title,
                artist=self.name,
                album="")
        return broadcast.metadata

    @classmethod
    def get_liquidsoap_config(cls):
        return '{0} = fallback(track_sensitive=false, [request.queue(id="{0}"), default])\n'.format(cls.formatted_station_name)
