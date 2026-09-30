"""
explore.py — quick script to test the inspect of live TripShot data for every
route in routes.py. Prints only the fields the app actually needs (vehicle
name, position, bearing, last-update time) instead of dumping raw JSON.

Usage:
    python explore.py            # check every route
    python explore.py [route]    # checks user input route
"""

import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from routes import ROUTES

TRIPSHOT_BASE = "https://rutgers.tripshot.com/v2/p/shared/route"
NY_TZ = ZoneInfo("America/New_York")


def fetch_live_vehicles(route_name: str, route_id: str):
    """Hit one route's /live endpoint and return a list of vehicle dicts."""
    today = datetime.now(NY_TZ).strftime("%Y-%m-%d")

    r = requests.get(
        f"{TRIPSHOT_BASE}/{route_id}/live",
        params={
            "day": today,
            "includePreviousDayRidesSpanningMidnight": "true",
        },
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()["InternalRouteLiveData"]

    vehicles = []
    for direction in data.get("inexactLiveData", []):
        for ride in direction.get("liveRides", []):
            vs = ride.get("vehicleStatus")
            loc = vs.get("location") if vs else None
            if not vs or not loc:
                continue
            vehicles.append({
                "route": route_name,
                "name": vs.get("name"),
                "lat": loc.get("lt"),
                "lon": loc.get("lg"),
                "bearing": vs.get("bearing"),
                "speed": vs.get("speed"),
                "updated": vs.get("when"),
            })
    return vehicles


def main():
    # Optional: pass a route name as a CLI arg to check just one route.
    if len(sys.argv) > 1:
        name = sys.argv[1]
        if name not in ROUTES:
            print(f"Unknown route '{name}'. Known routes: {', '.join(ROUTES)}")
            return
        targets = {name: ROUTES[name]}
    else:
        targets = ROUTES

    total_vehicles = 0

    for name, route_id in targets.items():
        try:
            vehicles = fetch_live_vehicles(name, route_id)
        except requests.RequestException as exc:
            print(f"{name:8s} ERROR: {exc}")
            continue

        if not vehicles:
            print(f"{name:8s} no active vehicles right now")
            continue

        for v in vehicles:
            print(
                f"{v['route']:8s} {v['name']:>6s}  "
                f"({v['lat']:.5f}, {v['lon']:.5f})  "
                f"bearing={v['bearing']}  speed={v['speed']}  "
                f"updated={v['updated']}"
            )
        total_vehicles += len(vehicles)

    print(f"\n{total_vehicles} vehicle(s) currently reporting across {len(targets)} route(s).")


if __name__ == "__main__":
    main()