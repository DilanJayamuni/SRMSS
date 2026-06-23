from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from init_db import get_db, log_audit

assign_driver_bp = Blueprint('assign_driver', __name__)

@assign_driver_bp.route('/assign-driver')
def assign_driver_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('assign_driver.html', user=session['user'])

@assign_driver_bp.route('/api/assign-driver', methods=['GET', 'POST'])
def api_assign_driver():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    if request.method == 'POST':
        d = request.json
        driver_id = d['driver_id']
        vehicle_id = d['vehicle_id']

        taken_vehicle = db.execute('SELECT id FROM assigndriver WHERE vehicle_id=?', (vehicle_id,)).fetchone()
        if taken_vehicle:
            db.close()
            return jsonify({"error": "This vehicle already has a driver assigned."}), 409

        existing = db.execute('SELECT vehicle_id FROM assigndriver WHERE driver_id=?', (driver_id,)).fetchall()
        if existing:
            existing_ids = [row['vehicle_id'] for row in existing]
            placeholders = ','.join('?' * len(existing_ids))
            conflict = db.execute(f'''
                SELECT 1 FROM schedules s1
                JOIN schedules s2 ON s1.vehicle_id=? AND s2.vehicle_id IN ({placeholders})
                AND s1.departure_time < s2.arrival_time
                AND (s1.arrival_time IS NULL OR s1.arrival_time > s2.departure_time)
                LIMIT 1
            ''', [vehicle_id] + existing_ids).fetchone()
            if conflict:
                db.close()
                return jsonify({"error": "This driver's existing vehicles have timetable entries that overlap with this vehicle's schedules."}), 409

        db.execute('INSERT INTO assigndriver (driver_id, vehicle_id) VALUES (?,?)',
                   (driver_id, vehicle_id))
        db.commit()
        db.close()
        return jsonify({"success": True})

    items = db.execute('''
        SELECT a.id, a.driver_id, a.vehicle_id, a.assigned_at,
               d.name as driver_name, v.registration_no as vehicle_reg
        FROM assigndriver a
        JOIN drivers d ON a.driver_id = d.id
        JOIN vehicles v ON a.vehicle_id = v.id
        ORDER BY a.assigned_at DESC
    ''').fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@assign_driver_bp.route('/api/assign-driver/available')
def api_assign_driver_available():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    drivers = db.execute('SELECT id, name FROM drivers ORDER BY name').fetchall()
    vehicles = db.execute('''
        SELECT id, registration_no FROM vehicles
        WHERE id NOT IN (SELECT vehicle_id FROM assigndriver)
    ''').fetchall()
    db.close()
    return jsonify({
        "drivers": [dict(d) for d in drivers],
        "vehicles": [dict(v) for v in vehicles]
    })

@assign_driver_bp.route('/api/assign-driver/<int:id>', methods=['GET'])
def api_assign_driver_detail(id):
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    item = db.execute('''
        SELECT a.id, a.driver_id, a.vehicle_id, a.assigned_at,
               d.name as driver_name, v.registration_no as vehicle_reg
        FROM assigndriver a
        JOIN drivers d ON a.driver_id = d.id
        JOIN vehicles v ON a.vehicle_id = v.id
        WHERE a.id=?
    ''', (id,)).fetchone()
    db.close()
    if not item:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(item))

@assign_driver_bp.route('/api/assign-driver/<int:id>', methods=['PUT'])
def update_assign_driver(id):
    if 'user' not in session or session['user']['role'] != 'Administrator':
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    d = request.json

    current = db.execute('SELECT * FROM assigndriver WHERE id=?', (id,)).fetchone()
    if not current:
        db.close()
        return jsonify({"error": "Not found"}), 404
    old = dict(current)

    driver_id = d.get('driver_id', current['driver_id'])
    vehicle_id = d.get('vehicle_id', current['vehicle_id'])

    taken_vehicle = db.execute('SELECT id FROM assigndriver WHERE vehicle_id=? AND id!=?', (vehicle_id, id)).fetchone()
    if taken_vehicle:
        db.close()
        return jsonify({"error": "This vehicle already has a driver assigned."}), 409

    existing = db.execute('SELECT vehicle_id FROM assigndriver WHERE driver_id=? AND id!=?', (driver_id, id)).fetchall()
    if existing:
        existing_ids = [row['vehicle_id'] for row in existing]
        placeholders = ','.join('?' * len(existing_ids))
        conflict = db.execute(f'''
            SELECT 1 FROM schedules s1
            JOIN schedules s2 ON s1.vehicle_id=? AND s2.vehicle_id IN ({placeholders})
            AND s1.departure_time < s2.arrival_time
            AND (s1.arrival_time IS NULL OR s1.arrival_time > s2.departure_time)
            LIMIT 1
        ''', [vehicle_id] + existing_ids).fetchone()
        if conflict:
            db.close()
            return jsonify({"error": "This driver's existing vehicles have timetable entries that overlap with this vehicle's schedules."}), 409

    db.execute('UPDATE assigndriver SET driver_id=?, vehicle_id=? WHERE id=?',
               (driver_id, vehicle_id, id))
    db.commit()
    log_audit('EDIT', 'assigndriver', id, old, {'driver_id': driver_id, 'vehicle_id': vehicle_id})
    db.close()
    return jsonify({"success": True})

@assign_driver_bp.route('/api/assign-driver/<int:id>', methods=['DELETE'])
def delete_assign_driver(id):
    if 'user' not in session or session['user']['role'] != 'Administrator':
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    old = db.execute('SELECT * FROM assigndriver WHERE id=?', (id,)).fetchone()
    if not old:
        db.close()
        return jsonify({"error": "Not found"}), 404
    db.execute('DELETE FROM assigndriver WHERE id=?', (id,))
    db.commit()
    log_audit('DELETE', 'assigndriver', id, dict(old))
    db.close()
    return jsonify({"success": True})
