const REFRESH_MS = 8000;
const RUTGERS_CENTER = [40.5008, -74.4474];

const map = L.map('map').setView(RUTGERS_CENTER, 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// vehicle id -> Leaflet marker
const markers = new Map();
const statusEl = document.getElementById('status');

function busIcon(route, color) {
  const bg = color || '#cc0033';
  return L.divIcon({
    className: '',
    html: `<div class="bus-label" style="background:${bg}">${route ?? '?'}</div>`,
    iconSize: [null, null]
  });
}

async function refresh() {
  try {
    const res = await fetch('/api/vehicles');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const buses = await res.json();

    const seen = new Set();

    for (const bus of buses) {
      seen.add(bus.id);
      const pos = [bus.lat, bus.lon];

      if (markers.has(bus.id)) {
        // Move the existing marker instead of recreating it — this is what
        // keeps the map from flickering on every refresh.
        markers.get(bus.id).setLatLng(pos);
      } else {
        const marker = L.marker(pos, { icon: busIcon(bus.route, bus.color) })
          .addTo(map)
          .bindPopup(`<strong>${bus.route ?? '—'}</strong><br>Bus ${bus.name ?? bus.id}`);
        markers.set(bus.id, marker);
      }
    }

    // Remove buses that have gone out of service.
    for (const [id, marker] of markers) {
      if (!seen.has(id)) {
        map.removeLayer(marker);
        markers.delete(id);
      }
    }

    statusEl.textContent =
      `${buses.length} buses · updated ${new Date().toLocaleTimeString()}`;
  } catch (err) {
    console.error(err);
    statusEl.textContent = 'Connection issue — retrying…';
  }
}

refresh();
setInterval(refresh, REFRESH_MS);