from init_db import get_db

def _seed_route():
    db = get_db()
    db.execute("INSERT INTO routes (route_name, start_point, end_point, distance_km) VALUES ('R1','A','B',10)")
    db.commit()
    rid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return rid

def _seed_vehicle(reg="V1"):
    db = get_db()
    db.execute("INSERT INTO vehicles (registration_no, type, seats) VALUES (?,?,?)", (reg, "Bus", 20))
    db.commit()
    vid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return vid

def _seed_driver(name="D1", lic="L1"):
    db = get_db()
    db.execute("INSERT INTO drivers (name, license_no) VALUES (?,?)", (name, lic))
    db.commit()
    did = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return did

def test_missing_departure_returns_400(client, db):
    rid, vid, did = _seed_route(), _seed_vehicle(), _seed_driver()
    resp = client.post('/api/schedules', json={
        "route_id": rid, "vehicle_id": vid, "driver_id": did
    })
    assert resp.status_code == 400
    assert "departure" in resp.get_json()["error"].lower()

def test_missing_arrival_returns_400(client, db):
    rid, vid, did = _seed_route(), _seed_vehicle(), _seed_driver()
    resp = client.post('/api/schedules', json={
        "route_id": rid, "vehicle_id": vid, "driver_id": did,
        "departure_time": "2026-06-13 08:00"
    })
    assert resp.status_code == 400
    assert "arrival" in resp.get_json()["error"].lower()

def test_arrival_before_departure_returns_400(client, db):
    rid, vid, did = _seed_route(), _seed_vehicle(), _seed_driver()
    resp = client.post('/api/schedules', json={
        "route_id": rid, "vehicle_id": vid, "driver_id": did,
        "departure_time": "2026-06-13 10:00",
        "arrival_time": "2026-06-13 08:00"
    })
    assert resp.status_code == 400
    assert "arrival" in resp.get_json()["error"].lower()

def test_valid_schedule_creation(client, db):
    rid, vid, did = _seed_route(), _seed_vehicle(), _seed_driver()
    resp = client.post('/api/schedules', json={
        "route_id": rid, "vehicle_id": vid, "driver_id": did,
        "departure_time": "2026-06-13 08:00",
        "arrival_time": "2026-06-13 10:00"
    })
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_staff_cannot_update_schedule(auth_staff, db):
    rid, vid, did = _seed_route(), _seed_vehicle(), _seed_driver()
    db_conn = get_db()
    db_conn.execute("INSERT INTO schedules (route_id, vehicle_id, driver_id, departure_time, arrival_time) VALUES (?,?,?,?,?)",
                    (rid, vid, did, "2026-06-13 08:00", "2026-06-13 10:00"))
    db_conn.commit()
    sid = db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_conn.close()
    resp = auth_staff.put(f'/api/schedules/{sid}', json={
        "route_id": rid, "vehicle_id": vid, "driver_id": did,
        "departure_time": "2026-06-13 09:00", "arrival_time": "2026-06-13 11:00"
    })
    assert resp.status_code == 403

def test_staff_cannot_delete_schedule(auth_staff, db):
    rid, vid, did = _seed_route(), _seed_vehicle(), _seed_driver()
    db_conn = get_db()
    db_conn.execute("INSERT INTO schedules (route_id, vehicle_id, driver_id, departure_time, arrival_time) VALUES (?,?,?,?,?)",
                    (rid, vid, did, "2026-06-13 08:00", "2026-06-13 10:00"))
    db_conn.commit()
    sid = db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_conn.close()
    resp = auth_staff.delete(f'/api/schedules/{sid}')
    assert resp.status_code == 403

def test_vehicle_conflict_detected(client, db):
    rid, vid, did = _seed_route(), _seed_vehicle(), _seed_driver()
    db_conn = get_db()
    db_conn.execute("INSERT INTO schedules (route_id, vehicle_id, driver_id, departure_time, arrival_time) VALUES (?,?,?,?,?)",
                    (rid, vid, did, "2026-06-13 08:00", "2026-06-13 10:00"))
    db_conn.commit()
    db_conn.close()
    d2id = _seed_driver("D2", "L2")
    resp = client.post('/api/schedules/check', json={
        "vehicle_id": vid, "driver_id": d2id,
        "departure_time": "2026-06-13 09:00", "arrival_time": "2026-06-13 11:00"
    })
    data = resp.get_json()
    assert data["conflict"] is True
    assert "vehicle" in data["message"].lower()

def test_driver_conflict_detected(client, db):
    rid, vid, did = _seed_route(), _seed_vehicle(), _seed_driver()
    db_conn = get_db()
    db_conn.execute("INSERT INTO schedules (route_id, vehicle_id, driver_id, departure_time, arrival_time) VALUES (?,?,?,?,?)",
                    (rid, vid, did, "2026-06-13 08:00", "2026-06-13 10:00"))
    db_conn.commit()
    db_conn.close()
    v2id = _seed_vehicle("V2")
    resp = client.post('/api/schedules/check', json={
        "vehicle_id": v2id, "driver_id": did,
        "departure_time": "2026-06-13 09:00", "arrival_time": "2026-06-13 11:00"
    })
    data = resp.get_json()
    assert data["conflict"] is True
    assert "driver" in data["message"].lower()

def test_status_update(client, db):
    rid, vid, did = _seed_route(), _seed_vehicle(), _seed_driver()
    db_conn = get_db()
    db_conn.execute("INSERT INTO schedules (route_id, vehicle_id, driver_id, departure_time, arrival_time) VALUES (?,?,?,?,?)",
                    (rid, vid, did, "2026-06-13 08:00", "2026-06-13 10:00"))
    db_conn.commit()
    sid = db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_conn.close()
    resp = client.post(f'/api/operations/status/{sid}', json={"status": "Completed"})
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    db_conn = get_db()
    s = db_conn.execute("SELECT status FROM schedules WHERE id=?", (sid,)).fetchone()
    db_conn.close()
    assert s["status"] == "Completed"
