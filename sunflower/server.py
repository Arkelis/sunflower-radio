from flask import Flask, jsonify, render_template, url_for

import sunflower.radio as radio

app = Flask(__name__)

@app.route("/")
def index():
    metadata = radio.fetch(radio.get_current_station())
    if metadata["station"] == "RTL 2":
        if metadata["type"] == "Musique":
            title = metadata["artist"] + " &bull; " + metadata["title"]
        else:
            title = metadata["type"]
    elif "France " in metadata["station"]:
        title = metadata["diffusion_title"]
        metadata["thumbnail_src"] = url_for("static", filename="inter.png")
    return render_template("radio.html", card_title=title, metadata=metadata)

@app.route("/on-air")
def current_show_data():
    metadata = radio.fetch(radio.get_current_station())
    return jsonify(metadata)
