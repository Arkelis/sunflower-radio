import requests
from datetime import datetime, date, time, timedelta

from bs4 import BeautifulSoup
from dotenv import load_dotenv
import json
import os

from sunflower.utils import RedisMixin, CardMetadata, MetadataType

class Station(RedisMixin):
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
        - type: element of MetadataType enum (see utils.py)
        - metadata fields required by format_info() method (see below)
        """

    def format_info(self, metadata) -> CardMetadata:
        """Format metadata for displaying in the card.
        
        Should return a CardMetadata namedtuple (see utils.py).
        If empty, a given key should have "" (empty string) as value, and not None.
        Don't support MetadataType.NONE case as it is done in Channel class.
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
        if metadata["type"] == MetadataType.MUSIC:
            return MetadataType.MUSIC
        return ""

    def format_info(self, metadata) -> CardMetadata:
        return CardMetadata(
            current_thumbnail=metadata["thumbnail"],
            current_show_title=self.get_show_title(metadata),
            current_broadcast_summary="",
            current_station=self.station_name,
            current_broadcast_title="{} • {}".format(metadata["artist"], metadata["title"]),
        )

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
            return {"type": MetadataType.ADS, "end": 0}
        if diffusion_type != "Musique":
            return {"type": MetadataType.NONE, "end": 0}
        else:
            return self._fetch_metadata(True)

    def get_metadata(self):
        """Returns mapping containing info about current song.

        If music: {"type": MetadataType.MUSIC, "artist": artist, "title": title}
        If ads: "type": MetadataType.ADS
        Else: "type": MetadataType.NONE

        Moreover, returns other metadata for postprocessing.
        end datetime object

        To sum up, here are the keys of returned mapping:
        - type: str
        - end: str (ISO format) or 0 if unknown
        - artist: str (optionnal)
        - title: str (optionnal)
        """
        fetched_data = self._fetch_metadata()
        if fetched_data.get("type") in (MetadataType.ADS, MetadataType.NONE):
            return fetched_data
        metadata = {
            "artist": fetched_data["singer"],
            "title": fetched_data["title"],
            "end": int(fetched_data["end"] / 1000),
            "thumbnail": fetched_data.get("thumbnail") or self.station_thumbnail,
            "type": MetadataType.MUSIC,
        }
        return metadata


class RadioFranceStation(Station):
    API_RATE_LIMIT_EXCEEDED = 1
    station_name = str()

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

    def format_info(self, metadata) -> CardMetadata:
        card_info = {
            "current_thumbnail" : metadata["thumbnail_src"],
            "current_station": self.station_name,
        }
        if metadata["type"] == "Erreur":
            card_info.update({
                "current_broadcast_title": "Vous écoutez {}".format(self.station_name),
                "current_show_title": "Informations indisponibles",
                "current_broadcast_summary": "Le nombre de requêtes autorisées à l'API de Radio France a été atteinte.",
            })
        elif metadata["type"] == MetadataType.PROGRAMME:
            card_info.update({
                "current_broadcast_title": metadata.get("diffusion_title", metadata["show_title"]),
                "current_show_title": metadata["show_title"],
                "current_broadcast_summary": metadata["summary"],
            })
        return CardMetadata(**card_info)

    def get_metadata(self):
        fetched_data = self._fetch_metadata()
        if fetched_data == self.API_RATE_LIMIT_EXCEEDED:
            return {
                "message": "Radio France API rate limit exceeded",
                "type": "Erreur",
                "end": int((datetime.now() + timedelta(hours=24)).timestamp()),
                "thumbnail_src": self.station_thumbnail,
            }
        try:
            first_show_in_grid = fetched_data["data"]["grid"][0]
            # si la dernière émission est terminée et la suivante n'a pas encore démarrée
            if first_show_in_grid["end"] < int(datetime.now().timestamp()):
                next_show = fetched_data["data"]["grid"][1]
                return {
                    "type": MetadataType.NONE,
                    "end": int(next_show["start"]),
                }
            if first_show_in_grid["start"] > int(datetime.now().timestamp()):
                return {
                    "type": MetadataType.NONE,
                    "end": int(first_show_in_grid["start"]),
                }
            # sinon on traite les différentes formes d'émissions possibles
            diffusion = first_show_in_grid.get("diffusion")
            metadata = {
                "type": MetadataType.PROGRAMME,
                "end": int(first_show_in_grid["end"]),
                "thumbnail_src": self.station_thumbnail,
            }
            # il n'y a pas d'info sur la diffusion mais uniquement l'émission
            if diffusion is None:
                metadata.update({
                    "show_title": first_show_in_grid["title"],
                    "summary": "",
                })
            # il y a à la fois les infos de la diffusion et de l'émission
            else:
                summary = first_show_in_grid["diffusion"]["standFirst"]
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
    station_url = "http://icecast.radiofrance.fr/franceinter-hifi.aac"


class FranceInfo(RadioFranceStation):
    station_name = "France Info"
    _station_api_name = "FRANCEINFO"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/franceinfo-carre.svg"
    station_url = "http://icecast.radiofrance.fr/franceinfo-hifi.aac"


class FranceMusique(RadioFranceStation):
    station_name = "France Musique"
    _station_api_name = "FRANCEMUSIQUE"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/france-musique-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/francemusique-hifi.aac"


class FranceCulture(RadioFranceStation):
    station_name = "France Culture"
    _station_api_name = "FRANCECULTURE"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/france-culture-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/franceculture-hifi.aac"
