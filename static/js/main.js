const API = '/api';

function initTheme() {
    const t = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', t);
    const btn = document.querySelector('.theme-switch');
    if (btn) btn.innerText = t === 'dark' ? '☀️' : '🌙';
}
function toggleTheme() {
    const c = document.documentElement.getAttribute('data-theme');
    const n = c === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', n);
    localStorage.setItem('theme', n);
    document.querySelector('.theme-switch').innerText = n === 'dark' ? '☀️' : '🌙';
}
initTheme();

async function apiGet(endpoint) {
    try {
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (e) {
        console.error("API Error:", e);
        return null;
    }
}
async function apiPost(endpoint, data) {
    return await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
}
async function apiPut(endpoint, data) {
    return await fetch(endpoint, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
}
async function apiDel(endpoint) {
    return await fetch(endpoint, { method: 'DELETE' });
}

function showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = 'toast toast-' + (type || 'error');
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(function() { toast.classList.add('toast-show'); }, 10);
    setTimeout(function() {
        toast.classList.remove('toast-show');
        setTimeout(function() { toast.remove(); }, 300);
    }, 3500);
    toast.addEventListener('click', function() {
        toast.classList.remove('toast-show');
        setTimeout(function() { toast.remove(); }, 300);
    });
}
