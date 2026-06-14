from init_db import get_db

def _seed_route(name="Route A", start="A", end="B", dist=10.5):
    db = get_db()
    db.execute("INSERT INTO routes (route_name, start_point, end_point, distance_km, path_geometry, stops) VALUES (?,?,?,?,?,?)",
               (name, start, end, dist, "", ""))
    db.commit()
    rid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return rid

def test_list_routes(client, db):
    resp = client.get('/api/routes')
    assert resp.status_code == 200

def test_create_route(client, db):
    resp = client.post('/api/routes', json={
        "route_name": "Route A", "start_point": "A", "end_point": "B",
        "distance_km": 10.5, "path_geometry": "", "stops": ""
    })
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_non_admin_cannot_update_route(auth_supervisor, db):
    rid = _seed_route()
    resp = auth_supervisor.put(f'/api/routes/{rid}', json={
        "route_name": "R2", "start_point": "X", "end_point": "Y",
        "distance_km": 20, "path_geometry": "", "stops": ""
    })
    assert resp.status_code == 403

def test_admin_delete_route_no_references(auth_admin, db):
    rid = _seed_route()
    resp = auth_admin.delete(f'/api/routes/{rid}')
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

def test_admin_delete_route_with_schedule_references(auth_admin, db):
    rid = _seed_route()
    db_conn = get_db()
    db_conn.execute("INSERT INTO vehicles (registration_no, type, seats) VALUES ('V1','Bus',20)")
    db_conn.commit()
    vid = db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_conn.execute("INSERT INTO drivers (name, license_no) VALUES ('D1','L1')")
    db_conn.commit()
    did = db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    db_conn.execute("INSERT INTO schedules (route_id, vehicle_id, driver_id, departure_time, arrival_time) VALUES (?,?,?,?,?)",
                    (rid, vid, did, "2026-06-13 08:00", "2026-06-13 10:00"))
    db_conn.commit()
    db_conn.close()
    resp = auth_admin.delete(f'/api/routes/{rid}')
    assert resp.status_code == 409
    assert "schedule" in resp.get_json()["error"].lower()
