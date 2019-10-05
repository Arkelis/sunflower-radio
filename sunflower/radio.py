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
                if start < current_time < end:
                    return station
    except FileNotFoundError:
        raise RuntimeError("Vous devez créer une configuration d'horaires (fichier timetable.conf).")

def build_radio_france_query(station: str, start: datetime, end: datetime, template=GRID_TEMPLATE):
    query = template.format(start=int(start.timestamp()), end=int(end.timestamp()), station=station)
    return query

def format_radio_france_metadata(rep):
    data = json.loads(rep.content.decode())
    current_show = data["data"]["grid"][0]
    return {
        "type": "Emission",
        "show_title": current_show["diffusion"]["show"]["title"],
        "diffusion_title": current_show["diffusion"]["title"],
        "summary": current_show["diffusion"]["standFirst"],
    }
    

def fetch_radio_france_meta(station, token):
    start = datetime.now()
    end = datetime.now() + timedelta(minutes=120)
    station = {
        "France Inter": "FRANCEINTER",
        "France Info": "FRANCEINFO",
        "France Culture": "CULTURE",
        "France Musique": "FRANCEMUSIQUE"
    }[station]
    rep = requests.post("https://openapi.radiofrance.fr/v1/graphql?x-token={}".format(token), json={"query": build_radio_france_query(station, start, end)})
    data = format_radio_france_metadata(rep)
    data.update({"type":"Emission"})
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
        previous_url = soup.find_all("a")[6].attrs["href"]
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
    end = datetime.fromtimestamp(int(data[0]["end"]) // 1000).isoformat()
    return {"type": "Musique", "artist": artist, "title": song, "end": end}

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
    metadata.update({"station": station})
    return metadata

if __name__ == "__main__":
    print(fetch(get_current_station()))
