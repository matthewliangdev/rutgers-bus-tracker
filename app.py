import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from routes import ROUTES

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

TRIPSHOT_BASE = "https://rutgers.tripshot.com/v2/p/shared/route"
CACHE_SECONDS = 8
NY_TZ = ZoneInfo("America/New_York")

_cache = {"data": None, "ts": 0.0}


def fetch_route_live(route_name: str, route_id: str):
    """Fetch one route's live vehicle positions and stop locations."""
    today = datetime.now(NY_TZ).strftime("%Y-%m-%d")
    resp = requests.get(
        f"{TRIPSHOT_BASE}/{route_id}/live",
        params={
            "day": today,
            "includePreviousDayRidesSpanningMidnight": "true",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()["InternalRouteLiveData"]

    buses = []
    for direction in data.get("inexactLiveData", []):
        for ride in direction.get("liveRides", []):
            vs = ride.get("vehicleStatus")
            loc = vs.get("location") if vs else None
            if not vs or not loc:
                continue
            buses.append({
                "id": vs.get("vehicleId"),
                "name": vs.get("name"),
                "route": route_name,
                "color": ride.get("color"),
                "lat": loc.get("lt"),
                "lon": loc.get("lg"),
                "bearing": vs.get("bearing"),
                "speed": vs.get("speed"),
                "updated": vs.get("when"),
            })
    return buses


def fetch_all_vehicles():
    now = time.time()
    if _cache["data"] is not None and now - _cache["ts"] < CACHE_SECONDS:
        return _cache["data"]

    all_buses = []
    for route_name, route_id in ROUTES.items():
        try:
            all_buses.extend(fetch_route_live(route_name, route_id))
        except requests.RequestException as exc:
            app.logger.warning("route %s fetch failed: %s", route_name, exc)
            # Skip this route this cycle rather than failing the whole response.
            continue

    _cache["data"] = all_buses
    _cache["ts"] = now
    return all_buses


@app.route("/api/vehicles")
def vehicles():
    try:
        return jsonify(fetch_all_vehicles())
    except Exception as exc:
        app.logger.warning("fetch failed entirely: %s", exc)
        if _cache["data"] is not None:
            return jsonify(_cache["data"])
        return jsonify({"error": "upstream unavailable"}), 503


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)