from sunflower.channels import tournesol, music
from sunflower.stations import FranceMusique, FranceInter, FranceInfo, FranceCulture, RTL, RTL2, PycolorePlaylistStation
from collections import Counter


def test_tournesol_station_parsing():
    # Counter([...]) == Counter([...]) permet de comparer les éléments et leurs occurrences
    # de deux itérables sans se soucier de l'ordre
    assert Counter(tournesol.stations) == Counter((FranceCulture, FranceInfo, FranceInter, FranceMusique))


def test_music_station_parsing():
    assert Counter(music.stations) == Counter((RTL2, RTL, PycolorePlaylistStation))
