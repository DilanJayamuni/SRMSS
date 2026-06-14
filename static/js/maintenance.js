async function loadMaintenance() {
    const tbody = document.getElementById('maintenance-table-body');
    const vehSel = document.getElementById('m_veh');
    const filterVeh = document.getElementById('filter_veh');
    if (!tbody) return;

    const params = new URLSearchParams();
    const dateFrom = document.getElementById('filter_date_from');
    const dateTo = document.getElementById('filter_date_to');
    if (dateFrom && dateFrom.value) params.append('date_from', dateFrom.value);
    if (dateTo && dateTo.value) params.append('date_to', dateTo.value);
    if (filterVeh && filterVeh.value) params.append('vehicle_id', filterVeh.value);
    const qs = params.toString();
    const url = '/api/maintenance' + (qs ? '?' + qs : '');

    const [items, vehicles] = await Promise.all([
        apiGet(url),
        apiGet('/api/vehicles')
    ]);

    const opts = vehicles ? vehicles.map(v => `<option value="${v.id}">${v.registration_no}</option>`).join('') : '';
    if (vehSel) vehSel.innerHTML = opts;
    if (filterVeh) {
        const cur = filterVeh.value;
        filterVeh.innerHTML = '<option value="">All Vehicles</option>' + opts;
        filterVeh.value = cur || '';
    }

    if (items) {
        const role = document.getElementById('user-role-display').innerText;
        let total = 0;
        tbody.innerHTML = items.map(l => {
            total += Number(l.cost) || 0;
            const canEdit = role === 'Administrator' || l.status === 'Pending';
            const actions = canEdit
                ? `<td><button class="btn btn-sm btn-primary" onclick="openEditModal(${l.id})">Edit</button> <button class="btn btn-sm btn-danger" onclick="deleteMaint(${l.id})">Delete</button></td>`
                : `<td>-</td>`;
            return `<tr><td>${l.date || '-'}</td><td>${l.registration_no}</td><td>${l.description || '-'}</td><td>${l.mileage != null ? l.mileage + ' km' : '-'}</td><td>Rs.${l.cost}</td><td><span class="badge ${l.status === 'Approved' ? 'badge-green' : l.status === 'Rejected' ? 'badge-red' : 'badge-yellow'}">${l.status}</span></td>${actions}</tr>`;
        }).join('');
        document.getElementById('maintenance-total-cost').textContent = total;
    }
}

async function saveMaint() {
    await apiPost('/api/maintenance', {
        vehicle_id: document.getElementById('m_veh').value,
        date: document.getElementById('m_date').value,
        mileage: document.getElementById('m_mile').value || null,
        description: document.getElementById('m_desc').value,
        cost: document.getElementById('m_cost').value
    });
    window.location.reload();
}

function applyFilters() {
    loadMaintenance();
}

function resetFilters() {
    document.getElementById('filter_date_from').value = '';
    document.getElementById('filter_date_to').value = '';
    document.getElementById('filter_veh').value = '';
    loadMaintenance();
}

function openEditModal(id) {
    apiGet(`/api/maintenance/${id}`).then(l => {
        const editVeh = document.getElementById('edit_veh');
        apiGet('/api/vehicles').then(vehicles => {
            if (vehicles) {
                editVeh.innerHTML = vehicles.map(v =>
                    `<option value="${v.id}" ${v.id === l.vehicle_id ? 'selected' : ''}>${v.registration_no}</option>`
                ).join('');
            }
        });
        document.getElementById('edit_id').value = l.id;
        document.getElementById('edit_date').value = l.date || '';
        document.getElementById('edit_mile').value = l.mileage || '';
        document.getElementById('edit_desc').value = l.description || '';
        document.getElementById('edit_cost').value = l.cost;
        document.getElementById('edit-modal').style.display = 'flex';
    });
}

function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

async function saveEdit() {
    const id = document.getElementById('edit_id').value;
    await apiPut(`/api/maintenance/${id}`, {
        vehicle_id: document.getElementById('edit_veh').value,
        date: document.getElementById('edit_date').value,
        mileage: document.getElementById('edit_mile').value || null,
        description: document.getElementById('edit_desc').value,
        cost: document.getElementById('edit_cost').value
    });
    closeEditModal();
    window.location.reload();
}

let deleteTargetId = null;

function deleteMaint(id) {
    deleteTargetId = id;
    document.getElementById('delete-modal').style.display = 'flex';
}

function closeDeleteModal() {
    deleteTargetId = null;
    document.getElementById('delete-modal').style.display = 'none';
}

async function confirmDelete() {
    if (deleteTargetId === null) return;
    await apiDel(`/api/maintenance/${deleteTargetId}`);
    closeDeleteModal();
    window.location.reload();
}

loadMaintenance();
