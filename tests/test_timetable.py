from datetime import datetime

import pytest
from sunflower.core.channel import Channel
from sunflower.core.timetable import Timetable
from tests.common import FakeRepository
from tests.common import fip
from tests.common import radio_pycolore
from tests.common import rtl2


valid_dict = {
    (0, 1, 2, 3,): [
        ("00:00", "06:00", fip),
        ("06:00", "09:00", rtl2),
        ("09:00", "12:00", radio_pycolore),
        ("12:00", "13:30", rtl2),
        ("13:30", "18:00", fip),
        ("18:00", "22:00", rtl2),
        ("22:00", "00:00", radio_pycolore)],
    (4,): [
        ("00:00", "06:00", fip),
        ("06:00", "09:00", rtl2),
        ("09:00", "12:00", radio_pycolore),
        ("12:00", "13:30", rtl2),
        ("13:30", "18:00", fip),
        ("18:00", "22:00", rtl2),
        ("22:00", "01:00", radio_pycolore)],
    (5,): [
        ("00:00", "01:00", radio_pycolore),
        ("01:00", "06:00", fip),
        ("06:00", "09:00", rtl2),
        ("09:00", "12:00", radio_pycolore),
        ("12:00", "13:30", rtl2),
        ("13:30", "18:00", fip),
        ("18:00", "22:00", rtl2),
        ("22:00", "01:00", radio_pycolore)],
    (6,): [
        ("00:00", "01:00", radio_pycolore),
        ("01:00", "06:00", fip),
        ("06:00", "09:00", rtl2),
        ("09:00", "12:00", radio_pycolore),
        ("12:00", "13:30", rtl2),
        ("13:30", "22:00", fip),
        ("22:00", "00:00", radio_pycolore)]}

invalid_dict = {
    (0, 1, 2, 3,): [
        ("00:00", "06:00", fip),
        ("06:00", "09:00", rtl2),
        ("09:00", "12:00", radio_pycolore),
        ("12:00", "13:30", rtl2),
        ("13:30", "18:00", fip),
        ("18:00", "22:00", rtl2),
        ("22:00", "00:00", radio_pycolore)],
    (4,): [
        ("00:00", "06:00", fip),
        ("06:00", "09:00", rtl2),
        ("09:00", "12:00", radio_pycolore),
        ("12:00", "13:30", rtl2),
        ("13:30", "18:00", fip),
        ("18:00", "22:00", rtl2),
        ("22:00", "01:00", radio_pycolore)],
    (5,): [
        ("00:00", "01:00", radio_pycolore),
        ("01:00", "06:00", fip),
        ("06:00", "09:00", rtl2),
        ("09:00", "12:00", radio_pycolore),
        ("12:00", "13:30", rtl2),
        ("13:30", "18:00", fip),
        ("18:00", "22:00", rtl2),
        ("22:00", "01:00", radio_pycolore)]}


@pytest.fixture
def channel() -> Channel:
    return Channel("test", "Test", repository=FakeRepository(), timetable=Timetable(valid_dict))


def test_timetable_without_seven_weekdays():
    with pytest.raises(ValueError) as err:
        timetable = Timetable(invalid_dict)

    assert str(err.value) == "The provided timetable misses a week day."


def test_stations(channel):
    assert channel.stations == {fip, rtl2, radio_pycolore}


def test_station_at(channel):
    assert channel.station_at(datetime(2021, 4, 12, 0, 0, 0)) == fip


def test_station_after(channel):
    assert channel.station_after(datetime(2021, 4, 11, 23, 0, 0)) == fip
    assert channel.station_after(datetime(2021, 4, 12, 0, 0, 0)) == rtl2
