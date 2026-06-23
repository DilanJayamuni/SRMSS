import sqlite3

DB_NAME = "srmss_rbac.db"

conn = sqlite3.connect(DB_NAME)
conn.executescript("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        username TEXT,
        action_type TEXT,
        table_name TEXT,
        record_id INTEGER,
        old_values TEXT,
        new_values TEXT,
        timestamp TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
    CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name);
    DELETE FROM audit_log;
""")
conn.commit()
count = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
print(f"audit_log table ready. Rows: {count}")
conn.close()
