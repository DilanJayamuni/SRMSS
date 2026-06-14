async function loadFuel() {
    const tbody = document.getElementById('fuel-table-body');
    const vehSel = document.getElementById('f_veh');
    const filterVeh = document.getElementById('filter_veh');
    if (!tbody) return;

    const params = new URLSearchParams();
    const dateFrom = document.getElementById('filter_date_from');
    const dateTo = document.getElementById('filter_date_to');
    if (dateFrom && dateFrom.value) params.append('date_from', dateFrom.value);
    if (dateTo && dateTo.value) params.append('date_to', dateTo.value);
    if (filterVeh && filterVeh.value) params.append('vehicle_id', filterVeh.value);
    const qs = params.toString();
    const url = '/api/fuel' + (qs ? '?' + qs : '');

    const [logs, vehicles] = await Promise.all([
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

    if (logs) {
        const role = document.getElementById('user-role-display').innerText;
        let total = 0;
        tbody.innerHTML = logs.map(l => {
            total += Number(l.cost) || 0;
            const canEdit = role === 'Administrator' || l.status === 'Pending';
            const actions = canEdit
                ? `<td><button class="btn btn-sm btn-primary" onclick="openEditModal(${l.id})">Edit</button> <button class="btn btn-sm btn-danger" onclick="deleteFuel(${l.id})">Delete</button></td>`
                : `<td>-</td>`;
            return `<tr><td>${l.date || '-'}</td><td>${l.registration_no}</td><td>${l.mileage != null ? l.mileage + ' km' : '-'}</td><td>${l.liters}L</td><td>Rs.${l.cost}</td><td><span class="badge ${l.status === 'Approved' ? 'badge-green' : l.status === 'Rejected' ? 'badge-red' : 'badge-yellow'}">${l.status}</span></td>${actions}</tr>`;
        }).join('');
        document.getElementById('fuel-total-cost').textContent = total;
    }
}

async function saveFuel() {
    await apiPost('/api/fuel', {
        vehicle_id: document.getElementById('f_veh').value,
        date: document.getElementById('f_date').value,
        liters: document.getElementById('f_lit').value,
        cost: document.getElementById('f_cost').value,
        mileage: document.getElementById('f_mile').value || null
    });
    window.location.reload();
}

function applyFilters() {
    loadFuel();
}

function resetFilters() {
    document.getElementById('filter_date_from').value = '';
    document.getElementById('filter_date_to').value = '';
    document.getElementById('filter_veh').value = '';
    loadFuel();
}

function openEditModal(id) {
    apiGet(`/api/fuel/${id}`).then(l => {
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
        document.getElementById('edit_lit').value = l.liters;
        document.getElementById('edit_cost').value = l.cost;
        document.getElementById('edit-modal').style.display = 'flex';
    });
}

function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

async function saveEdit() {
    const id = document.getElementById('edit_id').value;
    await apiPut(`/api/fuel/${id}`, {
        vehicle_id: document.getElementById('edit_veh').value,
        date: document.getElementById('edit_date').value,
        liters: document.getElementById('edit_lit').value,
        cost: document.getElementById('edit_cost').value,
        mileage: document.getElementById('edit_mile').value || null
    });
    closeEditModal();
    window.location.reload();
}

let deleteTargetId = null;

function deleteFuel(id) {
    deleteTargetId = id;
    document.getElementById('delete-modal').style.display = 'flex';
}

function closeDeleteModal() {
    deleteTargetId = null;
    document.getElementById('delete-modal').style.display = 'none';
}

async function confirmDelete() {
    if (deleteTargetId === null) return;
    await apiDel(`/api/fuel/${deleteTargetId}`);
    closeDeleteModal();
    window.location.reload();
}

loadFuel();
