"""Utilitary classes used in several parts of sunflower application."""

from sunflower.core.config import K
from sunflower.core.config import get_config
from fastapi import HTTPException
from server.proxies import ChannelProxy
from sunflower.core.repository import RedisRepository


redis_repo = RedisRepository()

definitions = get_config()
channels_definitions = definitions[K("channels")]
channels_ids = [channel_def[K("id")] for channel_def in channels_definitions]


def get_channel_or_404(channel: str):
    if channel not in channels_ids:
        raise HTTPException(404, f"Channel {channel} does not exist")
    return ChannelProxy(redis_repo, channel)
