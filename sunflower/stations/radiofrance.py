import json
import os
import traceback
from datetime import datetime, time, timedelta
from logging import Logger
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

from sunflower.core.bases import URLStation
from sunflower.core.custom_types import Broadcast, BroadcastType, Step, StreamMetadata
from sunflower.utils.music import fetch_apple_podcast_cover

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

    # def format_info(self, current_info: CardMetadata, metadata: MetadataDict, logger: Logger) -> CardMetadata:
    #     assert metadata["type"] == BroadcastType.PROGRAMME, "Type de métadonnées non gérée : {}".format(metadata["type"])
    #     parent_title = metadata.get("parent_title")
    #     if metadata.get("diffusion_title") is None:
    #         current_broadcast_title = metadata["show_title"]
    #         current_show_title = parent_title or ""
    #     else:
    #         show_title = metadata["show_title"]
    #         if parent_title is not None and show_title.lower() != parent_title.lower():
    #             show_title += " • " + parent_title
    #         current_broadcast_title = self._format_html_anchor_element(metadata.get("diffusion_url"), metadata["diffusion_title"])
    #         current_show_title = self._format_html_anchor_element(metadata.get("show_url"), show_title)
    #     return CardMetadata(
    #         current_thumbnail=metadata["thumbnail_src"],
    #         current_station=self.html_formatted_station_name,
    #         current_broadcast_title=current_broadcast_title,
    #         current_show_title=current_show_title,
    #         current_broadcast_summary=metadata.get("diffusion_summary") or "",
    #     )

    def get_step(self, logger: Logger, dt: datetime, channel, for_schedule=False) -> Step:
        start = int(dt.timestamp())
        fetched_data = self._fetch_metadata(dt)
        if "API Timeout" in fetched_data.values():
            logger.error("API Timeout")
            return Step.empty_until(start, start + 90, self)
        if "API rate limit exceeded" in fetched_data.values():
            logger.error("Radio France API rate limit exceeded")
            return Step.empty_until(start, start + 90, self)
        try:
            # on récupère la première émission trouvée
            first_show_in_grid = fetched_data["data"]["grid"][0]

            # si celle-ci est terminée et la suivante n'a pas encore démarrée
            # alors on RENVOIE une métadonnées neutre jusqu'au démarrage de l'émission
            # suivante (sauf dans le cas où on demande le programme)
            if first_show_in_grid["end"] < start:
                next_show = fetched_data["data"]["grid"][1]
                if for_schedule:
                    first_show_in_grid = next_show
                else:
                    return Step.empty_until(start, int(next_show["start"]), self)
            
            # si l'émission n'est pas encore démarrée, on RENVOIE une métaonnée neutre
            # jusqu'au démarrage de celle-ci
            if first_show_in_grid["start"] > dt.timestamp() and not for_schedule:
                return Step.empty_until(start, int(first_show_in_grid['start']), self)

            # Sinon on traite les différentes formes d'émissions possibles.
            # On initialise le dictionnaire de métadonnées avec les infos de
            # base
            metadata = {"station": self.station_info, "type": BroadcastType.PROGRAMME}

            # Un step peut avoir une liste de sous-programmes enfants
            children = (
                first_show_in_grid.get("children")
                if not for_schedule
                else []
            )

            # on teste si children n'est pas None et n'est pas vide
            if children:
                # on récupère l'enfant en cours et sa fin
                current_show, current_show_end = self._find_current_child_show(children, first_show_in_grid, dt)
                # ici, on réupère le titre du parent pour l'ajouter dans les métadonnées
                parent = first_show_in_grid
                 # ajout de parent title s'il est différent du titre du current show
                if parent.get("diffusion") is None:
                    parent_title = parent["title"]
                    parent_url = ""
                else:
                    parent_title = parent["diffusion"]["show"]["title"]
                    parent_url = parent["diffusion"]["show"]["url"]
            else:
                # sinon on garde le premier élément de la grille récupérée
                current_show, current_show_end = first_show_in_grid, int(first_show_in_grid["end"])
                # et le parent est vide
                parent = {}
                parent_title = ""
                parent_url = ""

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
                    "title": show_title,
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
                if not diffusion_summary or len(diffusion_summary.strip()) == 1:
                    diffusion_summary = ""
                
                # métadonnées d'émission (show)
                # show = attribut "show" de diffusion ou attribut "show" du parent ou {} s'il vaut None
                show = diffusion.get("show", (parent_diffusion or {}).get("show")) or {}
                podcast_link = (show.get("podcast") or {}).get("itunes")
                thumbnail_src = fetch_apple_podcast_cover(podcast_link, self.station_thumbnail)
                show_title = show.get("title", "")
                show_url = show.get("url", "")

                # update metadata dict
                metadata.update({
                    "show_title": show_title,
                    "show_link": show_url,
                    "title": diffusion_title,
                    "link": diffusion.get("url", ""),
                    "summary": diffusion_summary.strip(),
                    "thumbnail_src": thumbnail_src,
                })

            if parent_title and parent_title.lower().strip() != show_title.lower().strip():
                metadata.update({"parent_show_title": parent_title, "parent_show_link": parent_url})

            # on RENVOIE alors les métadonnées
            return Step(start=start, end=current_show_end, broadcast=Broadcast(**metadata))
        except Exception as err:
            logger.error(traceback.format_exc())
            logger.error("Données récupérées avant l'exception : {}".format(fetched_data))
            if for_schedule:
                raise RuntimeError("An error occurred during making schedule")
            return Step.empty_until(start, start+90, self)

    def format_stream_metadata(self, broadcast: Broadcast) -> Optional[StreamMetadata]:
        artist = self.name
        title, album = {
            True: (broadcast.show_title, broadcast.title),
            False: (broadcast.title, ""),
        }[any(broadcast.show_title)]
        return StreamMetadata(title=title, artist=artist, album=album)

    def _fetch_metadata(self, dt: datetime) -> Dict[Any, Any]:
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
        data = json.loads(rep.text)
        return data
    
    @staticmethod
    def _find_current_child_show(children: List[Any], parent: Dict[str, Any], dt: datetime):
        """Return current show among children and its end timestamp.

        Sometimes, current timestamp is between 2 children. In this case,
        return parent show and next child start as end.

        Parameters:
        - children: list of dict representing radiofrance steps
        - parent: dict representing radiofrance step
        - dt: datetime object representing asked timestamp

        Return a tuple containing:
        - dict representing a step
        - end timestamp
        """
        
        dt_timestamp = dt.timestamp()

        # on trie dans l'ordre inverse
        children = sorted(children, key=lambda x: x.get("start"), reverse=True)

        # on initialise l'enfant suivant (par défaut le dernier)
        next_child = children[-1]
        # et on parcourt la liste des enfants à l'envers
        for child in children:
            # dans certains cas, le type de step ne nous intéresse pas
            # et est donc vide, on passe directement au suivant
            # (c'est le cas des TrackSteps)
            if child.get("start") is None:
                continue

            # si le début du programme est à venir, on passe au précédent
            if child["start"] > dt_timestamp:
                next_child = child
                continue
            
            # au premier programme dont le début est avant la date courante
            # on sait qu'on est potentiellement dans le programme courant.
            # Il faut vérifier que l'on est encore dedans en vérifiant :
            if child["end"] > dt_timestamp:
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
            return parent, int(next_child.get("start")) or parent["end"]
    

