(async function loadDrivers() {
    const tbody = document.getElementById('drivers-table-body');
    if (!tbody) return;
    const items = await apiGet('/api/drivers') || [];
    const role = document.getElementById('user-role-display').innerText;
    const isAdmin = role === 'Administrator';
    tbody.innerHTML = items.map(i => {
        const actions = isAdmin
            ? `<td><button class="btn btn-sm btn-primary" onclick="openEditModal(${i.id})">Edit</button> <button class="btn btn-sm btn-danger" onclick="deleteDriver(${i.id})">Delete</button></td>`
            : '';
        return `<tr><td>${i.name}</td><td>${i.license_no}</td><td>${i.license_expiry || 'N/A'}</td>${actions}</tr>`;
    }).join('');
})();

async function saveDriver() {
    const name = document.getElementById('d_name').value.trim();
    const lic = document.getElementById('d_lic').value.trim();
    const exp = document.getElementById('d_exp').value;
    if (!name) { showToast('Name is required.', 'error'); return; }
    if (!lic) { showToast('License number is required.', 'error'); return; }
    if (!exp) { showToast('License expiry is required.', 'error'); return; }
    if (new Date(exp) <= new Date(new Date().toDateString())) { showToast('License expiry must be a future date.', 'error'); return; }
    await apiPost('/api/drivers', { name, license_no: lic, license_expiry: exp });
    window.location.reload();
}

function openEditModal(id) {
    apiGet(`/api/drivers/${id}`).then(i => {
        document.getElementById('edit_id').value = i.id;
        document.getElementById('edit_name').value = i.name;
        document.getElementById('edit_lic').value = i.license_no;
        document.getElementById('edit_exp').value = i.license_expiry || '';
        document.getElementById('edit-modal').style.display = 'flex';
    });
}

function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

async function saveEdit() {
    const name = document.getElementById('edit_name').value.trim();
    const lic = document.getElementById('edit_lic').value.trim();
    const exp = document.getElementById('edit_exp').value;
    if (!name) { showToast('Name is required.', 'error'); return; }
    if (!lic) { showToast('License number is required.', 'error'); return; }
    if (!exp) { showToast('License expiry is required.', 'error'); return; }
    if (new Date(exp) <= new Date(new Date().toDateString())) { showToast('License expiry must be a future date.', 'error'); return; }
    const id = document.getElementById('edit_id').value;
    await apiPut(`/api/drivers/${id}`, { name, license_no: lic, license_expiry: exp });
    window.location.reload();
}

let deleteTargetId = null;

function deleteDriver(id) {
    deleteTargetId = id;
    document.getElementById('delete-modal').style.display = 'flex';
}

function closeDeleteModal() {
    deleteTargetId = null;
    document.getElementById('delete-modal').style.display = 'none';
}

async function confirmDelete() {
    if (deleteTargetId === null) return;
    await apiDel(`/api/drivers/${deleteTargetId}`);
    closeDeleteModal();
    window.location.reload();
}
