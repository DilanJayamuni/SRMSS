let trackingMap = null;
let vehicleMarkers = {};
let vehicleData = [];
let pollInterval = null;

const markerColors = {
    'In Transit': '#2563eb',
    'Scheduled': '#eab308',
    'Completed': '#16a34a',
    'Delayed': '#ef4444',
    'Cancelled': '#64748b'
};

function vehicleIcon(status) {
    const color = markerColors[status] || '#64748b';
    return L.divIcon({
        className: '',
        html: `
        <div style="position:relative;width:48px;height:48px;display:flex;align-items:center;justify-content:center;">
            <div style="position:absolute;inset:0;border-radius:50%;background:${color};opacity:0.25;animation:pulse-ring 2s infinite;"></div>
            <div style="background:${color};border-radius:50%;width:38px;height:38px;border:3px solid #fff;box-shadow:0 3px 12px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;z-index:1;">
                <i class="fas fa-truck" style="color:#fff;font-size:16px;"></i>
            </div>
        </div>`,
        iconSize: [48, 48],
        iconAnchor: [24, 24]
    });
}

function initTrackingMap() {
    const container = document.getElementById('tracking-map');
    if (!container) return;
    trackingMap = L.map('tracking-map').setView([6.9271, 79.8612], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(trackingMap);
}

function buildPopupHtml(v) {
    const badgeColor = markerColors[v.status] || '#64748b';
    return `
        <div style="min-width:200px;">
            <div style="font-weight:700;font-size:16px;margin-bottom:8px;">${v.registration_no}</div>
            <table style="width:100%;font-size:13px;">
                <tr><td style="padding:2px 8px 2px 0;opacity:0.7;">Type</td><td>${v.vehicle_type || '—'}</td></tr>
                <tr><td style="padding:2px 8px 2px 0;opacity:0.7;">Route</td><td>${v.route_name || '—'}</td></tr>
                <tr><td style="padding:2px 8px 2px 0;opacity:0.7;">Driver</td><td>${v.driver_name || '—'}</td></tr>
                <tr><td style="padding:2px 8px 2px 0;opacity:0.7;">Speed</td><td>${v.speed || 0} km/h</td></tr>
                <tr><td style="padding:2px 8px 2px 0;opacity:0.7;">Progress</td><td>${v.progress || 0}%</td></tr>
                <tr><td style="padding:2px 8px 2px 0;opacity:0.7;">Status</td><td><span style="background:${badgeColor};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;">${v.status}</span></td></tr>
            </table>
            <div style="margin-top:6px;font-size:11px;opacity:0.5;">Simulated position</div>
        </div>
    `;
}

async function fetchTrackingData() {
    const data = await apiGet('/api/tracking');
    if (data) {
        vehicleData = data;
        updateMarkers();
        updateStatusBar();
    }
}

function updateMarkers() {
    const map = trackingMap;
    if (!map) return;

    const activeIds = new Set(vehicleData.map(v => v.vehicle_id));
    const container = document.getElementById('tracking-map');
    const emptyEl = document.getElementById('tracking-empty');

    if (vehicleData.length === 0) {
        if (container) container.style.display = 'none';
        if (emptyEl) emptyEl.style.display = 'block';
    } else {
        if (container) container.style.display = 'block';
        if (emptyEl) emptyEl.style.display = 'none';
    }

    for (const id in vehicleMarkers) {
        if (!activeIds.has(parseInt(id))) {
            map.removeLayer(vehicleMarkers[id]);
            delete vehicleMarkers[id];
        }
    }

    const bounds = [];
    for (const v of vehicleData) {
        const id = v.vehicle_id;
        const latlng = [v.latitude, v.longitude];

        if (vehicleMarkers[id]) {
            vehicleMarkers[id].setLatLng(latlng);
        } else {
            const marker = L.marker(latlng, { icon: vehicleIcon(v.status) })
                .addTo(map)
                .bindPopup(buildPopupHtml(v));
            vehicleMarkers[id] = marker;
        }

        vehicleMarkers[id].setPopupContent(buildPopupHtml(v));
        bounds.push(latlng);
    }

    if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
    }
}

function updateStatusBar() {
    const countEl = document.getElementById('tracking-vehicle-count');
    const updateEl = document.getElementById('tracking-last-update');
    if (countEl) countEl.innerText = `${vehicleData.length} vehicle${vehicleData.length !== 1 ? 's' : ''} tracked`;
    if (updateEl) updateEl.innerText = `Last updated: ${new Date().toLocaleTimeString()}`;
}

function refreshTracking() {
    const btn = document.getElementById('refresh-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
    }
    fetchTrackingData().then(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
        }
    });
}

function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(fetchTrackingData, 10000);
}

(function init() {
    initTrackingMap();
    fetchTrackingData().then(() => {
        startPolling();
    });
})();
