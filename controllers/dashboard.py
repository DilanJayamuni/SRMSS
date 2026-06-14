from datetime import datetime
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from init_db import get_db
from functools import wraps

dashboard_bp = Blueprint('dashboard', __name__)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        if session['user']['role'] != 'Administrator':
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)
    return decorated

def require_supervisor_or_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        if session['user']['role'] not in ('Administrator', 'Supervisor'):
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)
    return decorated

@dashboard_bp.route('/dashboard')
def dashboard_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    db = get_db()
    role = session['user']['role']
    context = {"user": session['user']}
    if role == 'Administrator':
        context['fleet_size'] = db.execute('SELECT COUNT(*) FROM vehicles').fetchone()[0]
        context['active_trips_today'] = db.execute("SELECT COUNT(*) FROM schedules WHERE date(departure_time) = date('now')").fetchone()[0]
        context['pending_fuel'] = db.execute("SELECT COUNT(*) FROM fuel_logs WHERE status='Pending'").fetchone()[0]
        context['pending_maint'] = db.execute("SELECT COUNT(*) FROM maintenance_logs WHERE status='Pending'").fetchone()[0]
        context['total_monthly_cost'] = db.execute("SELECT COALESCE(SUM(cost),0) FROM fuel_logs WHERE status='Approved' AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')").fetchone()[0] + db.execute("SELECT COALESCE(SUM(cost),0) FROM maintenance_logs WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')").fetchone()[0]
        context['expiring_drivers'] = db.execute("SELECT COUNT(*) FROM drivers WHERE license_expiry IS NOT NULL AND license_expiry != '' AND julianday(license_expiry) - julianday('now') <= 30").fetchone()[0]
    elif role == 'Supervisor':
        context['today_total_trips'] = db.execute("SELECT COUNT(*) FROM schedules WHERE date(departure_time) = date('now')").fetchone()[0]
        today_total = db.execute("SELECT COUNT(*) FROM schedules WHERE date(departure_time) = date('now')").fetchone()[0]
        today_completed = db.execute("SELECT COUNT(*) FROM schedules WHERE date(departure_time) = date('now') AND status='Completed'").fetchone()[0]
        context['completion_rate'] = round(today_completed / today_total * 100, 1) if today_total > 0 else 0
        context['active_fleet_count'] = db.execute("SELECT COUNT(DISTINCT vehicle_id) FROM schedules WHERE date(departure_time) = date('now')").fetchone()[0]
        context['pending_fuel'] = db.execute("SELECT COUNT(*) FROM fuel_logs WHERE status='Pending'").fetchone()[0]
    else:
        context['my_trips_today'] = 0
        driver = db.execute("SELECT d.id FROM drivers d JOIN assigndriver ad ON d.id=ad.driver_id JOIN vehicles v ON ad.vehicle_id=v.id WHERE d.name LIKE ?", ('%' + session['user']['username'] + '%',)).fetchone()
        if driver:
            context['my_trips_today'] = db.execute("SELECT COUNT(*) FROM schedules WHERE driver_id=? AND date(departure_time)=date('now')", (driver['id'],)).fetchone()[0]
        context['fleet_count'] = db.execute('SELECT COUNT(*) FROM vehicles').fetchone()[0]
    db.close()
    return render_template('dashboard.html', **context)

@dashboard_bp.route('/api/stats')
def stats():
    db = get_db()
    s = {
        "vehicles": db.execute('SELECT COUNT(*) FROM vehicles').fetchone()[0],
        "drivers": db.execute('SELECT COUNT(*) FROM drivers').fetchone()[0],
        "trips": db.execute("SELECT COUNT(*) FROM schedules").fetchone()[0],
        "pending_fuel": db.execute("SELECT COUNT(*) FROM fuel_logs WHERE status='Pending'").fetchone()[0],
        "active_today": db.execute("SELECT COUNT(*) FROM schedules WHERE date(departure_time) = date('now')").fetchone()[0]
    }
    db.close()
    return jsonify(s)

