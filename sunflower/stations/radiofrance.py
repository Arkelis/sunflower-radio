import json
import os
import traceback
from datetime import datetime
from datetime import time
from datetime import timedelta
from logging import Logger
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import TYPE_CHECKING
from typing import Tuple

import requests
from dotenv import load_dotenv
from sunflower.core.custom_types import Broadcast
from sunflower.core.custom_types import BroadcastType
from sunflower.core.custom_types import SongPayload
from sunflower.core.custom_types import Step
from sunflower.core.custom_types import StreamMetadata
from sunflower.core.custom_types import UpdateInfo
from sunflower.core.stations import URLStation
from sunflower.utils import music

if TYPE_CHECKING:
    from sunflower.core.bases import Channel


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
            }}
        }}
        ... on TrackStep {{
            start
            end
            track {{
                title
                albumTitle
                mainArtists
                performers
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

    @staticmethod
    def _notifying_update_info(step):
        return UpdateInfo(should_notify_update=True, step=step)

    def _fetch_metadata(self, start: datetime, end: datetime, retry=0, current=0, raise_exc=False) -> Dict[Any, Any]:
        """Fetch metadata from radiofrance open API."""
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
            if current < retry:
                return self._fetch_metadata(start, end, retry, current + 1, raise_exc)
            if raise_exc:
                raise TimeoutError("Radio France API Timeout")
            return {"message": "API Timeout"}
        data = json.loads(rep.text)
        return data

    @staticmethod
    def _find_current_child_show(children: List[Any], parent: Dict[str, Any], start: int) -> Tuple[Dict, int, bool]:
        """Return current show among children and its end timestamp.

        Sometimes, current timestamp is between 2 children. In this case,
        return parent show and next child start as end.

        Parameters:
        - children: list of dict representing radiofrance steps
        - parent: dict representing radiofrance step
        - start: datetime object representing asked timestamp

        Return a tuple containing:
        - dict representing a step
        - end timestamp
        - True if the current show is child or not
        """

        # on enlève les enfants vides (les TrackStep que l'on ne prend pas en compte)
        children = filter(bool, children)
        # on trie dans l'ordre inverse
        children = sorted(children, key=lambda x: x.get("start"), reverse=True)

        # on initialise l'enfant suivant (par défaut le dernier)
        next_child = children[0]
        # et on parcourt la liste des enfants à l'envers
        for child in children:
            # dans certains cas, le type de step ne nous intéresse pas
            # et est donc vide, on passe directement au suivant
            # (c'est le cas des TrackSteps)
            if child.get("start") is None:
                continue

            # si le début du programme est à venir, on passe au précédent
            if child["start"] > start:
                next_child = child
                continue

            # au premier programme dont le début est avant la date courante
            # on sait qu'on est potentiellement dans le programme courant.
            # Il faut vérifier que l'on est encore dedans en vérifiant :
            if child["end"] > start:
                return child, int(child["end"]), True

            # sinon, on est dans un "trou" : on utilise donc le parent
            # et le début de l'enfant suivant. Cas particulier : si on est
            # entre la fin du dernier enfant et la fin du parent (càd l'enfant
            # suivant est égal à l'enfant courant), on prend la fin du parent.
            elif next_child == child:
                return parent, int(parent["end"]), False
            else:
                return parent, int(next_child["start"]), False
        else:
            # si on est ici, c'est que la boucle a parcouru tous les enfants
            # sans valider child["start"] < now. Autrement dit, le premier
            # enfant n'a pas encore commencé. On renvoie donc le parent et le
            # début du premier enfant (stocké dans next_child) comme end
            return parent, int(next_child.get("start")) or parent["end"], False

    def _handle_api_exception(self, api_data, logger, start) -> Optional[Step]:
        """Return a step if an error in API response was detected. Else return None."""
        error_message: Optional[str] = None
        if "API Timeout" in api_data.values():
            error_message = "API Timeout"
        elif "API rate limit exceeded" in api_data.values():
            error_message = "Radio France API rate limit exceeded"
        elif api_data.get("data") is None:
            error_message = "No data provided by Radio France API"
        elif not api_data["data"]["grid"]:
            error_message = "Grid provided by Radio France API is empty"
        if error_message:
            logger.error(error_message)
        return Step.empty_until(start, start+90, self) if error_message else None

    @staticmethod
    def _get_detailed_metadata(metadata: dict, parent: dict, child: dict, is_child: bool) -> dict:
        """Alter (add detailed information to) a copy of metadata and return it

        :param metadata: metadata to update (this method creates a copy and alter it)
        :param parent: parent broadcast
        :param child: child broadcast (may be identical to parent)
        :param is_child: if True, add parent_show_title and parent_show_link info
        :return: updated copy of metadata input
        """
        detailed_metadata = metadata.copy()
        diffusion = child.get("diffusion") or {}
        show = diffusion.get("show") or {}
        if not is_child:
            diffusion_summary = diffusion.get("standFirst", "") or ""
            if len(diffusion_summary.strip()) == 1:
                diffusion_summary = ""
            detailed_metadata.update({
                "show_link": show.get("url", ""),
                "link": diffusion.get("url", ""),
                "summary": diffusion_summary.strip(),
            })
            return detailed_metadata
        parent_diffusion = parent.get("diffusion") or {}
        parent_show = parent_diffusion.get("show") or {}
        diffusion_summary = diffusion.get("standFirst", "") or parent_diffusion.get("standFirst", "") or ""
        child_show_link = diffusion.get("url", "") or parent_diffusion.get("url", "")
        parent_show_link = parent_show.get("url") or ""
        parent_show_title = parent_show.get("title") or parent["title"]
        # on vérifie que les infos parents ne sont pas redondantes avec les infos enfantes
        if (
            parent_show_link == child_show_link
            or parent_show_title.upper() in (metadata.get("title", "").upper(), metadata.get("show_title", "").upper())
        ):
            parent_show_link = ""
            parent_show_title = ""
        if len(diffusion_summary.strip()) == 1:
            diffusion_summary = ""
        detailed_metadata.update({
            "show_link": show.get("url", ""),
            "link": diffusion.get("url", "") or parent_diffusion.get("url", ""),
            "summary": diffusion_summary.strip(),
            "parent_show_title": parent_show_title,
            "parent_show_link": parent_show_link,
        })
        return detailed_metadata

    def _get_radiofrance_step(self, api_data: dict, dt: datetime, child_precision: bool, detailed: bool) -> Step:
        """Return a track step or a programme step from Radio France depending of contained metadata"""
        return (
            self._get_radiofrance_track_step(api_data, dt)
            if api_data.get("track")
            else self._get_radiofrance_programme_step(api_data, dt, child_precision, detailed)
        )

    def _get_radiofrance_programme_step(self, api_data: dict, dt: datetime, child_precision: bool, detailed: bool):
        """Return radio france step starting at dt.

        Parameters:
        child_precision: bool -- if True, search current child if current broadcast contains any
        detailed: bool -- if True, return more info in step such as summary, external links, parent broadcast
        """
        start = max(int(api_data["start"]), int(dt.timestamp()))
        metadata = {"station": self.station_info, "type": BroadcastType.PROGRAMME}
        children = (api_data.get("children") or []) if child_precision else []
        broadcast, broadcast_end, is_child = (
            self._find_current_child_show(children, api_data, start) if any(children)
            else (api_data, int(api_data["end"]), False)
        )
        diffusion = broadcast.get("diffusion")
        if diffusion is None:
            title = broadcast["title"]
            show_title = ""
            thumbnail_src = self.station_thumbnail
        else:
            show = diffusion.get("show", {})
            title = diffusion.get("title") or show.get("title", "")
            show_title = show.get("title", "") if title != show.get("title", "") else ""
            podcast_link = (show.get("podcast") or {}).get("itunes")
            thumbnail_src = music.fetch_apple_podcast_cover(podcast_link, self.station_thumbnail)
        metadata.update({
            "title": title,
            "show_title": show_title,
            "thumbnail_src": thumbnail_src,
        })
        if detailed:
            metadata = self._get_detailed_metadata(metadata, api_data, broadcast, is_child)
        return Step(start=start, end=broadcast_end, broadcast=Broadcast(**metadata))

    def _get_radiofrance_track_step(self, api_data: dict, dt: datetime):
        start = max(int(api_data["start"]), int(dt.timestamp()))
        track_data = api_data["track"]
        artists = ", ".join(track_data.get("mainArtists") or track_data.get("performers"))
        cover_link, deezer_link = music.fetch_cover_and_link_on_deezer(self.station_thumbnail,
                                                                       artists,
                                                                       track_data.get("albumTitle"))
        return Step(
            start=start,
            end=api_data["end"],
            broadcast=Broadcast(
                title=f"{artists} • {track_data['title']}",
                type=BroadcastType.MUSIC,
                station=self.station_info,
                link=deezer_link,
                summary=self.station_slogan,
                thumbnail_src=cover_link,
                metadata=SongPayload(title=track_data["title"], artist=artists, album=track_data.get("album", ""))
            ),
        )

    def get_step(self, logger: Logger, dt: datetime, channel) -> UpdateInfo:
        start = int(dt.timestamp())
        fetched_data = self._fetch_metadata(dt, dt+timedelta(minutes=120))
        if (error_step := self._handle_api_exception(fetched_data, logger, start)) is not None:
            return self._notifying_update_info(error_step)
        try:
            # on récupère la première émission trouvée
            first_show_in_grid = fetched_data["data"]["grid"][0]
            # si celle-ci est terminée et la suivante n'a pas encore démarrée
            # alors on RENVOIE une métadonnées neutre jusqu'au démarrage de l'émission
            # suivante
            if first_show_in_grid["end"] < start:
                next_show = fetched_data["data"]["grid"][1]
                return self._notifying_update_info(Step.empty_until(start, int(next_show["start"]), self))
            # si l'émission n'est pas encore démarrée, on RENVOIE une métaonnée neutre
            # jusqu'au démarrage de celle-ci
            if first_show_in_grid["start"] > dt.timestamp():
                return self._notifying_update_info(Step.empty_until(start, int(first_show_in_grid['start']), self))
            # cas où on est dans un programme, on RENVOIE les métadonnées de ce programme
            return self._notifying_update_info(
                self._get_radiofrance_step(first_show_in_grid, dt, child_precision=True, detailed=True)
            )

        except Exception as err:
            logger.error(traceback.format_exc())
            logger.error("Données récupérées avant l'exception : {}".format(fetched_data))
            return self._notifying_update_info(Step.empty_until(start, start+90, self))

    def get_next_step(self, logger: Logger, dt: datetime, channel: "Channel") -> Step:
        api_data = self._fetch_metadata(dt, dt+timedelta(minutes=60))
        if (error_step := self._handle_api_exception(api_data, logger, int(dt.timestamp()))) is not None:
            return error_step
        try:
            first_show_in_grid = api_data["data"]["grid"][0]
            return self._get_radiofrance_step(first_show_in_grid, dt, child_precision=True, detailed=False)
        except Exception as err:
            start = int(dt.timestamp())
            logger.error(traceback.format_exc())
            logger.error("Données récupérées avant l'exception : {}".format(api_data))
            return Step.empty_until(start, start+90, self)

    def get_schedule(self, logger: Logger, start: datetime, end: datetime) -> List[Step]:
        api_data = self._fetch_metadata(start, end, retry=5, raise_exc=True)
        temp_end, end = start, end
        steps = []
        grid = api_data["data"]["grid"]
        while grid:
            step_data = grid.pop(0)
            new_step = self._get_radiofrance_programme_step(step_data, temp_end, child_precision=False, detailed=False)
            steps.append(new_step)
            temp_end = datetime.fromtimestamp(new_step.end)
        return steps

    def format_stream_metadata(self, broadcast: Broadcast) -> Optional[StreamMetadata]:
        if broadcast.type == BroadcastType.PROGRAMME:
            artist = self.name
            title, album = (
                (broadcast.show_title, broadcast.title)
                if any(broadcast.show_title)
                else (broadcast.title, "")
            )
            return StreamMetadata(title=title, artist=artist, album=album)
        elif broadcast.type == BroadcastType.MUSIC:
            # for RadioFrance, a track step has metadata already filled, see _get_radiofrance_track_step()
            return broadcast.metadata


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

    WEEKEND_TIME_SLOTS = [
        (time(6, 0, 0), "France Info la nuit"),
        (time(10, 0, 0), "Le 6/10"),
        (time(14, 0, 0), "Le 10/14"),
        (time(17, 0, 0), "Le 14/17"),
        (time(20, 0, 0), "Le 17/20"),
        (time(21, 0, 0), "Les Informés de France Info"),
        (time(23, 59, 59), "Le 21/minuit"),
    ]

    WEEK_TIME_SLOTS = [
        (time(5, 0, 0), "Minuit/5h"),
        (time(7, 0, 0), "Le 5/7"),
        (time(9, 0, 0), "Le 7/9"),
        (time(9, 30, 0), "Les Informés du matin"),
        (time(12, 0, 0), "Le 9h30/Midi"),
        (time(14, 0, 0), "Le 12/14"),
        (time(17, 0, 0), "Le 14/17"),
        (time(20, 0, 0), "Le 17/20"),
        (time(21, 0, 0), "Les Informés de France Info"),
        (time(23, 59, 59), "Le 21/Minuit"),
    ]

    def _get_franceinfo_slot(self, start: datetime) -> Tuple[str, datetime]:
        start_time = start.time()
        slots = self.WEEKEND_TIME_SLOTS if start.weekday() in (5, 6) else self.WEEK_TIME_SLOTS
        for end_time, title in slots:
            if start_time >= end_time:
                continue
            return title, datetime.combine(start.date(), end_time)
        else:
            return slots[0][1], datetime.combine(start.date(), time(6, 0, 0)) + timedelta(days=1)

    def get_schedule(self, logger: Logger, start: datetime, end: datetime) -> List[Step]:
        temp_end, end = start, end
        steps = []
        while temp_end <= end:
            temp_start = temp_end
            title, temp_end = self._get_franceinfo_slot(temp_end)
            steps.append(Step(
                start=int(temp_start.timestamp()),
                end=int(temp_end.timestamp()),
                broadcast=Broadcast(title=title,
                                    type=BroadcastType.PROGRAMME,
                                    station=self.station_info,
                                    thumbnail_src=self.station_thumbnail)
            ))
        return steps


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


class FranceInterParis(RadioFranceStation):
    name = "FIP"
    station_website_url = "https://fip.fr"
    station_slogan = "La radio musicale la plus éclectique"
    _station_api_name = "FIP"
    station_thumbnail = "https://charte.dnm.radiofrance.fr/images/fip-numerique.svg"
    station_url = "http://icecast.radiofrance.fr/fip-hifi.aac"

    def get_next_step(self, logger: Logger, dt: datetime, channel: "Channel") -> Step:
        if self == channel.station_at:
            return Step.none()
        return Step(start=int(dt.timestamp()), end=int(dt.timestamp()), broadcast=Broadcast.empty(self))

    def get_schedule(self, logger: Logger, start: datetime, end: datetime) -> List[Step]:
        return [Step(start=int(start.timestamp()), end=int(end.timestamp()), broadcast=Broadcast.empty(self))]