class FranceInter(RadioFranceStation):
    name = "France Inter"
    station_website_url = "https://www.franceinter.fr"
    station_slogan = "Inter-Venez"
    _station_api_name = "FRANCEINTER"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/france-inter-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/franceinter-hifi.aac"


class FranceInfo(RadioFranceStation):
    name = "France Info"
    station_website_url = "https://www.francetvinfo.fr"
    station_slogan = "Et tout est plus clair"
    _station_api_name = "FRANCEINFO"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/franceinfo-carre.svg"
    station_url = "http://icecast.radiofrance.fr/franceinfo-hifi.aac"

    def get_step(self, logger: Logger, dt: datetime, channel, for_schedule=False) -> Step:
        if for_schedule:
            start = int(dt.timestamp())
            if not time(19, 55) < dt.time() < time(21, 0):
                return Step.empty_until(start=start, end=start, station=self)
            else:
                return Step(
                    start=int(datetime.combine(dt.date(), time(20, 0)).timestamp()),
                    end=int(datetime.combine(dt.date(), time(21, 0)).timestamp()),
                    broadcast=Broadcast(
                        title="Les Informés de France Info",
                        type=BroadcastType.PROGRAMME,
                        station=self.station_info,
                        thumbnail_src="https://cdn.radiofrance.fr/s3/cruiser-production/2019/08/8eff949c-a7a7-4e1f-b3c0-cd6ad1a2eabb/1400x1400_rf_omm_0000022892_ite.jpg",
                ))
        return super().get_step(logger, dt, channel, for_schedule)


class FranceMusique(RadioFranceStation):
    name = "France Musique"
    station_website_url = "https://www.francemusique.fr"
    station_slogan = "Vous allez LA DO RÉ !"
    _station_api_name = "FRANCEMUSIQUE"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/france-musique-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/francemusique-hifi.aac"


class FranceCulture(RadioFranceStation):
    name = "France Culture"
    station_website_url = "https://www.franceculture.fr"
    station_slogan = "L'esprit d'ouverture"
    _station_api_name = "FRANCECULTURE"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/france-culture-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/franceculture-hifi.aac"
