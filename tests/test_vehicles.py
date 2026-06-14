from init_db import get_db

def _seed_vehicle(reg="ABC-123"):
    db = get_db()
    db.execute("INSERT INTO vehicles (registration_no, type, seats, mileage, vehicle_number) VALUES (?,?,?,?,?)",
               (reg, "Bus", 40, 1000, ""))
    db.commit()
    vid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return vid

def test_list_vehicles_empty(client, db):
    resp = client.get('/api/vehicles')
    assert resp.status_code == 200
    assert resp.get_json() == []

def test_create_vehicle(client, db):
    resp = client.post('/api/vehicles', json={
        "registration_no": "ABC-123", "type": "Bus", "seats": 40
    })
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_get_vehicle_detail(client, db):
    vid = _seed_vehicle()
    resp = client.get(f'/api/vehicles/{vid}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["registration_no"] == "ABC-123"
    assert data["type"] == "Bus"

def test_staff_cannot_update_vehicle(auth_staff, db):
    vid = _seed_vehicle()
    resp = auth_staff.put(f'/api/vehicles/{vid}', json={
        "registration_no": "XYZ-999", "type": "Van", "seats": 10
    })
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "Forbidden"

def test_admin_can_update_vehicle(auth_admin, db):
    vid = _seed_vehicle()
    resp = auth_admin.put(f'/api/vehicles/{vid}', json={
        "registration_no": "XYZ-999", "type": "Van", "seats": 10
    })
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    db_conn = get_db()
    v = db_conn.execute("SELECT * FROM vehicles WHERE id=?", (vid,)).fetchone()
    db_conn.close()
    assert v["registration_no"] == "XYZ-999"

def test_staff_cannot_delete_vehicle(auth_staff, db):
    vid = _seed_vehicle()
    resp = auth_staff.delete(f'/api/vehicles/{vid}')
    assert resp.status_code == 403

def test_admin_can_delete_vehicle(auth_admin, db):
    vid = _seed_vehicle()
    resp = auth_admin.delete(f'/api/vehicles/{vid}')
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    db_conn = get_db()
    v = db_conn.execute("SELECT * FROM vehicles WHERE id=?", (vid,)).fetchone()
    db_conn.close()
    assert v is None
