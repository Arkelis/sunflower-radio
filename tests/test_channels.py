import json
import logging
from collections import Counter
from datetime import datetime
from typing import Any
from typing import Callable
from typing import Optional
from typing import Type

from sunflower.core.bases import Channel
from sunflower.core.persistence import Repository
from sunflower.stations import FranceCulture
from sunflower.stations import FranceInfo
from sunflower.stations import FranceInter
from sunflower.stations import FranceInterParis
from sunflower.stations import FranceMusique


class FakeRepository(Repository):
    def retrieve(self, key: str, object_hook: Optional[Callable] = None):
        pass

    def persist(self, key: str, value: Any, json_encoder_cls: Optional[Type[json.JSONEncoder]] = None):
        pass

    def publish(self, key: str, channel, data):
        pass


france_culture = FranceCulture()
france_inter = FranceInter()
fip = FranceInterParis()
france_info = FranceInfo()
france_musique = FranceMusique()

test_channel = Channel(
    id="tournesol",
    repository=FakeRepository(),
    timetable={
        (0, 1, 2, 3, 4): [
            # (start, end, station_name),
            ("00:00", "05:00", france_culture),
            ("06:00", "10:00", france_inter),
            ("10:00", "12:00", france_culture),
            ("12:00", "12:30", france_info),
            ("12:30", "13:30", france_inter),
            ("13:30", "18:00", france_culture),
            ("18:00", "20:00", france_inter),
            ("20:00", "00:00", france_info),
        ],
        (5,): [
            ("00:00", "06:00", france_culture),
            ("06:00", "09:00", france_inter),
            ("09:00", "11:00", france_info),
            ("11:00", "12:00", france_culture),
            ("12:00", "14:00", france_inter),
            ("14:00", "17:00", france_culture),
            ("17:00", "18:00", france_inter),
            ("18:00", "19:00", france_culture),
            ("19:00", "21:00", france_info),
            ("21:00", "00:00", france_culture),
        ],
        (6,): [
            ("00:00", "07:00", france_culture),
            ("07:00", "09:00", france_musique),
            ("09:00", "10:00", france_inter),
            ("10:00", "11:00", france_info),
            ("11:00", "14:00", france_inter),
            ("14:00", "18:00", france_musique),
            ("18:00", "19:00", france_info),
            ("19:00", "22:00", france_inter),
            ("22:00", "00:00", fip),
        ]
    },
)


def test_planning_parsing():
    # Counter([...]) == Counter([...]) permet de comparer les éléments et leurs occurrences
    # de deux itérables sans se soucier de l'ordre
    assert Counter(test_channel.stations) == Counter(
        (fip, france_culture, france_info, france_inter, france_musique)
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
