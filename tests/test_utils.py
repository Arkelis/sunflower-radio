import glob

from sunflower.core.types import Song
from sunflower.utils.deezer import parse_songs, prevent_consecutive_artists


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
    songs = [Song("", "A", "", "", 0)] * 5
    treated_songs = prevent_consecutive_artists(songs)
    assert songs == treated_songs, "The two lists should be equal."

    # C A C B C
    songs = [Song("", "A", "", "", 0), Song("", "B", "", "", 0), Song("", "C", "", "", 0), Song("", "C", "", "", 0), Song("", "C", "", "", 0)]
    treated_songs = prevent_consecutive_artists(songs)
    for i in range(len(treated_songs)-1):
        assert treated_songs[i].artist != treated_songs[i+1].artist, "Two songs in a row have the same artist."
