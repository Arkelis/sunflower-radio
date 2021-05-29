import json
import locale
from datetime import datetime
from logging import Logger
from typing import List
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union

import requests
from bs4 import BeautifulSoup
from sunflower.core.custom_types import Broadcast
from sunflower.core.custom_types import BroadcastType
from sunflower.core.custom_types import SongPayload
from sunflower.core.custom_types import Step
from sunflower.core.custom_types import StreamMetadata
from sunflower.core.custom_types import UpdateInfo
from sunflower.core.stations import URLStation

try:
    locale.setlocale(locale.LC_TIME, "fr_FR.utf8")
except locale.Error:
    pass

if TYPE_CHECKING:
    from sunflower.core.bases import Channel

class RTLGroupMixin:
    # _main_data_url: str = ""
    _songs_data_url: str = ""

    def _fetch_song_metadata(self, retry=0):
        """Return mapping containing song info"""
        try:
            rep = requests.get(self._songs_data_url, timeout=1)
            song_data = json.loads(rep.text)[0]
            song_data["start"] = int(song_data["start"] / 1000)
            song_data["end"] = int(song_data["end"] / 1000)
            return song_data
        except requests.exceptions.Timeout:
            if retry == 11:
                raise requests.exceptions.Timeout from None
            return self._fetch_song_metadata(retry + 1)

    # def _fetch_metadata(self, dt: datetime, retry=0):
    #     """Fetch data from timeline.rtl.fr.
    #
    #     Scrap from items page. If song object detected, get data from songs endpoint.
    #     Else return BroadcastType object.
    #     """
    #     try:
    #         rep = requests.get(self._main_data_url, timeout=1)
    #         soup = BeautifulSoup(rep.text, "html.parser")
    #         try:
    #             first_row: BeautifulSoup = soup.find_all("tr")[2]
    #             diffusion_type: str = first_row.find_all("td")[1].text
    #             start_end_text: str = first_row.find_all("td")[-1].text.replace(" ", "").replace("\n", "")
    #             start_time, end_time = map(time.fromisoformat, start_end_text[:start_end_text.index("(")].split("⇾")) # type: time, time
    #             start = int(datetime.combine(dt.date(), start_time).timestamp())
    #             end = int(datetime.combine(dt.date(), end_time).timestamp())
    #         except IndexError:
    #             previous_url = (
    #                 "/".join(self._main_data_url.split("/")[:3]) + soup.find_all("a")[8].attrs["href"]
    #             )
    #             rep = requests.get(previous_url, timeout=1)
    #             soup = BeautifulSoup(rep.content.decode(), "html.parser")
    #             try:
    #                 first_row: BeautifulSoup = soup.find_all("tr")[2]
    #                 diffusion_type: str = first_row.find_all("td")[1].text
    #                 start_end_text: str = first_row.find_all("td")[-1].text.replace(" ", "").replace("\n", "")
    #                 start_time, end_time = map(
    #                     time.fromisoformat,
    #                     start_end_text[:start_end_text.index("(")].split("⇾")
    #                 )  # type: time, time
    #                 start = int(datetime.combine(dt.date(), start_time).timestamp())
    #                 end = int(datetime.combine(dt.date(), end_time).timestamp())
    #             except KeyError:
    #                 raise RuntimeError("Le titre de la chanson oupne peut pas être trouvé.")
    #     except requests.exceptions.Timeout:
    #         if retry == 11:
    #             raise requests.exceptions.Timeout from None
    #         return self._fetch_metadata(dt, retry + 1)
    #     if diffusion_type == "Pubs":
    #         return {"type": BroadcastType.ADS, "end": 0}
    #     elif diffusion_type == "Emissions":
    #         return {"type": BroadcastType.PROGRAMME, "start": start, "end": end}
    #     elif diffusion_type != "Musique" or end < dt.timestamp():
    #         return {"type": BroadcastType.NONE, "end": 0}
    #     else:
    #         return self._fetch_song_metadata()


