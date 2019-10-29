# This is Sunflower Radio app.

"""Module containing radio metadata fetching related functions."""

import json
import os
from abc import ABC
from datetime import datetime, time, timedelta
from backports.datetime_fromisoformat import MonkeyPatch


import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from sunflower import settings

class Radio:
    stations = {}

    @property
    def current_station_name(self):
        """Returning string matching current time according to TIMETABLE dict in settings."""
        assert hasattr(settings, "TIMETABLE"), "TIMETABLE not defined in settings."
        current_time = datetime.now().time()
        timetable = settings.TIMETABLE
        try:
            MonkeyPatch.patch_fromisoformat()
            for t in timetable:
                station = t[2]
                start, end = map(time.fromisoformat, t[:2])
                end = time(23, 59, 59) if end == time(0, 0, 0) else end
                if start < current_time < end:
                    return station
            else:
                raise RuntimeError("Aucune station programmée à cet horaire.")
        except FileNotFoundError:
            raise RuntimeError("Vous devez créer une configuration d'horaires (fichier timetable.conf).")
    
    def get_current_broadcast_metadata(self):
        """Return metadata of current broadcasted programm for current station.
        
        This is for pure json data exposure.
        """
        try:
            station = self.stations.get(self.current_station_name)()
        except TypeError as exception:
            raise RuntimeError("Station '{}' non gérée.".format(self.current_station_name)) from exception
        metadata = station.get_metadata()
        metadata.update({"station": station.station_name})
        return metadata
    
    def get_current_broadcast_info(self):
        """Return data for displaying broadcast info in player.
        
        This is for data display in player client.
        """
        print(self.stations)
        try:
            station = self.stations.get(self.current_station_name)()
        except TypeError as exception:
            raise RuntimeError("Station '{}' non gérée.".format(self.current_station_name)) from exception
        card_info = station.format_info()
        return card_info


class StationMeta(type):
    def __new__(mcls, name, bases, attrs):
        cls = super().__new__(mcls, name, bases, attrs)
        if hasattr(cls, "station_name"):
            Radio.stations[cls.station_name] = cls
        return cls


class Station(metaclass=StationMeta):
    # station_name: str # needs to be commented for python3.5
    # station_thumbnail: str # needs to be commented for python3.5

    # THE FOLLOWING METHOD IS COMMENTED (BECAUSE UNUSED) IN PYTHON 3.5
    # ITS BEHAVIOR IS REPLACED WITH StationMeta METACLASS (see above).
    # def __init_subclass__(cls):
    #     if hasattr(cls, "station_name"):
    #         Radio.stations[cls.station_name] = cls
    #     return super().__init_subclass__()

    def get_metadata(self):
        """Return mapping containing metadata about current broadcast.
        
        This is data meant to be exposed as json and used by format_info() method.
        
        Required fields:
        - type: Emission|Musique|Publicité
        - metadata fields required by format_info() method (see below)
        """

    def format_info(self):
        """Format data for displaying in the card.
        
        Should return a dict containing:
        - current_thumbnail
        - current_station
        - current_broadcast_title
        - current_show_title
        - current_broadcast_summary
        - current_broadcast_end

        If empty, a given key should have "" (empty string) as value, and not None, except
        for current_broadcast_end which is False if unknown.
        """
    


class RTL2(Station):
    station_name = "RTL 2"
    station_thumbnail = "https://upload.wikimedia.org/wikipedia/fr/f/fa/RTL2_logo_2015.svg"
    _main_data_url = "https://timeline.rtl.fr/RTL2/items"
    _songs_data_url = "https://timeline.rtl.fr/RTL2/songs"

    def format_info(self):
        metadata = self.get_metadata()
        card_info = {
            "current_thumbnail": metadata["thumbnail"],
            "current_broadcast_end": metadata["end"],
            "current_show_title": "",
            "current_broadcast_summary": "",
            "current_station": self.station_name,
        }
        if metadata["type"] == "Musique":
            card_info["current_broadcast_title"] = metadata["artist"] + " • " + metadata["title"]
        else: 
            card_info["current_broadcast_title"] = metadata["type"]
        return card_info

    def _fetch_metadata(self, song=False):
        if song:
            rep = requests.get(self._songs_data_url)
            return json.loads(rep.content.decode())[0]
        rep = requests.get(self._main_data_url)
        soup = BeautifulSoup(rep.content.decode(), "html.parser")
        try:
            diffusion_type = soup.find_all("tr")[2].find_all("td")[1].text
        except IndexError:
            previous_url = "/".join(self._main_data_url.split("/")[:3]) + soup.find_all("a")[6].attrs["href"]
            rep = requests.get(previous_url)
            soup = BeautifulSoup(rep.content.decode(), "html.parser")
            try:
                diffusion_type = soup.find_all("tr")[2].find_all("td")[1].text
            except:
                raise RuntimeError("Le titre de la chanson ne peut pas être trouvé.")
        if diffusion_type == "Pubs":
            return {"type": "Publicités", "end": False}
        if diffusion_type != "Musique":
            return {"type": "Intermède", "end": False}
        else:
            return self._fetch_metadata(True)

    def get_metadata(self):
        """Returns mapping containing info about current song.

        If music: {"type": "Musique", "artist": artist, "title": title}
        If ads: "type": Publicité"
        Else: "type": "Intermède"

        Moreover, returns other metadata for postprocessing.
        end datetime object

        To sum up, here are the keys of returned mapping:
        - type: str
        - end: str (ISO format) or False if unknown
        - artist: str (optionnal)
        - title: str (optionnal)
        """
        fetched_data = self._fetch_metadata()
        if fetched_data.get("type") in ("Publicités", "Intermède"):
            fetched_data.update({"thumbnail": self.station_thumbnail})
            return fetched_data
        metadata = {
            "artist": fetched_data["singer"],
            "title": fetched_data["title"],
            "end": int(fetched_data["end"]),
            "thumbnail": fetched_data["thumbnail"] or self.station_thumbnail,
            "type": "Musique",
        }
        return metadata


