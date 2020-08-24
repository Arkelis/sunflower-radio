import asyncio
from typing import List

import redis
from fastapi import FastAPI
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
    allow_origins=["http://localhost:1234", "http://0.0.0.0:1234"],
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


@app.get("/channels/", tags=["Channels-related endpoints"], summary="Channels list", response_description="List of channels URLs.")
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
    tags=["Channels-related endpoints"]
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
        "current_step": channel.current_step,
        "next_step": channel.next_step,
        "schedule": request.url_for("get_schedule_of", channel=channel.endpoint),
    }


# @app.get("/stations/{station}/", response_model=Station, tags=["stations"])
# @get_station_or_404
# def get_station(station):
#     return {
#         "endpoint": station.endpoint,
#         "name": station.name,
#     }


async def updates_generator(endpoint):
    pubsub = redis.Redis().pubsub()
    pubsub.subscribe("sunflower:channel:" + endpoint)
    while True:
        await asyncio.sleep(4)
        message = pubsub.get_message()
        if message is None:
            continue
        redis_data = message.get("data")
        data_to_send = {
            str(NotifyChangeStatus.UNCHANGED.value).encode(): "unchanged",
            str(NotifyChangeStatus.UPDATED.value).encode(): "updated"
        }.get(redis_data)
        if data_to_send is None:
            continue
        yield f"data: {data_to_send}\n\n"


@app.get("/channels/{channel}/events/", include_in_schema=False)
async def update_broadcast_info_stream(channel):
    return StreamingResponse(updates_generator(channel), media_type="text/event-stream", headers={"access-control-allow-origin": "*"})


@app.get(
    "/channels/{channel}/current/",
    summary="Get current broadcast",
    tags=["Channels-related endpoints"],
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
    tags=["Channels-related endpoints"],
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
    tags=["Channels-related endpoints"],
    response_model=List[Step],
    response_description="List of steps containing start and end timestamps, and broadcasts"
)
@get_channel_or_404
def get_schedule_of(channel):
    """Get information about next broadcast on given channel"""
    return channel.schedule

# custom endpoints

@app.get(
    "/stations/pycolore/playlist/",
    summary="Get the playlist of Pycolore station",
    tags=["Endpoints specific to Radio Pycolore"],
    response_description="List of songs of the playlist"
)
def get_pycolore_playlist():
    """Get information about next broadcast on given channel"""
    return PycoloreStationProxy().public_playlist

