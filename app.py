from flask import Flask, render_template, request, redirect, url_for, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import os
import json

cred_data = json.loads(os.environ["GOOGLE_CREDS"])

scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_data, scope)
client = gspread.authorize(creds)

app = Flask(__name__)

# ---- TJEDNI ZA 2026 ----
import datetime

def generate_weeks(year=2026):
    weeks = []
    date = datetime.date(year, 1, 1)

    while date.weekday() != 0:
        date += datetime.timedelta(days=1)

    while date.year == year:
        start = date
        end = date + datetime.timedelta(days=6)

        week_str = f"{start.strftime('%d.%m.')}-{end.strftime('%d.%m.')}"
        weeks.append(week_str)

        date += datetime.timedelta(days=7)

    return weeks

weeks = generate_weeks()

popunjenost = {}

LIMITS = {
    "Kampus": {"Poslovođa": 3, "Kuhar": 14, "Konobar": 13, "Pomoćni radnik": 12, "Slastičar": 3, "Blagajnik": 2, "Skladištar": 1},
    "Index": {"Voditelj": 1, "Poslovođa": 1, "Šef smjene": 1, "Blagajnik": 1, "Konobar": 1, "Kuhar": 2, "Pomoćni radnik": 3},
    "SOS": {"Voditelj": 1, "Konobar": 1, "Kuhar": 1, "Pomoćni radnik": 3},
    "MEFST": {"Poslovođa": 1, "Kuhar": 1, "Pomoćni kuhar": 1, "Konobar": 1, "Pomoćni radnik": 2},
    "STOP": {"Kuhar": 4, "Pomoćni kuhar": 1, "Pizza majstor": 1, "Pomoćni radnik": 4, "Blagajnik": 2, "Poslovođa": 1, "Voditelj objekta": 1},
    "FGAG": {"Pizza majstor": 1, "Konobar": 1, "Pomoćni radnik": 1},
    "Ekonomija": {"Poslovođa": 1, "Kuhar": 1, "Pomoćni kuhar": 1, "Konobar": 1, "Pomoćni radnik": 1},
    "BB": {"Poslovođa": 1, "Pizza majstor": 1, "Kuhar": 1, "Konobar": 1, "Blagajnik": 1, "Pomoćni radnik": 2},
    "Spinut": {"Voditelj": 1, "Poslovođa": 1, "Kuhar": 4, "Blagajnik": 1, "Konobar": 1, "Pomoćni radnik": 3}
}

# ----- GOOGLE SHEETS SETUP -----

def google_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    return gspread.authorize(creds)

def get_sheet(restoran):
    client = google_client()
    doc = client.open_by_key("16X-Fbzm9iP74RzGNPOWS19AwnBL4D7Is3gfu9rDRVz4")

    try:
        sheet = doc.worksheet(restoran)
    except gspread.WorksheetNotFound:
        sheet = doc.add_worksheet(title=restoran, rows="1000", cols=str(4 + len(weeks)))
        sheet.append_row(["Ime", "Prezime", "Restoran", "Pozicija"] + weeks)

    return sheet

def get_global_sheet():
    client = google_client()
    doc = client.open_by_key("16X-Fbzm9iP74RzGNPOWS19AwnBL4D7Is3gfu9rDRVz4")

    try:
        sheet = doc.worksheet("GO2026")
    except gspread.WorksheetNotFound:
        sheet = doc.add_worksheet(title="GO2026", rows="2000", cols=str(4 + len(weeks)))
        sheet.append_row(["Ime", "Prezime", "Restoran", "Pozicija"] + weeks)

    return sheet


@app.route("/")
def index():
    return render_template("index.html", weeks=weeks)


@app.route("/status")
def status():
    return jsonify(popunjenost)

@app.route("/reset")
def reset():
    global popunjenost
    popunjenost = {}
    return "Resetirano!", 200


@app.route("/submit", methods=["POST"])
def submit():
    ime = request.form.get("ime")
    prezime = request.form.get("prezime")
    restoran = request.form.get("restoran")
    pozicija = request.form.get("pozicija")
    odabrani_tjedni = request.form.getlist("weeks")

    if restoran not in popunjenost:
        popunjenost[restoran] = {}
    if pozicija not in popunjenost[restoran]:
        popunjenost[restoran][pozicija] = {}

    limit = LIMITS[restoran][pozicija]

    for week in odabrani_tjedni:
        current_count = popunjenost[restoran][pozicija].get(week, 0)
        if current_count >= limit:
            return f"Tjedan {week} je već popunjen!", 400

    for week in odabrani_tjedni:
        popunjenost[restoran][pozicija][week] = popunjenost[restoran][pozicija].get(week, 0) + 1

    # ---- Upis u GOOGLE SHEETS ----
    row = [ime, prezime, restoran, pozicija] + [
        1 if w in odabrani_tjedni else "" for w in weeks
    ]

    # 1) Sheet restorana
    sheet_rest = get_sheet(restoran)
    sheet_rest.append_row(row)

    # 2) Globalni sheet "SviUpisi"
    sheet_global = get_global_sheet()
    sheet_global.append_row(row)

    print("POPUNJENOST:", popunjenost)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
