import logging
from datetime import datetime

from sunflower.channels import tournesol
from sunflower.core.bases import STATIONS_INSTANCES
from sunflower.stations import (FranceCulture, FranceInfo, FranceInter, FranceMusique, PycolorePlaylistStation, RTL2)


def test_instances_created():
    for station_cls in (RTL2, FranceInfo, FranceInter, FranceMusique, FranceCulture, PycolorePlaylistStation):
        assert isinstance(station_cls(), station_cls)


def test_instances_unique():
    for (cls, inst) in STATIONS_INSTANCES.items():
        for station_cls in (RTL2, FranceInfo, FranceInter, FranceMusique, FranceCulture, PycolorePlaylistStation):
            if cls == station_cls:
                assert inst is station_cls()


def test_radiofrance_step():
    now = datetime.now()
    logger = logging.Logger("test")
    assert FranceInter().get_step(logger, now, tournesol) is not None
    assert FranceCulture().get_step(logger, now, tournesol) is not None
    assert FranceInfo().get_step(logger, now, tournesol) is not None
    assert FranceMusique().get_step(logger, now, tournesol) is not None
    assert FranceInter().get_next_step(logger, now, tournesol) is not None
    assert FranceCulture().get_next_step(logger, now, tournesol) is not None
    assert FranceInfo().get_next_step(logger, now, tournesol) is not None
    assert FranceMusique().get_next_step(logger, now, tournesol) is not None
