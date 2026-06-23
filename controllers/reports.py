from flask import Blueprint, render_template, jsonify, session, redirect, url_for, request, Response
from init_db import get_db
import csv
from io import StringIO
from datetime import date

reports_bp = Blueprint('reports', __name__)

def require_report_access():
    return 'user' in session and session['user']['role'] in ('Administrator', 'Supervisor')

def require_admin():
    return 'user' in session and session['user']['role'] == 'Administrator'

def _apply_date_filters(conditions, params, date_from, date_to, date_col='date'):
    if date_from:
        conditions.append(f"{date_col} >= ?")
        params.append(date_from)
    if date_to:
        conditions.append(f"{date_col} <= ?")
        params.append(date_to)

def _where(conditions):
    return " WHERE " + " AND ".join(conditions) if conditions else ""

@reports_bp.route('/reports')
def reports_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('reports.html', user=session['user'])

@reports_bp.route('/api/reports/summary')
def reports_summary():
    if not require_report_access():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    fc = 0; mc = 0; liters = 0
    fc_conds = ["status='Approved'"]; m_conds = []; s_conds = []
    fc_params = []; m_params = []; s_params = []
    _apply_date_filters(fc_conds, fc_params, date_from, date_to, 'date')
    _apply_date_filters(m_conds, m_params, date_from, date_to, 'date')
    _apply_date_filters(s_conds, s_params, date_from, date_to, 'departure_time')

    fc_res = db.execute(f"SELECT SUM(cost) FROM fuel_logs{_where(fc_conds)}", fc_params).fetchone()[0]
    mc_res = db.execute(f"SELECT SUM(cost) FROM maintenance_logs{_where(m_conds)}", m_params).fetchone()[0]
    ltr_res = db.execute(f"SELECT SUM(liters) FROM fuel_logs{_where(fc_conds)}", fc_params).fetchone()[0]
    tot_trips = db.execute(f"SELECT COUNT(*) FROM schedules{_where(s_conds)}", s_params).fetchone()[0]
    comp_conds = ["status='Completed'"] + s_conds
    comp_params = s_params[:]
    comp_trips = db.execute(f"SELECT COUNT(*) FROM schedules{_where(comp_conds)}", comp_params).fetchone()[0]

    fc = fc_res if fc_res else 0
    mc = mc_res if mc_res else 0
    liters = ltr_res if ltr_res else 0
    rate = (comp_trips / tot_trips * 100) if tot_trips > 0 else 0

    db.close()
    return jsonify({
        "total_fuel_cost": fc, "total_maint_cost": mc, "total_trips": tot_trips,
        "completed_trips": comp_trips, "completion_rate": round(rate, 1), "total_liters": liters
    })

