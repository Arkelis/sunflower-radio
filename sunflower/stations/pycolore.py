import telnetlib
from datetime import date, datetime, time, timedelta

from sunflower import settings
from sunflower.core.bases import DynamicStation
from sunflower.core.types import CardMetadata, MetadataType
from sunflower.utils.functions import fetch_cover_and_link_on_deezer, parse_songs, prevent_consecutive_artists


class PycolorePlaylistStation(DynamicStation):
    station_name = "Radio Pycolore"
    station_thumbnail = "https://upload.wikimedia.org/wikipedia/commons/c/ce/Sunflower_clip_art.svg"
    endpoint = "pycolore"

    def __setup__(self):
        self._songs_to_play = []
        self._current_song = None
        self._current_song_end = 0
        self._end_of_use = datetime.now()

    def _get_next_song(self, max_length):
        if len(self._songs_to_play) <= 5:
            self._songs_to_play += parse_songs(settings.BACKUP_SONGS_GLOB_PATTERN)
            self._songs_to_play = prevent_consecutive_artists(self._songs_to_play)
        for (i, song) in enumerate(self._songs_to_play):
            if song.length < max_length:
                return self._songs_to_play.pop(i)
        return None

    @property
    def _artists(self):
        """Property returning artists of the 5 next-played songs."""
        songs = self._songs_to_play
        artists_list = [self._current_song.artist]
        for song in songs:
            if song.artist not in artists_list:
                artists_list.append(song.artist)
            if len(artists_list) == 5:
                break
        return artists_list
        
    def _play(self, delay, max_length, logger):
        self._current_song = self._get_next_song(max_length)
        if self._current_song is None:
            self._current_song_end = int(datetime.now().timestamp()) + max_length
            return
        logger.debug("station={} Playing {} - {} ({} songs remaining in current list).".format(self.formated_station_name, self._current_song.artist, self._current_song.title, len(self._songs_to_play)))
        self._current_song_end = int((datetime.now() + timedelta(seconds=self._current_song.length)).timestamp()) + delay
        session = telnetlib.Telnet("localhost", 1234)
        session.write("{}_station_queue.push {}\n".format(self.formated_station_name, self._current_song.path).encode())
        session.write("exit\n".encode())
        session.close()

    def get_metadata(self, current_metadata, logger, dt):
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
            "end": self._current_song_end,
            "show": "La playlist Pycolore",
            "summary": "Une sélection aléatoire de chansons parmi les musiques stockées sur Pycolore. À suivre : {}.".format(artists_str)
        }

    def format_info(self, metadata, logger):
        current_broadcast_title = self._format_html_anchor_element(metadata.get("link"), "{} • {}".format(metadata["artist"], metadata["title"]))
        return CardMetadata(
            current_thumbnail=metadata["thumbnail_src"],
            current_station=metadata["station"],
            current_broadcast_title=current_broadcast_title,
            current_show_title=metadata["show"],
            current_broadcast_summary=metadata["summary"],
        )

    def process(self, logger, channels_using, **kwargs):
        """Play new song if needed."""
        now = datetime.now()

        # if station is not used, return
        channels_using_self = channels_using[self]
        if not channels_using_self:
            return

        # compute end of use
        for channel in channels_using_self:
            end_of_current_station = channel.get_station_info(now)[1]
            if self._end_of_use < end_of_current_station:
                self._end_of_use = end_of_current_station

        if self._current_song_end - 10 < int(now.timestamp()):
            delay = max(self._current_song_end - int(now.timestamp()), 0)
            max_length = (self._end_of_use - now).seconds - delay
            self._play(delay, max_length, logger)

    @classmethod
    def get_liquidsoap_config(cls):
        string = '{0} = fallback(track_sensitive=false, [request.queue(id="{0}_station_queue"), default])\n'.format(cls.formated_station_name)
        return string
