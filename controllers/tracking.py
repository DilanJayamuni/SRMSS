import json
import math
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from init_db import get_db

tracking_bp = Blueprint('tracking', __name__)

def parse_dt(val):
    for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(val, fmt)
        except (ValueError, TypeError):
            pass
    return None

@tracking_bp.route('/tracking')
def tracking_page():
    if 'user' not in session:
        return redirect(url_for('login.index'))
    if session['user']['role'] != 'Administrator':
        return redirect(url_for('dashboard.dashboard_page'))
    return render_template('tracking.html', user=session['user'])

@tracking_bp.route('/api/tracking')
def api_tracking():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()

    schedules = db.execute('''
        SELECT s.id, s.departure_time, s.arrival_time, s.status,
               v.id as vehicle_id, v.registration_no, v.type as vehicle_type,
               r.route_name, r.distance_km, r.path_geometry,
               d.name as driver_name
        FROM schedules s
        JOIN vehicles v ON s.vehicle_id = v.id
        JOIN routes r ON s.route_id = r.id
        JOIN drivers d ON s.driver_id = d.id
        WHERE s.status = 'In Transit'
    ''').fetchall()

    now = datetime.now()
    result = []

    for s in schedules:
        dep = parse_dt(s['departure_time'])
        arr = parse_dt(s['arrival_time'])
        if not dep or not arr:
            continue

        total = (arr - dep).total_seconds()
        elapsed = (now - dep).total_seconds()
        progress = max(0.0, min(1.0, elapsed / total)) if total > 0 else 1.0

        lat, lng = 0.0, 0.0
        heading = 0.0

        if s['path_geometry']:
            try:
                path = json.loads(s['path_geometry'])
                if path and len(path) >= 2:
                    seg_count = len(path) - 1
                    seg_idx = min(int(progress * seg_count), seg_count - 1)
                    seg_frac = (progress * seg_count) - seg_idx
                    p1 = path[seg_idx]
                    p2 = path[min(seg_idx + 1, len(path) - 1)]
                    lat = p1[0] + (p2[0] - p1[0]) * seg_frac
                    lng = p1[1] + (p2[1] - p1[1]) * seg_frac
                    heading = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
                elif path:
                    lat, lng = path[0][0], path[0][1]
            except (json.JSONDecodeError, IndexError, TypeError):
                continue

        speed = 0.0
        if s['distance_km'] and total > 0:
            speed = round((s['distance_km'] / total) * 3600, 1)

        result.append({
            'vehicle_id': s['vehicle_id'],
            'registration_no': s['registration_no'],
            'vehicle_type': s['vehicle_type'],
            'latitude': lat,
            'longitude': lng,
            'speed': speed,
            'heading': round(heading, 1),
            'route_name': s['route_name'],
            'driver_name': s['driver_name'],
            'status': s['status'],
            'progress': round(progress * 100, 1)
        })

    db.close()
    return jsonify(result)
