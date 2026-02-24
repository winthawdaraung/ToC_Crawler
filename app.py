"""
app.py  ─  Flask web application for the F1 Driver Crawler
Run locally:   python app.py
Production:    gunicorn app:app
"""

from flask import Flask, render_template, request, jsonify, abort
import json
import os
import re

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "drivers.json")

# ── RE used inside the web layer ─────────────────────────────────────────────
RE_SANITIZE  = re.compile(r'[^a-zA-Z0-9\s\-\']')   # clean user search input
RE_YEAR_ONLY = re.compile(r'(?:19|20)\d{2}')         # pull year from DOB string
RE_NAT_CLEAN = re.compile(r'\(.*?\)')                 # strip parentheses from nationality


def load_drivers():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def enrich(driver: dict) -> dict:
    """Add computed fields not in raw JSON."""
    dob = driver.get("dob", "")
    y = RE_YEAR_ONLY.search(dob)
    driver.setdefault("age", str(2025 - int(y.group())) if y else "N/A")
    nat = RE_NAT_CLEAN.sub("", driver.get("nationality", "N/A")).strip()
    driver["nationality"] = nat if nat else "N/A"
    return driver


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    drivers    = [enrich(d) for d in load_drivers()]
    nations    = sorted({d["nationality"] for d in drivers if d["nationality"] != "N/A"})
    teams      = sorted({d.get("team","N/A") for d in drivers if d.get("team","N/A") != "N/A"})
    return render_template("index.html",
                           drivers=drivers,
                           nations=nations,
                           teams=teams,
                           total=len(drivers))


@app.route("/driver/<path:name>")
def driver_detail(name):
    drivers = load_drivers()
    driver  = next((enrich(d) for d in drivers if d["name"] == name), None)
    if not driver:
        abort(404)
    return render_template("driver.html", driver=driver)


@app.route("/api/drivers")
def api_drivers():
    drivers = [enrich(d) for d in load_drivers()]

    raw_q = request.args.get("q", "")
    q     = RE_SANITIZE.sub("", raw_q).strip().lower()
    nat   = request.args.get("nationality", "").lower()
    team  = request.args.get("team", "").lower()

    if q:
        drivers = [d for d in drivers if q in d["name"].lower()]
    if nat:
        drivers = [d for d in drivers if nat in d["nationality"].lower()]
    if team:
        drivers = [d for d in drivers if team in d.get("team","").lower()]

    return jsonify({"count": len(drivers), "drivers": drivers})


@app.route("/api/stats")
def api_stats():
    drivers = load_drivers()
    by_nat, by_team, decades = {}, {}, {}
    for d in drivers:
        n = d.get("nationality","N/A")
        t = d.get("team","N/A")
        by_nat[n]  = by_nat.get(n, 0) + 1
        by_team[t] = by_team.get(t, 0) + 1
        y_m = RE_YEAR_ONLY.search(d.get("dob",""))
        if y_m:
            decade = (int(y_m.group()) // 10) * 10
            decades[str(decade)+"s"] = decades.get(str(decade)+"s", 0) + 1
    return jsonify({
        "total":       len(drivers),
        "by_nationality": dict(sorted(by_nat.items(), key=lambda x: -x[1])[:15]),
        "by_team":     dict(sorted(by_team.items(), key=lambda x: -x[1])[:15]),
        "by_decade":   decades,
    })


if __name__ == "__main__":
    if not os.path.exists(DATA_FILE):
        print("⚠  data/drivers.json not found — running scraper first…")
        from scraper import run_crawler
        run_crawler()
    app.run(debug=True, port=5000)
