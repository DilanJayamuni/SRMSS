from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from init_db import get_db

login_bp = Blueprint('login', __name__)

@login_bp.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard.dashboard_page'))
    return render_template('login.html')

@login_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username=? AND password=?',
                      (data['username'], data['password'])).fetchone()
    db.close()
    if user:
        session['user'] = {"id": user["id"], "username": user["username"], "role": user["role"]}
        return jsonify({"success": True, "user": {"username": user["username"], "role": user["role"]}})
    return jsonify({"success": False}), 401

@login_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login.index'))
