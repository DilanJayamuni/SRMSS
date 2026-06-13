from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from init_db import get_db

assign_route_bp = Blueprint('assign_route', __name__)

@assign_route_bp.route('/assign-route')
def assign_route_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('assign_route.html', user=session['user'])

@assign_route_bp.route('/api/assign-route', methods=['GET', 'POST'])
def api_assign_route():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    if request.method == 'POST':
        d = request.json
        route_id = d['route_id']
        vehicle_id = d['vehicle_id']

        taken_vehicle = db.execute('SELECT id FROM assignroute WHERE vehicle_id=?', (vehicle_id,)).fetchone()
        if taken_vehicle:
            db.close()
            return jsonify({"error": "This vehicle already has a route assigned."}), 409

        db.execute('INSERT INTO assignroute (route_id, vehicle_id) VALUES (?,?)',
                   (route_id, vehicle_id))
        db.commit()
        db.close()
        return jsonify({"success": True})

    items = db.execute('''
        SELECT a.id, a.route_id, a.vehicle_id, a.assigned_at,
               r.route_name, v.registration_no as vehicle_reg
        FROM assignroute a
        JOIN routes r ON a.route_id = r.id
        JOIN vehicles v ON a.vehicle_id = v.id
        ORDER BY a.assigned_at DESC
    ''').fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@assign_route_bp.route('/api/assign-route/available')
def api_assign_route_available():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    routes = db.execute('SELECT id, route_name FROM routes ORDER BY route_name').fetchall()
    vehicles = db.execute('''
        SELECT id, registration_no FROM vehicles
        WHERE id NOT IN (SELECT vehicle_id FROM assignroute)
        ORDER BY registration_no
    ''').fetchall()
    db.close()
    return jsonify({
        "routes": [dict(r) for r in routes],
        "vehicles": [dict(v) for v in vehicles]
    })

@assign_route_bp.route('/api/assign-route/<int:id>', methods=['GET'])
def api_assign_route_detail(id):
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    item = db.execute('''
        SELECT a.id, a.route_id, a.vehicle_id, a.assigned_at,
               r.route_name, v.registration_no as vehicle_reg
        FROM assignroute a
        JOIN routes r ON a.route_id = r.id
        JOIN vehicles v ON a.vehicle_id = v.id
        WHERE a.id=?
    ''', (id,)).fetchone()
    db.close()
    if not item:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(item))

@assign_route_bp.route('/api/assign-route/<int:id>', methods=['PUT'])
def update_assign_route(id):
    if 'user' not in session or session['user']['role'] != 'Administrator':
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    d = request.json

    current = db.execute('SELECT * FROM assignroute WHERE id=?', (id,)).fetchone()
    if not current:
        db.close()
        return jsonify({"error": "Not found"}), 404

    vehicle_id = d.get('vehicle_id', current['vehicle_id'])

    taken_vehicle = db.execute('SELECT id FROM assignroute WHERE vehicle_id=? AND id!=?', (vehicle_id, id)).fetchone()
    if taken_vehicle:
        db.close()
        return jsonify({"error": "This vehicle already has a route assigned."}), 409

    db.execute('UPDATE assignroute SET vehicle_id=? WHERE id=?',
               (vehicle_id, id))
    db.commit()
    db.close()
    return jsonify({"success": True})

@assign_route_bp.route('/api/assign-route/<int:id>', methods=['DELETE'])
def delete_assign_route(id):
    if 'user' not in session or session['user']['role'] != 'Administrator':
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    db.execute('DELETE FROM assignroute WHERE id=?', (id,))
    db.commit()
    db.close()
    return jsonify({"success": True})
