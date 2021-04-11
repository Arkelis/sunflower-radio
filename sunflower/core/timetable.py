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


class TimeTimetableSlot(NamedTuple):
    start: time
    end: time
    station: Station


class DatetimeTimetableSlot(NamedTuple):
    start: datetime
    end: datetime
    station: Station


class Timetable:
    def __init__(
            self,
            dict_representation: Dict[Tuple[int, ...], Tuple[str, str, Station]]):
        stations, timetables = self._extract_from_dict(dict_representation)
        self._stations = stations
        self._timetables = timetables

    @staticmethod
    def _extract_from_dict(
            dict_representation: Dict[Tuple[int, ...], Tuple[str, str, Station]]):
        weekday_timetables: List[Optional[Tuple[TimeTimetableSlot]]] = [None] * 7
        stations = set()
        for weekday_tuple, slots_list in dict_representation.items():
            day_timetable = []
            for slot_tuple in slots_list:
                start = time.fromisoformat(slot_tuple[0])
                end = time.fromisoformat(slot_tuple[1])
                station = slot_tuple[2]
                stations.add(station)
                day_timetable.append(TimeTimetableSlot(start, end, station))
            for weekday in weekday_tuple:
                weekday_timetables[weekday] = tuple(day_timetable)
        if None in weekday_timetables:
            raise ValueError("The provided timetable misses a week day.")
        return stations, weekday_timetables

    @property
    def stations(self):
        return self._stations

    @property
    def weekday_timetables(self):
        return self._timetables

    def _slot_at(self, dt: datetime) -> DatetimeTimetableSlot:
        weekday = dt.weekday()
        for slot in self._timetables[weekday]:
            start_dt = datetime.combine(dt.date(), slot.start)
            end_dt = datetime.combine(dt.date(), slot.end)
            if end_dt < start_dt:
                end_dt += timedelta(hours=24)
            if start_dt <= dt < end_dt:
                return DatetimeTimetableSlot(start_dt, end_dt, slot.station)
        else:
            raise RuntimeError(f"No slot found at {dt}.")

    def station_at(self, dt: datetime) -> Station:
        return self._slot_at(dt).station

    def end_of_slot_at(self, dt: datetime) -> datetime:
        return self._slot_at(dt).end

    def station_after(self, dt: datetime) -> Station:
        return self._slot_at(self.end_of_slot_at(dt)).station
