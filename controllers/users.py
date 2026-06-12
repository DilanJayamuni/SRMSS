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
        db.execute('INSERT INTO users (username, password, role) VALUES (?,?,?)',
                   (d['username'], d['password'], d['role']))
        db.commit()
        db.close()
        return jsonify({"success": True})
    items = db.execute('SELECT id, username, role FROM users').fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@users_bp.route('/api/users/<int:id>', methods=['PUT', 'DELETE'])
def update_user(id):
    db = get_db()
    if request.method == 'PUT':
        db.execute('UPDATE users SET role = ? WHERE id = ?', (request.json['role'], id))
    else:
        db.execute('DELETE FROM users WHERE id = ?', (id,))
    db.commit()
    db.close()
    return jsonify({"success": True})
