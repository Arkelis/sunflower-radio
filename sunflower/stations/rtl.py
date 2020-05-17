import json
from datetime import date, datetime, time, timedelta
from logging import Logger

import requests
from bs4 import BeautifulSoup

from sunflower import settings
from sunflower.core.bases import URLStation
from sunflower.core.types import CardMetadata, MetadataDict, MetadataType


class RTL2(URLStation):
    station_name = "RTL 2"
    station_slogan = "Le son Pop-Rock"
    station_website_url = "https://www.rtl2.fr"
    station_thumbnail = "https://upload.wikimedia.org/wikipedia/fr/f/fa/RTL2_logo_2015.svg"
    station_url = "http://streaming.radio.rtl2.fr/rtl2-1-48-192"
    _main_data_url = "https://timeline.rtl.fr/RTL2/items"
    _songs_data_url = "https://timeline.rtl.fr/RTL2/songs"

    @staticmethod
    def _fetch_show_metadata(dt: datetime):
        start_str = dt.isoformat(sep=" ", timespec="seconds")
        end_str = (dt + timedelta(seconds=5)).isoformat(sep=" ", timespec="seconds")
        req = requests.get(
            "https://pc.middleware.6play.fr/6play/v2/platforms/m6group_web/services/m6replay/guidetv?channel=rtl2&from={}&to={}&limit=1&offset=0&with=realdiffusiondates".format(
                start_str, end_str
            )
        )
        data = json.loads(req.content.decode()).get("rtl2")
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
            current_station=self.html_formated_station_name,
            current_broadcast_title=current_broadcast_title,
        )

    def _fetch_song_metadata(self, retry=0):
        """Return mapping containing song info"""
        try:
            rep = requests.get(self._songs_data_url, timeout=1)
            return json.loads(rep.content.decode())[0]
        except requests.exceptions.Timeout:
            if retry == 11:
                return self._get_error_metadata("API Timeout", 90)
            return self._fetch_song_metadata(retry + 1)

    def _fetch_metadata(self, retry=0):
        """Fetch data from timeline.rtl.fr.
        
        Scrap from items page. If song object detected, get data from songs endpoint.
        Else return MetadataType object. 
        """
        try:
            rep = requests.get(self._main_data_url, timeout=1)
            soup = BeautifulSoup(rep.content.decode(), "html.parser")
            try:
                diffusion_type = soup.find_all("tr")[2].find_all("td")[1].text
            except IndexError:
                previous_url = (
                    "/".join(self._main_data_url.split("/")[:3]) + soup.find_all("a")[8].attrs["href"]
                )
                rep = requests.get(previous_url, timeout=1)
                soup = BeautifulSoup(rep.content.decode(), "html.parser")
                try:
                    diffusion_type = soup.find_all("tr")[2].find_all("td")[1].text
                except:
                    raise RuntimeError("Le titre de la chanson ne peut pas être trouvé.")
        except requests.exceptions.Timeout:
            if retry == 11:
                return self._get_error_metadata("API Timeout", 90)
            return self._fetch_metadata(retry + 1)
        if diffusion_type == "Pubs":
            return {"type": MetadataType.ADS}
        if diffusion_type != "Musique":
            return {"type": MetadataType.NONE}
        else:
            return self._fetch_song_metadata()

    def get_metadata(self, current_metadata, logger, dt: datetime):
        """Returns mapping containing info about current song.

        If music: {"type": MetadataType.MUSIC, "artist": artist, "title": title}
        If ads: "type": MetadataType.ADS
        Else: "type": MetadataType.NONE

        Moreover, returns other metadata for postprocessing.
        end datetime object

        To sum up, here are the keys of returned mapping:
        - type: MetadataType object
        - end: timestamp in sec
        - artist: str (optionnal)
        - title: str (optionnal)
        - thumbnail_src: url to thumbnail
        """
        dt_timestamp = dt.timestamp()

        # first, update show info if needed
        show_metadata_keys = ("show_end", "show_title", "show_summary")
        if current_metadata.get("show_end") is None or current_metadata.get("show_end") < dt_timestamp:
            show_metadata = self._fetch_show_metadata()
        else:
            show_metadata = {k: v for k, v in current_metadata.items() if k in show_metadata_keys}

        # next, update song info
        fetched_data = self._fetch_metadata()
        fetched_data_type = fetched_data.get("type")

        if fetched_data_type in (MetadataType.ADS, MetadataType.NONE):
            return {
                "station": self.station_name,
                "thumbnail_src": self.station_thumbnail,
                "type": fetched_data_type,
                "end": 0,
            }

        end = int(fetched_data["end"] / 1000)
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
