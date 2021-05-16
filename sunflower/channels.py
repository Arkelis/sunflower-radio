# This file is part of sunflower package. Radio app.

import edn_format
from edn_format import Keyword
from sunflower.core.channel import Channel
from sunflower.core.repository import RedisRepository
from sunflower.stations import FranceCulture
from sunflower.stations import FranceInfo
from sunflower.stations import FranceInter
from sunflower.stations import FranceInterParis
from sunflower.stations import FranceMusique
from sunflower.stations import PycolorePlaylistStation
from sunflower.stations import RTL2

# read definitions
with open("sunflower/conf.edn") as f:
    definitions = edn_format.loads(f.read())
channels_definitions = definitions[Keyword("channels")]
stations_definitions = definitions[Keyword("stations")]

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
