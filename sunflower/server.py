from flask import abort, Flask, jsonify, render_template, url_for, request, stream_with_context, Response
from flask_cors import CORS, cross_origin
import time
import threading
import json

import redis

from sunflower.radio import Channel
from sunflower import settings

app = Flask(__name__)
cors = CORS(app)
channels = {name: Channel(name) for name in settings.CHANNELS}

# En attendant de prendre en charge le multi chaines 
tournesol = channels["tournesol"]



@app.route("/")
def index():
    context = {
        "card_info": tournesol.current_broadcast_info,
        "flux_url": settings.ICECAST_SERVER_URL + tournesol.endpoint,
        "update_url": request.url_root + "update",
    }
    return render_template("radio.html", **context)

@app.route("/update")
def update_broadcast_info():
    return jsonify(tournesol.current_broadcast_info)

@app.route("/update/<string:channel>")
def update_broadcast_info_stream(channel):
    # if channel not in settings.CHANNELS:
    # En attendant de prendre en charge le multi chaines 
    if channel != "tournesol":
        abort(404) 
    def updates_generator():
        pubsub = redis.Redis().pubsub()
        pubsub.subscribe(channel)
        for message in pubsub.listen():
            if message.get("message") is None:
                continue
            yield message["message"]
    return Response(stream_with_context(updates_generator()), mimetype="text/event-steam")


@app.route("/on-air")
def current_show_data():
    return jsonify(tournesol.current_broadcast_metadata)
