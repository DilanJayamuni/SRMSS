from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from init_db import get_db, log_audit

fuel_bp = Blueprint('fuel', __name__)

@fuel_bp.route('/fuel')
def fuel_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('fuel.html', user=session['user'])

@fuel_bp.route('/api/fuel', methods=['GET', 'POST'])
def api_fuel():
    db = get_db()
    if request.method == 'POST':
        d = request.json
        db.execute('INSERT INTO fuel_logs (vehicle_id, date, liters, cost, mileage, status) VALUES (?,?,?,?,?,?)',
                   (d['vehicle_id'], d['date'], d['liters'], d['cost'], d.get('mileage'), 'Pending'))
        db.commit()
        db.close()
        return jsonify({"success": True})
    q = 'SELECT f.id, f.date, f.liters, f.cost, f.mileage, f.status, v.registration_no FROM fuel_logs f JOIN vehicles v ON f.vehicle_id = v.id'
    params = []
    where_clauses = []
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    vehicle_id = request.args.get('vehicle_id')
    if date_from:
        where_clauses.append('f.date >= ?')
        params.append(date_from)
    if date_to:
        where_clauses.append('f.date <= ?')
        params.append(date_to)
    if vehicle_id:
        where_clauses.append('f.vehicle_id = ?')
        params.append(vehicle_id)
    if where_clauses:
        q += ' WHERE ' + ' AND '.join(where_clauses)
    items = db.execute(q, params).fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@fuel_bp.route('/api/fuel/pending')
def pending_fuel():
    db = get_db()
    items = db.execute('SELECT f.id, f.liters, f.mileage, v.registration_no FROM fuel_logs f JOIN vehicles v ON f.vehicle_id = v.id WHERE f.status="Pending"').fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@fuel_bp.route('/api/fuel/<int:id>', methods=['GET'])
def api_fuel_detail(id):
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    item = db.execute('SELECT f.*, v.registration_no FROM fuel_logs f JOIN vehicles v ON f.vehicle_id = v.id WHERE f.id=?', (id,)).fetchone()
    db.close()
    if not item:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(item))

@fuel_bp.route('/api/fuel/<int:id>', methods=['PUT'])
def update_fuel(id):
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    item = db.execute('SELECT * FROM fuel_logs WHERE id=?', (id,)).fetchone()
    if not item:
        db.close()
        return jsonify({"error": "Not found"}), 404
    role = session['user']['role']
    if item['status'] != 'Pending' and role != 'Administrator':
        db.close()
        return jsonify({"error": "Forbidden"}), 403
    old = dict(item)
    d = request.json
    db.execute('UPDATE fuel_logs SET vehicle_id=?, date=?, liters=?, cost=?, mileage=? WHERE id=?',
               (d['vehicle_id'], d['date'], d['liters'], d['cost'], d.get('mileage'), id))
    db.commit()
    log_audit('EDIT', 'fuel_logs', id, old, d)
    db.close()
    return jsonify({"success": True})

@fuel_bp.route('/api/fuel/<int:id>', methods=['DELETE'])
def delete_fuel(id):
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    item = db.execute('SELECT * FROM fuel_logs WHERE id=?', (id,)).fetchone()
    if not item:
        db.close()
        return jsonify({"error": "Not found"}), 404
    role = session['user']['role']
    if item['status'] != 'Pending' and role != 'Administrator':
        db.close()
        return jsonify({"error": "Forbidden"}), 403
    old = dict(item)
    db.execute('DELETE FROM fuel_logs WHERE id=?', (id,))
    db.commit()
    log_audit('DELETE', 'fuel_logs', id, old)
    db.close()
    return jsonify({"success": True})

@fuel_bp.route('/api/fuel/approve/<int:id>', methods=['POST'])
def approve_fuel(id):
    db = get_db()
    db.execute('UPDATE fuel_logs SET status="Approved" WHERE id=?', (id,))
    db.commit()
    db.close()
    return jsonify({"success": True})

@fuel_bp.route('/api/fuel/reject/<int:id>', methods=['POST'])
def reject_fuel(id):
    db = get_db()
    db.execute('UPDATE fuel_logs SET status="Rejected" WHERE id=?', (id,))
    db.commit()
    db.close()
    return jsonify({"success": True})
