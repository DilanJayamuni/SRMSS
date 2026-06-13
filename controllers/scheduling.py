from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from init_db import get_db

scheduling_bp = Blueprint('scheduling', __name__)

@scheduling_bp.route('/timetable')
def timetable_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('scheduling.html', user=session['user'])

@scheduling_bp.route('/control')
def control_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('control.html', user=session['user'])

@scheduling_bp.route('/api/schedules', methods=['GET', 'POST'])
def api_schedules():
    db = get_db()
    if request.method == 'POST':
        d = request.json
        departure = d.get('departure_time', '')
        arrival = d.get('arrival_time', '')

        if not departure:
            db.close()
            return jsonify({"error": "Departure time is required."}), 400
        if not arrival:
            db.close()
            return jsonify({"error": "Estimated arrival time is required."}), 400
        if arrival <= departure:
            db.close()
            return jsonify({"error": "Estimated arrival must be later than departure."}), 400

        db.execute('INSERT INTO schedules (route_id, vehicle_id, driver_id, departure_time, arrival_time, recurrence) VALUES (?,?,?,?,?,?)',
                   (d['route_id'], d['vehicle_id'], d['driver_id'], departure, arrival, d.get('recurrence', 'Once')))
        db.commit()
        db.close()
        return jsonify({"success": True})
    q = '''SELECT s.id, s.departure_time, s.arrival_time, s.recurrence, s.status,
                  s.route_id, s.vehicle_id, s.driver_id,
                  r.route_name, v.registration_no, d.name as driver_name
           FROM schedules s
           JOIN routes r ON s.route_id = r.id
           JOIN vehicles v ON s.vehicle_id = v.id
           JOIN drivers d ON s.driver_id = d.id'''
    items = db.execute(q).fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@scheduling_bp.route('/api/schedules/<int:id>', methods=['PUT'])
def update_schedule(id):
    if 'user' not in session or session['user']['role'] != 'Administrator':
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    d = request.json
    departure = d.get('departure_time', '')
    arrival = d.get('arrival_time', '')

    if not departure:
        db.close()
        return jsonify({"error": "Departure time is required."}), 400
    if not arrival:
        db.close()
        return jsonify({"error": "Estimated arrival time is required."}), 400
    if arrival <= departure:
        db.close()
        return jsonify({"error": "Estimated arrival must be later than departure."}), 400

    db.execute('''UPDATE schedules SET route_id=?, vehicle_id=?, driver_id=?,
                  departure_time=?, arrival_time=?, recurrence=? WHERE id=?''',
               (d['route_id'], d['vehicle_id'], d['driver_id'],
                departure, arrival, d.get('recurrence', 'Once'), id))
    db.commit()
    db.close()
    return jsonify({"success": True})

@scheduling_bp.route('/api/schedules/<int:id>', methods=['DELETE'])
def delete_schedule(id):
    if 'user' not in session or session['user']['role'] != 'Administrator':
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    db.execute('DELETE FROM schedules WHERE id=?', (id,))
    db.commit()
    db.close()
    return jsonify({"success": True})

@scheduling_bp.route('/api/schedules/check', methods=['POST'])
def check_schedule():
    d = request.json
    db = get_db()
    vid = d['vehicle_id']
    did = d['driver_id']
    new_dep = d['departure_time']
    new_arr = d['arrival_time']
    exclude_id = d.get('exclude_id')

    conflict = db.execute('''SELECT id FROM schedules WHERE vehicle_id=?
                             AND departure_time < ? AND (arrival_time IS NULL OR arrival_time > ?)
                             AND (? IS NULL OR id != ?)''',
                          (vid, new_arr, new_dep, exclude_id, exclude_id)).fetchone()
    if conflict:
        db.close()
        return jsonify({"conflict": True, "message": "Vehicle already scheduled during this time window."})

    conflict = db.execute('''SELECT id FROM schedules WHERE driver_id=?
                             AND departure_time < ? AND (arrival_time IS NULL OR arrival_time > ?)
                             AND (? IS NULL OR id != ?)''',
                          (did, new_arr, new_dep, exclude_id, exclude_id)).fetchone()
    if conflict:
        db.close()
        return jsonify({"conflict": True, "message": "Driver already scheduled during this time window."})

    db.close()
    return jsonify({"conflict": False})

@scheduling_bp.route('/api/vehicle-assignment/<int:id>')
def vehicle_assignment(id):
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()

    driver = db.execute('''
        SELECT d.id, d.name, d.license_no
        FROM assigndriver ad
        JOIN drivers d ON ad.driver_id = d.id
        WHERE ad.vehicle_id = ?
    ''', (id,)).fetchone()

    route = db.execute('''
        SELECT r.id, r.route_name, r.start_point, r.end_point
        FROM assignroute ar
        JOIN routes r ON ar.route_id = r.id
        WHERE ar.vehicle_id = ?
    ''', (id,)).fetchone()

    db.close()

    if not driver and not route:
        return jsonify({"error": "No driver or route assigned to this vehicle."}), 404
    if not driver:
        return jsonify({"error": "No driver assigned to this vehicle. Please assign a driver first."}), 404
    if not route:
        return jsonify({"error": "No route assigned to this vehicle. Please assign a route first."}), 404

    return jsonify({
        "driver": dict(driver),
        "route": dict(route)
    })

@scheduling_bp.route('/api/operations/status/<int:id>', methods=['POST'])
def op_status(id):
    db = get_db()
    db.execute('UPDATE schedules SET status = ? WHERE id = ?', (request.json['status'], id))
    db.commit()
    db.close()
    return jsonify({"success": True})
