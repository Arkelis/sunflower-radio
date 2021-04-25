# This file is part of sunflower package. Radio app.
import hy

from sunflower.core.channel import Channel
from sunflower.core.repository import RedisRepository
from sunflower.stations import FranceCulture
from sunflower.stations import FranceInfo
from sunflower.stations import FranceInter
from sunflower.stations import FranceInterParis
from sunflower.stations import FranceMusique
from sunflower.stations import PycolorePlaylistStation
from sunflower.stations import RTL2

from sunflower.utils.hy import read_definitions

# read definitions
definitions = read_definitions("sunflower/definitions.lisp")
channels_definitions = definitions["channels"]
stations_definitions = definitions["stations"]

# instantiate repository
redis_repository = RedisRepository()

# instantiate stations
stations = {station_cls.name: station_cls()
            for station_cls in [FranceCulture,
                                FranceInfo,
                                FranceInter,
                                FranceMusique,
                                FranceInterParis,
                                RTL2]}
stations["Radio Pycolore"] = PycolorePlaylistStation(
    redis_repository,
    stations_definitions["pycolore"]["id"],
    stations_definitions["pycolore"]["name"])


# define channels
tournesol = Channel.fromconfig(
    redis_repository,
    channels_definitions["tournesol"],
    stations,
    {})

music = Channel.fromconfig(
    redis_repository,
    channels_definitions["musique"],
    stations,
    {})
