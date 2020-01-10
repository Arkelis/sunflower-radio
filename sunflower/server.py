from flask import abort, Flask, jsonify, render_template, url_for, request, stream_with_context, Response
from flask_cors import CORS, cross_origin
import time
import threading
import json

import redis

from sunflower.radio import Channel
from sunflower.utils import get_channel_or_404
from sunflower import settings

app = Flask(__name__)
# cors = CORS(app)


# En attendant de prendre en charge le multi chaines 
tournesol = Channel("tournesol")



@app.route("/")
def index():
    context = {
        "card_info": tournesol.current_broadcast_info,
        "flux_url": settings.ICECAST_SERVER_URL + tournesol.endpoint,
        "update_url": request.url_root + "update/tournesol",
    }
    return render_template("radio.html", **context)

@app.route("/channel/<string:channel>/infos")
@get_channel_or_404
def get_channel_info(channel):
    return jsonify({
        "flux_url": settings.ICECAST_SERVER_URL + channel.endpoint,
        "update_url": request.url_root + "update/" + channel.endpoint,
    })

@app.route("/update/<string:channel>")
@get_channel_or_404
def update_broadcast_info(channel):
    return jsonify(channel.current_broadcast_info)

@app.route("/update-events/<string:channel>")
@get_channel_or_404
def update_broadcast_info_stream(channel):
    def updates_generator():
        pubsub = redis.Redis().pubsub()
        pubsub.subscribe("sunflower:" + channel.endpoint)
        for message in pubsub.listen():
            data = message.get("data")
            if not isinstance(data, type(b"")):
                continue
            yield "data: {}\n\n".format(data.decode())
        return
    return Response(stream_with_context(updates_generator()), mimetype="text/event-stream")

@app.route("/on-air")
def current_show_data():
    return jsonify(tournesol.current_broadcast_metadata)
