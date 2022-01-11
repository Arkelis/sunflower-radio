
import asyncio
import logging
import logging.handlers
import os
import sys
import traceback

from sunflower.core.repository import RedisRepository

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sunflower.core.scheduler import Scheduler
from sunflower.channels import channels


def launch_scheduler():
    # instantiate logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # format msg
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s :: %(message)s")
    
    # rotate
    file_handler = logging.handlers.RotatingFileHandler("/tmp/sunflower.scheduler.log", "a", 1_000_000, 1)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # instantiate repository
    repository = RedisRepository()

    logger.info("Starting scheduler.")
    try:
        scheduler = Scheduler(channels, repository, logger)
        logger.info("Scheduler instantiated.")
        asyncio.run(scheduler.run())
    except Exception as err:
        std_handler = logging.StreamHandler(sys.stdout)
        std_handler.setLevel(logging.ERROR)
        std_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(std_handler)
        logger.error(traceback.format_exc())




if __name__ == "__main__":
    launch_scheduler()
    # pid = "/tmp/beta-sunflower-radio-scheduler.pid"
    # daemon = Daemonize(app="beta-sunflower-radio-scheduler", pid=pid, action=launch_scheduler)
    # daemon.start()