# class RTL(Station, RTLGroupMixin):
#     name = "RTL"
#     station_slogan = "On a tellement de choses à se dire !"
#     station_website_url = "https://www.rtl.fr"
#     station_thumbnail = "/static/rtl.svg"
#     # station_url = "http://streaming.radio.rtl2.fr/rtl-1-48-192"
#     # _main_data_url = "https://timeline.rtl.fr/RTL/items"
#     # _songs_data_url = "https://timeline.rtl.fr/RTL/songs"
#     _grosses_tetes_podcast_url = "https://www.rtl.fr/podcast/les-grosses-tetes.xml"
#
#     def __init__(self):
#         super().__init__()
#         self._last_grosses_tetes_diffusion_date = date(1970, 1, 1)
#         self._grosses_tetes_broadcast: Optional[Broadcast] = None
#         self._grosses_tetes_audio_stream: Optional[str] = None
#         self._grosses_tetes_duration: Optional[int] = 0
#
#     @staticmethod
#     def _fetch_last_podcast_metadata(url):
#         namespace = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
#         rep = requests.get(url)
#         rss = ElementTree.fromstring(rep.text).find("channel")
#         show_url = rss.find("link").text
#         thumbnail_src = rss.find("image").find("url").text
#         show_title = rss.find("title").text
#         summary = rss.find("description").text
#         first_item = rss.find("item")
#         broadcast_title = first_item.find("title").text
#         stream_url = first_item.find("enclosure").get("url")
#         duration = tuple(map(int, first_item.find("itunes:duration", namespace).text.split(":")))
#         broadcast_length = duration[0]*3600 + duration[1]*60 + duration[2]
#         return {
#             "show_link": show_url,
#             "show_title": show_title,
#             "thumbnail_src": thumbnail_src,
#             "summary": summary,
#             "title": broadcast_title,
#             "stream_url": stream_url,
#             "duration": broadcast_length,
#         }
#
#     def get_step(self, logger: Logger, dt: datetime, channel, for_schedule=False) -> Step:
#         """Pour l'instant RTL n'est utilisé que pour les Grosses Têtes."""
#         dt_timestamp = int(dt.timestamp())
#         if dt.date() == self._last_grosses_tetes_diffusion_date:
#             if for_schedule:
#                 return Step(start=dt_timestamp, end=dt_timestamp, broadcast=self._grosses_tetes_broadcast)
#             return Step.ads(dt_timestamp, self)
#         # pour l'instant uniquement Les Grosses Têtes
#         self._last_grosses_tetes_diffusion_date = dt.date()
#         podcast_url = self._grosses_tetes_podcast_url
#         broadcast_metadata = self._fetch_last_podcast_metadata(podcast_url)
#         self._grosses_tetes_duration = broadcast_metadata.pop("duration")
#         self._grosses_tetes_audio_stream = broadcast_metadata.pop("stream_url")
#         self._grosses_tetes_broadcast = Broadcast(
#             type=BroadcastType.PROGRAMME,
#             station=self.station_info,
#             **broadcast_metadata)
#         if for_schedule:
#             return Step(start=dt_timestamp, end=dt_timestamp, broadcast=self._grosses_tetes_broadcast)
#         with suppress(ConnectionRefusedError):
#             with Telnet(LIQUIDSOAP_TELNET_HOST, LIQUIDSOAP_TELNET_PORT) as session:
#                 session.write(f"{self.formatted_station_name}.push {self._grosses_tetes_audio_stream}\n".encode())
#         return Step(start=dt_timestamp, end=dt_timestamp + self._grosses_tetes_duration, broadcast=self._grosses_tetes_broadcast)
#
#     def format_stream_metadata(self, broadcast: Broadcast) -> Optional[StreamMetadata]:
#         title, album = {
#             BroadcastType.MUSIC: (broadcast.title, broadcast.show_title),
#             BroadcastType.PROGRAMME: (broadcast.show_title, ""),
#             BroadcastType.ADS: (broadcast.title, ""),
#         }[broadcast.type]
#         return StreamMetadata(title=title, artist=self.name, album=album)
#
#     @classmethod
#     def get_liquidsoap_config(cls):
#         return '{0} = fallback(track_sensitive=false, [request.queue(id="{0}"), default])\n'.format(cls.formatted_station_name)


