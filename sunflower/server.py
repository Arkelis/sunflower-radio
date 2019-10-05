from flask import Flask, jsonify

import sunflower.radio as radio

app = Flask(__name__)

@app.route("/")
def index():
    metadata = radio.fetch(radio.get_current_station())
    return jsonify(metadata)
