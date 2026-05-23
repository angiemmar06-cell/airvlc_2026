const VALENCIA_CENTER = [39.47, -0.376];
const DEFAULT_ZOOM = 13;

const map = L.map("map").setView(VALENCIA_CENTER, DEFAULT_ZOOM);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  maxZoom: 19,
}).addTo(map);

const stationCountEl = document.getElementById("station-count");

fetch("/api/stations/")
  .then((res) => {
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  })
  .then((stations) => {
    stations.forEach((station) => {
      L.circleMarker([station.lat, station.lng], {
        radius: 9,
        color: "#0f172a",
        weight: 2,
        fillColor: "#64748b",
        fillOpacity: 0.85,
      })
        .bindPopup(
          `<div class="station-popup">
             <strong>${station.name}</strong>
             <span class="coords">${station.lat.toFixed(4)}, ${station.lng.toFixed(4)}</span>
           </div>`
        )
        .addTo(map);
    });
    stationCountEl.textContent = `${stations.length} estaciones`;
  })
  .catch((err) => {
    console.error("Error cargando estaciones:", err);
    stationCountEl.textContent = "Error al cargar estaciones";
  });