class RTL2(URLStation, RTLGroupMixin):
    name = "RTL 2"
    station_slogan = "Le son Pop-Rock"
    station_website_url = "https://www.rtl2.fr"
    station_thumbnail = "https://upload.wikimedia.org/wikipedia/fr/f/fa/RTL2_logo_2015.svg"
    station_url = "http://streaming.radio.rtl2.fr/rtl2-1-44-128"
    # _main_data_url = "https://timeline.rtl.fr/RTL2/items"
    _songs_data_url = "https://timeline.rtl.fr/RTL2/songs"
    _show_grid_url = "https://www.rtl2.fr/grille/{}"
    long_pull = True

    def __init__(self):
        super().__init__()
        self._current_show_data = {"show_end": datetime.now().timestamp()}
        self.current_step = Step.none()

    def _get_show_metadata(self, dt: datetime):
        if self._current_show_data.get("show_end") < dt.timestamp():
            self._current_show_data = self._fetch_show_metadata(dt)
        return self._current_show_data

    def _fetch_show_metadata(self, dt: Union[datetime, int]):
        if isinstance(dt, int): # convert dt to datetime object if a timestamp is given
            dt_timestamp, dt = dt, datetime.fromtimestamp(dt)
        else:
            dt_timestamp = int(dt.timestamp())
        date_str = dt.strftime("%d-%m-%Y")
        req = requests.get(self._show_grid_url.format(date_str))
        schedule_html = BeautifulSoup(req.content, features="html.parser")
        for show_element in schedule_html.find_all("div", class_="card-container"):
            schedule_element = show_element.find("div", class_="schedule")
            schedule_text = schedule_element.text.strip().split(" - ")
            start_time, end_time = map(
                lambda x: datetime.strptime(x, "%Hh%M").time(),
                schedule_text)
            if end_time < dt.time():
                continue
            show_title = show_element.find("div", class_="title").text
            start_timestamp = int(datetime.combine(dt.date(), start_time).timestamp())
            end_timestamp = int(datetime.combine(dt.date(), end_time).timestamp())
            href_show_page = show_element.find("a").get("href")
            show_page_html = BeautifulSoup(
                requests.get(href_show_page).content,
                features="html.parser")
            show_description = show_page_html.find(
                "div",
                class_="rtl-fs-lg-20 description read-more-container"
            ).text
            break
        else:
            raise RuntimeError(f"No show found at {dt}")
        return {
            "show_title": show_title,
            "summary": show_description,
            "show_end": end_timestamp,
            "show_start": max(start_timestamp, dt_timestamp),
        }

    def _step_from_show_data(self, show_data: dict):
        return Step(
            start=show_data.get("show_start"),
            end=show_data.get("show_end"),
            broadcast=Broadcast(
                title=show_data.get("show_title", self.station_slogan),
                type=BroadcastType.PROGRAMME,
                station=self.station_info,
                thumbnail_src=self.station_thumbnail,
                summary=show_data.get("summary", "")
            )
        )

    def get_step(self, logger: Logger, dt: datetime, channel) -> UpdateInfo:
        """Returns mapping containing info about current song.

        If music: {"type": BroadcastType.MUSIC, "artist": artist, "title": title}
        If ads: "type": BroadcastType.ADS
        Else: "type": BroadcastType.NONE

        Moreover, returns other metadata for postprocessing.
        end datetime object

        To sum up, here are the keys of returned mapping:
        - type: BroadcastType object
        - end: timestamp in sec
        - artist: str (optional)
        - title: str (optional)
        - thumbnail_src: url to thumbnail
        """
        start = int(dt.timestamp())
        try:
            fetched_data = self._fetch_song_metadata()
        except requests.exceptions.Timeout:
            return self._update_info(Step.empty_until(start, start+90, self))
        end = fetched_data["end"]
        if start > end:
            if not self._get_show_metadata(dt):
                return self._update_info(Step.empty(start, self))
            end = 0
            broadcast_data = {
                "thumbnail_src": self.station_thumbnail,
                "type": BroadcastType.PROGRAMME,
                "title": self.station_slogan,
            }
        else:
            title = fetched_data['title']
            artist = fetched_data['singer']
            broadcast_data = {
                "title": f"{artist} • {title}",
                "type": BroadcastType.MUSIC,
                "thumbnail_src": fetched_data.get("cover") or self.station_thumbnail,
                "metadata": SongPayload(title=title, artist=artist)
            }
        broadcast_data.update(station=self.station_info, **self._get_show_metadata(dt))
        return self._update_info(Step(start=start, end=end, broadcast=Broadcast(**broadcast_data)))

    def _update_info(self, step):
        self.current_step, current_step = step, self.current_step
        should_notify = current_step.broadcast != step.broadcast
        return UpdateInfo(should_notify_update=should_notify, step=step)

    def get_next_step(self, logger: Logger, dt: datetime, channel: "Channel") -> Step:
        dt = (datetime.fromtimestamp(self._get_show_metadata(dt).get("show_end"))
              if channel.station_at(dt) == self
              else channel.station_end_at(dt))
        show_data = self._get_show_metadata(dt)
        return self._step_from_show_data(show_data)

    def get_schedule(self, logger: Logger, start: datetime, end: datetime) -> List[Step]:
        temp_end, end = int(start.timestamp()), int(end.timestamp())
        steps = []
        while temp_end <= end:
            show_data = self._fetch_show_metadata(temp_end)
            steps.append(self._step_from_show_data(show_data))
            temp_end = show_data["show_end"]
        return steps

    def format_stream_metadata(self, broadcast: Broadcast) -> Optional[StreamMetadata]:
        title, artist, album = {
            BroadcastType.MUSIC: (broadcast.metadata.title, broadcast.metadata.artist, broadcast.metadata.album),
            BroadcastType.PROGRAMME: (broadcast.show_title, self.name, ""),
            BroadcastType.ADS: (broadcast.title, self.name, ""),
        }[broadcast.type]
        return StreamMetadata(title=title, artist=artist, album=album)
