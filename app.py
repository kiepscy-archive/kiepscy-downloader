from flask import Flask, request, redirect, jsonify, render_template, render_template_string
from chomyk import Chomyk, BASE_URL
import requests
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
    try:
        odc = request.args.get("odcinek")
        if not odc:
            return jsonify({"error": "Brak parametru 'odcinek'"}), 400

        files = get_files(odc)
        if not files:
            return jsonify({"error": "Nie znaleziono takiego sezonu/odcinka"}), 404

        ch = Chomyk("KiepscyArchive", "KiepscyArchive_0078224371", maxThreads=5, directory="/tmp")
        for f in files:
            ch.dl(BASE_URL + f)

        import time
        for _ in range(10):
            if ch.download_links:
                break
            time.sleep(0.5)

        if not ch.download_links:
            return jsonify({"error": "Brak linków (możliwe problemy z autoryzacją lub transferem)"}), 500

        return jsonify(ch.download_links)

    except Exception as e:
        import traceback
        print("❌ Błąd aplikacji:", e)
        traceback.print_exc()
        return jsonify({"error": f"Błąd serwera: {str(e)}"}), 500

@app.route("/download", methods=["GET"])
def download():
    odc = request.args.get("odcinek")
    if not odc:
        return "Brak parametru 'odcinek'", 400

    try:
        # lokalne zapytanie do get_links
        resp = requests.get("http://localhost:10000/get_links", params={"odcinek": odc})
        if resp.status_code != 200:
            return f"Błąd: {resp.json().get('error', 'Nieznany problem')}", 500

        links = resp.json()
        if not links:
            return "Brak dostępnych linków", 404

        first_url = links[0]['url']
        return redirect(first_url)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Błąd serwera: {str(e)}", 500

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/instrukcja")
def instrukcja():
    return render_template("instrukcja.html")

@app.route("/vlc")
def open_in_vlc():
    odc = request.args.get("odcinek")
    if not odc:
        return "Brak parametru 'odcinek'", 400

    try:
        resp = requests.get("http://localhost:10000/get_links", params={"odcinek": odc})
        if resp.status_code != 200:
            return f"Błąd: {resp.json().get('error', 'Nieznany problem')}", 500

        links = resp.json()
        if not links:
            return "Brak dostępnych linków", 404

        first_url = links[0]['url']
        return redirect(f"vlc://{first_url}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Błąd serwera: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
