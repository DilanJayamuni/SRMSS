(async function loadAssignments() {
    const tbody = document.getElementById('assignments-table-body');
    if (!tbody) return;
    const items = await apiGet('/api/assign-route') || [];
    const role = document.getElementById('user-role-display').innerText;
    const isAdmin = role === 'Administrator';
    tbody.innerHTML = items.map(i => {
        const actions = isAdmin
            ? `<td><button class="btn btn-sm btn-primary" onclick="openEditModal(${i.id})">Edit</button> <button class="btn btn-sm btn-danger" onclick="deleteAssignment(${i.id})">Delete</button></td>`
            : '';
        const date = i.assigned_at ? new Date(i.assigned_at).toLocaleDateString() : 'N/A';
        return `<tr><td>${i.route_name}</td><td>${i.vehicle_reg}</td><td>${date}</td>${actions}</tr>`;
    }).join('');

    const vehicleSel = document.getElementById('a_vehicle');
    const routeSel = document.getElementById('a_route');
    const avail = await apiGet('/api/assign-route/available') || { routes: [], vehicles: [] };
    if (vehicleSel) {
        vehicleSel.innerHTML = '<option value="">-- Select Vehicle --</option>' +
            avail.vehicles.map(v => `<option value="${v.id}">${v.registration_no}</option>`).join('');
    }
    if (routeSel) {
        routeSel.innerHTML = '<option value="">-- Select Route --</option>' +
            avail.routes.map(r => `<option value="${r.id}">${r.route_name}</option>`).join('');
    }
})();

async function saveAssignment() {
    const vehicleId = document.getElementById('a_vehicle').value;
    const routeId = document.getElementById('a_route').value;
    if (!vehicleId || !routeId) {
        showToast('Please select both a vehicle and a route.', 'error');
        return;
    }
    const resp = await apiPost('/api/assign-route', { vehicle_id: parseInt(vehicleId), route_id: parseInt(routeId) });
    if (!resp.ok) {
        const err = await resp.json();
        showToast(err.error || 'Failed to create assignment.', 'error');
        return;
    }
    window.location.reload();
}

let deleteTargetId = null;

function openEditModal(id) {
    apiGet(`/api/assign-route/${id}`).then(async i => {
        document.getElementById('edit_id').value = i.id;
        document.getElementById('edit_route').value = i.route_name;
        const avail = await apiGet('/api/assign-route/available') || { vehicles: [] };
        const vehicleSel = document.getElementById('edit_vehicle');
        vehicleSel.innerHTML = `<option value="${i.vehicle_id}">${i.vehicle_reg} (current)</option>` +
            avail.vehicles.map(v => `<option value="${v.id}">${v.registration_no}</option>`).join('');
        document.getElementById('edit-modal').style.display = 'flex';
    });
}

function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

async function saveEdit() {
    const id = document.getElementById('edit_id').value;
    const vehicleId = document.getElementById('edit_vehicle').value;
    if (!vehicleId) {
        showToast('Please select a vehicle.', 'error');
        return;
    }
    const resp = await apiPut(`/api/assign-route/${id}`, { vehicle_id: parseInt(vehicleId) });
    if (!resp.ok) {
        const err = await resp.json();
        showToast(err.error || 'Failed to update assignment.', 'error');
        return;
    }
    window.location.reload();
}

function deleteAssignment(id) {
    deleteTargetId = id;
    document.getElementById('delete-modal').style.display = 'flex';
}

function closeDeleteModal() {
    deleteTargetId = null;
    document.getElementById('delete-modal').style.display = 'none';
}

async function confirmDelete() {
    if (deleteTargetId === null) return;
    await apiDel(`/api/assign-route/${deleteTargetId}`);
    closeDeleteModal();
    window.location.reload();
}
