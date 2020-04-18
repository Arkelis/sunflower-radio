import json
import os
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from sunflower.core.bases import URLStation
from sunflower.core.types import CardMetadata, MetadataType


class RadioFranceStation(URLStation):
    API_RATE_LIMIT_EXCEEDED = 1
    _station_api_name = str()

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

    def get_metadata(self, current_metadata):
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
    station_slogan = "InterVenez"
    _station_api_name = "FRANCEINTER"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/france-inter-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/franceinter-midfi.mp3"


class FranceInfo(RadioFranceStation):
    station_slogan = "Et tout est plus clair"
    station_name = "France Info"
    _station_api_name = "FRANCEINFO"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/franceinfo-carre.svg"
    station_url = "http://icecast.radiofrance.fr/franceinfo-midfi.mp3"


class FranceMusique(RadioFranceStation):
    station_slogan = "Vous allez LA DO RÉ !"
    station_name = "France Musique"
    _station_api_name = "FRANCEMUSIQUE"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/france-musique-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/francemusique-midfi.mp3"


class FranceCulture(RadioFranceStation):
    station_name = "France Culture"
    station_slogan = "L'esprit d'ouverture"
    _station_api_name = "FRANCECULTURE"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/france-culture-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/franceculture-midfi.mp3"
