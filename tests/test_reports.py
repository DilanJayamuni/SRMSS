from init_db import get_db

def _seed_data():
    db = get_db()
    db.execute("INSERT INTO vehicles (registration_no, type, seats) VALUES ('V1','Bus',20)")
    db.commit()
    vid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute("INSERT INTO drivers (name, license_no) VALUES ('D1','L1')")
    db.commit()
    did = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute("INSERT INTO routes (route_name, start_point, end_point, distance_km) VALUES ('R1','A','B',10)")
    db.commit()
    rid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute("INSERT INTO fuel_logs (vehicle_id, date, liters, cost, status) VALUES (?,?,?,?,?)",
               (vid, "2026-06-13", 50, 100.0, "Approved"))
    db.execute("INSERT INTO fuel_logs (vehicle_id, date, liters, cost, status) VALUES (?,?,?,?,?)",
               (vid, "2026-06-13", 30, 60.0, "Pending"))
    db.execute("INSERT INTO maintenance_logs (vehicle_id, description, cost, date, status) VALUES (?,?,?,?,?)",
               (vid, "Repair", 200.0, "2026-06-13", "Approved"))
    db.execute("INSERT INTO schedules (route_id, vehicle_id, driver_id, departure_time, arrival_time, status) VALUES (?,?,?,?,?,?)",
               (rid, vid, did, "2026-06-13 08:00", "2026-06-13 10:00", "Completed"))
    db.execute("INSERT INTO schedules (route_id, vehicle_id, driver_id, departure_time, arrival_time, status) VALUES (?,?,?,?,?,?)",
               (rid, vid, did, "2026-06-13 12:00", "2026-06-13 14:00", "Scheduled"))
    db.commit()
    db.close()

def test_staff_gets_403_summary_report(auth_staff, db):
    _seed_data()
    resp = auth_staff.get('/api/reports/summary')
    assert resp.status_code == 403

def test_admin_can_access_summary_report(auth_admin, db):
    _seed_data()
    resp = auth_admin.get('/api/reports/summary')
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total_fuel_cost" in data
    assert data["total_trips"] == 2

def test_supervisor_gets_403_fuel_report(auth_supervisor, db):
    _seed_data()
    resp = auth_supervisor.get('/api/reports/fuel')
    assert resp.status_code == 403

def test_staff_gets_403_trips_report(auth_staff, db):
    _seed_data()
    resp = auth_staff.get('/api/reports/trips')
    assert resp.status_code == 403

def test_admin_can_access_trips_report(auth_admin, db):
    _seed_data()
    resp = auth_admin.get('/api/reports/trips')
    assert resp.status_code == 200
    data = resp.get_json()
    assert "by_status" in data
    assert "by_month" in data

def test_staff_gets_403_fleet_report(auth_staff, db):
    _seed_data()
    resp = auth_staff.get('/api/reports/fleet')
    assert resp.status_code == 403

def test_staff_gets_403_drivers_report(auth_staff, db):
    _seed_data()
    resp = auth_staff.get('/api/reports/drivers')
    assert resp.status_code == 403

def test_summary_with_date_range(auth_admin, db):
    _seed_data()
    resp = auth_admin.get('/api/reports/summary?date_from=2026-01-01&date_to=2026-12-31')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total_fuel_cost"] == 100.0

def test_csv_export_requires_admin(auth_supervisor, db):
    _seed_data()
    resp = auth_supervisor.get('/api/reports/export/summary')
    assert resp.status_code == 403

def test_unknown_export_returns_404(auth_admin, db):
    _seed_data()
    resp = auth_admin.get('/api/reports/export/invalid_report')
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Unknown report"
