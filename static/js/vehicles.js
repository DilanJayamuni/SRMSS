(async function loadVehicles() {
    const tbody = document.getElementById('vehicles-table-body');
    if (!tbody) return;
    const items = await apiGet('/api/vehicles') || [];
    const role = document.getElementById('user-role-display').innerText;
    const isAdmin = role === 'Administrator';
    tbody.innerHTML = items.map(i => {
        const actions = isAdmin
            ? `<td><button class="btn btn-sm btn-primary" onclick="openEditModal(${i.id})">Edit</button> <button class="btn btn-sm btn-danger" onclick="deleteVehicle(${i.id})">Delete</button></td>`
            : '';
        return `<tr><td>${i.registration_no}</td><td>${i.vehicle_number || ''}</td><td>${i.type}</td><td>${i.seats || 0}</td><td>${i.mileage || 0}</td>${actions}</tr>`;
    }).join('');
})();

async function saveVehicle() {
    const reg = document.getElementById('v_reg').value.trim();
    const type = document.getElementById('v_type').value.trim();
    const seats = document.getElementById('v_seats').value.trim();
    if (!reg) { showToast('Registration number is required.', 'error'); return; }
    if (!type) { showToast('Vehicle type is required.', 'error'); return; }
    if (!seats || parseInt(seats) < 1) { showToast('Number of seats must be at least 1.', 'error'); return; }
    await apiPost('/api/vehicles', {
        registration_no: reg,
        vehicle_number: document.getElementById('v_vehicle_no').value.trim(),
        type: type,
        seats: seats,
        mileage: document.getElementById('v_mile').value.trim() || 0
    });
    window.location.reload();
}

function openEditModal(id) {
    apiGet(`/api/vehicles/${id}`).then(i => {
        document.getElementById('edit_id').value = i.id;
        document.getElementById('edit_reg').value = i.registration_no;
        document.getElementById('edit_vehicle_no').value = i.vehicle_number || '';
        document.getElementById('edit_type').value = i.type;
        document.getElementById('edit_seats').value = i.seats || 0;
        document.getElementById('edit_mile').value = i.mileage || 0;
        document.getElementById('edit-modal').style.display = 'flex';
    });
}

function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

async function saveEdit() {
    const reg = document.getElementById('edit_reg').value.trim();
    const type = document.getElementById('edit_type').value.trim();
    const seats = document.getElementById('edit_seats').value.trim();
    if (!reg) { showToast('Registration number is required.', 'error'); return; }
    if (!type) { showToast('Vehicle type is required.', 'error'); return; }
    if (!seats || parseInt(seats) < 1) { showToast('Number of seats must be at least 1.', 'error'); return; }
    const id = document.getElementById('edit_id').value;
    await apiPut(`/api/vehicles/${id}`, {
        registration_no: reg,
        vehicle_number: document.getElementById('edit_vehicle_no').value.trim(),
        type: type,
        seats: seats,
        mileage: document.getElementById('edit_mile').value.trim() || 0
    });
    window.location.reload();
}

let deleteTargetId = null;

function deleteVehicle(id) {
    deleteTargetId = id;
    document.getElementById('delete-modal').style.display = 'flex';
}

function closeDeleteModal() {
    deleteTargetId = null;
    document.getElementById('delete-modal').style.display = 'none';
}

async function confirmDelete() {
    if (deleteTargetId === null) return;
    await apiDel(`/api/vehicles/${deleteTargetId}`);
    closeDeleteModal();
    window.location.reload();
}
