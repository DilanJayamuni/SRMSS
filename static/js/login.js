async function attemptLogin() {
    const user = document.getElementById('login_user').value;
    const pass = document.getElementById('login_pass').value;
    const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, password: pass })
    });
    const data = await res.json();
    if (data.success) {
        window.location.href = '/dashboard';
    } else {
        alert("Login Failed");
    }
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') attemptLogin();
});
