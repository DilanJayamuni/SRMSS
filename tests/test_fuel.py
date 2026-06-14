from init_db import get_db

def _seed_vehicle(reg="V1"):
    db = get_db()
    db.execute("INSERT INTO vehicles (registration_no, type, seats) VALUES (?,?,?)", (reg, "Bus", 20))
    db.commit()
    vid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return vid

def _seed_fuel(vid, status="Pending"):
    db = get_db()
    db.execute("INSERT INTO fuel_logs (vehicle_id, date, liters, cost, status) VALUES (?,?,?,?,?)",
               (vid, "2026-06-13", 50, 100.0, status))
    db.commit()
    fid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return fid

def test_create_pending_fuel_log(client, db):
    vid = _seed_vehicle()
    resp = client.post('/api/fuel', json={
        "vehicle_id": vid, "date": "2026-06-13", "liters": 50, "cost": 100.0
    })
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    db_conn = get_db()
    log = db_conn.execute("SELECT * FROM fuel_logs WHERE vehicle_id=?", (vid,)).fetchone()
    db_conn.close()
    assert log is not None
    assert log["status"] == "Pending"

def test_list_fuel_with_date_filter(client, db):
    vid = _seed_vehicle()
    _seed_fuel(vid)
    resp = client.get('/api/fuel?date_from=2026-01-01&date_to=2026-12-31')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_fuel_detail_unauthorized_401(client, db):
    vid = _seed_vehicle()
    fid = _seed_fuel(vid)
    resp = client.get(f'/api/fuel/{fid}')
    assert resp.status_code == 401

def test_staff_can_update_pending_log(auth_staff, db):
    vid = _seed_vehicle()
    fid = _seed_fuel(vid)
    resp = auth_staff.put(f'/api/fuel/{fid}', json={
        "vehicle_id": vid, "date": "2026-06-14", "liters": 60, "cost": 120.0
    })
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_staff_cannot_update_approved_log(auth_staff, db):
    vid = _seed_vehicle()
    fid = _seed_fuel(vid, status="Approved")
    resp = auth_staff.put(f'/api/fuel/{fid}', json={
        "vehicle_id": vid, "date": "2026-06-14", "liters": 60, "cost": 120.0
    })
    assert resp.status_code == 403

def test_staff_can_delete_pending_log(auth_staff, db):
    vid = _seed_vehicle()
    fid = _seed_fuel(vid)
    resp = auth_staff.delete(f'/api/fuel/{fid}')
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_approve_fuel_log(client, db):
    vid = _seed_vehicle()
    fid = _seed_fuel(vid)
    resp = client.post(f'/api/fuel/approve/{fid}')
    assert resp.status_code == 200
    db_conn = get_db()
    log = db_conn.execute("SELECT status FROM fuel_logs WHERE id=?", (fid,)).fetchone()
    db_conn.close()
    assert log["status"] == "Approved"

def test_reject_fuel_log(client, db):
    vid = _seed_vehicle()
    fid = _seed_fuel(vid)
    resp = client.post(f'/api/fuel/reject/{fid}')
    assert resp.status_code == 200
    db_conn = get_db()
    log = db_conn.execute("SELECT status FROM fuel_logs WHERE id=?", (fid,)).fetchone()
    db_conn.close()
    assert log["status"] == "Rejected"