@dashboard_bp.route('/api/operations/today')
def operations_today():
    db = get_db()
    date_param = request.args.get('date')
    if date_param:
        try:
            datetime.strptime(date_param, '%Y-%m-%d')
        except ValueError:
            date_param = None
    q = '''SELECT s.id, s.status, s.departure_time, r.route_name, v.registration_no, d.name as driver_name
           FROM schedules s
           JOIN routes r ON s.route_id = r.id
           JOIN vehicles v ON s.vehicle_id = v.id
           JOIN drivers d ON s.driver_id = d.id
           WHERE date(s.departure_time) = ?'''
    items = db.execute(q, (date_param or datetime.now().strftime('%Y-%m-%d'),)).fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@dashboard_bp.route('/api/monitoring/vehicles')
def monitoring_vehicles():
    db = get_db()
    q = '''SELECT v.id, v.registration_no, v.type, v.capacity, v.mileage, COUNT(s.id) as trip_count
           FROM vehicles v LEFT JOIN schedules s ON v.id = s.vehicle_id GROUP BY v.id'''
    items = db.execute(q).fetchall()
    db.close()
    return jsonify([dict(i) for i in items])

@dashboard_bp.route('/monitoring')
def monitoring_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('monitoring.html', user=session['user'])

@dashboard_bp.route('/api/dashboard/admin')
@require_admin
def dashboard_admin():
    db = get_db()
    fleet_size = db.execute('SELECT COUNT(*) FROM vehicles').fetchone()[0]
    active_trips_today = db.execute("SELECT COUNT(*) FROM schedules WHERE date(departure_time) = date('now')").fetchone()[0]
    pending_fuel = db.execute("SELECT COUNT(*) FROM fuel_logs WHERE status='Pending'").fetchone()[0]
    pending_maint = db.execute("SELECT COUNT(*) FROM maintenance_logs WHERE status='Pending'").fetchone()[0]
    pending_approvals_count = pending_fuel + pending_maint

    monthly_cost = [dict(r) for r in db.execute('''SELECT strftime('%Y-%m', f.date) as month,
                    COALESCE(SUM(f.cost),0) as fuel_cost,
                    0 as maint_cost
             FROM fuel_logs f WHERE f.status='Approved'
             AND strftime('%Y', f.date) = strftime('%Y', 'now')
             GROUP BY month ORDER BY month''').fetchall()]
    maint_monthly = db.execute('''SELECT strftime('%Y-%m', m.date) as month,
                    COALESCE(SUM(m.cost),0) as maint_cost
             FROM maintenance_logs m
             WHERE strftime('%Y', m.date) = strftime('%Y', 'now')
             GROUP BY month ORDER BY month''').fetchall()
    maint_map = {r['month']: r['maint_cost'] for r in maint_monthly}
    for r in monthly_cost:
        r['maint_cost'] = maint_map.get(r['month'], 0)
    monthly_set = set(r['month'] for r in monthly_cost)
    for r in maint_monthly:
        if r['month'] not in monthly_set:
            monthly_cost.append({"month": r['month'], "fuel_cost": 0, "maint_cost": r['maint_cost']})
    monthly_cost.sort(key=lambda x: x['month'])

    trip_status = [dict(r) for r in db.execute('''SELECT status, COUNT(*) as count
            FROM schedules
            WHERE strftime('%Y-%m', departure_time) = strftime('%Y-%m', 'now')
            GROUP BY status''').fetchall()]

    fleet_composition = [dict(r) for r in db.execute('''SELECT type, COUNT(*) as count
            FROM vehicles WHERE type IS NOT NULL AND type != ''
            GROUP BY type''').fetchall()]

    license_expiries = [dict(r) for r in db.execute('''SELECT d.name as driver_name, d.license_no,
            CAST(julianday(d.license_expiry) - julianday('now') AS INTEGER) as days_until_expiry
            FROM drivers d
            WHERE d.license_expiry IS NOT NULL AND d.license_expiry != ''
            AND julianday(d.license_expiry) - julianday('now') BETWEEN 0 AND 90
            ORDER BY days_until_expiry''').fetchall()]

    vehicle_utilization = [dict(r) for r in db.execute('''SELECT v.registration_no, COUNT(s.id) as trip_count
            FROM vehicles v LEFT JOIN schedules s ON v.id = s.vehicle_id
            AND strftime('%Y-%m', s.departure_time) = strftime('%Y-%m', 'now')
            GROUP BY v.id ORDER BY trip_count DESC''').fetchall()]

    route_completion = [dict(r) for r in db.execute('''SELECT r.route_name,
            COUNT(*) as total_trips,
            SUM(CASE WHEN s.status='Completed' THEN 1 ELSE 0 END) as completed_trips,
            ROUND(AVG(CASE WHEN s.status='Completed' THEN 100.0 ELSE 0 END), 1) as completion_rate
            FROM schedules s JOIN routes r ON s.route_id = r.id
            WHERE strftime('%Y-%m', s.departure_time) = strftime('%Y-%m', 'now')
            GROUP BY r.id ORDER BY completion_rate''').fetchall()]

    today_operations = [dict(r) for r in db.execute('''SELECT s.departure_time, r.route_name,
            v.registration_no, d.name as driver_name, s.status
            FROM schedules s
            JOIN routes r ON s.route_id = r.id
            JOIN vehicles v ON s.vehicle_id = v.id
            JOIN drivers d ON s.driver_id = d.id
            WHERE date(s.departure_time) = date('now')
            ORDER BY s.departure_time''').fetchall()]

    db.close()
    return jsonify({
        "fleet_size": fleet_size,
        "active_trips_today": active_trips_today,
        "pending_approvals_count": pending_approvals_count,
        "monthly_cost": monthly_cost,
        "trip_status": trip_status,
        "fleet_composition": fleet_composition,
        "license_expiries": license_expiries,
        "vehicle_utilization": vehicle_utilization,
        "route_completion": route_completion,
        "today_operations": today_operations
    })

