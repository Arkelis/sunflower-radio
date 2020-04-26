# This file is part of sunflower package. radio
# This module contains core functions.

from sunflower.core.bases import URLStation

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
        f.write('default = single("~/radio/franceinfo-long.ogg")\n\n')
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
                outputs.append("output.dummy({})".format(station.station_name.lower().replace(" ", "")))

        # puis on écrit les timetables
        timetables_string = "\n".join(timetables)
        f.write("\n" + timetables_string)

        # et les output
        outputs_string = "\n".join(outputs)
        f.write("\n" + outputs_string)
