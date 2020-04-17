# This is sunflower radio

import json
from collections import namedtuple
from enum import Enum

# Custom datamodel

Song = namedtuple("Song", ["path", "artist", "album", "title", "length"])
CardMetadata = namedtuple("CardMetadata", ["current_thumbnail",
                                           "current_station",
                                           "current_broadcast_title",
                                           "current_show_title",
                                           "current_broadcast_summary",])


# Available metadata types

class MetadataType(Enum):
    MUSIC = "Musique"
    PROGRAMME = "Emission"
    NONE = ""
    ADS = "Publicité"
    ERROR = "Erreur"
    WAITING_FOLLOWING = "Transition"

class MetadataEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, MetadataType):
            return obj.value
        return json.JSONEncoder.default(self, obj)

def as_metadata_type(mapping):
    type_ = mapping.get("type")
    if type_ is None:
        return mapping
    for member in MetadataType:
        if type_ == member.value:
            mapping["type"] = MetadataType(type_)
            break
    return mapping
