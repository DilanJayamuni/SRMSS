from flask import Blueprint, request, jsonify, session
from init_db import get_db

schedule_proposals_bp = Blueprint('schedule_proposals', __name__)


@schedule_proposals_bp.route('/api/schedule-proposals', methods=['POST'])
def create_proposal():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    d = request.json
    driver_id = d.get('driver_id')
    vehicle_id = d.get('vehicle_id')
    route_id = d.get('route_id')
    proposed_date = d.get('proposed_date', '')
    departure_time = d.get('departure_time', '')
    arrival_time = d.get('arrival_time', '')
    recurrence = d.get('recurrence', 'Once')
    notes = d.get('notes', '')

    if not driver_id:
        return jsonify({"error": "driver_id is required"}), 400
    if not vehicle_id:
        return jsonify({"error": "vehicle_id is required"}), 400
    if not route_id:
        return jsonify({"error": "route_id is required"}), 400
    if not departure_time:
        return jsonify({"error": "departure_time is required"}), 400

    db = get_db()
    db.execute('''
        INSERT INTO schedule_proposals
            (driver_id, vehicle_id, route_id, proposed_date, departure_time, arrival_time, recurrence, notes, proposed_by)
        VALUES (?,?,?,?,?,?,?,?,?)
    ''', (driver_id, vehicle_id, route_id, proposed_date, departure_time, arrival_time, recurrence, notes,
          session['user']['id']))
    db.commit()
    db.close()
    return jsonify({"success": True})


@schedule_proposals_bp.route('/api/schedule-proposals', methods=['GET'])
def list_proposals():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    status_filter = request.args.get('status')
    db = get_db()

    if status_filter:
        items = db.execute('''
            SELECT p.id, p.driver_id, p.vehicle_id, p.route_id,
                   p.proposed_date, p.departure_time, p.arrival_time,
                   p.recurrence, p.notes, p.status, p.created_at,
                   d.name as driver_name, v.registration_no as vehicle_reg, r.route_name
            FROM schedule_proposals p
            JOIN drivers d ON p.driver_id = d.id
            JOIN vehicles v ON p.vehicle_id = v.id
            JOIN routes r ON p.route_id = r.id
            WHERE p.status = ?
            ORDER BY p.created_at DESC
        ''', (status_filter,)).fetchall()
    else:
        items = db.execute('''
            SELECT p.id, p.driver_id, p.vehicle_id, p.route_id,
                   p.proposed_date, p.departure_time, p.arrival_time,
                   p.recurrence, p.notes, p.status, p.created_at,
                   d.name as driver_name, v.registration_no as vehicle_reg, r.route_name
            FROM schedule_proposals p
            JOIN drivers d ON p.driver_id = d.id
            JOIN vehicles v ON p.vehicle_id = v.id
            JOIN routes r ON p.route_id = r.id
            ORDER BY p.created_at DESC
        ''').fetchall()

    db.close()
    return jsonify([dict(i) for i in items])


@schedule_proposals_bp.route('/api/schedule-proposals/<int:id>/approve', methods=['POST'])
def approve_proposal(id):
    if 'user' not in session or session['user']['role'] not in ('Administrator', 'Supervisor'):
        return jsonify({"error": "Forbidden"}), 403

    db = get_db()
    proposal = db.execute('SELECT * FROM schedule_proposals WHERE id=? AND status="Pending"',
                          (id,)).fetchone()
    if not proposal:
        db.close()
        return jsonify({"error": "Proposal not found or already reviewed"}), 404

    db.execute('''
        INSERT INTO schedules (route_id, vehicle_id, driver_id, departure_time, arrival_time, recurrence, status)
        VALUES (?,?,?,?,?,?,'Scheduled')
    ''', (proposal['route_id'], proposal['vehicle_id'], proposal['driver_id'],
          proposal['departure_time'], proposal['arrival_time'], proposal['recurrence']))

    db.execute('''
        UPDATE schedule_proposals SET status='Approved', reviewed_at=datetime('now'), reviewed_by=?
        WHERE id=?
    ''', (session['user']['id'], id))
    db.commit()
    db.close()
    return jsonify({"success": True})


@schedule_proposals_bp.route('/api/schedule-proposals/<int:id>/reject', methods=['POST'])
def reject_proposal(id):
    if 'user' not in session or session['user']['role'] not in ('Administrator', 'Supervisor'):
        return jsonify({"error": "Forbidden"}), 403

    db = get_db()
    proposal = db.execute('SELECT id FROM schedule_proposals WHERE id=? AND status="Pending"',
                          (id,)).fetchone()
    if not proposal:
        db.close()
        return jsonify({"error": "Proposal not found or already reviewed"}), 404

    db.execute('''
        UPDATE schedule_proposals SET status='Rejected', reviewed_at=datetime('now'), reviewed_by=?
        WHERE id=?
    ''', (session['user']['id'], id))
    db.commit()
    db.close()
    return jsonify({"success": True})
