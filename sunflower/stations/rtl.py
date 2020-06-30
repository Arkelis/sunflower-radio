import json
import locale
from datetime import datetime, time, timedelta
from logging import Logger
from typing import Optional

import requests
from bs4 import BeautifulSoup

from sunflower.core.bases import URLStation
from sunflower.core.custom_types import CardMetadata, MetadataDict, MetadataType, StreamMetadata

try:
    locale.setlocale(locale.LC_TIME, "fr_FR.utf8")
except locale.Error:
    pass


class RTLGroupStation(URLStation):
    _main_data_url: str = ""
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
                return self._get_error_metadata("API Timeout", 90)
            return self._fetch_song_metadata(retry + 1)

    def _fetch_metadata(self, dt: datetime, retry=0):
        """Fetch data from timeline.rtl.fr.

        Scrap from items page. If song object detected, get data from songs endpoint.
        Else return MetadataType object.
        """
        try:
            rep = requests.get(self._main_data_url, timeout=1)
            soup = BeautifulSoup(rep.text, "html.parser")
            try:
                first_row: BeautifulSoup = soup.find_all("tr")[2]
                diffusion_type: str = first_row.find_all("td")[1].text
                start_end_text: str = first_row.find_all("td")[-1].text.replace(" ", "").replace("\n", "")
                start_time, end_time = map(time.fromisoformat, start_end_text[:start_end_text.index("(")].split("⇾")) # type: time, time
                start = int(datetime.combine(dt.date(), start_time).timestamp())
                end = int(datetime.combine(dt.date(), end_time).timestamp())
            except IndexError:
                previous_url = (
                    "/".join(self._main_data_url.split("/")[:3]) + soup.find_all("a")[8].attrs["href"]
                )
                rep = requests.get(previous_url, timeout=1)
                soup = BeautifulSoup(rep.content.decode(), "html.parser")
                try:
                    first_row: BeautifulSoup = soup.find_all("tr")[2]
                    diffusion_type: str = first_row.find_all("td")[1].text
                    start_end_text: str = first_row.find_all("td")[-1].text.replace(" ", "").replace("\n", "")
                    start_time, end_time = map(
                        time.fromisoformat,
                        start_end_text[:start_end_text.index("(")].split("⇾")
                    )  # type: time, time
                    start = int(datetime.combine(dt.date(), start_time).timestamp())
                    end = int(datetime.combine(dt.date(), end_time).timestamp())
                except KeyError:
                    raise RuntimeError("Le titre de la chanson ne peut pas être trouvé.")
        except requests.exceptions.Timeout:
            if retry == 11:
                return self._get_error_metadata("API Timeout", 90)
            return self._fetch_metadata(dt, retry + 1)
        if diffusion_type == "Pubs":
            return {"type": MetadataType.ADS, "end": 0}
        elif diffusion_type == "Emissions":
            return {"type": MetadataType.PROGRAMME, "start": start, "end": end}
        elif diffusion_type != "Musique" or end < dt.timestamp():
            return {"type": MetadataType.NONE, "end": 0}
        else:
            return self._fetch_song_metadata()


