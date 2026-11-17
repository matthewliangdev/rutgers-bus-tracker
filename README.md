# rutgers-bus-tracker
 
A little side project that shows live Rutgers bus positions on a map. Built mostly because I wanted to see if I could figure out how the official site gets its data, and because I was tired of guessing when the LX bus would actually show up.
 
Not polished, not meant to be a "real" product — just something I built for myself and to learn some stuff along the way.
 
## What it does
 
- Pulls live bus GPS positions from Rutgers' transit system (TripShot) and shows them on a Leaflet map
- Refreshes every few seconds
- Filters out buses that are parked/idle instead of actually running a route
## How it works
 
Rutgers doesn't publish a public API for this, so I had to find the endpoint myself by poking around in Chrome DevTools and watching what requests the official site makes. Turned out there's an undocumented endpoint like:
 
```
https://rutgers.tripshot.com/v2/p/shared/route/{routeId}/live
```
 
It's scoped to one route at a time (no "give me every bus" endpoint), so the backend here just loops through all the route IDs I collected and merges the results.
 
Stack:
- **Backend:** Python + Flask — fetches from TripShot, caches results briefly, serves a clean JSON endpoint
- **Frontend:** plain JS + Leaflet — polls the backend and draws markers on the map
- No database, no auth, nothing fancy. It's a map and a loop.
## Running it locally
 
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
 
Then go to `http://localhost:5000`.
 
## Known quirks / stuff I haven't fixed
 
- Only works during Rutgers bus service hours (roughly 7am–10pm weekdays). Outside that it'll just show an empty map, which is correct, not broken.
- Occasionally shows a bus sitting way off campus doing nothing — that's a vehicle whose GPS is still reporting even though it's not actually running a route (speed = 0, no heading). There's some basic filtering for this but it's not perfect.
- Route list is hardcoded in `routes.py` since I couldn't find an endpoint that lists all routes at once — I collected the IDs by hand from the browser.
- If Rutgers changes their transit provider again (they switched from Passio to TripShot in mid-2026), this will probably just stop working and I'll have to redo the whole reverse-engineering step.
## Why
 
Mostly curiosity, plus I wanted a project that touched real time data and an API I didn't control, since that's closer to what actual engineering work looks like.
 