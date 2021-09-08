"""Utilitary classes used in several parts of sunflower application."""
import base64
import glob
from functools import lru_cache
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import mutagen
import requests
from bs4 import BeautifulSoup
from sunflower.core.custom_types import Song


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
                path=path,
                artist=file.get("artist", file.get("author", [""]))[0],
                album=file.get("album", [""])[0],
                title=file.get("title", [""])[0],
                length=file.info.length,
            ))
        except KeyError as err:
            raise KeyError("Song file {} must have an artist and a title in metadata.".format(path)) from err
    return sorted(songs, key=lambda song: (song.artist + song.title).lower())


def _get_data_from_deezer_url(*urls: str,
                              getcover: Callable, getalbumurl: Callable,
                              getmatch: Callable[[Any], str] = None, match: str = None) -> Optional[Tuple[str, str]]:
    """Get json from given urls and return first relevant (cover_url, album_url) tuple.

    If no relevant data is found, return None.

    An endpoint of deezer api returns a list of objects. This function iterates on these json objects converted as dict
    to find and return the first relevant (cover_url, album_url) tuple thanks to getitem and match parameters. If they
    are not provided, the first element of the first list returned by an endpoint is returned.

    Parameters:

    - `*urls`: urls to fetch (in order)
    - `getcover()`: callable taking one dict as argument and returning cover from it
    - `getalbumurl()`: callable taking one dict as argument and returning album url from it

    Item filtering can be done with two optional parameters:

    - getitem: callable taking one dict as argument and returning an object relevant for filtering
    - match: an object which will be compared to the result of getitem(obj).

    If `getmatch(obj) == match` is evaluated True, this object is considered as relevant.
    If no getitem nor match are provided, return the first object of the first nonempty retrieved data.

    """
    relevant_data: Optional[Dict] = None
    for url in urls:
        resp = requests.get(url)
        resp_json = resp.json()
        json_data = [resp_json] if resp_json.get("data") is None else resp_json["data"]
        if not json_data:
            continue
        if not getmatch:
            relevant_data = json_data[0]
            break
        for data in json_data:
            if getmatch(data).lower() == match.lower():
                relevant_data = data
                break
        if relevant_data is not None:
            break
    else:
        return None
    return getcover(relevant_data), getalbumurl(relevant_data)


def fetch_cover_and_link_on_deezer(
        backup_cover: str,
        artist: str,
        album: Optional[str] = None,
        track: Optional[str] = None,
        deezertrack: Optional[int] = None) -> Tuple[str, str]:
    """Get cover and link from Deezer API.

    Search for a track with given artist , album or track.
    Return the cover of the album and the link to the album on Deezer.
    """

    data = None
    if deezertrack is not None:
        data = _get_data_from_deezer_url(
            f"https://api.deezer.com/track/{deezertrack}",
            getcover=lambda x: x["album"]["cover_big"],
            getalbumurl=lambda x: f"https://deezer.com/album/{x['album']['id']}")
    if data is None and album is not None:
        data = _get_data_from_deezer_url(
            f"https://api.deezer.com/search/album?q=artist:'{artist}' album:'{album}'",
            f"https://api.deezer.com/search/album?q={artist} {album}",
            getcover=lambda x: x["cover_big"],
            getalbumurl=lambda x: f"https://deezer.com/album/{x['id']}",
            getmatch=lambda x: x["title"],
            match=album)
    if data is None and track is not None:
        data = _get_data_from_deezer_url(
            f"https://api.deezer.com/search/track?q=artist:'{artist}' track:'{track}'",
            f'https://api.deezer.com/search/track?q={artist} {track}',
            getcover=lambda x: x["album"]["cover_big"],
            getalbumurl=lambda x: f"https://deezer.com/album/{x['album']['id']}")
    if data is None:
        data = _get_data_from_deezer_url(
            'https://api.deezer.com/search/artist?q={}'.format(artist),
            getcover=lambda x: x["picture_big"],
            getalbumurl=lambda x: f"https://deezer.com/artist/{x['id']}")

    return data or (backup_cover, "")


def fetch_apple_podcast_cover(podcast_link: str, fallback: str) -> str:
    """Scrap cover url from provided Apple Podcast link."""
    if not podcast_link:
        return fallback
    req = requests.get(podcast_link)
    bs = BeautifulSoup(req.content.decode(), "html.parser")
    sources = bs.find_all("source")
    cover_url: str = sources[0].attrs["srcset"].split(",")[1].replace("2x", "")
    return cover_url.strip()


@lru_cache(maxsize=4)
def url_to_base64(url) -> str:
    content = requests.get(url).content
    return base64.b64encode(content).decode()
