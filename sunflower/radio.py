import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import os
import time
from bs4 import BeautifulSoup

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
        url
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

def build_radio_france_query(station: str, start: datetime, end: datetime, template=GRID_TEMPLATE):
    query = template.format(start=int(start.timestamp()), end=int(end.timestamp()), station=station)
    return query

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
    return rep.content.decode()

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
    diffusion_type = soup.find_all("tr")[2].find_all("td")[1].text
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
    if station in ("France Inter", "France Info", "France Culture", "France Musique"):
        metadata = fetch_radio_france_meta(station, token)
    elif station == "RTL 2":
        metadata = fetch_rtl2_meta()
        metadata.update({"station": station})
    return metadata

if __name__ == "__main__":
    print(fetch("inter"))
    print(fetch("rtl2"))
