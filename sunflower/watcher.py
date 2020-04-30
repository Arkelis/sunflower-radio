
import os
import sys
import logging
import logging.handlers

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from daemonize import Daemonize
from sunflower.core.watcher import Watcher
from sunflower import settings
from sunflower.channels import tournesol, music


def launch_watcher():
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
    logger.info("Starting watcher.")
    
    watcher = Watcher([music, tournesol], logger)
    
    logger.info("Watcher instanciated")
    
    watcher.run()
    
if __name__ == "__main__":
    pid = "/tmp/sunflower-radio-watcher.pid"
    daemon = Daemonize(app="sunflower-radio-watcher", pid=pid, action=launch_watcher)
    daemon.start()
