import json
from datetime import datetime
from enum import Enum
from typing import List

import aredis
from fastapi import FastAPI
from fastapi import Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import AnyHttpUrl
from pydantic.dataclasses import dataclass as pydantic_dataclass
from server.proxies import PycoloreProxy
from server.utils import channels_ids
from server.utils import get_channel_or_404
from server.utils import redis_repo
from starlette.requests import Request
from starlette.responses import StreamingResponse
from sunflower import settings
from sunflower.core.custom_types import NotifyChangeStatus
from sunflower.core.custom_types import Step
from sunflower.settings import RADIO_NAME

app = FastAPI(
    title=RADIO_NAME,
    docs_url="/",
    redoc_url=None,
    version="1.0.0-beta1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])


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


@app.get(
    "/channels/",
    tags=["Channel-related endpoints"],
    summary="Channels list",
    response_description="List of channels URLs.")
def channels_list(request: Request):
    """Get the list of the channels: their endpoints and a link to their resource."""
    return {channel_id: request.url_for("get_channel", channel_id=channel_id)
            for channel_id in channels_ids}


# @app.get("/stations/", tags=["stations"], summary="Stations list", response_description="List of stations URLs.")
# def stations_list(request: Request):
#     return {endpoint: request.url_for("get_station", station=endpoint)
#             for endpoint in settings.STATIONS}


@app.get(
    "/channels/{channel_id}/",
    summary="Channel information",
    response_description="Channel information and related links",
    tags=["Channel-related endpoints"])
def get_channel(channel_id, request: Request):
    """Display information about one channel :

    - its endpoint
    - its name
    - the url to the current broadcast
    - the url to the next broadcast to be on air
    - the url to the schedule of this channel

    One path parameter is needed: the endpoint of the channel. URLs to all channels are given at /channels/ endpoint.
    """
    channel = get_channel_or_404(channel_id)
    return {
        "endpoint": channel.id,
        "name": channel.id.capitalize(),
        "audio_stream": settings.ICECAST_SERVER_URL + channel.id,
        "current_step": request.url_for("get_current_broadcast_of", channel_id=channel.id),
        "next_step": request.url_for("get_next_broadcast_of", channel_id=channel.id),
        "schedule": request.url_for("get_schedule_of", channel_id=channel.id),
    }


# @app.get("/stations/{station}/", response_model=Station, tags=["stations"])
# @get_station_or_404
# def get_station(station):
#     return {
#         "endpoint": station.endpoint,
#         "name": station.name,
#     }


async def updates_generator(request, *endpoints):
    pubsub = aredis.StrictRedis().pubsub()
    for endpoint in endpoints:
        await pubsub.subscribe("sunflower:channel:" + endpoint)
    while True:
        client_disconnected = await request.is_disconnected()
        if client_disconnected:
            print(datetime.now(), "Disconnected")
            break
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
async def update_broadcast_info_stream(request: Request, channel: List[str] = Query(channels_ids)):
    return StreamingResponse(updates_generator(request, *channel),
                             media_type="text/event-stream",
                             headers={"access-control-allow-origin": "*"})


@app.get(
    "/channels/{channel_id}/current/",
    summary="Get current broadcast",
    tags=["Channel-related endpoints"],
    response_model=Step,
    response_description="Information about current broadcast")
def get_current_broadcast_of(channel_id):
    """Get information about current broadcast on given channel"""
    return get_channel_or_404(channel_id).current


@app.get(
    "/channels/{channel_id}/next/",
    summary="Get next broadcast",
    tags=["Channel-related endpoints"],
    response_model=Step,
    response_description="Information about next broadcast")
def get_next_broadcast_of(channel_id):
    """Get information about next broadcast on given channel"""
    return get_channel_or_404(channel_id).next


@app.get(
    "/channels/{channel_id}/schedule/",
    summary="Get schedule of given channel",
    tags=["Channel-related endpoints"],
    response_model=List[Step],
    response_description="List of steps containing start and end timestamps, and broadcasts")
def get_schedule_of(channel_id):
    """Get information about next broadcast on given channel"""
    return get_channel_or_404(channel_id).schedule

# custom endpoints


class ShapeEnum(str, Enum):
    flat = 'flat'
    groupartist = 'groupartist'


@app.get(
    "/stations/pycolore/playlist/",
    summary="Get the playlist of Pycolore station",
    tags=["Endpoints specific to Radio Pycolore"],
    response_description="List of songs of the playlist")
def get_pycolore_playlist(shape: ShapeEnum = 'flat'):
    """Get information about next broadcast on given channel"""
    if shape == 'flat':
        return PycoloreProxy(redis_repo).playlist
    if shape == 'groupartist':
        playlist = PycoloreProxy(redis_repo).playlist
        sorted_playlist = {}
        for song in playlist:
            try:
                sorted_playlist[song["artist"]].append({'title': song["title"], 'album': song["album"]})
            except KeyError:
                sorted_playlist[song["artist"]] = [{'title': song["title"], 'album': song["album"]}]
        return sorted_playlist
