from datetime import datetime, timedelta
from init_db import get_db, DB_NAME
import sqlite3

def seed():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now()
    vehicles = c.execute('SELECT id, registration_no FROM vehicles').fetchall()
    drivers = c.execute('SELECT id, name FROM drivers').fetchall()
    routes = c.execute('SELECT id, route_name, distance_km FROM routes').fetchall()
    if not vehicles or not drivers or not routes:
        print('ERROR: Need existing vehicles, drivers, and routes in the DB.')
        conn.close()
        return
    demo_ids = [v[0] for v in vehicles[:5]]
    for vid in demo_ids:
        c.execute("UPDATE schedules SET status='Completed' WHERE vehicle_id=?", (vid,))
    schedule_specs = [
        (0, 0, 1.0, 3.5),
        (1, 1, 0.5, 4.0),
        (2, 7, 2.0, 5.0),
        (3, 9, 1.5, 2.5),
        (4, 5, 0.75, 2.0),
    ]
    created = 0
    for voff, roff, h_ago, dur_h in schedule_specs:
        if voff >= len(demo_ids) or roff >= len(routes):
            continue
        vid = demo_ids[voff]
        rid = routes[roff][0]
        dr = c.execute('SELECT driver_id FROM assigndriver WHERE vehicle_id=?', (vid,)).fetchone()
        if not dr:
            continue
        dep = now - timedelta(hours=h_ago)
        arr = dep + timedelta(hours=dur_h)
        c.execute("INSERT INTO schedules (route_id, vehicle_id, driver_id, departure_time, arrival_time, recurrence, status) VALUES (?, ?, ?, ?, ?, 'Once', 'In Transit')",
                  (rid, vid, dr[0], dep.strftime('%Y-%m-%dT%H:%M'), arr.strftime('%Y-%m-%dT%H:%M')))
        created += 1
    conn.commit()
    conn.close()
    print(f'Created {created} "In Transit" schedules.')

if __name__ == '__main__':
    seed()
