(async function loadUsers() {
    const tbody = document.getElementById('users-table-body');
    if (!tbody) return;
    const users = await apiGet('/api/users') || [];
    tbody.innerHTML = users.map(u =>
        `<tr><td>${u.username}</td><td>${u.role}</td>
        <td><select id="role-${u.id}" onchange="updateRole(${u.id})">
            <option ${u.role === 'Operational Staff' ? 'selected' : ''}>Operational Staff</option>
            <option ${u.role === 'Supervisor' ? 'selected' : ''}>Supervisor</option>
            <option ${u.role === 'Administrator' ? 'selected' : ''}>Administrator</option>
        </select></td>
        <td><span class="action-link" onclick="deleteUser(${u.id})">Delete</span></td></tr>`
    ).join('');
})();

async function createUser() {
    await apiPost('/api/users', {
        username: document.getElementById('u_name').value,
        password: document.getElementById('u_pass').value,
        role: document.getElementById('u_role').value
    });
    window.location.reload();
}

async function updateRole(id) {
    await apiPut(`/api/users/${id}`, { role: document.getElementById(`role-${id}`).value });
}

async function deleteUser(id) {
    await apiDel(`/api/users/${id}`);
    window.location.reload();
}
