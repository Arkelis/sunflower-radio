import logging
import logging.handlers
import os
import sys
from datetime import datetime
from time import sleep

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from daemonize import Daemonize
from sunflower import channels
from sunflower import settings

def watch():
    """Keep data for radio client up to date."""

    try:
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

        # add logger to channels and init
        for channel in channels.CHANNELS.values():
            channel.logger = logger
            channel.process_radio()

        # loop
        while True:
            sleep(4)
            for channel in channels.CHANNELS.values():
                if (
                    datetime.now().timestamp() < channel.current_broadcast_metadata["end"]
                    and channel.current_broadcast_metadata["station"] == channel.current_station.station_name
                ):
                    channel.publish_to_redis("unchanged")
                    continue
                logger.debug("New metadata for channel {}: {}.".format(channel.endpoint, channel.current_broadcast_info["current_broadcast_title"]))
                try:
                    channel.process_radio()
                except Exception as err:
                    import traceback
                    logger.error("Une erreur est survenue pendant la mise à jour des données: {}.".format(err))
                    logger.error(traceback.format_exc())
    except Exception as err:
        import traceback
        logger.error("Erreur fatale")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    pid = "/tmp/sunflower-radio-watcher.pid"
    daemon = Daemonize(app="sunflower-radio-watcher", pid=pid, action=watch)
    daemon.start()
