import os
import sys

from daemonize import Daemonize
from sunflower.radio import Radio

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


pid = "/tmp/sunflower-radio-watcher.pid"
daemon = Daemonize(app="sunflower-radio-watcher", pid=pid, action=Radio().watch)
daemon.start()
