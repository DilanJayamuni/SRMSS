(async function loadAssignments() {
    const tbody = document.getElementById('assignments-table-body');
    if (!tbody) return;
    const items = await apiGet('/api/assign-driver') || [];
    const role = document.getElementById('user-role-display').innerText;
    const isAdmin = role === 'Administrator';
    tbody.innerHTML = items.map(i => {
        const actions = isAdmin
            ? `<td><button class="btn btn-sm btn-primary" onclick="openEditModal(${i.id})">Edit</button> <button class="btn btn-sm btn-danger" onclick="deleteAssignment(${i.id})">Delete</button></td>`
            : '';
        const date = i.assigned_at ? new Date(i.assigned_at).toLocaleDateString() : 'N/A';
        return `<tr><td>${i.driver_name}</td><td>${i.vehicle_reg}</td><td>${date}</td>${actions}</tr>`;
    }).join('');

    const driverSel = document.getElementById('a_driver');
    const vehicleSel = document.getElementById('a_vehicle');
    if (!driverSel) return;
    const avail = await apiGet('/api/assign-driver/available') || { drivers: [], vehicles: [] };
    driverSel.innerHTML = '<option value="">-- Select Driver --</option>' +
        avail.drivers.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
    vehicleSel.innerHTML = '<option value="">-- Select Vehicle --</option>' +
        avail.vehicles.map(v => `<option value="${v.id}">${v.registration_no}</option>`).join('');
})();

async function saveAssignment() {
    const driverId = document.getElementById('a_driver').value;
    const vehicleId = document.getElementById('a_vehicle').value;
    if (!driverId || !vehicleId) {
        showToast('Please select both a driver and a vehicle.', 'error');
        return;
    }
    const resp = await apiPost('/api/assign-driver', { driver_id: parseInt(driverId), vehicle_id: parseInt(vehicleId) });
    if (!resp.ok) {
        const err = await resp.json();
        showToast(err.error || 'Failed to create assignment.', 'error');
        return;
    }
    window.location.reload();
}

let deleteTargetId = null;

function openEditModal(id) {
    apiGet(`/api/assign-driver/${id}`).then(async i => {
        document.getElementById('edit_id').value = i.id;
        document.getElementById('edit_vehicle').value = i.vehicle_reg;
        const avail = await apiGet('/api/assign-driver/available') || { drivers: [] };
        const driverSel = document.getElementById('edit_driver');
        driverSel.innerHTML = `<option value="${i.driver_id}">${i.driver_name} (current)</option>` +
            avail.drivers.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
        document.getElementById('edit-modal').style.display = 'flex';
    });
}

function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

async function saveEdit() {
    const id = document.getElementById('edit_id').value;
    const driverId = document.getElementById('edit_driver').value;
    if (!driverId) {
        showToast('Please select a driver.', 'error');
        return;
    }
    const resp = await apiPut(`/api/assign-driver/${id}`, { driver_id: parseInt(driverId) });
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
    await apiDel(`/api/assign-driver/${deleteTargetId}`);
    closeDeleteModal();
    window.location.reload();
}
