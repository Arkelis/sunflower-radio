import requests
from datetime import datetime, date, time, timedelta

from bs4 import BeautifulSoup
from dotenv import load_dotenv
import json
import os

from sunflower.utils import RedisMixin

class StationMeta(type):
    def __new__(mcls, name, bases, attrs):
        cls = super().__new__(mcls, name, bases, attrs)
        if not hasattr(cls, "station_name"):
            return cls
        assert hasattr(cls, 'station_thumbnail'), "Station object must define 'station_thumbnail' attribute."
        assert hasattr(cls, 'station_url'), "Station object must define 'station_url' attribute."
        _stations[cls.station_name] = cls
        return cls

class Station(RedisMixin, metaclass=StationMeta):
    """Base station.

    User defined stations should inherit from this class and define following properties:
    - station_name (str)
    - station_thumbnail (str): link to station thumbnail
    - station_url (str): url to music stream
    """

    def get_from_redis(self, key):
        """Get key from redis and perform other checkings."""
        store_data = super().get_from_redis(key)
        if store_data is None:
            return None
        store_data = json.loads(store_data.decode())
        if key == self.REDIS_METADATA:
            if store_data["station"] != self.station_name:
                raise KeyError("Station names not matching.")
        return store_data


    def get_metadata(self):
        """Return mapping containing metadata about current broadcast.
        
        This is data meant to be exposed as json and used by format_info() method.
        
        Required fields:
        - type: Emission|Musique|Publicité
        - metadata fields required by format_info() method (see below)
        """

    def format_info(self, metadata):
        """Format metadata for displaying in the card.
        
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
    station_url = "http://streaming.radio.rtl2.fr/rtl2-1-44-128"
    _main_data_url = "https://timeline.rtl.fr/RTL2/items"
    _songs_data_url = "https://timeline.rtl.fr/RTL2/songs"

    @staticmethod
    def get_show_title(metadata):
        if time(21, 00) < datetime.now().time() < time(22, 00):
            return "RTL 2 Made in France"
        if metadata["type"] == "Musique":
            return "Musique"
        return ""

    def format_info(self, metadata):
        card_info = {
            "current_thumbnail": metadata["thumbnail"],
            "current_broadcast_end": metadata["end"] * 1000, # client needs timestamp in ms
            "current_show_title": self.get_show_title(metadata),
            "current_broadcast_summary": "",
            "current_station": self.station_name,
        }
        if metadata["type"] == "Musique":
            card_info["current_broadcast_title"] = metadata["artist"] + " • " + metadata["title"]
        elif metadata["type"] == "Intermède": 
            card_info["current_broadcast_title"] = "Vous écoutez RTL 2"
        return card_info

    def _fetch_metadata(self, song=False):
        if song:
            rep = requests.get(self._songs_data_url, timeout=1)
            return json.loads(rep.content.decode())[0]
        rep = requests.get(self._main_data_url, timeout=1)
        soup = BeautifulSoup(rep.content.decode(), "html.parser")
        try:
            diffusion_type = soup.find_all("tr")[2].find_all("td")[1].text
        except IndexError:
            previous_url = "/".join(self._main_data_url.split("/")[:3]) + soup.find_all("a")[6].attrs["href"]
            rep = requests.get(previous_url, timeout=1)
            soup = BeautifulSoup(rep.content.decode(), "html.parser")
            try:
                diffusion_type = soup.find_all("tr")[2].find_all("td")[1].text
            except:
                raise RuntimeError("Le titre de la chanson ne peut pas être trouvé.")
        if diffusion_type == "Pubs":
            return {"type": "Publicités", "end": 0}
        if diffusion_type != "Musique":
            return {"type": "Intermède", "end": 0}
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
            "end": int(fetched_data["end"] / 1000),
            "thumbnail": fetched_data["thumbnail"] or self.station_thumbnail,
            "type": "Musique",
        }
        return metadata


class RadioFranceStation(Station):
    API_RATE_LIMIT_EXCEEDED = 1

    def __init__(self):
        super().__init__()
        f = open("/tmp/radiofrance-requests.txt", "a")
        f.close()

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

    def format_info(self, metadata):
        card_info = {
            "current_thumbnail" : metadata["thumbnail_src"],
            "current_broadcast_end": metadata["end"] * 1000, # client needs timestamp in ms
            "current_station": self.station_name,
        }
        if metadata["type"] == "Erreur":
            card_info.update({
                "current_broadcast_title": "Informations indisponibles",
                "current_show_title": "Informations indisponibles",
                "current_broadcast_summary": "Le nombre de requêtes autorisées à l'API de Radio France a été atteinte.",
            })
        elif metadata["type"] == "Emission":
            card_info.update({
                "current_broadcast_title": metadata.get("diffusion_title", metadata["show_title"]),
                "current_show_title": metadata["show_title"],
                "current_broadcast_summary": metadata["summary"],
            })
        return card_info

    def get_metadata(self):
        fetched_data = self._fetch_metadata()
        if fetched_data == self.API_RATE_LIMIT_EXCEEDED:
            return {
                "message": "Radio France API rate limit exceeded",
                "type": "Erreur",
                "station": self.station_name,
                "end": 0,
                "thumbnail_src": self.station_thumbnail,
            }
        try:
            current_show = fetched_data["data"]["grid"][0]
            next_show = fetched_data["data"]["grid"][1]
            diffusion = current_show.get("diffusion")
            metadata = {
                "type": "Emission",
                "end": int(next_show["start"]),
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
        except KeyError as err:
            raise RuntimeError("Impossible de décoder la réponse de l'API radiofrance : {}".format(fetched_data)) from err
    

    def _fetch_metadata(self):
        radiofrance_requests_counter_path = "/tmp/radiofrance-requests.txt"
        api_rate_limit = 1000
        with open(radiofrance_requests_counter_path, "r") as f:
            lines = f.read().split("\n")
        if lines[0] != datetime.now().date().isoformat():
            write_mode = "w"
        else:
            if len(lines) >= api_rate_limit:
                return self.API_RATE_LIMIT_EXCEEDED
            write_mode = "a"
        with open(radiofrance_requests_counter_path, write_mode) as f:
            f.write("{}\n".format(datetime.now().date()))
        start = datetime.now()
        end = datetime.now() + timedelta(minutes=120)
        query = self._grid_template.format(
            start=int(start.timestamp()),
            end=int(end.timestamp()),
            station=self._station_api_name
        )
        rep = requests.post(
            url="https://openapi.radiofrance.fr/v1/graphql?x-token={}".format(self.token),
            json={"query": query},
            timeout=4,
        )
        data = json.loads(rep.content.decode())
        return data


class FranceInter(RadioFranceStation):
    station_name = "France Inter"
    _station_api_name = "FRANCEINTER"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/france-inter-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/franceinter-midfi.mp3"


class FranceInfo(RadioFranceStation):
    station_name = "France Info"
    _station_api_name = "FRANCEINFO"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/franceinfo-carre.svg"
    station_url = "http://icecast.radiofrance.fr/franceinfo-midfi.mp3"


class FranceMusique(RadioFranceStation):
    station_name = "France Musique"
    _station_api_name = "FRANCEMUSIQUE"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/france-musique-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/francemusique-midfi.mp3"


class FranceCulture(RadioFranceStation):
    station_name = "France Culture"
    _station_api_name = "FRANCECULTURE"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/france-culture-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/franceculture-midfi.mp3"
