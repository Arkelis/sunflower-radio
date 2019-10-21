# This is Sunflower Radio app.

"""Module containing radio metadata fetching related functions."""

import json
import os
from abc import ABC
from datetime import datetime, time, timedelta

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

FLUX_URL = {
    "France Inter": "http://icecast.radiofrance.fr/franceinter-midfi.mp3",
    "France Culture": "http://icecast.radiofrance.fr/franceculture-midfi.mp3",
    "France Musique": "http://icecast.radiofrance.fr/francemusique-midfi.mp3",
    "France Info": "http://icecast.radiofrance.fr/franceinfo-midfi.mp3",
    "RTL 2": "http://streaming.radio.rtl2.fr/rtl2-1-48-192",
}


class Radio:
    @staticmethod
    def get_current_station_name():
        """Returning string matching current time according to timetable.conf."""
        current_time = datetime.now().time()
        try:
            with open(os.path.dirname(__file__) + "/" + "timetable.conf", "r") as f:
                timetable = [string.replace("\n", "").replace("\r", "") for string in f.readlines()]
                for line in timetable:
                    station = line[line.index(" ")+1:]
                    start, end = map(time.fromisoformat, line[:line.index(" ")].split("-"))
                    end = time(23, 59, 59) if end == time(0, 0, 0) else end
                    if start < current_time < end:
                        return station
                else:
                    raise RuntimeError("Aucune station programmée à cet horaire.")
        except FileNotFoundError:
            raise RuntimeError("Vous devez créer une configuration d'horaires (fichier timetable.conf).")

    
    def fetch(self):
        """Return metadata of current broadcasted programm for asked station.

        Parameters:
        - station: str - the radio station 
        - token: str - radio france api token

        Returns:
        - json containing data. See fetch_<radio>_meta()
        """

        station = self.get_current_station_name()
        if station in ("France Inter", "France Info", "France Culture", "France Musique"):
            metadata = RadioFranceStation(station).get_metadata()
        elif station == "RTL 2":
            metadata = RTL2().get_metadata()
        else:
            raise RuntimeError("Station '{}' non gérée.".format(station))
        metadata.update({"station": station})
        return metadata


class Station(ABC):
    station_name: str

    def get_metadata(self):
        """Return mapping containing metadata about current broadcast.
        
        This is data meant to be exposed as json and used by format_info() method.
        
        Required fields:
        - type: Emission|Musique|Publicité
        - metadata fields required by format_info() method (see below)
        """

    def format_info(self):
        """Format data for displaying in the card.
        
        Should return a tuple containing:
        - card_title: the title of the current broadcast
        - metadata: mapping containing info about broadcast

        metadata keys:
        - (REQUIRED) station (str): name of the station
        - show_title (str): name of the show if current broadcast is part of a show
        - summary (str): if provided by diffuser, a summary of current broadcast
        - (REQUIRED) thumbnail_src (str): url to thumbnail
        - (REQUIRED) end: timestamp of current broadcast's end

        This method should use metadata collected by get_metadata() method.
        """
    


class RTL2(Station):
    station_name = "RTL 2"
    _main_data_url = "https://timeline.rtl.fr/RTL2/items"
    _songs_data_url = "https://timeline.rtl.fr/RTL2/songs"

    def format_info(self):
        metadata = self.get_metadata()
        if metadata["type"] == "Musique":
            card_title = metadata["artist"] + " • " + metadata["title"]
        else: 
            card_title = metadata["type"]
        return card_title, metadata

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
        default_thumbnail = "https://upload.wikimedia.org/wikipedia/fr/f/fa/RTL2_logo_2015.svg"
        data = self._fetch_metadata()
        if data.get("type") in ("Publicités", "Intermède"):
            data.update({"thumbnail_src": default_thumbnail})
            return data
        artist = data["singer"]
        song = data["title"]
        end = int(data["end"])
        thumbnail = data["thumbnail"] or default_thumbnail
        return {"type": "Musique", "artist": artist, "title": song, "end": end, "thumbnail_src": thumbnail}


class RadioFranceStation(Station):
    def __init__(self, station_name):
        self.station_name = station_name

    @property
    def token(self):
        load_dotenv()
        token = self.__dict__["token"] = os.getenv("TOKEN")
        return token

    grid_template = """
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

    def _build_radio_france_query(self, station: str, start: datetime, end: datetime):
        query = self.grid_template.format(start=int(start.timestamp()), end=int(end.timestamp()), station=station)
        return query

    def format_info(self):
        metadata = self.get_metadata()
        card_title = metadata.get("diffusion_title", metadata["show_title"])
        return card_title, metadata

    def get_metadata(self):
        data = self._fetch_metadata()
        current_show = data["data"]["grid"][0]
        diffusion = current_show.get("diffusion")
        end = int(current_show["end"]) * 1000
        if diffusion is None:
            return {
                "type": "Emission",
                "show_title": current_show["title"],
                "end": end,
                "thumbnail_src": data["thumbnail_src"],
            }
        summary = current_show["diffusion"]["standFirst"]
        return {
            "type": "Emission",
            "show_title": current_show["diffusion"]["show"]["title"],
            "diffusion_title": current_show["diffusion"]["title"],
            "summary": summary if summary != "." else None,
            "end": end,
            "thumbnail_src": data["thumbnail_src"],
        }
    

    def _fetch_metadata(self):
        start = datetime.now()
        end = datetime.now() + timedelta(minutes=120)
        station, thumbnail_src = {
            "France Inter": ("FRANCEINTER", "https://upload.wikimedia.org/wikipedia/fr/thumb/8/8d/France_inter_2005_logo.svg/1024px-France_inter_2005_logo.svg.png"),
            "France Info": ("FRANCEINFO", "https://lh3.googleusercontent.com/VKfyGmPTaHyxOAf1065M_CftsEiGIOkZOiGpXUlP1MTSBUA4j5O5n9GRLJ3HvQsXQdY"),
            "France Culture": ("CULTURE", "https://upload.wikimedia.org/wikipedia/fr/thumb/c/c9/France_Culture_-_2008.svg/1024px-France_Culture_-_2008.svg.png"),
            "France Musique": ("FRANCEMUSIQUE" "https://upload.wikimedia.org/wikipedia/fr/thumb/2/22/France_Musique_-_2008.svg/1024px-France_Musique_-_2008.svg.png"),
        }[self.station_name]
        rep = requests.post("https://openapi.radiofrance.fr/v1/graphql?x-token={}".format(self.token), json={"query": self._build_radio_france_query(station, start, end)})
        data = json.loads(rep.content.decode())
        data.update({"thumbnail_src": thumbnail_src})
        return data
