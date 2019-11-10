from flask import Flask, jsonify, render_template, url_for, request
from flask_cors import CORS, cross_origin
import time
import threading

from sunflower.radio import Radio
from sunflower import settings

app = Flask(__name__)
cors = CORS(app)
radio = Radio()

@app.route("/")
def index():
    context = {
        "card_info": radio.current_broadcast_info,
        "flux_url": settings.FLUX_URL,
        "update_url": request.url_root + "update",
    }
    return render_template("radio.html", **context)

@app.route("/update")
def update_broadcast_info():
    return jsonify(radio.current_broadcast_info)

@app.route("/on-air")
def current_show_data():
    return jsonify(radio.current_broadcast_metadata)
