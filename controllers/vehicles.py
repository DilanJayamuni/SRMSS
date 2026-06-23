from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from init_db import get_db, log_audit

vehicles_bp = Blueprint('vehicles', __name__)

@vehicles_bp.route('/vehicles')
def vehicles_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('vehicles.html', user=session['user'])

@vehicles_bp.route('/api/vehicles', methods=['GET', 'POST'])
def api_vehicles():
    db = get_db()
    if request.method == 'POST':
        d = request.json
        db.execute('INSERT INTO vehicles (registration_no, type, seats, mileage, vehicle_number) VALUES (?,?,?,?,?)',
                   (d['registration_no'], d['type'], d['seats'], d.get('mileage', 0), d.get('vehicle_number', '')))
        db.commit()
        db.close()
        return jsonify({"success": True})
    items = db.execute('SELECT * FROM vehicles').fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@vehicles_bp.route('/api/vehicles/<int:id>', methods=['GET'])
def api_vehicle_detail(id):
    db = get_db()
    item = db.execute('SELECT * FROM vehicles WHERE id=?', (id,)).fetchone()
    db.close()
    return jsonify(dict(item))

@vehicles_bp.route('/api/vehicles/<int:id>', methods=['PUT'])
def update_vehicle(id):
    if 'user' not in session or session['user']['role'] != 'Administrator':
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    old = db.execute('SELECT * FROM vehicles WHERE id=?', (id,)).fetchone()
    if not old:
        db.close()
        return jsonify({"error": "Not found"}), 404
    d = request.json
    db.execute('UPDATE vehicles SET registration_no=?, type=?, seats=?, mileage=?, vehicle_number=? WHERE id=?',
               (d['registration_no'], d['type'], d['seats'], d.get('mileage', 0), d.get('vehicle_number', ''), id))
    db.commit()
    log_audit('EDIT', 'vehicles', id, dict(old), d)
    db.close()
    return jsonify({"success": True})

@vehicles_bp.route('/api/vehicles/<int:id>', methods=['DELETE'])
def delete_vehicle(id):
    if 'user' not in session or session['user']['role'] != 'Administrator':
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    old = db.execute('SELECT * FROM vehicles WHERE id=?', (id,)).fetchone()
    if not old:
        db.close()
        return jsonify({"error": "Not found"}), 404
    db.execute('DELETE FROM vehicles WHERE id=?', (id,))
    db.commit()
    log_audit('DELETE', 'vehicles', id, dict(old))
    db.close()
    return jsonify({"success": True})
