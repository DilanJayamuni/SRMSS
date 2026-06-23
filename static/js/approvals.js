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

    const pbody = document.getElementById('proposals-table-body');
    if (pbody) {
        const proposals = await apiGet('/api/schedule-proposals?status=Pending') || [];
        if (proposals.length === 0) {
            pbody.innerHTML = '<tr><td colspan="8" style="text-align:center; opacity:0.7;">No pending schedule proposals.</td></tr>';
        } else {
            pbody.innerHTML = proposals.map(p => {
                const date = p.proposed_date || p.departure_time ? p.departure_time.substring(0, 10) : '-';
                const dep = p.departure_time ? p.departure_time.substring(11, 16) : '-';
                const arr = p.arrival_time ? p.arrival_time.substring(11, 16) : '-';
                return `<tr>
                    <td>${p.driver_name}</td><td>${p.vehicle_reg}</td><td>${p.route_name}</td>
                    <td>${date}</td><td>${dep}</td><td>${arr}</td>
                    <td>${p.recurrence}</td>
                    <td><button class="btn btn-success btn-sm" onclick="approveProposal(${p.id})">Approve</button> <button class="btn btn-danger btn-sm" onclick="rejectProposal(${p.id})">Reject</button></td>
                </tr>`;
            }).join('');
        }
    }
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

async function approveProposal(id) {
    await apiPost(`/api/schedule-proposals/${id}/approve`, {});
    window.location.reload();
}

async function rejectProposal(id) {
    await apiPost(`/api/schedule-proposals/${id}/reject`, {});
    window.location.reload();
}
