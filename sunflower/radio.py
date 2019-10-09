# This is Sunflower Radio app.

"""Module containing radio metadata fetching related functions."""

import json
import os
from datetime import datetime, time, timedelta

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

FLUX_URL = {
    "France Inter": "http://icecast.radiofrance.fr/franceinter-midfi.mp3",
    "France Culture": "http://icecast.radiofrance.fr/franceculture-midfi.mp3",
    "France Musique": "http://icecast.radiofrance.fr/francemusique-midfi.mp3",
    "France Info": "http://icecast.radiofrance.fr/franceinfo-midfi.mp3",
    "RTL 2": "http://streaming.radio.rtl2.fr/rtl2-1-48-192",
}

GRID_TEMPLATE = """
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

def get_current_station():
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

def build_radio_france_query(station: str, start: datetime, end: datetime, template=GRID_TEMPLATE):
    query = template.format(start=int(start.timestamp()), end=int(end.timestamp()), station=station)
    return query

def format_radio_france_metadata(rep):
    data = json.loads(rep.content.decode())
    current_show = data["data"]["grid"][0]
    diffusion = current_show.get("diffusion")
    if diffusion is None:
        return {
            "type": "Emission",
            "show_title": current_show["title"],
        }
    summary = current_show["diffusion"]["standFirst"]
    return {
        "type": "Emission",
        "show_title": current_show["diffusion"]["show"]["title"],
        "diffusion_title": current_show["diffusion"]["title"],
        "summary": summary if summary != "." else None,
        "end": current_show["end"],
    }
    

def fetch_radio_france_meta(station, token):
    start = datetime.now()
    end = datetime.now() + timedelta(minutes=120)
    station, thumbnail_src = {
        "France Inter": ("FRANCEINTER", "https://upload.wikimedia.org/wikipedia/fr/thumb/8/8d/France_inter_2005_logo.svg/1024px-France_inter_2005_logo.svg.png"),
        "France Info": ("FRANCEINFO", "https://lh3.googleusercontent.com/VKfyGmPTaHyxOAf1065M_CftsEiGIOkZOiGpXUlP1MTSBUA4j5O5n9GRLJ3HvQsXQdY"),
        "France Culture": ("CULTURE", "https://upload.wikimedia.org/wikipedia/fr/thumb/c/c9/France_Culture_-_2008.svg/1024px-France_Culture_-_2008.svg.png"),
        "France Musique": ("FRANCEMUSIQUE" "https://upload.wikimedia.org/wikipedia/fr/thumb/2/22/France_Musique_-_2008.svg/1024px-France_Musique_-_2008.svg.png"),
    }[station]
    rep = requests.post("https://openapi.radiofrance.fr/v1/graphql?x-token={}".format(token), json={"query": build_radio_france_query(station, start, end)})
    data = format_radio_france_metadata(rep)
    data.update({"type":"Emission", "thumbnail_src": thumbnail_src})
    return data

def fetch_rtl2_meta():
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

    rep = requests.get("https://timeline.rtl.fr/RTL2/items")
    soup = BeautifulSoup(rep.content.decode(), "html.parser")
    try:
        diffusion_type = soup.find_all("tr")[2].find_all("td")[1].text
    except IndexError:
        previous_url = "https://timeline.rtl.fr" + soup.find_all("a")[6].attrs["href"]
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
    rep = requests.get("https://timeline.rtl.fr/RTL2/songs")
    data = json.loads(rep.content.decode())
    artist = data[0]["singer"]
    song = data[0]["title"]
    end = int(data[0]["end"]) // 1000
    thumbnail = data[0]["thumbnail"]
    return {"type": "Musique", "artist": artist, "title": song, "end": end, "thumbnail_src": thumbnail}

def fetch(station, token=TOKEN):
    """Return metadata of current broadcasted programm for asked station.

    Parameters:
    - station: str - the radio station 
    - token: str - radio france api token

    Returns:
    - json containing data. See fetch_<radio>_meta()
    """
    if station in ("France Inter", "France Info", "France Culture", "France Musique"):
        metadata = fetch_radio_france_meta(station, token)
    elif station == "RTL 2":
        metadata = fetch_rtl2_meta()
    else:
        raise RuntimeError("Station '{}' non gérée.".format(station))
    metadata.update({"station": station})
    return metadata

if __name__ == "__main__":
    print(fetch(get_current_station()))