@dashboard_bp.route('/api/dashboard/supervisor')
@require_supervisor_or_admin
def dashboard_supervisor():
    db = get_db()
    today_total_trips = db.execute("SELECT COUNT(*) FROM schedules WHERE date(departure_time) = date('now')").fetchone()[0]
    today_completed = db.execute("SELECT COUNT(*) FROM schedules WHERE date(departure_time) = date('now') AND status='Completed'").fetchone()[0]
    completion_rate = round(today_completed / today_total_trips * 100, 1) if today_total_trips > 0 else 0
    active_fleet_count = db.execute("SELECT COUNT(DISTINCT vehicle_id) FROM schedules WHERE date(departure_time) = date('now')").fetchone()[0]
    pending_fuel_count = db.execute("SELECT COUNT(*) FROM fuel_logs WHERE status='Pending'").fetchone()[0]

    today_trip_status = [dict(r) for r in db.execute('''SELECT status, COUNT(*) as count
            FROM schedules WHERE date(departure_time) = date('now')
            GROUP BY status''').fetchall()]

    route_completion = [dict(r) for r in db.execute('''SELECT r.route_name,
            COUNT(*) as total_trips,
            SUM(CASE WHEN s.status='Completed' THEN 1 ELSE 0 END) as completed_trips,
            ROUND(AVG(CASE WHEN s.status='Completed' THEN 100.0 ELSE 0 END), 1) as completion_rate
            FROM schedules s JOIN routes r ON s.route_id = r.id
            WHERE strftime('%Y-%m', s.departure_time) = strftime('%Y-%m', 'now')
            GROUP BY r.id ORDER BY completion_rate''').fetchall()]

    vehicle_utilization = [dict(r) for r in db.execute('''SELECT v.registration_no, COUNT(s.id) as trip_count
            FROM vehicles v LEFT JOIN schedules s ON v.id = s.vehicle_id
            AND strftime('%Y-%m', s.departure_time) = strftime('%Y-%m', 'now')
            GROUP BY v.id ORDER BY trip_count DESC''').fetchall()]

    today_operations = [dict(r) for r in db.execute('''SELECT s.departure_time, r.route_name,
            v.registration_no, d.name as driver_name, s.status
            FROM schedules s
            JOIN routes r ON s.route_id = r.id
            JOIN vehicles v ON s.vehicle_id = v.id
            JOIN drivers d ON s.driver_id = d.id
            WHERE date(s.departure_time) = date('now')
            ORDER BY s.departure_time''').fetchall()]

    fuel_cost_monthly = [dict(r) for r in db.execute('''SELECT strftime('%Y-%m', f.date) as month,
            COALESCE(SUM(f.cost),0) as total_cost
            FROM fuel_logs f WHERE f.status='Approved'
            AND strftime('%Y', f.date) = strftime('%Y', 'now')
            GROUP BY month ORDER BY month''').fetchall()]

    db.close()
    return jsonify({
        "today_total_trips": today_total_trips,
        "completion_rate": completion_rate,
        "active_fleet_count": active_fleet_count,
        "pending_fuel_count": pending_fuel_count,
        "today_trip_status": today_trip_status,
        "route_completion": route_completion,
        "vehicle_utilization": vehicle_utilization,
        "today_operations": today_operations,
        "fuel_cost_monthly": fuel_cost_monthly
    })

