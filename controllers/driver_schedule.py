from datetime import datetime, timedelta
import calendar
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from init_db import get_db

driver_schedule_bp = Blueprint('driver_schedule', __name__)
EXPANSION_LIMIT = 500


@driver_schedule_bp.route('/driver-schedule')
def driver_schedule_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    return render_template('driver_schedule.html', user=session['user'])



def expand_recurrences(schedules, year, month):
    expanded = []
    days_in_month = calendar.monthrange(year, month)[1]

    for s in schedules:
        dep = s['departure_time']
        if not dep:
            continue
        try:
            dep_dt = datetime.fromisoformat(dep)
        except (ValueError, TypeError):
            continue

        arr = s.get('arrival_time', '')
        arr_dt = None
        if arr:
            try:
                arr_dt = datetime.fromisoformat(arr)
            except (ValueError, TypeError):
                pass

        duration = None
        if arr_dt and dep_dt:
            duration = arr_dt - dep_dt

        recur = s.get('recurrence', 'Once')

        if recur == 'Once':
            if dep_dt.year == year and dep_dt.month == month:
                if len(expanded) >= EXPANSION_LIMIT:
                    break
                expanded.append({
                    'date': dep_dt.strftime('%Y-%m-%d'),
                    'departure_time': dep_dt.isoformat(),
                    'arrival_time': arr_dt.isoformat() if arr_dt else '',
                    'vehicle_reg': s.get('registration_no', ''),
                    'route_name': s.get('route_name', ''),
                    'status': s.get('status', ''),
                    'schedule_id': s['id']
                })

        elif recur == 'Daily':
            for day in range(1, days_in_month + 1):
                if len(expanded) >= EXPANSION_LIMIT:
                    break
                date_str = f'{year:04d}-{month:02d}-{day:02d}'
                new_dep = f'{date_str}T{dep_dt.strftime("%H:%M:%S")}'
                new_arr = ''
                if duration is not None:
                    arr_time = datetime.strptime(new_dep, '%Y-%m-%dT%H:%M:%S') + duration
                    new_arr = arr_time.isoformat()
                expanded.append({
                    'date': date_str,
                    'departure_time': new_dep,
                    'arrival_time': new_arr,
                    'vehicle_reg': s.get('registration_no', ''),
                    'route_name': s.get('route_name', ''),
                    'status': s.get('status', ''),
                    'schedule_id': s['id']
                })

        elif recur == 'Weekly':
            target_weekday = dep_dt.weekday()
            for day in range(1, days_in_month + 1):
                if len(expanded) >= EXPANSION_LIMIT:
                    break
                dt = datetime(year, month, day)
                if dt.weekday() == target_weekday:
                    date_str = dt.strftime('%Y-%m-%d')
                    new_dep = f'{date_str}T{dep_dt.strftime("%H:%M:%S")}'
                    new_arr = ''
                    if duration is not None:
                        arr_time = datetime.strptime(new_dep, '%Y-%m-%dT%H:%M:%S') + duration
                        new_arr = arr_time.isoformat()
                    expanded.append({
                        'date': date_str,
                        'departure_time': new_dep,
                        'arrival_time': new_arr,
                        'vehicle_reg': s.get('registration_no', ''),
                        'route_name': s.get('route_name', ''),
                        'status': s.get('status', ''),
                        'schedule_id': s['id']
                    })

    grouped = {}
    for entry in expanded:
        d = entry['date']
        if d not in grouped:
            grouped[d] = []
        grouped[d].append(entry)

    return grouped


@driver_schedule_bp.route('/api/driver-schedule')
def api_driver_schedule():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    driver_id = request.args.get('driver_id', type=int)
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)

    if not driver_id or not month or not year:
        return jsonify({"error": "driver_id, month, and year are required"}), 400

    if month < 1 or month > 12:
        return jsonify({"error": "month must be between 1 and 12"}), 400

    db = get_db()
    schedules = db.execute('''
        SELECT s.id, s.departure_time, s.arrival_time, s.recurrence, s.status,
               v.registration_no, r.route_name
        FROM schedules s
        JOIN vehicles v ON s.vehicle_id = v.id
        JOIN routes r ON s.route_id = r.id
        WHERE s.driver_id = ?
    ''', (driver_id,)).fetchall()
    db.close()

    grouped = expand_recurrences([dict(s) for s in schedules], year, month)

    driver_name = 'Unknown'
    db = get_db()
    dr = db.execute('SELECT name FROM drivers WHERE id=?', (driver_id,)).fetchone()
    db.close()
    if dr:
        driver_name = dr['name']

    return jsonify({
        'driver_id': driver_id,
        'driver_name': driver_name,
        'year': year,
        'month': month,
        'days_in_month': calendar.monthrange(year, month)[1],
        'schedules': grouped
    })
