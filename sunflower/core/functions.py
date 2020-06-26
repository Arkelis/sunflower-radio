# This file is part of sunflower package. radio
# This module contains core functions.

from sunflower.core.bases import URLStation
from sunflower.core.descriptors import PersistentAttribute


def write_liquidsoap_config(*channels, filename):
    """Write complete liquidsoap config file."""
    with open("{}.liq".format(filename), "w") as f:
        # config de base (pas de log, activation server telnet, source par défaut)
        f.write("#! /usr/bin/env liquidsoap\n\n")
        f.write("# log file\n")
        f.write('set("log.file", false)\n\n')
        f.write("# activate telnet server\n")
        f.write('set("server.telnet", true)\n\n')
        f.write("# default source\n")
        f.write('default = drop_metadata(single("~/radio/franceinfo-long.ogg"))\n\n')
        f.write("# streams\n")

        # configuration des chaînes
        # initialisation
        used_stations = set()

        # on récupère les infos de chaque chaîne
        timetables = []
        outputs = []
        for channel in channels:
            timetable, output = channel.get_liquidsoap_config()
            timetables.append(timetable)
            outputs.append(output)
            used_stations.update(channel.stations)

        # on commence par énumérer toutes les stations utilisées
        for station in used_stations:
            f.write(station.get_liquidsoap_config())
            if URLStation in station.mro():
                outputs.append("output.dummy({})".format(station.formatted_station_name))

        # puis on écrit les timetables
        timetables_string = "\n".join(timetables)
        f.write("\n" + timetables_string)

        # et les output
        outputs_string = "\n".join(outputs)
        f.write("\n" + outputs_string)


def check_obj_integrity(obj):
    """Perfom several checks in order to prevent some runtime errors."""
    
    errors = []

    # 1. If obj has PersistentAttribute attributes, check if this object
    #    has the 'data_type' and 'endpoint' attributes.

    for attr in vars(type(obj)).values():
        if not isinstance(attr, PersistentAttribute):
            continue
        if not hasattr(obj, "endpoint"):
            errors.append(f"Missing 'endpoint' attribute in {obj} which contains PersistentAttribute descriptor.")
        if not hasattr(obj, "data_type"):
            errors.append(f"Missing 'data_type' attribute in {obj} which contains PersistentAttribute descriptor.")

    return errors
