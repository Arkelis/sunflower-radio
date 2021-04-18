from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import TYPE_CHECKING
from typing import Tuple

from sunflower.core.stations import Station

if TYPE_CHECKING:
    pass


class TimetableSlot(NamedTuple):
    start: time
    end: time
    station: Station


class ResolvedTimetableSlot(NamedTuple):
    start: datetime
    end: datetime
    station: Station

    @classmethod
    def fromslot(cls, timetableslot: TimetableSlot, day: date):
        return cls(
            start=datetime.combine(day, timetableslot.start),
            end=(
                datetime.combine(day, timetableslot.end)
                if timetableslot.start < timetableslot.end
                else datetime.combine(day, timetableslot.end) + timedelta(days=1)),
            station=timetableslot.station)


class Timetable:
    def __init__(
            self,
            dict_representation: Dict[Tuple[int, ...], Tuple[str, str, Station]]):
        stations, timetables = self._extract_from_dict(dict_representation)
        self._stations = stations
        self._timetables = timetables

    @classmethod
    def fromconfig(cls, config, stations_map):
        new_config = {}
        for days, slots in config.items():
            new_config[days] = []
            for start, end, station_name in slots:
                new_config[days].append((start, end, stations_map[station_name]))
        return cls(new_config)

    @staticmethod
    def _extract_from_dict(
            dict_representation: Dict[Tuple[int, ...], List[Tuple[str, str, Station]]]):
        weekday_timetables: List[Optional[Tuple[TimetableSlot]]] = [None] * 7
        stations = set()
        for weekday_tuple, slots_list in dict_representation.items():
            day_timetable = []
            for slot_tuple in slots_list:
                start = time.fromisoformat(slot_tuple[0])
                end = time.fromisoformat(slot_tuple[1])
                station = slot_tuple[2]
                stations.add(station)
                day_timetable.append(TimetableSlot(start, end, station))
            for weekday in weekday_tuple:
                weekday_timetables[weekday] = tuple(day_timetable)
        if None in weekday_timetables:
            raise ValueError("The provided timetable misses a week day.")
        return stations, weekday_timetables

    @property
    def stations(self):
        return self._stations

    def resolved_timetable_of(self, dt: datetime) -> List[ResolvedTimetableSlot]:
        """Return a list of ResolvedTimetableSlot objects for the provided dt"""
        return [
            ResolvedTimetableSlot.fromslot(slot, dt.date())
            for slot in self._timetables[dt.weekday()]]

    def _slot_at(self, dt: datetime) -> ResolvedTimetableSlot:
        weekday = dt.weekday()
        for slot in self._timetables[weekday]:
            resolved_slot = ResolvedTimetableSlot.fromslot(slot, dt.date())
            if resolved_slot.start <= dt < resolved_slot.end:
                return resolved_slot
        else:
            raise RuntimeError(f"No slot found at {dt}.")

    def station_at(self, dt: datetime) -> Station:
        return self._slot_at(dt).station

    def end_of_slot_at(self, dt: datetime) -> datetime:
        return self._slot_at(dt).end

    def station_after(self, dt: datetime) -> Station:
        return self._slot_at(self.end_of_slot_at(dt)).station
