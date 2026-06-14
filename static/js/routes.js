let map = null;
let drawnRouteLayer = null;
let stopMarkersLayer = null;
let tempRouteData = {};
let searchMarker = null;
let searchTimeout = null;
let deleteTargetId = null;
let pendingStopLatLng = null;
let workflow = { mode: 'create', editingId: null, replacing: null };

function colorIcon(color) {
    return L.divIcon({
        className: '',
        html: `<div style="background:${color};border-radius:50%;width:22px;height:22px;border:3px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,0.3);"></div>`,
        iconSize: [22, 22],
        iconAnchor: [11, 11]
    });
}
const greenIcon = colorIcon('#22c55e');
const redIcon = colorIcon('#ef4444');
const blueIcon = colorIcon('#3b82f6');

function safeParseStops(stops) {
    if (!stops) return [];
    try { return JSON.parse(stops); } catch (_) {}
    return stops.split(',').map(function(s) { return s.trim(); }).filter(Boolean);
}

(async function loadRoutes() {
    const tbody = document.getElementById('routes-table-body');
    if (!tbody) return;
    const items = await apiGet('/api/routes');
    if (items) {
        const role = document.getElementById('user-role-display').innerText;
        const isAdmin = role === 'Administrator';
        tbody.innerHTML = items.map(i => {
            const actions = isAdmin
                ? `<td><button class="btn btn-sm btn-primary" onclick="openEditMode(${i.id})">Edit</button> <button class="btn btn-sm btn-danger" onclick="deleteRoute(${i.id})">Delete</button></td>`
                : '';
            const stopsCount = safeParseStops(i.stops).length;
            return `<tr><td>${i.route_name}</td><td>${i.distance_km} km</td><td>${stopsCount}</td>${actions}</tr>`;
        }).join('');
    }
})();

