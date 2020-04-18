import sys
import os


# add current directory in python path
sys.path.insert(0, os.path.dirname(__file__))

# load dotenv
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "sunflower/.env"))

# import flask app
from sunflower.server import app as application