class RTL(RTLGroupStation):
    station_name = "RTL"
    station_slogan = "On a tellement de choses à se dire !"
    station_website_url = "https://www.rtl.fr"
    station_thumbnail = "/static/rtl.svg"
    station_url = "http://streaming.radio.rtl2.fr/rtl-1-48-192"
    _main_data_url = "https://timeline.rtl.fr/RTL/items"
    _songs_data_url = "https://timeline.rtl.fr/RTL/songs"

    def get_metadata(self, current_metadata: MetadataDict, logger: Logger, dt: datetime):
        """Pour l'instant RTL n'est utilisé que pour les Grosses Têtes et A la bonne heure."""
        dt_timestamp = dt.timestamp()

        # next, update song info
        fetched_data = self._fetch_metadata(dt)
        fetched_data_type = fetched_data.get("type")

        if fetched_data_type in (MetadataType.ADS, MetadataType.NONE):
            return {
                "station": self.station_name,
                "thumbnail_src": self.station_thumbnail,
                "type": fetched_data_type,
                "end": 0,
            }

        end = fetched_data["end"]
        if fetched_data_type == MetadataType.PROGRAMME:
            if (
                datetime.combine(datetime.today(), time(15, 30)).timestamp()
                <= end
                <= datetime.combine(datetime.today(), time(18, 0)).timestamp()
            ):
                title = f"Les Grosses Têtes du {dt.strftime('%A %d %B %Y')}"
                show_title = "Les Grosses Têtes de Laurent Ruquier"
                show_summary = ("Du lundi au vendredi de 15h30 à 18h, retrouvez Laurent Ruquier, chef d'orchestre de "
                                "l'émission. Entouré des ses fidèles Grosses Têtes, il imprime sa marque à ce "
                                "programme culte de la radio tout en restant fidèle à ses fondamentaux.")
                show_url = "https://www.rtl.fr/emission/les-grosses-tetes"
            else:
                title = f"À la bonne heure ! {dt.strftime('%A %d %B %Y')}"
                show_title = "À la bonne heure ! de Stéphane Bern"
                show_summary = ('Du lundi au vendredi de 11h à 12h30, Stéphane Bern, entouré de ses espiègles '
                                'chroniqueurs, reçoit une personnalité de l’actualité culturelle pour une heure trente '
                                'de "drôleries".')
                show_url = "https://www.rtl.fr/emission/a-la-bonne-heure"
            return {
                "station": self.station_name,
                "thumbnail_src": self.station_thumbnail,
                "title": title,
                "show_title": show_title,
                "show_summary": show_summary,
                "show_url": show_url,
                "type": fetched_data_type,
                "end": end,
            }

        if dt_timestamp > end:
            return {
                "station": self.station_name,
                "thumbnail_src": self.station_thumbnail,
                "type": MetadataType.NONE,
                "end": 0,
            }
        else:
            return {
                "station": self.station_name,
                "artist": fetched_data["singer"],
                "title": fetched_data["title"],
                "end": end,
                "type": MetadataType.MUSIC,
                "thumbnail_src": fetched_data.get("cover") or self.station_thumbnail,
            }

    def format_info(self, current_info: CardMetadata, metadata: MetadataDict, logger: Logger) -> CardMetadata:
        current_broadcast_title = {
            MetadataType.ADS: "Publicité",
            MetadataType.MUSIC: "{} • {}".format(metadata.get("artist"), metadata.get("title")),
            MetadataType.PROGRAMME: metadata.get("title") or self.station_slogan
        }.get(metadata["type"], self.station_slogan)

        return CardMetadata(
            current_thumbnail=metadata["thumbnail_src"],
            current_show_title=self._format_html_anchor_element(metadata.get("show_url"), metadata.get("show_title", "")),
            current_broadcast_summary=metadata.get("show_summary", ""),
            current_station=self.html_formatted_station_name,
            current_broadcast_title=current_broadcast_title,
        )

    def format_stream_metadata(self, metadata) -> Optional[StreamMetadata]:
        title = metadata.get("title")
        track_metadata = (metadata.get("artist"), title)
        show_title = metadata.get("show_title", "")
        title = (" • ".join(track_metadata) if all(track_metadata) else title) or self.station_slogan
        return StreamMetadata(title, self.station_name, show_title)

    @classmethod
    def get_liquidsoap_config(cls):
        string = 'rtl_stream = input.http("{cls.station_url}", buffer=60., max=120.)\n'
        string += (f'{cls.formatted_station_name} = drop_metadata(fallback(track_sensitive=false, '
                   '[rtl_stream, default]))\n')
        return string


