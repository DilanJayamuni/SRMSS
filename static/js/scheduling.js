let currentAssignment = null;
let deleteTargetId = null;
let conflictResolver = null;
let _schedules = null;
let viewModalMap = null;
let editModalMap = null;

(async function loadTimetableForm() {
    const tbody = document.getElementById('timetable-body');
    const vehSel = document.getElementById('t_vehicle');
    const editVehSel = document.getElementById('edit_vehicle');
    if (!tbody) return;

    const [schedules, vehicles] = await Promise.all([
        apiGet('/api/schedules'),
        apiGet('/api/vehicles')
    ]);

    const vehOpts = '<option value="">Select Vehicle</option>' + (vehicles ? vehicles.map(v => `<option value="${v.id}">${v.registration_no}</option>`).join('') : '');
    if (vehSel) vehSel.innerHTML = vehOpts;
    if (editVehSel) editVehSel.innerHTML = vehOpts;

    if (vehSel) vehSel.addEventListener('change', onVehicleChange);
    if (editVehSel) editVehSel.addEventListener('change', onEditVehicleChange);

    if (schedules && tbody) {
        _schedules = schedules;
        const isAdmin = document.querySelector('meta[name="user-role"]') ? false : document.getElementById('user-role-display') && document.getElementById('user-role-display').innerText === 'Administrator';
        tbody.innerHTML = schedules.map(s => {
            const badgeClass = s.status === 'Scheduled' ? 'badge-blue' : s.status === 'Completed' ? 'badge-green' : 'badge-red';
            const arrivalDisplay = s.arrival_time || '-';
            const actions = isAdmin ? `<td><button class="btn btn-sm btn-secondary" onclick="openEditModal(${s.id})">Edit</button> <button class="btn btn-sm btn-danger" onclick="openDeleteModal(${s.id})">Delete</button></td>` : '';
            return `<tr data-id="${s.id}"><td>${s.registration_no}</td><td>${s.route_name}</td><td>${s.driver_name}</td><td>${s.departure_time}</td><td>${arrivalDisplay}</td><td><span class="badge ${badgeClass}">${s.status}</span></td>${actions}</tr>`;
        }).join('');
        tbody.querySelectorAll('tr').forEach(tr => {
            tr.addEventListener('click', function(e) {
                if (e.target.closest('button')) return;
                const id = parseInt(this.dataset.id);
                if (id) openViewModal(id);
            });
        });
    }
})();

async function onVehicleChange() {
    const vehId = document.getElementById('t_vehicle').value;
    const display = document.getElementById('assignment-display');
    const error = document.getElementById('assignment-error');
    const fields = document.getElementById('schedule-fields');

    if (!vehId) {
        display.style.display = 'none';
        error.style.display = 'none';
        fields.style.display = 'none';
        return;
    }

    const res = await fetch('/api/vehicle-assignment/' + vehId);
    if (!res.ok) {
        const data = await res.json();
        display.style.display = 'none';
        error.style.display = 'block';
        error.innerText = data.error || 'Vehicle assignment not found.';
        fields.style.display = 'none';
        currentAssignment = null;
        return;
    }

    const data = await res.json();
    document.getElementById('t_driver_display').innerText = data.driver.name;
    document.getElementById('t_route_display').innerText = data.route.route_name + ' (' + data.route.start_point + ' → ' + data.route.end_point + ')';
    display.style.display = 'block';
    error.style.display = 'none';
    fields.style.display = 'block';
    currentAssignment = { driver_id: data.driver.id, route_id: data.route.id };
}

async function onEditVehicleChange() {
    const vehId = document.getElementById('edit_vehicle').value;
    const error = document.getElementById('edit-assignment-error');

    if (!vehId) {
        document.getElementById('edit_driver_display').innerText = '';
        document.getElementById('edit_route_display').innerText = '';
        error.style.display = 'none';
        currentAssignment = null;
        return;
    }

    const res = await fetch('/api/vehicle-assignment/' + vehId);
    if (!res.ok) {
        const data = await res.json();
        document.getElementById('edit_driver_display').innerText = '';
        document.getElementById('edit_route_display').innerText = '';
        error.style.display = 'block';
        error.innerText = data.error || 'Vehicle assignment not found.';
        currentAssignment = null;
        return;
    }

    const data = await res.json();
    document.getElementById('edit_driver_display').innerText = data.driver.name;
    document.getElementById('edit_route_display').innerText = data.route.route_name;
    error.style.display = 'none';
    currentAssignment = { driver_id: data.driver.id, route_id: data.route.id };
    loadEditMap(data.route.id);
}

