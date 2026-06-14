from init_db import get_db

def _seed_driver(name="D1", lic="L1"):
    db = get_db()
    db.execute("INSERT INTO drivers (name, license_no) VALUES (?,?)", (name, lic))
    db.commit()
    did = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return did

def _seed_vehicle(reg="V1"):
    db = get_db()
    db.execute("INSERT INTO vehicles (registration_no, type, seats) VALUES (?,?,?)", (reg, "Bus", 20))
    db.commit()
    vid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return vid

def test_unauthorized_gets_401(client, db):
    d1, v1 = _seed_driver(), _seed_vehicle()
    resp = client.post('/api/assign-driver', json={"driver_id": d1, "vehicle_id": v1})
    assert resp.status_code == 401

def test_assign_already_assigned_driver(auth_admin, db):
    d1, v1 = _seed_driver(), _seed_vehicle()
    v2 = _seed_vehicle("V2")
    db_conn = get_db()
    db_conn.execute("INSERT INTO assigndriver (driver_id, vehicle_id) VALUES (?,?)", (d1, v1))
    db_conn.commit()
    db_conn.close()
    resp = auth_admin.post('/api/assign-driver', json={"driver_id": d1, "vehicle_id": v2})
    assert resp.status_code == 409
    assert "driver" in resp.get_json()["error"].lower()

def test_assign_to_already_assigned_vehicle(auth_admin, db):
    d1, v1 = _seed_driver(), _seed_vehicle()
    d2 = _seed_driver("D2", "L2")
    db_conn = get_db()
    db_conn.execute("INSERT INTO assigndriver (driver_id, vehicle_id) VALUES (?,?)", (d1, v1))
    db_conn.commit()
    db_conn.close()
    resp = auth_admin.post('/api/assign-driver', json={"driver_id": d2, "vehicle_id": v1})
    assert resp.status_code == 409
    assert "vehicle" in resp.get_json()["error"].lower()

def test_successful_assignment(auth_admin, db):
    d1, v1 = _seed_driver(), _seed_vehicle()
    resp = auth_admin.post('/api/assign-driver', json={"driver_id": d1, "vehicle_id": v1})
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    db_conn = get_db()
    row = db_conn.execute("SELECT * FROM assigndriver WHERE driver_id=? AND vehicle_id=?", (d1, v1)).fetchone()
    db_conn.close()
    assert row is not None

def test_staff_cannot_update_assignment(auth_staff, db):
    d1, v1 = _seed_driver(), _seed_vehicle()
    db_conn = get_db()
    db_conn.execute("INSERT INTO assigndriver (driver_id, vehicle_id) VALUES (?,?)", (d1, v1))
    db_conn.commit()
    aid = db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_conn.close()
    resp = auth_staff.put(f'/api/assign-driver/{aid}', json={"driver_id": d1, "vehicle_id": v1})
    assert resp.status_code == 403

def test_staff_cannot_delete_assignment(auth_staff, db):
    d1, v1 = _seed_driver(), _seed_vehicle()
    db_conn = get_db()
    db_conn.execute("INSERT INTO assigndriver (driver_id, vehicle_id) VALUES (?,?)", (d1, v1))
    db_conn.commit()
    aid = db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_conn.close()
    resp = auth_staff.delete(f'/api/assign-driver/{aid}')
    assert resp.status_code == 403

def test_available_endpoint(auth_admin, db):
    d1, v1 = _seed_driver(), _seed_vehicle()
    d2 = _seed_driver("D2", "L2")
    v2 = _seed_vehicle("V2")
    db_conn = get_db()
    db_conn.execute("INSERT INTO assigndriver (driver_id, vehicle_id) VALUES (?,?)", (d1, v1))
    db_conn.commit()
    db_conn.close()
    resp = auth_admin.get('/api/assign-driver/available')
    assert resp.status_code == 200
    data = resp.get_json()
    driver_ids = [d["id"] for d in data["drivers"]]
    vehicle_ids = [v["id"] for v in data["vehicles"]]
    assert d1 not in driver_ids
    assert d2 in driver_ids
    assert v1 not in vehicle_ids
    assert v2 in vehicle_ids
