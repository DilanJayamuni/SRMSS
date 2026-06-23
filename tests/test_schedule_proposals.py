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

def test_create_proposal_requires_auth(client, db):
    did, vid, rid = _seed_data()
    resp = client.post('/api/schedule-proposals', json={
        "driver_id": did, "vehicle_id": vid, "route_id": rid,
        "departure_time": "2026-06-15T08:00"
    })
    assert resp.status_code == 401

def test_create_proposal_success(auth_admin, db):
    did, vid, rid = _seed_data()
    resp = auth_admin.post('/api/schedule-proposals', json={
        "driver_id": did, "vehicle_id": vid, "route_id": rid,
        "departure_time": "2026-06-15T08:00", "arrival_time": "2026-06-15T10:00",
        "recurrence": "Once", "notes": "Test proposal"
    })
    assert resp.status_code == 200

def test_create_proposal_missing_fields(auth_admin, db):
    did, vid, rid = _seed_data()
    resp = auth_admin.post('/api/schedule-proposals', json={
        "vehicle_id": vid, "route_id": rid
    })
    assert resp.status_code == 400

def test_list_proposals(auth_admin, db):
    did, vid, rid = _seed_data()
    auth_admin.post('/api/schedule-proposals', json={
        "driver_id": did, "vehicle_id": vid, "route_id": rid,
        "departure_time": "2026-06-15T08:00"
    })
    resp = auth_admin.get('/api/schedule-proposals?status=Pending')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) >= 1
    assert data[0]['status'] == 'Pending'

def test_approve_proposal_creates_schedule(auth_admin, db):
    did, vid, rid = _seed_data()
    auth_admin.post('/api/schedule-proposals', json={
        "driver_id": did, "vehicle_id": vid, "route_id": rid,
        "departure_time": "2026-06-15T08:00"
    })
    resp = auth_admin.get('/api/schedule-proposals?status=Pending')
    proposals = resp.get_json()
    pid = proposals[0]['id']
    resp = auth_admin.post(f'/api/schedule-proposals/{pid}/approve')
    assert resp.status_code == 200
    db_conn = get_db()
    sched = db_conn.execute("SELECT id FROM schedules WHERE driver_id=?", (did,)).fetchone()
    db_conn.close()
    assert sched is not None

def test_reject_proposal(auth_admin, db):
    did, vid, rid = _seed_data()
    auth_admin.post('/api/schedule-proposals', json={
        "driver_id": did, "vehicle_id": vid, "route_id": rid,
        "departure_time": "2026-06-15T08:00"
    })
    resp = auth_admin.get('/api/schedule-proposals?status=Pending')
    proposals = resp.get_json()
    pid = proposals[0]['id']
    resp = auth_admin.post(f'/api/schedule-proposals/{pid}/reject')
    assert resp.status_code == 200
    db_conn = get_db()
    prop = db_conn.execute("SELECT status FROM schedule_proposals WHERE id=?", (pid,)).fetchone()
    db_conn.close()
    assert prop['status'] == 'Rejected'

def test_staff_cannot_approve_proposal(auth_staff, db):
    did, vid, rid = _seed_data()
    auth_staff.post('/api/schedule-proposals', json={
        "driver_id": did, "vehicle_id": vid, "route_id": rid,
        "departure_time": "2026-06-15T08:00"
    })
    resp = auth_staff.get('/api/schedule-proposals?status=Pending')
    proposals = resp.get_json()
    if proposals:
        pid = proposals[0]['id']
        resp = auth_staff.post(f'/api/schedule-proposals/{pid}/approve')
        assert resp.status_code == 403
