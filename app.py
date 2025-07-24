from flask import Flask, request, jsonify
from chomyk import Chomyk, BASE_URL

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

def get_files_to_download(file_number):
    file_number = file_number.strip().upper()
    if file_number in COMMANDS:
        val = COMMANDS[file_number]
        if isinstance(val, tuple):
            return [f"{i:03}.mp4" for i in range(val[0], val[1] + 1)]
        else:
            return val
    elif file_number == "ALL":
        return [f"{i:03}.mp4" for i in range(0, 590)]
    elif file_number.isdigit() and 0 <= int(file_number) <= 589:
        return [f"{int(file_number):03}.mp4"]
    return []

@app.route("/get_links", methods=["GET"])
def get_links():
    odcinek = request.args.get("odcinek", "")
    if not odcinek:
        return jsonify({"error": "Brak parametru 'odcinek'"}), 400

    files = get_files_to_download(odcinek)
    if not files:
        return jsonify({"error": "Nie znaleziono takiego sezonu/odcinka"}), 404

    ch = Chomyk("KiepscyArchive", "KiepscyArchive_0078224371")
    for f in files:
        ch.dl(BASE_URL + f)

    return jsonify(ch.download_links)

@app.route("/")
def index():
    return """
    <h2>Chomikuj Link Generator</h2>
    <form action="/get_links" method="get">
        <label>Odcinek lub sezon (np. 123 albo S01):</label>
        <input name="odcinek" type="text" />
        <input type="submit" value="Pobierz linki" />
    </form>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
