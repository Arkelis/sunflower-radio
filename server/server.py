import json
from enum import Enum
from typing import List

import aredis
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import AnyHttpUrl
from pydantic.dataclasses import dataclass as pydantic_dataclass
from starlette.requests import Request
from starlette.responses import StreamingResponse

from server.proxies import PycoloreStationProxy
from server.utils import get_channel_or_404
from sunflower import settings
from sunflower.core.custom_types import NotifyChangeStatus, Step
from sunflower.settings import RADIO_NAME

app = FastAPI(title=RADIO_NAME, docs_url="/", redoc_url=None, version="1.0.0-beta1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# models

# This dataclass represents a real Channel object in the API
@pydantic_dataclass
class Channel:
    endpoint: str
    name: str
    audio_stream: AnyHttpUrl
    current_step: AnyHttpUrl
    next_step: AnyHttpUrl
    schedule: AnyHttpUrl

#
# @app.get("/", summary="API root", response_description="Redirect to channels lists.", tags=["general"])
# def api_root(request: Request):
#     """Redirect to channels lists."""
#     return RedirectResponse(request.url_for("channels_list"))


@app.get("/channels/", tags=["Channel-related endpoints"], summary="Channels list", response_description="List of channels URLs.")
def channels_list(request: Request):
    """Get the list of the channels: their endpoints and a link to their resource."""
    return {endpoint: request.url_for("get_channel", channel=endpoint)
            for endpoint in settings.CHANNELS}


# @app.get("/stations/", tags=["stations"], summary="Stations list", response_description="List of stations URLs.")
# def stations_list(request: Request):
#     return {endpoint: request.url_for("get_station", station=endpoint)
#             for endpoint in settings.STATIONS}


@app.get(
    "/channels/{channel}/",
    summary="Channel information",
    response_description="Channel information and related links",
    # response_model=Channel,
    tags=["Channel-related endpoints"]
)
@get_channel_or_404
def get_channel(channel, request: Request):
    """Display information about one channel :

    - its endpoint
    - its name
    - the url to the current broadcast
    - the url to the next broadcast to be on air
    - the url to the schedule of this channel

    One path parameter is needed: the endpoint of the channel. URLs to all channels are given at /channels/ endpoint.
    """
    return {
        "endpoint": channel.endpoint,
        "name": channel.endpoint.capitalize(),
        "audio_stream": settings.ICECAST_SERVER_URL + channel.endpoint,
        "current_step": request.url_for("get_current_broadcast_of", channel=channel.endpoint),
        "next_step": request.url_for("get_next_broadcast_of", channel=channel.endpoint),
        "schedule": request.url_for("get_schedule_of", channel=channel.endpoint),
    }


# @app.get("/stations/{station}/", response_model=Station, tags=["stations"])
# @get_station_or_404
# def get_station(station):
#     return {
#         "endpoint": station.endpoint,
#         "name": station.name,
#     }


async def updates_generator(*endpoints):
    pubsub = aredis.StrictRedis().pubsub()
    for endpoint in endpoints:
        await pubsub.subscribe("sunflower:channel:" + endpoint)
    while True:
        message = await pubsub.get_message()
        if message is None:
            continue
        redis_data = message.get("data")
        if redis_data == str(NotifyChangeStatus.UNCHANGED.value).encode():
            yield ":\n\n"
            continue
        if redis_data != str(NotifyChangeStatus.UPDATED.value).encode():
            continue
        redis_channel = message.get("channel").decode()
        channel_endpoint = redis_channel.split(":")[-1]
        data_to_send = {"channel": channel_endpoint, "status": "updated"}
        yield f'data: {json.dumps(data_to_send)}\n\n'


@app.get("/events", tags=["Server-sent events"])
async def update_broadcast_info_stream(channel: List[str] = Query(None)):
    if channel is None:
        channel = ['musique', 'tournesol']
    return StreamingResponse(updates_generator(*channel),
                             media_type="text/event-stream",
                             headers={"access-control-allow-origin": "*"})


@app.get(
    "/channels/{channel}/current/",
    summary="Get current broadcast",
    tags=["Channel-related endpoints"],
    response_model=Step,
    response_description="Information about current broadcast"
)
@get_channel_or_404
def get_current_broadcast_of(channel):
    """Get information about current broadcast on given channel"""
    return channel.current_step

@app.get(
    "/channels/{channel}/next/",
    summary="Get next broadcast",
    tags=["Channel-related endpoints"],
    response_model=Step,
    response_description="Information about next broadcast"
)
@get_channel_or_404
def get_next_broadcast_of(channel):
    """Get information about next broadcast on given channel"""
    return channel.next_step

@app.get(
    "/channels/{channel}/schedule/",
    summary="Get schedule of given channel",
    tags=["Channel-related endpoints"],
    response_model=List[Step],
    response_description="List of steps containing start and end timestamps, and broadcasts"
)
@get_channel_or_404
def get_schedule_of(channel):
    """Get information about next broadcast on given channel"""
    return channel.schedule

# custom endpoints


class ShapeEnum(str, Enum):
    flat = 'flat'
    groupartist = 'groupartist'


@app.get(
    "/stations/pycolore/playlist/",
    summary="Get the playlist of Pycolore station",
    tags=["Endpoints specific to Radio Pycolore"],
    response_description="List of songs of the playlist",

)
def get_pycolore_playlist(shape: ShapeEnum = 'flat'):
    """Get information about next broadcast on given channel"""
    if shape == 'flat':
        return PycoloreStationProxy().public_playlist
    if shape == 'groupartist':
        playlist = PycoloreStationProxy().public_playlist
        sorted_playlist = {}
        for song in playlist:
            try:
                sorted_playlist[song["artist"]].append({'title': song["title"], 'album': song["album"]})
            except KeyError:
                sorted_playlist[song["artist"]] = [{'title': song["title"], 'album': song["album"]}]
        return sorted_playlist
