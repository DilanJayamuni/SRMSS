from init_db import get_db

def _seed_vehicle(reg="V1"):
    db = get_db()
    db.execute("INSERT INTO vehicles (registration_no, type, seats) VALUES (?,?,?)", (reg, "Bus", 20))
    db.commit()
    vid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return vid

def _seed_maintenance(vid, status="Pending"):
    db = get_db()
    db.execute("INSERT INTO maintenance_logs (vehicle_id, description, cost, date, status) VALUES (?,?,?,?,?)",
               (vid, "Oil change", 150.0, "2026-06-13", status))
    db.commit()
    mid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return mid

def test_create_pending_maintenance_log(client, db):
    vid = _seed_vehicle()
    resp = client.post('/api/maintenance', json={
        "vehicle_id": vid, "description": "Oil change", "cost": 150.0, "date": "2026-06-13"
    })
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    db_conn = get_db()
    log = db_conn.execute("SELECT * FROM maintenance_logs WHERE vehicle_id=?", (vid,)).fetchone()
    db_conn.close()
    assert log is not None
    assert log["status"] == "Pending"

def test_list_maintenance_with_vehicle_filter(client, db):
    vid = _seed_vehicle()
    _seed_maintenance(vid)
    resp = client.get(f'/api/maintenance?vehicle_id={vid}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_maintenance_detail_unauthorized_401(client, db):
    vid = _seed_vehicle()
    mid = _seed_maintenance(vid)
    resp = client.get(f'/api/maintenance/{mid}')
    assert resp.status_code == 401

def test_admin_can_update_approved_log(auth_admin, db):
    vid = _seed_vehicle()
    mid = _seed_maintenance(vid, status="Approved")
    resp = auth_admin.put(f'/api/maintenance/{mid}', json={
        "vehicle_id": vid, "description": "Brake fix", "cost": 200.0, "date": "2026-06-14"
    })
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_staff_cannot_update_approved_log(auth_staff, db):
    vid = _seed_vehicle()
    mid = _seed_maintenance(vid, status="Approved")
    resp = auth_staff.put(f'/api/maintenance/{mid}', json={
        "vehicle_id": vid, "description": "Brake fix", "cost": 200.0, "date": "2026-06-14"
    })
    assert resp.status_code == 403

def test_approve_maintenance_log(client, db):
    vid = _seed_vehicle()
    mid = _seed_maintenance(vid)
    resp = client.post(f'/api/maintenance/approve/{mid}')
    assert resp.status_code == 200
    db_conn = get_db()
    log = db_conn.execute("SELECT status FROM maintenance_logs WHERE id=?", (mid,)).fetchone()
    db_conn.close()
    assert log["status"] == "Approved"

def test_reject_maintenance_log(client, db):
    vid = _seed_vehicle()
    mid = _seed_maintenance(vid)
    resp = client.post(f'/api/maintenance/reject/{mid}')
    assert resp.status_code == 200
    db_conn = get_db()
    log = db_conn.execute("SELECT status FROM maintenance_logs WHERE id=?", (mid,)).fetchone()
    db_conn.close()
    assert log["status"] == "Rejected"
