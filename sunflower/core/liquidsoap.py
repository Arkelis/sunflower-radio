import typing
from typing import Type
from contextlib import contextmanager
from contextlib import suppress
from telnetlib import Telnet

from sunflower.settings import LIQUIDSOAP_TELNET_HOST
from sunflower.settings import LIQUIDSOAP_TELNET_PORT


if typing.TYPE_CHECKING:
    from sunflower.core.channel import Channel
    from sunflower.core.stations import Station


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


def generate_liquidsoap_config_for_channel(channel: "Channel"):
    """Renvoie une chaîne de caractères à écrire dans le fichier de configuration liquidsoap."""

    # définition des horaires des radios
    if channel.stations:
        source_str = f"# {channel.id} channel\n"
        for station in channel.stations:
            station_name = station.formatted_station_name
            source_str += f'{station_name}_on_{channel.id} = interactive.bool("{station_name}_on_{channel.id}", false)\n'
        source_str += f"{channel.id}_radio = switch(track_sensitive=false, [\n"
        for station in channel.stations:
            station_name = station.formatted_station_name
            source_str += f"    ({station_name}_on_{channel.id}, {station_name}),\n"
        source_str += "])\n"
    else:
        source_str = ""

    # metadata
    source_str += (
        f"\n"
        f'{channel.id}_title = interactive.string("{channel.id}_title", "")\n'
        f'{channel.id}_artist = interactive.string("{channel.id}_artist", "")\n'
        f'{channel.id}_album = interactive.string("{channel.id}_album", "")\n\n'
        f"def apply_{channel.id}_metadata(m) = \n"
        f'  [("title", title()), ("album", album()), ("artist", artist())]\n'
        f"end\n\n")

    # output
    fallback = f"{channel.id}_radio" if source_str else channel.stations[0].formatted_station_name
    source_str += f"{channel.id}_radio = fallback(track_sensitive=false, [{fallback}, default])\n"
    source_str += (
        f'{channel.id}_radio = fallback(track_sensitive=false, [request.queue(id='
        f'"{channel.id}_custom_songs", {channel.id}_radio])\n')
    source_str += (
        f'{channel.id}_radio = map_metadata(id="{channel.id}", '
        f'apply_{channel.id}_metadata, drop_metadata({channel.id}_radio))\n\n')

    output_str = (
        f'output.icecast(%vorbis(quality=0.6),\n'
        f'    host="localhost", port=3333, password="Arkelis77",\n'
        f'    mount="{channel.id}", {channel.id}_radio)\n\n')

    return source_str, output_str


def generate_liquidsoap_config_for_station(station: Type["Station"]):
    return (f'{station.formatted_station_name} = '
            f'mksafe(input.http(id="{station.formatted_station_name}", start=false, "{station.station_url}"))\n')


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
