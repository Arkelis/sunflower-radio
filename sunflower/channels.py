# This file is part of sunflower package. Radio app.

from sunflower.channels_definitions import channels_definitions
from sunflower.core.channel import Channel
from sunflower.core.repository import RedisRepository
from sunflower.stations import FranceCulture
from sunflower.stations import FranceInfo
from sunflower.stations import FranceInter
from sunflower.stations import FranceInterParis
from sunflower.stations import FranceMusique
from sunflower.stations import PycolorePlaylistStation
from sunflower.stations import RTL2

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
stations["Radio Pycolore"] = PycolorePlaylistStation(redis_repository)


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
