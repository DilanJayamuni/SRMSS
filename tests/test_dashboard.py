from init_db import get_db

def _seed_data():
    db = get_db()
    db.execute("INSERT INTO vehicles (registration_no, type, seats) VALUES ('V1','Bus',20)")
    db.execute("INSERT INTO vehicles (registration_no, type, seats) VALUES ('V2','Van',10)")
    db.execute("INSERT INTO drivers (name, license_no) VALUES ('D1','L1')")
    db.execute("INSERT INTO routes (route_name, start_point, end_point, distance_km) VALUES ('R1','A','B',10)")
    db.commit()
    db.close()

def test_unauthenticated_redirect_dashboard(client, db):
    resp = client.get('/dashboard')
    assert resp.status_code == 302

def test_stats_without_auth(client, db):
    resp = client.get('/api/stats')
    assert resp.status_code == 200
    data = resp.get_json()
    assert "vehicles" in data
    assert "drivers" in data
    assert "trips" in data

def test_admin_dashboard_unauthorized_401(client, db):
    resp = client.get('/api/dashboard/admin')
    assert resp.status_code == 401

def test_admin_dashboard_supervisor_403(auth_supervisor, db):
    resp = auth_supervisor.get('/api/dashboard/admin')
    assert resp.status_code == 403

def test_admin_dashboard_admin_success(auth_admin, db):
    _seed_data()
    resp = auth_admin.get('/api/dashboard/admin')
    assert resp.status_code == 200
    data = resp.get_json()
    assert "fleet_size" in data
    assert data["fleet_size"] == 2

def test_supervisor_dashboard_unauthorized_401(client, db):
    resp = client.get('/api/dashboard/supervisor')
    assert resp.status_code == 401

def test_supervisor_dashboard_staff_403(auth_staff, db):
    resp = auth_staff.get('/api/dashboard/supervisor')
    assert resp.status_code == 403

def test_staff_dashboard_unauthorized_401(client, db):
    resp = client.get('/api/dashboard/staff')
    assert resp.status_code == 401

def test_staff_dashboard_staff_success(auth_staff, db):
    _seed_data()
    resp = auth_staff.get('/api/dashboard/staff')
    assert resp.status_code == 200
    data = resp.get_json()
    assert "fleet_count" in data

def test_fleet_composition_unauthorized_401(client, db):
    resp = client.get('/api/dashboard/fleet/composition')
    assert resp.status_code == 401

def test_license_expiries_staff_403(auth_staff, db):
    resp = auth_staff.get('/api/dashboard/licenses/expiring')
    assert resp.status_code == 403
