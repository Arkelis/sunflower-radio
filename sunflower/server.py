from flask import Flask, jsonify, render_template, url_for
from flask_cors import CORS, cross_origin
import time

from sunflower.radio import Radio

app = Flask(__name__)
cors = CORS(app)
radio = Radio()

def _prepare_broadcast_info():
    metadata = radio.fetch()
    if metadata["station"] == "RTL 2":
        if metadata["type"] == "Musique":
            title = metadata["artist"] + " • " + metadata["title"]
        else:
            title = metadata["type"]
    elif "France " in metadata["station"]:
        title = metadata.get("diffusion_title", metadata["show_title"])
    flux_url = "http://icecast.pycolore.fr:8000/tournesol"
    return title, metadata, flux_url

@app.route("/")
def index():
    title, metadata, flux_url = _prepare_broadcast_info()
    return render_template("radio.html", card_title=title, metadata=metadata, flux_url=flux_url)

@app.route("/update")
def update_broadcast_info():
    title, metadata, flux_url = _prepare_broadcast_info()
    return render_template("card_body.html", card_title=title, metadata=metadata, flux_url=flux_url)

@app.route("/on-air")
def current_show_data():
    metadata = radio.fetch()
    return jsonify(metadata)
