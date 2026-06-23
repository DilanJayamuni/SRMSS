from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from init_db import get_db, log_audit

drivers_bp = Blueprint('drivers', __name__)

@drivers_bp.route('/drivers')
def drivers_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('drivers.html', user=session['user'])

@drivers_bp.route('/api/drivers', methods=['GET', 'POST'])
def api_drivers():
    db = get_db()
    if request.method == 'POST':
        d = request.json
        db.execute('INSERT INTO drivers (name, license_no, license_expiry) VALUES (?,?,?)',
                   (d['name'], d['license_no'], d.get('license_expiry', '')))
        db.commit()
        db.close()
        return jsonify({"success": True})
    items = db.execute('SELECT * FROM drivers').fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@drivers_bp.route('/api/drivers/<int:id>', methods=['GET'])
def api_driver_detail(id):
    db = get_db()
    item = db.execute('SELECT * FROM drivers WHERE id=?', (id,)).fetchone()
    db.close()
    return jsonify(dict(item))

@drivers_bp.route('/api/drivers/<int:id>', methods=['PUT'])
def update_driver(id):
    if 'user' not in session or session['user']['role'] != 'Administrator':
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    old = db.execute('SELECT * FROM drivers WHERE id=?', (id,)).fetchone()
    if not old:
        db.close()
        return jsonify({"error": "Not found"}), 404
    d = request.json
    db.execute('UPDATE drivers SET name=?, license_no=?, license_expiry=? WHERE id=?',
               (d['name'], d['license_no'], d.get('license_expiry', ''), id))
    db.commit()
    log_audit('EDIT', 'drivers', id, dict(old), d)
    db.close()
    return jsonify({"success": True})

@drivers_bp.route('/api/drivers/<int:id>', methods=['DELETE'])
def delete_driver(id):
    if 'user' not in session or session['user']['role'] != 'Administrator':
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()

    schedule_count = db.execute('SELECT COUNT(*) as cnt FROM schedules WHERE driver_id=?', (id,)).fetchone()
    if schedule_count['cnt'] > 0:
        db.close()
        return jsonify({"error": f"Cannot delete: this driver is used in {schedule_count['cnt']} schedule(s). Remove or reschedule these entries first."}), 409

    old = db.execute('SELECT * FROM drivers WHERE id=?', (id,)).fetchone()
    if not old:
        db.close()
        return jsonify({"error": "Not found"}), 404
    db.execute('DELETE FROM drivers WHERE id=?', (id,))
    db.commit()
    log_audit('DELETE', 'drivers', id, dict(old))
    db.close()
    return jsonify({"success": True})
