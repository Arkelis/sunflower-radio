import random
from datetime import datetime, timedelta
from logging import Logger
from typing import Dict, List, Optional

from sunflower import settings
from sunflower.core.bases import DynamicStation
from sunflower.core.custom_types import CardMetadata, MetadataDict, MetadataType, Song
from sunflower.core.descriptors import PersistentAttribute
from sunflower.core.liquidsoap import open_telnet_session
from sunflower.utils.deezer import fetch_cover_and_link_on_deezer, parse_songs, prevent_consecutive_artists


class PycolorePlaylistStation(DynamicStation):
    station_name = "Radio Pycolore"
    station_thumbnail = "https://upload.wikimedia.org/wikipedia/commons/c/ce/Sunflower_clip_art.svg"
    endpoint = "pycolore"

    public_playlist = PersistentAttribute("playlist", expiration_delay=172800)

    @public_playlist.pre_set_hook
    def public_playlist(self, songs: List[Song]):
        """Persist public fields of song objects in current playlist in redis."""
        return [
            {"artist": song.artist, "title": song.title, "album": song.album}
            for song in songs
        ]

    def __init__(self):
        super().__init__()
        self._songs_to_play: List[Song] = []
        self._populate_songs_to_play()
        self._current_song: Optional[Song] = None
        self._current_song_end: float = 0
        self._end_of_use: datetime = datetime.now()

    def _populate_songs_to_play(self):
        new_songs = parse_songs(settings.BACKUP_SONGS_GLOB_PATTERN)
        self.public_playlist = new_songs
        self._songs_to_play += random.sample(new_songs, len(new_songs))
        self._songs_to_play = prevent_consecutive_artists(self._songs_to_play)

    def _get_next_song(self, max_length: float):
        """Get next song in current playlist.

        Check if its length is not greater than remaining time before end of use
        of this station.
        """
        if len(self._songs_to_play) <= 5:
            self._populate_songs_to_play()
        for (i, song) in enumerate(self._songs_to_play):
            if song.length < max_length:
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
        Send a request to liquidsoap telnet server telling it to play the song.
        """
        self._current_song = self._get_next_song(max_length)
        if self._current_song is None:
            self._current_song_end = now.timestamp() + max_length
            return
        logger.debug(
            f"station={self.formatted_station_name} Playing {self._current_song.artist} - {self._current_song.title} ({len(self._songs_to_play)} songs remaining in current list)."
        )
        self._current_song_end = (now + timedelta(seconds=self._current_song.length)).timestamp() + delay
        with open_telnet_session(logger=logger) as session:
            session.write(f"{self.formatted_station_name}.push {self._current_song.path}\n".encode())

    def get_metadata(self, current_metadata: MetadataDict, logger: Logger, dt: datetime):
        if self._current_song is None:
            return {
                "station": self.station_name,
                "type": MetadataType.WAITING_FOR_FOLLOWING,
                "end": self._current_song_end,
            }
        artists_list = tuple(self._artists)
        artists_str = ", ".join(artists_list[:-1]) + " et " + artists_list[-1]
        thumbnail_src, link = fetch_cover_and_link_on_deezer(self.station_thumbnail, self._current_song.artist, self._current_song.album, self._current_song.title)
        return {
            "station": self.station_name,
            "type": MetadataType.MUSIC,
            "artist": self._current_song.artist,
            "title": self._current_song.title,
            "thumbnail_src": thumbnail_src,
            "link": link,
            "end": int(self._current_song_end),
            "show": "La playlist Pycolore",
            "summary": "Une sélection aléatoire de chansons parmi les musiques stockées sur Pycolore. À suivre : {}.".format(artists_str)
        }

    def format_info(self, current_info: CardMetadata, metadata: MetadataDict, logger: Logger) -> CardMetadata:
        current_broadcast_title = self._format_html_anchor_element(
            metadata.get("link"),
            f"{metadata['artist']} • {metadata['title']}",
        )
        return CardMetadata(
            current_thumbnail=metadata["thumbnail_src"],
            current_station=metadata["station"],
            current_broadcast_title=current_broadcast_title,
            current_show_title=self._format_html_anchor_element("/playlist/pycolore", metadata["show"]),
            current_broadcast_summary=metadata["summary"],
        )

    def process(self, logger: Logger, channels_using: Dict, now: datetime, **kwargs):
        """Play new song if needed.
        
        Compute end of use time of this station.
        If current song is about to end, prepare and play next song.

        Call _play() to trigger next song.
        """

        # if station is not used, return
        channels_using_self = channels_using[self]
        if not channels_using_self:
            return

        # compute end of use
        for channel in channels_using_self:
            end_of_current_station = channel.get_station_info(now)[1]
            if self._end_of_use < end_of_current_station:
                self._end_of_use = end_of_current_station

        if self._current_song_end - 10 < now.timestamp():
            delay = max(self._current_song_end - now.timestamp(), 0)
            max_length = (self._end_of_use - now).seconds - delay
            self._play(delay, max_length, logger, now)

    @classmethod
    def get_liquidsoap_config(cls):
        return '{0} = fallback(track_sensitive=false, [request.queue(id="{0}"), default])\n'.format(cls.formatted_station_name)
