
import logging
import logging.handlers
import os
import sys
import traceback

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from daemonize import Daemonize
from sunflower.core.scheduler import Scheduler
from sunflower.channels import tournesol, music
from sunflower.core.functions import check_obj_integrity


def launch_scheduler():
    # instantiate logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # format msg
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s :: %(message)s")
    
    # rotate
    file_handler = logging.handlers.RotatingFileHandler("/tmp/scheduler.log", "a", 1000000, 1)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Checking objects integrity.")

    scheduled_channels = [music, tournesol]
    check_errors = {}
    for channel in scheduled_channels:
        if errors := check_obj_integrity(channel):
            check_errors[str(channel)] = errors
        for station in channel.stations:
            if errors := check_obj_integrity(station):
                check_errors[str(station)] = errors

    if check_errors:
        for obj, errors in check_errors.items():
            logger.error(f"Errors for object {obj}:" + "\n" + "\n".join(f"- {err}" for err in errors))
        logger.info("Programme stopped.")
        raise RuntimeError("Integrity errors found.")

    logger.info("Starting scheduler.")
    try:
        scheduler = Scheduler(scheduled_channels, logger)
    except Exception as err:
        std_handler = logging.StreamHandler(sys.stdout)
        std_handler.setLevel(logging.ERROR)
        std_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(std_handler)
        logger.error(traceback.format_exc())
    logger.info("Scheduler instantiated.")
    
    scheduler.run()


if __name__ == "__main__":
    pid = "/tmp/sunflower-radio-scheduler.pid"
    daemon = Daemonize(app="sunflower-radio-scheduler", pid=pid, action=launch_scheduler)
    daemon.start()
