from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from init_db import get_db, log_audit

maintenance_bp = Blueprint('maintenance', __name__)

@maintenance_bp.route('/maintenance')
def maintenance_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('maintenance.html', user=session['user'])

@maintenance_bp.route('/api/maintenance', methods=['GET', 'POST'])
def api_maintenance():
    db = get_db()
    if request.method == 'POST':
        d = request.json
        db.execute('INSERT INTO maintenance_logs (vehicle_id, description, cost, date, mileage) VALUES (?,?,?,?,?)',
                   (d['vehicle_id'], d['description'], d['cost'], d.get('date'), d.get('mileage')))
        db.commit()
        db.close()
        return jsonify({"success": True})
    q = 'SELECT m.id, m.date, m.description, m.cost, m.mileage, m.status, v.registration_no FROM maintenance_logs m JOIN vehicles v ON m.vehicle_id = v.id'
    params = []
    where_clauses = []
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    vehicle_id = request.args.get('vehicle_id')
    if date_from:
        where_clauses.append('m.date >= ?')
        params.append(date_from)
    if date_to:
        where_clauses.append('m.date <= ?')
        params.append(date_to)
    if vehicle_id:
        where_clauses.append('m.vehicle_id = ?')
        params.append(vehicle_id)
    if where_clauses:
        q += ' WHERE ' + ' AND '.join(where_clauses)
    items = db.execute(q, params).fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@maintenance_bp.route('/api/maintenance/pending')
def pending_maintenance():
    db = get_db()
    items = db.execute('SELECT m.id, m.date, m.description, m.mileage, v.registration_no FROM maintenance_logs m JOIN vehicles v ON m.vehicle_id = v.id WHERE m.status="Pending"').fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@maintenance_bp.route('/api/maintenance/<int:id>', methods=['GET'])
def api_maintenance_detail(id):
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    item = db.execute('SELECT m.*, v.registration_no FROM maintenance_logs m JOIN vehicles v ON m.vehicle_id = v.id WHERE m.id=?', (id,)).fetchone()
    db.close()
    if not item:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(item))

@maintenance_bp.route('/api/maintenance/<int:id>', methods=['PUT'])
def update_maintenance(id):
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    item = db.execute('SELECT * FROM maintenance_logs WHERE id=?', (id,)).fetchone()
    if not item:
        db.close()
        return jsonify({"error": "Not found"}), 404
    role = session['user']['role']
    if item['status'] != 'Pending' and role != 'Administrator':
        db.close()
        return jsonify({"error": "Forbidden"}), 403
    old = dict(item)
    d = request.json
    db.execute('UPDATE maintenance_logs SET vehicle_id=?, description=?, cost=?, date=?, mileage=? WHERE id=?',
               (d['vehicle_id'], d['description'], d['cost'], d.get('date'), d.get('mileage'), id))
    db.commit()
    log_audit('EDIT', 'maintenance_logs', id, old, d)
    db.close()
    return jsonify({"success": True})

@maintenance_bp.route('/api/maintenance/<int:id>', methods=['DELETE'])
def delete_maintenance(id):
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    item = db.execute('SELECT * FROM maintenance_logs WHERE id=?', (id,)).fetchone()
    if not item:
        db.close()
        return jsonify({"error": "Not found"}), 404
    role = session['user']['role']
    if item['status'] != 'Pending' and role != 'Administrator':
        db.close()
        return jsonify({"error": "Forbidden"}), 403
    old = dict(item)
    db.execute('DELETE FROM maintenance_logs WHERE id=?', (id,))
    db.commit()
    log_audit('DELETE', 'maintenance_logs', id, old)
    db.close()
    return jsonify({"success": True})

@maintenance_bp.route('/api/maintenance/approve/<int:id>', methods=['POST'])
def approve_maintenance(id):
    db = get_db()
    db.execute('UPDATE maintenance_logs SET status="Approved" WHERE id=?', (id,))
    db.commit()
    db.close()
    return jsonify({"success": True})

@maintenance_bp.route('/api/maintenance/reject/<int:id>', methods=['POST'])
def reject_maintenance(id):
    db = get_db()
    db.execute('UPDATE maintenance_logs SET status="Rejected" WHERE id=?', (id,))
    db.commit()
    db.close()
    return jsonify({"success": True})