async function loadEditMap(routeId) {
    if (!routeId) return;
    const route = await apiGet('/api/routes/' + routeId);
    if (!route) return;

    if (editModalMap) editModalMap.remove();
    editModalMap = L.map(document.getElementById('edit-map')).setView([6.9271, 79.8612], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(editModalMap);

    if (route.path_geometry) {
        const coords = JSON.parse(route.path_geometry);
        L.polyline(coords, { color: 'blue', weight: 5 }).addTo(editModalMap);
        editModalMap.fitBounds(coords);
    }

    const stops = JSON.parse(route.stops || '[]');
    if (stops.length > 0) {
        L.circleMarker([stops[0].lat, stops[0].lon], { color: 'green', radius: 10, fillColor: '#22c55e', fillOpacity: 1 })
            .addTo(editModalMap).bindPopup('Start');
        L.circleMarker([stops[stops.length - 1].lat, stops[stops.length - 1].lon], { color: 'red', radius: 10, fillColor: '#ef4444', fillOpacity: 1 })
            .addTo(editModalMap).bindPopup('End');
        for (let i = 1; i < stops.length - 1; i++) {
            L.circleMarker([stops[i].lat, stops[i].lon], { color: '#3b82f6', radius: 8, fillColor: '#3b82f6', fillOpacity: 0.8 })
                .addTo(editModalMap).bindPopup(stops[i].name);
        }
    }
}

async function saveTimetable() {
    const departure = document.getElementById('t_departure').value;
    const arrival = document.getElementById('t_arrival').value;
    const conflictMsg = document.getElementById('conflict-msg');

    if (!departure) { conflictMsg.innerText = 'Departure time is required.'; return; }
    if (!arrival) { conflictMsg.innerText = 'Estimated arrival time is required.'; return; }
    if (arrival <= departure) { conflictMsg.innerText = 'Estimated arrival must be later than departure.'; return; }
    if (!currentAssignment) { conflictMsg.innerText = 'Please select a vehicle with valid assignments.'; return; }

    const payload = {
        route_id: currentAssignment.route_id,
        vehicle_id: parseInt(document.getElementById('t_vehicle').value),
        driver_id: currentAssignment.driver_id,
        departure_time: departure,
        arrival_time: arrival
    };

    conflictMsg.innerText = '';
    document.getElementById('save-btn').disabled = true;

    const check = await apiPost('/api/schedules/check', payload);
    const data = await check.json();

    if (data.conflict) {
        conflictMsg.innerText = 'Warning: ' + data.message;
        const force = await showConflictModal(data.message);
        if (force) {
            await apiPost('/api/schedules', payload);
            window.location.reload();
        } else {
            document.getElementById('save-btn').disabled = false;
        }
    } else {
        conflictMsg.innerText = '';
        await apiPost('/api/schedules', payload);
        window.location.reload();
    }
}

async function openEditModal(id) {
    const schedules = await apiGet('/api/schedules');
    const s = schedules.find(item => item.id === id);
    if (!s) return;

    document.getElementById('edit_id').value = s.id;
    document.getElementById('edit_vehicle').value = s.vehicle_id || '';
    document.getElementById('edit_departure').value = s.departure_time || '';
    document.getElementById('edit_arrival').value = s.arrival_time || '';
    document.getElementById('edit_driver_display').innerText = s.driver_name || '';
    document.getElementById('edit_route_display').innerText = s.route_name || '';
    document.getElementById('edit-assignment-error').style.display = 'none';
    document.getElementById('edit-conflict-msg').innerText = '';
    currentAssignment = { driver_id: s.driver_id, route_id: s.route_id };

    document.getElementById('edit-modal').style.display = 'flex';

    setTimeout(() => loadEditMap(s.route_id), 200);
}

function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
    if (editModalMap) {
        editModalMap.remove();
        editModalMap = null;
    }
}

async function saveEdit() {
    const id = document.getElementById('edit_id').value;
    const departure = document.getElementById('edit_departure').value;
    const arrival = document.getElementById('edit_arrival').value;
    const conflictMsg = document.getElementById('edit-conflict-msg');

    if (!departure) { conflictMsg.innerText = 'Departure time is required.'; return; }
    if (!arrival) { conflictMsg.innerText = 'Estimated arrival time is required.'; return; }
    if (arrival <= departure) { conflictMsg.innerText = 'Estimated arrival must be later than departure.'; return; }
    if (!currentAssignment) { conflictMsg.innerText = 'Please select a vehicle with valid assignments.'; return; }

    const payload = {
        route_id: currentAssignment.route_id,
        vehicle_id: parseInt(document.getElementById('edit_vehicle').value),
        driver_id: currentAssignment.driver_id,
        departure_time: departure,
        arrival_time: arrival
    };

    conflictMsg.innerText = '';

    const checkPayload = { ...payload, exclude_id: parseInt(id) };
    const check = await apiPost('/api/schedules/check', checkPayload);
    const data = await check.json();

    if (data.conflict) {
        conflictMsg.innerText = 'Warning: ' + data.message;
        const force = await showConflictModal(data.message);
        if (!force) return;
    }

    const res = await apiPut('/api/schedules/' + id, payload);
    if (res.ok) {
        window.location.reload();
    } else {
        const err = await res.json();
        conflictMsg.innerText = err.error || 'Failed to update schedule.';
    }
}

