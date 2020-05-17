import json
import os
import traceback
from datetime import datetime, timedelta
from logging import Logger
from typing import Dict, Any, List

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from sunflower.core.bases import URLStation
from sunflower.core.types import CardMetadata, MetadataType, MetadataDict

RADIO_FRANCE_GRID_TEMPLATE = """
{{
    grid(start: {start}, end: {end}, station: {station}) {{
        ... on DiffusionStep {{
            start
            end
            diffusion {{
                url
                title
                standFirst
                show {{
                    url
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
                        url
                        title
                        standFirst
                        show {{
                            url
                            podcast {{
                                itunes
                            }}
                            title
                        }}
                    }}
                }}
                ... on BlankStep {{
                    start
                    end
                    title
                }}
            }}
        }}
        ... on BlankStep {{
            start
            end
            title
            children {{
                ... on DiffusionStep {{
                    start
                    end
                    diffusion {{
                        url
                        title
                        standFirst
                        show {{
                            url
                            podcast {{
                                itunes
                            }}
                            title
                        }}
                    }}
                }}
                ... on BlankStep {{
                    start
                    end
                    title
                }}
            }}
        }}
    }}
}}
"""


class RadioFranceStation(URLStation):
    API_RATE_LIMIT_EXCEEDED = 1
    _station_api_name: str
    _grid_template = RADIO_FRANCE_GRID_TEMPLATE

    @property
    def token(self):
        if os.getenv("TOKEN") is None: # in case of development server
            load_dotenv()
            if os.getenv("TOKEN") is None:
                raise RuntimeError("No token for Radio France API found.")
        return os.getenv("TOKEN")

    def format_info(self, current_info: CardMetadata, metadata: MetadataDict, logger: Logger) -> CardMetadata:
        assert metadata["type"] == MetadataType.PROGRAMME, "Type de métadonnées non gérée : {}".format(metadata["type"])
        parent_title = metadata.get("parent_title")
        if metadata.get("diffusion_title") is None:
            current_broadcast_title = metadata["show_title"]
            current_show_title = parent_title or ""
        else:
            show_title = metadata["show_title"]
            if parent_title is not None and show_title.lower() != parent_title.lower():
                show_title += " • " + parent_title
            current_broadcast_title = self._format_html_anchor_element(metadata.get("diffusion_url"), metadata["diffusion_title"])
            current_show_title = self._format_html_anchor_element(metadata.get("show_url"), show_title)
        return CardMetadata(
            current_thumbnail=metadata["thumbnail_src"],
            current_station=self.html_formated_station_name,
            current_broadcast_title=current_broadcast_title,
            current_show_title=current_show_title,
            current_broadcast_summary=metadata.get("diffusion_summary") or "",
        )

    def get_metadata(self, current_metadata: MetadataDict, logger: Logger, dt: datetime):
        fetched_data = self._fetch_metadata(dt)
        if "API Timeout" in fetched_data.values():
            return self._get_error_metadata("API Timeout", 90) 
        if "API rate limit exceeded" in fetched_data.values():
            return self._get_error_metadata("Radio France API rate limit exceeded", 90)
        try:
            # on récupère la première émission trouvée
            first_show_in_grid = fetched_data["data"]["grid"][0]

            # si celle-ci est terminée et la suivante n'a pas encore démarrée
            # alors on RENVOIE une métadonnées neutre jusqu'au démarrage de l'émission
            # suivante
            if first_show_in_grid["end"] < int(dt.timestamp()):
                next_show = fetched_data["data"]["grid"][1]
                return {
                    "station": self.station_name,
                    "type": MetadataType.NONE,
                    "end": int(next_show["start"]),
                }
            
            # si l'émission n'est pas encore démarrée, on RENVOIE une métaonnée neutre
            # jusqu'au démarrage de celle-ci
            if first_show_in_grid["start"] > int(dt.timestamp()):
                return {
                    "station": self.station_name,
                    "type": MetadataType.NONE,
                    "end": int(first_show_in_grid["start"]),
                }

            # Sinon on traite les différentes formes d'émissions possibles.
            # On initialise le dictionnaire de métadonnées avec les infos de
            # base
            metadata = {"station": self.station_name, "type": MetadataType.PROGRAMME}

            # Un step peut avoir une liste de sous-programmes enfants
            children = first_show_in_grid.get("children")

            # on teste si children n'est pas None et n'est pas vide
            if children:
                # on récupère l'enfant en cours et sa fin
                current_show, current_show_end = self._find_current_child_show(children, first_show_in_grid, dt)
                # ici, on réupère le titre du parent pour l'ajouter dans les métadonnées
                parent = first_show_in_grid
                 # ajout de parent title s'il est différent du titre du current show
                if parent.get("diffusion") is None:
                    parent_title = parent["title"]
                else:
                    parent_title = parent["diffusion"]["show"]["title"]
            else:
                # sinon on garde le premier élément de la grille récupérée
                current_show, current_show_end = first_show_in_grid, int(first_show_in_grid["end"])
                # et le parent est vide
                parent = {}
                parent_title = ""

            # on peut maintenant ajouter la fin aux métadonnées
            metadata["end"] = current_show_end

            # on récupère le sous-objet diffusion s'il existe
            diffusion = current_show.get("diffusion")
            # on récupère celui du parent s'il existe si diffusion est nul
            if diffusion is None:
                parent_diffusion = parent.get("diffusion")
            else:
                parent_diffusion = None

            # si l'émission (l'objet Step pour l'api Radiofrance) ne possède
            # pas de sous-objet diffusion, il s'agit d'un format "simple" :
            # un simple titre.
            if diffusion is None and parent_diffusion is None:
                show_title = current_show["title"]
                metadata.update({
                    "show_title": show_title,
                    "thumbnail_src": self.station_thumbnail,
                })

            # si le sous-objet diffusion est trouvé, on l'utilise pour enrichir
            # les métadonnées : titre de l'émission, titre de la diffusion (diffusion
            # = un "numéro" de l'émission), éventuellement un résumé et une miniature
            # spéciale (on la récupère en parsant la page de podcast)
            else:
                # métadonnées de diffusion
                # cas où seul parent_diffusion n'est pas nul
                if diffusion is None:
                    # on garde le titre du step comme titre de diffusion
                    diffusion_title = current_show["title"]
                    # et le reste des infos proviennent du parent
                    diffusion = parent_diffusion
                else:
                    diffusion_title = diffusion["title"]
                diffusion_summary = diffusion["standFirst"]
                if not diffusion_summary or diffusion_summary in (".", "*"):
                    diffusion_summary = ""
                
                # métadonnées d'émission (show)
                show = diffusion.get("show", (parent_diffusion or {}).get("show", {}))
                podcast_link = show.get("podcast", {}).get("itunes")
                thumbnail_src = self._fetch_cover(podcast_link)
                show_title = show.get("title", "")
                show_url = show.get("url", "")

                # update metadata dict
                metadata.update({
                    "show_title": show_title,
                    "show_url": show_url,
                    "diffusion_title": diffusion_title,
                    "diffusion_url": diffusion.get("url", ""),
                    "diffusion_summary": diffusion_summary.strip(),
                    "thumbnail_src": thumbnail_src,
                })

            if parent_title and parent_title.lower().strip() != show_title.lower().strip():
                metadata.update({"parent_title": parent_title})

            # on RENVOIE alors les métadonnées
            return metadata
        except KeyError as err:
            logger.error(traceback.format_exc())
            logger.error("Données récupérées avant l'exception : {}".format(fetched_data))
            return self._get_error_metadata("Error during API response parsing: {}".format(err), 90) 
    

    def _fetch_cover(self, podcast_link):
        """Scrap cover url from provided Apple Podcast link."""
        if not podcast_link:
            return self.station_thumbnail
        req = requests.get(podcast_link)
        bs = BeautifulSoup(req.content.decode(), "html.parser")
        sources = bs.find_all("source")
        cover_url = sources[0].attrs["srcset"].split(",")[1].replace(" 2x", "")
        return cover_url


    def _fetch_metadata(self, dt: datetime):
        """Fetch metadata from radiofrance open API."""
        start = dt
        end = start + timedelta(minutes=120)
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
    
    @staticmethod
    def _find_current_child_show(children: List[Any], parent: Dict[str, Any], dt: datetime):
        """Return current show among children and its end timestamp.

        Sometimes, current timestamp is between 2 children. In this case,
        return parent show and next child start as end.

        Parameters:
        - children: list of dict representing radiofrance steps
        - parent: dict representing radiofrance step

        Return a tuple containing:
        - dict representing a step
        - end timestamp
        """

        # on initialise l'enfant suivant (par défaut le dernier)
        next_child = children[-1]
        # et on parcourt la liste des enfants à l'envers
        for child in reversed(children):
            # dans certains cas, le type de step ne nous intéresse pas
            # et est donc vide, on passe directement au suivant
            # (c'est le cas des TrackSteps)
            if child.get("start") is None:
                continue

            # si le début du programme est à venir, on passe au précédent
            if child["start"] > dt:
                next_child = child
                continue
            
            # au premier programme dont le début est avant la date courante
            # on sait qu'on est potentiellement dans le programme courant.
            # Il faut vérifier que l'on est encore dedans en vérifiant :
            if child["end"] > dt:
                return child, int(child["end"])

            # sinon, on est dans un "trou" : on utilise donc le parent
            # et le début de l'enfant suivant. Cas particulier : si on est
            # entre la fin du dernier enfant et la fin du parent (càd l'enfant
            # suivant est égal à l'enfant courant), on prend la fin du parent.
            elif next_child == child:
                return parent, int(parent["end"])
            else:
                return parent, int(next_child["start"])
        else:
            # si on est ici, c'est que la boucle a parcouru tous les enfants
            # sans valider child["start"] < now. Autrement dit, le premier
            # enfant n'a pas encore commencé. On renvoie donc le parent et le
            # début du premier enfant (stocké dans next_child) comme end
            return parent, int(next_child["start"])
    


class FranceInter(RadioFranceStation):
    station_name = "France Inter"
    station_website_url = "https://www.franceinter.fr"
    station_slogan = "Inter-Venez"
    _station_api_name = "FRANCEINTER"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/france-inter-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/franceinter-hifi.aac"


class FranceInfo(RadioFranceStation):
    station_name = "France Info"
    station_website_url = "https://www.francetvinfo.fr"
    station_slogan = "Et tout est plus clair"
    _station_api_name = "FRANCEINFO"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/franceinfo-carre.svg"
    station_url = "http://icecast.radiofrance.fr/franceinfo-hifi.aac"


class FranceMusique(RadioFranceStation):
    station_name = "France Musique"
    station_website_url = "https://www.francemusique.fr"
    station_slogan = "Vous allez LA DO RÉ !"
    _station_api_name = "FRANCEMUSIQUE"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/france-musique-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/francemusique-hifi.aac"


class FranceCulture(RadioFranceStation):
    station_name = "France Culture"
    station_website_url = "https://www.franceculture.fr"
    station_slogan = "L'esprit d'ouverture"
    _station_api_name = "FRANCECULTURE"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/france-culture-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/franceculture-hifi.aac"
