from flask import Flask, jsonify

import sunflower.radio as radio

app = Flask(__name__)

@app.route("/")
def index():
    metadata = radio.fetch("RTL 2")
    return jsonify(metadata)
