async function attemptLogin() {
    const user = document.getElementById('login_user');
    const pass = document.getElementById('login_pass');
    const btn = document.getElementById('loginBtn');
    const btnText = document.getElementById('loginBtnText');
    const btnLoader = document.getElementById('loginBtnLoader');
    const errorEl = document.getElementById('loginError');
    const card = document.getElementById('loginCard');

    clearError();

    btn.disabled = true;
    btnText.classList.add('hidden');
    btnLoader.classList.remove('hidden');

    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user.value, password: pass.value })
        });
        const data = await res.json();
        if (data.success) {
            window.location.href = '/dashboard';
        } else {
            showError('Invalid username or password');
        }
    } catch (e) {
        showError('Connection error. Please try again.');
    } finally {
        btn.disabled = false;
        btnText.classList.remove('hidden');
        btnLoader.classList.add('hidden');
    }
}

function showError(msg) {
    const errorEl = document.getElementById('loginError');
    const errorText = document.getElementById('loginErrorText');
    const card = document.getElementById('loginCard');
    const user = document.getElementById('login_user');
    const pass = document.getElementById('login_pass');

    errorText.textContent = msg;
    errorEl.classList.add('show');
    user.classList.add('input-error');
    pass.classList.add('input-error');

    card.classList.remove('shake');
    void card.offsetWidth;
    card.classList.add('shake');
}

function clearError() {
    const errorEl = document.getElementById('loginError');
    const user = document.getElementById('login_user');
    const pass = document.getElementById('login_pass');
    const card = document.getElementById('loginCard');

    errorEl.classList.remove('show');
    user.classList.remove('input-error');
    pass.classList.remove('input-error');
    card.classList.remove('shake');
}

document.getElementById('login_user').addEventListener('input', clearError);
document.getElementById('login_pass').addEventListener('input', clearError);

document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') attemptLogin();
});
