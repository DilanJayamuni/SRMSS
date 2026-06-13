(async function loadApprovals() {
    const tbody = document.getElementById('approvals-table-body');
    if (!tbody) return;
    const [fuelPending, maintPending] = await Promise.all([
        apiGet('/api/fuel/pending') || [],
        apiGet('/api/maintenance/pending') || []
    ]);
    const fuelRows = (fuelPending || []).map(p =>
        `<tr><td>${p.registration_no}</td><td>Fuel</td><td>${p.date || '-'}</td><td>${p.mileage != null ? p.mileage + ' km' : '-'}</td><td>-</td><td><button class="btn btn-success btn-sm" onclick="approveFuel(${p.id})">Approve</button> <button class="btn btn-danger btn-sm" onclick="rejectFuel(${p.id})">Reject</button></td></tr>`
    );
    const maintRows = (maintPending || []).map(p =>
        `<tr><td>${p.registration_no}</td><td>Maintenance</td><td>${p.date || '-'}</td><td>${p.mileage != null ? p.mileage + ' km' : '-'}</td><td>${p.description || '-'}</td><td><button class="btn btn-success btn-sm" onclick="approveMaintenance(${p.id})">Approve</button> <button class="btn btn-danger btn-sm" onclick="rejectMaintenance(${p.id})">Reject</button></td></tr>`
    );
    tbody.innerHTML = fuelRows.concat(maintRows).join('');
})();

async function approveFuel(id) {
    await apiPost(`/api/fuel/approve/${id}`, {});
    window.location.reload();
}

async function rejectFuel(id) {
    await apiPost(`/api/fuel/reject/${id}`, {});
    window.location.reload();
}

async function approveMaintenance(id) {
    await apiPost(`/api/maintenance/approve/${id}`, {});
    window.location.reload();
}

async function rejectMaintenance(id) {
    await apiPost(`/api/maintenance/reject/${id}`, {});
    window.location.reload();
}
