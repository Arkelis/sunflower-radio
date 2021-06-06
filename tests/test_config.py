from datetime import datetime

from sunflower.core.channel import Channel
from sunflower.core.config import K
from sunflower.core.config import get_config
from sunflower.stations import FranceCulture
from sunflower.stations import FranceInterParis
from tests.common import FakeRepository


def test_config_parsing():
    config = get_config("tests/fixtures/conf.edn")
    assert config[K("radio-name")] == "Radio Test Pycolore"


def test_channel_instantiation_with_config():
    france_culture = FranceCulture()
    fip = FranceInterParis()

    channel = Channel.fromconfig(
        get_config("tests/fixtures/conf.edn")[K("channels")][0],
        {"France Culture": france_culture,
         "FIP": fip},
        {})

    assert channel.name == "Tournesol test"
    assert channel.__id__ == "tournesol-test"
    assert channel.timetable.stations == {france_culture, fip}
    assert channel.timetable.station_at(datetime(2021, 1, 1, 0, 0, 0)) == france_culture
    assert channel.timetable.station_after(datetime(2021, 1, 1, 0, 0, 0)) == fip
    assert channel.timetable.station_at(datetime(2021, 1, 1, 5, 0, 0)) == fip
    assert channel.timetable.station_after(datetime(2021, 1, 1, 5, 0, 0)) == france_culture
    assert channel.timetable.station_at(datetime(2021, 1, 1, 6, 0, 0)) == fip
    assert channel.timetable.station_after(datetime(2021, 1, 1, 6, 0, 0)) == france_culture
