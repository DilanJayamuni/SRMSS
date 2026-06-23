import sqlite3

DB_NAME = 'srmss_rbac.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT);
        CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY, registration_no TEXT UNIQUE, type TEXT, capacity INTEGER, mileage INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS drivers (id INTEGER PRIMARY KEY, name TEXT, license_no TEXT UNIQUE, license_expiry TEXT);
        CREATE TABLE IF NOT EXISTS routes (id INTEGER PRIMARY KEY, route_name TEXT, start_point TEXT, end_point TEXT, distance_km REAL);
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY, 
            route_id INTEGER, 
            vehicle_id INTEGER, 
            driver_id INTEGER, 
            departure_time TEXT,
            arrival_time TEXT NOT NULL DEFAULT '',
            recurrence TEXT DEFAULT 'Once',
            status TEXT DEFAULT 'Scheduled'
        );
        CREATE TABLE IF NOT EXISTS fuel_logs (id INTEGER PRIMARY KEY, vehicle_id INTEGER, date TEXT, liters REAL, cost REAL, status TEXT DEFAULT 'Pending');
        CREATE TABLE IF NOT EXISTS maintenance_logs (id INTEGER PRIMARY KEY, vehicle_id INTEGER, description TEXT, cost REAL, date TEXT, mileage REAL, status TEXT DEFAULT 'Pending');
        CREATE TABLE IF NOT EXISTS assigndriver (
            id INTEGER PRIMARY KEY,
            driver_id INTEGER NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
            vehicle_id INTEGER UNIQUE NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            assigned_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS schedule_proposals (
            id INTEGER PRIMARY KEY,
            driver_id INTEGER NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
            vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            route_id INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
            proposed_date TEXT,
            departure_time TEXT NOT NULL,
            arrival_time TEXT NOT NULL DEFAULT '',
            recurrence TEXT DEFAULT 'Once',
            notes TEXT DEFAULT '',
            status TEXT DEFAULT 'Pending',
            proposed_by INTEGER REFERENCES users(id),
            created_at TEXT DEFAULT (datetime('now')),
            reviewed_at TEXT,
            reviewed_by INTEGER REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS assignroute (
            id INTEGER PRIMARY KEY,
            route_id INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
            vehicle_id INTEGER UNIQUE NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
            assigned_at TEXT DEFAULT (datetime('now'))
        );
    ''')

    cursor.execute("PRAGMA table_info(routes)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'stops' not in columns: cursor.execute("ALTER TABLE routes ADD COLUMN stops TEXT")
    if 'path_geometry' not in columns: cursor.execute("ALTER TABLE routes ADD COLUMN path_geometry TEXT")

    cursor.execute("PRAGMA table_info(vehicles)")
    v_cols = [info[1] for info in cursor.fetchall()]
    if 'mileage' not in v_cols: cursor.execute("ALTER TABLE vehicles ADD COLUMN mileage INTEGER DEFAULT 0")
    if 'vehicle_number' not in v_cols: cursor.execute("ALTER TABLE vehicles ADD COLUMN vehicle_number TEXT")
    if 'seats' not in v_cols:
        cursor.execute("ALTER TABLE vehicles ADD COLUMN seats INTEGER DEFAULT 0")
        cursor.execute("UPDATE vehicles SET seats = capacity WHERE seats IS NULL OR seats = 0")

    cursor.execute("PRAGMA table_info(drivers)")
    d_cols = [info[1] for info in cursor.fetchall()]
    if 'license_expiry' not in d_cols: cursor.execute("ALTER TABLE drivers ADD COLUMN license_expiry TEXT")
    if 'assigned_route' in d_cols:
        cursor.executescript('''
            CREATE TABLE drivers_new (id INTEGER PRIMARY KEY, name TEXT, license_no TEXT UNIQUE, license_expiry TEXT);
            INSERT INTO drivers_new (id, name, license_no, license_expiry) SELECT id, name, license_no, license_expiry FROM drivers;
            DROP TABLE drivers;
            ALTER TABLE drivers_new RENAME TO drivers;
        ''')

    cursor.execute("PRAGMA index_list(assigndriver)")
    ad_indexes = cursor.fetchall()
    unique_count = sum(1 for idx in ad_indexes if idx[2] == 1)
    if unique_count > 1:
        cursor.executescript('''
            CREATE TABLE assigndriver_new (
                id INTEGER PRIMARY KEY,
                driver_id INTEGER NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
                vehicle_id INTEGER UNIQUE NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
                assigned_at TEXT DEFAULT (datetime('now'))
            );
            INSERT INTO assigndriver_new (id, driver_id, vehicle_id, assigned_at)
            SELECT id, driver_id, vehicle_id, assigned_at FROM assigndriver;
            DROP TABLE assigndriver;
            ALTER TABLE assigndriver_new RENAME TO assigndriver;
        ''')

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schedule_proposals'")
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE schedule_proposals (
                id INTEGER PRIMARY KEY,
                driver_id INTEGER NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
                vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
                route_id INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
                proposed_date TEXT,
                departure_time TEXT NOT NULL,
                arrival_time TEXT NOT NULL DEFAULT '',
                recurrence TEXT DEFAULT 'Once',
                notes TEXT DEFAULT '',
                status TEXT DEFAULT 'Pending',
                proposed_by INTEGER REFERENCES users(id),
                created_at TEXT DEFAULT (datetime('now')),
                reviewed_at TEXT,
                reviewed_by INTEGER REFERENCES users(id)
            )
        ''')

    cursor.execute("PRAGMA table_info(schedules)")
    s_cols = [info[1] for info in cursor.fetchall()]
    if 'recurrence' not in s_cols: cursor.execute("ALTER TABLE schedules ADD COLUMN recurrence TEXT DEFAULT 'Once'")
    if 'status' not in s_cols: cursor.execute("ALTER TABLE schedules ADD COLUMN status TEXT DEFAULT 'Scheduled'")
    if 'arrival_time' not in s_cols:
        cursor.execute("ALTER TABLE schedules ADD COLUMN arrival_time TEXT NOT NULL DEFAULT ''")
        cursor.execute("UPDATE schedules SET arrival_time = departure_time WHERE arrival_time = ''")

    cursor.execute("PRAGMA table_info(fuel_logs)")
    f_cols = [info[1] for info in cursor.fetchall()]
    if 'status' not in f_cols: cursor.execute("ALTER TABLE fuel_logs ADD COLUMN status TEXT DEFAULT 'Pending'")
    if 'cost' not in f_cols: cursor.execute("ALTER TABLE fuel_logs ADD COLUMN cost REAL")
    if 'mileage' not in f_cols: cursor.execute("ALTER TABLE fuel_logs ADD COLUMN mileage REAL")

    cursor.execute("PRAGMA table_info(maintenance_logs)")
    m_cols = [info[1] for info in cursor.fetchall()]
    if 'cost' not in m_cols: cursor.execute("ALTER TABLE maintenance_logs ADD COLUMN cost REAL")
    if 'date' not in m_cols: cursor.execute("ALTER TABLE maintenance_logs ADD COLUMN date TEXT")
    if 'mileage' not in m_cols: cursor.execute("ALTER TABLE maintenance_logs ADD COLUMN mileage REAL")
    if 'status' not in m_cols: cursor.execute("ALTER TABLE maintenance_logs ADD COLUMN status TEXT DEFAULT 'Pending'")
    if 'type' in m_cols:
        cursor.executescript('''
            CREATE TABLE maintenance_logs_new (id INTEGER PRIMARY KEY, vehicle_id INTEGER, description TEXT, cost REAL, date TEXT, mileage REAL, status TEXT DEFAULT 'Pending');
            INSERT INTO maintenance_logs_new (id, vehicle_id, description, cost, date, mileage, status) SELECT id, vehicle_id, description, cost, date, mileage, status FROM maintenance_logs;
            DROP TABLE maintenance_logs;
            ALTER TABLE maintenance_logs_new RENAME TO maintenance_logs;
        ''')

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assignments'")
    if cursor.fetchone():
        cursor.executescript('''
            INSERT OR IGNORE INTO assigndriver (id, driver_id, vehicle_id, assigned_at)
            SELECT id, driver_id, vehicle_id, assigned_at FROM assignments;
            DROP TABLE assignments;
        ''')

    cursor.execute("PRAGMA table_info(users)")
    u_cols = [info[1] for info in cursor.fetchall()]
    if 'first_name' not in u_cols: cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
    if 'last_name' not in u_cols: cursor.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
    if 'phone_number' not in u_cols: cursor.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
    if 'address' not in u_cols: cursor.execute("ALTER TABLE users ADD COLUMN address TEXT")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fuel_date ON fuel_logs(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_maint_date ON maintenance_logs(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sched_departure ON schedules(departure_time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sched_status ON schedules(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sched_driver_departure ON schedules(driver_id, departure_time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_proposal_status ON schedule_proposals(status)")

    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin123', 'Administrator')")
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('super', 'super123', 'Supervisor')")
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('staff', 'staff123', 'Operational Staff')")

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn
