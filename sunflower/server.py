from flask import Flask, jsonify, render_template, url_for

import sunflower.radio as radio

app = Flask(__name__)

@app.route("/")
def index():
    current_station = radio.get_current_station()
    metadata = radio.fetch(current_station)
    if metadata["station"] == "RTL 2":
        if metadata["type"] == "Musique":
            title = metadata["artist"] + " &bull; " + metadata["title"]
        else:
            title = metadata["type"]
    elif "France " in metadata["station"]:
        title = metadata["diffusion_title"]
        metadata["thumbnail_src"] = "https://upload.wikimedia.org/wikipedia/fr/thumb/8/8d/France_inter_2005_logo.svg/1024px-France_inter_2005_logo.svg.png"
    flux_url = radio.FLUX_URL.get(current_station)
    return render_template("radio.html", card_title=title, metadata=metadata, flux_url=flux_url)

@app.route("/on-air")
def current_show_data():
    metadata = radio.fetch(radio.get_current_station())
    return jsonify(metadata)
