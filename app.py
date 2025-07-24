from flask import Flask, request, jsonify
from chomyk import Chomyk, BASE_URL
import time

app = Flask(__name__)

COMMANDS = {
    "S00": [ "000.mp4", "589.mp4" ],
    "S01": (0, 145),
    "S02": (146, 154),
    "S03": (155, 171),
    "S04": (172, 202),
    "S05": (203, 244),
    "S06": (245, 265),
    "S07": (266, 282),
    "S08": (283, 297),
    "S09": (298, 307),
    "S10": (308, 322),
    "S11": (323, 337),
    "S12": (338, 352),
    "S13": (353, 365),
    "S14": (366, 379),
    "S15": (380, 392),
    "S16": (393, 405),
    "S17": (406, 418),
    "S18": (419, 431),
    "S19": (432, 444),
    "S20": (445, 456),
    "S21": (457, 468),
    "S22": (469, 480),
    "S23": (481, 492),
    "S24": (493, 504),
    "S25": (505, 516),
    "S26": (517, 528),
    "S27": (529, 540),
    "S28": (541, 552),
    "S29": (553, 564),
    "S30": (565, 576),
    "S31": (577, 588),
}

def get_files(odcinek):
    odcinek = odcinek.strip().upper()
    if odcinek in COMMANDS:
        val = COMMANDS[odcinek]
        return [f"{i:03}.mp4" for i in range(val[0], val[1] + 1)] if isinstance(val, tuple) else val
    elif odcinek == "ALL":
        return [f"{i:03}.mp4" for i in range(0, 590)]
    elif odcinek.isdigit() and 0 <= int(odcinek) <= 589:
        return [f"{int(odcinek):03}.mp4"]
    return []

@app.route("/get_links", methods=["GET"])
def get_links():
    odc = request.args.get("odcinek")
    if not odc:
        return jsonify({"error": "Brak parametru 'odcinek'"}), 400

    files = get_files(odc)
    if not files:
        return jsonify({"error": "Nie znaleziono takiego sezonu/odcinka"}), 404

    ch = Chomyk("KiepscyArchive", "KiepscyArchive_0078224371")
    for f in files:
        ch.dl(BASE_URL + f)

    for i in range(10):
        if ch.download_links:
            break
        time.sleep(0.5)

    if not ch.download_links:
        return jsonify({"error": "Brak linków (możliwe problemy z autoryzacją)"}), 500

    return jsonify(ch.download_links)

@app.route("/")
def index():
    return """
    <h2>Generator linków Chomikuj</h2>
    <form action="/get_links" method="get">
        <label>Podaj odcinek lub sezon (np. 123, S01, ALL):</label><br>
        <input type="text" name="odcinek" />
        <input type="submit" value="Generuj linki" />
    </form>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
