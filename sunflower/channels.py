# This file is part of sunflower package. Radio app.

from sunflower.core.channel import Channel
from sunflower.core.config import get_config
from sunflower.core.config import K
from sunflower.core.repository import RedisRepository
from sunflower.stations import FranceCulture
from sunflower.stations import FranceInfo
from sunflower.stations import FranceInter
from sunflower.stations import FranceInterParis
from sunflower.stations import FranceMusique
from sunflower.stations import PycolorePlaylistStation
from sunflower.stations import RTL2

# read definitions
definitions = get_config()
channels_definitions = definitions[K("channels")]
stations_definitions = definitions[K("stations")]

# instantiate repository
redis_repository = RedisRepository()

# instantiate URL stations
stations = {
    station_cls.name: station_cls()
    for station_cls in [FranceCulture,
                        FranceInfo,
                        FranceInter,
                        FranceMusique,
                        FranceInterParis,
                        RTL2]}

# add dynamic stations
stations["Radio Pycolore"] = PycolorePlaylistStation(redis_repository)


# instantiate channels
channels = [
    Channel.fromconfig(
        redis_repository,
        channel_definition,
        stations,
        {})
    for channel_definition in channels_definitions]
