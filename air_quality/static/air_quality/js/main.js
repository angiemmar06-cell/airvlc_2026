const VALENCIA_CENTER = [39.47, -0.376];
const DEFAULT_ZOOM = 13;
const DEFAULT_MARKER_COLOR = "#64748b";
const MARKER_STYLE = { radius: 9, color: "#0f172a", weight: 2, fillOpacity: 0.85 };

const map = L.map("map").setView(VALENCIA_CENTER, DEFAULT_ZOOM);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  maxZoom: 19,
}).addTo(map);

const els = {
  pollutant: document.getElementById("pollutant"),
  station: document.getElementById("station"),
  startDate: document.getElementById("start-date"),
  endDate: document.getElementById("end-date"),
  presets: document.querySelectorAll("[data-preset]"),
  apply: document.getElementById("apply"),
  stats: document.getElementById("stats"),
  chartSection: document.getElementById("chart-section"),
  chartCanvas: document.getElementById("chart"),
  stationCount: document.getElementById("station-count"),
};

let chartInstance = null;

const markers = new Map(); // name -> L.circleMarker
let dataRange = { min_date: null, max_date: null };

function resetAllMarkers() {
  for (const marker of markers.values()) {
    marker.setStyle({ fillColor: DEFAULT_MARKER_COLOR });
  }
}

function colorStationMarker(name, color) {
  const marker = markers.get(name);
  if (marker) marker.setStyle({ fillColor: color });
}

async function loadStations() {
  const res = await fetch("/api/stations/");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const stations = await res.json();

  stations.forEach((s) => {
    const marker = L.circleMarker([s.lat, s.lng], {
      ...MARKER_STYLE,
      fillColor: DEFAULT_MARKER_COLOR,
    })
      .bindPopup(
        `<div class="station-popup">
           <strong>${s.name}</strong>
           <span class="coords">${s.lat.toFixed(4)}, ${s.lng.toFixed(4)}</span>
         </div>`
      )
      .addTo(map);

    // Sincronia: click en marker -> selecciona en el dropdown y dispara la consulta.
    marker.on("click", () => {
      els.station.value = s.name;
      applyFilters();
    });

    markers.set(s.name, marker);

    const opt = document.createElement("option");
    opt.value = s.name;
    opt.textContent = s.name;
    els.station.appendChild(opt);
  });

  els.stationCount.textContent = `${stations.length} estaciones`;
  if (stations.length && !els.station.value) {
    els.station.value = stations[0].name;
  }
}

async function loadMeta() {
  const res = await fetch("/api/meta/");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  dataRange = await res.json();
}

function subtractDays(dateStr, days) {
  const d = new Date(dateStr + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() - days);
  return d.toISOString().slice(0, 10);
}

function addDays(dateStr, days) {
  const d = new Date(dateStr + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

const PRESET_DAYS = { "1m": 30, "1y": 365, "5y": 365 * 5 };

function applyPreset(preset) {
  const max = dataRange.max_date;
  const min = dataRange.min_date;
  if (!max || !min) return;

  if (preset === "all") {
    els.startDate.value = min;
    els.endDate.value = max;
  } else if (els.startDate.value) {
    // Usuario puso una fecha en Desde -> avanzamos N dias hacia adelante,
    // capando en el maximo de datos disponibles.
    const end = addDays(els.startDate.value, PRESET_DAYS[preset]);
    els.endDate.value = end > max ? max : end;
  } else {
    // Sin Desde -> anclamos al final de datos y retrocedemos N dias.
    const start = subtractDays(max, PRESET_DAYS[preset]);
    els.startDate.value = start < min ? min : start;
    els.endDate.value = max;
  }

  els.presets.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.preset === preset);
  });
}

const formatValue = (v) => (v == null ? "—" : Number(v).toFixed(1));

function renderStats(data) {
  const cat = data.overall_category;
  const unit = data.unit || "";
  els.stats.hidden = false;
  els.stats.innerHTML = `
    <h2>Resumen — ${data.station}</h2>
    ${cat ? `<div class="ica-chip" style="background:${cat.color}">${cat.label}</div>` : ""}
    <dl class="stat-grid">
      <dt>Media</dt><dd>${formatValue(data.stats.mean)} ${unit}</dd>
      <dt>Mínimo</dt><dd>${formatValue(data.stats.min)} ${unit}</dd>
      <dt>Máximo</dt><dd>${formatValue(data.stats.max)} ${unit}</dd>
      <dt>Muestras</dt><dd>${data.stats.count}</dd>
    </dl>
  `;
}

function renderError(message) {
  els.stats.hidden = false;
  els.stats.innerHTML = `<p class="error">${message}</p>`;
  els.chartSection.hidden = true;
}

function renderChart(payload) {
  const points = payload.data || [];
  if (points.length === 0) {
    els.chartSection.hidden = true;
    return;
  }

  const labels = points.map((p) => p.time);
  const values = points.map((p) => p.value);
  const unit = payload.unit || "";

  // Chart.js no permite pintar dos veces en el mismo canvas: hay que
  // destruir el chart anterior antes de crear el nuevo.
  if (chartInstance) chartInstance.destroy();

  chartInstance = new Chart(els.chartCanvas.getContext("2d"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: `${payload.pollutant} (${unit})`,
        data: values,
        borderColor: "#38bdf8",
        backgroundColor: "rgba(56, 189, 248, 0.15)",
        fill: true,
        tension: 0.25,
        pointRadius: 0,
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: {
          ticks: { color: "#94a3b8", maxTicksLimit: 6 },
          grid: { color: "rgba(148, 163, 184, 0.1)" },
        },
        y: {
          ticks: { color: "#94a3b8" },
          grid: { color: "rgba(148, 163, 184, 0.1)" },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0f172a",
          titleColor: "#e2e8f0",
          bodyColor: "#e2e8f0",
          callbacks: {
            label: (ctx) => `${ctx.parsed.y?.toFixed(1)} ${unit}`,
          },
        },
      },
    },
  });

  els.chartSection.hidden = false;
}

async function applyFilters() {
  const station = els.station.value;
  if (!station) return;

  const params = new URLSearchParams({
    station,
    pollutant: els.pollutant.value,
    aggregate: "daily",
  });
  if (els.startDate.value) params.set("start_date", els.startDate.value);
  if (els.endDate.value) params.set("end_date", els.endDate.value);

  els.apply.disabled = true;
  els.apply.textContent = "Cargando…";

  try {
    const res = await fetch(`/api/measurements/?${params}`);
    const payload = await res.json();
    if (!res.ok) throw new Error(payload.error || `HTTP ${res.status}`);

    renderStats(payload);
    renderChart(payload);
    resetAllMarkers();
    if (payload.overall_category) {
      colorStationMarker(payload.station, payload.overall_category.color);
    }
  } catch (err) {
    console.error("Error al aplicar filtros:", err);
    renderError(err.message);
  } finally {
    els.apply.disabled = false;
    els.apply.textContent = "Aplicar";
  }
}

els.apply.addEventListener("click", applyFilters);
els.presets.forEach((btn) =>
  btn.addEventListener("click", () => applyPreset(btn.dataset.preset))
);

(async () => {
  try {
    await Promise.all([loadStations(), loadMeta()]);
    applyPreset("1y"); // default: ultimo año de datos disponibles
  } catch (err) {
    console.error("Error inicializando:", err);
    els.stationCount.textContent = "Error al cargar";
  }
})();