function initRouteMap() {
    map = L.map('map').setView([6.9271, 79.8612], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    drawnRouteLayer = L.layerGroup().addTo(map);
    stopMarkersLayer = L.layerGroup().addTo(map);
    tempRouteData = { start: null, end: null, geometry: [], stops: [] };

    map.on('click', function(e) {
        if (workflow.mode === 'edit') {
            handleEditClick(e);
            return;
        }
        if (!tempRouteData.start) {
            tempRouteData.start = e.latlng;
            L.marker(e.latlng, { icon: greenIcon }).addTo(drawnRouteLayer).bindPopup("Start").openPopup();
            document.getElementById('r_start_name').value = "Start";
        } else if (!tempRouteData.end) {
            tempRouteData.end = e.latlng;
            L.marker(e.latlng, { icon: redIcon }).addTo(drawnRouteLayer).bindPopup("End").openPopup();
            document.getElementById('r_end_name').value = "End";
            calculateRoute();
        }
    });
}

function handleEditClick(e) {
    if (workflow.replacing === 'start') {
        tempRouteData.start = e.latlng;
        workflow.replacing = null;
        renderEditActions();
        if (tempRouteData.end) calculateRoute();
    } else if (workflow.replacing === 'end') {
        tempRouteData.end = e.latlng;
        workflow.replacing = null;
        renderEditActions();
        if (tempRouteData.start) calculateRoute();
    }
}

function renderEditActions() {
    const container = document.getElementById('edit-mode-actions');
    if (workflow.mode === 'edit') {
        container.innerHTML = `
            Change <a href="#" onclick="startReplace('start');return false;" style="color:var(--primary)">Start</a> |
            <a href="#" onclick="startReplace('end');return false;" style="color:var(--primary)">End</a>
            &nbsp; <span style="opacity:0.5">(click highlighted to replace)</span>`;
    } else {
        container.innerHTML = '';
    }
}

function startReplace(type) {
    workflow.replacing = type;
    document.getElementById('edit-mode-actions').innerHTML = `Click on the map to set new ${type} point...`;
}

async function calculateRoute() {
    const start = tempRouteData.start;
    const end = tempRouteData.end;
    const url = `https://router.project-osrm.org/route/v1/driving/${start.lng},${start.lat};${end.lng},${end.lat}?overview=full&geometries=geojson`;
    try {
        const res = await fetch(url);
        const data = await res.json();
        if (data.routes && data.routes.length > 0) {
            const route = data.routes[0];
            document.getElementById('r_dist').value = (route.distance / 1000).toFixed(2);
            const coords = route.geometry.coordinates.map(c => [c[1], c[0]]);
            tempRouteData.geometry = coords;

            drawnRouteLayer.clearLayers();
            L.marker(start, { icon: greenIcon }).addTo(drawnRouteLayer);
            L.marker(end, { icon: redIcon }).addTo(drawnRouteLayer);

            const polyline = L.polyline(coords, { color: '#2563eb', weight: 5 }).addTo(drawnRouteLayer);
            map.fitBounds(polyline.getBounds());

            polyline.on('click', function(e) {
                L.DomEvent.stopPropagation(e);
                showStopModal(e.latlng);
            });
        }
    } catch (err) { alert("Route error"); }
}

function renderStopList() {
    const container = document.getElementById('stops-list');
    container.innerHTML = '';
    tempRouteData.stops.forEach((s, i) => {
        container.innerHTML += `<div>${i + 1}. ${s.name}</div>`;
    });
}

async function saveRoute() {
    const payload = {
        route_name: document.getElementById('r_name').value,
        distance_km: document.getElementById('r_dist').value,
        start_point: document.getElementById('r_start_name').value,
        end_point: document.getElementById('r_end_name').value,
        path_geometry: JSON.stringify(tempRouteData.geometry || []),
        stops: JSON.stringify(tempRouteData.stops || [])
    };
    if (workflow.mode === 'edit') {
        await apiPut(`/api/routes/${workflow.editingId}`, payload);
    } else {
        await apiPost('/api/routes', payload);
    }
    const isEdit = workflow.mode === 'edit';
    document.getElementById('success-modal-title').textContent = isEdit ? 'Route Updated' : 'Route Saved';
    document.getElementById('success-modal-message').textContent = isEdit ? 'Route has been updated successfully.' : 'Route has been saved successfully.';
    document.getElementById('success-modal').style.display = 'flex';
}

function closeSuccessModal() {
    document.getElementById('success-modal').style.display = 'none';
    window.location.reload();
}

function initSearch() {
    const input = document.getElementById('city-search');
    if (!input) return;
    input.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const q = this.value.trim();
        if (!q) {
            document.getElementById('search-suggestions').style.display = 'none';
            return;
        }
        searchTimeout = setTimeout(function() { performSearch(q); }, 300);
    });
}

