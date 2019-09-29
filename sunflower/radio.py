import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

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
    print(query)
    return query

def fetch_grid(station, token=TOKEN):
    start = datetime.now()
    end = datetime.now() + timedelta(minutes=120)
    rep = requests.post("https://openapi.radiofrance.fr/v1/graphql?x-token={}".format(token), json={"query": build_radio_france_query(station, start, end)})
    print(rep.content.decode())

if __name__ == "__main__":
    fetch_grid("FRANCEINTER")
