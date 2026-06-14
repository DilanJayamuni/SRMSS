from init_db import get_db

def _seed_driver(name="John Doe", license_no="LIC-001"):
    db = get_db()
    db.execute("INSERT INTO drivers (name, license_no, license_expiry) VALUES (?,?,?)",
               (name, license_no, "2027-06-01"))
    db.commit()
    did = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return did

def test_list_drivers_empty(client, db):
    resp = client.get('/api/drivers')
    assert resp.status_code == 200
    assert resp.get_json() == []

def test_create_driver(client, db):
    resp = client.post('/api/drivers', json={
        "name": "John Doe", "license_no": "LIC-001", "license_expiry": "2027-06-01"
    })
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_staff_cannot_update_driver(auth_staff, db):
    did = _seed_driver()
    resp = auth_staff.put(f'/api/drivers/{did}', json={"name": "Jane Doe", "license_no": "LIC-002"})
    assert resp.status_code == 403

def test_admin_can_update_driver(auth_admin, db):
    did = _seed_driver()
    resp = auth_admin.put(f'/api/drivers/{did}', json={"name": "Jane Doe", "license_no": "LIC-002"})
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    db_conn = get_db()
    d = db_conn.execute("SELECT * FROM drivers WHERE id=?", (did,)).fetchone()
    db_conn.close()
    assert d["name"] == "Jane Doe"

def test_admin_delete_driver_no_references(auth_admin, db):
    did = _seed_driver()
    resp = auth_admin.delete(f'/api/drivers/{did}')
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    db_conn = get_db()
    d = db_conn.execute("SELECT * FROM drivers WHERE id=?", (did,)).fetchone()
    db_conn.close()
    assert d is None

def test_admin_delete_driver_with_schedule_references(auth_admin, db):
    did = _seed_driver()
    db_conn = get_db()
    db_conn.execute("INSERT INTO vehicles (registration_no, type, seats) VALUES ('V1','Bus',20)")
    db_conn.commit()
    vid = db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_conn.execute("INSERT INTO routes (route_name, start_point, end_point, distance_km) VALUES ('R1','A','B',10)")
    db_conn.commit()
    rid = db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_conn.execute("INSERT INTO schedules (route_id, vehicle_id, driver_id, departure_time, arrival_time) VALUES (?,?,?,?,?)",
                    (rid, vid, did, "2026-06-13 08:00", "2026-06-13 10:00"))
    db_conn.commit()
    db_conn.close()
    resp = auth_admin.delete(f'/api/drivers/{did}')
    assert resp.status_code == 409
    assert "schedule" in resp.get_json()["error"].lower()
