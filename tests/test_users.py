from init_db import get_db

def test_list_users(client, db):
    resp = client.get('/api/users')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 3
    usernames = [u['username'] for u in data]
    assert 'admin' in usernames
    assert 'super' in usernames
    assert 'staff' in usernames

def test_create_user(client, db):
    resp = client.post('/api/users', json={
        "username": "newuser", "password": "pass123", "role": "Operational Staff"
    })
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    db_conn = get_db()
    user = db_conn.execute("SELECT * FROM users WHERE username='newuser'").fetchone()
    db_conn.close()
    assert user is not None
    assert user['role'] == 'Operational Staff'

def test_update_user(client, db):
    resp = client.put('/api/users/1', json={"role": "Supervisor"})
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    db_conn = get_db()
    user = db_conn.execute("SELECT * FROM users WHERE id=1").fetchone()
    db_conn.close()
    assert user['role'] == 'Supervisor'

def test_delete_last_administrator_fails(client, db):
    resp = client.delete('/api/users/1')
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "last Administrator" in data["error"]

def test_delete_user(client, db):
    db_conn = get_db()
    db_conn.execute("INSERT INTO users (username, password, role) VALUES ('todelete','x','Operational Staff')")
    db_conn.commit()
    db_conn.close()
    resp = client.delete('/api/users/4')
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    db_conn = get_db()
    user = db_conn.execute("SELECT * FROM users WHERE id=4").fetchone()
    db_conn.close()
    assert user is None
