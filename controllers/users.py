from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from init_db import get_db

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
def users_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('users.html', user=session['user'])

@users_bp.route('/api/users', methods=['GET', 'POST'])
def api_users():
    db = get_db()
    if request.method == 'POST':
        d = request.json
        db.execute(
            'INSERT INTO users (username, password, role, first_name, last_name, phone_number, address) VALUES (?,?,?,?,?,?,?)',
            (d['username'], d['password'], d['role'], d.get('first_name'), d.get('last_name'), d.get('phone_number'), d.get('address'))
        )
        db.commit()
        db.close()
        return jsonify({"success": True})
    items = db.execute('SELECT id, username, role, first_name, last_name, phone_number, address FROM users').fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@users_bp.route('/api/users/<int:id>', methods=['PUT', 'DELETE'])
def update_user(id):
    db = get_db()
    if request.method == 'PUT':
        d = request.json
        db.execute(
            'UPDATE users SET role = ?, first_name = ?, last_name = ?, phone_number = ?, address = ? WHERE id = ?',
            (d.get('role'), d.get('first_name'), d.get('last_name'), d.get('phone_number'), d.get('address'), id)
        )
    else:
        user = db.execute('SELECT role FROM users WHERE id = ?', (id,)).fetchone()
        if user and user['role'] == 'Administrator':
            count = db.execute('SELECT COUNT(*) AS cnt FROM users WHERE role = ?', ('Administrator',)).fetchone()['cnt']
            if count <= 1:
                db.close()
                return jsonify({"success": False, "error": "Cannot delete the last Administrator account. At least one Administrator must always exist."}), 400
        db.execute('DELETE FROM users WHERE id = ?', (id,))
    db.commit()
    db.close()
    return jsonify({"success": True})
