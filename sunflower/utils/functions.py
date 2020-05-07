"""Utilitary classes used in several parts of sunflower application."""

import functools
import glob
import json
from typing import List

import random
from collections import namedtuple

import mutagen
import requests
from flask import abort
import redis

from sunflower import settings
from sunflower.core.types import Song
from sunflower.core.types import ChannelView

# Custom views

r = redis.Redis()

def get_channel_or_404(view_function):
    @functools.wraps(view_function)
    def wrapper(channel: str):
        if channel not in settings.CHANNELS:
            abort(404)
        channel_view = ChannelView(channel)
        return view_function(channel_view)
    return wrapper

# utils functions

def prevent_consecutive_artists(songs_list: List[Song]) -> List[Song]:
    """Make sure two consecutive songs never have the same artist.
    
    Parameter: songs_list, a list of sunflower.core.types.Song objects.
    Return: a new list (this function doesnt mutate input list, it creates a copy)
    """
    songs: List[Song] = list(songs_list)
    number_of_songs = len(songs_list)
    for i in range(number_of_songs-1):
        j = 2
        n = 0
        while songs[i].artist == songs[i+1].artist:
            if n > number_of_songs * 5:
                break
            if i + j >= number_of_songs - 1:
                j -= number_of_songs
            if songs[i+j-1].artist == songs[i+1].artist == songs[i+j+1].artist:
                n, j = n + 1, j + 1
                continue
            songs[i+1], songs[i+j] = songs[i+j], songs[i+1]
            n, j = n + 1, j + 1
    return songs

def parse_songs(glob_pattern: str) -> List[Song]:
    """Parse songs matching glob_pattern and return a list of Song objects.
    
    Song object is a namedtuple defined in sunflower.core.types module.
    """
    songs: List[Song] = []
    for path in glob.iglob(glob_pattern):
        file = mutagen.File(path)
        try:
            songs.append(Song(
                path,
                file.get("artist", [None])[0],
                file.get("album", [None])[0],
                file.get("title", [None])[0],
                int(file.info.length),
            ))
        except KeyError as err:
            raise KeyError("Song file {} must have an artist and a title in metadata.".format(path)) from err
    random.shuffle(songs)
    return songs

def fetch_cover_and_link_on_deezer(backup_cover, artist, album=None, track=None):
    """Get cover from Deezer API.

    Search for a track with given artist and track. 
    Take the cover of the album of the first found track.
    """
    if album is not None:
        req = requests.get('https://api.deezer.com/search/album?q={} {}'.format(artist, album))
    elif track is not None:
        req = requests.get('https://api.deezer.com/search/track?q={} {}'.format(artist, track))
    else:
        req = requests.get('https://api.deezer.com/search/artist?q={}'.format(artist))

    data = json.loads(req.content.decode())["data"]
    if not data:
        return backup_cover, ""
    obj = data[0]

    if album is not None:
        cover_src = obj["cover_big"]
        album_url = obj["link"]
    elif track is not None:
        cover_src = obj["album"]["cover_big"]
        album_url = f"https://www.deezer.com/album/{obj['album']['id']}"
    else:
        cover_src = obj["picture_big"]
        album_url = ""
    return cover_src, album_url
