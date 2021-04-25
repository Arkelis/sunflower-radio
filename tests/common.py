import json
from typing import Any
from typing import Callable
from typing import Optional
from typing import Optional
from typing import Type

from sunflower.core.repository import Repository
from sunflower.stations import FranceCulture
from sunflower.stations import FranceInfo
from sunflower.stations import FranceInter
from sunflower.stations import FranceInterParis
from sunflower.stations import FranceMusique
from sunflower.stations import PycolorePlaylistStation
from sunflower.stations import RTL2


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
rtl2 = RTL2()
radio_pycolore = PycolorePlaylistStation(FakeRepository(), "pycolore", "Radio Pycolore")
