from daemonize import Daemonize
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from radio import Radio

pid = "/tmp/sunflower-radio-watcher.pid"
daemon = Daemonize(app="sunflower-radio-watcher", pid=pid, action=Radio().watch)
daemon.start()
