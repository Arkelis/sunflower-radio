import asyncio
import json
from collections import defaultdict
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
    return [
        {
            "id": channel_id,
            "name": channel_id.capitalize(),
            "url": request.url_for("get_channel", channel_id=channel_id),
            "schedule_url": request.url_for("get_schedule_of", channel_id=channel_id),
            "current_step": get_channel_or_404(channel_id).current,
            "next_step": get_channel_or_404(channel_id).next,
            "audio_stream": settings.ICECAST_SERVER_URL + channel_id,
        }
        for channel_id in channels_ids]


@app.get(
    "/channels/{channel_id}",
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
        "current_step": channel.current,
        "next_step": channel.next,
        "schedule": request.url_for("get_schedule_of", channel_id=channel.id),
    }


async def updates_generator(request, *endpoints):
    pubsub = aredis.StrictRedis().pubsub()
    for endpoint in endpoints:
        await pubsub.subscribe(f"sunflower:channel:{endpoint}:updates")
    while True:
        client_disconnected = await request.is_disconnected()
        if client_disconnected:
            print(datetime.now(), "Disconnected")
            break
        try:
            message = await asyncio.wait_for(pubsub.get_message(), timeout=4)
        except asyncio.TimeoutError:
            yield ":\n\n"
        if message is None:
            continue
        redis_data = message.get("data")
        if redis_data != str(NotifyChangeStatus.UPDATED.value).encode():
            continue
        redis_channel = message.get("channel").decode()
        channel_endpoint = redis_channel.split(":")[2]
        data_to_send = {"channel": channel_endpoint, "status": "updated"}
        yield f'data: {json.dumps(data_to_send)}\n\n'


@app.get("/events", tags=["Server-sent events"])
async def update_broadcast_info_stream(request: Request, channel: List[str] = Query(channels_ids)):
    return StreamingResponse(updates_generator(request, *channel),
                             media_type="text/event-stream",
                             headers={"access-control-allow-origin": "*"})


@app.get(
    "/channels/{channel_id}/schedule",
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
    "/stations/pycolore/playlist",
    summary="Get the playlist of Pycolore station",
    tags=["Endpoints specific to Radio Pycolore"],
    response_description="List of songs of the playlist")
def get_pycolore_playlist(shape: ShapeEnum = ShapeEnum.flat.value):
    """Get information about next broadcast on given channel"""
    if shape == ShapeEnum.flat.value:
        return PycoloreProxy(redis_repo).playlist
    if shape == ShapeEnum.groupartist.value:
        playlist = PycoloreProxy(redis_repo).playlist
        sorted_playlist = defaultdict(list)
        for song in playlist:
            sorted_playlist[song["artist"]].append({'title': song["title"], 'album': song["album"]})
        return sorted_playlist
