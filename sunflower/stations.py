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
    station_name = str()
    station_thumbnail = str()
    station_url = str()

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
    def _get_show_title():
        if time(21, 00) < datetime.now().time() < time(22, 00):
            return "RTL 2 Made in France"
        return ""

    def format_info(self, metadata) -> CardMetadata:
        current_broadcast_title = {
            MetadataType.ADS: "Publicité",
            MetadataType.MUSIC: "{} • {}".format(metadata.get("artist"), metadata.get("title")),
        }.get(metadata["type"], "Vous écoutez RTL 2")

        return CardMetadata(
            current_thumbnail=metadata["thumbnail_src"],
            current_show_title=self._get_show_title(),
            current_broadcast_summary="",
            current_station=self.station_name,
            current_broadcast_title=current_broadcast_title,
        )

    def _fetch_song_metadata(self):
        """Return mapping containing song info"""
        rep = requests.get(self._songs_data_url, timeout=1)
        return json.loads(rep.content.decode())[0]

    def _fetch_metadata(self):
        """Fetch data from timeline.rtl.fr.
        
        Scrap from items page. If song object detected, get data from songs endpoint.
        Else return MetadataType object. 
        """
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
            return {"type": MetadataType.ADS}
        if diffusion_type != "Musique":
            return {"type": MetadataType.NONE}
        else:
            return self._fetch_song_metadata()

    def get_metadata(self):
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
        fetched_data = self._fetch_metadata()
        thumbnail_src = fetched_data.get("thumbnail") or self.station_thumbnail
        fetched_data_type = fetched_data.get("type")

        if fetched_data_type in (MetadataType.ADS, MetadataType.NONE):
            return {
                "thumbnail_src": thumbnail_src,
                "type": fetched_data_type,
                "end": 0,
            }

        end = int(fetched_data["end"] / 1000)
        if datetime.now().timestamp() > end:
            return {
                "thumbnail_src": thumbnail_src,
                "type": MetadataType.NONE,
                "end": 0,
            }

        return {
            "artist": fetched_data["singer"],
            "title": fetched_data["title"],
            "end": end,
            "type": MetadataType.MUSIC,
            "thumbnail_src": thumbnail_src,
        }


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

    _grid_template = """{{
    grid(start: {start}, end: {end}, station: {station}) {{
        ... on DiffusionStep {{
            start
            end
            diffusion {{
                title
                standFirst
                show {{
                    podcast {{
                        itunes
                    }}
                    title
                }}
            }}
            children {{
                ... on DiffusionStep {{
                    start
                    end
                    diffusion {{
                        title
                        standFirst
                        show {{
                            podcast {{
                                itunes
                            }}
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
            }
            # il n'y a pas d'info sur la diffusion mais uniquement l'émission
            if diffusion is None:
                metadata.update({
                    "show_title": first_show_in_grid["title"],
                    "summary": "",
                    "thumbnail_src": self.station_thumbnail,
                })
            # il y a à la fois les infos de la diffusion et de l'émission
            else:
                summary = diffusion["standFirst"]
                if not summary or summary == ".":
                    summary = ""
                podcast_link = diffusion["show"]["podcast"]["itunes"]
                thumbnail_src = self._fetch_cover(podcast_link)
                metadata.update({
                    "show_title": diffusion["show"]["title"],
                    "diffusion_title": diffusion["title"],
                    "summary": summary,
                    "thumbnail_src": thumbnail_src,
                })
            return metadata
        except KeyError as err:
            raise RuntimeError("Impossible de décoder la réponse de l'API radiofrance : {}".format(fetched_data)) from err
    

    def _fetch_cover(self, podcast_link):
        """Scrap cover url from provided Apple Podcast link."""
        req = requests.get(podcast_link)
        bs = BeautifulSoup(req.content.decode(), "html.parser")
        sources = bs.find_all("source")
        cover_url = sources[2].attrs["srcset"].split(",")[2].replace(" 3x", "")
        return cover_url


    def _fetch_metadata(self):
        """Fetch metadata from radiofrance open API."""
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
