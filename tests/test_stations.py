from sunflower.core.bases import STATIONS_INSTANCES

from sunflower.stations import (
    RTL2,
    FranceCulture, FranceInter, FranceMusique, FranceInfo,
    PycolorePlaylistStation,
)

def test_instances_created():
    for station_cls in (RTL2, FranceInfo, FranceInter, FranceMusique, FranceCulture, PycolorePlaylistStation):
        assert isinstance(station_cls(), station_cls), "Instances must be created automatically"

def test_instances_unique():
    for (name, inst) in STATIONS_INSTANCES.items():
        for station_cls in (RTL2, FranceInfo, FranceInter, FranceMusique, FranceCulture, PycolorePlaylistStation):
            if name == station_cls.__name__:
                assert inst is station_cls()
