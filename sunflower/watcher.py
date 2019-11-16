import logging
import logging.handlers
import os
import sys
from datetime import datetime
from time import sleep

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from daemonize import Daemonize
from sunflower.radio import Radio

def watch():
    """Keep data for radio client up to date."""
    # instanciate radio
    radio = Radio()

    # instanciate logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # format msg
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s :: %(message)s")

    # rotate
    file_handler = logging.handlers.RotatingFileHandler("/tmp/watcher.log", "a", 1000000, 1)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.debug("Starting watcher.")

    if radio.current_broadcast_metadata is None:
        radio.current_broadcast_metadata = radio.get_current_broadcast_metadata()

    # loop
    while True:
        if datetime.now().timestamp() > radio.current_broadcast_metadata["end"]:
            logger.debug("Processing. Current timestamp is {}".format(datetime.now().timestamp()))
            logger.debug("Before processing, metadata is {}".format(radio.current_broadcast_metadata))
            try:
                radio.process_radio()
            except Exception as err:
                import traceback
                logger.error("Une erreur est survenue pendant la mise à jour des données.")
                logger.error(traceback.format_exc())
                metadata = {
                    "message": "An error occured when fetching data.",
                    "type": "Erreur",
                    "end": 0,
                }
                info = {
                    "current_thumbnail": radio.current_station.station_thumbnail,
                    "current_station": radio.current_station.station_name,
                    "current_broadcast_title": "Une erreur est survenue",
                    "current_show_title": "Erreur interne du serveur",
                    "current_broadcast_summary": "Une erreur est survenue pendant la récupération des métadonnées . Si cette erreur n'est pas bloquante, les données ont une chance de se mettre à jour automatiquement.",
                    "current_broadcast_end": 0,
                }
            logger.debug("After processing, metadata is {}".format(radio.current_broadcast_metadata))
        sleep(5)


if __name__ == "__main__":
    pid = "/tmp/sunflower-radio-watcher.pid"
    daemon = Daemonize(app="sunflower-radio-watcher", pid=pid, action=watch)
    daemon.start()