class RTL2(RTLGroupStation):
    station_name = "RTL 2"
    station_slogan = "Le son Pop-Rock"
    station_website_url = "https://www.rtl2.fr"
    station_thumbnail = "https://upload.wikimedia.org/wikipedia/fr/f/fa/RTL2_logo_2015.svg"
    station_url = "http://streaming.radio.rtl2.fr/rtl2-1-48-192"
    _main_data_url = "https://timeline.rtl.fr/RTL2/items"
    _songs_data_url = "https://timeline.rtl.fr/RTL2/songs"
    _show_grid_url = ("https://pc.middleware.6play.fr/6play/v2/platforms/m6group_web/services/m6replay/guidetv?channel="
                      "rtl2&from={}&to={}&limit=1&offset=0&with=realdiffusiondates")

    def _fetch_show_metadata(self, dt: datetime):
        start_str = dt.isoformat(sep=" ", timespec="seconds")
        end_str = (dt + timedelta(seconds=5)).isoformat(sep=" ", timespec="seconds")
        req = requests.get(self._show_grid_url.format(start_str, end_str))
        data = json.loads(req.text).get(self.formatted_station_name)
        if not data:
            return {}
        show = data[0]
        end_of_show = datetime.strptime(show["diffusion_end_date"], "%Y-%m-%d %H:%M:%S")
        end_of_show_timestamp = int(end_of_show.timestamp())
        return {
            "show_title": show["title"],
            "show_summary": show["description"],
            "show_end": end_of_show_timestamp,
        }

    def format_info(self, current_info: CardMetadata, metadata: MetadataDict, logger: Logger) -> CardMetadata:
        current_broadcast_title = {
            MetadataType.ADS: "Publicité",
            MetadataType.MUSIC: "{} • {}".format(metadata.get("artist"), metadata.get("title")),
        }.get(metadata["type"], self.station_slogan)

        return CardMetadata(
            current_thumbnail=metadata["thumbnail_src"],
            current_show_title=metadata.get("show_title", ""),
            current_broadcast_summary=metadata.get("show_summary", ""),
            current_station=self.html_formatted_station_name,
            current_broadcast_title=current_broadcast_title,
        )

    def get_metadata(self, current_metadata: MetadataDict, logger: Logger, dt: datetime):
        """Returns mapping containing info about current song.

        If music: {"type": MetadataType.MUSIC, "artist": artist, "title": title}
        If ads: "type": MetadataType.ADS
        Else: "type": MetadataType.NONE

        Moreover, returns other metadata for postprocessing.
        end datetime object

        To sum up, here are the keys of returned mapping:
        - type: MetadataType object
        - end: timestamp in sec
        - artist: str (optional)
        - title: str (optional)
        - thumbnail_src: url to thumbnail
        """
        dt_timestamp = dt.timestamp()

        # first, update show info if needed
        show_metadata_keys = ("show_end", "show_title", "show_summary")
        if current_metadata.get("show_end") is None or current_metadata.get("show_end") < dt_timestamp:
            show_metadata = self._fetch_show_metadata(dt)
        else:
            show_metadata = {k: v for k, v in current_metadata.items() if k in show_metadata_keys}

        # next, update song info
        fetched_data = self._fetch_metadata(dt)
        fetched_data_type = fetched_data.get("type")

        if fetched_data_type == MetadataType.ADS:
            return {
                "station": self.station_name,
                "thumbnail_src": self.station_thumbnail,
                "type": fetched_data_type,
                "end": 0,
            }

        end = fetched_data["end"]
        if dt_timestamp > end:
            if not show_metadata:
                return {
                    "station": self.station_name,
                    "thumbnail_src": self.station_thumbnail,
                    "type": MetadataType.NONE,
                    "end": 0,
                }
            metadata = {
                "thumbnail_src": self.station_thumbnail,
                "type": MetadataType.PROGRAMME,
                "end": 0,
            }
        else:
            metadata = {
                "artist": fetched_data["singer"],
                "title": fetched_data["title"],
                "end": end,
                "type": MetadataType.MUSIC,
                "thumbnail_src": fetched_data.get("cover") or self.station_thumbnail,
            }
        metadata.update(station=self.station_name, **show_metadata)
        return metadata

    def format_stream_metadata(self, metadata) -> Optional[StreamMetadata]:
        track_metadata = (metadata.get("artist"), metadata.get("title"))
        show_title = metadata.get("show_title", "")
        title = " • ".join(track_metadata) if all(track_metadata) else self.station_slogan
        return StreamMetadata(title, self.station_name, show_title)