function showConflictModal(message) {
    return new Promise((resolve) => {
        conflictResolver = resolve;
        document.getElementById('conflict-modal-msg').innerText = message;
        document.getElementById('conflict-modal').style.display = 'flex';
    });
}

function resolveConflict(force) {
    document.getElementById('conflict-modal').style.display = 'none';
    if (conflictResolver) {
        conflictResolver(force);
        conflictResolver = null;
    }
}

function openDeleteModal(id) {
    deleteTargetId = id;
    document.getElementById('delete-modal').style.display = 'flex';
}

function closeDeleteModal() {
    deleteTargetId = null;
    document.getElementById('delete-modal').style.display = 'none';
}

async function confirmDelete() {
    if (!deleteTargetId) return;
    await apiDel('/api/schedules/' + deleteTargetId);
    window.location.reload();
}

async function openViewModal(id) {
    const s = _schedules.find(item => item.id === id);
    if (!s) return;

    document.getElementById('view_vehicle').innerText = s.registration_no || '';
    document.getElementById('view_driver').innerText = s.driver_name || '';
    document.getElementById('view_route').innerText = s.route_name || '';
    document.getElementById('view_departure').innerText = s.departure_time || '';
    document.getElementById('view_arrival').innerText = s.arrival_time || '';
    document.getElementById('view_status').innerHTML = `<span class="badge ${s.status === 'Scheduled' ? 'badge-blue' : s.status === 'Completed' ? 'badge-green' : 'badge-red'}">${s.status}</span>`;
    document.getElementById('view_recurrence').innerText = s.recurrence || 'Once';

    document.getElementById('view-modal').style.display = 'flex';

    setTimeout(async () => {
        if (viewModalMap) viewModalMap.remove();
        const mapEl = document.getElementById('view-map');
        viewModalMap = L.map(mapEl).setView([6.9271, 79.8612], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(viewModalMap);

        const route = await apiGet('/api/routes/' + s.route_id);
        if (!route) return;

        if (route.path_geometry) {
            const coords = JSON.parse(route.path_geometry);
            L.polyline(coords, { color: 'blue', weight: 5 }).addTo(viewModalMap);
            viewModalMap.fitBounds(coords);
        }

        const stops = JSON.parse(route.stops || '[]');
        if (stops.length > 0) {
            L.circleMarker([stops[0].lat, stops[0].lon], { color: 'green', radius: 10, fillColor: '#22c55e', fillOpacity: 1 })
                .addTo(viewModalMap).bindPopup('Start');
            L.circleMarker([stops[stops.length - 1].lat, stops[stops.length - 1].lon], { color: 'red', radius: 10, fillColor: '#ef4444', fillOpacity: 1 })
                .addTo(viewModalMap).bindPopup('End');
            for (let i = 1; i < stops.length - 1; i++) {
                L.circleMarker([stops[i].lat, stops[i].lon], { color: '#3b82f6', radius: 8, fillColor: '#3b82f6', fillOpacity: 0.8 })
                    .addTo(viewModalMap).bindPopup(stops[i].name);
            }
        }
    }, 200);
}

function closeViewModal() {
    document.getElementById('view-modal').style.display = 'none';
    if (viewModalMap) {
        viewModalMap.remove();
        viewModalMap = null;
    }
}

(async function loadControlCenter() {
    const container = document.getElementById('trip-cards');
    if (!container) return;
    const operations = await apiGet('/api/operations/today');
    if (!operations) { container.innerHTML = '<p>No operations today.</p>'; return; }
    container.innerHTML = operations.map(op => {
        const isDelayed = op.status === 'Delayed';
        const isComplete = op.status === 'Completed';
        const statusClass = isDelayed ? 'delayed' : (isComplete ? 'completed' : 'ontime');
        const badgeClass = isDelayed ? 'badge-red' : (isComplete ? 'badge-purple' : 'badge-green');
        return `<div class="status-card ${statusClass}">
            <h4>${op.route_name} - ${op.registration_no}</h4>
            <p>Driver: ${op.driver_name} | Time: ${op.departure_time}</p>
            <div style="margin-top:10px;">
                <span class="badge ${badgeClass}">${op.status}</span>
                <button class="btn btn-sm btn-secondary" onclick="updateTripStatus(${op.id}, 'Delayed')">Delay</button>
                <button class="btn btn-sm btn-success" onclick="updateTripStatus(${op.id}, 'Completed')">Complete</button>
            </div>
        </div>`;
    }).join('');
})();

async function updateTripStatus(id, status) {
    await apiPost('/api/operations/status/' + id, { status: status });
    window.location.reload();
}
