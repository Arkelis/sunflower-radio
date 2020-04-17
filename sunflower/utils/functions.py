"""Utilitary classes used in several parts of sunflower application."""

import functools
import glob
import json

import random
from collections import namedtuple

import mutagen
import requests
from flask import abort

from sunflower import settings
from sunflower.core.types import Song

# Custom views

def get_channel_or_404(view_function):
    @functools.wraps(view_function)
    def wrapper(channel):
        if channel not in settings.CHANNELS:
            abort(404)
        from sunflower.channels import CHANNELS
        return view_function(channel=CHANNELS[channel])
    return wrapper

# utils functions

def parse_songs(glob_pattern):
    """Parse songs matching glob_pattern and return a list of Song objects.
    
    Song object is a namedtuple defined in sunflower.utils module.
    """
    songs = []
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

def fetch_cover_on_deezer(backup_cover, artist, album=None, track=None):
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
        return backup_cover
    obj = data[0]

    if album is not None:
        cover_src = obj["cover_big"]
    elif track is not None:
        cover_src = obj["album"]["cover_big"]
    else:
        cover_src = obj["picture_big"]

    return cover_src
