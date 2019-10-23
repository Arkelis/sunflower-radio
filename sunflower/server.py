from flask import Flask, jsonify, render_template, url_for, request
from flask_cors import CORS, cross_origin
import time

from sunflower.radio import Radio
from sunflower import settings

app = Flask(__name__)
cors = CORS(app)
radio = Radio()

def _prepare_broadcast_info():
    title, metadata = radio.get_current_broadcast_info()
    flux_url = settings.FLUX_URL
    return title, metadata, flux_url

@app.route("/")
def index():
    title, metadata, flux_url = _prepare_broadcast_info()
    update_url = request.url_root + "update"
    return render_template("radio.html", card_title=title, metadata=metadata, flux_url=flux_url, update_url=update_url)

@app.route("/update")
def update_broadcast_info():
    title, metadata, flux_url = _prepare_broadcast_info()
    return render_template("card_body.html", card_title=title, metadata=metadata, flux_url=flux_url)

@app.route("/on-air")
def current_show_data():
    metadata = radio.get_current_broadcast_metadata()
    return jsonify(metadata)
