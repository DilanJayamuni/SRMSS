(async function loadUsers() {
    const tbody = document.getElementById('users-table-body');
    if (!tbody) return;
    const users = await apiGet('/api/users') || [];
    tbody.innerHTML = users.map(u =>
        `<tr><td>${u.username}</td><td>${u.first_name || ''}</td><td>${u.last_name || ''}</td><td>${u.role}</td>
        <td><button class="btn btn-sm btn-primary" onclick="openEditModal(${u.id})">Edit</button> <button class="btn btn-sm btn-danger" onclick="deleteUser(${u.id})">Delete</button></td></tr>`
    ).join('');
})();

async function createUser() {
    await apiPost('/api/users', {
        username: document.getElementById('u_name').value,
        password: document.getElementById('u_pass').value,
        role: document.getElementById('u_role').value,
        first_name: document.getElementById('u_first_name').value,
        last_name: document.getElementById('u_last_name').value,
        phone_number: document.getElementById('u_phone').value,
        address: document.getElementById('u_address').value
    });
    window.location.reload();
}

async function openEditModal(id) {
    const users = await apiGet('/api/users') || [];
    const u = users.find(user => user.id === id);
    if (!u) return;
    document.getElementById('edit_id').value = u.id;
    document.getElementById('edit_role').value = u.role;
    document.getElementById('edit_first_name').value = u.first_name || '';
    document.getElementById('edit_last_name').value = u.last_name || '';
    document.getElementById('edit_phone').value = u.phone_number || '';
    document.getElementById('edit_address').value = u.address || '';
    document.getElementById('edit-modal').style.display = 'flex';
}

function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

async function saveEdit() {
    const id = document.getElementById('edit_id').value;
    await apiPut(`/api/users/${id}`, {
        role: document.getElementById('edit_role').value,
        first_name: document.getElementById('edit_first_name').value,
        last_name: document.getElementById('edit_last_name').value,
        phone_number: document.getElementById('edit_phone').value,
        address: document.getElementById('edit_address').value
    });
    window.location.reload();
}

async function deleteUser(id) {
    const resp = await apiDel(`/api/users/${id}`);
    const data = await resp.json().catch(() => ({}));
    if (data && data.success === false) {
        showToast(data.error || 'Delete failed', 'error');
    } else {
        window.location.reload();
    }
}
