from contextlib import contextmanager
from contextlib import suppress
from telnetlib import Telnet

from sunflower.settings import LIQUIDSOAP_TELNET_HOST
from sunflower.settings import LIQUIDSOAP_TELNET_PORT


def write_liquidsoap_config(channels, filename):
    """Write complete liquidsoap config file."""
    with open("{}.liq".format(filename), "w") as f:
        # config de base (log, activation server telnet, source par défaut)
        f.write("#! /usr/bin/env liquidsoap\n\n")

        f.write("# log file\n")
        f.write('settings.log.file.set(true)\n')
        f.write('settings.log.file.path.set("/tmp/sunflower.liquidsoap.log")\n')
        f.write('settings.log.file.append.set(true)\n')
        f.write('settings.log.stdout.set(false)\n\n')

        f.write("# activate telnet server\n")
        f.write('settings.server.telnet.set(true)\n\n')
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

        # puis on écrit les timetables
        timetables_string = "\n".join(timetables)
        f.write("\n" + timetables_string)

        # et les output
        outputs_string = "\n".join(outputs)
        f.write("\n" + outputs_string)


class FakeSession:
    def write(self, *ars, **kwargs):
        pass

    def read_until(self, *args, **kwargs):
        pass


@contextmanager
def liquidsoap_telnet_session():
    try:
        with Telnet(LIQUIDSOAP_TELNET_HOST, LIQUIDSOAP_TELNET_PORT) as session:
            yield session
    except ConnectionError:
        yield FakeSession()
