import json
import threading
import time

import redis
from flask import (Flask, Response, abort, jsonify, redirect, render_template,
                   request, stream_with_context, url_for)
from flask_cors import CORS, cross_origin

from sunflower import settings
from sunflower.channels import Channel
from sunflower.core.types import MetadataEncoder
from sunflower.utils.functions import get_channel_or_404

app = Flask(__name__, static_url_path="/static", static_folder="static/dist")
app.json_encoder = MetadataEncoder
# cors = CORS(app)

# Views

@app.route("/")
def index():
    last_visited_channel = request.cookies.get("lastVisitedChannel")
    return redirect(last_visited_channel or url_for("channel", channel="tournesol"))

@app.route("/<string:channel>/")
@get_channel_or_404
def channel(channel):
    context = {
        "card_info": channel.current_broadcast_info,
        "flux_url": settings.ICECAST_SERVER_URL + channel.endpoint,
        "update_url": url_for("update_broadcast_info", channel=channel.endpoint),
        "listen_url": url_for("update_broadcast_info_stream", channel=channel.endpoint),
        "infos_url": url_for("get_channel_info", channel=channel.endpoint),
    }
    return render_template("radio.html", **context)

# API views

@app.route("/api/")
def api_root():
    return jsonify({
        "channels": {endpoint: url_for("get_channel_links", channel=endpoint, _external=True) 
                     for endpoint in settings.CHANNELS},
        "stations": {endpoint: url_for("get_station_links", station=endpoint, _external=True)
                     for endpoint in settings.STATIONS},
    })

@app.route("/api/channels/<string:channel>/")
@get_channel_or_404
def get_channel_links(channel):
    return jsonify({
        "audio_stream": settings.ICECAST_SERVER_URL + channel.endpoint,
        "card_formated_metadata": url_for("update_broadcast_info", channel=channel.endpoint, _external=True),
        "metadata_update_events": url_for("update_broadcast_info_stream", channel=channel.endpoint, _external=True),
        "raw_metadata": url_for("get_channel_info", channel=channel.endpoint, _external=True),
    })

@app.route("/api/stations/<string:station>/")
def get_station_links(station):
    print(station)
    if station != "pycolore":
        abort(status=404)
    return jsonify({
        "playlist": "Rien pour l'instant"
    })

@app.route("/api/<string:channel>/metadata/")
@get_channel_or_404
def get_channel_info(channel):
    return jsonify(channel.current_broadcast_metadata)

@app.route("/api/<string:channel>/update/")
@get_channel_or_404
def update_broadcast_info(channel):
    return jsonify(channel.current_broadcast_info._asdict())

@app.route("/api/<string:channel>/events/")
@get_channel_or_404
def update_broadcast_info_stream(channel):
    def updates_generator():
        pubsub = redis.Redis().pubsub()
        pubsub.subscribe("sunflower:" + channel.endpoint)
        for message in pubsub.listen():
            data = message.get("data")
            if not isinstance(data, type(b"")):
                continue
            if data == "unchanged":
                yield ":"
            yield "data: {}\n\n".format(data.decode())
        return
    return Response(stream_with_context(updates_generator()), mimetype="text/event-stream")