@reports_bp.route('/api/reports/fuel')
def reports_fuel():
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    vehicle_id = request.args.get('vehicle_id')
    conds = ["f.status='Approved'"]; params = []
    _apply_date_filters(conds, params, date_from, date_to, 'f.date')
    if vehicle_id:
        conds.append("f.vehicle_id = ?"); params.append(vehicle_id)
    rows = db.execute(f'''SELECT v.registration_no, v.type,
                          SUM(f.cost) as total_cost, SUM(f.liters) as total_liters,
                          COUNT(f.id) as entry_count, ROUND(AVG(f.cost/f.liters),2) as avg_cost_per_liter,
                          strftime('%Y-%m',f.date) as month
                   FROM fuel_logs f JOIN vehicles v ON f.vehicle_id=v.id{_where(conds)}
                   GROUP BY v.id, month ORDER BY month''', params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@reports_bp.route('/api/reports/fuel/efficiency')
def reports_fuel_efficiency():
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    vehicle_id = request.args.get('vehicle_id')
    f_conds = ["f.status='Approved'"]; f_params = []
    s_conds = ["s.status='Completed'"]; s_params = []
    _apply_date_filters(f_conds, f_params, date_from, date_to, 'f.date')
    _apply_date_filters(s_conds, s_params, date_from, date_to, 's.departure_time')
    if vehicle_id:
        f_conds.append("f.vehicle_id = ?"); f_params.append(vehicle_id)
        s_conds.append("s.vehicle_id = ?"); s_params.append(vehicle_id)
    rows = db.execute(f'''SELECT v.id, v.registration_no, v.type,
                          COALESCE(f.total_liters,0) as total_liters,
                          COALESCE(s.total_km,0) as total_km,
                          CASE WHEN COALESCE(s.total_km,0) > 0
                               THEN ROUND(COALESCE(f.total_liters,0)/s.total_km*100,2)
                               ELSE 0 END as efficiency
                   FROM vehicles v
                   LEFT JOIN (SELECT vehicle_id, SUM(liters) as total_liters FROM fuel_logs{_where(f_conds)} GROUP BY vehicle_id) f ON v.id=f.vehicle_id
                   LEFT JOIN (SELECT s.vehicle_id, SUM(r.distance_km) as total_km
                              FROM schedules s JOIN routes r ON s.route_id=r.id{_where(s_conds)} GROUP BY s.vehicle_id) s ON v.id=s.vehicle_id
                   ORDER BY efficiency DESC''', f_params + s_params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@reports_bp.route('/api/reports/maintenance')
def reports_maintenance():
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    vehicle_id = request.args.get('vehicle_id')
    status = request.args.get('status')
    conds = []; params = []
    _apply_date_filters(conds, params, date_from, date_to, 'm.date')
    if vehicle_id:
        conds.append("m.vehicle_id = ?"); params.append(vehicle_id)
    if status:
        conds.append("m.status = ?"); params.append(status)
    rows = db.execute(f'''SELECT v.registration_no, v.type,
                          SUM(m.cost) as total_cost, COUNT(m.id) as entry_count,
                          MAX(m.date) as last_date,
                          strftime('%Y-%m',m.date) as month
                   FROM maintenance_logs m JOIN vehicles v ON m.vehicle_id=v.id{_where(conds)}
                   GROUP BY v.id, month ORDER BY month''', params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@reports_bp.route('/api/reports/maintenance/pending')
def reports_maintenance_pending():
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    rows = db.execute('''SELECT m.id, m.date, m.description, m.cost, m.mileage, v.registration_no
                         FROM maintenance_logs m JOIN vehicles v ON m.vehicle_id=v.id
                         WHERE m.status='Pending' ORDER BY m.date''').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@reports_bp.route('/api/reports/trips')
def reports_trips():
    if not require_report_access():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    route_id = request.args.get('route_id')
    vehicle_id = request.args.get('vehicle_id')
    driver_id = request.args.get('driver_id')
    conds = []; params = []
    _apply_date_filters(conds, params, date_from, date_to, 's.departure_time')
    if route_id:
        conds.append("s.route_id = ?"); params.append(route_id)
    if vehicle_id:
        conds.append("s.vehicle_id = ?"); params.append(vehicle_id)
    if driver_id:
        conds.append("s.driver_id = ?"); params.append(driver_id)
    by_status = db.execute(f'''SELECT s.status, COUNT(*) as count
                               FROM schedules s{_where(conds)} GROUP BY s.status''', params).fetchall()
    by_month = db.execute(f'''SELECT COUNT(*) as total,
                              SUM(CASE WHEN s.status='Completed' THEN 1 ELSE 0 END) as completed,
                              strftime('%Y-%m',s.departure_time) as month
                       FROM schedules s{_where(conds)} GROUP BY month ORDER BY month''', params).fetchall()
    db.close()
    return jsonify({"by_status": [dict(r) for r in by_status], "by_month": [dict(r) for r in by_month]})

@reports_bp.route('/api/reports/trips/routes')
def reports_trips_routes():
    if not require_report_access():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    conds = []; params = []
    _apply_date_filters(conds, params, date_from, date_to, 's.departure_time')
    rows = db.execute(f'''SELECT r.route_name, COUNT(*) as total_trips,
                          SUM(CASE WHEN s.status='Completed' THEN 1 ELSE 0 END) as completed_trips,
                          ROUND(AVG(CASE WHEN s.status='Completed' THEN 100.0 ELSE 0 END),1) as completion_rate
                   FROM schedules s JOIN routes r ON s.route_id=r.id{_where(conds)}
                   GROUP BY r.id ORDER BY completion_rate''', params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@reports_bp.route('/api/reports/fleet')
def reports_fleet():
    if not require_report_access():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    vehicle_type = request.args.get('vehicle_type')
    s_conds = ["s.status='Completed'"]; s_params = []
    _apply_date_filters(s_conds, s_params, date_from, date_to, 's.departure_time')
    v_where = ""
    v_params = []
    if vehicle_type:
        v_where = " WHERE v.type = ?"
        v_params.append(vehicle_type)
    rows = db.execute(f'''SELECT v.id, v.registration_no, v.type, v.mileage,
                          COALESCE(st.trip_count,0) as trips_completed,
                          COALESCE(st.total_km,0) as total_distance_km,
                          COALESCE(fl.total_liters,0) as total_fuel_liters
                   FROM vehicles v
                   LEFT JOIN (SELECT s.vehicle_id, COUNT(*) as trip_count, SUM(r.distance_km) as total_km
                              FROM schedules s JOIN routes r ON s.route_id=r.id{_where(s_conds)} GROUP BY s.vehicle_id) st
                        ON v.id=st.vehicle_id
                   LEFT JOIN (SELECT vehicle_id, SUM(liters) as total_liters
                              FROM fuel_logs WHERE status='Approved' GROUP BY vehicle_id) fl
                        ON v.id=fl.vehicle_id{v_where}
                   ORDER BY trips_completed DESC''', s_params + v_params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@reports_bp.route('/api/reports/drivers')
def reports_drivers():
    if not require_report_access():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    driver_id = request.args.get('driver_id')
    s_conds = ["s.status='Completed'"]; s_params = []
    _apply_date_filters(s_conds, s_params, date_from, date_to, 's.departure_time')
    if driver_id:
        s_conds.append("s.driver_id = ?"); s_params.append(driver_id)
    rows = db.execute(f'''SELECT d.id, d.name, d.license_no,
                          COUNT(s.id) as trips_completed
                   FROM drivers d
                   LEFT JOIN schedules s ON d.id=s.driver_id{_where(s_conds)}
                   GROUP BY d.id ORDER BY trips_completed DESC''', s_params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@reports_bp.route('/api/reports/drivers/licenses')
def reports_drivers_licenses():
    if not require_report_access():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    window = request.args.get('window', type=int)
    q = '''SELECT id, name, license_no, license_expiry,
                  CAST(julianday(license_expiry) - julianday('now') AS INTEGER) as days_until_expiry
           FROM drivers WHERE license_expiry IS NOT NULL AND license_expiry != '' '''
    params = []
    if window:
        q += " AND julianday(license_expiry) - julianday('now') <= ?"
        params.append(window)
    q += " ORDER BY license_expiry ASC"
    rows = db.execute(q, params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@reports_bp.route('/api/reports/audit-log')
def reports_audit_log():
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    user_id = request.args.get('user_id')
    action_type = request.args.get('action_type')
    table_name = request.args.get('table_name')
    conds = []
    params = []
    if date_from:
        conds.append("timestamp >= ?")
        params.append(date_from)
    if date_to:
        conds.append("timestamp <= ?")
        params.append(date_to)
    if user_id:
        conds.append("user_id = ?")
        params.append(user_id)
    if action_type:
        conds.append("action_type = ?")
        params.append(action_type)
    if table_name:
        conds.append("table_name = ?")
        params.append(table_name)
    q = "SELECT * FROM audit_log"
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY timestamp DESC"
    rows = db.execute(q, params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

def _csv_response(rows, filename):
    if not rows:
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(["No data"])
    else:
        keys = rows[0].keys()
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(keys)
        for r in rows:
            writer.writerow([r[k] for k in keys])
    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename={filename}'})

@reports_bp.route('/api/reports/export/<report_name>')
def reports_export(report_name):
    if not require_admin():
        return jsonify({"error": "Forbidden"}), 403
    db = get_db()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    today = date.today().isoformat()

    if report_name == 'summary':
        fc_conds = ["status='Approved'"]; fc_p = []
        s_conds = []; s_p = []
        _apply_date_filters(fc_conds, fc_p, date_from, date_to, 'date')
        _apply_date_filters(s_conds, s_p, date_from, date_to, 'departure_time')
        rows = db.execute(f'''SELECT (SELECT SUM(cost) FROM fuel_logs{_where(fc_conds)}) as total_fuel_cost,
                                     (SELECT SUM(cost) FROM maintenance_logs) as total_maint_cost,
                                     (SELECT COUNT(*) FROM schedules{_where(s_conds)}) as total_trips,
                                     (SELECT COUNT(*) FROM schedules WHERE status='Completed'{_where(s_conds).replace('WHERE','AND') if s_conds else ''}) as completed_trips''',
                          fc_p + s_p).fetchall()
        db.close()
        return _csv_response(rows, f'srmss_summary_{today}.csv')

    elif report_name == 'fuel':
        conds = ["f.status='Approved'"]; params = []
        _apply_date_filters(conds, params, date_from, date_to, 'f.date')
        if request.args.get('vehicle_id'):
            conds.append("f.vehicle_id = ?"); params.append(request.args.get('vehicle_id'))
        rows = db.execute(f'''SELECT v.registration_no, v.type, SUM(f.cost) as total_cost, SUM(f.liters) as total_liters,
                              COUNT(f.id) as entry_count, strftime('%Y-%m',f.date) as month
                       FROM fuel_logs f JOIN vehicles v ON f.vehicle_id=v.id{_where(conds)}
                       GROUP BY v.id, month ORDER BY month''', params).fetchall()
        db.close()
        return _csv_response(rows, f'srmss_fuel_{today}.csv')

    elif report_name == 'fuel-efficiency':
        f_conds = ["f.status='Approved'"]; f_p = []
        s_conds = ["s.status='Completed'"]; s_p = []
        _apply_date_filters(f_conds, f_p, date_from, date_to, 'f.date')
        _apply_date_filters(s_conds, s_p, date_from, date_to, 's.departure_time')
        if request.args.get('vehicle_id'):
            f_p.append(request.args.get('vehicle_id')); s_p.append(request.args.get('vehicle_id'))
        rows = db.execute(f'''SELECT v.registration_no, v.type, COALESCE(f.total_liters,0) as total_liters,
                              COALESCE(s.total_km,0) as total_km,
                              CASE WHEN COALESCE(s.total_km,0)>0 THEN ROUND(COALESCE(f.total_liters,0)/s.total_km*100,2) ELSE 0 END as efficiency
                       FROM vehicles v
                       LEFT JOIN (SELECT vehicle_id, SUM(liters) as total_liters FROM fuel_logs{_where(f_conds)} GROUP BY vehicle_id) f ON v.id=f.vehicle_id
                       LEFT JOIN (SELECT s.vehicle_id, SUM(r.distance_km) as total_km FROM schedules s JOIN routes r ON s.route_id=r.id{_where(s_conds)} GROUP BY s.vehicle_id) s ON v.id=s.vehicle_id
                       ORDER BY efficiency DESC''', f_p + s_p).fetchall()
        db.close()
        return _csv_response(rows, f'srmss_fuel_efficiency_{today}.csv')

    elif report_name == 'maintenance':
        conds = []; params = []
        _apply_date_filters(conds, params, date_from, date_to, 'm.date')
        if request.args.get('vehicle_id'):
            conds.append("m.vehicle_id = ?"); params.append(request.args.get('vehicle_id'))
        if request.args.get('status'):
            conds.append("m.status = ?"); params.append(request.args.get('status'))
        rows = db.execute(f'''SELECT v.registration_no, v.type, SUM(m.cost) as total_cost, COUNT(m.id) as entry_count,
                              MAX(m.date) as last_date, strftime('%Y-%m',m.date) as month
                       FROM maintenance_logs m JOIN vehicles v ON m.vehicle_id=v.id{_where(conds)}
                       GROUP BY v.id, month ORDER BY month''', params).fetchall()
        db.close()
        return _csv_response(rows, f'srmss_maintenance_{today}.csv')

    elif report_name == 'trips':
        conds = []; params = []
        _apply_date_filters(conds, params, date_from, date_to, 's.departure_time')
        if request.args.get('route_id'):
            conds.append("s.route_id = ?"); params.append(request.args.get('route_id'))
        if request.args.get('vehicle_id'):
            conds.append("s.vehicle_id = ?"); params.append(request.args.get('vehicle_id'))
        if request.args.get('driver_id'):
            conds.append("s.driver_id = ?"); params.append(request.args.get('driver_id'))
        rows = db.execute(f'''SELECT s.status, COUNT(*) as count, strftime('%Y-%m',s.departure_time) as month
                       FROM schedules s{_where(conds)} GROUP BY s.status, month ORDER BY month''', params).fetchall()
        db.close()
        return _csv_response(rows, f'srmss_trips_{today}.csv')

    elif report_name == 'routes':
        conds = []; params = []
        _apply_date_filters(conds, params, date_from, date_to, 's.departure_time')
        rows = db.execute(f'''SELECT r.route_name, COUNT(*) as total_trips,
                              SUM(CASE WHEN s.status='Completed' THEN 1 ELSE 0 END) as completed_trips,
                              ROUND(AVG(CASE WHEN s.status='Completed' THEN 100.0 ELSE 0 END),1) as completion_rate
                       FROM schedules s JOIN routes r ON s.route_id=r.id{_where(conds)}
                       GROUP BY r.id ORDER BY completion_rate''', params).fetchall()
        db.close()
        return _csv_response(rows, f'srmss_routes_{today}.csv')

    elif report_name == 'fleet':
        s_conds = ["s.status='Completed'"]; s_p = []
        _apply_date_filters(s_conds, s_p, date_from, date_to, 's.departure_time')
        v_where = ""
        v_p = []
        if request.args.get('vehicle_type'):
            v_where = " WHERE v.type = ?"
            v_p.append(request.args.get('vehicle_type'))
        rows = db.execute(f'''SELECT v.registration_no, v.type, v.mileage, COALESCE(st.trip_count,0) as trips_completed,
                              COALESCE(st.total_km,0) as total_distance_km, COALESCE(fl.total_liters,0) as total_fuel_liters
                       FROM vehicles v
                       LEFT JOIN (SELECT s.vehicle_id, COUNT(*) as trip_count, SUM(r.distance_km) as total_km FROM schedules s JOIN routes r ON s.route_id=r.id{_where(s_conds)} GROUP BY s.vehicle_id) st ON v.id=st.vehicle_id
                       LEFT JOIN (SELECT vehicle_id, SUM(liters) as total_liters FROM fuel_logs WHERE status='Approved' GROUP BY vehicle_id) fl ON v.id=fl.vehicle_id{v_where}
                       ORDER BY trips_completed DESC''', s_p + v_p).fetchall()
        db.close()
        return _csv_response(rows, f'srmss_fleet_{today}.csv')

    elif report_name == 'drivers':
        s_conds = ["s.status='Completed'"]; s_p = []
        _apply_date_filters(s_conds, s_p, date_from, date_to, 's.departure_time')
        if request.args.get('driver_id'):
            s_conds.append("s.driver_id = ?"); s_p.append(request.args.get('driver_id'))
        rows = db.execute(f'''SELECT d.name, d.license_no, COUNT(s.id) as trips_completed
                       FROM drivers d LEFT JOIN schedules s ON d.id=s.driver_id{_where(s_conds)}
                       GROUP BY d.id ORDER BY trips_completed DESC''', s_p).fetchall()
        db.close()
        return _csv_response(rows, f'srmss_drivers_{today}.csv')

    elif report_name == 'licenses':
        window = request.args.get('window', type=int)
        q = '''SELECT name, license_no, license_expiry,
                       CAST(julianday(license_expiry) - julianday('now') AS INTEGER) as days_until_expiry
                FROM drivers WHERE license_expiry IS NOT NULL AND license_expiry != '' '''
        params = []
        if window:
            q += " AND julianday(license_expiry) - julianday('now') <= ?"
            params.append(window)
        q += " ORDER BY license_expiry ASC"
        rows = db.execute(q, params).fetchall()
        db.close()
        return _csv_response(rows, f'srmss_licenses_{today}.csv')

    elif report_name == 'audit-log':
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        user_id = request.args.get('user_id')
        action_type = request.args.get('action_type')
        table_name = request.args.get('table_name')
        conds = []
        params = []
        if date_from:
            conds.append("timestamp >= ?")
            params.append(date_from)
        if date_to:
            conds.append("timestamp <= ?")
            params.append(date_to)
        if user_id:
            conds.append("user_id = ?")
            params.append(user_id)
        if action_type:
            conds.append("action_type = ?")
            params.append(action_type)
        if table_name:
            conds.append("table_name = ?")
            params.append(table_name)
        q = "SELECT * FROM audit_log"
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY timestamp DESC"
        rows = db.execute(q, params).fetchall()
        db.close()
        return _csv_response(rows, f'srmss_audit_log_{today}.csv')

    db.close()
    return jsonify({"error": "Unknown report"}), 404
