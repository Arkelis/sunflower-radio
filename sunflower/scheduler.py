
import os
import sys
import logging
import logging.handlers

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from daemonize import Daemonize
from sunflower.core.scheduler import Scheduler
from sunflower import settings
from sunflower.channels import tournesol, music


def launch_scheduler():
    # instanciate logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # format msg
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s :: %(message)s")
    
    # rotate
    file_handler = logging.handlers.RotatingFileHandler("/tmp/scheduler.log", "a", 1000000, 1)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.info("Starting scheduler.")
    
    scheduler = Scheduler([music, tournesol], logger)
    
    logger.info("Scheduler instanciated")
    
    scheduler.run()
    
if __name__ == "__main__":
    pid = "/tmp/sunflower-radio-scheduler.pid"
    daemon = Daemonize(app="sunflower-radio-scheduler", pid=pid, action=launch_scheduler)
    daemon.start()
