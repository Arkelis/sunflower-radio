import glob

from sunflower.core.custom_types import Song
from sunflower.utils.music import fetch_cover_and_link_on_deezer
from sunflower.utils.music import parse_songs
from sunflower.utils.music import prevent_consecutive_artists


def test_parse_songs():
    pattern = "/home/guillaume/backup-songs/*.opus"
    songs = parse_songs(pattern)
    songs_number = len(glob.glob(pattern))
    assert songs_number == len(songs), "La liste ne prend pas en compte toutes les chansons"


def test_prevent_consecutive_artists():
    # Check that length is preserved
    pattern = "/home/guillaume/backup-songs/*.opus"
    songs = parse_songs(pattern)
    treated_songs = prevent_consecutive_artists(songs)
    for song in songs:
        assert song in treated_songs, "A song has been kicked!"

    # All same artists: return the same
    songs = [Song(path="", artist="A", album="", title="", length=0)] * 5
    treated_songs = prevent_consecutive_artists(songs)
    assert songs == treated_songs, "The two lists should be equal."

    # C A C B C
    songs = [Song(path="", artist="A", album="", title="", length=0),
             Song(path="", artist="B", album="", title="", length=0),
             Song(path="", artist="C", album="", title="", length=0),
             Song(path="", artist="C", album="", title="", length=0),
             Song(path="", artist="C", album="", title="", length=0)]
    treated_songs = prevent_consecutive_artists(songs)
    for i in range(len(treated_songs)-1):
        assert treated_songs[i].artist != treated_songs[i+1].artist, "Two songs in a row have the same artist."


def test_get_cover_from_deezer_with_deezertrack():
    cover, link = fetch_cover_and_link_on_deezer("backup", "LP", deezertrack=1245069102)

    assert link == "https://www.deezer.com/album/207861892"
    assert cover == "https://cdns-images.dzcdn.net/images/cover/b2284e22177a46ed3029dc91ea95d4e8/500x500-000000-80-0-0.jpg"


def test_get_cover_from_deezer_with_artist():
    cover, link = fetch_cover_and_link_on_deezer("backup", "LP")

    assert link == "https://www.deezer.com/artist/112259"
    assert cover == "https://cdns-images.dzcdn.net/images/artist/42a2ef16887e2cd54b07b848fdfd9619/500x500-000000-80-0-0.jpg"