@dashboard_bp.route('/api/dashboard/staff')
@require_auth
def dashboard_staff():
    db = get_db()
    fleet_count = db.execute('SELECT COUNT(*) FROM vehicles').fetchone()[0]
    fleet_composition = [dict(r) for r in db.execute('''SELECT type, COUNT(*) as count
            FROM vehicles WHERE type IS NOT NULL AND type != ''
            GROUP BY type''').fetchall()]

    my_trips = []
    my_trips_today = 0
    driver = db.execute("SELECT d.id FROM drivers d JOIN assigndriver ad ON d.id=ad.driver_id JOIN vehicles v ON ad.vehicle_id=v.id WHERE d.name LIKE ?", ('%' + session['user']['username'] + '%',)).fetchone()
    if driver:
        my_trips_today = db.execute("SELECT COUNT(*) FROM schedules WHERE driver_id=? AND date(departure_time)=date('now')", (driver['id'],)).fetchone()[0]
        my_trips = [dict(r) for r in db.execute('''SELECT s.departure_time, r.route_name,
                v.registration_no, s.status
                FROM schedules s
                JOIN routes r ON s.route_id = r.id
                JOIN vehicles v ON s.vehicle_id = v.id
                WHERE s.driver_id = ? AND date(s.departure_time) = date('now')
                ORDER BY s.departure_time''', (driver['id'],)).fetchall()]

    db.close()
    return jsonify({
        "my_trips_today": my_trips_today,
        "my_trips": my_trips,
        "fleet_composition": fleet_composition,
        "fleet_count": fleet_count
    })

@dashboard_bp.route('/api/dashboard/costs/monthly')
@require_supervisor_or_admin
def dashboard_costs_monthly():
    db = get_db()
    fuel_costs = {r['month']: r['fuel_cost'] for r in db.execute('''SELECT strftime('%Y-%m', date) as month,
                   COALESCE(SUM(cost),0) as fuel_cost FROM fuel_logs
                   WHERE status='Approved' AND strftime('%Y', date) = strftime('%Y', 'now')
                   GROUP BY month''').fetchall()}
    maint_costs = {r['month']: r['maint_cost'] for r in db.execute('''SELECT strftime('%Y-%m', date) as month,
                    COALESCE(SUM(cost),0) as maint_cost FROM maintenance_logs
                    WHERE strftime('%Y', date) = strftime('%Y', 'now')
                    GROUP BY month''').fetchall()}
    all_months = sorted(set(list(fuel_costs.keys()) + list(maint_costs.keys())))
    result = [{"month": m, "fuel_cost": fuel_costs.get(m, 0), "maint_cost": maint_costs.get(m, 0)} for m in all_months]
    db.close()
    return jsonify(result)

@dashboard_bp.route('/api/dashboard/fleet/composition')
@require_auth
def dashboard_fleet_composition():
    db = get_db()
    result = [dict(r) for r in db.execute('''SELECT type, COUNT(*) as count
            FROM vehicles WHERE type IS NOT NULL AND type != ''
            GROUP BY type''').fetchall()]
    db.close()
    return jsonify(result)

@dashboard_bp.route('/api/dashboard/licenses/expiring')
@require_supervisor_or_admin
def dashboard_licenses_expiring():
    db = get_db()
    result = [dict(r) for r in db.execute('''SELECT d.name as driver_name, d.license_no,
            CAST(julianday(d.license_expiry) - julianday('now') AS INTEGER) as days_until_expiry
            FROM drivers d
            WHERE d.license_expiry IS NOT NULL AND d.license_expiry != ''
            AND julianday(d.license_expiry) - julianday('now') BETWEEN 0 AND 90
            ORDER BY days_until_expiry''').fetchall()]
    db.close()
    return jsonify(result)
