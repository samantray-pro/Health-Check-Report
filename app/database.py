import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path("health_tracker.db")

def init_db():
    """Initializes the local SQLite database schema and indexes."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 1. Persona Profiles Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            health_issues TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Uploaded Source Reports Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            report_date DATE,
            extracted_raw_text TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
        );
        """)

        # 3. Individual Medical Test Records Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            report_id INTEGER,
            test_name TEXT NOT NULL,
            raw_test_name TEXT,
            value REAL NOT NULL,
            value_str TEXT,
            unit TEXT,
            reference_range TEXT,
            flag TEXT DEFAULT 'NORMAL',
            test_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE,
            FOREIGN KEY (report_id) REFERENCES reports (id) ON DELETE SET NULL
        );
        """)

        # Performance indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_profile_test ON test_records (profile_id, test_name, test_date ASC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_test_date ON test_records (test_date);")
        conn.commit()

@contextmanager
def get_db():
    """Context manager for thread-safe SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def seed_sample_data_if_empty():
    """No-op: sample data seeding disabled to ensure clean, user-owned local database."""
    pass
