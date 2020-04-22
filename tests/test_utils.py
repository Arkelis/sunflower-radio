from sunflower.utils.functions import parse_songs
import glob

def test_parse_songs():
    pattern = "/home/guillaume/backup-songs/*.opus"
    songs = parse_songs(pattern)
    songs_number = len(glob.glob(pattern))
    assert songs_number == len(songs), "La liste ne prend pas en compte toutes les chansons"
    for i in range(len(songs)-1):
        assert songs[i].artist != songs[i+1].artist, "Deux chansons consécutvies ont le même artiste."
