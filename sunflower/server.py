from flask import abort, Flask, jsonify, render_template, url_for, request, stream_with_context, Response
from flask_cors import CORS, cross_origin
import time
import threading
import json

import redis

from sunflower.channels import Channel
from sunflower.utils import get_channel_or_404
from sunflower import settings

app = Flask(__name__)
# cors = CORS(app)

@app.route("/<string:channel>/")
@get_channel_or_404
def index(channel):
    context = {
        "card_info": channel.current_broadcast_info,
        "flux_url": settings.ICECAST_SERVER_URL + channel.endpoint,
        "update_url": url_for("update_broadcast_info", channel=channel.endpoint),
        "listen_url": url_for("update_broadcast_info_stream", channel=channel.endpoint),
        "infos_url": url_for("get_channel_info", channel=channel.endpoint),
    }
    return render_template("radio.html", **context)

@app.route("/<string:channel>/infos/")
@get_channel_or_404
def get_channel_info(channel):
    return jsonify({
        "audio_stream_url": settings.ICECAST_SERVER_URL + channel.endpoint,
        "card_formated_metadata_url": url_for("update_broadcast_info", channel=channel.endpoint, _external=True),
        "metadata_update_events_url": url_for("update_broadcast_info_stream", channel=channel.endpoint, _external=True),
        "raw_metadata": channel.current_broadcast_metadata,
    })

@app.route("/<string:channel>/update/")
@get_channel_or_404
def update_broadcast_info(channel):
    return jsonify(channel.current_broadcast_info)

@app.route("/<string:channel>/update-events/")
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