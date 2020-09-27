import logging
from collections import Counter
from datetime import datetime

from sunflower.channels import music, tournesol
from sunflower.stations import FranceCulture, FranceInfo, FranceInter, FranceMusique, PycolorePlaylistStation, RTL2


def test_tournesol_station_parsing():
    # Counter([...]) == Counter([...]) permet de comparer les éléments et leurs occurrences
    # de deux itérables sans se soucier de l'ordre
    assert Counter(tournesol.stations) == Counter((FranceCulture, FranceInfo, FranceInter, FranceMusique))


def test_music_station_parsing():
    assert Counter(music.stations) == Counter((RTL2, PycolorePlaylistStation))


def _test_schedule():
    logger = logging.Logger("test")
    for step in music.get_schedule(logger):
        print(datetime.fromtimestamp(step.start), datetime.fromtimestamp(step.end), step.broadcast.title)


if __name__ == '__main__':
    _test_schedule()
