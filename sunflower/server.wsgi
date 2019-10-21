import sys
import os

# in case of a virtualenv, which is located in same directory as server.wsgi.
# this virtualenv must be named env and created with virtualenv (not venv).
activate_this = os.path.dirname(__file__) + "/env/bin/activate_this.py"
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))
# add current directory in python path
sys.path.insert(0, os.path.dirname(__file__))

from sunflower.server import app as application
