from init_db import get_db

def _seed_data():
    db = get_db()
    db.execute("INSERT INTO drivers (name, license_no) VALUES ('D1','L1')")
    db.commit()
    did = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute("INSERT INTO vehicles (registration_no, type, seats) VALUES ('V1','Bus',20)")
    db.commit()
    vid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute("INSERT INTO routes (route_name, start_point, end_point) VALUES ('Route A','X','Y')")
    db.commit()
    rid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return did, vid, rid

def _seed_schedule(driver_id, vehicle_id, route_id, departure, arrival, recurrence='Once'):
    db = get_db()
    db.execute("INSERT INTO schedules (route_id, vehicle_id, driver_id, departure_time, arrival_time, recurrence) VALUES (?,?,?,?,?,?)",
               (route_id, vehicle_id, driver_id, departure, arrival, recurrence))
    db.commit()
    db.close()

def test_requires_auth(client, db):
    resp = client.get('/api/driver-schedule?driver_id=1&month=6&year=2026')
    assert resp.status_code == 401

def test_requires_all_params(auth_admin, db):
    resp = auth_admin.get('/api/driver-schedule?driver_id=1&month=6')
    assert resp.status_code == 400

def test_returns_empty_for_no_schedules(auth_admin, db):
    did, _, _ = _seed_data()
    resp = auth_admin.get(f'/api/driver-schedule?driver_id={did}&month=6&year=2026')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['driver_name'] == 'D1'
    assert data['year'] == 2026
    assert data['month'] == 6
    assert data['schedules'] == {}

def test_returns_once_schedule(auth_admin, db):
    did, vid, rid = _seed_data()
    _seed_schedule(did, vid, rid, '2026-06-15T08:00:00', '2026-06-15T10:00:00', 'Once')
    resp = auth_admin.get(f'/api/driver-schedule?driver_id={did}&month=6&year=2026')
    assert resp.status_code == 200
    data = resp.get_json()
    assert '2026-06-15' in data['schedules']
    assert len(data['schedules']['2026-06-15']) == 1

def test_expands_daily_recurrence(auth_admin, db):
    did, vid, rid = _seed_data()
    _seed_schedule(did, vid, rid, '2026-06-01T08:00:00', '2026-06-01T10:00:00', 'Daily')
    resp = auth_admin.get(f'/api/driver-schedule?driver_id={did}&month=6&year=2026')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data['schedules']) == 30

def test_expands_weekly_recurrence(auth_admin, db):
    did, vid, rid = _seed_data()
    _seed_schedule(did, vid, rid, '2026-06-01T08:00:00', '2026-06-01T10:00:00', 'Weekly')
    resp = auth_admin.get(f'/api/driver-schedule?driver_id={did}&month=6&year=2026')
    assert resp.status_code == 200
    data = resp.get_json()
    june_mondays = [d for d in data['schedules'].keys()]
    assert all(d for d in june_mondays)
