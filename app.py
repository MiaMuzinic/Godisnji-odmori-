from flask import Flask, render_template, request, jsonify, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, json, datetime

app = Flask(__name__)

# ------------------ GENERIRANJE TJEDANA ------------------

def generate_weeks(year=2026):
    weeks = []
    date = datetime.date(year, 1, 1)

    while date.weekday() != 0:  # ponedjeljak
        date += datetime.timedelta(days=1)

    while date.year == year:
        start = date
        end = date + datetime.timedelta(days=6)
        weeks.append(f"{start.strftime('%d.%m.')}-{end.strftime('%d.%m.')}")
        date += datetime.timedelta(days=7)

    return weeks

weeks = generate_weeks()


# ------------------ LIMTI ------------------

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


# ------------------ GOOGLE SETUP ------------------

def google_client():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]

    creds = json.loads(os.environ["GOOGLE_CREDS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds, scope)
    return gspread.authorize(creds)


def get_sheet(restoran):
    client = google_client()
    doc = client.open_by_key("16X-Fbzm9iP74RzGNPOWS19AwnBL4D7Is3gfu9rDRVz4")

    try:
        return doc.worksheet(restoran)
    except gspread.WorksheetNotFound:
        sheet = doc.add_worksheet(title=restoran, rows="1000", cols=str(4 + len(weeks)))
        sheet.append_row(["Ime", "Prezime", "Restoran", "Pozicija"] + weeks)
        return sheet


def get_global_sheet():
    client = google_client()
    doc = client.open_by_key("16X-Fbzm9iP74RzGNPOWS19AwnBL4D7Is3gfu9rDRVz4")

    try:
        return doc.worksheet("GO2026")
    except gspread.WorksheetNotFound:
        sheet = doc.add_worksheet(title="GO2026", rows="2000", cols=str(4 + len(weeks)))
        sheet.append_row(["Ime", "Prezime", "Restoran", "Pozicija"] + weeks)
        return sheet


# ------------------ API ZA STATUS POPUNJENOSTI ------------------

@app.route("/status")
def status():
    restoran = request.args.get("restoran")
    pozicija = request.args.get("pozicija")

    if not restoran or not pozicija:
        return jsonify({})

    limit = LIMITS[restoran][pozicija]

    sheet = get_sheet(restoran)
    data = sheet.get_all_records()

    counts = {w: 0 for w in weeks}

    for row in data:
        if row["Pozicija"] == pozicija:
            for w in weeks:
                if str(row.get(w, "")).strip() == "1":
                    counts[w] += 1

    full_weeks = [w for w in weeks if counts[w] >= limit]

    return jsonify({"full": full_weeks})


# ------------------ SUBMIT ------------------

@app.route("/submit", methods=["POST"])
def submit():
    ime = request.form.get("ime")
    prezime = request.form.get("prezime")
    restoran = request.form.get("restoran")
    pozicija = request.form.get("pozicija")
    odabrani_tjedni = request.form.getlist("weeks")

    sheet = get_sheet(restoran)
    global_sheet = get_global_sheet()

    row = [ime, prezime, restoran, pozicija] + [
        1 if w in odabrani_tjedni else "" for w in weeks
    ]

    sheet.append_row(row)
    global_sheet.append_row(row)

    return redirect(url_for("index"))


# ------------------ RENDER INDEX ------------------

@app.route("/")
def index():
    return render_template("index.html", weeks=weeks)


if __name__ == "__main__":
    app.run(debug=True)
