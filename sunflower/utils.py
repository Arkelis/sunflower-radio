"""Utilitary classes used in several parts of sunflower application."""

import functools
import glob
import json
import random
import telnetlib
from collections import namedtuple
from datetime import datetime
from enum import Enum

import mutagen
import redis
import requests
from flask import abort

from sunflower import settings

# Mixins

class RedisMixin:
    """Provide a method to access data from redis database.
    
    Define REDIS_KEYS containing keys the application has right 
    to access.
    """

    REDIS_KEYS = [
        item 
        for name in settings.CHANNELS 
        for item in ("sunflower:{}:metadata".format(name), "sunflower:{}:info".format(name))
    ]
    
    REDIS_CHANNELS = {name: "sunflower:" + name for name in settings.CHANNELS}

    def __init__(self, *args, **kwargs):
        self._redis = redis.Redis()

    def get_from_redis(self, key, object_hook=None):
        """Get value for given key from Redis.
        
        Data got from Redis is loaded from json with given object_hook.
        If no data is found, return None.
        """
        assert key in self.REDIS_KEYS, "Only {} keys are used by this application.".format(self.REDIS_KEYS)
        raw_data = self._redis.get(key)
        if raw_data is None:
            return None
        return json.loads(raw_data.decode(), object_hook=object_hook)
    
    def set_to_redis(self, key, value, json_encoder_cls=None):
        """Set new value for given key in Redis.
        
        value is dumped as json with given json_encoder_cls.
        """
        assert key in self.REDIS_KEYS, "Only {} keys are used by this application.".format(self.REDIS_KEYS)
        json_data = json.dumps(value, cls=json_encoder_cls)
        return self._redis.set(key, json_data, ex=86400)

    def publish_to_redis(self, channel, data):
        """publish a message to a redis channel.

        Parameters:
        - channel (str): channel name
        - data (jsonable data or str): data to publish
        
        channel in redis is prefixed with 'sunflower:'.
        """
        assert channel in self.REDIS_CHANNELS, "Channel not defined in settings."
        if not isinstance(data, str):
            data = json.dumps(data)
        self._redis.publish(self.REDIS_CHANNELS[channel], data)

# Custom views

def get_channel_or_404(view_function):
    @functools.wraps(view_function)
    def wrapper(channel):
        if channel not in settings.CHANNELS:
            abort(404)
        from sunflower.channels import CHANNELS
        return view_function(channel=CHANNELS[channel])
    return wrapper

# Custom datamodel

Song = namedtuple("Song", ["path", "artist", "title", "length"])
CardMetadata = namedtuple("CardMetadata", ["current_thumbnail",
                                           "current_station",
                                           "current_broadcast_title",
                                           "current_show_title",
                                           "current_broadcast_summary",])

# Available metadata types

class MetadataType(Enum):
    MUSIC = "Musique"
    PROGRAMME = "Emission"
    NONE = ""
    ADS = "Publicité"
    ERROR = "Erreur"

class MetadataEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, MetadataType):
            return obj.value
        return json.JSONEncoder.default(self, obj)

def as_metadata_type(mapping):
    type_ = mapping.get("type")
    if type_ is None:
        return mapping
    for member in MetadataType:
        if type_ == member.value:
            mapping["type"] = MetadataType(type_)
            break
    return mapping

# utils functions

def parse_songs(glob_pattern):
    """Parse songs matching glob_pattern and return a list of Song objects.
    
    Song object is a namedtuple defined in sunflower.utils module.
    """
    songs = []
    if not glob_pattern.endswith(".ogg"):
        raise RuntimeError("Only ogg files are supported.")
    for path in glob.iglob(glob_pattern):
        file = mutagen.File(path)
        try:
            songs.append(Song(
                path,
                file["artist"][0],
                file["title"][0],
                int(file.info.length),
            ))
        except KeyError as err:
            raise KeyError("Song file {} must have an artist and a title in metadata.".format(path)) from err
    random.shuffle(songs)
    return songs

def fetch_cover_on_deezer(artist, track, backup_cover):
    """Get cover from Deezer API.

    Search for a track with given artist and track. 
    Take the cover of the album of the first found track.
    """
    req = requests.get('https://api.deezer.com/search/track?q={} {}'.format(artist, track))
    data = json.loads(req.content.decode())["data"]
    if not data:
        return backup_cover
    track = data[0]
    cover_src = track["album"]["cover_big"]
    return cover_src

# utils classes

class AdsHandler:
    def __init__(self, channel):
        self.channel = channel
        self.glob_pattern = settings.BACKUP_SONGS_GLOB_PATTERN
        self.backup_songs = self._parse_songs()

    def _fetch_cover_on_deezer(self, artist, track):
        return fetch_cover_on_deezer(artist, track, self.channel.current_station.station_thumbnail)

    def _parse_songs(self):
        return parse_songs(self.glob_pattern)

    def process(self, metadata, info, logger) -> (dict(), CardMetadata):
        """Play backup songs if advertising is detected on currently broadcasted station."""
        if metadata["type"] == MetadataType.ADS:
            self.channel.logger.info("Ads detected.")
            if not self.backup_songs:
                self.channel.logger.info("Backup songs list must be generated.")
                self.backup_songs = self._parse_songs()
            backup_song = self.backup_songs.pop(0)

            # tell liquidsoap to play backup song
            session = telnetlib.Telnet("localhost", 1234)
            session.write("{}_custom_songs.push {}\n".format(self.channel.endpoint, backup_song.path).encode())
            session.close()
            
            type_ = MetadataType.MUSIC
            station = metadata["station"]
            artist = backup_song.artist
            title = backup_song.title
            thumbnail = self._fetch_cover_on_deezer(artist, title)

            # and update metadata
            metadata = {
                "artist": artist,
                "title": title,
                "end": int(datetime.now().timestamp()) + backup_song.length,
                "type": type_,
                "station": station,
                "thumbnail_src": thumbnail,
            }
            info = CardMetadata(
                current_thumbnail=thumbnail,
                current_station=station,
                current_broadcast_title=backup_song.artist + " • " + backup_song.title,
                current_show_title=type_,
                current_broadcast_summary="Publicité en cours sur {}. Dans un instant, retour sur la station.".format(station),
            )
        return metadata, info
