import sqlite3

DB_NAME = 'srmss_rbac.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT);
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
