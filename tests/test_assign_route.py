from init_db import get_db

def _seed_route(name="R1"):
    db = get_db()
    db.execute("INSERT INTO routes (route_name, start_point, end_point, distance_km) VALUES (?,?,?,?)",
               (name, "A", "B", 10))
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

def test_unauthorized_gets_401(client, db):
    r1, v1 = _seed_route(), _seed_vehicle()
    resp = client.post('/api/assign-route', json={"route_id": r1, "vehicle_id": v1})
    assert resp.status_code == 401

def test_assign_to_already_assigned_vehicle(auth_admin, db):
    r1, v1 = _seed_route(), _seed_vehicle()
    db_conn = get_db()
    db_conn.execute("INSERT INTO assignroute (route_id, vehicle_id) VALUES (?,?)", (r1, v1))
    db_conn.commit()
    db_conn.close()
    r2 = _seed_route("R2")
    resp = auth_admin.post('/api/assign-route', json={"route_id": r2, "vehicle_id": v1})
    assert resp.status_code == 409
    assert "vehicle" in resp.get_json()["error"].lower()

def test_successful_route_assignment(auth_admin, db):
    r1, v1 = _seed_route(), _seed_vehicle()
    resp = auth_admin.post('/api/assign-route', json={"route_id": r1, "vehicle_id": v1})
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    db_conn = get_db()
    row = db_conn.execute("SELECT * FROM assignroute WHERE route_id=? AND vehicle_id=?", (r1, v1)).fetchone()
    db_conn.close()
    assert row is not None

def test_staff_cannot_update_route_assignment(auth_staff, db):
    r1, v1 = _seed_route(), _seed_vehicle()
    db_conn = get_db()
    db_conn.execute("INSERT INTO assignroute (route_id, vehicle_id) VALUES (?,?)", (r1, v1))
    db_conn.commit()
    aid = db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_conn.close()
    resp = auth_staff.put(f'/api/assign-route/{aid}', json={"route_id": r1, "vehicle_id": v1})
    assert resp.status_code == 403

def test_staff_cannot_delete_route_assignment(auth_staff, db):
    r1, v1 = _seed_route(), _seed_vehicle()
    db_conn = get_db()
    db_conn.execute("INSERT INTO assignroute (route_id, vehicle_id) VALUES (?,?)", (r1, v1))
    db_conn.commit()
    aid = db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_conn.close()
    resp = auth_staff.delete(f'/api/assign-route/{aid}')
    assert resp.status_code == 403

def test_available_endpoint(auth_admin, db):
    r1, v1 = _seed_route(), _seed_vehicle()
    v2 = _seed_vehicle("V2")
    r2 = _seed_route("R2")
    db_conn = get_db()
    db_conn.execute("INSERT INTO assignroute (route_id, vehicle_id) VALUES (?,?)", (r1, v1))
    db_conn.commit()
    db_conn.close()
    resp = auth_admin.get('/api/assign-route/available')
    assert resp.status_code == 200
    data = resp.get_json()
    vehicle_ids = [v["id"] for v in data["vehicles"]]
    route_ids = [r["id"] for r in data["routes"]]
    assert v1 not in vehicle_ids
    assert v2 in vehicle_ids
    assert r1 in route_ids
    assert r2 in route_ids
