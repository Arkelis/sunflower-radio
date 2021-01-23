import logging
from collections import Counter
from datetime import datetime

from sunflower.core.bases import Channel
from sunflower.stations import FranceCulture
from sunflower.stations import FranceInfo
from sunflower.stations import FranceInter
from sunflower.stations import FranceInterParis
from sunflower.stations import FranceMusique

test_channel = Channel(
    endpoint="tournesol",
    timetable={
        (0, 1, 2, 3, 4): [
            ("00:00", "05:00", FranceCulture),
            ("06:00", "10:00", FranceInter),
            ("10:00", "12:00", FranceCulture),
            ("12:00", "12:30", FranceInfo),
            ("12:30", "13:30", FranceInter),
            ("13:30", "18:00", FranceCulture),
            ("18:00", "20:00", FranceInter),
            ("20:00", "00:00", FranceInfo),
        ],
        (5,): [
            ("00:00", "06:00", FranceCulture),
            ("06:00", "09:00", FranceInter),
            ("09:00", "11:00", FranceInfo),
            ("11:00", "12:00", FranceCulture),
            ("12:00", "14:00", FranceInter),
            ("14:00", "17:00", FranceCulture),
            ("17:00", "18:00", FranceInter),
            ("18:00", "19:00", FranceCulture),
            ("19:00", "21:00", FranceInfo),
            ("21:00", "00:00", FranceCulture),
        ],
        (6,): [
            ("00:00", "07:00", FranceCulture),
            ("07:00", "09:00", FranceMusique),
            ("09:00", "10:00", FranceInter),
            ("10:00", "11:00", FranceInfo),
            ("11:00", "14:00", FranceInter),
            ("14:00", "18:00", FranceMusique),
            ("18:00", "19:00", FranceInfo),
            ("19:00", "22:00", FranceInter),
            ("22:00", "00:00", FranceInterParis),
        ],
    },
)


def test_tournesol_station_parsing():
    # Counter([...]) == Counter([...]) permet de comparer les éléments et leurs occurrences
    # de deux itérables sans se soucier de l'ordre
    assert Counter(test_channel.stations) == Counter(
        (FranceInterParis, FranceCulture, FranceInfo, FranceInter, FranceMusique)
    )


def _test_schedule():
    logger = logging.Logger("test")
    for step in test_channel.get_schedule(logger):
        print(
            datetime.fromtimestamp(step.start),
            datetime.fromtimestamp(step.end),
            step.broadcast.title,
        )


if __name__ == "__main__":
    _test_schedule()
