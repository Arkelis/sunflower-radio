from sunflower.core.bases import STATIONS_INSTANCES

from sunflower.stations import (
    RTL2,
    FranceCulture, FranceInter, FranceMusique, FranceInfo,
    PycolorePlaylistStation,
)


def test_instances_created():
    for station_cls in (RTL2, FranceInfo, FranceInter, FranceMusique, FranceCulture, PycolorePlaylistStation):
        assert isinstance(station_cls(), station_cls)


def test_instances_unique():
    for (cls, inst) in STATIONS_INSTANCES.items():
        for station_cls in (RTL2, FranceInfo, FranceInter, FranceMusique, FranceCulture, PycolorePlaylistStation):
            if cls == station_cls:
                assert inst is station_cls()