async function performSearch(q) {
    try {
        const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=5&accept-language=en`, {
            headers: { 'User-Agent': 'SRMSS/1.0' }
        });
        const data = await res.json();
        const container = document.getElementById('search-suggestions');
        if (!data || data.length === 0) {
            container.innerHTML = '<div style="padding:10px;font-size:13px;opacity:0.7;">No results found</div>';
            container.style.display = 'block';
            return;
        }
        container.innerHTML = data.map(function(p) {
            return `<div class="search-suggestion-item" data-lat="${p.lat}" data-lon="${p.lon}" data-display="${p.display_name}" style="padding:10px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--input-border);">${p.display_name}</div>`;
        }).join('');
        container.style.display = 'block';

        container.querySelectorAll('.search-suggestion-item').forEach(function(el) {
            el.addEventListener('click', function() {
                selectSuggestion(parseFloat(this.dataset.lat), parseFloat(this.dataset.lon), this.dataset.display);
            });
        });
    } catch (e) {
        console.error("Search error:", e);
    }
}

function selectSuggestion(lat, lon, display) {
    document.getElementById('city-search').value = display.split(',')[0];
    document.getElementById('search-suggestions').style.display = 'none';
    if (searchMarker) map.removeLayer(searchMarker);
    searchMarker = L.marker([lat, lon]).addTo(drawnRouteLayer).bindPopup(display.split(',')[0]).openPopup();
    map.flyTo([lat, lon], 14);
}

document.addEventListener('click', function(e) {
    const container = document.getElementById('search-suggestions');
    if (container && !e.target.closest('.search-container')) {
        container.style.display = 'none';
    }
});

async function openEditMode(id) {
    const data = await apiGet(`/api/routes/${id}`);
    if (!data) return;
    workflow.mode = 'edit';
    workflow.editingId = id;
    workflow.replacing = null;

    document.getElementById('define-route-title').textContent = 'Edit Route';
    document.getElementById('save-route-btn').textContent = 'Update Route';
    document.getElementById('cancel-edit-btn').classList.remove('hidden');

    const geometry = JSON.parse(data.path_geometry || '[]');
    const stops = safeParseStops(data.stops);

    tempRouteData = {
        start: geometry.length > 0 ? L.latLng(geometry[0][0], geometry[0][1]) : null,
        end: geometry.length > 0 ? L.latLng(geometry[geometry.length - 1][0], geometry[geometry.length - 1][1]) : null,
        geometry: geometry,
        stops: stops
    };

    document.getElementById('r_name').value = data.route_name;
    document.getElementById('r_dist').value = data.distance_km;
    document.getElementById('r_start_name').value = data.start_point;
    document.getElementById('r_end_name').value = data.end_point;

    drawnRouteLayer.clearLayers();
    stopMarkersLayer.clearLayers();

    if (tempRouteData.start) {
        L.marker(tempRouteData.start, { icon: greenIcon }).addTo(drawnRouteLayer).bindPopup("Start");
    }
    if (tempRouteData.end) {
        L.marker(tempRouteData.end, { icon: redIcon }).addTo(drawnRouteLayer).bindPopup("End");
    }
    if (geometry.length > 0) {
        const polyline = L.polyline(geometry, { color: '#2563eb', weight: 5 }).addTo(drawnRouteLayer);
        map.fitBounds(polyline.getBounds());
        polyline.on('click', function(e) {
            L.DomEvent.stopPropagation(e);
            showStopModal(e.latlng);
        });
    }
    stops.forEach(function(s) {
        L.marker([s.lat, s.lon], { icon: blueIcon }).addTo(stopMarkersLayer).bindPopup(s.name);
    });
    renderStopList();
    renderEditActions();
}

function cancelEdit() {
    workflow = { mode: 'create', editingId: null, replacing: null };
    tempRouteData = { start: null, end: null, geometry: [], stops: [] };
    drawnRouteLayer.clearLayers();
    stopMarkersLayer.clearLayers();
    document.getElementById('define-route-title').textContent = 'Define Route';
    document.getElementById('save-route-btn').textContent = 'Save Route';
    document.getElementById('cancel-edit-btn').classList.add('hidden');
    document.getElementById('r_name').value = '';
    document.getElementById('r_dist').value = '';
    document.getElementById('r_start_name').value = '';
    document.getElementById('r_end_name').value = '';
    document.getElementById('stops-list').innerHTML = 'Click map to start.';
    document.getElementById('edit-mode-actions').innerHTML = '';
}

function showStopModal(latlng) {
    pendingStopLatLng = latlng;
    document.getElementById('stop-name-input').value = '';
    document.getElementById('stop-modal').style.display = 'flex';
    document.getElementById('stop-name-input').focus();
}

function closeStopModal() {
    pendingStopLatLng = null;
    document.getElementById('stop-modal').style.display = 'none';
}

function confirmStop() {
    const stopName = document.getElementById('stop-name-input').value.trim();
    if (!stopName) { showToast('Stop name is required.', 'error'); return; }
    const latlng = pendingStopLatLng;
    closeStopModal();
    L.marker(latlng, { icon: blueIcon }).addTo(stopMarkersLayer).bindPopup(stopName);
    tempRouteData.stops.push({ name: stopName, lat: latlng.lat, lon: latlng.lng });
    renderStopList();
}

function deleteRoute(id) {
    deleteTargetId = id;
    document.getElementById('delete-modal').style.display = 'flex';
}

function closeDeleteModal() {
    deleteTargetId = null;
    document.getElementById('delete-modal').style.display = 'none';
}

async function confirmDelete() {
    if (deleteTargetId === null) return;
    await apiDel(`/api/routes/${deleteTargetId}`);
    closeDeleteModal();
    window.location.reload();
}

if (document.getElementById('map')) {
    initRouteMap();
    initSearch();
}
