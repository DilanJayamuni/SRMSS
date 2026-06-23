from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from init_db import get_db, log_audit

routes_bp = Blueprint('routes', __name__)

@routes_bp.route('/routes')
def routes_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('routes.html', user=session['user'])

@routes_bp.route('/api/routes', methods=['GET', 'POST'])
def api_routes():
    db = get_db()
    if request.method == 'POST':
        d = request.json
        db.execute('INSERT INTO routes (route_name, start_point, end_point, distance_km, path_geometry, stops) VALUES (?,?,?,?,?,?)',
                   (d['route_name'], d['start_point'], d['end_point'], d['distance_km'], d['path_geometry'], d['stops']))
        db.commit()
        db.close()
        return jsonify({"success": True})
    items = db.execute('SELECT * FROM routes').fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@routes_bp.route('/api/routes/<int:id>', methods=['GET'])
def api_route_detail(id):
    db = get_db()
    item = db.execute('SELECT * FROM routes WHERE id=?', (id,)).fetchone()
    db.close()
    return jsonify(dict(item))

@routes_bp.route('/api/routes/<int:id>', methods=['PUT'])
def update_route(id):
    if 'user' not in session or session['user']['role'] != 'Administrator':
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    old = db.execute('SELECT * FROM routes WHERE id=?', (id,)).fetchone()
    if not old:
        db.close()
        return jsonify({"error": "Not found"}), 404
    d = request.json
    db.execute('UPDATE routes SET route_name=?, start_point=?, end_point=?, distance_km=?, path_geometry=?, stops=? WHERE id=?',
               (d['route_name'], d['start_point'], d['end_point'], d['distance_km'], d['path_geometry'], d['stops'], id))
    db.commit()
    log_audit('EDIT', 'routes', id, dict(old), d)
    db.close()
    return jsonify({"success": True})

@routes_bp.route('/api/routes/<int:id>', methods=['DELETE'])
def delete_route(id):
    if 'user' not in session or session['user']['role'] != 'Administrator':
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()

    schedule_count = db.execute('SELECT COUNT(*) as cnt FROM schedules WHERE route_id=?', (id,)).fetchone()
    if schedule_count['cnt'] > 0:
        db.close()
        return jsonify({"error": f"Cannot delete: this route is used in {schedule_count['cnt']} schedule(s). Remove or reschedule these entries first."}), 409

    assign_count = db.execute('SELECT COUNT(*) as cnt FROM assignroute WHERE route_id=?', (id,)).fetchone()
    if assign_count['cnt'] > 0:
        db.close()
        return jsonify({"error": "Cannot delete: this route is currently assigned to a vehicle. Unassign the route first."}), 409

    old = db.execute('SELECT * FROM routes WHERE id=?', (id,)).fetchone()
    if not old:
        db.close()
        return jsonify({"error": "Not found"}), 404
    db.execute('DELETE FROM routes WHERE id=?', (id,))
    db.commit()
    log_audit('DELETE', 'routes', id, dict(old))
    db.close()
    return jsonify({"success": True})

@routes_bp.route('/viewer')
def viewer_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('viewer.html', user=session['user'])
