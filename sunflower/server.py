from flask import Flask, jsonify, render_template, url_for
from flask_cors import CORS, cross_origin
import time

import sunflower.radio as radio

app = Flask(__name__)
cors = CORS(app)

def _prepare_broadcast_info():
    current_station = radio.get_current_station()
    metadata = radio.fetch(current_station)
    if metadata["station"] == "RTL 2":
        if metadata["type"] == "Musique":
            title = metadata["artist"] + " • " + metadata["title"]
        else:
            title = metadata["type"]
    elif "France " in metadata["station"]:
        title = metadata.get("diffusion_title", metadata["show_title"])
    flux_url = "http://pycolorefr:8000/tournesol"
    return title, metadata, flux_url, 5000

@app.route("/")
def index():
    title, metadata, flux_url, refresh_timeout = _prepare_broadcast_info()
    return render_template("radio.html", card_title=title, metadata=metadata, flux_url=flux_url, refresh_timeout=refresh_timeout)

@app.route("/update")
def update_broadcast_info():
    title, metadata, flux_url, refresh_timeout = _prepare_broadcast_info()
    return render_template("card_body.html", card_title=title, metadata=metadata, flux_url=flux_url, refresh_timeout=refresh_timeout)

@app.route("/on-air")
def current_show_data():
    metadata = radio.fetch(radio.get_current_station())
    return jsonify(metadata)
