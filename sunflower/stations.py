import requests
from datetime import datetime, date, time, timedelta
import telnetlib

from bs4 import BeautifulSoup
from dotenv import load_dotenv
import json
import os

from sunflower import settings
from sunflower.utils import CardMetadata, MetadataType, parse_songs, fetch_cover_on_deezer

class Station:
    """Base station.

    User defined stations should inherit from this class and define following properties:
    - station_name (str)
    - station_thumbnail (str): link to station thumbnail
    - station_url (str): url to music stream
    """
    station_name = str()
    station_thumbnail = str()
    station_url = str()


    def _get_error_metadata(self, message, seconds):
        return {
            "type": MetadataType.ERROR,
            "message": message,
            "end": int((datetime.now() + timedelta(seconds=seconds)).timestamp()),
            "thumbnail_src": self.station_thumbnail,
        }


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

    def _fetch_song_metadata(self, retry=0):
        """Return mapping containing song info"""
        try:
            rep = requests.get(self._songs_data_url, timeout=1)
            return json.loads(rep.content.decode())[0]
        except requests.exceptions.Timeout:
            if (retry == 11):
                return self._get_error_metadata("API Timeout", 90)
            return self._fetch_song_metadata(retry+1)

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
                previous_url = "/".join(self._main_data_url.split("/")[:3]) + soup.find_all("a")[6].attrs["href"]
                rep = requests.get(previous_url, timeout=1)
                soup = BeautifulSoup(rep.content.decode(), "html.parser")
                try:
                    diffusion_type = soup.find_all("tr")[2].find_all("td")[1].text
                except:
                    raise RuntimeError("Le titre de la chanson ne peut pas être trouvé.")
        except requests.exceptions.Timeout:
            if (retry == 11):
                return self._get_error_metadata("API Timeout", 90)
            return self._fetch_metadata(retry+1)
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
        thumbnail_src = fetched_data.get("cover") or self.station_thumbnail
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
    _station_api_name = str()

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
        assert metadata["type"] == MetadataType.PROGRAMME, "Type de métadonnées non gérée : {}".format(metadata["type"])
        if metadata.get("diffusion_title") is None:
            current_broadcat_title = metadata["show_title"]
            current_show_title = ""
        else:
            current_broadcat_title = metadata["diffusion_title"]
            current_show_title = metadata["show_title"]
        return CardMetadata(
            current_thumbnail=metadata["thumbnail_src"],
            current_station=self.station_name,
            current_broadcast_title=current_broadcat_title,
            current_show_title=current_show_title,
            current_broadcast_summary=metadata["summary"],
        )

    def get_metadata(self):
        fetched_data = self._fetch_metadata()
        if "API Timeout" in fetched_data.values():
            return self._get_error_metadata("API Timeout", 90) 
        if "API rate limit exceeded" in fetched_data.values():
            return self._get_error_metadata("Radio France API rate limit exceeded", 90)
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
        cover_url = sources[0].attrs["srcset"].split(",")[1].replace(" 2x", "")
        return cover_url


    def _fetch_metadata(self):
        """Fetch metadata from radiofrance open API."""
        # radiofrance_requests_counter_path = "/tmp/radiofrance-requests.txt"
        # api_rate_limit = 1000
        # with open(radiofrance_requests_counter_path, "r") as f:
        #     lines = f.read().split("\n")
        # if lines[0] != datetime.now().date().isoformat():
        #     write_mode = "w"
        # else:
        #     if len(lines) >= api_rate_limit:
        #         return self.API_RATE_LIMIT_EXCEEDED
        #     write_mode = "a"
        # with open(radiofrance_requests_counter_path, write_mode) as f:
        #     f.write("{}\n".format(datetime.now().date()))
        start = datetime.now()
        end = datetime.now() + timedelta(minutes=120)
        query = self._grid_template.format(
            start=int(start.timestamp()),
            end=int(end.timestamp()),
            station=self._station_api_name
        )
        try:
            rep = requests.post(
                url="https://openapi.radiofrance.fr/v1/graphql?x-token={}".format(self.token),
                json={"query": query},
                timeout=4,
            )
        except requests.exceptions.Timeout:
            return {"message": "API Timeout"}
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


class PycolorePlaylistStation(Station):
    station_name = "Radio Pycolore"
    station_thumbnail = "https://upload.wikimedia.org/wikipedia/commons/c/ce/Sunflower_clip_art.svg"
    
    def __init__(self):
        self._songs_to_play = []
        self._current_song = None
        self._current_song_end = 0

    def _get_next_song(self, max_length):
        if not self._songs_to_play:
            self._songs_to_play = parse_songs(settings.BACKUP_SONGS_GLOB_PATTERN)
        for (i, song) in enumerate(self._songs_to_play):
            if song.length < max_length:
                return self._songs_to_play.pop(i)
        return None

    @property
    def _artists(self):
        """Property returning artists of the 5 next-played songs."""
        songs_to_play = self._songs_to_play
        artists_set = {self._current_song.artist}
        for song in songs_to_play:
            artists_set.add(song.artist)
            if len(artists_set) == 5:
                break
        return artists_set
        
    def _play(self, delay, max_length):
        self._current_song = self._get_next_song(max_length)
        if self._current_song is None:
            self._current_song_end = int(datetime.now().timestamp()) + max_length
            return
        self._current_song_end = int((datetime.now() + timedelta(seconds=self._current_song.length)).timestamp()) + delay
        formated_station_name = self.station_name.lower().replace(" ", "")
        session = telnetlib.Telnet("localhost", 1234)
        session.write("{}_station_queue.push {}\n".format(formated_station_name, self._current_song.path).encode())
        session.close()

    def get_metadata(self):
        if self._current_song is None:
            return {
                "type": MetadataType.WAITING_FOLLOWING,
                "end": self._current_song_end,
            }
        return {
            "type": MetadataType.MUSIC,
            "artist": self._current_song.artist,
            "title": self._current_song.title,
            "thumbnail_src": fetch_cover_on_deezer(self._current_song.artist, self._current_song.title, self.station_thumbnail),
            "end": self._current_song_end,
        }

    def format_info(self, metadata):
        artists_str = ", ".join(self._artists)
        return CardMetadata(
            current_thumbnail=metadata["thumbnail_src"],
            current_station=self.station_name,
            current_broadcast_title="{} • {}".format(metadata["artist"], metadata["title"]),
            current_show_title="La playlist Pycolore",
            current_broadcast_summary="Une sélection aléatoire de chansons parmi les musiques stockées sur Pycolore. Au menu : {}...".format(artists_str),
        )

    def process(self, channel):
        """Play new song if needed."""
        now = datetime.now()
        if self._current_song_end - 10 < int(now.timestamp()):
            delay = max(self._current_song_end - int(now.timestamp()), 0)
            end_of_current_station = datetime.combine(date.today(), channel.get_station_info(now.time())[1])
            max_length = (end_of_current_station - now).seconds - delay
            self._play(delay, max_length)

    @classmethod
    def get_liquidsoap_config(cls):
        formated_name = cls.station_name.lower().replace(" ", "")
        string = '{0} = fallback(track_sensitive=false, [request.queue(id="{0}_station_queue"), default])\n'.format(formated_name)
        return string
