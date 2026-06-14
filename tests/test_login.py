from init_db import get_db

def test_login_success(client, db):
    resp = client.post('/api/login', json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "Administrator"

def test_login_failure_wrong_password(client, db):
    resp = client.post('/api/login', json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["success"] is False

def test_root_redirects_when_logged_in(auth_admin, db):
    resp = auth_admin.get('/')
    assert resp.status_code == 302
    assert '/dashboard' in resp.location

def test_root_shows_login_when_unauthenticated(client, db):
    resp = client.get('/')
    assert resp.status_code == 200

def test_logout_clears_session(client, db):
    with client.session_transaction() as sess:
        sess['user'] = {"id": 1, "username": "admin", "role": "Administrator"}
    resp = client.get('/logout')
    assert resp.status_code == 302
    assert resp.location == '/' or resp.location.endswith('/')
    with client.session_transaction() as sess:
        assert 'user' not in sess