class RadioFranceStation(Station):
    # station_name: str # commented in python3.5
    # station_thumbnail: str # commented in python3.5
    # _station_api_name: str # commented in python3.5

    @property
    def token(self):
        if os.getenv("TOKEN") is None: # in case of development server
            load_dotenv()
            if os.getenv("TOKEN") is None:
                raise RuntimeError("No token for Radio France API found.")
        return os.getenv("TOKEN")

    _grid_template = """
    {{
    grid(start: {start}, end: {end}, station: {station}) {{
        ... on DiffusionStep {{
        start
        end
        diffusion {{
            title
            standFirst
            show {{
            title
            }}
        }}
        }}
        ... on TrackStep {{
        start
        end
        track {{
            title
            albumTitle
        }}
        }}
        ... on BlankStep {{
        start
        end
        title
        }}
    }}
    }}
    """

    def format_info(self):
        metadata = self.get_metadata()
        card_info = {
            "current_broadcast_title": metadata.get("diffusion_title", metadata["show_title"]),
            "current_thumbnail": metadata["thumbnail_src"],
            "current_broadcast_end": metadata["end"],
            "current_show_title": metadata["show_title"],
            "current_broadcast_summary": metadata["summary"],
            "current_station": self.station_name,
        }
        return card_info

    def get_metadata(self):
        fetched_data = self._fetch_metadata()
        current_show = fetched_data["data"]["grid"][0]
        next_show = fetched_data["data"]["grid"][1]
        diffusion = current_show.get("diffusion")
        metadata = {
            "type": "Emission",
            "end": int(next_show["start"]) * 1000, # client needs timestamp in ms
            "thumbnail_src": self.station_thumbnail,
        }
        if diffusion is None:
            metadata.update({
                "show_title": current_show["title"],
                "summary": "",
            })
        else:
            summary = current_show["diffusion"]["standFirst"]
            if not summary or summary == ".":
                summary = ""
            metadata.update({
                "show_title": diffusion["show"]["title"],
                "diffusion_title": diffusion["title"],
                "summary": summary,
            })
        return metadata
    

    def _fetch_metadata(self):
        start = datetime.now()
        end = datetime.now() + timedelta(minutes=120)
        query = self._grid_template.format(
            start=int(start.timestamp()),
            end=int(end.timestamp()),
            station=self._station_api_name
        )
        rep = requests.post(
            url="https://openapi.radiofrance.fr/v1/graphql?x-token={}".format(self.token),
            json={"query": query}
        )
        data = json.loads(rep.content.decode())
        return data


class FranceInter(RadioFranceStation):
    station_name = "France Inter"
    _station_api_name = "FRANCEINTER"
    station_thumbnail = "https://upload.wikimedia.org/wikipedia/fr/thumb/8/8d/France_inter_2005_logo.svg/1024px-France_inter_2005_logo.svg.png"


class FranceInfo(RadioFranceStation):
    station_name = "France Info"
    _station_api_name = "FRANCEINFO"
    station_thumbnail = "https://lh3.googleusercontent.com/VKfyGmPTaHyxOAf1065M_CftsEiGIOkZOiGpXUlP1MTSBUA4j5O5n9GRLJ3HvQsXQdY"


class FranceMusique(RadioFranceStation):
    station_name = "France Musique"
    _station_api_name = "FRANCEMUSIQUE"
    station_thumbnail = "https://upload.wikimedia.org/wikipedia/fr/thumb/2/22/France_Musique_-_2008.svg/1024px-France_Musique_-_2008.svg.png"


class FranceCulture(RadioFranceStation):
    station_name = "France Culture"
    _station_api_name = "FRANCECULTURE"
    station_thumbnail = "https://upload.wikimedia.org/wikipedia/fr/thumb/c/c9/France_Culture_-_2008.svg/1024px-France_Culture_-_2008.svg.png"
