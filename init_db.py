import sqlite3

DB_NAME = 'srmss_rbac.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT);
        CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY, registration_no TEXT UNIQUE, type TEXT, capacity INTEGER, mileage INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS drivers (id INTEGER PRIMARY KEY, name TEXT, license_no TEXT UNIQUE, license_expiry TEXT);
    ''')
    
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
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assignments'")
    if cursor.fetchone():
        cursor.executescript('''
            INSERT OR IGNORE INTO assigndriver (id, driver_id, vehicle_id, assigned_at)
            SELECT id, driver_id, vehicle_id, assigned_at FROM assignments;
            DROP TABLE assignments;
        ''')

    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin123', 'Administrator')")
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('super', 'super123', 'Supervisor')")
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('staff', 'staff123', 'Operational Staff')")

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn
